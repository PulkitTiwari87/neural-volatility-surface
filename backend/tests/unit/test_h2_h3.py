"""Experiments H2 (tail-fraction validation) and H3 (calendar features): split purity, causality, shapes."""
import unittest

import numpy as np
import pandas as pd

from volatility_lab.evaluation.walkforward import assert_no_overlap, make_folds
from volatility_lab.experiments import runner
from volatility_lab.features.panel import calendar_block, prepare, sequence_features, tabular_features, trailing_mean
from volatility_lab.experiments.runner import pca_factor_targets
from ._fixtures import CFG, pipeline


class TailFractionFoldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = pipeline()["prepared"]
        cls.old = make_folds(cls.p, CFG.split)
        cls.new = make_folds(cls.p, CFG.split, "tail_frac", 0.2)

    def test_same_test_sets_and_chronological_purged_sets(self):
        self.assertEqual([f.test_year for f in self.new], [f.test_year for f in self.old])
        for a, b in zip(self.old, self.new):
            np.testing.assert_array_equal(a.test, b.test)
            assert_no_overlap(self.p, b)
            self.assertLess(b.train.max(), b.val.min())

    def test_validation_is_about_a_fifth_of_the_pool(self):
        for f in self.new:
            share = len(f.val) / (len(f.val) + len(f.train))
            self.assertTrue(0.15 < share < 0.25, share)

    def test_default_mode_is_unchanged_and_bad_mode_rejected(self):
        for a, b in zip(self.old, make_folds(self.p, CFG.split, "prev_year")):
            np.testing.assert_array_equal(a.val, b.val)
        with self.assertRaises(ValueError):
            make_folds(self.p, CFG.split, "nope")


class CalendarFeatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        P = pipeline()
        cls.panel = P["panel"]
        cls.p0 = P["prepared"]
        cls.p3 = prepare(cls.panel, CFG.features, "nearest_expiry", calendar=True)

    def test_block_shape_weekday_one_hot_and_dte_matches_anchor(self):
        cal = calendar_block(self.panel)
        n, nt = self.panel["anchor_expiry"].shape
        self.assertEqual(cal.shape, (n, nt + 5))
        self.assertTrue((cal[:, nt:].sum(axis=1) <= 1).all())
        d = self.panel["dates"].astype("datetime64[D]")
        mon_to_fri = (d.astype("datetime64[D]").astype(int) + 3) % 7
        np.testing.assert_array_equal(pd.DatetimeIndex(d).dayofweek, mon_to_fri)
        a = self.panel["anchor_expiry"]
        ok = a >= 0
        np.testing.assert_array_equal(cal[:, :nt][ok], (a - self.panel["dates"][:, None])[ok])
        np.testing.assert_array_equal(cal[:, :nt][~ok], np.broadcast_to(self.panel["tenor_days"], a.shape)[~ok])

    def test_features_gain_exactly_the_calendar_columns_and_causal(self):
        filled = np.nan_to_num(self.p0.iv, nan=0.2)
        extra = self.panel["anchor_expiry"].shape[1] + 5
        self.assertEqual(tabular_features(self.p3, filled, CFG.features).shape[1],
                         tabular_features(self.p0, filled, CFG.features).shape[1] + extra)
        self.assertEqual(sequence_features(self.p3, filled, CFG.features).shape[2],
                         sequence_features(self.p0, filled, CFG.features).shape[2] + extra)
        self.assertIsNone(self.p0.calendar)
        t = self.p3.origins[40]
        panel2 = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in self.panel.items()}
        panel2["anchor_expiry"][t + 1:] = -1
        np.testing.assert_array_equal(calendar_block(panel2)[: t + 1], calendar_block(self.panel)[: t + 1])

    def test_baselines_run_with_calendar_features(self):
        folds = make_folds(self.p3, CFG.split)
        preds, _ = runner.run_baselines(self.p3, folds, CFG, log=lambda *_: None)
        self.assertTrue({"persistence", "ridge", "pca_ridge"} <= set(preds[folds[0].test_year]))


class MeanReversionAndFactorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        P = pipeline()
        cls.panel, cls.p0 = P["panel"], P["prepared"]
        cls.p4 = prepare(cls.panel, CFG.features, "fixed_expiry", calendar=True, mr_window=20)

    def test_trailing_mean_is_causal(self):
        a = np.random.default_rng(0).normal(size=(60, 3))
        b = a.copy(); b[40:] = 999.0
        np.testing.assert_allclose(trailing_mean(a, 20)[:40], trailing_mean(b, 20)[:40])

    def test_mr_block_adds_one_surface_width_and_default_is_off(self):
        filled = np.nan_to_num(self.p0.iv, nan=0.2)
        base = tabular_features(prepare(self.panel, CFG.features, "fixed_expiry", calendar=True), filled, CFG.features)
        mr = tabular_features(self.p4, filled, CFG.features)
        self.assertEqual(mr.shape[1], base.shape[1] + filled.shape[1])
        self.assertIsNone(self.p0.mr_window)

    def test_baselines_run_with_mr(self):
        folds = make_folds(self.p4, CFG.split)
        preds, _ = runner.run_baselines(self.p4, folds, CFG, log=lambda *_: None)
        self.assertIn("pca_ridge", preds[folds[0].test_year])

    def test_factor_targets_use_training_rows_only_and_reconstruct(self):
        rng = np.random.default_rng(1)
        s = rng.normal(size=(50, 8)); D = rng.normal(size=(50, 8)); M = rng.random((50, 8)) > 0.2
        Dz, Mz, V = pca_factor_targets(s, D, M, np.arange(30), 3)
        s2 = s.copy(); s2[30:] = 123.0                    # later rows must not change the basis
        _, _, V2 = pca_factor_targets(s2, D, M, np.arange(30), 3)
        np.testing.assert_allclose(np.abs(V), np.abs(V2))
        self.assertEqual((Dz.shape, Mz.shape, V.shape), ((50, 3), (50, 3), (3, 8)))
        np.testing.assert_allclose(V @ V.T, np.eye(3), atol=1e-10)
        np.testing.assert_allclose(Dz, np.where(M, D, 0.0) @ V.T)
