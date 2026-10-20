"""Evidence governance (Phase 4): descriptive results cannot be labelled validated; protocols must be stated; unlike
protocols are flagged non-equivalent; verdicts come from the pre-registered vocabulary. No model is trained."""
import tempfile
import unittest
from pathlib import Path

from volatility_lab.evaluation import evidence as ev
from volatility_lab.evaluation.decision_rule import combine_labels
from volatility_lab.experiments import runner

GOOD = {"label": "fixed_expiry", "val_mode": "prev_year", "config_sha256": "28b90c2a" + "0" * 8,
        "claim_level": "descriptive", "dataset_origin": "synthetic", "verdict": "holds_under_fixed_expiry_label_only"}
VALIDATED_EVIDENCE = {"claim_level": "validated", "dataset_origin": "real", "licence_status": "verified",
                      "intervals": {"mse_skill": [0.01, 0.05]}, "owner_confirmed_by": "owner", "test_accessed_count": 0}


class RunRecordTests(unittest.TestCase):
    def test_a_complete_descriptive_record_is_accepted(self):
        self.assertEqual(ev.validate_run_record(GOOD), [])

    def test_every_required_field_is_required(self):
        for k in ev.REQUIRED:
            rec = {x: v for x, v in GOOD.items() if x != k}
            self.assertEqual(ev.validate_run_record(rec), [f"missing field: {k}"], k)

    def test_unknown_label_protocol_origin_or_short_config_hash_is_rejected(self):
        for patch in ({"label": "nearest"}, {"val_mode": "random_split"}, {"dataset_origin": "provider"},
                      {"config_sha256": "abc"}, {"claim_level": "proven"}):
            self.assertTrue(ev.validate_run_record({**GOOD, **patch}), patch)

    def test_a_random_split_is_not_an_allowed_validation_protocol(self):
        self.assertNotIn("random", " ".join(ev.VAL_MODES))


class ValidatedClaimTests(unittest.TestCase):
    def test_validated_is_rejected_unless_every_item_of_evidence_exists(self):
        full = {**GOOD, **VALIDATED_EVIDENCE}
        self.assertEqual(ev.validate_run_record(full), [])
        for drop, text in (("intervals", "intervals"), ("owner_confirmed_by", "owner"),
                           ("licence_status", "licence"), ("test_accessed_count", "test_accessed_count")):
            rec = {k: v for k, v in full.items() if k != drop}
            self.assertTrue(any(text in p for p in ev.validate_run_record(rec)), drop)

    def test_validated_is_rejected_for_synthetic_data_and_for_touched_test_windows(self):
        full = {**GOOD, **VALIDATED_EVIDENCE}
        self.assertTrue(any("real data" in p for p in ev.validate_run_record({**full, "dataset_origin": "synthetic"})))
        self.assertTrue(any("test_accessed_count" in p for p in ev.validate_run_record({**full, "test_accessed_count": 3})))
        self.assertTrue(any("licence" in p for p in ev.validate_run_record({**full, "licence_status": "unverified"})))

    def test_a_record_shaped_like_the_h5_h6_results_cannot_claim_validated(self):
        h = {**GOOD, "claim_level": "validated", "dataset_origin": "real", "licence_status": "unverified"}
        problems = ev.validate_run_record(h)
        self.assertTrue(any("licence" in p for p in problems) and any("intervals" in p for p in problems))
        with self.assertRaises(ev.EvidenceError):
            ev.require_valid(h)


class VerdictTests(unittest.TestCase):
    def test_vocabulary_equals_what_the_pre_registered_rule_can_return(self):
        outs = {combine_labels({"label_pass": n}, {"label_pass": f})
                for n in (True, False, None) for f in (True, False, None)}
        self.assertEqual(outs, set(ev.VERDICTS))

    def test_free_text_claims_are_refused(self):
        for bad in ("validated", "outperforms persistence", "significant improvement", ""):
            with self.assertRaises(ev.EvidenceError):
                ev.check_verdict(bad)
        self.assertEqual(ev.check_verdict("holds_under_fixed_expiry_label_only"), "holds_under_fixed_expiry_label_only")


class ComparabilityTests(unittest.TestCase):
    def test_identical_protocols_are_equivalent_only_when_features_are_shown_identical(self):
        self.assertTrue(ev.compare_records(GOOD, dict(GOOD), same_features=True)["equivalent"])
        unknown = ev.compare_records(GOOD, dict(GOOD))
        self.assertFalse(unknown["equivalent"])
        self.assertIn("feature sets not shown to be identical", unknown["differences"])

    def test_h6_style_tail_validation_vs_h3_style_previous_year_validation_is_non_equivalent(self):
        h3 = {**GOOD, "val_mode": "prev_year"}
        h6 = {**GOOD, "val_mode": "tail_frac"}
        res = ev.compare_records(h3, h6, same_features=True)
        self.assertFalse(res["equivalent"])
        self.assertTrue(any("validation protocol" in d for d in res["differences"]))

    def test_different_target_labels_are_non_equivalent(self):
        res = ev.compare_records(GOOD, {**GOOD, "label": "nearest_expiry"}, same_features=True)
        self.assertFalse(res["equivalent"])
        self.assertTrue(any("target label" in d for d in res["differences"]))


class ManifestIntegrationTests(unittest.TestCase):
    def test_write_manifest_accepts_a_valid_record_and_still_accepts_legacy_extras(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "a.txt").write_text("x")
            runner.write_manifest(td, {"config_sha256": "28b90c2a" + "0" * 8})        # legacy: no claim_level, unchanged
            runner.write_manifest(td, dict(GOOD))
            self.assertEqual(runner.verify_manifest(td), [])

    def test_write_manifest_refuses_a_validated_claim_without_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ev.EvidenceError):
                runner.write_manifest(td, {**GOOD, "claim_level": "validated"})
            self.assertFalse((Path(td) / "manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
