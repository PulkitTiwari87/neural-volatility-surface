"""Regression tests added by the Phase 0 audit (POST HOC). SYNTHETIC SPIKE.

F1 near-node status/value defect  - F3 analytic SD  - F4 equal-weight ratio  - F5 bootstrap calibration.
"""
import math
import random
import statistics
import unittest

from phase0.audit import _series, bootstrap_coverage, wilson
from phase0.evaluate import analytic_rel_sd, block_bootstrap_ci, compare, lag1_autocorr, per_origin_mse
from phase0.pipeline import PipelineConfig
from phase0.run import fast_world_config, run_single
from phase0.surface import CellStatus as S
from phase0.surface import SurfaceConfig, build_surface
from phase0.synth import WorldConfig, _normal

NODES = (-0.10, -0.05, 0.0, 0.05, 0.10)


class F1_NearNodeStatusValueConsistency(unittest.TestCase):
    OBS = [[(-0.10, 0.30), (5e-7, 0.20), (0.10, 0.26)]]  # the middle observation sits 5e-7 from the 0.0 node

    def test_default_tolerance_does_not_label_a_near_node_observation_as_observed(self):
        s = build_surface(0, self.OBS, SurfaceConfig(k_nodes=NODES))
        self.assertEqual(SurfaceConfig().tol_k, 1e-9)
        self.assertIs(s.status[0][2], S.INTERPOLATED)
        # linear interpolation corrects for the 5e-7 offset using the local slope (-1/1.0000005 per unit k):
        self.assertAlmostEqual(s.iv[0][2], 0.20 + 5e-7 * (0.10 / 0.1000005), places=12)
        self.assertNotEqual(s.iv[0][2], 0.20)  # NOT the uncorrected copy of the observation's own IV
        self.assertEqual((s.max_snap_dk, s.n_snapped), (0.0, 0))

    def test_v1_tolerance_reproduces_v1_behaviour_and_exposes_the_bias_bound(self):
        s = build_surface(0, self.OBS, SurfaceConfig(k_nodes=NODES, tol_k=1e-6))
        self.assertIs(s.status[0][2], S.OBSERVED)
        self.assertEqual(s.iv[0][2], 0.20)  # v1: value copied from k = 5e-7, not the node
        self.assertAlmostEqual(s.max_snap_dk, 5e-7, places=15)
        self.assertEqual(s.n_snapped, 1)

    def test_exact_node_observation_is_observed_with_zero_snap(self):
        s = build_surface(0, [[(0.0, 0.2)]], SurfaceConfig(k_nodes=NODES))
        self.assertIs(s.status[0][2], S.OBSERVED)
        self.assertEqual((s.max_snap_dk, s.n_snapped), (0.0, 0))

    def test_the_two_v1_failing_seeds_v1_vs_v2(self):
        """RW 20261104 and AR 20261106 failed v1 H-S1 (cell error 1.2e-7 / 4.3e-7). Under v2 they pass; under the v1
        tolerance the failure is reproduced AND explained by the analytic bias bound (H-S1b)."""
        for name, seed, v1_min_err in (("RW", 20261104, 1e-7), ("AR", 20261106, 4e-7)):
            cfg = WorldConfig(name=name, seed=seed, n_days=300)
            v1 = run_single(cfg, PipelineConfig(surface=SurfaceConfig(tol_k=1e-6)), B=100)
            self.assertFalse(v1["hypotheses"]["H-S1_recovery"]["pass"])  # pre-registered failure reproduced
            self.assertGreater(v1["hypotheses"]["H-S1_recovery"]["max_abs_observed_cell_error"], v1_min_err)
            self.assertTrue(v1["hypotheses"]["H-S1b_POST_HOC_bias_bound"]["pass"])  # explained by slope x snap
            v2 = run_single(cfg, B=100)
            self.assertTrue(v2["hypotheses"]["H-S1_recovery"]["pass"])
            self.assertTrue(v2["hypotheses"]["H-S1b_POST_HOC_bias_bound"]["pass"])
            self.assertLessEqual(v2["pipeline_diagnostics"]["node_matching"]["max_snap_dk"], 1e-9)

    def test_consistency_rule_recovery_tolerance_vs_matching_tolerance(self):
        rec = run_single(fast_world_config("RW", 20261012, 60), B=50)
        nm = rec["pipeline_diagnostics"]["node_matching"]
        self.assertLessEqual(nm["max_slope_bound"] * nm["tol_k"], 1e-8)  # default tol_k is consistent with the 1e-8 criterion
        self.assertLessEqual(PipelineConfig().surface.tol_k, 1e-9 * 1.000001)  # slope bound ~1 => bias <= ~1e-9 < 1e-8


class F3_AnalyticSD(unittest.TestCase):
    """The analytic relative SD of realized/expected persistence MSE is checked against Monte Carlo."""

    @staticmethod
    def _records(ks):
        return [{"k": k} for k in ks]

    def test_rw_level_only_equals_sqrt_2_over_n(self):
        self.assertAlmostEqual(analytic_rel_sd(self._records([0.0, 0.1, -0.1]), (0.002, 0.0, 0.0), None, 240),
                               math.sqrt(2.0 / 240), places=12)

    def test_ar_level_only_matches_closed_form(self):
        # g_h/g_0 = -(1-phi) phi^(h-1) / 2 ; factor 1 + 2*sum (g_h/g_0)^2 = 1 + 2 * 0.0625/(1-0.25)
        expected = math.sqrt(2.0 * (1.0 + 2.0 * 0.0625 / 0.75) / 240)
        self.assertAlmostEqual(analytic_rel_sd(self._records([0.0]), (0.002, 0.0, 0.0), 0.5, 240), expected, places=6)

    def _mc_sd(self, sigma, phi, ks, n=240, reps=1500, seed=11):
        rng = random.Random(seed)
        m2 = sum(k * k for k in ks) / len(ks)
        devs = []
        for _ in range(reps):
            mses = []
            if phi is None:
                for _ in range(n):
                    mses.append(sigma[0] ** 2 * _normal(rng) ** 2 + sigma[1] ** 2 * _normal(rng) ** 2 * m2)
                expected = sigma[0] ** 2 + sigma[1] ** 2 * m2
            else:
                xs = [[_normal(rng) * s / math.sqrt(1 - phi ** 2) for s in sigma[:2]]]
                for _ in range(n):
                    xs.append([phi * xs[-1][j] + sigma[j] * _normal(rng) for j in range(2)])
                for t in range(n):
                    mses.append((xs[t + 1][0] - xs[t][0]) ** 2 + (xs[t + 1][1] - xs[t][1]) ** 2 * m2)
                expected = 2.0 / (1.0 + phi) * (sigma[0] ** 2 + sigma[1] ** 2 * m2)
            devs.append(sum(mses) / n / expected - 1.0)
        return statistics.stdev(devs)

    def test_rw_two_factor_analytic_sd_matches_monte_carlo(self):
        ks = [-0.2, -0.1, 0.0, 0.1, 0.2]  # symmetric: mean k = 0 so cross terms vanish
        a = analytic_rel_sd(self._records(ks), (0.002, 0.01, 0.0), None, 240)
        self.assertAlmostEqual(self._mc_sd((0.002, 0.01, 0.0), None, ks), a, delta=0.08 * a)

    def test_ar_two_factor_analytic_sd_matches_monte_carlo(self):
        ks = [-0.2, -0.1, 0.0, 0.1, 0.2]
        a = analytic_rel_sd(self._records(ks), (0.002, 0.01, 0.0), 0.5, 240)
        self.assertAlmostEqual(self._mc_sd((0.002, 0.01, 0.0), 0.5, ks), a, delta=0.08 * a)


class F4_F5_EvaluationBookkeeping(unittest.TestCase):
    @staticmethod
    def _recs(counts, base_err, model_err):
        out = []
        for t, c in enumerate(counts):
            for i in range(c):
                out.append({"t": t, "k": 0.0, "y": 0.2, "pred": {"b": 0.2 + base_err[t], "m": 0.2 + model_err[t]}})
        return out

    def test_origin_mean_ratio_equals_pooled_ratio_when_cells_per_origin_are_equal(self):
        recs = self._recs([4] * 10, [0.02 * (1 + t % 3) for t in range(10)], [0.01 * (1 + t % 3) for t in range(10)])
        c = compare(recs, "b", "m", B=50, seed=1)
        self.assertAlmostEqual(c["mse_ratio"], c["mse_ratio_origin_mean"], places=12)
        self.assertAlmostEqual(c["mse_ratio"], 0.25, places=12)

    def test_origin_mean_ratio_differs_from_pooled_when_origins_are_weighted_differently(self):
        # origin 0: 9 cells, base err 0.02 / model 0.02 ; origin 1: 1 cell, base 0.10 / model 0.01
        recs = self._recs([9, 1], [0.02, 0.10], [0.02, 0.01])
        c = compare(recs, "b", "m", B=50, seed=1)
        pooled = (9 * 0.02 ** 2 + 0.01 ** 2) / (9 * 0.02 ** 2 + 0.10 ** 2)
        origin_mean = ((0.02 ** 2 + 0.01 ** 2) / 2) / ((0.02 ** 2 + 0.10 ** 2) / 2)
        self.assertAlmostEqual(c["mse_ratio"], pooled, places=12)
        self.assertAlmostEqual(c["mse_ratio_origin_mean"], origin_mean, places=12)
        self.assertNotAlmostEqual(c["mse_ratio"], c["mse_ratio_origin_mean"], places=3)

    def test_mean_d_equals_independent_recomputation(self):
        recs = self._recs([3, 5, 2, 4], [0.03, 0.01, 0.05, 0.02], [0.02, 0.02, 0.01, 0.03])
        c = compare(recs, "b", "m", B=50, seed=2)
        lb, lm = per_origin_mse(recs, "b"), per_origin_mse(recs, "m")
        manual = sum(0.2 * 0 + (e_b ** 2 - e_m ** 2) for e_b, e_m in zip((0.03, 0.01, 0.05, 0.02), (0.02, 0.02, 0.01, 0.03))) / 4
        self.assertAlmostEqual(c["mean_d"], manual, places=15)
        self.assertEqual(sorted(lb), sorted(lm))

    def test_lag1_autocorrelation_hand_value(self):
        # d = 1..5: mean 3; numerator (-2)(-1)+(-1)(0)+(0)(1)+(1)(2) = 4 ; denominator 4+1+0+1+4 = 10
        self.assertAlmostEqual(lag1_autocorr([1, 2, 3, 4, 5]), 0.4, places=15)
        self.assertIsNone(lag1_autocorr([1.0, 1.0, 1.0]))

    def test_wilson_interval_hand_values(self):
        lo, hi = wilson(0, 9)
        self.assertEqual(lo, 0.0)
        self.assertAlmostEqual(hi, 0.2991, places=3)  # Wilson upper bound for 0/9
        lo, hi = wilson(5, 200)
        self.assertTrue(0.01 < lo < 0.025 < hi < 0.06)

    def test_bootstrap_percentile_indices_and_ordering(self):
        d = [random.Random(5).random() for _ in range(1)] + [float(i % 7) for i in range(60)]
        mean, lo, hi = block_bootstrap_ci(d, 5, 400, 3)
        self.assertLessEqual(lo, hi)
        self.assertTrue(lo <= mean <= hi)

    def test_bootstrap_coverage_smoke_known_mean_zero(self):
        """Light calibration guard (iid normal, n=100, 300 replications): coverage must be near 95% (4 SE band)."""
        r = bootstrap_coverage("normal", 0.0, n=100, reps=300, B=300, block=5, seed0=9001)
        self.assertGreater(r["coverage"], 0.95 - 4 * r["coverage_se"] * math.sqrt(1000 / 300))
        self.assertLess(r["lo_gt_0_rate"], 0.08)

    def test_series_generator_has_unit_variance_and_requested_autocorrelation(self):
        d = _series("normal", 0.6, 20000, random.Random(3))
        self.assertAlmostEqual(statistics.pvariance(d), 1.0, delta=0.06)
        self.assertAlmostEqual(lag1_autocorr(d), 0.6, delta=0.03)
        sk = _series("skewed", 0.3, 20000, random.Random(4))
        self.assertAlmostEqual(statistics.mean(sk), 0.0, delta=0.06)


if __name__ == "__main__":
    unittest.main()
