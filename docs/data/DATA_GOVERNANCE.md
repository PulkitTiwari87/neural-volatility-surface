# Data Governance

**Status:** PROPOSED · **Canonical for:** licensing, provenance, retention, access, redistribution, data-mode labelling · **Source:** MP §2, §6, §19–§20, §25 · **Related:** [DATA_SOURCE_ASSESSMENT](DATA_SOURCE_ASSESSMENT.md), [SECURITY](../engineering/SECURITY.md), guardrails GR-DATA-04/06/07, GR-SEC-01

## 1. Principles
1. **Licence first.** No data is collected, stored, displayed, exported or published beyond what the licence permits (DATA-002, SEC-006).
2. **No market data in Git.** Ever. `data/` contents are ignored; only labelled synthetic fixtures (`*.synthetic.*`) may be tracked.
3. **Provenance on every record** (source, snapshot, ingestion time, versions) — see [DATA_DICTIONARY](DATA_DICTIONARY.md).
4. **Honest labelling** of data mode: `historical`, `delayed`, `latest_available`, `real_time_licensed`. "Live" only when truly real-time licensed with known latency (DATA-003).
5. **No unauthorized acquisition:** no scraping against terms; no credential sharing; no circumvention of rate limits.

## 2. Data classes
| Class | Examples | Handling |
|---|---|---|
| Licensed provider data (raw & derived) | Quotes, vendor IV, Greeks, snapshots | Stored per licence; access-controlled; not committed; export/display limited by licence |
| Public/reference data | Calendars, public rate series | Record source/licence; may be derived into assumption sets |
| Synthetic data | Test fixtures, feasibility samples | Labelled `origin = synthetic`, `*.synthetic.*`; safe to commit when small |
| Research outputs | Surfaces, forecasts, metrics | May be derivative of licensed data → inherit restrictions until licence review says otherwise |
| Secrets | API keys, tokens | Environment/secret store only; never in data, logs, or Git |

## 3. Licence review checklist (complete per candidate source, record in the ADR for DEC-002)
The step-by-step process, the owner-authorization record template and the register of what is authorized today are in [DATA_ACQUISITION_AUTHORIZATION](DATA_ACQUISITION_AUTHORIZATION.md); no acquisition happens without an owner-signed record.

- [ ] May raw responses be stored locally? For how long?
- [ ] May derived data (IV, surfaces, forecasts, metrics) be stored and shared? Under what attribution?
- [ ] May any data or derivatives be displayed in an application — to the owner only, to a team, to the public?
- [ ] May results/figures be published (papers, blog posts)? Restrictions on screenshots?
- [ ] Redistribution and sublicensing terms; number of users/seats.
- [ ] Display delay/real-time obligations; exchange fee or non-professional/professional status requirements.
- [ ] Termination terms: must data and derivatives be deleted?
- [ ] Automated access, rate limits, and scraping terms.

If any answer is unknown, the source's use is restricted to the narrowest interpretation until clarified.

**Phase 0 status (2026-10-12):** per-candidate answers and the unresolved items are in [DATA_SOURCE_ASSESSMENT](DATA_SOURCE_ASSESSMENT.md) §5 and §7. Only Cboe's agreement and data policies were read directly; all other providers' terms are unread or unstated. Until blockers B1–B4 close, the working assumption is **internal, local, single-user research use only — no public display, no committed data, no sharing of raw files**.

## 4. Provenance and versioning
Raw records are immutable; corrections create new versions; every result pins data versions ([DATA_VERSIONING](DATA_VERSIONING.md)). Exclusions are recorded with reasons (GR-DATA-02/03).

## 5. Access and handling
- Principle of least privilege: provider credentials readable only by ingestion jobs.
- Public exposure of data/derived values requires a recorded licence conclusion (Phase 6 gate).
- Exports embed source/licence metadata; the export function refuses classes the licence forbids.
- Logs exclude raw payloads where licence forbids retention and never include secrets.

## 6. Retention and deletion
Retain raw data as long as licence and research reproducibility need; define a documented purge procedure (including derived data where the licence requires) before collecting data; test the procedure on synthetic data. Backups follow the same retention.

## 7. Incident handling
Suspected leak of secrets or licensed data: stop the pipeline, rotate credentials, assess scope, document, notify the owner (and provider if required by terms), fix root cause, add a regression check (GR-SEC-01).

## 8. Disclosures
README and Methodology page state: data source, data mode, coverage, known gaps, licence notices, and the research-only disclaimer. Content is generated from dataset metadata where possible so labels cannot drift.

## 9. Validation
Release checklist (Phase 6 gate); CI check that no data files are tracked; tests for data-mode labels and export metadata; periodic licence re-check (review trigger in DEC-002).
