"""Phase 2 numerical edge cases for the Black-76 inversion (GR-QNT-01/02/06). SYNTHETIC prices, never market data.

Complements test_iv_recovery.py (grid recovery, bounds, statuses) with input-shape / dtype / extreme-parameter cases and
internal-consistency properties. Tolerances: RECOVERY_TOL as declared in test_iv_recovery.py.
"""
import unittest

import numpy as np

from volatility_lab.pricing import bs

TOL = 1e-7


def _iv(price, F, K, T, call):
    iv, st = bs.implied_vol(price, F, K, T, call)
    return float(iv), int(st)


class InputShapeTests(unittest.TestCase):
    def test_empty_input_returns_empty_output_not_an_error(self):
        e = np.array([])
        iv, st = bs.implied_vol(e, e, e, e, np.array([], dtype=bool))
        self.assertEqual((iv.shape, st.shape), ((0,), (0,)))

    def test_integer_inputs_are_accepted(self):
        iv, st = _iv(5, 100, 100, 1, True)
        self.assertEqual(st, bs.OK)
        self.assertAlmostEqual(float(bs.black76_price(100, 100, 1, iv, True)), 5.0, places=9)

    def test_broadcasting_over_a_grid_keeps_shape_and_each_cell_is_independent(self):
        K = np.array([95.0, 100.0, 105.0])
        call = np.array([[True], [False]])
        price = bs.black76_price(100.0, K[None, :], 0.25, 0.3, call)
        iv, st = bs.implied_vol(price, 100.0, K[None, :], 0.25, call)
        self.assertEqual(iv.shape, (2, 3))
        self.assertTrue((st == bs.OK).all())
        self.assertLess(np.max(np.abs(iv - 0.3)), TOL)

    def test_inf_and_negative_prices_are_invalid_input_never_an_iv(self):
        for bad in (np.inf, -np.inf, -1.0, np.nan):
            iv, st = _iv(bad, 100.0, 100.0, 0.25, True)
            self.assertEqual(st, bs.INVALID_INPUT, bad)
            self.assertTrue(np.isnan(iv), bad)


class ExtremeParameterTests(unittest.TestCase):
    def test_extremely_short_maturities_recover_the_volatility(self):
        for T in (1e-9, 1e-6, 1e-4, 1.0 / 365):
            price = float(bs.black76_price(100.0, 100.0, T, 0.2, True))
            iv, st = _iv(price, 100.0, 100.0, T, True)
            self.assertEqual(st, bs.OK, T)
            self.assertLess(abs(iv - 0.2), TOL, T)

    def test_very_far_otm_strikes_recover_the_volatility_on_both_sides(self):
        for k, call in ((5.0, True), (-5.0, False), (3.0, True), (-3.0, False)):
            K = 100.0 * np.exp(k)
            price = float(bs.black76_price(100.0, K, 0.5, 0.4, call))
            iv, st = _iv(price, 100.0, K, 0.5, call)
            self.assertEqual(st, bs.OK, k)
            self.assertLess(abs(iv - 0.4), 1e-5, k)

    def test_the_solver_bracket_edges_themselves_are_solvable(self):
        for sigma in (bs.SIGMA_LO, bs.SIGMA_HI):
            iv, st = _iv(float(bs.black76_price(100.0, 100.0, 0.25, sigma, True)), 100.0, 100.0, 0.25, True)
            self.assertEqual(st, bs.OK, sigma)
            self.assertLess(abs(iv - sigma), 1e-9, sigma)

    def test_large_and_small_forward_scales_give_the_same_volatility(self):
        for F in (1e-3, 1.0, 1e6):
            price = float(bs.black76_price(F, F * 1.05, 0.25, 0.35, True))
            iv, st = _iv(price, F, F * 1.05, 0.25, True)
            self.assertEqual(st, bs.OK, F)
            self.assertLess(abs(iv - 0.35), 1e-6, F)


class ConsistencyTests(unittest.TestCase):
    def test_a_call_and_a_put_priced_with_one_volatility_invert_to_the_same_volatility(self):
        for K in (70.0, 100.0, 140.0):
            ic, sc = _iv(float(bs.black76_price(100.0, K, 0.5, 0.3, True)), 100.0, K, 0.5, True)
            ip, sp = _iv(float(bs.black76_price(100.0, K, 0.5, 0.3, False)), 100.0, K, 0.5, False)
            self.assertEqual((sc, sp), (bs.OK, bs.OK))
            self.assertLess(abs(ic - ip), TOL, K)

    def test_put_call_parity_of_the_undiscounted_prices(self):
        K = np.array([60.0, 100.0, 150.0])
        c = bs.black76_price(100.0, K, 0.7, 0.25, True)
        p = bs.black76_price(100.0, K, 0.7, 0.25, False)
        np.testing.assert_allclose(c - p, 100.0 - K, atol=1e-10)

    def test_iv_is_strictly_increasing_in_price(self):
        prices = np.linspace(0.5, 15.0, 200)
        iv, st = bs.implied_vol(prices, 100.0, 100.0, 0.25, True)
        self.assertTrue((st == bs.OK).all())
        self.assertTrue(np.all(np.diff(iv) > 0))

    def test_inversion_is_deterministic(self):
        prices = np.linspace(0.5, 15.0, 50)
        a = bs.implied_vol(prices, 100.0, 100.0, 0.25, True)
        b = bs.implied_vol(prices, 100.0, 100.0, 0.25, True)
        np.testing.assert_array_equal(a[0], b[0])
        np.testing.assert_array_equal(a[1], b[1])

    def test_chunking_does_not_change_results(self):
        rng = np.random.default_rng(0)
        sig = rng.uniform(0.05, 1.5, 300)
        K = 100.0 * np.exp(rng.uniform(-0.3, 0.3, 300))
        call = K >= 100.0
        price = bs.black76_price(100.0, K, 0.25, sig, call)
        whole = bs.implied_vol(price, 100.0, K, 0.25, call)
        small = bs.implied_vol(price, 100.0, K, 0.25, call, chunk=7)
        np.testing.assert_array_equal(whole[0], small[0])
        np.testing.assert_array_equal(whole[1], small[1])

    def test_vega_is_positive_and_matches_a_finite_difference(self):
        F, K, T, s = 100.0, 105.0, 0.5, 0.3
        h = 1e-6
        fd = (float(bs.black76_price(F, K, T, s + h, True)) - float(bs.black76_price(F, K, T, s - h, True))) / (2 * h)
        self.assertGreater(float(bs.black76_vega(F, K, T, s)), 0.0)
        self.assertAlmostEqual(float(bs.black76_vega(F, K, T, s)), fd, places=6)


if __name__ == "__main__":
    unittest.main()
