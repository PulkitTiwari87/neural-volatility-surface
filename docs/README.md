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
| Phase 0 scientific audit (reproduction, findings F1–F12, post-hoc analyses A2–A5, readiness) | [research/PHASE0_AUDIT](research/PHASE0_AUDIT.md) | decision.md PA-1…PA-5 |
| Phase 0 next steps to a real-data go/no-go | [research/NEXT_STEPS](research/NEXT_STEPS.md) | PHASE0_AUDIT, DATA_SOURCE_ASSESSMENT |
| A2d diagnostic: frozen design and results (synthetic, diagnostic only) | [research/PHASE0_A2D_DIAGNOSTIC_DESIGN](research/PHASE0_A2D_DIAGNOSTIC_DESIGN.md), [research/PHASE0_A2D_RESULTS](research/PHASE0_A2D_RESULTS.md) | PHASE0_A2B_SCREENING_DIAGNOSTIC §8 |
| A2b Stage 1 screening diagnostic and next-protocol proposal (read-only) | [research/PHASE0_A2B_SCREENING_DIAGNOSTIC](research/PHASE0_A2B_SCREENING_DIAGNOSTIC.md) | decision.md PA-1 |
| Phase 0 owner decision package (PA-1, PA-4, A2b/A2c audit, real-data checklist, approvals) | [research/PHASE0_OWNER_DECISION_PACKAGE](research/PHASE0_OWNER_DECISION_PACKAGE.md) | decision.md PA-1…PA-5 |
| Draft questions to Cboe (not sent) | [data/CBOE_LICENSING_QUESTIONS](data/CBOE_LICENSING_QUESTIONS.md) | DATA_SOURCE_ASSESSMENT §10.3 |
| Schemas | [data/DATA_DICTIONARY](data/DATA_DICTIONARY.md) | — |
| Licensing & governance | [data/DATA_GOVERNANCE](data/DATA_GOVERNANCE.md) | — |
| Quote filters | [data/QUOTE_QUALITY_POLICY](data/QUOTE_QUALITY_POLICY.md) | — |
| UI behaviour & acceptance | [design.md](../design.md) | [design/*](design/) |
| Phase 0 closure (exit-criteria status, owner-accepted CLOSED — NO-GO for the synthetic inference methodology) | [research/PHASE0_CLOSURE_RECORD](research/PHASE0_CLOSURE_RECORD.md) | [research/PHASE0_AUDIT](research/PHASE0_AUDIT.md) |
| Hosted dataset assessment for experiment E-1 (candidates, licence caveat, access method) | [data/HOSTED_DATASET_ASSESSMENT](data/HOSTED_DATASET_ASSESSMENT.md) | [data/DATA_SOURCE_ASSESSMENT](data/DATA_SOURCE_ASSESSMENT.md) |
| Experiments E-1 and E-2 results (hosted SPY data, GPU neural vs baselines; nearest- vs fixed-expiry label) | [research/E1_RESULTS](research/E1_RESULTS.md), [research/E2_FIXED_EXPIRY_RESULTS](research/E2_FIXED_EXPIRY_RESULTS.md) | [data/HOSTED_DATASET_ASSESSMENT](data/HOSTED_DATASET_ASSESSMENT.md) |
| Implementation status of the chain→surface→baseline path (spike) | [engineering/IMPLEMENTATION_MATRIX](engineering/IMPLEMENTATION_MATRIX.md) | `scripts/phase0_synthetic/chainpipe/` |
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
