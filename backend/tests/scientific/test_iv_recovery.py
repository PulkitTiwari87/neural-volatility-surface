"""Phase 2 known-answer IV tests (GR-QNT-01, GR-QNT-02, GR-QNT-06). SYNTHETIC prices, never market data.

Tolerances are declared here, in one place, with their reason (IMPLEMENTATION_PLAN Phase 2 A1). They derive from
float64 conditioning, not from looking at results: the bisection bracket ends at ~1e-14, so the recovery error
of a price with relative resolution ``eps`` is ``eps * F / vega``. A quote whose vega is below ``VEGA_FLOOR * F``
cannot identify its volatility, which is why the pipeline only inverts out-of-the-money quotes.

Ordering caveat (recorded in IV_METHODOLOGY): experiment E-1 had already run on real SPY data before these
tolerances were written down, so Phase 2 A1's "set before real data" cannot be claimed.
"""
import itertools
import unittest

import numpy as np

from volatility_lab.pricing import bs

REPRICE_TOL = 1e-10          # |model_price(iv) - price| / F, for every OK status
RECOVERY_TOL = 1e-7          # |iv - sigma| where the quote identifies sigma
VEGA_FLOOR = 1e-4            # vega / F below which sigma is not identifiable from a float64 price

SIGMAS = (0.05, 0.10, 0.20, 0.40, 0.80, 1.50, 3.00)
T_DAYS = (1, 2, 7, 30, 91, 182, 365, 730)   # very short maturities included on purpose
KS = (-0.5, -0.3, -0.15, -0.05, 0.0, 0.05, 0.15, 0.3, 0.5)   # ln(K/F), deep ITM and OTM both sides


def _grid(F=100.0):
    rows = list(itertools.product(SIGMAS, T_DAYS, KS, (True, False)))
    sig, td, k, call = (np.array(c) for c in zip(*rows))
    T = td / 365.0
    K = F * np.exp(k)
    price = bs.black76_price(F, K, T, sig, call)
    iv, st = bs.implied_vol(price, F, K, T, call)
    return dict(F=F, K=K, T=T, sig=sig, k=k, call=call, price=price, iv=iv, st=st)


class RecoveryGridTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = {F: _grid(F) for F in (100.0, 4500.0)}

    def test_every_ok_status_reprices_the_input(self):
        """GR-QNT-02: a returned IV is always a root of the pricing equation."""
        for F, g in self.g.items():
            ok = g["st"] == bs.OK
            re = bs.black76_price(F, g["K"][ok], g["T"][ok], g["iv"][ok], g["call"][ok])
            self.assertLess(np.max(np.abs(re - g["price"][ok])) / F, REPRICE_TOL, F)

    def test_no_iv_without_ok_status_and_no_ok_without_iv(self):
        for g in self.g.values():
            self.assertTrue(np.array_equal(np.isfinite(g["iv"]), g["st"] == bs.OK))

    def test_recovery_where_identifiable_and_every_miss_is_explained(self):
        """GR-QNT-06: grid over vol x maturity (1d..2y) x moneyness (+-0.5) x call/put."""
        for F, g in self.g.items():
            ok = g["st"] == bs.OK
            vega = bs.black76_vega(F, g["K"], g["T"], g["sig"])
            identifiable = ok & (vega >= VEGA_FLOOR * F)
            err = np.abs(g["iv"] - g["sig"])
            self.assertGreater(identifiable.sum(), 300, F)          # the grid really exercises recovery
            self.assertLess(np.nanmax(err[identifiable]), RECOVERY_TOL, F)
            # every OK cell that misses the tolerance must be a non-identifiable one - no unexplained error
            missed = ok & ~(err < RECOVERY_TOL)
            self.assertTrue(np.all(vega[missed] < VEGA_FLOOR * F), F)

    def test_failure_to_solve_only_when_the_price_is_indistinguishable_from_a_bound(self):
        """A non-OK status is never the solver giving up on a well-posed price."""
        for F, g in self.g.items():
            bad = g["st"] != bs.OK
            lower = np.where(g["call"], np.maximum(F - g["K"], 0.0), np.maximum(g["K"] - F, 0.0))
            upper = np.where(g["call"], F, g["K"])
            at_bound = (g["price"] <= lower * (1 + 1e-12) + 1e-12 * F) | (g["price"] >= upper * (1 - 1e-12))
            self.assertTrue(np.all(at_bound[bad]), F)

    def test_scale_invariance(self):
        """Prices and strikes scaled by F leave IV unchanged (SPY ~100 vs SPX ~4500)."""
        a, b = self.g[100.0], self.g[4500.0]
        both = (a["st"] == bs.OK) & (b["st"] == bs.OK)
        vega = bs.black76_vega(100.0, a["K"], a["T"], a["sig"])
        well = both & (vega >= VEGA_FLOOR * 100.0)
        self.assertLess(np.max(np.abs(a["iv"][well] - b["iv"][well])), 2 * RECOVERY_TOL)

    def test_otm_domain_the_pipeline_uses_recovers_everywhere_it_is_priced(self):
        """The pipeline inverts only OTM quotes (calls for K>=F, puts below): recovery must hold wherever the
        price is representable (price/F above float resolution of the bracket)."""
        for F, g in self.g.items():
            otm = np.where(g["call"], g["k"] >= 0, g["k"] < 0)
            ok = otm & (g["st"] == bs.OK) & (g["price"] > 1e-8 * F)
            self.assertGreater(ok.sum(), 200)
            self.assertLess(np.max(np.abs(g["iv"][ok] - g["sig"][ok])), 1e-5, F)


class BoundsAndInvalidInputTests(unittest.TestCase):
    F, T = 100.0, 0.25

    def test_prices_at_or_beyond_the_no_arbitrage_bounds_give_explicit_status_for_calls_and_puts(self):
        """GR-QNT-01 for ITM/OTM calls and puts, not only the ATM call."""
        F, T = self.F, self.T
        for K, call in ((90.0, True), (110.0, True), (90.0, False), (110.0, False)):
            lower = max(F - K, 0.0) if call else max(K - F, 0.0)
            upper = F if call else K
            for price, expect in ((lower, bs.BELOW_LOWER_BOUND), (lower * 0.5, bs.BELOW_LOWER_BOUND),
                                  (upper, bs.ABOVE_UPPER_BOUND), (upper * 1.5, bs.ABOVE_UPPER_BOUND)):
                iv, st = bs.implied_vol(price, F, K, T, call)
                self.assertEqual(int(st), expect, (K, call, price))
                self.assertTrue(np.isnan(iv), (K, call, price))

    def test_invalid_inputs_never_produce_an_iv(self):
        bad = [dict(F=-1.0, K=100.0, T=0.25), dict(F=100.0, K=0.0, T=0.25), dict(F=100.0, K=100.0, T=-0.1),
               dict(F=100.0, K=100.0, T=0.0), dict(F=np.inf, K=100.0, T=0.25), dict(F=100.0, K=np.nan, T=0.25)]
        for b in bad:
            iv, st = bs.implied_vol(5.0, b["F"], b["K"], b["T"], True)
            self.assertEqual(int(st), bs.INVALID_INPUT, b)
            self.assertTrue(np.isnan(iv), b)

    def test_roots_outside_the_solver_bracket_are_not_reported_as_arbitrage_bounds(self):
        """Regression: a price inside the no-arbitrage bounds whose root lies beyond [SIGMA_LO, SIGMA_HI] used to be
        labelled BELOW_LOWER_BOUND (even for a price of 95 on a 100 forward). It is a solver-range failure."""
        F, K, T = self.F, 100.0, self.T
        for sigma, expect in ((1e-5, bs.BELOW_SOLVER_FLOOR), (8.0, bs.ABOVE_SOLVER_CEILING),
                              (20.0, bs.ABOVE_SOLVER_CEILING)):
            price = float(bs.black76_price(F, K, T, sigma, True))
            lower, upper = 0.0, F
            self.assertTrue(lower < price < upper, sigma)       # genuinely inside the no-arbitrage bounds
            iv, st = bs.implied_vol(price, F, K, T, True)
            self.assertEqual(int(st), expect, sigma)
            self.assertTrue(np.isnan(iv), sigma)
        self.assertEqual(bs.STATUS_NAMES[bs.BELOW_SOLVER_FLOOR], "BELOW_SOLVER_FLOOR")
        self.assertEqual(bs.STATUS_NAMES[bs.ABOVE_SOLVER_CEILING], "ABOVE_SOLVER_CEILING")

    def test_statuses_cover_a_mixed_array_without_cross_contamination(self):
        price = np.array([5.0, 0.0, np.nan, 100.0, 5.0])
        iv, st = bs.implied_vol(price, 100.0, 100.0, 0.25, True)
        self.assertEqual(list(st), [bs.OK, bs.BELOW_LOWER_BOUND, bs.INVALID_INPUT, bs.ABOVE_UPPER_BOUND, bs.OK])
        self.assertEqual(iv[0], iv[4])


if __name__ == "__main__":
    unittest.main()
