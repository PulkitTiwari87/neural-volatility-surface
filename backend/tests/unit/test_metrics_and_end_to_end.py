import tempfile
import unittest
from pathlib import Path

import numpy as np

from volatility_lab.evaluation import metrics as M
from volatility_lab.evaluation.walkforward import make_folds
from volatility_lab.experiments import runner
from volatility_lab.features.panel import causal_fill, cell_means
from volatility_lab.surfaces.grid import OBSERVED, build_surface_panel
from ._fixtures import CFG, pipeline


class MetricsTests(unittest.TestCase):
    def setUp(self):
        self.P = pipeline()
        self.p = self.P["prepared"]
        self.f = make_folds(self.p, CFG.split)[0]

    def test_mask_requires_observed_target_and_a_real_value_at_the_origin(self):
        m = M.eval_mask(self.p, self.f.test, "primary")
        st = self.p.status[self.p.targets[self.f.test]]
        av = self.p.avail[self.p.origins[self.f.test]]
        self.assertTrue(((st == OBSERVED) & av)[m].all())
        self.assertEqual(m.sum(), ((st == OBSERVED) & av).sum())
        self.assertGreaterEqual(M.eval_mask(self.p, self.f.test, "all").sum(), m.sum())

    def test_mae_rmse_equal_a_hand_computation(self):
        pos = self.f.test[:5]
        y = self.p.iv[self.p.targets[pos]]
        pred = np.where(np.isfinite(y), y + 0.01, 0.0)      # constant +1 vol point error
        m = M.eval_mask(self.p, pos, "all")
        o = M.overall(self.p, pos, pred, m)
        self.assertAlmostEqual(o["mae"], 1.0, places=9)
        self.assertAlmostEqual(o["rmse"], 1.0, places=9)
        self.assertEqual(o["n_cells"], int(m.sum()))
        d = M.daily_mae(self.p, pos, pred, m)
        np.testing.assert_allclose(d[np.isfinite(d)], 1.0)

    def test_regime_cutoffs_come_from_training_origins_only(self):
        lo, hi = M.rv_terciles(self.p, self.f.train)
        self.assertLess(lo, hi)
        r = self.p.rv[self.p.origins[self.f.train], -1]
        self.assertAlmostEqual(lo, float(np.quantile(r[np.isfinite(r)], 1 / 3)))


class EndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.P = pipeline()
        cls.p = cls.P["prepared"]
        cls.folds = make_folds(cls.p, CFG.split)
        cls.preds, cls.chosen = runner.run_baselines(cls.p, cls.folds, CFG, log=lambda *_: None)
        cls.per_fold, cls.pooled, cls.brk, cls.paired = runner.evaluate_all(cls.p, cls.folds, cls.preds)

    def test_exported_forecasts_round_trip_through_the_viewer_api(self):
        from volatility_lab.api.service import RunStore
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "runs" / "r1"
            run.mkdir(parents=True)
            runner.save_panel(self.P["panel"], run / "panel.npz")
            names = runner.export_forecasts(self.p, self.folds, self.preds, run)
            self.assertEqual(names, sorted(self.preds[self.folds[0].test_year]))
            store = RunStore(Path(td) / "runs")
            self.assertEqual(store.run_info("r1")["forecasts"], names)
            f = self.folds[0]
            pos = int(f.test[3])
            tgt, org = int(self.p.targets[pos]), int(self.p.origins[pos])
            out = store.forecast("r1", "persistence", tgt)
            self.assertEqual(out["origin_date"], store.surface("r1", org)["date"])
            self.assertLess(org, tgt)
            # the exported array is the evaluated prediction, cell for cell
            want = self.preds[f.test_year]["persistence"][3].reshape(self.p.n_tenor, self.p.n_k)
            got = np.array([[np.nan if v is None else v for v in r] for r in out["forecast"]])
            np.testing.assert_allclose(got, want, equal_nan=True)
            # dates in the panel are the prepared rows (no row dropped between panel and Prepared)
            self.assertEqual(len(self.P["panel"]["dates"]), len(self.p.dates))
            # every exported (target, origin) pair satisfies the API's no-look-ahead rule for every model
            for n in names:
                with np.load(run / "forecasts" / f"{n}.npz") as z:
                    self.assertTrue((z["origin_index"] < z["target_index"]).all())
                    self.assertEqual(z["pred"].shape[1:], (self.p.n_tenor, self.p.n_k))

    def test_every_model_is_scored_on_exactly_the_same_cells(self):
        for cells, g in self.pooled.groupby("cells"):
            self.assertEqual(g.n_cells.nunique(), 1, cells)
            self.assertEqual(g.n_days.nunique(), 1, cells)

    def test_persistence_has_zero_skill_by_construction_and_others_are_reported_against_it(self):
        row = self.pooled[(self.pooled.model == "persistence") & (self.pooled.cells == "primary")].iloc[0]
        self.assertAlmostEqual(row.mse_skill_vs_persistence, 0.0, places=12)
        self.assertEqual(set(self.pooled.model), {"persistence", "rolling_mean", "ridge", "pca_ridge"})

    def test_breakdowns_cover_tenor_moneyness_year_and_regime_with_counts(self):
        self.assertEqual(set(self.brk.group_type), {"tenor_days", "log_moneyness", "origin_year", "rv_regime"})
        self.assertTrue((self.brk.n_cells >= 0).all())

    def test_small_sample_groups_are_flagged_not_dropped(self):
        self.assertIn("insufficient_n", self.brk.columns)
        self.assertEqual(self.brk.insufficient_n.tolist(), (self.brk.n_cells < M.MIN_CELLS).tolist())
        f = self.folds[0]
        mask = M.eval_mask(self.p, f.test, "primary")
        pred = self.preds[f.test_year]["persistence"]
        strict = M.breakdowns(self.p, f.test, pred, mask, M.rv_terciles(self.p, f.train), min_cells=10 ** 9)
        self.assertTrue(strict.insufficient_n.all())
        self.assertEqual(len(strict), int((self.brk.fold == f.test_year).sum() / self.brk.model.nunique()))

    def test_comparisons_are_descriptive_not_inferential(self):
        cols = " ".join(self.paired.columns).lower() + " ".join(self.pooled.columns).lower()
        for banned in ("p_value", "pvalue", "signific", "confidence", "ci_"):
            self.assertNotIn(banned, cols)

    def test_gap_in_the_calendar_cannot_create_a_fake_horizon(self):
        d = self.p.dates
        self.assertTrue(((d[self.p.targets] - d[self.p.origins]) <= CFG.features.horizon + 4).all())

    def test_artifact_manifest_roundtrip_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            runner.save_panel(self.P["panel"], td / "panel.npz")
            self.pooled.to_csv(td / "pooled.csv", index=False)
            runner.write_manifest(td, {"config_sha256": CFG.sha256()})
            self.assertEqual(runner.verify_manifest(td), [])
            back = runner.load_panel(td / "panel.npz")
            np.testing.assert_array_equal(np.nan_to_num(back["iv"], nan=-1), np.nan_to_num(self.P["panel"]["iv"], nan=-1))
            (td / "pooled.csv").write_text("tampered")
            self.assertTrue(any("hash mismatch" in b for b in runner.verify_manifest(td)))

    def test_data_audit_reports_coverage(self):
        audit = runner.data_audit({"quotes": self.P["quotes"], "panel": self.P["panel"]})
        self.assertEqual(audit["n_surface_dates"], len(self.P["panel"]["dates"]))
        self.assertAlmostEqual(sum(audit["cell_share"].values()), 1.0)

    def test_config_hash_changes_with_any_setting(self):
        import dataclasses
        other = dataclasses.replace(CFG, train=dataclasses.replace(CFG.train, lr=2e-3))
        self.assertNotEqual(CFG.sha256(), other.sha256())


if __name__ == "__main__":
    unittest.main()