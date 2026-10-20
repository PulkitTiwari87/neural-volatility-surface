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


class ApiRobustnessTests(unittest.TestCase):
    """Corrupt / hostile run directories must give predictable 4xx/5xx JSON, never a crash or a leaked path."""

    @classmethod
    def setUpClass(cls):
        cls.td = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.td.name)
        wide, _ = make_chain(10, seed=1)
        src = cls.dir / "chain.csv"
        wide.to_csv(src, index=False)
        m = ingest(cls.dir / "store", [src], Config())
        cls.root = cls.dir / "store" / "datasets"
        cls.good = cls.root / m["version_id"]
        with np.load(cls.good / "panel.npz") as z:
            cls.arrays = {k: z[k] for k in z.files}

    @classmethod
    def tearDownClass(cls):
        cls.td.cleanup()

    def _run(self, name, **arrays):
        d = self.root / name
        d.mkdir(exist_ok=True)
        np.savez_compressed(d / "panel.npz", **{**self.arrays, **arrays})
        return d

    def test_empty_table_file_is_an_empty_table_not_a_crash(self):
        d = self._run("empty_table")
        (d / "tables").mkdir(exist_ok=True)
        (d / "tables" / "blank.csv").write_text("")
        code, _, t = _get(RunStore(self.root), "/api/runs/empty_table/tables/blank")
        self.assertEqual((code, t["columns"], t["rows"]), (200, [], []))

    def test_undecodable_table_is_a_400(self):
        d = self._run("bad_bytes")
        (d / "tables").mkdir(exist_ok=True)
        (d / "tables" / "t.csv").write_bytes(b"a,b\n\xff\xfe,1\n")
        self.assertEqual(_get(RunStore(self.root), "/api/runs/bad_bytes/tables/t")[0], 400)

    def test_malformed_meta_json_leaves_the_run_listed_as_unlabelled(self):
        d = self._run("bad_meta")
        (d / "meta.json").write_text("{not json")
        store = RunStore(self.root)
        listed = {r["id"]: r for r in _get(store, "/api/runs")[2]}
        self.assertEqual(listed["bad_meta"]["origin"], "unlabelled")
        self.assertEqual(_get(store, "/api/runs/bad_meta")[0], 200)

    def test_malformed_manifest_is_a_400_not_silently_dropped_lineage(self):
        d = self._run("bad_manifest")
        (d / "manifest.json").write_text('["not", "an", "object"]')
        code, _, body = _get(RunStore(self.root), "/api/runs/bad_manifest")
        self.assertEqual(code, 400)
        self.assertIn("manifest.json", body["error"])

    def test_corrupt_or_incomplete_panel_is_a_400(self):
        d = self.root / "garbage_panel"
        d.mkdir(exist_ok=True)
        (d / "panel.npz").write_bytes(b"this is not a zip archive")
        self.assertEqual(_get(RunStore(self.root), "/api/runs/garbage_panel")[0], 400)
        d2 = self.root / "short_panel"
        d2.mkdir(exist_ok=True)
        np.savez_compressed(d2 / "panel.npz", iv=self.arrays["iv"])
        code, _, body = _get(RunStore(self.root), "/api/runs/short_panel")
        self.assertEqual(code, 400)
        self.assertIn("lacks required arrays", body["error"])

    def test_missing_spot_is_null_and_the_response_is_strict_json(self):
        spot = self.arrays["spot"].astype(float).copy()
        spot[0] = np.nan
        self._run("nan_spot", spot=spot)
        code, ctype, s = _get(RunStore(self.root), "/api/runs/nan_spot/surface/0")
        self.assertEqual((code, ctype), (200, "application/json"))
        self.assertIsNone(s["spot"])

    def test_symlink_pointing_outside_the_tables_folder_is_not_served(self):
        outside = self.dir / "outside.csv"
        outside.write_text("secret\n1\n")
        d = self._run("linked")
        (d / "tables").mkdir(exist_ok=True)
        try:
            (d / "tables" / "leak.csv").symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks not permitted on this system")
        self.assertEqual(_get(RunStore(self.root), "/api/runs/linked/tables/leak")[0], 404)

    def test_unexpected_reader_error_gives_generic_500_without_paths(self):
        class Broken(RunStore):
            def run_info(self, run_id):
                raise KeyError(str(self.root / "secret-location"))
        code, _, body = _get(Broken(self.root), "/api/runs/anything")
        self.assertEqual(code, 500)
        self.assertEqual(body, {"error": "the run data could not be read"})


class ApiOriginLabelTests(unittest.TestCase):
    """GR-DATA-04: manifest origin is a fallback label; a disagreeing meta.json makes the run 'unlabelled'."""

    def test_manifest_origin_fallback_and_conflict(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "chain.csv"
            make_chain(10, seed=1)[0].to_csv(src, index=False)
            m = ingest(Path(td) / "store", [src], Config(), origin="synthetic")
            root = Path(td) / "store" / "datasets"
            run = root / m["version_id"]
            store = RunStore(root)
            (run / "meta.json").unlink()
            self.assertEqual(_get(store, f"/api/runs/{m['version_id']}")[2]["origin"], "synthetic")
            (run / "meta.json").write_text(json.dumps({"origin": "real", "description": "x"}))
            info = _get(store, f"/api/runs/{m['version_id']}")[2]
            self.assertEqual((info["origin"], info["origin_conflict"]), ("unlabelled", True))


if __name__ == "__main__":
    unittest.main()
