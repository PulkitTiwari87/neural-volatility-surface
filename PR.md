# PR.md — Product Requirements Document

**Status:** PROPOSED (requirements extracted from the baseline master plan; not yet reviewed/approved)
**Canonical for:** requirement IDs (`FR`, `SCI`, `DATA`, `UI`, `NFR`, `SEC`), objectives, acceptance criteria, traceability to the master plan.
**Source of truth:** [`NEURAL_VOLATILITY_SURFACE_FORECASTING_LAB_MASTER_PLAN.md`](NEURAL_VOLATILITY_SURFACE_FORECASTING_LAB_MASTER_PLAN.md) (hereafter **MP**, cited as `MP §n`). MP is never edited; this file derives from it.
**Related:** [architecture.md](architecture.md) · [guardrails.md](guardrails.md) · [design.md](design.md) · [decision.md](decision.md) · [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) · [docs/project/REQUIREMENTS.md](docs/project/REQUIREMENTS.md)

**Provenance labels used below:** `FACT` = stated in MP · `REC` = MP recommendation ("should", "suggested") · `ASSUMPTION` = inferred, needs confirmation · `HYPOTHESIS` = to be tested, not believed · `OPEN` = unresolved (see [decision.md](decision.md)). Every requirement carries one of these in the *Basis* column. Requirements marked `ASSUMPTION` originate from the foundation brief, not MP.

---

## 1. Problem statement

Implied-volatility (IV) surfaces vary across strike/moneyness and maturity and evolve over time. Whether a neural time-series model can forecast the *next* surface better than simple baselines is an empirical question that is easily answered wrongly: option data is sparse, noisy, licensed, and prone to look-ahead leakage; IV is inferred, not observed; and 3D visuals can mislead (MP §1, §3, §25).

The project builds an inspectable, reproducible research workflow — data → quote validation → IV → surface → features → baselines/neural models → walk-forward evaluation → visual inspection — in which every number is traceable to its inputs and every limitation is visible (MP §26).

**Core question (FACT, MP §1):** Given the option market observed at time *t*, how accurately can a model forecast the IV surface at a future horizon, such as the next trading day?

## 2. Objectives and non-objectives

### Objectives (FACT, MP §1 "Main deliverables")
- **O1** Historical options-data ingestion and validation pipeline.
- **O2** IV calculation and surface-construction engine.
- **O3** Research dataset and feature-engineering pipeline.
- **O4** Neural forecasting model *with* strong statistical baselines.
- **O5** Backtesting and model-evaluation framework.
- **O6** Interactive 3D surface explorer and forecast comparison.
- **O7** Research dashboard explaining model behavior and forecast errors.
- **O8** Reproducible experiment tracking and documentation.

### Non-objectives (FACT, MP §2 "Out of scope for the initial version")
- Automated trade execution; personalized investment advice; profitability claims.
- Scraping sites whose terms prohibit it; live exchange feeds without license.
- Treating every observed quote as a reliable executable price.
- Real-time/live updating in the first release (`REC`, MP §5, §22: historical mode first).
- Multi-underlying, multi-horizon, probabilistic, arbitrage-aware, regime-conditioned, intraday work — deferred to Phase 7 (MP §23).

## 3. Target users and research questions

**Primary user (FACT, MP §4):** a quantitative researcher or developer who wants to understand and test volatility-forecasting methods.

Research questions the platform must be able to answer (FACT, MP §4), each with a stable ID for traceability from experiments:

| ID | Question |
|---|---|
| RQ-01 | How does the smile/skew differ by maturity? |
| RQ-02 | How stable are surface shapes day to day? |
| RQ-03 | Which surface regions are hardest to forecast? |
| RQ-04 | Does the neural model outperform persistence and statistical baselines? |
| RQ-05 | How do results change in calm vs. high-volatility regimes? |
| RQ-06 | Are errors concentrated around earnings, macro events, or stress? |
| RQ-07 | Does the model produce smooth, plausible surfaces? |
| RQ-08 | Do forecasts violate basic option-price / no-arbitrage sanity checks? |
| RQ-09 | How sensitive are results to data quality, quote filters, interpolation? |

## 4. Functional requirements

Status of every requirement below: `PLANNED`. Phase = roadmap phase in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md).

| ID | Requirement | Basis | MP ref | Phase |
|---|---|---|---|---|
| FR-001 | Ingest historical option-chain snapshots for one defined underlying/market via a provider-adapter interface. | FACT | §2, §8.1 | 1 |
| FR-002 | Preserve raw source records (or normalized raw records) with source metadata, source timestamps and ingestion timestamps; raw snapshots immutable where licensing allows. | FACT | §5, §8.2, §19 | 1 |
| FR-003 | Normalize fields, units, timezones, contract IDs, missing-value representation; deduplicate by contract/timestamp/source rules. | FACT | §8.3–8.4 | 1 |
| FR-004 | Validate quotes (negative prices, crossed markets, zero/implausible bid-ask, stale timestamps, inconsistent metadata) and emit per-record quality flags stating why a quote was retained, excluded, or down-weighted. | FACT | §8.5, §8.8 | 1 |
| FR-005 | Align each quote with an underlying reference price/timestamp and with rate, dividend, day-count and calendar assumptions, all recorded. | FACT | §7, §8.6–8.7, §9 | 1 |
| FR-006 | Provide a configurable quote-selection policy (min quality, spread, staleness, zero-bid handling; midpoint as starting point) and support sensitivity comparison of policies. | FACT/REC | §8 "Quote-selection policy" | 1–2 |
| FR-007 | Compute IV from eligible quotes with a documented pricing model, bounded solver, convergence tolerances, and failure statuses; store solver diagnostics and inputs. | FACT | §9 | 2 |
| FR-008 | Construct standardized surface snapshots (documented coordinate system and maturity convention) with observed / interpolated / missing masks and construction method+version; save both raw IV observations and standardized grid. | FACT | §10 | 2 |
| FR-009 | Build a versioned research dataset: lagged surface features, surface-summary features, market-context features, with stored feature definitions. | FACT | §11 | 3 |
| FR-010 | Implement baselines before neural models: persistence; training-only historical average/change; linear/regularized regression; statistical time-series where supported; parametric surface baseline. | FACT | §13 | 3 |
| FR-011 | Implement chronological train/validation/test splits and walk-forward (rolling-origin) evaluation. | FACT | §14 | 3 |
| FR-012 | Implement an initial neural forecaster (MLP or justified alternative) and compare against baselines; sequence/latent-factor models only when data supports them. | FACT/REC | §13, §23 Ph4 | 4 |
| FR-013 | Compare at least grid forecasting against a lower-dimensional representation (factor/parametric). | FACT | §12 | 3–4 |
| FR-014 | Track experiments and artifacts so any published result can be reproduced from saved configuration and data versions. | FACT | §19, §24 | 3–4 |
| FR-015 | Persist forecasts (grid, values, origin, horizon, model/version, input-data version, uncertainty if any) in a forecast store. | FACT | §5, §7 | 4 |
| FR-016 | Expose a research API for: available underlyings/dates, chain snapshot + quality report, surface snapshot, forecast by model/origin/horizon, experiment metrics, feature/residual diagnostics, job start/inspect. Planning-level only — no contract is final. | FACT | §18 | 5–6 |
| FR-017 | Run training, backtests and ingestion as asynchronous/background jobs; the frontend never trains models. | FACT | §5, §20, §22 | 6 |
| FR-018 | Support exportable research results (e.g., tables/figures with their lineage metadata). Format `OPEN`. | FACT | §2 | 5 |

## 5. Scientific requirements

| ID | Requirement | Basis | MP ref |
|---|---|---|---|
| SCI-001 | Primary evaluation is chronological; never randomly shuffle dates across train/test. | FACT | §14 |
| SCI-002 | Scalers/transforms/imputation are fit on training-eligible data only. | FACT | §11, §14 |
| SCI-003 | Features use only information available at the forecast origin; no future prices/Greeks/revised data. | FACT | §11 |
| SCI-004 | Baselines are established before any neural claim; neural model is never presumed superior; improvement claims need out-of-sample evidence. | FACT | §13, §24 |
| SCI-005 | Metrics (MAE, RMSE, vol-point error, relative-to-persistence, directional accuracy if defined) are reported per maturity/moneyness/period/regime **with sample counts** and disclosed missing/excluded cells; no single aggregate score. | FACT | §14 |
| SCI-006 | Robustness checks: multiple periods, calm vs stressed regimes, quote-filter and interpolation sensitivity, liquid vs illiquid regions, dependence on few dates/contracts, feature ablations, failure cases. | FACT | §14 |
| SCI-007 | IV solver recovers known generating volatility from synthetic prices within tolerance; tests cover short maturities, deep ITM/OTM, invalid bounds, convergence failures. | FACT | §9, §21 |
| SCI-008 | Option prices are checked against theoretical bounds; the pricing model is appropriate to the instrument (e.g., American vs European exercise) and its limitations are documented. | FACT | §9 |
| SCI-009 | Observed, interpolated, extrapolated and missing surface values are always distinguishable; no silent extrapolation far beyond observed region. | FACT/REC | §10 |
| SCI-010 | Uncertainty estimates are labeled for what they are; "calibrated" is claimed only with coverage/calibration evidence. | FACT | §14, §15 |
| SCI-011 | Surfaces and forecasts get basic option-price / no-arbitrage sanity diagnostics (diagnostic only before Phase 7; constraints/parameterizations are Phase 7). | FACT | §4, §25, §23 Ph7 |
| SCI-012 | Explainability outputs state method and limitations (correlated features → unstable importance); never presented as causal proof. | FACT | §15 |
| SCI-013 | Every published result records: source+snapshot, processing version, quote-filter config, pricing/IV method, grid+interpolation version, feature version, train/val/test windows, model config+weights version, seed, evaluation code version, creation timestamp. | FACT | §19 |
| SCI-014 | The final test period remains untouched during model selection. | ASSUMPTION (stated in foundation brief; consistent with MP §14 "final untouched period") | §14 |

## 6. Data requirements

| ID | Requirement | Basis | MP ref |
|---|---|---|---|
| DATA-001 | Compare candidate data sources against the nine-row assessment table (coverage, granularity, quote fields, timestamps, adjustments, history, reliability, licensing, cost/limits) **before** selecting a provider. | FACT | §6 |
| DATA-002 | Licensing for storage, display and redistribution is reviewed before data is collected or published. | FACT | §6, §20, §25 |
| DATA-003 | Data freshness is labeled as exactly one of *historical*, *delayed*, *latest available*, *real-time licensed*; "live" is never used unless provider currency and latency are known. | FACT | §6 |
| DATA-004 | Raw data is separate from cleaned/derived data; corrections create a new version rather than mutating data behind a historical result. | FACT | §5, §19 |
| DATA-005 | No silent discarding: exclusions are recorded with reasons and counts. | FACT | §8 |
| DATA-006 | Market calendar (holidays, weekends, early closes, expiration conventions) and timestamp/timezone conventions are explicit and tested. | FACT | §8.7, §9 |
| DATA-007 | Processed datasets are versioned and reproducible. | FACT | §8.9, §19 |
| DATA-008 | The conceptual entities of MP §7 (underlying snapshot, option quote, market assumptions, derived IV observation, surface snapshot, forecast & experiment) are specified as formal schemas in the data dictionary once provider is chosen. | FACT | §7 |
| DATA-009 | Initial market and underlying universe: one market, one underlying universe. **OPEN** (DEC-001). | FACT (requirement) / OPEN (value) | §2 |

## 7. UI requirements

Details in [design.md](design.md) (canonical for UI behaviour) and [docs/design/VISUALIZATION_SPEC.md](docs/design/VISUALIZATION_SPEC.md).

| ID | Requirement | Basis | MP ref | Phase |
|---|---|---|---|---|
| UI-001 | Eight primary sections: Overview, Surface Explorer, Forecast Lab, Backtesting, Research & Explainability, Data Quality, Experiments & Models, Methodology. | REC | §17 | 5 |
| UI-002 | 3D surface explorer: rotate/pan/zoom; hover shows coordinates, IV, timestamp, data status; toggle observed/interpolated; expiration/moneyness slice; two-date comparison; camera reset. | FACT | §16A | 5 |
| UI-003 | Actual vs. forecast: side-by-side, overlay, difference surface (forecast − observed); choose origin, target date, model version; label historical backtest vs. prospective forecast. | FACT | §16B | 5 |
| UI-004 | Surface evolution animation in chronological order; interpolated points never imply observations. | FACT | §16C | 5 |
| UI-005 | 2D slices/heatmaps: smile, term structure, error heatmap, quote-quality heatmap, difference heatmap, ATM/skew/curvature time series. | FACT | §16D | 5 |
| UI-006 | Research charts: loss curves, baseline/model comparison, predicted-vs-actual, residual distribution, error over time, feature importance/correlation, regime performance. | FACT | §16E | 5 |
| UI-007 | Axes, units (decimal IV vs vol points), timestamps, forecast origin/horizon, model version and data status always visible. | FACT | §16 | 5 |
| UI-008 | Loading, empty, partial-data, error and stale-data states for every view. | FACT/REC | §16 | 5 |
| UI-009 | Accessible tables or 2D alternatives for every key 3D result. | FACT | §16 | 5 |
| UI-010 | Lineage drill-down from a grid point/surface to underlying quotes, IV calculation, construction method, forecast, baseline, and evidence. | FACT | §26, §23 Ph5 | 5 |
| UI-011 | Methodology section exposes assumptions, equations, definitions, limitations, data-source disclosures. | FACT | §17 | 5–6 |
| UI-012 | Dark and light themes if feasible; restrained motion; no effects that hinder numerical comparison. | REC | §17 | 5 |

## 8. Non-functional requirements

| ID | Requirement | Basis | MP ref |
|---|---|---|---|
| NFR-001 | Layers are independently testable with explicit contracts; data processing, training, inference and visualization are separated. | FACT | §5 |
| NFR-002 | Historical backtests are reproducible from saved data + configuration (deterministic where feasible). | FACT | §5, §21, §24 |
| NFR-003 | Frontend performs no heavy model training. | FACT | §5 |
| NFR-004 | Long-running training/backtests/ingestion are asynchronous, with resource limits. | FACT | §20, §22 |
| NFR-005 | Visualization downsamples/simplifies geometry as needed and never blocks the UI during loading. Quantitative targets `OPEN` until a feasibility test (DEC-008). | FACT (qualitative) / OPEN (numbers) | §16 |
| NFR-006 | Log ingestion, solver, training and API failures without leaking secrets; monitor data freshness and provider failures. | FACT | §20 |
| NFR-007 | Separate frontend/backend configuration; environment-based configuration. | FACT | §20, §22 |
| NFR-008 | Graceful handling of unavailable data and model failures. | FACT | §20 |
| NFR-009 | Historical-data mode is delivered before any live-update mode. | FACT | §5, §22 |
| NFR-010 | Cache repeated expensive queries where appropriate. | FACT | §20, §22 |
| NFR-011 | Documented recovery procedure for failed jobs; health checks for services and pipelines. | FACT | §22 |
| NFR-012 | Minimal complexity: YAGNI, explicit dependency management, no microservices/orchestration/registries/paid infrastructure without a documented need. | ASSUMPTION (foundation brief §3.3; MP §19 "premature infrastructure complexity") | §19 |

## 9. Security and governance requirements

| ID | Requirement | Basis | MP ref |
|---|---|---|---|
| SEC-001 | Provider credentials/secrets stay server-side; never in frontend code or Git. | FACT | §20 |
| SEC-002 | Validate all external inputs. | FACT | §20 |
| SEC-003 | Authentication and rate limiting if the app is publicly exposed. | FACT | §20 |
| SEC-004 | Access control on expensive/privileged operations (training, backtests, ingestion). | FACT | §18 |
| SEC-005 | Logs never contain secrets. | FACT | §20 |
| SEC-006 | Respect provider licensing and redistribution restrictions in storage, display and export. | FACT | §20 |
| SEC-007 | Product copy and behaviour: research/education only; no trading automation, personalized advice, or profitability claims; limitations visible. | FACT | header, §2 |

## 10. Constraints and assumptions

- **C-1** One market and underlying universe for the first milestone (MP §2). Value `OPEN`.
- **C-2** Free access to complete historical chains or real-time OPRA must not be assumed (MP §2).
- **C-3** First release favours a reliable historical workflow over real-time (MP §22).
- **A-1** *ASSUMPTION:* a Python data-science backend and separate web frontend (MP §18 "may use"); frameworks `OPEN`.
- **A-2** *ASSUMPTION:* PyTorch is a likely neural framework (MP §13 "PyTorch or another selected framework"); `OPEN`, see DEC-012/DEC-015.
- **A-3** *ASSUMPTION:* project is developed by a small team or individual; no dedicated platform engineering. Used only to justify NFR-012.
- **H-1** *HYPOTHESIS:* a lower-dimensional representation may be more stable than grid forecasting when history is limited (MP §12). To be tested, not assumed.
- **H-2** *HYPOTHESIS:* a neural model may add value beyond persistence/regression in some surface regions. Null result is an acceptable outcome (SCI-004).

## 11. Dependencies

- Data provider + licence (DEC-001/002/003) block Phase 1 implementation and gate everything after it.
- Pricing/coordinate/grid decisions (DEC-004/005/006) block Phase 2.
- Forecast representation (DEC-011) and chronological-split design block Phase 3/4.
- Stack decisions (DEC-007/008/009/010/013) are resolved by small feasibility experiments, not up front. See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for the dependency graph.

## 12. Acceptance criteria (product level)

The first release is acceptable only when all MP §24 Definition-of-Done items hold. They are restated here as checkable criteria; per-milestone criteria live in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) and [docs/project/ACCEPTANCE_CRITERIA.md](docs/project/ACCEPTANCE_CRITERIA.md).

| ID | Criterion (MP §24) | Verified by |
|---|---|---|
| AC-01 | Ingests documented, permitted data. | Data-source decision record + licence review (DATA-001/002). |
| AC-02 | Preserves timestamps and data lineage. | Lineage test from grid point → quote (UI-010, FR-002). |
| AC-03 | IV with tested numerical behaviour. | Scientific test suite SCI-007/008 passes. |
| AC-04 | Observed/interpolated/missing distinguishable. | Mask-preservation tests (SCI-009) + UI tests (UI-002..004). |
| AC-05 | Comparable surfaces across dates. | Coordinate-convention tests; documented grid version. |
| AC-06 | No look-ahead leakage. | Leakage tests (SCI-001..003) in CI. |
| AC-07 | Neural results compared with simple baselines. | Experiment report includes persistence + regression rows (SCI-004). |
| AC-08 | Out-of-sample metrics by region and period. | Evaluation report with sample counts (SCI-005). |
| AC-09 | Useful 2D and 3D visualizations. | UI acceptance in [design.md](design.md) §17. |
| AC-10 | Model version, origin, horizon, assumptions shown. | UI-007 checks. |
| AC-11 | Failure cases and limitations explained. | [docs/research/KNOWN_LIMITATIONS.md](docs/research/KNOWN_LIMITATIONS.md) current; Methodology page (UI-011). |
| AC-12 | Historical experiment reproducible from saved config + data versions. | Re-run test reproduces stored metrics within stated tolerance (SCI-013, NFR-002). |

## 13. Traceability: master plan → requirements

| MP section | Covered by |
|---|---|
| §1 Vision, deliverables | O1–O8, RQ, FR-* |
| §2 Scope | Non-objectives, C-1, C-2, DATA-009, SEC-007 |
| §3 Key concepts | [docs/project/GLOSSARY.md](docs/project/GLOSSARY.md), FR-007, FR-008 |
| §4 Users/questions | RQ-01…RQ-09 |
| §5 Architecture | NFR-001..003, NFR-009; [architecture.md](architecture.md) |
| §6 Data sources/governance | DATA-001..003 |
| §7 Data model | DATA-008, FR-005, FR-015 |
| §8 Ingestion/quality | FR-001..006, DATA-004..007 |
| §9 IV | FR-007, SCI-007, SCI-008 |
| §10 Surfaces | FR-008, SCI-009 |
| §11 Features | FR-009, SCI-002, SCI-003 |
| §12 Targets/horizons | FR-013, DEC-011 |
| §13 Modeling | FR-010, FR-012, SCI-004 |
| §14 Training/backtesting | FR-011, SCI-001, SCI-005, SCI-006, SCI-010, SCI-014 |
| §15 Explainability | UI-006, SCI-012 |
| §16 3D/2D experience | UI-002..009 |
| §17 Information architecture | UI-001, UI-011, UI-012 |
| §18 API/services | FR-016, SEC-004 |
| §19 Storage/reproducibility | FR-002, FR-014, SCI-013, DATA-004 |
| §20 Security/operations | SEC-001..006, NFR-004, NFR-006..008, NFR-010 |
| §21 Testing | [guardrails.md](guardrails.md), [docs/engineering/TESTING_STRATEGY.md](docs/engineering/TESTING_STRATEGY.md) |
| §22 Deployment/performance | NFR-004, NFR-007, NFR-009..011, DEC-013 |
| §23 Roadmap | [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) |
| §24 Definition of done | AC-01…AC-12 |
| §25 Risks | [docs/planning/RISKS.md](docs/planning/RISKS.md) |
| §26 Final standard | UI-010, SCI-013 |
