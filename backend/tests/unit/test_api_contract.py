"""Phase 5: stable read-only API contract (golden key sets), error-body shape, and no-write guarantee. SYNTHETIC runs.

If a key set changes on purpose, update docs/architecture/API_CONTRACTS.md section 8 and this test together.
"""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from volatility_lab.api.server import dispatch
from volatility_lab.api.service import RunStore
from volatility_lab.config.settings import Config
from volatility_lab.datasets.synthetic import make_chain
from volatility_lab.storage.raw_store import ingest

RUN_LIST = {"id", "origin", "description"}
RUN_INFO = {"id", "origin", "description", "dates", "tenor_days", "k_nodes", "status_labels", "status_counts",
            "tables", "forecasts", "lineage"}
LINEAGE = {"version_id", "config_sha256", "inputs", "ledgers_conserved", "ledger_prefilter", "ledger_quotes",
           "panel_sha256_recorded", "panel_sha256_actual", "panel_hash_matches"}
SURFACE = {"run", "origin", "description", "index", "date", "spot", "n_quotes", "tenor_days", "k_nodes", "iv", "status",
           "iv_units"}
FORECAST = {"run", "origin", "description", "model", "index", "target_date", "origin_date", "horizon_panel_steps",
            "tenor_days", "k_nodes", "actual", "status", "forecast", "difference", "n_difference_cells",
            "n_observed_cells", "mae_observed_vol_points", "iv_units"}
TABLE = {"run", "table", "columns", "truncated", "rows"}


def _get(store, path):
    code, ctype, body = dispatch(store, path)
    return code, ctype, (json.loads(body) if ctype == "application/json" else body)


def _tree_hash(root: Path) -> dict:
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


class ApiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.td = tempfile.TemporaryDirectory()
        d = Path(cls.td.name)
        wide, _ = make_chain(10, seed=1)
        (d / "c.csv").write_text(wide.to_csv(index=False))
        m = ingest(d / "store", [d / "c.csv"], Config(), origin="synthetic")
        cls.root = d / "store" / "datasets"
        cls.id = m["version_id"]
        run = cls.root / cls.id
        with np.load(run / "panel.npz") as z:
            iv = z["iv"]
        n = iv.shape[0]
        (run / "forecasts").mkdir()
        np.savez_compressed(run / "forecasts" / "persistence.npz", target_index=np.arange(1, n),
                            origin_index=np.arange(0, n - 1), pred=iv[:-1])
        (run / "tables").mkdir()
        (run / "tables" / "t.csv").write_text("a,b\n1,2\n")
        cls.store = RunStore(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls.td.cleanup()

    def test_response_key_sets_are_the_documented_contract(self):
        s, rid = self.store, self.id
        self.assertEqual({k for r in _get(s, "/api/runs")[2] for k in r}, RUN_LIST)
        info = _get(s, f"/api/runs/{rid}")[2]
        self.assertEqual(set(info), RUN_INFO)
        self.assertEqual(set(info["lineage"]), LINEAGE)
        self.assertEqual(set(_get(s, f"/api/runs/{rid}/surface/2")[2]), SURFACE)
        self.assertEqual(set(_get(s, f"/api/runs/{rid}/forecasts/persistence/3")[2]), FORECAST)
        self.assertEqual(set(_get(s, f"/api/runs/{rid}/tables/t")[2]), TABLE)

    def test_grid_shapes_are_consistent_with_the_declared_axes(self):
        surf = _get(self.store, f"/api/runs/{self.id}/surface/2")[2]
        T, K = len(surf["tenor_days"]), len(surf["k_nodes"])
        for key in ("iv", "status"):
            self.assertEqual((len(surf[key]), {len(r) for r in surf[key]}), (T, {K}), key)
        fc = _get(self.store, f"/api/runs/{self.id}/forecasts/persistence/3")[2]
        for key in ("actual", "status", "forecast", "difference"):
            self.assertEqual((len(fc[key]), {len(r) for r in fc[key]}), (T, {K}), key)

    def test_labels_carry_the_origin_and_never_claim_real_for_synthetic_runs(self):
        for path in (f"/api/runs/{self.id}", f"/api/runs/{self.id}/surface/1",
                     f"/api/runs/{self.id}/forecasts/persistence/2"):
            self.assertEqual(_get(self.store, path)[2]["origin"], "synthetic", path)

    def test_every_error_body_is_exactly_an_error_message(self):
        for path, code in (("/api/nope", 404), ("/api/runs/missing", 404), (f"/api/runs/{self.id}/surface/99999", 404),
                           ("/api/runs/..", 400), (f"/api/runs/{self.id}/tables/nope", 404),
                           (f"/api/runs/{self.id}/forecasts/nope/2", 404)):
            c, ctype, body = _get(self.store, path)
            self.assertEqual((c, ctype, set(body)), (code, "application/json", {"error"}), path)
            self.assertIsInstance(body["error"], str)
            self.assertNotIn(str(self.root), body["error"])           # no filesystem path in any error

    def test_serving_requests_never_modifies_the_run_directory(self):
        before = _tree_hash(self.root)
        for path in ("/api/runs", f"/api/runs/{self.id}", f"/api/runs/{self.id}/surface/0",
                     f"/api/runs/{self.id}/forecasts/persistence/2", f"/api/runs/{self.id}/tables/t",
                     "/api/runs/nope", "/", "/index.html"):
            dispatch(self.store, path)
        self.assertEqual(_tree_hash(self.root), before)

    def test_json_is_strict_no_nan_or_infinity_tokens(self):
        for path in (f"/api/runs/{self.id}/surface/0", f"/api/runs/{self.id}/forecasts/persistence/2"):
            body = dispatch(self.store, path)[2].decode()
            self.assertNotRegex(body, r"\bNaN\b|\bInfinity\b")


if __name__ == "__main__":
    unittest.main()
