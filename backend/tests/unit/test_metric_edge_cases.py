"""Phase 3 A3 / GR-MOD-02 / GR-MOD-03: metric tables carry n and n_missing; hand-calculated values; degenerate inputs.
SYNTHETIC fixture only."""
import unittest
import warnings

import numpy as np

from volatility_lab.evaluation import metrics as M
from volatility_lab.evaluation.walkforward import make_folds
from volatility_lab.features.panel import target_arrays
from ._fixtures import CFG, pipeline


class MetricTableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = pipeline()["prepared"]
        cls.fold = make_folds(cls.p, CFG.split)[0]
        cls.pos = cls.fold.test
        cls.mask = M.eval_mask(cls.p, cls.pos, "primary")
        cls.y = target_arrays(cls.p)[0][cls.pos]
        cls.cuts = M.rv_terciles(cls.p, cls.fold.train)

    def _pred(self, shift):
        return np.where(self.mask, self.y + shift, np.nan)

    def test_constant_error_gives_the_hand_calculated_metric(self):
        """IV is a decimal; metrics are in vol points (x100). A uniform +0.01 error is exactly 1.0 point."""
        for shift, expect in ((0.01, 1.0), (-0.02, 2.0), (0.0, 0.0)):
            o = M.overall(self.p, self.pos, self._pred(shift), self.mask)
            self.assertAlmostEqual(o["mae"], expect, places=9, msg=shift)
            self.assertAlmostEqual(o["rmse"], expect, places=9, msg=shift)
            self.assertEqual(o["n_cells"], int(self.mask.sum()))

    def test_overall_reports_n_missing_as_the_cells_that_could_not_be_evaluated(self):
        o = M.overall(self.p, self.pos, self._pred(0.01), self.mask)
        self.assertEqual(o["n_cells"] + o["n_missing"], self.mask.size)
        self.assertGreater(o["n_missing"], 0)               # the fixture has missing cells; they are counted, not hidden

    def test_every_group_row_has_n_and_n_missing_that_add_up_to_the_group_population(self):
        brk = M.breakdowns(self.p, self.pos, self._pred(0.01), self.mask, self.cuts)
        self.assertIn("n_missing", brk.columns)
        n_pos = len(self.pos)
        for _, r in brk[brk.group_type == "tenor_days"].iterrows():
            cells = int((self.p.cell_tenor == r.group).sum())
            self.assertEqual(r.n_cells + r.n_missing, n_pos * cells, r.group)
        for _, r in brk[brk.group_type == "log_moneyness"].iterrows():
            cells = int((self.p.cell_k == r.group).sum())
            self.assertEqual(r.n_cells + r.n_missing, n_pos * cells, r.group)
        # a partition of the evaluated cells: tenor groups add up to the evaluated total
        self.assertEqual(int(brk[brk.group_type == "tenor_days"].n_cells.sum()), int(self.mask.sum()))
        self.assertEqual(int(brk[brk.group_type == "origin_year"].n_cells.sum()), int(self.mask.sum()))

    def test_small_groups_are_flagged_not_dropped(self):
        brk = M.breakdowns(self.p, self.pos, self._pred(0.01), self.mask, self.cuts, min_cells=10 ** 9)
        self.assertTrue(brk.insufficient_n.all())
        self.assertEqual(len(brk), len(M.breakdowns(self.p, self.pos, self._pred(0.01), self.mask, self.cuts)))


class DegenerateInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = pipeline()["prepared"]
        cls.fold = make_folds(cls.p, CFG.split)[0]
        cls.pos = cls.fold.test
        cls.y = target_arrays(cls.p)[0][cls.pos]
        cls.cuts = M.rv_terciles(cls.p, cls.fold.train)

    def test_an_empty_mask_gives_nan_metrics_zero_n_and_everything_missing(self):
        mask = np.zeros(self.y.shape, dtype=bool)
        o = M.overall(self.p, self.pos, np.zeros_like(self.y), mask)
        self.assertEqual((o["n_cells"], o["n_days"], o["n_missing"]), (0, 0, mask.size))
        self.assertTrue(np.isnan(o["mae"]) and np.isnan(o["rmse"]))
        brk = M.breakdowns(self.p, self.pos, np.zeros_like(self.y), mask, self.cuts)
        self.assertTrue(brk.insufficient_n.all())
        self.assertTrue((brk.n_cells == 0).all())

    def test_daily_mae_is_nan_on_days_without_evaluable_cells_not_zero(self):
        mask = M.eval_mask(self.p, self.pos, "primary")
        mask[0] = False
        with warnings.catch_warnings():
            warnings.simplefilter("error")                  # an empty day is a legitimate case, not a warning
            d = M.daily_mae(self.p, self.pos, np.where(mask, self.y + 0.01, np.nan), mask)
        self.assertTrue(np.isnan(d[0]))
        self.assertTrue(np.allclose(d[mask.any(axis=1)], 1.0))

    def test_a_nan_prediction_on_an_evaluable_cell_is_visible_not_silently_dropped(self):
        """The evaluation mask must stay identical across models (common sample); a model that fails to predict an
        evaluable cell therefore shows a NaN metric instead of quietly shrinking its own sample."""
        mask = M.eval_mask(self.p, self.pos, "primary")
        pred = np.where(mask, self.y + 0.01, np.nan)
        i, j = np.argwhere(mask)[0]
        pred[i, j] = np.nan
        o = M.overall(self.p, self.pos, pred, mask)
        self.assertTrue(np.isnan(o["mae"]))
        self.assertEqual(o["n_cells"], int(mask.sum()))

    def test_zero_variance_regime_cut_still_partitions_origins(self):
        flat = (0.0, 0.0)                                   # degenerate terciles: low = rv<=0, mid empty, high = rv>0
        mask = M.eval_mask(self.p, self.pos, "primary")
        brk = M.breakdowns(self.p, self.pos, np.where(mask, self.y + 0.01, np.nan), mask, flat)
        reg = brk[brk.group_type == "rv_regime"].set_index("group")
        self.assertEqual(reg.loc["mid", "n_cells"], 0)
        self.assertTrue(reg.loc["mid", "insufficient_n"])


if __name__ == "__main__":
    unittest.main()
