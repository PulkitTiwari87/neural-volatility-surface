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

## 5. Rollback
Deployments are versioned; rollback = redeploy previous version with the same data/model artifact IDs; data stores are append/versioned so rollback does not require data restoration except after a failed migration (migration policy decided with DEC-009).

## 6. Out of scope until Phase 6
Infrastructure-as-code, container images, CI/CD deployment pipelines, domain names, cloud accounts.
