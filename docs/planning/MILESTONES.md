# Milestones

**Status:** PROPOSED · **Canonical for:** milestone definitions with measurable exit gates and the gate-outcome log · **Detailed criteria:** [IMPLEMENTATION_PLAN](../../IMPLEMENTATION_PLAN.md) · **Evidence procedure:** [ACCEPTANCE_CRITERIA](../project/ACCEPTANCE_CRITERIA.md)

## Milestone table
| ID | Milestone | Measurable exit gate (summary) | Required evidence | Status |
|---|---|---|---|---|
| M-F | Repository foundation | All required files/dirs exist; consistency audit passed; no code/data/results | Audit report | IN_PROGRESS |
| M-0 | Feasibility | Data-source ADR with licence conclusions; scope; MVD quantified and measured; pre-registered success criteria; sample exercises full path | ADRs, assessment, sample run notes | IN_PROGRESS (desk research, proposed MVD/criteria, and a **synthetic** feasibility run with 57 passing tests completed 2026-10-12; real-data evidence list in assessment §10.4 unmet; gate NOT passed) |
| M-1 | Data foundation | Re-ingestion identical or explicitly versioned; ingested = retained + excluded for every snapshot; write-once raw; timestamp/calendar tests pass | Test logs, quality reports | PLANNED |
| M-2 | IV & surfaces | Synthetic recovery within recorded tolerances; no fabricated IV; surface rebuild hash-identical; statuses on all cells; method comparison documented | Scientific test logs, comparison report | PLANNED |
| M-3 | Baselines | Leakage tests pass for all features/splits; baselines reproduce from records; regional metrics with n; go/no-go note for neural | Test logs, experiment records | PLANNED |
| M-4 | Neural | Out-of-sample comparison vs baselines with variability; test window accessed once per frozen config; failures documented | Experiment records, reports | PLANNED |
| M-5 | UI | UA-01…UA-14 pass; reviewer can state origin/horizon/versions/baseline/limitation from UI alone; accessible alternatives | E2E/a11y logs, review notes | PLANNED |
| M-6 | Release | AC-01…AC-12 verified; licence/disclosure sign-off; recovery drill; guardrail coverage audit | Full evidence pack | PLANNED |
| M-7.x | Advanced items | Per accepted proposal | Per proposal | DEFERRED |

## Gate-outcome log (append-only)
| Date | Milestone | Outcome (PASS / FAIL / PASS-WITH-EXCEPTIONS) | Evidence links | Exceptions & owner acceptance |
|---|---|---|---|---|
| — | — | No gate has been evaluated yet | — | — |

## Rules
Statuses change only with evidence. A milestone cannot be PASS while an earlier one is not. Exceptions require the owner's explicit acceptance, recorded with reasons and a remediation plan. Use the checklist in ACCEPTANCE_CRITERIA.
