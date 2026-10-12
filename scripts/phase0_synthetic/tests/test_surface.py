"""Observed vs interpolated vs missing: hand-checkable cases; no silent extrapolation."""
import random
import unittest

from phase0.pipeline import run_pipeline
from phase0.run import fast_world_config
from phase0.surface import CellStatus as S
from phase0.surface import SurfaceConfig, build_surface
from phase0.synth import generate_world

CFG = SurfaceConfig(k_nodes=(-0.10, -0.05, 0.0, 0.05, 0.10), tol_k=1e-6, max_gap=0.15)


class SurfaceHandChecks(unittest.TestCase):
    def test_observed_interpolated_values_and_statuses(self):
        obs = [[(-0.10, 0.30), (0.0, 0.20), (0.10, 0.26)]]
        s = build_surface(0, obs, CFG)
        self.assertEqual(s.status[0], [S.OBSERVED, S.INTERPOLATED, S.OBSERVED, S.INTERPOLATED, S.OBSERVED])
        self.assertAlmostEqual(s.iv[0][0], 0.30, places=15)   # observed value kept exactly
        self.assertAlmostEqual(s.iv[0][1], 0.25, places=15)   # midpoint of 0.30 and 0.20
        self.assertAlmostEqual(s.iv[0][2], 0.20, places=15)
        self.assertAlmostEqual(s.iv[0][3], 0.23, places=15)   # midpoint of 0.20 and 0.26
        self.assertAlmostEqual(s.iv[0][4], 0.26, places=15)

    def test_no_extrapolation_outside_the_observed_hull(self):
        s = build_surface(0, [[(-0.05, 0.25), (0.05, 0.21)]], CFG)
        self.assertEqual(s.status[0], [S.MISSING, S.OBSERVED, S.INTERPOLATED, S.OBSERVED, S.MISSING])
        self.assertIsNone(s.iv[0][0])
        self.assertIsNone(s.iv[0][4])
        self.assertAlmostEqual(s.iv[0][2], 0.23, places=15)

    def test_gap_wider_than_max_gap_stays_missing(self):
        s = build_surface(0, [[(-0.10, 0.30), (0.10, 0.20)]], CFG)  # gap 0.20 > 0.15
        self.assertEqual(s.status[0], [S.OBSERVED, S.MISSING, S.MISSING, S.MISSING, S.OBSERVED])

    def test_empty_slice_is_all_missing_and_counts_are_reported(self):
        s = build_surface(0, [[], [(0.0, 0.2)]], CFG)
        self.assertEqual(s.status[0], [S.MISSING] * 5)
        self.assertEqual(s.n_obs, [0, 1])

    def test_linear_surface_is_reproduced_exactly_by_interpolation(self):
        f = lambda k: 0.2 - 0.5 * k
        obs = [[(k, f(k)) for k in (-0.08, 0.03, 0.09)]]
        s = build_surface(0, obs, CFG)
        for ki, k in enumerate(CFG.k_nodes):
            if s.status[0][ki] is S.INTERPOLATED:
                self.assertAlmostEqual(s.iv[0][ki], f(k), places=14)
        self.assertEqual(s.status[0][0], S.MISSING)   # -0.10 is outside [-0.08, 0.09]
        self.assertEqual(s.status[0][4], S.MISSING)   # 0.10 is outside

    def test_observation_within_tolerance_counts_as_observed_but_not_beyond(self):
        s = build_surface(0, [[(5e-7, 0.2), (0.0501, 0.3)]], CFG)
        self.assertIs(s.status[0][2], S.OBSERVED)
        self.assertNotIn(s.status[0][3], (S.OBSERVED,))  # 1e-4 away > tol_k

    def test_extrapolated_is_never_produced_on_random_observations(self):
        rng = random.Random(1)
        for _ in range(300):
            obs = [[(rng.uniform(-0.3, 0.3), rng.uniform(0.1, 0.4)) for _ in range(rng.randint(0, 8))]]
            s = build_surface(0, obs, CFG)
            self.assertEqual(s.n_status(S.EXTRAPOLATED), 0)
            for row_iv, row_st in zip(s.iv, s.status):
                for v, st in zip(row_iv, row_st):
                    self.assertEqual(v is None, st is S.MISSING)  # a value exists iff the cell is not missing


class PipelineStatusHonesty(unittest.TestCase):
    def test_every_surface_cell_has_a_status_value_consistency_and_no_extrapolation(self):
        world = generate_world(fast_world_config("RW", 20261012, 25))
        out = run_pipeline(world)
        total = {s.value: 0 for s in S}
        for surf in out["surfaces"]:
            for row_iv, row_st in zip(surf.iv, surf.status):
                for v, st in zip(row_iv, row_st):
                    total[st.value] += 1
                    self.assertEqual(v is None, st is S.MISSING)
        self.assertEqual(total["extrapolated"], 0)
        self.assertGreater(total["observed"], 0)
        self.assertGreater(total["interpolated"], 0)
        self.assertGreater(total["missing"], 0)
        self.assertEqual(sum(total.values()), 25 * 6 * 9)


if __name__ == "__main__":
    unittest.main()
