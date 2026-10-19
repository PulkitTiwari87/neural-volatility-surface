"""Phase 5: read-only research API (SYNTHETIC runs): labelling, lineage, NaN handling, path safety, GET-only."""
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np

from volatility_lab.api.server import FRONTEND, create_server, dispatch
from volatility_lab.api.service import RunStore
from volatility_lab.config.settings import Config
from volatility_lab.datasets.synthetic import make_chain
from volatility_lab.storage.raw_store import ingest


def _get(store, path):
    code, ctype, body = dispatch(store, path)
    return code, ctype, (json.loads(body) if ctype == "application/json" else body)


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.td = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.td.name)
        wide, _ = make_chain(10, seed=1)
        src = cls.dir / "chain.csv"
        wide.to_csv(src, index=False)
        m = ingest(cls.dir / "store", [src], Config())
        cls.root = cls.dir / "store" / "datasets"
        cls.id = m["version_id"]
        run = cls.root / cls.id
        (run / "meta.json").write_text(json.dumps({"origin": "synthetic", "description": "x"}))
        (run / "tables").mkdir()
        (run / "tables" / "demo.csv").write_text("tenor_days,mae,n\n7,0.5,12\n14,,0\n")
        # a persistence forecast: surface at t+1 is predicted by the surface at t (origin strictly before target)
        with np.load(run / "panel.npz") as z:
            iv = z["iv"]
        (run / "forecasts").mkdir()
        n = iv.shape[0]
        np.savez_compressed(run / "forecasts" / "persistence.npz", target_index=np.arange(1, n),
                            origin_index=np.arange(0, n - 1), pred=iv[:-1])
        np.savez_compressed(run / "forecasts" / "from_future.npz", target_index=np.arange(0, n - 1),
                            origin_index=np.arange(1, n), pred=iv[1:])
        # a second run with no meta.json and no manifest
        other = cls.root / "bare_run"
        other.mkdir()
        with np.load(run / "panel.npz") as z:
            np.savez_compressed(other / "panel.npz", **{k: z[k] for k in z.files})
        cls.store = RunStore(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls.td.cleanup()

    def test_runs_are_listed_with_an_explicit_origin_label(self):
        code, _, runs = _get(self.store, "/api/runs")
        self.assertEqual(code, 200)
        origins = {r["id"]: r["origin"] for r in runs}
        self.assertEqual(origins[self.id], "synthetic")
        self.assertEqual(origins["bare_run"], "unlabelled")

    def test_run_info_reports_lineage_and_status_counts(self):
        _, _, info = _get(self.store, f"/api/runs/{self.id}")
        self.assertTrue(info["lineage"]["panel_hash_matches"])
        self.assertTrue(info["lineage"]["ledgers_conserved"])
        self.assertEqual(info["tables"], ["demo"])
        self.assertEqual(sum(info["status_counts"].values()), len(info["dates"]) * len(info["tenor_days"]) * len(info["k_nodes"]))
        self.assertIsNone(_get(self.store, "/api/runs/bare_run")[2]["lineage"])

    def test_tampered_panel_is_reported_as_a_hash_mismatch(self):
        run = self.root / self.id
        with np.load(run / "panel.npz") as z:
            panel = {k: z[k] for k in z.files}
        clone = self.root / "tampered"
        clone.mkdir(exist_ok=True)
        panel["spot"] = panel["spot"] + 1.0
        np.savez_compressed(clone / "panel.npz", **panel)
        (clone / "manifest.json").write_text((run / "manifest.json").read_text())
        self.assertFalse(_get(self.store, "/api/runs/tampered")[2]["lineage"]["panel_hash_matches"])

    def test_missing_cells_are_null_never_filled_and_json_is_strict(self):
        _, _, info = _get(self.store, f"/api/runs/{self.id}")
        saw_missing = False
        for i in range(len(info["dates"])):
            code, _, s = _get(self.store, f"/api/runs/{self.id}/surface/{i}")
            self.assertEqual(code, 200)
            for r_iv, r_st in zip(s["iv"], s["status"]):
                for v, st in zip(r_iv, r_st):
                    if st == 0:
                        saw_missing = True
                        self.assertIsNone(v)
                    else:
                        self.assertIsInstance(v, float)
        self.assertTrue(saw_missing, "fixture should contain at least one missing cell")

    def test_out_of_range_and_unknown_routes(self):
        self.assertEqual(_get(self.store, f"/api/runs/{self.id}/surface/9999")[0], 404)
        self.assertEqual(_get(self.store, "/api/nope")[0], 404)
        self.assertEqual(_get(self.store, "/api/runs/does_not_exist")[0], 404)

    def test_tables_are_served_and_empty_cells_stay_text(self):
        code, _, t = _get(self.store, f"/api/runs/{self.id}/tables/demo")
        self.assertEqual(code, 200)
        self.assertEqual(t["columns"], ["tenor_days", "mae", "n"])
        self.assertEqual(t["rows"][0], [7.0, 0.5, 12.0])
        self.assertEqual(t["rows"][1][1], "")

    def test_forecast_is_listed_and_difference_is_forecast_minus_actual(self):
        self.assertEqual(_get(self.store, f"/api/runs/{self.id}")[2]["forecasts"], ["from_future", "persistence"])
        code, _, a = _get(self.store, f"/api/runs/{self.id}/surface/4")
        code2, _, f = _get(self.store, f"/api/runs/{self.id}/forecasts/persistence/4")
        _, _, prev = _get(self.store, f"/api/runs/{self.id}/surface/3")
        self.assertEqual((code, code2), (200, 200))
        self.assertEqual((f["origin_date"], f["target_date"], f["horizon_panel_steps"]), (prev["date"], a["date"], 1))
        n_diff = n_obs = 0
        abs_obs = []
        for j, row in enumerate(f["difference"]):
            for c, d in enumerate(row):
                st, act, fc = a["status"][j][c], a["iv"][j][c], prev["iv"][j][c]
                if st == 0 or fc is None:                      # missing actual or no forecast -> no difference
                    self.assertIsNone(d)
                    self.assertIsNone(f["actual"][j][c] if st == 0 else None)
                else:
                    self.assertAlmostEqual(d, fc - act, places=12)
                    n_diff += 1
                    if st == 3:
                        n_obs += 1
                        abs_obs.append(abs(d) * 100.0)
        self.assertGreater(n_diff, 0)
        self.assertEqual((f["n_difference_cells"], f["n_observed_cells"]), (n_diff, n_obs))
        if abs_obs:
            self.assertAlmostEqual(f["mae_observed_vol_points"], sum(abs_obs) / len(abs_obs), places=9)
        else:
            self.assertIsNone(f["mae_observed_vol_points"])

    def test_a_forecast_file_with_an_origin_at_or_after_its_target_is_rejected(self):
        self.assertEqual(_get(self.store, f"/api/runs/{self.id}/forecasts/from_future/0")[0], 400)

    def test_unknown_forecast_model_or_target_index_is_404_and_names_are_validated(self):
        self.assertEqual(_get(self.store, f"/api/runs/{self.id}/forecasts/nope/3")[0], 404)
        self.assertEqual(_get(self.store, f"/api/runs/{self.id}/forecasts/persistence/0")[0], 404)  # no forecast of day 0
        for bad in ("..", "%2e%2e%2fmeta", "a%2fb", ".hidden"):
            self.assertIn(_get(self.store, f"/api/runs/{self.id}/forecasts/{bad}/3")[0], (400, 404), bad)

    def test_path_traversal_is_rejected(self):
        (self.dir / "secret.csv").write_text("a\n1\n")
        for bad in ("..", "%2e%2e", "..%2fstore", "a%2fb", ".hidden", "x" * 200):
            code, _, _ = _get(self.store, f"/api/runs/{bad}")
            self.assertIn(code, (400, 404), bad)
        for bad in ("..%2fmeta", "../meta", "%2e%2e%2f%2e%2e%2fsecret", "demo.csv%00"):
            self.assertIn(_get(self.store, f"/api/runs/{self.id}/tables/{bad}")[0], (400, 404), bad)

    def test_non_loopback_bind_is_refused(self):
        with self.assertRaises(ValueError):
            create_server(self.root, host="0.0.0.0", port=0)

    def test_real_socket_get_ok_and_other_methods_405_with_security_headers(self):
        srv = create_server(self.root, port=0)
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            base = f"http://127.0.0.1:{srv.server_address[1]}"
            with urllib.request.urlopen(base + "/api/runs", timeout=10) as r:
                self.assertEqual(r.status, 200)
                self.assertEqual(r.headers["X-Content-Type-Options"], "nosniff")
                self.assertIn("default-src 'none'", r.headers["Content-Security-Policy"])
            with urllib.request.urlopen(base + "/", timeout=10) as r:
                # transport only: the served bytes are the frontend file on disk, whatever its wording (the
                # frontend is owned by the dashboard workstream and is edited independently of the API)
                self.assertEqual(r.read(), FRONTEND.read_bytes())
                self.assertTrue(r.headers["Content-Type"].startswith("text/html"))
            req = urllib.request.Request(base + "/api/runs", data=b"{}", method="POST")
            with self.assertRaises(urllib.error.HTTPError) as cm:
                urllib.request.urlopen(req, timeout=10)
            self.assertEqual(cm.exception.code, 405)
        finally:
            srv.shutdown()
            srv.server_close()


if __name__ == "__main__":
    unittest.main()
