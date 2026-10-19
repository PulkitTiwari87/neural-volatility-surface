import sys
import unittest
from pathlib import Path

import numpy as np

from volatility_lab.pricing import bs

SPIKE = Path(__file__).resolve().parents[3] / "scripts" / "phase0_synthetic"


class PricingTests(unittest.TestCase):
    def test_iv_round_trip_recovers_the_generating_vol(self):
        rng = np.random.default_rng(0)
        n = 5000
        F = rng.uniform(50, 500, n)
        K = F * np.exp(rng.uniform(-0.4, 0.4, n))
        T = rng.uniform(5, 400, n) / 365
        sig = rng.uniform(0.05, 1.5, n)
        call = rng.random(n) < 0.5
        price = bs.black76_price(F, K, T, sig, call)
        iv, st = bs.implied_vol(price, F, K, T, call)
        ok = st == bs.OK
        # Where vega ~ 0 (deep ITM: price is all intrinsic; ultra-far OTM) the vol is not identifiable at
        # float precision. That is why the pipeline only uses OTM quotes; demand recovery where it is identifiable.
        vega = bs.black76_vega(F, K, T, sig)
        meaningful = ok & (vega > 1e-4 * F)
        self.assertGreater(meaningful.mean(), 0.6)
        self.assertLess(np.max(np.abs(iv[meaningful] - sig[meaningful])), 1e-7)
        otm = ok & (np.where(call, K >= F, K < F)) & (price > 1e-8 * F)
        self.assertLess(np.max(np.abs(iv[otm] - sig[otm])), 1e-4)

    def test_failures_are_explicit_and_never_fabricated(self):
        F, K, T = 100.0, 100.0, 0.25
        cases = [(0.0, True, bs.BELOW_LOWER_BOUND), (F, True, bs.ABOVE_UPPER_BOUND),
                 (np.nan, True, bs.INVALID_INPUT), (-1.0, True, bs.INVALID_INPUT), (5.0, False, bs.OK)]
        for price, call, expect in cases:
            iv, st = bs.implied_vol(price, F, K, T, call)
            self.assertEqual(int(st), expect, price)
            self.assertEqual(bool(np.isnan(iv)), expect != bs.OK)
        iv, st = bs.implied_vol(1.0, F, K, 0.0, True)           # T = 0
        self.assertEqual(int(st), bs.INVALID_INPUT)
        iv, st = bs.implied_vol(0.5, 100, 100, 0.25, True)       # intrinsic 0, tiny price but valid
        self.assertEqual(int(st), bs.OK)

    def test_put_call_parity_and_greeks_by_finite_difference(self):
        F, K, T, s = 100.0, 95.0, 0.5, 0.3
        c, p = bs.black76_price(F, K, T, s, True), bs.black76_price(F, K, T, s, False)
        self.assertAlmostEqual(float(c - p), F - K, places=10)
        d, g, v = bs.black76_greeks(F, K, T, s, True)
        h = 1e-4
        up, dn = bs.black76_price(F + h, K, T, s, True), bs.black76_price(F - h, K, T, s, True)
        self.assertAlmostEqual(float(d), float((up - dn) / (2 * h)), places=6)
        self.assertAlmostEqual(float(g), float((up - 2 * c + dn) / h ** 2), places=4)
        vu, vd = bs.black76_price(F, K, T, s + h, True), bs.black76_price(F, K, T, s - h, True)
        self.assertAlmostEqual(float(v), float((vu - vd) / (2 * h)), places=6)

    def test_matches_the_scalar_phase0_reference_implementation(self):
        sys.path.insert(0, str(SPIKE))
        try:
            from phase0.bsm import black76_price as ref_price
            from phase0.iv import implied_vol as ref_iv
        finally:
            sys.path.remove(str(SPIKE))
        rng = np.random.default_rng(1)
        for _ in range(60):
            F = float(rng.uniform(80, 120)); K = F * float(np.exp(rng.uniform(-0.2, 0.2)))
            T = float(rng.uniform(10, 300) / 365); s = float(rng.uniform(0.1, 0.8)); call = bool(rng.random() < 0.5)
            self.assertAlmostEqual(float(bs.black76_price(F, K, T, s, call)), ref_price(F, K, T, 0.0, s, call), places=10)
            price = ref_price(F, K, T, 0.0, s, call)
            res = ref_iv(price, F, K, T, 0.0, call)
            ours, st = bs.implied_vol(price, F, K, T, call)
            if res.iv is not None and int(st) == bs.OK:
                self.assertLess(abs(float(ours) - res.iv), 1e-6)


if __name__ == "__main__":
    unittest.main()