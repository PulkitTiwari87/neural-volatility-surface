"""Hand-computed checks of the pre-registered descriptive decision rule (evaluation.decision_rule)."""
import unittest

import pandas as pd

from volatility_lab.evaluation.decision_rule import combine_labels, improvement_rule


def _pooled(skill, mae_m, mae_p=1.0):
    return pd.DataFrame([{"cells": "primary", "model": "persistence", "mae": mae_p, "mse_skill_vs_persistence": 0.0},
                         {"cells": "primary", "model": "m", "mae": mae_m, "mse_skill_vs_persistence": skill}])


def _paired(txt):
    return pd.DataFrame([{"model": "m", "folds_better_than_persistence": txt}])


def _brk(model_rmse, pers_rmse=2.0, n=60, folds=(2016, 2017)):
    rows = []
    for fold in folds:
        for g in ("low", "mid", "high"):
            rows.append({"group_type": "rv_regime", "group": g, "model": "m", "fold": fold, "rmse": model_rmse[g], "n_cells": n})
            rows.append({"group_type": "rv_regime", "group": g, "model": "persistence", "fold": fold, "rmse": pers_rmse, "n_cells": n})
    return pd.DataFrame(rows)


GOOD = {"low": 1.9, "mid": 2.1, "high": 1.9}


class RuleTests(unittest.TestCase):
    def test_all_criteria_pass(self):
        r = improvement_rule(_pooled(0.05, 0.9), _brk(GOOD), _paired("6/8"), "m")
        self.assertEqual([r[k]["pass"] for k in "abcd"], [True, True, None, True])   # c not applicable
        self.assertIs(r["label_pass"], True)

    def test_criterion_a_needs_both_skill_and_mae(self):
        self.assertFalse(improvement_rule(_pooled(0.05, 1.1), _brk(GOOD), _paired("7/8"), "m")["a"]["pass"])
        self.assertFalse(improvement_rule(_pooled(-0.01, 0.9), _brk(GOOD), _paired("7/8"), "m")["a"]["pass"])

    def test_criterion_b_threshold_and_unevaluable(self):
        self.assertTrue(improvement_rule(_pooled(0.05, 0.9), _brk(GOOD), _paired("6/8"), "m")["b"]["pass"])
        r = improvement_rule(_pooled(0.05, 0.9), _brk(GOOD), _paired("5/8"), "m")
        self.assertFalse(r["b"]["pass"])
        self.assertIs(r["label_pass"], False)
        r = improvement_rule(_pooled(0.05, 0.9), _brk(GOOD), _paired("3/3"), "m")
        self.assertIsNone(r["b"]["pass"])
        self.assertIsNone(r["label_pass"])

    def test_criterion_c_every_seed_must_beat_persistence(self):
        r = improvement_rule(_pooled(0.05, 0.9), _brk(GOOD), _paired("7/8"), "m", seed_skills=[0.04, 0.06, -0.01])
        self.assertFalse(r["c"]["pass"])
        self.assertIs(r["label_pass"], False)
        r = improvement_rule(_pooled(0.05, 0.9), _brk(GOOD), _paired("7/8"), "m", seed_skills=[0.04, 0.06, 0.01])
        self.assertTrue(r["c"]["pass"])
        self.assertIs(r["label_pass"], True)

    def test_criterion_d_regimes_counted_from_pooled_mse_with_sample_floor(self):
        # regime pooled n = 120 each; model beats persistence in 1 of 3 regimes -> fails
        r = improvement_rule(_pooled(0.05, 0.9), _brk({"low": 1.9, "mid": 2.1, "high": 2.2}), _paired("7/8"), "m")
        self.assertFalse(r["d"]["pass"])
        # n = 40 per fold x 2 folds = 80 < 100 in every regime -> not evaluable, never silently passed
        r = improvement_rule(_pooled(0.05, 0.9), _brk(GOOD, n=40), _paired("7/8"), "m")
        self.assertIsNone(r["d"]["pass"])
        self.assertIsNone(r["label_pass"])

    def test_regime_skill_value_is_one_minus_mse_ratio(self):
        r = improvement_rule(_pooled(0.05, 0.9), _brk(GOOD), _paired("7/8"), "m")
        self.assertIn(f"low {1 - 1.9 ** 2 / 2.0 ** 2:+.4f}", r["d"]["detail"])

    def test_combine_labels_truth_table(self):
        T, F, N = {"label_pass": True}, {"label_pass": False}, {"label_pass": None}
        self.assertEqual(combine_labels(T, T), "improves_on_persistence_under_both_labels")
        self.assertEqual(combine_labels(T, F), "holds_under_nearest_expiry_label_only")
        self.assertEqual(combine_labels(N, T), "holds_under_fixed_expiry_label_only")
        self.assertEqual(combine_labels(F, F), "no_improvement_shown")
        self.assertEqual(combine_labels(N, N), "not_evaluable")


if __name__ == "__main__":
    unittest.main()
