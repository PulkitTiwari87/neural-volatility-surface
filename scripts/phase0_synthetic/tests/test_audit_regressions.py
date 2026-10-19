"""Regression tests added by the Phase 0 audit (POST HOC). SYNTHETIC SPIKE.

F1 near-node status/value defect  - F3 analytic SD  - F4 equal-weight ratio  - F5 bootstrap calibration.
"""
import json
import math
import random
import statistics
import unittest

from unittest import mock

from phase0.audit import (A2B_CASES, A2B_METHODS, BOOT_OFFSET, PROTOCOL, RESERVED_SEEDS, _overlaps, _series, _stage,
                          bootstrap_coverage, check_prefix, hac_ci, invalid_world_ledger, protocol_sha256, run_sensitivity,
                          select_method, select_trace, stopped_world_days, wilson)
from phase0.run import code_hashes
from phase0.evaluate import analytic_rel_sd, block_bootstrap_ci, compare, lag1_autocorr, per_origin_mse
from phase0.pipeline import PipelineConfig
from phase0.run import fast_world_config, run_single
from phase0.surface import CellStatus as S
from phase0.surface import SurfaceConfig, build_surface
from phase0.synth import WorldConfig, _normal, generate_world

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


class A2b_A6_NewBehaviour(unittest.TestCase):
    """A2b (interval-method sensitivity) and A6 (stopped worlds): hand values, boundary null, refusal to overwrite."""

    def test_hac_hand_value(self):
        # d = [1,-1,1,-1]: mean 0, L = 1, gamma0 = 1, gamma1 = -3/4 -> V = 1 + 2*(1/2)*(-0.75) = 0.25
        m, lo, hi = hac_ci([1.0, -1.0, 1.0, -1.0])
        half = 1.959963984540054 * math.sqrt(0.25 / 4)  # no small-sample factor
        self.assertAlmostEqual(m, 0.0, places=12)
        self.assertAlmostEqual(hi, half, places=12)
        self.assertAlmostEqual(lo, -half, places=12)

    def test_boundary_null_series_are_reproducible_and_have_zero_mean(self):
        self.assertEqual(_series("skewed", 0.3, 50, random.Random(5)), _series("skewed", 0.3, 50, random.Random(5)))
        for case, rho in (("normal", 0.3), ("skewed", 0.3), ("normal", -0.2)):
            means = [statistics.mean(_series(case, rho, 240, random.Random(100 + i))) for i in range(1500)]
            se = statistics.stdev(means) / math.sqrt(len(means))
            self.assertLess(abs(statistics.mean(means)), 4 * se, case)  # true mean is exactly 0

    def test_sensitivity_smoke_structure_and_refusals(self):
        import tempfile
        from pathlib import Path
        from phase0.run import OUT_DIR
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "a2b.json"
            rec = run_sensitivity(out, reps=4, B=40)
            self.assertTrue(out.exists())
            self.assertEqual(len(rec["cases"]), 7)
            self.assertEqual(tuple(rec["cases"][0]["methods"]), A2B_METHODS)
            self.assertIsNone(rec["m0_first1000_regression_vs_stored_A2"])  # needs >= 1000 replications
            self.assertTrue(rec["plumbing_check_only"])  # fewer than 2000 replications: not evidence
            self.assertTrue(rec["analysis"].startswith("PLUMBING CHECK ONLY - NOT EVIDENCE"))
            self.assertFalse(rec["screening_valid"] or rec["formal_valid"])
            self.assertIsNone(rec["selected_by_proposed_rule"])
            with self.assertRaises(SystemExit):
                run_sensitivity(Path(td) / "other.json", reps=2, B=40, methods=["M9_nonsense"])
            with self.assertRaises(SystemExit):
                run_sensitivity(out, reps=4, B=40)  # existing file
        with self.assertRaises(SystemExit):
            run_sensitivity(OUT_DIR / "should_never_exist.json", reps=4, B=40)  # under experiments/
        self.assertFalse((OUT_DIR / "should_never_exist.json").exists())

    def test_m0_inside_sensitivity_is_the_unchanged_a2_bootstrap(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as td:
            rec = run_sensitivity(Path(td) / "a2b.json", reps=12, B=40)
        for c in rec["cases"]:
            if c["n"] != 240 or c["case"] != "normal" or c["rho_z"] not in (0.0, 0.3):
                continue
            a2 = bootstrap_coverage(c["case"], c["rho_z"], n=240, reps=12, B=40, block=5, seed0=7001)
            m0 = c["methods"]["M0_block5"]
            self.assertEqual((m0["coverage"], m0["lo_gt_0_rate"]), (a2["coverage"], a2["lo_gt_0_rate"]))

    def test_hac_lag_truncates_dependence_like_a_block_of_length_lag_plus_one(self):
        # Independent derivation: Bartlett(L) long-run variance of unit-variance AR(1) = 1 + 2 sum (1 - j/(L+1)) rho^j
        rho, L = 0.6, 4
        expected = 1 + 2 * sum((1 - j / (L + 1)) * rho ** j for j in range(1, L + 1))  # 2.6165, vs the full (1+rho)/(1-rho) = 4
        d = _series("normal", rho, 200000, random.Random(21))
        _, lo, hi = hac_ci(d, L)
        implied = ((hi - lo) / 2 / 1.959963984540054) ** 2 * len(d)
        self.assertAlmostEqual(implied, expected, delta=0.06 * expected)

    def test_skewed_case_dependence_is_rho_squared_not_rho(self):
        self.assertAlmostEqual(lag1_autocorr(_series("skewed", 0.3, 200000, random.Random(11))), 0.09, delta=0.02)
        self.assertAlmostEqual(lag1_autocorr(_series("skewed", math.sqrt(0.3), 200000, random.Random(12))), 0.30, delta=0.03)
        eff = {c[0]: (c[2] ** 2 if c[1] == "skewed" else c[2]) for c in A2B_CASES}
        self.assertAlmostEqual(eff["G4"], 0.09, places=12)
        self.assertAlmostEqual(eff["G5"], 0.30, places=12)

    def test_selection_is_calibration_first_not_narrowest_wins(self):
        stats = {"M0_block5": {"admissible": True, "geo": 1.00, "max_lo": 0.034},   # narrowest, closest to the gate
                 "M1_block10": {"admissible": True, "geo": 1.10, "max_lo": 0.027},  # slightly wider, better calibrated
                 "M2_block20": {"admissible": True, "geo": 1.60, "max_lo": 0.020},  # beyond the width cap
                 "M3_hac_L4": {"admissible": False, "geo": 0.90, "max_lo": 0.030}}  # narrower still but fails the gate
        self.assertEqual(select_method(stats), "M1_block10")
        stats["M1_block10"]["max_lo"] = 0.0306  # now within one tie band (0.35 pp) of M0's 0.034 -> tie -> lowest ID wins
        self.assertEqual(select_method(stats), "M0_block5")
        self.assertIsNone(select_method({m: dict(v, admissible=False) for m, v in stats.items()}))

    def test_stopping_rule_and_prefix_property(self):
        self.assertEqual(stopped_world_days("RW", 20262012, n_max=40), 40)  # valid world: not stopped
        self.assertEqual(stopped_world_days("RW", 20262096, n_max=300), 128)  # invalid A3 world: guard fires on day 128
        with self.assertRaises(ValueError):
            generate_world(WorldConfig(name="RW", seed=20262096, n_days=129))
        generate_world(WorldConfig(name="RW", seed=20262096, n_days=128))  # must not raise
        chk = check_prefix("RW", 20262096, 128)  # full world only generable with the guard bypassed
        self.assertTrue(chk["factors_equal"] and chk["spots_equal"] and chk["days_equal"])


class PA4_Ledger_and_A2b_Safeguards(unittest.TestCase):
    """PA-4 reporting format (R1-R5, R6 kept separate) and extra A2b safeguards. Reporting-format tests do not validate any method."""

    def test_ledger_hand_values_for_the_a3_rw_counts(self):
        inv = [{"world": "RW", "seed": 20262000 + i} for i in range(10)]
        r = invalid_world_ledger(200, 190, 3, inv)
        self.assertEqual((r["R1"]["attempted"], r["R1"]["valid"], r["R1"]["invalid"]), (200, 190, 10))
        self.assertAlmostEqual(r["R1"]["invalid_rate"], 0.05, places=12)
        self.assertEqual(r["R2"]["reason_counts"], {"IMPLAUSIBLE_IV": 10})
        self.assertEqual(r["R3"]["label"], "conditional on world validity")
        self.assertAlmostEqual(r["R3"]["rate"], 3 / 190, places=12)
        self.assertEqual(r["R4"]["unconditional_rate_bounds"], [0.015, 0.065])
        self.assertEqual(r["R4"]["wilson95_union"], [wilson(3, 200)[0], wilson(13, 200)[1]])
        be = r["R5"]["break_even_invalid_world_detection_rate"]
        self.assertAlmostEqual(be["for_2.5pct"], 0.2, places=12)
        self.assertAlmostEqual(be["for_5pct"], 0.7, places=12)
        tab = r["R5"]["unconditional_rate_by_invalid_world_detection_rate"]
        self.assertAlmostEqual(tab["0.0"], 0.015, places=12)
        self.assertAlmostEqual(tab["0.2"], 0.025, places=12)
        self.assertAlmostEqual(tab["1.0"], 0.065, places=12)

    def test_ledger_zero_invalid_and_inconsistent_counts(self):
        r = invalid_world_ledger(200, 200, 200, [])
        self.assertIsNone(r["R5"]["break_even_invalid_world_detection_rate"]["for_2.5pct"])
        self.assertEqual(r["R4"]["unconditional_rate_bounds"], [1.0, 1.0])
        self.assertEqual(r["R2"]["reason_counts"], {"IMPLAUSIBLE_IV": 0})
        for bad in ((10, 11, 0), (10, 8, 9), (10, 8, 1, [{"world": "RW", "seed": 1}])):
            with self.assertRaises(ValueError):
                invalid_world_ledger(*bad)

    def test_ledger_cli_is_read_only_and_never_pools_a6(self):
        import contextlib, io, tempfile
        from pathlib import Path
        from phase0.audit import main
        w = lambda nv, det: {"n_valid": nv, "detections": det}
        a3 = {"summary": {"n_seeds": 20, "RW": w(18, 1), "AR": w(20, 20),
                          "invalid_worlds": [{"world": "RW", "seed": 1}, {"world": "RW", "seed": 2}]}}
        a6 = {"attempted": 2, "completed": 2, "failed": 0, "detections": 2, "detection_wilson95": [0.3, 1.0],
              "stopping_rule": "x", "note": "do not pool"}
        with tempfile.TemporaryDirectory() as td:
            p3, p6 = Path(td) / "a3.json", Path(td) / "a6.json"
            p3.write_text(json.dumps(a3))
            p6.write_text(json.dumps(a6))
            before = sorted(x.name for x in Path(td).iterdir())
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(main(["ledger", "--a3", str(p3), "--a6", str(p6)]), 0)
            self.assertEqual(before, sorted(x.name for x in Path(td).iterdir()))  # nothing written
        out = json.loads(buf.getvalue())
        self.assertEqual(out["RW"]["R3"]["detections"], 1)  # A6's 2 detections must not leak in
        self.assertEqual(out["RW"]["R4"]["unconditional_rate_bounds"], [0.05, 0.15])
        self.assertEqual(out["R6_stopped_worlds_A6"]["detections"], 2)
        self.assertFalse(any("pool" in k or "combined" in k for k in out["RW"]))

    def test_sensitivity_is_deterministic_and_records_its_settings(self):
        import tempfile
        from pathlib import Path

        def strip(x):
            if isinstance(x, dict):
                return {k: strip(v) for k, v in x.items() if k not in ("seconds",)}
            if isinstance(x, list):
                return [strip(v) for v in x]
            return x
        with tempfile.TemporaryDirectory() as td:
            a = run_sensitivity(Path(td) / "a.json", reps=3, B=30, seed0=50001)
            b = run_sensitivity(Path(td) / "b.json", reps=3, B=30, seed0=50001)
        self.assertEqual(strip(a), strip(b))
        for k in ("label", "analysis", "config", "code_sha256", "python", "null", "verdict", "plumbing_check_only"):
            self.assertIn(k, a)
        self.assertEqual(a["config"]["seed0"], 50001)
        self.assertEqual(tuple(a["config"]["methods"]), A2B_METHODS)
        for k in ("reps", "B", "screen", "formal_one_sided_95", "width_cap", "tie", "cases"):
            self.assertIn(k, a["config"])
        for c in a["cases"]:
            self.assertEqual(c["replications"], {"attempted": 3, "completed": 3, "invalid": 0})

    def test_confirmation_seeds_may_not_reuse_screening_or_a2_seeds(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as td:
            for bad in (8001, 5000, 9000):
                with self.assertRaises(SystemExit):
                    run_sensitivity(Path(td) / ("x%d.json" % bad), reps=3000 if bad == 5000 else 5000, B=30, seed0=bad)
            run_sensitivity(Path(td) / "ok.json", reps=2, B=30, seed0=50001)  # fresh range is accepted
        lo, hi = RESERVED_SEEDS
        self.assertTrue(20001 > hi and 20001 + 5000 - 1 > hi)  # the proposed confirmation range 20001..25000 is disjoint


class A2b_FrozenProtocol(unittest.TestCase):
    """Frozen A2b-v1 behaviour: seeds, selection determinism, stage separation, confirmation cannot re-select."""

    @staticmethod
    def _ranges(s):
        return [(s["seed0"], s["seed0"] + s["reps"] - 1), (s["seed0"] + BOOT_OFFSET, s["seed0"] + BOOT_OFFSET + s["reps"] - 1)]

    def test_frozen_confirmation_seeds_are_disjoint_from_screening_and_a2(self):
        scr, conf = self._ranges(PROTOCOL["screening"]), self._ranges(PROTOCOL["confirmation"])
        self.assertEqual(scr, [(7001, 9000), (107001, 109000)])
        self.assertEqual(conf, [(20001, 24999 + 1), (120001, 125000)])
        for a in scr + [(7001, 8000), (107001, 108000)]:  # screening and the stored A2 (series and bootstrap seeds)
            for b in conf:
                self.assertFalse(_overlaps(a, b), (a, b))
        self.assertTrue(set(range(*(scr[0][0], scr[0][1] + 1))).isdisjoint(range(conf[0][0], conf[0][1] + 1)))

    def test_selection_rule_is_deterministic_and_boundaries_are_inclusive(self):
        base = {"M0_block5": {"admissible": True, "geo": 1.0, "max_lo": 0.0340},
                "M1_block10": {"admissible": True, "geo": 1.0, "max_lo": 0.0305}}
        self.assertEqual(select_trace(base)["selected"], "M0_block5")  # exactly 0.0035 apart: tie -> lowest identifier
        base["M1_block10"]["max_lo"] = 0.03049
        self.assertEqual(select_trace(base)["selected"], "M1_block10")  # just outside the tie band
        base["M1_block10"].update(geo=1.5, max_lo=0.010)
        self.assertEqual(select_trace(base)["selected"], "M1_block10")  # exactly 1.5x the narrowest: inside the cap
        base["M1_block10"]["geo"] = 1.5001
        self.assertEqual(select_trace(base)["selected"], "M0_block5")  # beyond the cap
        shuffled = dict(reversed(list(base.items())))
        self.assertEqual(select_trace(shuffled), select_trace(base))  # independent of dict order
        self.assertEqual(select_trace(base), select_trace(base))
        none = {m: dict(v, admissible=False) for m, v in base.items()}
        self.assertEqual(select_trace(none)["selected"], None)  # no admissible method: no selection

    def test_stage_is_determined_by_the_frozen_settings_only(self):
        s, c = PROTOCOL["screening"], PROTOCOL["confirmation"]
        self.assertEqual(_stage(s["reps"], s["B"], s["seed0"], A2B_METHODS), "screening")
        self.assertEqual(_stage(c["reps"], c["B"], c["seed0"], ("M1_block10",)), "confirmation")
        self.assertEqual(_stage(c["reps"], c["B"], c["seed0"], ("M1_block10", "M0_block5")), "exploratory")  # two methods: no confirmation
        self.assertEqual(_stage(s["reps"], 500, s["seed0"], A2B_METHODS), "exploratory")
        self.assertEqual(_stage(2500, s["B"], s["seed0"], A2B_METHODS), "exploratory")
        self.assertEqual(_stage(10, s["B"], s["seed0"], A2B_METHODS), "plumbing")

    def test_non_protocol_runs_carry_no_selection_and_no_formal_verdict(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as td:
            rec = run_sensitivity(Path(td) / "p.json", reps=3, B=30, seed0=50001)
        self.assertEqual(rec["stage"], "plumbing")
        self.assertFalse(rec["protocol_conformant"])
        self.assertIsNone(rec["selected_by_proposed_rule"])
        self.assertTrue(all(v["formal_pass"] is None for v in rec["verdict"].values()))
        self.assertEqual(rec["schema"], "A2b-v1")
        self.assertEqual(rec["protocol_sha256"], protocol_sha256())
        self.assertIn("NOT a certification", rec["config"]["threshold_semantics"]["screen"])
        self.assertIn("only certification criterion", rec["config"]["threshold_semantics"]["formal"])
        self.assertEqual(rec["config"]["series_seeds"], [50001, 50003])

    def test_screening_stage_is_void_when_m0_does_not_reproduce_a2(self):
        import tempfile
        from pathlib import Path
        with mock.patch.dict(PROTOCOL, {"screening": {"seed0": 7001, "reps": 4, "B": 30}}):
            with tempfile.TemporaryDirectory() as td:
                rec = run_sensitivity(Path(td) / "s.json", reps=4, B=30, seed0=7001)  # 4 reps cannot reproduce the 1000-rep A2
        self.assertEqual(rec["stage"], "screening")
        self.assertIsNotNone(rec["void_reason"])
        self.assertFalse(rec["screening_valid"])
        self.assertIsNone(rec["selected_by_proposed_rule"])
        self.assertEqual(rec["outcome"], "VOID")

    def test_no_other_run_may_touch_the_single_use_confirmation_seeds(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as td:
            for kw in (dict(reps=3, B=30, seed0=20001), dict(reps=5000, B=1000, seed0=20001), dict(reps=3, B=30, seed0=19999)):
                with self.assertRaises(SystemExit) as cm:
                    run_sensitivity(Path(td) / "x.json", **kw)  # plumbing or exploratory on the confirmation range
                self.assertIn("reserved single-use confirmation seeds", str(cm.exception))
            self.assertFalse((Path(td) / "x.json").exists())

    def test_confirmation_is_single_method_linked_to_its_screening_record_and_single_use(self):
        import tempfile
        from pathlib import Path
        tiny = {"confirmation": {"seed0": 20001, "reps": 3, "B": 30}}
        with mock.patch.dict(PROTOCOL, tiny), tempfile.TemporaryDirectory() as td:
            td = Path(td)
            scr = {"schema": "A2b-v1", "stage": "screening", "protocol_conformant": True, "void_reason": None,
                   "protocol_sha256": protocol_sha256(), "code_sha256": code_hashes(), "selected_by_proposed_rule": "M3_hac_L4"}
            sp = td / "screening.json"
            sp.write_text(json.dumps(scr))
            kw = dict(reps=3, B=30, seed0=20001)
            with self.assertRaises(SystemExit):  # no screening record
                run_sensitivity(td / "c0.json", methods=["M3_hac_L4"], **kw)
            with self.assertRaises(SystemExit) as cm:  # a different method than the screening selected
                run_sensitivity(td / "c1.json", methods=["M1_block10"], screening=sp, **kw)
            self.assertIn("replacement method cannot be chosen", str(cm.exception))
            bad = dict(scr, code_sha256={"audit.py": "0" * 64})
            (td / "badcode.json").write_text(json.dumps(bad))
            with self.assertRaises(SystemExit):  # screening produced by different code
                run_sensitivity(td / "c2.json", methods=["M3_hac_L4"], screening=td / "badcode.json", **kw)
            with self.assertRaises(SystemExit):  # --screening outside the confirmation stage
                run_sensitivity(td / "c3.json", reps=3, B=30, seed0=7001, screening=sp)
            self.assertFalse(list(td.glob("*.confirmation_used")))  # nothing was claimed by the refused attempts
            rec = run_sensitivity(td / "c4.json", methods=["M3_hac_L4"], screening=sp, **kw)
            self.assertEqual(rec["stage"], "confirmation")
            self.assertTrue(rec["formal_valid"])
            self.assertIsNone(rec["selected_by_proposed_rule"])  # confirmation never selects
            self.assertIn("forbidden", rec["outcome"]["replacement_selection"])
            self.assertEqual(rec["confirmation_link"]["screening_selected"], "M3_hac_L4")
            self.assertIsNone(rec["verdict"]["M3_hac_L4"]["screening_admissible"])
            self.assertEqual(len(rec["outcome"]["per_case"]), 5)  # five gating cases
            with self.assertRaises(SystemExit) as cm:  # the confirmation seeds are single-use
                run_sensitivity(td / "c5.json", methods=["M3_hac_L4"], screening=sp, **kw)
            self.assertIn("already claimed", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
