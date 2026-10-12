# Requirements — Organization and Traceability

**Status:** PROPOSED · **Canonical requirement text lives in [PR.md](../../PR.md)**; this document explains the structure and provides cross-reference matrices without restating requirements.

## Requirement categories (organization requested by the brief)
| Category | ID prefix | Where |
|---|---|---|
| Functional | `FR-` | PR.md §4 |
| Scientific | `SCI-` | PR.md §5 |
| Data | `DATA-` | PR.md §6 |
| UI | `UI-` | PR.md §7 (+ [design.md](../../design.md)) |
| Operational / non-functional | `NFR-` | PR.md §8 |
| Security & governance | `SEC-` | PR.md §9 |
| Research questions | `RQ-` | PR.md §3 |
| Product acceptance | `AC-` | PR.md §12 |

*Operational* requirements are NFR-004, 006, 007, 009, 010, 011 (jobs, logging, config, historical mode, caching, recovery).

## Provenance of each requirement
`FACT` (in master plan) · `REC` (master-plan recommendation) · `ASSUMPTION` · `HYPOTHESIS` · `OPEN`. Source-versus-open split: all decisions that MP explicitly leaves open (market, provider, pricing model for each instrument, grid, interpolation, frameworks, storage, tracking, architecture, deployment) are in [decision.md](../../decision.md); requirements never presuppose them.

## Lifecycle
`PLANNED` → `IN_PROGRESS` → `IMPLEMENTED` (code merged, tests pass, evidence linked) → `VALIDATED` (scientific/acceptance evidence recorded). Status of every requirement is currently `PLANNED`. Changes to a requirement: edit PR.md, add a CHANGELOG entry; never renumber (retire with `SUPERSEDED by …`).

## Matrix: requirement → phase → primary guardrails → verification home
| Requirements | Phase | Guardrails | Tests live in |
|---|---|---|---|
| FR-001…006, DATA-004…007 | 1 | GR-DATA-01…08, GR-QNT-05 | `backend/tests/{unit,integration}` |
| FR-007, SCI-007/008 | 2 | GR-QNT-01…06 | `backend/tests/scientific` |
| FR-008, SCI-009/011 | 2 | GR-DATA-05, GR-QNT-07 | `backend/tests/{unit,scientific}` |
| FR-009…011, FR-013, SCI-001…003, SCI-005/006, SCI-014 | 3 | GR-LEAK-01…06, GR-MOD-01…03 | `backend/tests/scientific` |
| FR-012, FR-014, FR-015, SCI-004, SCI-010, SCI-013 | 3–4 | GR-MOD-01…06 | `backend/tests/{scientific,integration}` |
| FR-016…018, NFR-003…005, 008, 010 | 5–6 | GR-SEC-02/03/05 | `backend/tests/integration`, `tests/` |
| UI-001…012 | 5 | GR-PRD-02…05 | `tests/end_to_end`, frontend tests |
| SEC-001…007 | 1, 6 | GR-SEC-01…06, GR-PRD-01/02 | CI checks, API tests |
| DATA-001…003, DATA-009 | 0 | GR-DATA-06/07 | review + ADR evidence |
| NFR-001/002/012 | all | GR-ENG-01…07 | architecture tests, repro tests |

## Known requirement gaps (to resolve)
- Quantitative performance targets (NFR-005, UA-14) — pending feasibility data.
- Minimum-sample thresholds and tolerance values (`TBD(Phase n)`) — set from evidence, not here.
- Export format (FR-018) — `OPEN`.
