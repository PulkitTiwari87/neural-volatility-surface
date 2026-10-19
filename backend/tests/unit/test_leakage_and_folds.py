import dataclasses
import unittest

import numpy as np

from volatility_lab.evaluation.walkforward import Fold, assert_no_overlap, make_folds
from volatility_lab.features.panel import (causal_fill, cell_means, realized_vol, sequence_features,
                                           tabular_features, Prepared)
from volatility_lab.evaluation.leakage import feature_invariance_check, perturb_after
from volatility_lab.models import baselines
from ._fixtures import CFG, pipeline


def _perturb_after(p, row, seed=0):
    return perturb_after(p, row, CFG, seed)


class LeakageTests(unittest.TestCase):
    def setUp(self):
        self.p = pipeline()["prepared"]

    def test_features_at_an_origin_ignore_everything_after_it(self):
        p, cfg = self.p, CFG.features
        t0 = 300
        q = _perturb_after(p, t0)
        rows = np.arange(0, t0 + 1)
        fv = cell_means(p, rows)
        np.testing.assert_array_equal(fv, cell_means(q, rows))
        f1, f2 = causal_fill(p, cfg.ffill_days, fv), causal_fill(q, cfg.ffill_days, fv)
        np.testing.assert_array_equal(f1[: t0 + 1], f2[: t0 + 1])
        sel = p.origins <= t0
        np.testing.assert_array_equal(tabular_features(p, f1, cfg)[sel], tabular_features(q, f2, cfg)[sel])
        np.testing.assert_array_equal(sequence_features(p, f1, cfg)[sel], sequence_features(q, f2, cfg)[sel])
        self.assertGreater(sel.sum(), 100)

    def test_library_invariance_audit_passes_and_would_catch_a_leak(self):
        self.assertTrue(feature_invariance_check(self.p, CFG)["passed"])
        # a deliberately leaky feature (uses the NEXT row) must make the same comparison fail
        p, cfg = self.p, CFG
        row = 300
        q = _perturb_after(p, row)
        fv = cell_means(p, np.arange(0, row + 1))
        leaky1 = causal_fill(p, cfg.features.ffill_days, fv)[p.origins + 1]
        leaky2 = causal_fill(q, cfg.features.ffill_days, fv)[q.origins + 1]
        sel = p.origins <= row
        self.assertFalse(np.array_equal(leaky1[sel], leaky2[sel]))

    def test_causal_fill_expires_after_ffill_days_and_never_looks_ahead(self):
        p = self.p
        small = dataclasses.replace(p, iv=np.array([[0.2], [np.nan], [np.nan], [np.nan], [0.3]]),
                                    status=np.array([[3], [0], [0], [0], [3]], dtype=np.int8),
                                    avail=np.array([[True], [False], [False], [False], [True]]))
        out = causal_fill(small, ffill_days=2, fill_values=np.array([0.99]))
        np.testing.assert_allclose(out[:, 0], [0.2, 0.2, 0.2, 0.99, 0.3])   # 0.3 never leaks backwards

    def test_realised_vol_uses_only_the_past(self):
        s = np.exp(np.cumsum(np.random.default_rng(0).normal(0, 0.01, 80)))
        a = realized_vol(s, (5, 20))
        s2 = s.copy(); s2[60:] *= 3
        np.testing.assert_array_equal(a[:60], realized_vol(s2, (5, 20))[:60])

    def test_folds_are_chronological_and_purged(self):
        folds = make_folds(self.p, CFG.split)
        for f in folds:
            assert_no_overlap(self.p, f)
            yr = self.p.year[self.p.origins]
            self.assertTrue((yr[f.train] < f.val_year).all())
            self.assertTrue((yr[f.val] == f.val_year).all())
            self.assertTrue((yr[f.test] == f.test_year).all())

    def test_overlap_is_detected(self):
        f = make_folds(self.p, CFG.split)[0]
        bad = Fold(f.test_year, f.val_year, np.r_[f.train, f.val[:3]], f.val, f.test, f.train_rows_end)
        with self.assertRaises(AssertionError):
            assert_no_overlap(self.p, bad)

    def test_hyperparameter_selection_never_reads_the_test_year(self):
        p = self.p
        f = make_folds(p, CFG.split)[0]
        last_pre_test = int(p.targets[f.val].max())
        q = _perturb_after(p, last_pre_test)                  # scrambles the test year entirely
        fv = cell_means(p, np.arange(0, f.train_rows_end + 1))
        _, chosen_a = baselines.predict_baselines(p, f, causal_fill(p, CFG.features.ffill_days, fv), CFG)
        _, chosen_b = baselines.predict_baselines(q, f, causal_fill(q, CFG.features.ffill_days, fv), CFG)
        self.assertEqual(chosen_a, chosen_b)

    def test_no_fold_when_the_split_cannot_be_satisfied(self):
        from volatility_lab.config.settings import SplitConfig
        with self.assertRaises(ValueError):
            make_folds(self.p, SplitConfig(first_test_year=2018, last_test_year=2018, min_train_years=3))


if __name__ == "__main__":
    unittest.main()