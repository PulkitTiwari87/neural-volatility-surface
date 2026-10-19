"""Tests for the A2d diagnostic (diagnostics/a2d.py). SYNTHETIC. Plumbing runs only; the frozen run is not executed here."""
import copy
import json
import math
import random
import statistics
import tempfile
import unittest
from pathlib import Path

from diagnostics import a2d
from phase0.audit import _series, hac_ci, protocol_sha256
from phase0.run import OUT_DIR, code_hashes


class A2d_Cases_and_Exact_Moments(unittest.TestCase):
    def test_sinh_control_hits_the_target_kurtosis_and_lag1(self):
        a = a2d.solve_sinh_a()
        u = math.exp(2 * a * a)
        self.assertAlmostEqual((u ** 4 - 4 * u + 3) / (2 * (u - 1) ** 2), 15.0, places=8)  # excess kurtosis 12
        for target in (0.09, 0.30):
            rho = a2d.sinh_rho_z(target, a)
            self.assertAlmostEqual(math.sinh(a * a * rho) / math.sinh(a * a), target, places=12)

    def test_exact_variance_of_the_mean_matches_the_ar1_closed_form(self):
        n, rho = 240, 0.3
        closed = ((1 + rho) / (1 - rho) - 2 * rho * (1 - rho ** n) / (n * (1 - rho) ** 2)) / n
        c = next(x for x in a2d.build_cases() if x["id"] == "G2")
        self.assertAlmostEqual(c["V_n"], closed, places=14)

    def test_exact_variance_agrees_with_simulation_for_every_case_kind(self):
        for cid in ("G2", "G4", "C4"):
            c = next(x for x in a2d.build_cases() if x["id"] == cid)
            means = [statistics.mean(a2d.generate(c, random.Random(300000 + i))) for i in range(3000)]
            self.assertAlmostEqual(statistics.pvariance(means) / c["V_n"], 1.0, delta=0.12, msg=cid)

    def test_controls_are_symmetric_and_have_the_requested_dependence(self):
        c = next(x for x in a2d.build_cases() if x["id"] == "C5")
        y = a2d.generate(dict(c, n=300000), random.Random(77))
        m, s = statistics.mean(y), statistics.pstdev(y)
        self.assertAlmostEqual(sum(((v - m) / s) ** 3 for v in y) / len(y), 0.0, delta=0.5)  # symmetric (skewness noisy under heavy tails)
        r1 = sum((y[i] - m) * (y[i + 1] - m) for i in range(len(y) - 1)) / sum((v - m) ** 2 for v in y)
        self.assertAlmostEqual(r1, 0.30, delta=0.04)

    def test_captured_fractions_equal_the_independent_bartlett_formula(self):
        c = next(x for x in a2d.build_cases() if x["id"] == "S1")
        for L in a2d.LAGS:
            expected = (1 + 2 * sum((1 - j / (L + 1)) * 0.6 ** j for j in range(1, L + 1))) / ((1 + 0.6) / (1 - 0.6))
            self.assertAlmostEqual(c["captured_fraction"][str(L)], expected, places=6)


class A2d_Seeds_and_Design(unittest.TestCase):
    def test_a2d_streams_are_disjoint_from_every_used_or_reserved_stream(self):
        checks = a2d.check_seeds()
        self.assertTrue(all(x["disjoint"] for x in checks))
        self.assertEqual(len(checks), 2 * len(a2d.USED_RANGES))
        self.assertEqual(a2d.SERIES_SEEDS, (a2d.FROZEN["seed0"], a2d.FROZEN["seed0"] + a2d.FROZEN["reps"] - 1))
        self.assertEqual(a2d.BOOT_SEEDS_RESERVED, (a2d.SERIES_SEEDS[0] + 100000, a2d.SERIES_SEEDS[1] + 100000))
        self.assertEqual([x for x in a2d.USED_RANGES if x[0].startswith("A2b screening")][0][1], (7001, 9000))

    def test_overlap_is_detected(self):
        for bad in ((8000, 9500), (20001, 22000), (24999, 26000)):
            with self.assertRaises(SystemExit):
                a2d.check_seeds(series=bad)
        with self.assertRaises(SystemExit):
            a2d.check_seeds(series=(40001, 42000), boot=(41000, 43000))

    def test_design_identity_is_stable_and_phase0_code_is_unchanged_by_a2d(self):
        self.assertEqual(a2d.design_sha256(), a2d.design_sha256())
        self.assertEqual(a2d.design_spec()["frozen"], {"seed0": 40001, "reps": 2000})
        self.assertNotIn("a2d.py", code_hashes())  # A2d lives outside phase0/, so the frozen A2b code hashes are not affected
        self.assertEqual(len(protocol_sha256()), 64)


class A2d_Run_and_Analysis(unittest.TestCase):
    def _run(self, td, name="p", reps=6, seed0=60001):
        return a2d.run_a2d(Path(td) / name, reps=reps, seed0=seed0)

    def test_plumbing_run_schema_counts_and_no_selection_or_verdicts(self):
        with tempfile.TemporaryDirectory() as td:
            rec = self._run(td)
            text = (Path(td) / "p_summary.json").read_text()
            self.assertEqual(rec["stage"], "plumbing")
            self.assertTrue(rec["analysis"].startswith("PLUMBING CHECK ONLY - NOT EVIDENCE"))
            self.assertFalse(rec["selection_performed"] or rec["formal_verdicts_issued"])
            for banned in ("selected_by_proposed_rule", "formal_pass", "screening_admissible"):
                self.assertNotIn(banned, text)
            self.assertEqual(len(rec["cases"]), 8)
            for c in rec["cases"]:
                self.assertEqual(c["replications"], {"attempted": 6, "completed": 6, "invalid": 0})
            self.assertEqual(rec["raw_file"]["rows"], 48)
            self.assertEqual(rec["design_sha256"], a2d.design_sha256())
            self.assertEqual(rec["code_sha256_phase0"], code_hashes())
            self.assertEqual(rec["config"]["series_seeds"], [60001, 60006])
            self.assertEqual(rec["config"]["bootstrap_seeds_reserved_unused"], [160001, 160006])

    def test_summary_is_reproduced_from_the_raw_file_alone(self):
        with tempfile.TemporaryDirectory() as td:
            rec = self._run(td)
            again = a2d.analyze_raw(Path(td) / "p_raw.csv", 6)
            self.assertEqual(json.loads(json.dumps(again, default=str)), json.loads(json.dumps(rec["cases"], default=str)))

    def test_raw_rows_are_reproducible_from_the_seed_mapping(self):
        with tempfile.TemporaryDirectory() as td:
            self._run(td)
            first = (Path(td) / "p_raw.csv").read_text().splitlines()[1].split(",")  # case G1, rep 0, seed 60001
            y = _series("normal", 0.0, 240, random.Random(60001))
            _, lo, hi = hac_ci(y, 4)
            self.assertEqual((first[0], first[1], first[2]), ("G1", "0", "60001"))
            self.assertEqual(float(first[3]), sum(y) / 240)
            self.assertEqual(float(first[4]), (hi - lo) / 2.0)

    def test_variance_estimator_reconstruction_equals_a_direct_bartlett_computation(self):
        y = _series("skewed", 0.3, 240, random.Random(5))
        n, m = len(y), sum(y) / len(y)
        c = [v - m for v in y]
        for L in a2d.LAGS:
            v = sum(x * x for x in c) / n + 2 * sum((1 - j / (L + 1)) * sum(c[i] * c[i + j] for i in range(n - j)) / n for j in range(1, L + 1))
            _, lo, hi = hac_ci(y, L)
            self.assertAlmostEqual(n * (((hi - lo) / 2) / a2d.Z) ** 2 / v, 1.0, places=12)

    def test_variance_ratio_is_vhat_over_n_times_vn(self):
        # regression for the executed v1 scale error: the mean ratio must be ~1 for an unbiased case (G1), not ~n
        c = next(x for x in a2d.build_cases() if x["id"] == "G1")
        rows = []
        for i in range(400):
            y = a2d.generate(c, random.Random(910000 + i))
            h = [(hi - lo) / 2.0 for L in a2d.LAGS for _, lo, hi in [hac_ci(y, L)]]
            rows.append((sum(y) / len(y), h[0], h[1], h[2]))
        res = a2d.analyze_case(c, rows, 400)
        self.assertAlmostEqual(res["variance_estimator"]["4"]["mean_ratio_Vhat_over_Vn"], 1.0, delta=0.08)
        const = [(0.01 * i, 0.2, 0.2, 0.2) for i in range(1, 6)]  # exact scale check with a constant half-width
        r = a2d.analyze_case(c, const, 5)["variance_estimator"]["4"]["mean_ratio_Vhat_over_Vn"]
        self.assertAlmostEqual(r, (0.2 / a2d.Z) ** 2 / c["V_n"], places=12)

    def test_reanalyze_requires_the_same_raw_file_refuses_overwrite_and_keeps_the_original(self):
        import hashlib
        with tempfile.TemporaryDirectory() as td:
            self._run(td)
            td = Path(td)
            before = hashlib.sha256((td / "p_summary.json").read_bytes()).hexdigest()
            rec = a2d.reanalyze(td / "p_raw.csv", td / "p_summary.json", td / "p_corrected.json", reps=6)
            self.assertEqual(hashlib.sha256((td / "p_summary.json").read_bytes()).hexdigest(), before)  # original untouched
            self.assertFalse(rec["selection_performed"] or rec["formal_verdicts_issued"] or rec["rules_and_thresholds_changed"])
            self.assertEqual(rec["design_sha256_as_frozen"], a2d.FROZEN_DESIGN_SHA256)
            self.assertIn("signatures_corrected", rec)
            self.assertIn("signatures_as_originally_reported", rec)
            with self.assertRaises(SystemExit):
                a2d.reanalyze(td / "p_raw.csv", td / "p_summary.json", td / "p_corrected.json", reps=6)  # overwrite
            (td / "tampered_raw.csv").write_text((td / "p_raw.csv").read_text() + "G1,99,1,0.0,1.0,1.0,1.0" + chr(10))
            with self.assertRaises(SystemExit):
                a2d.reanalyze(td / "tampered_raw.csv", td / "p_summary.json", td / "p_other.json", reps=6)  # raw hash mismatch

    def test_invalid_replications_are_counted_and_excluded(self):
        c = next(x for x in a2d.build_cases() if x["id"] == "G1")
        rows = [(0.01 * i, 0.1, 0.1, 0.1) for i in range(1, 9)] + [(0.0, 0.0, 0.1, 0.1), (float("nan"), 0.1, 0.1, 0.1)]
        res = a2d.analyze_case(c, rows, 10)
        self.assertEqual(res["replications"], {"attempted": 10, "completed": 8, "invalid": 2})

    def test_mirror_cases_are_exact_negations(self):
        with tempfile.TemporaryDirectory() as td:
            rec = self._run(td)
        for c in rec["cases"]:
            if c["kind"] == "skewed":
                for k, v in c["mirror_by_negation"].items():
                    self.assertEqual(v["lower_tail"], c["intervals"][k]["upper_tail"])
                    self.assertEqual(v["upper_tail"], c["intervals"][k]["lower_tail"])
            else:
                self.assertNotIn("mirror_by_negation", c)

    def test_refusals(self):
        with tempfile.TemporaryDirectory() as td:
            self._run(td)
            with self.assertRaises(SystemExit):
                self._run(td)  # existing output
            for bad in (40001, 8001, 20001, 139999):
                with self.assertRaises(SystemExit):
                    self._run(td, name="q%d" % bad, seed0=bad)  # reserved, used, or A2d streams
        with self.assertRaises(SystemExit):
            a2d.run_a2d(OUT_DIR / "a2d_should_never_exist", reps=2, seed0=60001)  # under experiments/
        self.assertFalse((OUT_DIR / "a2d_should_never_exist_raw.csv").exists())

    def test_signature_rules_are_pure_functions_of_the_summary(self):
        with tempfile.TemporaryDirectory() as td:
            rec = self._run(td)
        again = a2d.evaluate_signatures(copy.deepcopy(rec["cases"]))
        self.assertEqual(json.loads(json.dumps(again, default=str)), json.loads(json.dumps(rec["signatures"], default=str)))


if __name__ == "__main__":
    unittest.main()
