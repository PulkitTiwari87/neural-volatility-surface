# Acceptance Criteria — How Gates Are Evidenced

**Status:** PROPOSED · **Canonical per-phase criteria:** [IMPLEMENTATION_PLAN](../../IMPLEMENTATION_PLAN.md) · **Product-level criteria (AC-01…AC-12):** [PR.md](../../PR.md) §12 · **UI criteria (UA-01…UA-14):** [design.md](../../design.md) §17. This document defines *how* acceptance is demonstrated; it does not duplicate the criteria.

## Principles
1. A criterion is met only with a **linked artifact**: a test run (with command and result), an experiment record, a report, an ADR, or a review sign-off.
2. Documentation alone never satisfies an implementation or scientific criterion.
3. Thresholds are fixed **before** viewing the results they judge (pre-registration) and stored in versioned config.
4. A failed criterion is recorded, not hidden; the gate stays closed until fixed or the owner records an explicit exception with reasons.

## Status meanings applied to acceptance
| Label | Evidence required |
|---|---|
| `IMPLEMENTED` | Code merged; targeted tests pass in a recorded run; docs updated. |
| `VALIDATED` | Scientific/acceptance evidence recorded (e.g., synthetic recovery within tolerance; leakage tests pass; out-of-sample report with sample counts). |
| `BLOCKED` | Names the blocking decision/dependency. |

## Gate evidence checklist (copy into the milestone record)
```
Phase: __   Gate date: ____   Reviewer: ____
[ ] Each acceptance criterion listed, with pass/fail and artifact link
[ ] Guardrails due this phase have enforcing checks (list GR-IDs and test names)
[ ] Decisions required by this phase are DECIDED (list DEC-IDs and ADR links)
[ ] Documentation updated (architecture / methodology / schema / API / limitations)
[ ] CHANGELOG updated
[ ] Known limitations and deviations recorded
[ ] No unreviewed exceptions
Outcome: PASS / FAIL / PASS-WITH-EXCEPTIONS (list)
```

## Per-phase pointer table
| Phase | Gate (MP §23) | Criteria |
|---|---|---|
| 0 | Written data-source decision, documented scope, sample data for full analytical path | IMPLEMENTATION_PLAN Phase 0 A1–A5 |
| 1 | Repeatable ingestion, auditable quality checks | Phase 1 A1–A5 |
| 2 | Verified IV, reproducible surface snapshots | Phase 2 A1–A5 |
| 3 | Trustworthy baselines with leakage checks | Phase 3 A1–A5 |
| 4 | Reproducible out-of-sample results; clear evidence where neural helps or fails | Phase 4 A1–A5 |
| 5 | Users can inspect how a forecast was produced without reading source | Phase 5 A1–A4 + UA-* |
| 6 | Stable, documented, reproducible, honest | Phase 6 A1–A4 + AC-01…12 |

## Release definition of done
All twelve MP §24 items ⇒ AC-01…AC-12 verified with evidence ([PR.md](../../PR.md) §12).
