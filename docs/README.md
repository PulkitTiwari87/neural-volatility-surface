# Documentation Index

**Status:** PROPOSED. **Purpose:** one canonical location per topic. When two documents touch the same topic, the canonical one owns the requirement/definition; others link to it. Do not copy sections between documents.

**Baseline specification (read-only):** [../NEURAL_VOLATILITY_SURFACE_FORECASTING_LAB_MASTER_PLAN.md](../NEURAL_VOLATILITY_SURFACE_FORECASTING_LAB_MASTER_PLAN.md) (MP).

## Canonical locations

| Topic | Canonical document | Supporting documents |
|---|---|---|
| Requirement IDs, objectives, acceptance (product level) | [PR.md](../PR.md) | [project/REQUIREMENTS](project/REQUIREMENTS.md), [project/ACCEPTANCE_CRITERIA](project/ACCEPTANCE_CRITERIA.md) |
| Vision & scope | [project/VISION](project/VISION.md), [project/SCOPE](project/SCOPE.md) | PR.md §2 |
| Terminology | [project/GLOSSARY](project/GLOSSARY.md) | — |
| Guardrails (rules + enforcement) | [guardrails.md](../guardrails.md) | [engineering/TESTING_STRATEGY](engineering/TESTING_STRATEGY.md) |
| Open decisions & options | [decision.md](../decision.md) | [architecture/ADR/](architecture/ADR/), [planning/OPEN_QUESTIONS](planning/OPEN_QUESTIONS.md) |
| Phases, gates, out-of-scope | [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) | [planning/ROADMAP](planning/ROADMAP.md), [planning/MILESTONES](planning/MILESTONES.md) |
| Risks | [planning/RISKS](planning/RISKS.md) | MP §25 |
| Architecture principles & module boundaries | [architecture.md](../architecture.md) | [architecture/SYSTEM_OVERVIEW](architecture/SYSTEM_OVERVIEW.md) |
| Stage-by-stage data flow & versioning points | [architecture/DATA_FLOW](architecture/DATA_FLOW.md) | [data/DATA_VERSIONING](data/DATA_VERSIONING.md) |
| Storage zones & layout | [architecture/STORAGE_DESIGN](architecture/STORAGE_DESIGN.md) | DEC-009 |
| API shape (planning-level) | [architecture/API_CONTRACTS](architecture/API_CONTRACTS.md) | DEC-007 |
| Research method overview | [research/RESEARCH_METHODOLOGY](research/RESEARCH_METHODOLOGY.md) | — |
| IV calculation | [research/IV_METHODOLOGY](research/IV_METHODOLOGY.md) | DEC-004 |
| Surface construction & coordinates | [research/SURFACE_CONSTRUCTION](research/SURFACE_CONSTRUCTION.md) | DEC-005, DEC-006 |
| Features | [research/FEATURE_CATALOG](research/FEATURE_CATALOG.md) | — |
| Forecast targets & models | [research/FORECASTING_STRATEGY](research/FORECASTING_STRATEGY.md) | DEC-011, DEC-012 |
| Evaluation, splits, metrics | [research/EVALUATION_PROTOCOL](research/EVALUATION_PROTOCOL.md) | — |
| Uncertainty | [research/UNCERTAINTY_AND_CALIBRATION](research/UNCERTAINTY_AND_CALIBRATION.md) | — |
| Limitations | [research/KNOWN_LIMITATIONS](research/KNOWN_LIMITATIONS.md) | — |
| Data source selection (evidence, licence findings, blockers) | [data/DATA_SOURCE_ASSESSMENT](data/DATA_SOURCE_ASSESSMENT.md) | DEC-001/002/003 |
| Minimum viable dataset, Phase 0 success criteria, synthetic sample, feasibility experiment | [research/PHASE0_FEASIBILITY_PLAN](research/PHASE0_FEASIBILITY_PLAN.md) | EVALUATION_PROTOCOL §8 |
| Phase 0 synthetic experiment results (tests, scenarios, study, deviations) | [research/PHASE0_SYNTHETIC_RESULTS](research/PHASE0_SYNTHETIC_RESULTS.md) | `scripts/phase0_synthetic/`, ADR-0003 |
| Draft questions to Cboe (not sent) | [data/CBOE_LICENSING_QUESTIONS](data/CBOE_LICENSING_QUESTIONS.md) | DATA_SOURCE_ASSESSMENT §10.3 |
| Schemas | [data/DATA_DICTIONARY](data/DATA_DICTIONARY.md) | — |
| Licensing & governance | [data/DATA_GOVERNANCE](data/DATA_GOVERNANCE.md) | — |
| Quote filters | [data/QUOTE_QUALITY_POLICY](data/QUOTE_QUALITY_POLICY.md) | — |
| UI behaviour & acceptance | [design.md](../design.md) | [design/*](design/) |
| Coding standards | [engineering/CODING_STANDARDS](engineering/CODING_STANDARDS.md) | — |
| Security | [engineering/SECURITY](engineering/SECURITY.md) | guardrails GR-SEC |
| Observability / performance | [engineering/OBSERVABILITY](engineering/OBSERVABILITY.md), [engineering/PERFORMANCE](engineering/PERFORMANCE.md) | — |
| Local dev, config, deploy, recovery | [operations/*](operations/) | — |
| Templates | [templates/*](templates/) | `.github/` templates |
| AI-agent working rules | [CLAUDE.md](../CLAUDE.md) | — |

## Standard document header

Substantive documents begin with: **Status** (one of `PLANNED`, `PROPOSED`, `IN_PROGRESS`, `IMPLEMENTED`, `VALIDATED`, `BLOCKED`, `DEFERRED`), purpose/scope, canonical-for line, related documents; and end (or contain) validation/acceptance criteria. Facts from the master plan are cited `MP §n`. Items not supported by the master plan are labelled `ASSUMPTION`, `PROPOSED`, `OPEN` or `NEEDS RESEARCH`.

## Maintenance

Any change to architecture, methodology, data schemas, API contracts, guardrails or decisions must update the canonical document **in the same change** ([CLAUDE.md](../CLAUDE.md) §12). Keep this index current when documents are added or moved.
