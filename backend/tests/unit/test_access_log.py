"""GR-LEAK-04/05: test-window access log (synthetic fixture only)."""
import unittest

import numpy as np

from ._fixtures import CFG, pipeline
from volatility_lab.evaluation.access_log import AccessLog, TestWindowAccessError
from volatility_lab.evaluation.walkforward import make_folds
from volatility_lab.experiments.runner import run_baselines


class AccessLogTests(unittest.TestCase):
    def test_counts_only_test_fit_or_select(self):
        log = AccessLog()
        log.record("fit", "train", 100)
        log.record("select", "val", 20)
        log.record("predict", "test", 30)
        log.record("evaluate", "test", 30)
        self.assertEqual(log.test_accessed_for_selection, 0)
        d = log.to_dict()
        self.assertEqual(d["test_accessed_count"], 0)
        self.assertEqual(len(d["events"]), 4)

    def test_selection_access_to_test_raises_and_is_not_logged(self):
        log = AccessLog()
        for purpose in ("fit", "select"):
            with self.assertRaises(TestWindowAccessError):
                log.record(purpose, "test", 5)
        self.assertEqual(log.events, [])

    def test_authorized_access_is_logged_and_counted(self):
        log = AccessLog(authorized=True)
        log.record("select", "test", 5)
        self.assertEqual(log.test_accessed_for_selection, 1)
        self.assertTrue(log.to_dict()["events"][0]["authorized"])

    def test_unknown_kind_rejected(self):
        with self.assertRaises(ValueError):
            AccessLog().record("fit", "holdout", 1)


class RunBaselinesAccessTests(unittest.TestCase):
    def test_baselines_record_no_test_selection_and_same_predictions(self):
        p = pipeline()["prepared"]
        folds = make_folds(p, CFG.split)
        quiet = lambda *_a, **_k: None  # noqa: E731
        base, _ = run_baselines(p, folds, CFG, log=quiet)
        log = AccessLog()
        logged, _ = run_baselines(p, folds, CFG, log=quiet, access_log=log)
        self.assertEqual(log.test_accessed_for_selection, 0)
        self.assertEqual(log.to_dict()["test_accessed_count"], 0)
        self.assertEqual(len(log.events), 3 * len(folds))
        for f in folds:
            self.assertEqual(
                [e["n"] for e in log.events if e["kind"] == "test"], [len(g.test) for g in folds])
            self.assertEqual(sorted(base[f.test_year]), sorted(logged[f.test_year]))
            for name in base[f.test_year]:
                np.testing.assert_array_equal(base[f.test_year][name], logged[f.test_year][name])


if __name__ == "__main__":
    unittest.main()
