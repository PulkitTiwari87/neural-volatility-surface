"""Leakage safeguards for every feature VARIANT that produced a reported result (Phase 3 A1; GR-LEAK-03/04).

The default feature_invariance_check ran only on the plain tabular/sequence blocks. The H3-H6 results use the calendar
block (days-to-expiry per tenor + weekday) and H4 the mean-reversion block, under both target labels; each variant must
satisfy the same truncation-invariance property, and the audit must be able to FAIL for a calendar leak.
SYNTHETIC fixture only."""
import unittest

import numpy as np

from volatility_lab.evaluation.leakage import feature_invariance_check, perturb_after
from volatility_lab.features.panel import (causal_fill, cell_means, prepare, sequence_features, tabular_features)
from ._fixtures import CFG, pipeline

VARIANTS = [(target, cal, mr) for target in ("nearest_expiry", "fixed_expiry") for cal in (False, True)
            for mr in (None, 5)]


class VariantInvarianceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.panel = pipeline()["panel"]

    def test_every_feature_variant_is_invariant_to_anything_after_the_origin(self):
        for target, cal, mr in VARIANTS:
            p = prepare(self.panel, CFG.features, target, calendar=cal, mr_window=mr)
            rep = feature_invariance_check(p, CFG)
            self.assertTrue(rep["passed"], (target, cal, mr, rep))
            self.assertGreater(rep["origins_checked"], 100)

    def test_the_perturbation_reaches_the_calendar_block_only_after_the_origin(self):
        p = prepare(self.panel, CFG.features, "fixed_expiry", calendar=True)
        row = 300
        q = perturb_after(p, row, CFG)
        np.testing.assert_array_equal(p.calendar[: row + 1], q.calendar[: row + 1])
        self.assertFalse(np.array_equal(p.calendar[row + 1:], q.calendar[row + 1:]))

    def test_a_calendar_feature_that_reads_the_next_row_would_be_caught(self):
        """Negative control: an off-by-one calendar read changes under the perturbation, so the audit can fail."""
        p = prepare(self.panel, CFG.features, "fixed_expiry", calendar=True)
        row = 300
        q = perturb_after(p, row, CFG)
        sel = p.origins <= row
        leaky_p, leaky_q = p.calendar[p.origins + 1][sel], q.calendar[q.origins + 1][sel]
        self.assertFalse(np.array_equal(leaky_p, leaky_q))
        honest_p, honest_q = p.calendar[p.origins][sel], q.calendar[q.origins][sel]
        np.testing.assert_array_equal(honest_p, honest_q)

    def test_features_with_calendar_and_mean_reversion_ignore_the_future_directly(self):
        p = prepare(self.panel, CFG.features, "nearest_expiry", calendar=True, mr_window=5)
        row = 300
        q = perturb_after(p, row, CFG)
        fv = cell_means(p, np.arange(0, row + 1))
        f1, f2 = causal_fill(p, CFG.features.ffill_days, fv), causal_fill(q, CFG.features.ffill_days, fv)
        sel = p.origins <= row
        np.testing.assert_array_equal(tabular_features(p, f1, CFG.features)[sel],
                                      tabular_features(q, f2, CFG.features)[sel])
        np.testing.assert_array_equal(sequence_features(p, f1, CFG.features)[sel],
                                      sequence_features(q, f2, CFG.features)[sel])


if __name__ == "__main__":
    unittest.main()
