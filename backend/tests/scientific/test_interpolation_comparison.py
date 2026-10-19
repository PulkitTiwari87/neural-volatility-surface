"""Known-answer tests for the Phase 2 comparison harness (surfaces.compare_methods). SYNTHETIC only.

These prove the *harness* is correct and that method rankings are determined by the generating surface -
which is why synthetic results alone cannot decide DEC-006.
"""
import unittest

import numpy as np
import pandas as pd

from volatility_lab.config.settings import Config, SplitConfig
from volatility_lab.datasets.synthetic import make_chain, true_sigma
from volatility_lab.ingestion.optionsdx import RejectLedger, prefilter_batch
from volatility_lab.surfaces import compare_methods as cm

CFG = Config(split=SplitConfig(first_test_year=2020, last_test_year=2020, min_train_years=1))
LIN, TV = "linear_iv", "linear_total_variance (production)"


def _quotes(iv_fn, expiry_days=(14, 21, 28, 35, 42, 49, 56), step=0.01):
    rows = []
    for e in expiry_days:
        T = e / 365.0
        for k in np.round(np.arange(-0.15, 0.1501, step), 10):
            rows.append({"date": 1, "expiry": 1 + e, "T": T, "k": k, "iv": float(iv_fn(k, T))})
    return pd.DataFrame(rows)


def _err(df, name):
    return np.abs(df[df.method == name].err.to_numpy())


class KDirectionKnownAnswer(unittest.TestCase):
    def test_methods_are_exact_for_iv_linear_in_k_except_total_variance(self):
        r = cm.loo_k(_quotes(lambda k, T: 0.20 - 0.5 * k), stride=1)
        self.assertLess(_err(r, "linear_iv (production)").max(), 1e-12)
        self.assertLess(_err(r, "pchip_iv").max(), 1e-12)
        self.assertLess(_err(r, "cubic_spline_iv").max(), 1e-9)
        self.assertGreater(_err(r, "linear_total_variance").max(), 1e-6)   # w is quadratic in k, so the chord is biased

    def test_curvature_gives_linear_a_known_chord_error_and_cubic_none(self):
        curv, h = 2.0, 0.01
        r = cm.loo_k(_quotes(lambda k, T: 0.20 + curv * k * k), stride=1)
        # hiding a node of a parabola and interpolating linearly across 2h gives exactly curv * h^2 at the node
        self.assertAlmostEqual(_err(r, "linear_iv (production)").max(), curv * h * h, places=9)
        self.assertLess(_err(r, "cubic_spline_iv").max(), 1e-9)            # not-a-knot cubic reproduces a quadratic
        self.assertLess(_err(r, "pchip_iv").mean(), _err(r, "linear_iv (production)").mean())

    def test_held_out_quotes_are_interior_so_nothing_extrapolates(self):
        q = _quotes(lambda k, T: 0.2)
        r = cm.loo_k(q, stride=1)
        self.assertTrue(np.isfinite(r.err).all())
        self.assertGreater(r.k.min(), q.k.min())
        self.assertLess(r.k.max(), q.k.max())

    def test_cubic_spline_reports_nan_when_too_few_points(self):
        k = np.array([0.0, 0.1, 0.2]); iv = np.array([0.2, 0.21, 0.22])
        self.assertTrue(np.isnan(cm.k_cubic_spline_iv(k, iv, 0.1, np.array([0.05]))).all())

    def test_outside_the_hull_pchip_and_spline_give_nan_but_np_interp_clamps(self):
        """Documented boundary behaviour: production code must keep its explicit inside-hull mask."""
        k = np.linspace(-0.1, 0.1, 9); iv = 0.2 + k * k
        self.assertTrue(np.isnan(cm.k_pchip_iv(k, iv, 0.1, np.array([0.3]))).all())
        self.assertTrue(np.isnan(cm.k_cubic_spline_iv(k, iv, 0.1, np.array([0.3]))).all())
        self.assertTrue(np.isfinite(cm.k_linear_iv(k, iv, 0.1, np.array([0.3]))).all())   # clamped, hence the mask


class TDirectionKnownAnswer(unittest.TestCase):
    def test_linear_iv_truth_makes_linear_iv_exact_and_total_variance_biased(self):
        r = cm.loo_expiry_t(_quotes(lambda k, T: 0.15 + 0.5 * T), stride=1)
        self.assertLess(_err(r, LIN).max(), 1e-12)
        self.assertGreater(_err(r, TV).max(), 1e-5)

    def test_linear_total_variance_truth_makes_total_variance_exact_and_linear_iv_biased(self):
        # w(T) = a*T + b*T^2 would not be linear; use iv^2 * T = c + d*T  ->  iv = sqrt((c + d T) / T)
        r = cm.loo_expiry_t(_quotes(lambda k, T: np.sqrt((0.002 + 0.03 * T) / T)), stride=1)
        self.assertLess(_err(r, TV).max(), 1e-12)
        self.assertGreater(_err(r, LIN).max(), 1e-5)

    def test_wider_expiry_gap_is_recorded_and_hurts_nearest_expiry_most(self):
        q = _quotes(lambda k, T: 0.15 + 0.5 * T, expiry_days=tuple(range(7, 140, 7)))
        a, b = cm.loo_expiry_t(q, thin=1, stride=3), cm.loo_expiry_t(q, thin=3, stride=3)
        self.assertGreater(b.t_gap.mean(), a.t_gap.mean())
        self.assertGreater(_err(b, "nearest_expiry").mean(), _err(a, "nearest_expiry").mean())


class ReportingTests(unittest.TestCase):
    def test_summary_flags_insufficient_n_and_counts_missing(self):
        df = pd.DataFrame({"method": ["m"] * 4, "k": [0.0, 0.0, 0.0, 0.0], "err": [0.001, -0.002, np.nan, 0.003]})
        s = cm.summarize_by_region(df, min_n=100)
        row = s[(s.method == "m") & (s.region == "ALL")].iloc[0]
        self.assertEqual((row.n, row.n_missing, bool(row.insufficient_n)), (3, 1, True))
        self.assertAlmostEqual(row.mae_vp, 100 * (0.001 + 0.002 + 0.003) / 3, places=9)
        self.assertAlmostEqual(row.rmse_vp, 100 * np.sqrt((1e-6 + 4e-6 + 9e-6) / 3), places=9)

    def test_regions_partition_the_k_axis(self):
        ks = np.array([-0.3, -0.1, -0.05, -0.02, 0.0, 0.019, 0.02, 0.05, 0.1, 0.4])
        s = cm.summarize_by_region(pd.DataFrame({"method": "m", "k": ks, "err": 0.001}), min_n=1)
        self.assertEqual(s[s.region != "ALL"].n.sum(), len(ks))


class FilterPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw, cls.truth = make_chain(25, seed=3, noise_free=False)
        cls.wide = prefilter_batch(cls.raw, CFG.data, RejectLedger())

    def test_stricter_filters_keep_fewer_quotes_and_never_increase_worst_case_error(self):
        r = cm.filter_policy_report(self.wide, self.truth, true_sigma, CFG).set_index("policy")
        default, strict, loose = (r.loc[n] for n in r.index)           # order of FILTER_POLICIES
        self.assertLess(strict.quotes_kept, default.quotes_kept)
        self.assertLess(default.quotes_kept, loose.quotes_kept)
        self.assertLessEqual(strict.quote_max_vp, default.quote_max_vp)
        self.assertLessEqual(default.quote_max_vp, loose.quote_max_vp)
        self.assertGreaterEqual(strict.cells_missing, loose.cells_missing)   # coverage is the price of strictness

    def test_cell_status_shares_sum_to_one(self):
        r = cm.filter_policy_report(self.wide, self.truth, true_sigma, CFG)
        shares = r[[c for c in r.columns if c.startswith("cells_")]].sum(axis=1)
        np.testing.assert_allclose(shares, 1.0, atol=1e-12)

    def test_report_is_deterministic(self):
        a = cm.filter_policy_report(self.wide, self.truth, true_sigma, CFG)
        b = cm.filter_policy_report(self.wide, self.truth, true_sigma, CFG)
        pd.testing.assert_frame_equal(a, b)


if __name__ == "__main__":
    unittest.main()
