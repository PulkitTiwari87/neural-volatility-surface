"""Evidence governance (Phase 4; guardrails GR-MOD-04, GR-MOD-05, GR-LEAK-05, CLAUDE.md section 7/16).

Pure functions over plain dicts; standard library only. Nothing here computes a metric or changes a result.

* ``validate_run_record`` - a result artifact must say which label and validation protocol produced it.
* ``claim_level`` is ``descriptive`` unless ALL the evidence for ``validated`` exists. Today none of it does (the only
  real data used was of unverified licence and has been withdrawn), so a record claiming ``validated`` is rejected.
* ``compare_records`` - two results are *equivalent* only if label, validation protocol and feature set agree; otherwise
  the comparison is flagged non-equivalent (e.g. H6's tail-fraction validation vs H3's previous-year validation).
* ``check_verdict`` - the verdict must come from the pre-registered rule's own vocabulary
  (``decision_rule.combine_labels``); free text such as "validated" or "outperforms" is refused.
"""
from __future__ import annotations

from typing import Iterable, List

LABELS = ("nearest_expiry", "fixed_expiry")
VAL_MODES = ("prev_year", "tail_frac")
CLAIM_LEVELS = ("descriptive", "validated")
VERDICTS = ("improves_on_persistence_under_both_labels", "holds_under_nearest_expiry_label_only",
            "holds_under_fixed_expiry_label_only", "no_improvement_shown", "not_evaluable")
REQUIRED = ("label", "val_mode", "config_sha256", "claim_level", "dataset_origin")


class EvidenceError(ValueError):
    """A result artifact or claim does not meet the evidence rules."""


def validate_run_record(rec: dict) -> List[str]:
    """Return the problems with a run record (empty list = acceptable)."""
    problems = [f"missing field: {k}" for k in REQUIRED if k not in rec]
    if problems:
        return problems
    if rec["label"] not in LABELS:
        problems.append(f"label must be one of {LABELS}, got {rec['label']!r}")
    if rec["val_mode"] not in VAL_MODES:
        problems.append(f"val_mode must be one of {VAL_MODES}, got {rec['val_mode']!r}")
    if rec["claim_level"] not in CLAIM_LEVELS:
        problems.append(f"claim_level must be one of {CLAIM_LEVELS}, got {rec['claim_level']!r}")
    if rec["dataset_origin"] not in ("synthetic", "real"):
        problems.append(f"dataset_origin must be 'synthetic' or 'real', got {rec['dataset_origin']!r}")
    if len(str(rec["config_sha256"])) < 8:
        problems.append("config_sha256 is missing or too short to identify a configuration")
    if rec.get("verdict") is not None and rec["verdict"] not in VERDICTS:
        problems.append(f"verdict {rec['verdict']!r} is not in the pre-registered vocabulary")
    if rec["claim_level"] == "validated":
        problems += validated_problems(rec)
    return problems


def validated_problems(rec: dict) -> List[str]:
    """Why a record may NOT be labelled ``validated`` (all of these must be absent)."""
    out = []
    if rec.get("dataset_origin") != "real":
        out.append("validated requires real data: synthetic recovery is not evidence of market behaviour")
    if rec.get("licence_status") != "verified":
        out.append("validated requires a verified data licence")
    if not rec.get("intervals"):
        out.append("validated requires uncertainty intervals (this project's runs have none)")
    if not rec.get("owner_confirmed_by"):
        out.append("validated requires an owner confirmation")
    if rec.get("test_accessed_count") != 0:
        out.append("validated requires test_accessed_count == 0 (final test window untouched for selection)")
    return out


def require_valid(rec: dict) -> None:
    problems = validate_run_record(rec)
    if problems:
        raise EvidenceError("; ".join(problems))


def check_verdict(verdict: str) -> str:
    if verdict not in VERDICTS:
        raise EvidenceError(f"verdict {verdict!r} is not in the pre-registered vocabulary {VERDICTS}")
    return verdict


def compare_records(a: dict, b: dict, *, same_features: bool | None = None) -> dict:
    """Are two results directly comparable? ``equivalent`` is True only when nothing below differs.

    ``same_features`` lets the caller state whether the feature sets are identical (the records carry hashes only for
    the whole configuration, which the experiment flags do not enter - see KNOWN_LIMITATIONS); ``None`` = unknown,
    which is reported as a difference rather than assumed equal."""
    diffs = []
    for key, what in (("label", "target label"), ("val_mode", "validation protocol"),
                      ("dataset_origin", "dataset origin")):
        if a.get(key) != b.get(key):
            diffs.append(f"{what} differs: {a.get(key)!r} vs {b.get(key)!r}")
    if same_features is None:
        diffs.append("feature sets not shown to be identical")
    elif not same_features:
        diffs.append("feature sets differ")
    return {"equivalent": not diffs, "differences": diffs}


def assert_all_labelled(records: Iterable[dict]) -> None:
    bad = [i for i, r in enumerate(records) if validate_run_record(r)]
    if bad:
        raise EvidenceError(f"records without a valid label/protocol: {bad}")
