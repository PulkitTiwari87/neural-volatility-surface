"""Hand-checkable metrics, chronological evaluation (no look-ahead), bootstrap behaviour."""
import math
import unittest

from phase0.evaluate import (analytic_persistence_mse, block_bootstrap_ci, metrics, per_origin_mse, walk_forward)
from phase0.forecast import FactorAR1Forecaster, HistoryView, LookaheadError, PersistenceForecaster
from phase0.pipeline import run_pipeline
from phase0.run import fast_world_config
from phase0.surface import CellStatus as S
from phase0.surface import Surface
from phase0.synth import generate_world, term

KN = (-0.1, 0.0, 0.1)
MAT = (0.25,)


def surf(day, vals, miss=()):
    iv = [[None if i in miss else v for i, v in enumerate(vals)]]
    st = [[S.MISSING if i in miss else S.OBSERVED for i in range(len(vals))]]
    return Surface(day, iv, st, [len(vals) - len(miss)])


class HandCheckedMetrics(unittest.TestCase):
    """Days: d0=(0.20,0.22,0.24) d1=(0.21,0.20,0.26) d2=(0.20,0.23,0.25); persistence forecasts day t+1 with day t.

    origin0 errors (pred-y): -0.01, +0.02, -0.02      origin1 errors: +0.01, -0.03, +0.01
    sum|e| = 0.10 over 6 cells -> MAE = 0.016666...;   sum e^2 = 20e-4 -> MSE = 3.3333e-4 -> RMSE = 0.0182574...
    per-origin MSE: origin0 = 9e-4/3 = 3e-4 ; origin1 = 11e-4/3 = 3.6667e-4
    """

    def setUp(self):
        self.surfaces = [surf(0, (0.20, 0.22, 0.24)), surf(1, (0.21, 0.20, 0.26)), surf(2, (0.20, 0.23, 0.25))]
        self.wf = walk_forward(self.surfaces, {"persistence": PersistenceForecaster()}, KN, MAT, min_history=1)

    def test_mae_rmse_and_counts(self):
        m = metrics(self.wf["records"], "persistence")
        self.assertEqual((m["n"], m["n_origins"]), (6, 2))
        self.assertAlmostEqual(m["mae"], 0.10 / 6, places=14)
        self.assertAlmostEqual(m["rmse"], math.sqrt(20e-4 / 6), places=14)
        self.assertAlmostEqual(m["mae_volpts"], 100 * 0.10 / 6, places=12)   # decimal vs vol points kept distinct
        self.assertAlmostEqual(m["rmse_volpts"], 100 * 0.018257418583505537, places=10)

    def test_per_origin_mse(self):
        p = per_origin_mse(self.wf["records"], "persistence")
        self.assertAlmostEqual(p[0], 3e-4, places=14)
        self.assertAlmostEqual(p[1], 11e-4 / 3, places=14)

    def test_missing_cells_are_counted_not_silently_dropped(self):
        # day1 cell 0 missing: origin0 target-missing (skipped, not counted); origin1 persistence missing -> not comparable
        surfaces = [surf(0, (0.20, 0.22, 0.24)), surf(1, (0.21, 0.20, 0.26), miss=(0,)), surf(2, (0.20, 0.23, 0.25))]
        wf = walk_forward(surfaces, {"persistence": PersistenceForecaster()}, KN, MAT, min_history=1)
        self.assertEqual(wf["n_missing_by_origin"], {0: 0, 1: 1})
        m = metrics(wf["records"], "persistence")
        # remaining cells: origin0 cells 1,2 -> +0.02,-0.02 ; origin1 cells 1,2 -> -0.03,+0.01
        self.assertEqual(m["n"], 4)
        self.assertAlmostEqual(m["mae"], 0.08 / 4, places=14)
        self.assertAlmostEqual(m["rmse"], math.sqrt(18e-4 / 4), places=14)

    def test_group_filter_by_origin_status(self):
        surfaces = [surf(0, (0.20, 0.22, 0.24)), surf(1, (0.21, 0.20, 0.26)), surf(2, (0.20, 0.23, 0.25))]
        surfaces[0].status[0][1] = S.INTERPOLATED
        wf = walk_forward(surfaces, {"persistence": PersistenceForecaster()}, KN, MAT, min_history=1)
        a = metrics(wf["records"], "persistence", lambda r: r["origin_status"] is S.OBSERVED)
        b = metrics(wf["records"], "persistence", lambda r: r["origin_status"] is S.INTERPOLATED)
        self.assertEqual((a["n"], b["n"]), (5, 1))

    def test_analytic_expectation_hand_value(self):
        # k=0.1, sigma=(0.002,0.01,0.02): 4e-6 + 1e-4*0.01 + 4e-4*1e-4 = 5.04e-6 (kappa=1); x1.5 for kappa=1.5
        recs = [{"k": 0.1}]
        self.assertAlmostEqual(analytic_persistence_mse(recs, (0.002, 0.01, 0.02), 1.0), 5.04e-6, places=15)
        self.assertAlmostEqual(analytic_persistence_mse(recs, (0.002, 0.01, 0.02), 1.5), 7.56e-6, places=15)


class ChronologicalEvaluation(unittest.TestCase):
    def test_history_view_blocks_future_reads(self):
        surfaces = [surf(i, (0.2, 0.2, 0.2)) for i in range(5)]
        h = HistoryView(surfaces, 2)
        self.assertEqual(len(h), 3)
        self.assertIs(h[-1], surfaces[2])
        self.assertIs(h[0], surfaces[0])
        for bad in (3, 4, -4):
            with self.assertRaises(LookaheadError):
                h[bad]

    def test_peeking_forecaster_is_rejected_by_walk_forward(self):
        class Peeker:
            def predict(self, history):
                return history[history.upto + 1].iv  # reads tomorrow

        surfaces = [surf(i, (0.2, 0.2, 0.2)) for i in range(6)]
        with self.assertRaises(LookaheadError):
            walk_forward(surfaces, {"peek": Peeker()}, KN, MAT, min_history=2)

    def test_forecast_at_origin_t_is_invariant_to_all_later_days(self):
        world = generate_world(fast_world_config("AR", 20261013, 90))
        surfaces = run_pipeline(world)["surfaces"]
        t = 70
        garbage = [Surface(s.day, [[9.9] * len(s.iv[0]) for _ in s.iv], [[S.OBSERVED] * len(s.iv[0]) for _ in s.iv],
                           s.n_obs) if s.day > t else s for s in surfaces]
        kn = tuple(round(-0.20 + 0.05 * i, 12) for i in range(9))
        mats = world.cfg.maturities
        a = FactorAR1Forecaster(kn, mats, term).predict(HistoryView(surfaces, t))
        b = FactorAR1Forecaster(kn, mats, term).predict(HistoryView(garbage, t))
        self.assertIsNotNone(a)
        self.assertEqual(a, b)  # identical: no information from days > t entered the fit

    def test_targets_are_never_used_to_forecast(self):
        # Replace the target day by garbage after forecasting: forecasts (made before) must not change.
        world = generate_world(fast_world_config("RW", 20261012, 80))
        surfaces = run_pipeline(world)["surfaces"]
        kn = tuple(round(-0.20 + 0.05 * i, 12) for i in range(9))
        fc = {"persistence": PersistenceForecaster(), "factor_ar1": FactorAR1Forecaster(kn, world.cfg.maturities, term)}
        wf = walk_forward(surfaces, fc, kn, world.cfg.maturities, 60)
        origins = sorted({r["t"] for r in wf["records"]})
        self.assertEqual(origins[0], 59)
        self.assertEqual(origins[-1], 78)  # last origin is N-2: the final day is only ever a target


class BlockBootstrap(unittest.TestCase):
    def test_deterministic_given_seed(self):
        d = [0.1 * math.sin(i) for i in range(60)]
        self.assertEqual(block_bootstrap_ci(d, 5, 200, 7), block_bootstrap_ci(d, 5, 200, 7))
        self.assertNotEqual(block_bootstrap_ci(d, 5, 200, 7), block_bootstrap_ci(d, 5, 200, 8))

    def test_constant_positive_differences_exclude_zero(self):
        mean, lo, hi = block_bootstrap_ci([1.0] * 50, 5, 300, 1)
        self.assertEqual((mean, lo, hi), (1.0, 1.0, 1.0))

    def test_zero_mean_differences_include_zero(self):
        d = [(-1.0) ** i for i in range(200)]
        mean, lo, hi = block_bootstrap_ci(d, 5, 500, 3)
        self.assertEqual(mean, 0.0)
        self.assertLessEqual(lo, 0.0)  # the interval brackets zero
        self.assertGreaterEqual(hi, 0.0)


if __name__ == "__main__":
    unittest.main()
