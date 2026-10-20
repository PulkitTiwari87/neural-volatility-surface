"""GR-QNT-03: per-quote solver residual and solver-status reject counts (SYNTHETIC data only)."""
import unittest

import numpy as np

from tests.unit._fixtures import pipeline
from volatility_lab.pricing import bs

REPRICE_TOL = 1e-10  # same bound as tests/scientific/test_iv_recovery.py


class QuoteDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.P = pipeline()

    def test_reprice_err_finite_and_within_tolerance(self):
        q = self.P["quotes"]
        self.assertGreater(len(q), 0)
        self.assertIn("reprice_err", q.columns)
        err = q.reprice_err.to_numpy()
        self.assertTrue(np.isfinite(err).all())
        self.assertLess(err.max(), REPRICE_TOL)

    def test_reprice_err_is_independent_recomputation(self):
        q = self.P["quotes"]
        re = np.abs(bs.black76_price(q.F, q.strike, q["T"], q.iv, q.is_call) - q.mid / q.DF) / q.F
        np.testing.assert_allclose(q.reprice_err.to_numpy(), re.to_numpy(), rtol=0, atol=1e-15)

    def test_diagnostics_keys_and_consistency(self):
        d, q, led = self.P["diag"], self.P["quotes"], self.P["ledger2"]
        self.assertAlmostEqual(d["reprice_err_max"], float(q.reprice_err.max()), places=15)
        self.assertAlmostEqual(d["reprice_err_median"], float(q.reprice_err.median()), places=15)
        self.assertLessEqual(d["reprice_err_median"], d["reprice_err_max"])
        s = d["solver_status_rejects"]
        self.assertIn("BELOW_SOLVER_FLOOR", s)
        self.assertIn("ABOVE_SOLVER_CEILING", s)
        self.assertNotIn("OK", s)
        self.assertEqual(s["BELOW_SOLVER_FLOOR"], led.rejects.get("iv_below_solver_floor", 0))
        self.assertEqual(s["ABOVE_SOLVER_CEILING"], led.rejects.get("iv_above_solver_ceiling", 0))

    def test_ledger_still_conserved(self):
        led = self.P["ledger2"]
        led.check()
        self.assertEqual(led.kept, len(self.P["quotes"]))
        self.assertEqual(led.kept + sum(led.rejects.values()), led.rows_in)


if __name__ == "__main__":
    unittest.main()
