# Recovery

**Status:** PROPOSED (procedures to be written and **drilled** in Phase 6; nothing exists to recover yet) · **Source:** MP §20, §22 ("A documented recovery procedure for failed jobs") · **Related:** [STORAGE_DESIGN](../architecture/STORAGE_DESIGN.md), [OBSERVABILITY](../engineering/OBSERVABILITY.md), [SECURITY](../engineering/SECURITY.md), NFR-008/011

## 1. Design properties that make recovery simple
- Jobs are **idempotent by input version** and publish **atomically** (staging → promote); a crashed job leaves no visible partial output.
- Raw data is write-once; derived data is rebuildable from raw + config + code version.
- Every result pins versions, so re-running reproduces it (or reveals a difference to investigate).

## 2. Failure scenarios and procedures (to be completed and drilled)
| Scenario | Detection | Procedure outline |
|---|---|---|
| Ingestion job fails midway | Job status/log; staging dir present | Discard staging; fix cause (provider outage, auth, format); re-run; confirm raw snapshot ID/reconciliation |
| Provider outage or format change | Elevated error rate; validation failure spike | Pause scheduled ingestion; record gap in data-quality metadata; update adapter; backfill if provider allows |
| Provider restates history | Hash mismatch on re-pull | Ingest as new raw version; mark affected experiments; do not overwrite |
| IV/surface job crash | Job failure | Re-run from versioned inputs; verify output ID matches expectation |
| Training job crash / OOM | Job status | Resume from checkpoint if recorded, else re-run with seeds and config; compare to run record |
| Corrupted artifact or storage | Hash verification failure | Quarantine; rebuild derived from raw; restore raw from backup |
| Lost/compromised credentials | Alert, audit log, provider notice | Rotate keys; invalidate sessions; review logs; see DATA_GOVERNANCE incident handling |
| Bad deployment | Health checks, errors | Roll back to previous version (DEPLOYMENT §5) |
| Accidental deletion | Missing IDs | Restore from backup; rebuild derived |
| Stale data in UI | Freshness metric | Show stale state; re-run ingestion; investigate cadence |

## 3. Backup policy (to be set; `TBD(Phase 6)`)
Back up raw zone and experiment records (hard to recreate); verify backups by restore tests; protect backups with the same access controls and retention rules as primary data.

## 4. Drills (Phase 6 gate)
1. Kill an ingestion job mid-run → recover; 2. corrupt a derived artifact → detect via hash and rebuild; 3. restore raw + records onto a clean environment and reproduce one historical experiment (AC-12); 4. rotate provider credentials. Record duration, issues, and fixes.

## 5. Post-incident
Write a short incident note: what happened, impact on published results, fix, regression test added. Update KNOWN_LIMITATIONS if results were affected.

## 6. Validation
Fault-injection tests on synthetic data (crash points in staging/promote); idempotent re-run tests; restore drill logs attached to the gate.
