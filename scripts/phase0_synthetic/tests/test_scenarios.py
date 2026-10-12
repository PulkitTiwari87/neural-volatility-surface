"""Two SYNTHETIC scenarios: persistence appropriate (World RW) and known predictability (World AR).

Seeds, tolerances and criteria were frozen in docs/research/PHASE0_FEASIBILITY_PLAN.md section 9.4
BEFORE this file was run. Failures here are reported, never tuned away.
"""
import dataclasses
import unittest

from phase0.pipeline import PipelineConfig
from phase0.run import TOL, fast_world_config, run_single
from phase0.surface import SurfaceConfig
from phase0.synth import WorldConfig

SEED_RW, SEED_AR = 20261012, 20261013


class ScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rw = run_single(fast_world_config("RW", SEED_RW, 150))
        cls.ar = run_single(fast_world_config("AR", SEED_AR, 150))

    # ---- H-S1 / H-S2 / H-S3 (both worlds) ----
    def test_iv_recovery_through_the_full_pipeline(self):
        for rec in (self.rw, self.ar):
            h = rec["hypotheses"]["H-S1_recovery"]
            self.assertTrue(h["pass"], h)
            self.assertLessEqual(h["max_abs_observed_cell_error"], TOL["recovery_abs"])
            self.assertGreater(rec["pipeline_diagnostics"]["recovery"]["n_observed_cells_checked"], 1000)

    def test_validation_conserves_and_detects_injected_defects_exactly(self):
        """Fast config. The PRE-REGISTERED strict H-S2 (unalignable == 0) FAILED here: the 30-day slice has ~4.5 strikes
        with both sides, so some expiry-days have < 3 put-call pairs and are (correctly) flagged unalignable.
        What must hold regardless of chain density is the exact accounting identity (POST HOC, disclosed)."""
        for rec in (self.rw, self.ar):
            d = rec["pipeline_diagnostics"]
            self.assertTrue(d["validation"]["conserved_every_day"])
            self.assertTrue(d["defect_counts_match_exactly"])
            self.assertGreater(sum(v for k, v in d["injected_defects"].items()), 20)
            h2a = rec["hypotheses"]["H-S2a_accounting_identity_POST_HOC"]
            self.assertTrue(h2a["pass"], h2a)
            self.assertEqual(h2a["above_bound_detected_by_solver"],
                             h2a["above_bound_injected"] - h2a["above_bound_injected_in_unalignable_expiries"])
            # the strict outcome is reported faithfully, whatever it is
            strict = rec["hypotheses"]["H-S2_conservation_and_defects"]
            self.assertEqual(strict["pass"], d["unalignable_expiries"] == 0 and h2a["pass"]
                             and d["above_bound_injected"] == d["above_bound_detected_by_solver"])
            # unalignable expiries are explicit, never silently filled: those slices have zero observations
            self.assertEqual(d["solver_status_counts"].get("CONVERGED", 0) + d["above_bound_detected_by_solver"],
                             sum(d["solver_status_counts"].values()))  # no other failure status occurs in clean mode

    def test_no_cell_is_extrapolated(self):
        for rec in (self.rw, self.ar):
            self.assertTrue(rec["hypotheses"]["H-S3_no_extrapolation"]["pass"])

    # ---- H-S6 hand-checkable persistence error ----
    def test_persistence_error_matches_analytic_expectation(self):
        for rec in (self.rw, self.ar):
            h = rec["hypotheses"]["H-S6_analytic_persistence_mse"]
            self.assertTrue(h["pass"], h)

    # ---- H-S4: persistence is the appropriate baseline in World RW ----
    def test_rw_world_persistence_is_not_artificially_beaten(self):
        h = self.rw["hypotheses"]["H-S4_persistence_appropriate"]
        self.assertFalse(h["factor_ar1_detected_better"], h)
        self.assertLessEqual(h["oracle_equals_persistence_on_observed_max_abs_gap"], TOL["oracle_equal_abs"])
        self.assertTrue(h["pass"], h)

    # ---- H-S5: known predictability is detected in World AR ----
    def test_ar_world_predictability_is_detected(self):
        h = self.ar["hypotheses"]["H-S5_predictability_detected"]
        self.assertTrue(h["factor_ar1_detected_better"], h)
        lo, hi = TOL["ar1_ratio"]
        self.assertTrue(lo <= h["factor_ar1_mse_ratio"] <= hi, h)
        olo, ohi = TOL["oracle_ratio"]
        self.assertTrue(olo <= h["oracle_mse_ratio"] <= ohi, h)
        self.assertEqual(h["analytic_oracle_ratio"], 0.75)
        self.assertTrue(h["pass"], h)

    # ---- evaluation bookkeeping ----
    def test_walk_forward_covers_expected_origins_and_reports_counts(self):
        for rec in (self.rw, self.ar):
            r = rec["results"]
            self.assertEqual(r["n_origins_evaluated"] + r["n_origins_skipped"], 150 - 1 - 59)
            for name in ("persistence", "factor_ar1", "oracle_ar"):
                m = r["metrics_all"][name]
                self.assertGreater(m["n"], 1000)
                self.assertEqual(m["n"], r["metrics_all"]["persistence"]["n"])  # identical comparable cells
                a, b = r["metrics_group_A_observed_at_t"][name], r["metrics_group_B_interpolated_at_t"][name]
                self.assertEqual(a["n"] + b["n"], m["n"])

    def test_records_are_labelled_synthetic(self):
        for rec in (self.rw, self.ar):
            self.assertEqual(rec["origin"], "synthetic")
            self.assertIn("SYNTHETIC", rec["label"])


class FullConfigPreRegistered(unittest.TestCase):
    """Full configuration (N=300, strike step 0.025): the STRICT pre-registered criteria, same seeds."""

    @classmethod
    def setUpClass(cls):
        cls.rw = run_single(WorldConfig(name="RW", seed=SEED_RW, n_days=300))
        cls.ar = run_single(WorldConfig(name="AR", seed=SEED_AR, n_days=300))

    def test_strict_pre_registered_hypotheses_hold_in_both_worlds(self):
        for rec, key in ((self.rw, "H-S4_persistence_appropriate"), (self.ar, "H-S5_predictability_detected")):
            for h in ("H-S1_recovery", "H-S2_conservation_and_defects", "H-S3_no_extrapolation",
                      "H-S6_analytic_persistence_mse", key):
                self.assertTrue(rec["hypotheses"][h]["pass"], (h, rec["hypotheses"][h]))


class ExploratoryNoiseMode(unittest.TestCase):
    def test_tick_rounded_quotes_degrade_gracefully(self):  # H-S9 (exploratory, loose bound)
        wcfg = dataclasses.replace(fast_world_config("RW", SEED_RW, 70), tick=0.01)
        rec = run_single(wcfg, PipelineConfig(surface=SurfaceConfig(tol_k=5e-4)), B=200)
        med = rec["pipeline_diagnostics"]["recovery"]["median_abs_obs_error"]
        self.assertIsNotNone(med)
        self.assertLess(med, 0.01)
        self.assertIsNone(rec["hypotheses"]["H-S1_recovery"]["pass"])  # tight criteria apply to clean mode only


if __name__ == "__main__":
    unittest.main()
