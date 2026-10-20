# Deployment

**Status:** DEFERRED to Phase 6 — **target undecided** (DEC-013). No deployment artifacts exist, and none should be created earlier. · **Source:** MP §20, §22 · **Related:** [SECURITY](../engineering/SECURITY.md), [OBSERVABILITY](../engineering/OBSERVABILITY.md), [RECOVERY](RECOVERY.md), [CONFIGURATION](CONFIGURATION.md)

## 1. Preconditions (MP §22: "Deployment should follow successful local validation and data licensing review")
- Phases 0–5 gates passed; reproducible local historical workflow.
- Licence review concluded for the intended audience (DEC-002; DATA_GOVERNANCE).
- Exposure level chosen (SECURITY §5) and DEC-013 decided via ADR.
- Software licence decided if the code will be public (DEC-014).

## 2. Planning requirements (MP §22)
| Requirement | Notes |
|---|---|
| Separate frontend and backend configuration | NFR-007 |
| Background jobs for ingestion, training, backtests | NFR-004; mechanism `OPEN` |
| Scheduled ingestion only at a cadence supported by the source | Respect provider terms/rate limits |
| Versioned model artifacts and reproducible environment definitions | Lockfile/image digests; artifact IDs |
| Health checks for services and pipelines | OBSERVABILITY §4 |
| Error monitoring and logs | Redaction required |
| Caching for repeated surface queries | Immutable-by-ID caching |
| Resource limits for expensive visualization and model jobs | Memory/time/concurrency caps |
| Documented recovery procedure for failed jobs | RECOVERY |

## 3. Target options (no selection)
Local-only workstation · single VM or container host · managed platform-as-a-service · private-network internal host. Criteria: licence permissions for display, security effort, cost (no paid infrastructure without need), job-scheduling needs, team size. First release favours a **reliable historical workflow over a fragile real-time architecture** (MP §22).

## 4. Release checklist (to be executed at Phase 6)
- [ ] All gates evidenced; AC-01…AC-12 verified
- [ ] Guardrails each enforced or exceptions recorded
- [ ] Secrets injected by platform; none in repo/images; rotation tested
- [ ] AuthN/Z, TLS, rate limits per exposure level
- [ ] Licence/disclosure review recorded; data-mode labels correct
- [ ] Backups configured; restore drill passed
- [ ] Monitoring/alerts configured; runbook accessible
- [ ] Rollback procedure tested
- [ ] Methodology and limitations published; research-only disclaimer present
- [ ] Reproduce a historical experiment on the deployed environment

### 4a. State of this checklist (2026-10-20) — nothing is ticked on purpose
| Item | Evidence today | Blocker |
|---|---|---|
| Gates evidenced | Only Phase F is owner-accepted; Phases 0–5 partial; Phase 0 gate unmet and the synthetic inference audit is `CLOSED — NO-GO` | Phase 0 evidence and owner decisions ([CORE_STATUS](../engineering/CORE_STATUS.md)) |
| Guardrails enforced | Many by offline tests; gaps listed in CORE_STATUS §4 | per-quote solver diagnostics, test-access log, mandatory GR-MOD-01 in notebooks |
| Secrets / AuthN / TLS / rate limits | None exist: the API is loopback-only, read-only, unauthenticated | no approved deployment target, user model or exposure level (DEC-013/014) |
| Licence / disclosure review | Not done; hosted dataset licence unverified, Cboe questions unsent ([DATA_ACQUISITION_AUTHORIZATION](../data/DATA_ACQUISITION_AUTHORIZATION.md)) | owner |
| Backups, monitoring, rollback | Not applicable until something is deployed | deployment decision |
| Reproduce a historical experiment | E-1/E-2/H1–H6 outputs were not saved outside Colab/Kaggle runtimes; they cannot be re-hashed | owner-run GPU session |
| CI | Workflow drafted ([tests.yml](../../.github/workflows/tests.yml)); **never run on a runner**; local passes are not CI passes | first push (owner) |

Engineering readiness of the offline test suite does not imply scientific GO or release authorization.

## 5. Rollback
Deployments are versioned; rollback = redeploy previous version with the same data/model artifact IDs; data stores are append/versioned so rollback does not require data restoration except after a failed migration (migration policy decided with DEC-009).

## 6. Out of scope until Phase 6
Infrastructure-as-code, container images, CI/CD deployment pipelines, domain names, cloud accounts.
