import unittest

import numpy as np

from volatility_lab.datasets.synthetic import true_sigma
from volatility_lab.evaluation import compare, metrics as M
from volatility_lab.evaluation.walkforward import make_folds
from volatility_lab.experiments import runner
from volatility_lab.features.panel import fixed_expiry_targets, prepare, target_arrays
from volatility_lab.surfaces.grid import build_surface_panel
from ._fixtures import CFG, pipeline


def _tiny_panel(anchor_row0=100, next_slices=None, status0=3, nk=2):
    """3 rows, 1 tenor, ``nk`` nodes; row 0 is anchored on expiry ``anchor_row0``."""
    st = np.zeros((3, 1, nk), dtype=np.int8)
    st[0, 0, :] = status0
    next_slices = next_slices or []
    rows, exps, ivs, gaps = [], [], [], []
    for row, exp, v, g in next_slices:
        rows.append(row)
        exps.append(exp)
        ivs.append(v)
        gaps.append(g)
    return {"iv": np.full((3, 1, nk), 0.2), "status": st, "anchor_expiry": np.array([[anchor_row0], [-1], [-1]]),
            "slice_row": np.array(rows, dtype=np.int64), "slice_expiry": np.array(exps, dtype=np.int64),
            "slice_iv": np.array(ivs, dtype=float).reshape(len(rows), nk),
            "slice_gap": np.array(gaps, dtype=float).reshape(len(rows), nk),
            "k_nodes": np.arange(nk) * 0.01, "tenor_days": np.array([7]), "gap_tight": np.asarray(0.02)}


class TargetDefinitionTests(unittest.TestCase):
    def test_same_expiry_tight_target_is_status_3_and_uses_that_expiry(self):
        pan = _tiny_panel(next_slices=[(1, 100, [0.3, 0.31], [0.005, 0.005]), (1, 107, [0.9, 0.9], [0.005, 0.005])])
        ty, tst = fixed_expiry_targets(pan, 1)
        np.testing.assert_allclose(ty[0], [0.3, 0.31])      # expiry 100, never the other expiry
        self.assertTrue((tst[0] == 3).all())

    def test_expired_or_missing_expiry_is_censored_never_imputed(self):
        pan = _tiny_panel(next_slices=[(1, 107, [0.9, 0.9], [0.005, 0.005])])      # expiry 100 gone on the target row
        ty, tst = fixed_expiry_targets(pan, 1)
        self.assertTrue(np.isnan(ty[0]).all())
        self.assertTrue((tst[0] == 0).all())

    def test_node_outside_the_tracked_slice_is_missing_and_sparse_quotes_downgrade(self):
        pan = _tiny_panel(next_slices=[(1, 100, [0.3, np.nan], [0.005, np.nan])])
        ty, tst = fixed_expiry_targets(pan, 1)
        self.assertEqual(list(tst[0]), [3, 0])
        self.assertTrue(np.isnan(ty[0, 1]))
        loose = _tiny_panel(next_slices=[(1, 100, [0.3, 0.31], [0.05, 0.005])])      # loose bracket on the target date
        self.assertEqual(list(fixed_expiry_targets(loose, 1)[1][0]), [2, 3])

    def test_cell_not_anchored_on_a_real_expiry_has_no_target(self):
        pan = _tiny_panel(anchor_row0=-1, status0=1, next_slices=[(1, 100, [0.3, 0.31], [0.005, 0.005])])
        self.assertTrue((fixed_expiry_targets(pan, 1)[1] == 0).all())
        interp_t = _tiny_panel(status0=1, next_slices=[(1, 100, [0.3, 0.31], [0.005, 0.005])])   # INTERP_T origin
        self.assertTrue((fixed_expiry_targets(interp_t, 1)[1][0] == 0).all())

    def test_unknown_target_name_is_rejected(self):
        with self.assertRaises(ValueError):
            prepare(pipeline()["panel"], CFG.features, "bogus")


class SyntheticKnownAnswerTests(unittest.TestCase):
    def setUp(self):
        self.P = pipeline()
        self.p1 = self.P["prepared"]
        self.p2 = prepare(self.P["panel"], CFG.features, "fixed_expiry")

    def test_nearest_mode_is_unchanged(self):
        self.assertIsNone(self.p1.target_iv)
        y, st = target_arrays(self.p1)
        np.testing.assert_array_equal(y, self.p1.iv[self.p1.targets])
        np.testing.assert_array_equal(st, self.p1.status[self.p1.targets])

    def test_fixed_expiry_target_equals_the_generating_surface_of_the_same_expiry(self):
        panel, truth = self.P["panel"], self.P["truth"]
        lv = dict(zip(truth.date.values.astype("datetime64[D]").astype("int64"), zip(truth["level"], truth["skew"])))
        nk = panel["k_nodes"].size
        ty, tst = target_arrays(self.p2)
        errs = []
        for pos in np.arange(0, len(self.p2.origins), 7):
            t, tt = self.p2.origins[pos], self.p2.targets[pos]
            for c in np.flatnonzero(tst[pos] == 3):
                j, i = divmod(int(c), nk)
                E = panel["anchor_expiry"][t, j]
                T = (E - panel["dates"][tt]) / 365.0
                L, S = lv[int(panel["dates"][tt])]
                errs.append(abs(ty[pos, c] - true_sigma(panel["k_nodes"][i], T, L, S)))
        errs = np.asarray(errs)
        self.assertGreater(errs.size, 500)
        self.assertLess(np.median(errs), 1e-3)
        self.assertLess(np.quantile(errs, 0.99), 6e-3)

    def test_when_the_anchor_did_not_switch_both_targets_coincide(self):
        y1, st1 = target_arrays(self.p1)
        y2, st2 = target_arrays(self.p2)
        same = (~self.p1.anchor_changed) & (st1 == 3) & (st2 == 3)
        self.assertGreater(same.sum(), 1000)
        np.testing.assert_allclose(y1[same], y2[same], atol=1e-12)

    def test_anchor_switches_exist_and_change_the_label_when_expiries_are_dense(self):
        """With daily expiries (as SPY lists today) the nearest expiry changes between dates; E-1 and E-2 then differ."""
        from volatility_lab.datasets.synthetic import make_chain
        from volatility_lab.ingestion.optionsdx import RejectLedger, prefilter_batch
        from volatility_lab.validation.quotes import build_otm_quotes
        raw, _ = make_chain(150, seed=5, expiry_freq="B", max_dte=45, strike_step=2.0)
        wide = prefilter_batch(raw, CFG.data, RejectLedger())
        quotes, _, _ = build_otm_quotes(wide, CFG.data)
        panel = build_surface_panel(quotes, CFG.surface)
        q1 = prepare(panel, CFG.features)
        q2 = prepare(panel, CFG.features, "fixed_expiry")
        y1, st1 = target_arrays(q1)
        y2, st2 = target_arrays(q2)
        sw = q1.anchor_changed & (st1 == 3) & (st2 == 3)
        self.assertGreater(sw.sum(), 100)                               # the E-1 composition effect appears
        self.assertGreater(np.nanmean(np.abs(y1[sw] - y2[sw])), 1e-4)   # ... and changes the label
        same = (~q1.anchor_changed) & (st1 == 3) & (st2 == 3)
        np.testing.assert_allclose(y1[same], y2[same], atol=1e-12)      # ... but only where the anchor switched


class NoLookaheadTests(unittest.TestCase):
    def test_origin_side_quantities_ignore_every_later_quote(self):
        P = pipeline()
        q = P["quotes"]
        panel = P["panel"]
        cut = int(panel["dates"][250])
        q2 = q.copy()
        later = q2.date > cut
        rng = np.random.default_rng(0)
        q2.loc[later, "iv"] = rng.uniform(0.05, 0.9, int(later.sum()))
        panel2 = build_surface_panel(q2, CFG.surface)
        n = int((panel["dates"] <= cut).sum())
        for key in ("status", "anchor_expiry"):
            np.testing.assert_array_equal(panel[key][:n], panel2[key][:n])
        np.testing.assert_array_equal(np.nan_to_num(panel["iv"][:n], nan=-1), np.nan_to_num(panel2["iv"][:n], nan=-1))


class ComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        P = pipeline()
        cls.p1 = P["prepared"]
        cls.p2 = prepare(P["panel"], CFG.features, "fixed_expiry")
        cls.folds = make_folds(cls.p1, CFG.split)
        cls.preds1, _ = runner.run_baselines(cls.p1, cls.folds, CFG, log=lambda *_: None)
        cls.preds2, _ = runner.run_baselines(cls.p2, cls.folds, CFG, log=lambda *_: None)

    def test_both_targets_share_origins_targets_and_folds(self):
        np.testing.assert_array_equal(self.p1.origins, self.p2.origins)
        np.testing.assert_array_equal(self.p1.targets, self.p2.targets)
        self.assertEqual(len(make_folds(self.p2, CFG.split)), len(self.folds))

    def test_coverage_counts_are_consistent(self):
        cov = compare.coverage_by_fold(self.p1, self.p2, self.folds)
        self.assertTrue((cov.e1_eligible == cov.common + cov.e1_only).all())
        self.assertTrue((cov.e2_eligible == cov.common + cov.e2_only).all())
        self.assertTrue((cov.e2_eligible <= cov.e2_anchored_at_origin).all())
        self.assertTrue(((0 <= cov.e1_switch_share) & (cov.e1_switch_share <= 1)).all())

    def test_every_model_is_scored_on_the_same_cells_under_each_target(self):
        per, pooled = compare.paired_on_common(self.p1, self.p2, self.folds, self.preds1, self.preds2)
        for target, g in pooled.groupby("target"):
            self.assertEqual(g.n_cells.nunique(), 1, target)
        a = pooled[pooled.target == "nearest_expiry"].n_cells.iloc[0]
        b = pooled[pooled.target == "fixed_expiry"].n_cells.iloc[0]
        self.assertEqual(a, b)                                        # the common sample is the same for both targets
        for target in ("nearest_expiry", "fixed_expiry"):
            row = pooled[(pooled.model == "persistence") & (pooled.target == target)].iloc[0]
            self.assertAlmostEqual(row.mse_skill_vs_persistence, 0.0, places=12)

    def test_switch_breakdown_partitions_the_primary_cells(self):
        sb = compare.switch_breakdown(self.p1, self.folds, self.preds1)
        self.assertAlmostEqual(sb.share.sum(), 1.0)
        total = sum(M.eval_mask(self.p1, f.test, "primary").sum() for f in self.folds)
        self.assertEqual(int(sb.n_cells.sum()), int(total))

    def test_baselines_and_evaluation_run_on_the_fixed_expiry_target(self):
        per_fold, pooled, brk, paired = runner.evaluate_all(self.p2, self.folds, self.preds2)
        prim = pooled[pooled.cells == "primary"]
        self.assertEqual(prim.n_cells.nunique(), 1)
        self.assertEqual(set(prim.model), {"persistence", "rolling_mean", "ridge", "pca_ridge"})
        self.assertTrue(np.isfinite(prim.rmse).all())


if __name__ == "__main__":
    unittest.main()
