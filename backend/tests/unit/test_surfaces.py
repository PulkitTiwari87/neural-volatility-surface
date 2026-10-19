import unittest

import numpy as np
import pandas as pd

from volatility_lab.config.settings import SurfaceConfig
from volatility_lab.datasets.synthetic import true_sigma
from volatility_lab.surfaces import grid
from volatility_lab.surfaces.diagnostics import butterfly_violations, calendar_violations, diagnostics_report
from ._fixtures import CFG, pipeline


def _day(expiries_days, ks, iv=0.2):
    rows = [{"date": 1, "expiry": 1 + d, "T": d / 365.0, "k": k, "iv": iv} for d in expiries_days for k in ks]
    return pd.DataFrame(rows)


class SurfaceStatusTests(unittest.TestCase):
    cfg = SurfaceConfig(tenor_days=(7, 30), k_nodes=(-0.12, 0.0, 0.12), min_quotes_per_slice=2)

    def test_observed_means_expiry_near_tenor_and_tight_real_quotes(self):
        iv, st = grid.build_day_surface(_day([30, 60], np.arange(-0.05, 0.0501, 0.01)), self.cfg)
        self.assertEqual(st[1, 1], grid.OBSERVED)
        self.assertAlmostEqual(iv[1, 1], 0.2, places=12)

    def test_never_extrapolated_in_k_or_maturity(self):
        iv, st = grid.build_day_surface(_day([30, 60], np.arange(-0.05, 0.0501, 0.01)), self.cfg)
        self.assertEqual(st[1, 0], grid.MISSING)         # node k = -0.12 outside the quotes
        self.assertEqual(st[1, 2], grid.MISSING)
        self.assertTrue(np.isnan(iv[st == grid.MISSING]).all())
        self.assertTrue((st[0] == grid.MISSING).all())   # tenor 7d is below the shortest expiry (30d)

    def test_maturity_interpolation_uses_total_variance(self):
        iv, st = grid.build_day_surface(_day([20, 40], np.arange(-0.05, 0.0501, 0.01)), self.cfg)
        self.assertEqual(st[1, 1], grid.INTERP_T)
        self.assertAlmostEqual(iv[1, 1], 0.2, places=12)   # flat vol -> variance linear in T -> same vol
        # increasing term structure: result lies strictly between the bracketing vols
        d = pd.concat([_day([20], np.arange(-0.05, 0.0501, 0.01), 0.18), _day([40], np.arange(-0.05, 0.0501, 0.01), 0.24)])
        iv, st = grid.build_day_surface(d, self.cfg)
        self.assertTrue(0.18 < iv[1, 1] < 0.24)

    def test_sparse_bracketing_quotes_are_interp_k_not_observed(self):
        iv, st = grid.build_day_surface(_day([30, 60], [-0.05, 0.05]), self.cfg)
        self.assertEqual(st[1, 1], grid.INTERP_K)

    def test_q25_observed_cells_exist_when_strikes_sit_on_a_K_grid(self):
        """Regression for Q-25: the old definition almost never produced observed cells."""
        panel = pipeline()["panel"]
        share = (panel["status"] == grid.OBSERVED).mean()
        self.assertGreater(share, 0.25)

    def test_observed_cells_match_the_generating_surface(self):
        P = pipeline()
        panel, truth = P["panel"], P["truth"]
        lv = dict(zip(truth.date.values.astype("datetime64[D]").astype("int64"), zip(truth["level"], truth["skew"])))
        errs = []
        for i, d in enumerate(panel["dates"]):
            L, S = lv[int(d)]
            for j, tau in enumerate(panel["tenor_days"]):
                for m, k in enumerate(panel["k_nodes"]):
                    if panel["status"][i, j, m] == grid.OBSERVED:
                        errs.append(abs(panel["iv"][i, j, m] - true_sigma(k, tau / 365, L, S)))
        errs = np.asarray(errs)
        self.assertGreater(errs.size, 1000)
        self.assertLess(np.median(errs), 1e-3)
        self.assertLess(np.quantile(errs, 0.99), 6e-3)

    def test_panel_is_deterministic(self):
        P = pipeline()
        again = grid.build_surface_panel(P["quotes"], CFG.surface)
        for key in ("iv", "status", "dates"):
            np.testing.assert_array_equal(np.nan_to_num(P["panel"][key], nan=-1), np.nan_to_num(again[key], nan=-1))


class DiagnosticsTests(unittest.TestCase):
    tenors = np.array([30, 60, 91])
    ks = np.array([-0.08, -0.04, 0.0, 0.04, 0.08])

    def test_clean_flat_surface_has_no_flags(self):
        iv = np.full((2, 3, 5), 0.2)
        self.assertEqual(calendar_violations(iv, self.tenors)[0], 0)
        self.assertEqual(butterfly_violations(iv, self.tenors, self.ks)[0], 0)

    def test_calendar_violation_is_flagged(self):
        iv = np.full((1, 3, 5), 0.2)
        iv[0, 1, :] = 0.10          # total variance drops with maturity
        self.assertGreater(calendar_violations(iv, self.tenors)[0], 0)

    def test_butterfly_violation_is_flagged(self):
        iv = np.full((1, 3, 5), 0.2)
        iv[0, 0, 2] = 0.9            # a spike at one strike makes the call price non-convex
        self.assertGreater(butterfly_violations(iv, self.tenors, self.ks)[0], 0)

    def test_report_states_it_is_not_a_proof(self):
        self.assertIn("not a proof", diagnostics_report(pipeline()["panel"])["note"])


if __name__ == "__main__":
    unittest.main()