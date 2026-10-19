"""GR-LEAK-02/04/05 sentinel tests on SYNTHETIC panels (fitted baselines, not just feature invariance).

The unit suite already shows features at an origin ignore later data and that the *chosen ridge penalty* ignores
the test year. These tests close the remaining gap: the **fitted model itself** (standardiser, PCA, ridge weights)
must be unchanged when everything after the validation period is scrambled, and the test must be able to fail.
"""
import unittest

import numpy as np

from volatility_lab.evaluation.leakage import perturb_after
from volatility_lab.evaluation.walkforward import Fold, make_folds
from volatility_lab.features.panel import causal_fill, cell_means
from volatility_lab.models import baselines
from tests.unit._fixtures import CFG, pipeline


def _predict(p, fold):
    fv = cell_means(p, np.arange(0, fold.train_rows_end + 1))
    return baselines.predict_baselines(p, fold, causal_fill(p, CFG.features.ffill_days, fv), CFG)


class FittedBaselinesIgnoreThePostValidationFuture(unittest.TestCase):
    def setUp(self):
        self.p = pipeline()["prepared"]
        self.f = make_folds(self.p, CFG.split)[0]
        self.cut = int(self.p.targets[self.f.val].max())          # last row any train/val label touches
        self.q = perturb_after(self.p, self.cut, CFG)               # scramble surfaces, status and spot after it

    def _as_scored_on_validation(self, fold):
        # Score the *validation* origins: their features/labels lie before the cut, so identical outputs on p and q
        # prove the fitted parameters did not read anything after it.
        return Fold(fold.test_year, fold.val_year, fold.train, fold.val, fold.val, fold.train_rows_end)

    def test_every_baseline_prediction_on_pre_cut_origins_is_identical(self):
        g = self._as_scored_on_validation(self.f)
        (out_p, chosen_p), (out_q, chosen_q) = _predict(self.p, g), _predict(self.q, g)
        self.assertEqual(chosen_p, chosen_q)
        self.assertEqual(set(out_p), {"persistence", "rolling_mean", "ridge", "pca_ridge"})
        for name in out_p:
            np.testing.assert_array_equal(out_p[name], out_q[name], err_msg=name)

    def test_the_sentinel_can_fail_training_on_post_cut_origins_changes_predictions(self):
        """Negative control: put test-year origins into the training set and the same comparison must differ."""
        leaky = Fold(self.f.test_year, self.f.val_year, np.r_[self.f.train, self.f.test], self.f.val, self.f.val,
                     int(self.p.targets[self.f.test].max()))
        (out_p, _), (out_q, _) = _predict(self.p, leaky), _predict(self.q, leaky)
        self.assertFalse(np.array_equal(out_p["ridge"], out_q["ridge"]))
        self.assertFalse(np.array_equal(out_p["pca_ridge"], out_q["pca_ridge"]))

    def test_every_fold_keeps_the_test_year_out_of_training_and_validation(self):
        for f in make_folds(self.p, CFG.split):
            yr = self.p.year[self.p.origins]
            self.assertFalse(set(f.test) & (set(f.train) | set(f.val)))
            self.assertTrue((yr[f.test] == f.test_year).all())
            self.assertLess(self.p.dates[self.p.targets[f.train]].max(), self.p.dates[self.p.origins[f.val]].min())
            self.assertLess(self.p.dates[self.p.targets[f.val]].max(), self.p.dates[self.p.origins[f.test]].min())


if __name__ == "__main__":
    unittest.main()
