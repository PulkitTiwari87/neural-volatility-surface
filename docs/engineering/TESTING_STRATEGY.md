# Testing Strategy

**Status:** PROPOSED (no tests exist; tooling not selected) · **Canonical for:** test categories, minimum scientific test set, fixture policy, CI expectations · **Source:** MP §21, foundation brief §9 · **Related:** [guardrails.md](../../guardrails.md) (what each test enforces), [CLAUDE.md](../../CLAUDE.md) §10

## 1. Categories and locations
| Category | Location | Purpose |
|---|---|---|
| Unit | `backend/tests/unit/` | Pure functions: normalization, validation, time/maturity, pricing, coordinates, features, metrics |
| Integration | `backend/tests/integration/` | Adapter → raw store; raw → IV → surface; dataset → features → inference; forecast → API |
| Scientific | `backend/tests/scientific/` | Known-answer and invariance tests: IV recovery, leakage, baselines, reproducibility |
| Fixtures | `backend/tests/fixtures/`, `tests/fixtures/` | Small **synthetic**, labelled (`*.synthetic.*`) |
| End-to-end | `tests/end_to_end/` | User journeys through API + UI |
| Regression | `tests/regression/` | Frozen synthetic scenarios for previously fixed defects; golden outputs for deterministic stages |

## 2. Principles
1. **Synthetic known-answer tests** are the backbone for science code: construct inputs whose correct outputs are known analytically (e.g., prices from a chosen σ).
2. **Test failure paths** as thoroughly as success paths.
3. **Property-based tests** where invariants exist (conservation of records, `iv ≠ null ⇒ converged`, idempotent re-run).
4. **Deterministic tests:** fixed seeds; tolerances explicit; no network access; no reliance on real market data or credentials.
5. **Tests are never weakened** to pass; fix the cause (CLAUDE.md §10).
6. **A test run counts only if executed**, with output captured (GR-ENG-06).
7. Tests must not embed licensed data; fixtures are synthetic or tiny hand-written.

## 3. Minimum scientific validation set (from the foundation brief §9 and MP §21)

### Implied volatility (`scientific/`, Phase 2)
- Recover known volatility from synthetic option prices across σ, *T* (incl. very short), moneyness (incl. deep ITM/OTM), call/put.
- Valid and invalid price bounds → correct statuses; no IV for out-of-bound prices.
- Solver convergence/failure states: no-bracket, max-iterations, NaN/inf inputs.
- Missing, crossed, stale, unreliable quotes → excluded with reason codes (integration with validation).
- Pricing assumptions fit the supported instrument; unsupported style rejected.
- Reference cases from independently documented values (source cited).

### Surface construction (Phase 2)
- Coordinate transformations round-trip (strike ↔ *k*, date ↔ *T*).
- Observed/interpolated/extrapolated/missing masks preserved through build → store → API.
- Sparse and irregular chains; hull boundaries; no silent extrapolation.
- Construction method + version tracked; rebuild yields identical hash.

### Features and forecasting (Phase 3–4)
- Chronological split tests incl. gaps; no overlap or reordering.
- Leakage: truncation invariance for every feature; scaler sentinel tests; no test-window access during selection.
- Persistence baseline calculations against hand-computed examples.
- Evaluation: forecasts vs chronological holdout; metrics by region with sample counts; hand-checked metric values.
- Synthetic worlds with known best model (random walk ⇒ persistence unbeatable; AR structure ⇒ AR beats persistence) to confirm the pipeline neither invents nor hides improvement.
- Deterministic reproducibility of baselines (exact) and stochastic models (within documented tolerance).

### Visualization (Phase 5)
- Displayed values equal backend outputs for fixture selections (UA-01).
- Units, timestamps, horizons, data status labelled (UA-02/03).
- Empty, partial, error, stale states (UA-05).
- Accessible 2D/table alternative for each 3D view (UA-06).

## 4. Integration and E2E journeys (MP §21)
Select underlying/date → open Surface Explorer → compare actual vs forecast → inspect a grid point's lineage → view backtest metrics and experiment metadata → handle missing data and failed-forecast scenarios.

## 5. Security and governance tests
Secret-scan check; log redaction test; API input validation and authorization tests; no market data tracked; export metadata/licence tagging (GR-SEC, GR-DATA-06).

## 6. CI expectations (Phase 1 onward; tool/host per DEC-015)
On every change: lint/type/format; unit + integration + scientific suites for affected modules; secret scan; architecture (import-direction) test; docs link check; for Phase 5+: E2E and accessibility checks. CI logs are evidence for gates.

## 7. Coverage philosophy
Prefer meaningful guardrail coverage over a percentage target. Each GR with an enforcement test is traceable (the table in guardrails.md). A numeric coverage threshold may be set later if useful; it never substitutes for known-answer tests.

## 8. Data-driven checks on real data (Phase 1+, outside CI)
Quality reports and diagnostics on real data are produced and reviewed by humans; they are not unit tests, and real data never enters the repository.
