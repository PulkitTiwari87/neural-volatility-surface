# decision.md — Decision Register

**Status:** IN_PROGRESS (register established; **no decision below is finalized**)
**Canonical for:** open technical/scientific/legal decisions, their options, evidence needed, and review triggers. Accepted outcomes are recorded as ADRs in [docs/architecture/ADR/](docs/architecture/ADR/) and linked here; the template is [ADR-0001](docs/architecture/ADR/ADR-0001-template.md).
**Related:** [PR.md](PR.md) · [architecture.md](architecture.md) · [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) · [docs/planning/OPEN_QUESTIONS.md](docs/planning/OPEN_QUESTIONS.md) · [docs/architecture/ADR/ADR-0002-initial-technical-questions.md](docs/architecture/ADR/ADR-0002-initial-technical-questions.md)

## How to read this register

**Status values:** `OPEN` (nothing chosen, no recommendation yet) · `NEEDS RESEARCH` (cannot be responsibly proposed without evidence) · `PROPOSED` (a recommendation exists with reasons; **not approved**) · `DECIDED` (approved, ADR linked) · `SUPERSEDED`. At the time of writing, **zero** decisions are `DECIDED`.

**A `PROPOSED` recommendation is a starting hypothesis for a feasibility experiment, not a commitment.** Code must not be written that depends on a non-`DECIDED` choice in a way that is expensive to reverse (see [CLAUDE.md](CLAUDE.md) "Open decisions").

**Owner** is a responsible *role*, not a named person; assign people when staffing is known.

**Resolution gates** (which phase may not start until the decision is `DECIDED`) are in the summary table and in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md).

## Summary

| ID | Decision | Status | Blocks | Owner role |
|---|---|---|---|---|
| DEC-001 | Initial options market & underlying universe | NEEDS RESEARCH | Phase 0 exit, all later | Project owner / quant lead |
| DEC-002 | Historical data provider & licensing | NEEDS RESEARCH | Phase 1 start | Project owner / data engineer |
| DEC-003 | Historical coverage & snapshot frequency | NEEDS RESEARCH | Phase 0 exit | Quant lead / data engineer |
| DEC-004 | Initial pricing model & instrument assumptions | PROPOSED (conditional on DEC-001) | Phase 2 | Quant lead |
| DEC-005 | Moneyness convention & maturity definition | PROPOSED | Phase 2 | Quant lead |
| DEC-006 | Surface grid & interpolation method | NEEDS RESEARCH | Phase 2 exit | Quant lead |
| DEC-007 | Backend API framework | PROPOSED | Phase 5 (API) | Backend lead |
| DEC-008 | Frontend framework & charting/3D technology | NEEDS RESEARCH | Phase 5 | Frontend lead |
| DEC-009 | Storage & analytical file formats | PROPOSED | Phase 1 (raw store) | Data engineer |
| DEC-010 | Experiment tracking & artifact versioning | PROPOSED | Phase 3 | ML engineer |
| DEC-011 | Initial forecasting representation | PROPOSED | Phase 3 | Quant lead / ML engineer |
| DEC-012 | Initial neural architecture | PROPOSED | Phase 4 | ML engineer |
| DEC-013 | Deployment target | OPEN | Phase 6 | Project owner |
| DEC-014 | Project software licence (added) | OPEN | Public release | Project owner |
| DEC-015 | Python version, environment & dependency management (added) | OPEN | First code commit | Backend lead |

DEC-014 and DEC-015 are additions beyond the 13 required: the brief demands the licence be documented as open, and no manifest/lockfile may be created until DEC-015 is decided.

---

## DEC-001 — Initial options market and underlying universe

- **Status:** NEEDS RESEARCH (PROPOSED direction below is conditional only)
- **Context:** MP §2 requires one market and one underlying universe for the first milestone; MP §6 warns against assuming free access to complete historical chains or real-time OPRA. The choice drives data availability, exercise style (DEC-004), liquidity/grid density (DEC-006) and licensing (DEC-002).
- **Options:** (a) one broad-index option series; (b) one liquid single-name equity/ETF; (c) a non-US market; (d) a small basket (rejected for v1 by MP §2 "one underlying universe" intent and Phase 7 deferral).
- **Criteria:** data obtainable under a licence permitting required storage/display; history length; strike/expiry density across the standardized grid; quote quality/liquidity; exercise style simplicity; presence of dividends/corporate actions complexity; relevance to the research questions (RQ-01…09).
- **Evidence required:** results of [DATA_SOURCE_ASSESSMENT](docs/data/DATA_SOURCE_ASSESSMENT.md) for ≥2 candidate (underlying, provider) pairs; a measured count of usable snapshots and per-snapshot strike/expiry counts from a sample.
- **Recommendation:** none final. *PROPOSED direction (conditional):* evaluate index options before single-name equities, because European-style, cash-settled contracts remove the early-exercise issue flagged in MP §9. Drop this direction if licensing or history makes it infeasible.
- **Consequences:** fixes `DATA-009`; constrains DEC-002..006; defines what "enough clean historical snapshots" means for the Phase 0 exit.
- **Review trigger:** Phase 0 exit review, or discovery that the chosen provider cannot supply the needed history.

## DEC-002 — Historical data provider and licensing

- **Status:** NEEDS RESEARCH
- **Context:** MP §6: "The first technical decision is the data provider." Licence terms govern storage, display, redistribution, and whether a public deployment is possible at all.
- **Options (categories from MP §6):** licensed market-data vendors; broker APIs; academic/research datasets; public prototyping datasets. Specific vendors are enumerated in [DATA_SOURCE_ASSESSMENT](docs/data/DATA_SOURCE_ASSESSMENT.md) as *unverified candidates*.
- **Criteria:** the nine-row table in MP §6 (coverage, granularity, quote fields, timestamps, adjustments, depth, reliability, licensing, cost/limits); ability to preserve raw responses; reproducibility (stable snapshots/versioning from provider).
- **Evidence required:** written licence/ToS review per candidate (storage, derived-data display, redistribution, publication of results); price quote or free-tier limits; a sample extract proving field coverage; provider's correction policy.
- **Recommendation:** none. Do not select a provider from familiarity.
- **Consequences:** determines `SEC-006`, whether the app can be public (DEC-013), whether `data/samples/` can include any real data (default: no), and the provider adapter design.
- **Review trigger:** any licence/ToS change; cost change; Phase 0 exit.

## DEC-003 — Historical coverage and snapshot frequency

- **Status:** NEEDS RESEARCH
- **Context:** MP §6 distinguishes end-of-day, intraday and streaming; MP §12 starts with the next-session surface; MP §23 Ph7 defers intraday.
- **Options:** end-of-day (EOD) snapshots; fixed intraday snapshots; streaming.
- **Criteria:** enough independent surfaces for chronological train/validation/test and walk-forward (a *minimum viable dataset*, to be defined quantitatively in Phase 0); regime diversity (calm and stressed periods, SCI-006); consistency of quote timestamps vs underlying timestamps.
- **Evidence required:** count of trading days with complete-enough chains; coverage of at least one stressed regime; timestamp alignment audit.
- **Recommendation:** *PROPOSED (conditional on provider):* EOD snapshots for v1, consistent with MP §22 and the next-trading-day target. Minimum history length is **not** asserted here.
- **Consequences:** sets sample size ceiling, hence model-capacity limits (DEC-012) and statistical power of conclusions.
- **Review trigger:** Phase 0 minimum-viable-dataset test fails or passes marginally.

## DEC-004 — Initial pricing model and instrument assumptions

- **Status:** PROPOSED (conditional on DEC-001)
- **Context:** MP §9 requires a pricing model "appropriate to the instrument" and flags American-style exercise as a hazard for simple European Black–Scholes.
- **Options:** (a) European Black–Scholes–Merton with continuous dividend yield or forward-based (Black-76) inputs; (b) discrete-dividend adjustments; (c) American-option model (lattice/PDE/approximation) with early-exercise handling; (d) use provider IV (rejected as primary: IV must be reproducible and inspectable, MP §3, §9).
- **Criteria:** correctness for the chosen instrument; testability against synthetic known-vol prices (SCI-007); ability to document limitations; compute cost.
- **Evidence required:** confirmed exercise style, settlement and dividend treatment of the chosen contracts (from contract specs, **verified against the provider's data**); error-magnitude study if a European model is applied to American contracts.
- **Recommendation:** *PROPOSED:* European model on forward price for European-style instruments only; if DEC-001 selects American-style contracts, either restrict to regions where early-exercise premium is negligible (to be shown, not assumed) or adopt an American model. Never apply a European model silently to American options.
- **Consequences:** defines the `pricing/` module contract, solver bounds, and quote-eligibility rules.
- **Review trigger:** DEC-001 decided; solver test failures concentrated in deep-ITM/short-maturity regions.

## DEC-005 — Moneyness convention and maturity definition

- **Status:** PROPOSED
- **Context:** MP §10: use a standardized system such as log-moneyness and time to maturity, "with the exact convention recorded".
- **Options (moneyness):** raw strike *K*; `K/S`; `ln(K/S)`; forward log-moneyness `ln(K/F)` with `F = S·e^{(r−q)T}`; delta-based. **(maturity):** calendar-day ACT/365 years; trading-day /252; business-day with calendar; time to exchange settlement time vs date only.
- **Criteria:** comparability across dates; independence from rate/dividend assumption noise; invertibility to strikes; behaviour for very short expiries; consistency with pricing model (DEC-004).
- **Evidence required:** sensitivity of the surface to the choice on a sample; effect on grid density.
- **Recommendation:** *PROPOSED:* forward log-moneyness and a documented calendar-based year fraction (day-count `OPEN` until DEC-001/004 settle which instruments and settlement times apply). Convention is versioned and recorded in every surface snapshot.
- **Consequences:** fixes the feature and API coordinate semantics; changing it later invalidates stored surfaces (new version required, DATA-004).
- **Review trigger:** sensitivity study shows material difference; instrument change.

## DEC-006 — Surface grid and interpolation method

- **Status:** NEEDS RESEARCH
- **Context:** MP §10 lists candidate methods (nearest/linear, shape-preserving, spline, parametric, arbitrage-aware later) and requires masks and no silent extrapolation.
- **Options:** grid resolution (coarse/medium/fine, evenly vs. non-uniform); interpolation (nearest, linear, shape-preserving, smoothing spline, parametric fit).
- **Criteria:** fidelity to observations at observed nodes; smoothness without inventing structure; behaviour in sparse regions; mask correctness; effect on forecast metrics (RQ-09).
- **Evidence required:** per-snapshot density statistics; comparison of ≥2 methods on held-out observed points (leave-out reconstruction error) and on downstream baseline metrics.
- **Recommendation:** none on resolution. *Principle (not a method choice):* start with the most transparent method that supports masks (e.g., linear within the observed hull) as the baseline for comparison.
- **Consequences:** determines target dimensionality (DEC-011) and error-region definitions.
- **Review trigger:** Phase 2 comparison results.

## DEC-007 — Backend API framework

- **Status:** PROPOSED
- **Context:** MP §18: "may use a Python backend for data science… precise framework is a later decision." The API is thin and read-heavy plus job control; business logic lives in domain modules (see [architecture.md](architecture.md)).
- **Options:** FastAPI; Flask; Django (+DRF); a minimal ASGI toolkit; defer API (CLI/files only) until Phase 5.
- **Criteria:** typed request/response schemas that double as contract tests; async job support; small dependency footprint; team familiarity; security tooling (auth/rate-limit options).
- **Evidence required:** a spike serving one surface-snapshot endpoint with schema validation, input validation tests, and a background-job stub.
- **Recommendation:** *PROPOSED:* FastAPI-class framework (typed schemas → machine-readable contract) — **conditional on the spike**. No API code before Phase 5 unless a pipeline phase needs it.
- **Consequences:** shapes [API_CONTRACTS](docs/architecture/API_CONTRACTS.md) and frontend client generation.
- **Review trigger:** spike result; need for built-in admin/auth that favours another framework.

## DEC-008 — Frontend framework and charting/3D technology

- **Status:** NEEDS RESEARCH
- **Context:** MP §16: "React with a charting library… Three.js through React Three Fiber… selected during technical design after a small feasibility test."
- **Options:** React + (R3F | Plotly 3D | deck.gl | vtk.js) for 3D; (Plotly.js | ECharts | visx | Recharts | Vega-Lite) for 2D; alternatives to React (Svelte, Vue); or a Python-native UI (Streamlit/Dash) for early phases.
- **Criteria:** exact value inspection on hover; accessibility and 2D/tabular alternatives (UI-009); rendering performance on target grids (NFR-005); mask/status encoding; export; bundle size; theming; test-ability.
- **Evidence required:** feasibility prototype (throwaway, not committed as product code) rendering a synthetic surface with observed/interpolated masks, hover readout, two-surface diff, and keyboard-accessible table alternative; measured frame time and load time.
- **Recommendation:** none. MP names React + R3F as a *possibility*, not a decision.
- **Consequences:** fixes `frontend/` toolchain and the visual encoding in [VISUALIZATION_SPEC](docs/design/VISUALIZATION_SPEC.md).
- **Review trigger:** feasibility result; accessibility audit failures.

## DEC-009 — Storage and analytical file formats

- **Status:** PROPOSED
- **Context:** MP §19: relational DB for metadata/experiments, columnar files for large analytical data; "follow a small benchmark rather than premature infrastructure complexity."
- **Options:** columnar files (Parquet/Arrow) + embedded query engine; embedded relational DB (SQLite); server RDBMS (PostgreSQL); object store; hybrid.
- **Criteria:** immutability & versioning of raw snapshots; query patterns (by date, by snapshot, by contract); dataset size from DEC-001/003; reproducibility; operational burden; licence-compliant deletion.
- **Evidence required:** size estimate of raw + derived data; benchmark of the three query patterns on a synthetic dataset of that size.
- **Recommendation:** *PROPOSED:* file-based immutable raw store plus embedded metadata store (no server database) for Phase 1–4; revisit at Phase 6 only if concurrency or multi-user needs appear.
- **Consequences:** shapes [STORAGE_DESIGN](docs/architecture/STORAGE_DESIGN.md) and backup/recovery ([RECOVERY](docs/operations/RECOVERY.md)).
- **Review trigger:** benchmark result; multi-user requirement.

## DEC-010 — Experiment tracking and artifact versioning

- **Status:** PROPOSED
- **Context:** MP §19 lists required metadata; MP §5 mentions a "Model / Experiment Registry". Foundation brief forbids complex registries without documented need.
- **Options:** structured run directories (config + metrics + hashes, schema in [EXPERIMENT_TEMPLATE](docs/templates/EXPERIMENT_TEMPLATE.md)); MLflow; DVC; Weights & Biases (hosted, third-party data egress); custom DB tables.
- **Criteria:** captures SCI-013 fields; reproducibility; offline-capable; data-licence safety (no uploading licensed data to third parties); effort.
- **Evidence required:** reproduce one baseline run from its stored record on a clean checkout.
- **Recommendation:** *PROPOSED:* start with structured, hashed run records; adopt a tool only when a documented limitation appears.
- **Consequences:** defines `experiments/` and `artifacts/` conventions.
- **Review trigger:** run count or collaboration needs outgrow files.

## DEC-011 — Initial forecasting representation

- **Status:** PROPOSED
- **Context:** MP §12: four representations (grid, latent factor, parametric, change forecasting); must compare grid with a lower-dimensional form.
- **Options:** absolute grid IV; grid change vs. latest surface; PCA/autoencoder latent factors; parametric-fit parameters.
- **Criteria:** stability with limited history (H-1); evaluability on the common grid; ability to reconstruct masked regions honestly; interpretability.
- **Evidence required:** persistence and regression results on candidate representations over chronological splits.
- **Recommendation:** *PROPOSED:* primary = change forecasting on the standardized grid (next valid session); comparator = a low-dimensional factor representation. Evaluate all on the same observed grid cells.
- **Consequences:** defines dataset schema and evaluation targets.
- **Review trigger:** Phase 3 baseline results.

## DEC-012 — Initial neural architecture

- **Status:** PROPOSED
- **Context:** MP §13 recommended order: persistence → regression → MLP → TCN/GRU → latent-factor → complexity vs. out-of-sample benefit.
- **Options:** MLP on lagged features; TCN; GRU/LSTM; Transformer; autoencoder + temporal model.
- **Criteria:** data volume sufficiency; out-of-sample improvement over baselines; stability across seeds; runtime; interpretability.
- **Evidence required:** Phase 3 baselines exist and leakage tests pass (gate); multi-seed MLP results.
- **Recommendation:** *PROPOSED:* MLP first, per MP; no sequence/Transformer model unless data volume and MLP results justify (SCI-004). Null results are valid outcomes.
- **Consequences:** framework choice (see DEC-015); training-job resource needs.
- **Review trigger:** MLP vs. baseline comparison.

## DEC-013 — Deployment target

- **Status:** OPEN
- **Context:** MP §22: deployment follows local validation and licensing review; first release favours reliable historical workflow.
- **Options:** local-only (research workstation); single VM/container host; managed PaaS; private-network internal deployment; public web.
- **Criteria:** licence permissions for display (DEC-002); security/auth effort (SEC-003); cost (no paid infrastructure without need); job scheduling needs (NFR-004).
- **Evidence required:** licence decision on public display; resource profile of training/backtest jobs; user audience (single researcher vs. team).
- **Recommendation:** none now. *Constraint:* no deployment work before Phase 6 entry.
- **Consequences:** drives [DEPLOYMENT](docs/operations/DEPLOYMENT.md), auth, and monitoring scope.
- **Review trigger:** Phase 5 exit.

## DEC-014 — Project software licence (added)

- **Status:** OPEN
- **Context:** The brief says to create `LICENSE` only if the intended licence is decided. It is not. Software licence is independent of *data* licence (DEC-002): open-sourcing code does not allow redistributing provider data.
- **Options:** permissive (MIT/Apache-2.0); copyleft (GPL/AGPL); proprietary/all-rights-reserved; undecided until first release.
- **Criteria:** owner intent; dependency licence compatibility (checked at DEC-015); patent concerns; whether the repository will be public.
- **Evidence required:** owner decision; dependency licence audit.
- **Recommendation:** none. No `LICENSE` file exists; README states the code is unlicensed until decided.
- **Consequences:** until decided, no one has a granted right to reuse the code beyond what law gives by default.
- **Review trigger:** before making the repository public or accepting external contributions.

## DEC-015 — Python version, environment and dependency management (added)

- **Status:** OPEN
- **Context:** MP says a Python backend "may" be used and PyTorch is a likely framework (MP §13). The brief forbids fabricating a manifest or lockfile. A decision is needed before the first dependency exists.
- **Options:** `pyproject.toml` with a lock-capable tool (e.g., uv, Poetry, pip-tools); conda/mamba environment files; plain `requirements` files with hashes.
- **Criteria:** reproducible environments including numeric/ML wheels; CI simplicity; Windows/Linux support; ability to pin hardware-specific builds; lockfile with hashes.
- **Evidence required:** a clean-machine install test on the target OSes with a pinned numeric stack.
- **Recommendation:** none yet.
- **Consequences:** unlocks creation of the first manifest and lockfile; sets CI setup ([workflows](.github/workflows/)).
- **Review trigger:** Phase 1 kickoff (first code).
