"""Quote validation (exact counts, conservation), parity forward, OTM selection, defect reconciliation."""
import math
import unittest

from phase0.bsm import black76_price
from phase0.quotes import QualityPolicy, Reason, infer_forward, select_otm, validate_day
from phase0.run import fast_world_config
from phase0.synth import Quote, generate_world


def q(i, strike=100.0, is_call=True, bid=1.0, ask=1.2, mat=0, T=0.25):
    return Quote(i, 0, mat, T, strike, is_call, bid, ask)


class ValidationHandChecks(unittest.TestCase):
    def test_each_reason_counted_exactly_and_conserved(self):
        quotes = [q(0), q(1, strike=105.0),                      # clean, clean
                  q(2, strike=110.0, ask=None),                  # MISSING_FIELD
                  q(3, strike=115.0, bid=-0.01),                 # NEGATIVE_PRICE
                  q(4, strike=120.0, bid=2.0, ask=1.0),          # CROSSED_MARKET
                  q(5, strike=125.0, bid=0.0, ask=0.5),          # ZERO_BID
                  q(6, strike=100.0)]                            # DUPLICATE of record 0
        retained, rep = validate_day(quotes)
        self.assertEqual(rep.ingested, 7)
        self.assertEqual(rep.retained, 2)
        self.assertEqual(rep.excluded, 5)
        self.assertEqual(rep.counts, {"RETAINED": 2, "MISSING_FIELD": 1, "NEGATIVE_PRICE": 1, "CROSSED_MARKET": 1,
                                      "ZERO_BID": 1, "DUPLICATE": 1})
        self.assertTrue(rep.conserved)
        self.assertEqual([x.record_id for x in retained], [0, 1])
        self.assertEqual(len(rep.dispositions), 7)  # every record has a disposition

    def test_precedence_and_policy(self):
        _, rep = validate_day([q(0, bid=-0.01, ask=None), q(1, strike=101.0, bid=-1.0, ask=-2.0)])
        self.assertEqual(rep.dispositions[0], Reason.MISSING_FIELD)   # missing beats negative
        self.assertEqual(rep.dispositions[1], Reason.NEGATIVE_PRICE)  # negative beats crossed
        _, rep2 = validate_day([q(0, bid=0.0, ask=0.5)], QualityPolicy(exclude_zero_bid=False))
        self.assertEqual(rep2.dispositions[0], Reason.RETAINED)

    def test_non_finite_prices_are_flagged_not_dropped(self):
        _, rep = validate_day([q(0, bid=float("nan")), q(1, strike=101.0, ask=float("inf"))])
        self.assertEqual(rep.counts["MISSING_FIELD"], 2)
        self.assertTrue(rep.conserved)


class ForwardAndSelection(unittest.TestCase):
    def _chain(self, F=100.0, T=0.5, r=0.02, sigma=0.25):
        out, i = [], 0
        for K in (90.0, 95.0, 97.5, 100.0, 102.5, 105.0, 110.0):
            for is_call in (True, False):
                m = black76_price(F, K, T, r, sigma, is_call)
                out.append(Quote(i, 0, 0, T, K, is_call, m - 0.01, m + 0.01))
                i += 1
        return out

    def test_parity_forward_recovers_exact_forward(self):
        F = 101.37
        self.assertAlmostEqual(infer_forward(self._chain(F=F), 0.5, 0.02), F, places=9)

    def test_forward_unavailable_with_fewer_than_three_pairs(self):
        self.assertIsNone(infer_forward(self._chain()[:4], 0.5, 0.02))

    def test_forward_ignores_a_corrupted_far_strike(self):
        chain = self._chain(F=100.0)
        bad = [Quote(c.record_id, c.day, c.mat_idx, c.T, c.strike, c.is_call, c.bid * 3, c.ask * 3)
               if c.strike == 90.0 and c.is_call else c for c in chain]
        self.assertAlmostEqual(infer_forward(bad, 0.5, 0.02), 100.0, places=9)

    def test_select_otm(self):
        sel = select_otm(self._chain(), 100.0)
        self.assertEqual(len(sel), 7)  # one side per strike
        for x in sel:
            self.assertEqual(x.is_call, x.strike >= 100.0 * (1 - 1e-9))


class DefectReconciliationOnSyntheticWorld(unittest.TestCase):
    def test_validator_finds_exactly_the_injected_defects_record_by_record(self):
        world = generate_world(fast_world_config("RW", 20261012, 40))
        expected = {"NEGATIVE_PRICE": Reason.NEGATIVE_PRICE, "CROSSED_MARKET": Reason.CROSSED_MARKET,
                    "ZERO_BID": Reason.ZERO_BID, "MISSING_FIELD": Reason.MISSING_FIELD, "DUPLICATE": Reason.DUPLICATE,
                    "ABOVE_UPPER_BOUND": Reason.RETAINED}  # above-bound passes validation; the solver rejects it
        total_injected = 0
        for day in world.days:
            retained, rep = validate_day(day.quotes)
            self.assertTrue(rep.conserved)
            for rid, kind in day.ledger.items():
                self.assertEqual(rep.dispositions[rid], expected[kind], (day.day, rid, kind))
                total_injected += 1
            for kind in ("NEGATIVE_PRICE", "CROSSED_MARKET", "ZERO_BID", "MISSING_FIELD", "DUPLICATE"):
                self.assertEqual(rep.counts[kind], day.injected[kind])
            # no clean record is wrongly flagged
            for x in day.quotes:
                if x.record_id not in day.ledger:
                    self.assertIs(rep.dispositions[x.record_id], Reason.RETAINED)
        self.assertGreater(total_injected, 10)  # the test really exercised injected defects

    def test_every_generated_quote_is_labelled_synthetic(self):
        world = generate_world(fast_world_config("AR", 7, 10))
        self.assertTrue(all(x.origin == "synthetic" for d in world.days for x in d.quotes))
        self.assertIn("SYNTHETIC", world.label)


if __name__ == "__main__":
    unittest.main()
