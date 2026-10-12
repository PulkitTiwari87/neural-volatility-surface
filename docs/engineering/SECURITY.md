# Security

**Status:** PROPOSED (nothing implemented) · **Source:** MP §20, §22 · **Canonical for:** security requirements, threat considerations, controls · **Related:** PR.md SEC-001…007, guardrails GR-SEC, [DATA_GOVERNANCE](../data/DATA_GOVERNANCE.md), [architecture.md](../../architecture.md) §10

## 1. Scope and posture
A research application that handles **provider credentials** and **licensed data**. Initially local-only; additional exposure (team/public) raises requirements in §5. No security properties are claimed until implemented and tested.

## 2. Assets
Provider credentials; licensed raw/derived data; experiment records and model artifacts (integrity matters for reproducibility); compute resources (training jobs); source code and documentation integrity; reputation (misleading outputs).

## 3. Threats considered (initial)
| Threat | Example | Controls |
|---|---|---|
| Credential leakage | Key committed to Git, logged, shipped to browser | `.gitignore`, secret scanning (GR-SEC-01), env-only config, log redaction (GR-SEC-04), no provider calls from frontend (GR-SEC-02) |
| Licence breach via exposure | Public UI shows licensed quotes | Display/export gating by licence class; Phase 6 review (SEC-006) |
| Malicious/malformed input | Oversized or crafted API params, path traversal, injection | Schema validation, allow-lists, opaque IDs not paths, parameterized queries (SEC-002, GR-SEC-03) |
| Abuse of expensive operations | Unauthenticated training/backtest requests, DoS | AuthN/Z, rate limits, resource caps, job queue limits (SEC-003/004, GR-SEC-05) |
| Supply-chain risk | Malicious/compromised dependency | Minimal dependencies, pinned + hashed lockfile, review additions, dependency audit (GR-ENG-02) |
| Data integrity tampering | Altered raw data or artifacts changes results silently | Write-once raw zone, content hashes, lineage verification |
| Untrusted provider payloads | Unexpected formats/oversize | Validate before use; size limits; no code execution from data |
| Unsafe deserialization | Loading untrusted pickled models/data | Avoid pickle for untrusted/shared artifacts; prefer safe formats; verify hashes (artifact format decided with DEC-010) |
| Misleading outputs | Fake "live" labels, advice-like language | GR-DATA-07, GR-PRD-02 |

## 4. Requirements and controls
1. **Secrets:** only via environment/secret store, server-side; `.env` ignored; `.env.example` placeholders; rotation procedure documented; secrets never in logs, errors, fixtures, notebooks.
2. **Input validation** at every boundary (API, files, provider data, config).
3. **AuthN/AuthZ:** required before exposing beyond localhost; privileged scopes for jobs and data export; method `OPEN` (DEC-013).
4. **Rate limiting & quotas** for public/shared deployments.
5. **Transport security** (TLS) when networked.
6. **Least privilege:** ingestion jobs only hold provider keys; API has read-only access to serving zone except job metadata.
7. **Logging/audit:** security-relevant events (auth failures, job submissions, data exports) logged with IDs, no secrets.
8. **Dependency hygiene:** audit on addition and periodically; remove unused.
9. **Frontend:** no secrets or privileged tokens in bundle; content security policy and standard headers when served; no `eval`-style dynamic code from data.
10. **Destructive operations** (purge, overwrite, force operations) require explicit confirmation flags; default dry-run (GR-SEC-06).
11. **Backups** protect raw data and experiment records; backups are access-controlled and follow retention.

## 5. Exposure levels
| Level | Description | Additional requirements |
|---|---|---|
| L0 Local single user | Localhost only | Controls 1,2,6,8,10 |
| L1 Private network / team | Shared host | + AuthN/Z, TLS, audit logging, rate limits |
| L2 Public | Internet-facing | + licence clearance for every displayed datum, WAF/abuse protection, hardened deployment, security review, incident response contact |

Moving up a level requires an ADR and a Phase 6-style review.

## 6. Vulnerability reporting
Before any public release a private reporting channel is defined and documented here and in CONTRIBUTING. Until then: contact the project owner directly; do not post details publicly. (`OPEN`)

## 7. Validation
Secret-scan in CI; log-redaction test; API validation/authorization tests; bundle inspection for secrets; dependency audit report at Phase 6; recovery drill includes credential rotation; security review sign-off recorded in the Phase 6 gate.
