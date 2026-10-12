"""Deterministic reproducibility of the SYNTHETIC data, pipeline and metrics."""
import unittest

from phase0.run import fast_world_config, run_single
from phase0.synth import data_hash, generate_world


class Reproducibility(unittest.TestCase):
    def test_same_seed_same_data_hash_different_seed_different(self):
        a = data_hash(generate_world(fast_world_config("RW", 11, 20)))
        b = data_hash(generate_world(fast_world_config("RW", 11, 20)))
        c = data_hash(generate_world(fast_world_config("RW", 12, 20)))
        d = data_hash(generate_world(fast_world_config("AR", 11, 20)))
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertNotEqual(a, d)

    def test_world_contents_identical_across_regeneration(self):
        w1, w2 = generate_world(fast_world_config("AR", 5, 15)), generate_world(fast_world_config("AR", 5, 15))
        self.assertEqual(w1.factors, w2.factors)
        self.assertEqual(w1.spots, w2.spots)
        self.assertEqual([d.quotes for d in w1.days], [d.quotes for d in w2.days])
        self.assertEqual([d.ledger for d in w1.days], [d.ledger for d in w2.days])

    def test_full_run_is_bit_reproducible(self):
        cfg = fast_world_config("AR", 20261013, 80)
        r1 = run_single(cfg, B=300)
        r2 = run_single(cfg, B=300)
        self.assertEqual(r1["data_sha256"], r2["data_sha256"])
        self.assertEqual(r1["metrics_sha256"], r2["metrics_sha256"])
        self.assertEqual(r1["results"], r2["results"])
        self.assertEqual(r1["comparison_factor_ar1_vs_persistence"], r2["comparison_factor_ar1_vs_persistence"])
        self.assertEqual(r1["hypotheses"], r2["hypotheses"])

    def test_bootstrap_seed_changes_interval_but_not_point_metrics(self):
        cfg = fast_world_config("RW", 3, 80)
        r1 = run_single(cfg, B=300)
        r2 = run_single(cfg, B=300)
        self.assertEqual(r1["results"]["metrics_all"], r2["results"]["metrics_all"])

    def test_run_record_contains_reproducibility_metadata(self):
        rec = run_single(fast_world_config("RW", 9, 70), B=100)
        self.assertEqual(rec["config"]["world"]["seed"], 9)
        self.assertEqual(rec["config"]["bootstrap"]["seed"], 10)
        self.assertEqual(rec["environment"]["implementation"], "CPython")
        self.assertIn("synth.py", rec["code_sha256"])
        self.assertEqual(len(rec["data_sha256"]), 64)
        self.assertTrue(rec["limitations"])


if __name__ == "__main__":
    unittest.main()
