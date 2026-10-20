"""Determinism acceptance: Phase 2 A3 (surface rebuild hash), Phase 3 A2 (baselines reproduce exactly),
Phase 4 A1 (evaluation reproduces from the stored predictions). SYNTHETIC fixture only; nothing is trained."""
import unittest
from dataclasses import replace

import numpy as np
import pandas as pd

from volatility_lab.config.settings import Config, DataConfig
from volatility_lab.evaluation.walkforward import make_folds
from volatility_lab.experiments import runner
from volatility_lab.features.panel import causal_fill, cell_means
from volatility_lab.ingestion.optionsdx import RejectLedger, prefilter_batch
from volatility_lab.storage.raw_store import panel_sha256
from volatility_lab.surfaces.grid import build_surface_panel
from volatility_lab.validation.quotes import build_otm_quotes
from ._fixtures import CFG, chain, pipeline


class SurfaceRebuildTests(unittest.TestCase):
    def test_rebuilding_a_panel_from_the_same_quotes_and_config_gives_the_same_hash(self):
        P = pipeline()
        a, b = build_surface_panel(P["quotes"], CFG.surface), build_surface_panel(P["quotes"], CFG.surface)
        self.assertEqual(panel_sha256(a), panel_sha256(b))
        self.assertEqual(panel_sha256(a), panel_sha256(P["panel"]))

    def test_the_whole_chain_from_the_same_raw_rows_is_deterministic_and_input_sensitive(self):
        def run(seed):
            raw, _ = chain(560, seed)
            wide = prefilter_batch(raw, CFG.data, RejectLedger())
            quotes, _, _ = build_otm_quotes(wide, CFG.data)
            return panel_sha256(build_surface_panel(quotes, CFG.surface))
        self.assertEqual(run(3), run(3))
        self.assertNotEqual(run(3), run(4))

    def test_a_changed_surface_setting_changes_the_panel_hash(self):
        P = pipeline()
        other = replace(CFG.surface, tenor_days=CFG.surface.tenor_days[:-1])      # one tenor fewer: the grid must differ
        self.assertNotEqual(panel_sha256(build_surface_panel(P["quotes"], other)), panel_sha256(P["panel"]))


class ConfigHashTests(unittest.TestCase):
    def test_config_hash_is_stable_across_instances_and_sensitive_to_every_section(self):
        self.assertEqual(Config().sha256(), Config().sha256())
        self.assertNotEqual(Config().sha256(), Config(data=DataConfig(min_dte=3)).sha256())
        self.assertEqual(len(Config().sha256()), 64)


class BaselineReproducibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = pipeline()["prepared"]
        cls.folds = make_folds(cls.p, CFG.split)
        cls.a, cls.chosen_a = runner.run_baselines(cls.p, cls.folds, CFG, log=lambda *_: None)
        cls.b, cls.chosen_b = runner.run_baselines(cls.p, cls.folds, CFG, log=lambda *_: None)

    def test_baseline_predictions_and_chosen_penalties_are_bit_identical_on_rerun(self):
        self.assertEqual(self.chosen_a, self.chosen_b)
        self.assertEqual(sorted(self.a), sorted(self.b))
        for year in self.a:
            self.assertEqual(sorted(self.a[year]), sorted(self.b[year]))
            for name in self.a[year]:
                np.testing.assert_array_equal(self.a[year][name], self.b[year][name], err_msg=f"{year}/{name}")

    def test_evaluation_tables_reproduce_exactly_from_the_same_predictions(self):
        one = runner.evaluate_all(self.p, self.folds, self.a)
        two = runner.evaluate_all(self.p, self.folds, self.b)
        for x, y in zip(one, two):
            pd.testing.assert_frame_equal(x, y, check_exact=True)

    def test_persistence_equals_the_filled_current_surface_by_construction(self):
        """Hand check: the persistence forecast of the surface at t+1 is the (causally filled) surface at t."""
        f = self.folds[0]
        filled = causal_fill(self.p, CFG.features.ffill_days, cell_means(self.p, np.arange(0, f.train_rows_end + 1)))
        np.testing.assert_array_equal(self.a[f.test_year]["persistence"], filled[self.p.origins[f.test]])


if __name__ == "__main__":
    unittest.main()
