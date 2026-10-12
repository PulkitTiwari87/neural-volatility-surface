# guardrails.md — Enforceable Project Guardrails

**Status:** PROPOSED (rules are in force as policy now; automated enforcement of the product is `PLANNED` — no product tests or CI exist; only the disposable Phase 0 synthetic spike has unit tests, which exercise parts of GR-QNT-01/02/06, GR-LEAK-01 and GR-DATA-02/04/05 on synthetic data, see [PHASE0_AUDIT](docs/research/PHASE0_AUDIT.md))
**Canonical for:** non-negotiable scientific, data, product, security and engineering rules and how each is verified.
**Source:** foundation brief §3, §9; MP §5, §8–§11, §14, §20–§21, §25. **Related:** [PR.md](PR.md) · [CLAUDE.md](CLAUDE.md) · [docs/engineering/TESTING_STRATEGY.md](docs/engineering/TESTING_STRATEGY.md) · [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)

## How guardrails work

- Each guardrail has an ID (`GR-<AREA>-nn`), a testable rule, and an **enforcement** column naming the test/check that will verify it and the phase in which that check must exist. Test file names are *planned* names, not existing files.
- **Until a check exists, the rule is enforced by review** (the checklist in [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md)). A guardrail whose check is missing at its due phase blocks that phase's exit gate.
- Numeric tolerances/thresholds are **not invented here**. Where a number is needed it is marked `TBD(Phase n)` and must be set from the data/solver specification at that phase, then recorded in config and docs.
- Loosening or removing a guardrail requires an ADR ([ADR-0001 template](docs/architecture/ADR/ADR-0001-template.md)) and a note in [CHANGELOG.md](CHANGELOG.md). Convenience is not a justification.
- **On violation:** stop, record it (issue using the bug template), fix root cause, add a regression test. Do not publish results produced while a guardrail was violated.

---

## 1. Data integrity (`GR-DATA`)

| ID | Rule | Enforcement (validation / test) | Due |
|---|---|---|---|
| GR-DATA-01 | Preserve raw source records and provenance where licence permits; raw store is write-once. | Integration test: ingest a synthetic provider payload → raw store holds the unmodified payload + source metadata + ingestion timestamp; a second write to the same snapshot ID fails. `backend/tests/integration/test_raw_store_immutable` | Ph1 |
| GR-DATA-02 | Never silently discard observations. | Property test: for any input batch, `retained + excluded == input`, and every excluded record has a reason from the defined enum. `backend/tests/unit/test_validation_conservation` | Ph1 |
| GR-DATA-03 | Record exclusion reasons and quality counts per snapshot. | Fixture with injected, known defects (crossed, negative, stale, duplicate…) → quality report counts equal injected counts exactly. | Ph1 |
| GR-DATA-04 | Never fabricate market observations; synthetic data is always labelled. | Schema field `origin ∈ {provider, synthetic}` is mandatory; synthetic records are rejected by the provider raw-store writer; fixture files must match `*.synthetic.*` and carry a header stating so; check that nothing under `data/` except placeholders is tracked by Git. | Ph1 |
| GR-DATA-05 | Observed, interpolated, extrapolated and missing surface values are distinguishable at every layer. | Surface schema requires a non-null 4-valued status per cell; round-trip tests (build → store → API → UI model) preserve statuses; test that interpolation never sets `observed`. | Ph2 |
| GR-DATA-06 | Respect data licensing and redistribution limits. | Release checklist gate (manual, recorded in the ADR for DEC-002); CI check that no market data file is tracked; export function stamps source/licence metadata. | Ph0, Ph6 |
| GR-DATA-07 | Freshness is labelled exactly: `historical`, `delayed`, `latest_available`, or `real_time_licensed`. | Schema enum; UI test: the word "live" only renders when mode is `real_time_licensed` and latency is known. | Ph1, Ph5 |
| GR-DATA-08 | Corrections create a new data version; results pin versions. | Test: mutate-and-republish yields a new version ID while the old version's content hash is unchanged and still retrievable. | Ph1 |

## 2. Quantitative correctness (`GR-QNT`)

| ID | Rule | Enforcement | Due |
|---|---|---|---|
| GR-QNT-01 | Validate option prices against theoretical bounds before solving. | Unit tests: price below lower bound / above upper bound → explicit non-converged status, no IV. Cover calls & puts. | Ph2 |
| GR-QNT-02 | Do not fabricate IV when the solver fails. | Property test: `iv is not null ⇒ status == CONVERGED ∧ |model_price(iv) − market_price| ≤ tol`; failure ⇒ `iv is null ∧ reason != null`. | Ph2 |
| GR-QNT-03 | Record solver status, iterations, assumptions and failure reasons. | Schema test: required diagnostic fields are non-null for every IV observation. | Ph2 |
| GR-QNT-04 | Pricing-model limitations are documented and enforced. | [IV_METHODOLOGY](docs/research/IV_METHODOLOGY.md) lists limitations; pricing API declares supported exercise styles; test: unsupported instrument → `UNSUPPORTED_INSTRUMENT`, never a silent fallback. | Ph2 |
| GR-QNT-05 | One consistent timestamp/maturity convention. | Tests of year-fraction computation across weekends, holidays, early closes, timezone/DST boundaries using a fixed calendar fixture; all date arithmetic goes through one module (grep/architecture check). | Ph1–2 |
| GR-QNT-06 | IV calculations are verified on synthetic prices with known generating volatility. | Scientific test: price → solve → compare over a grid of volatility, maturity (incl. very short), moneyness (incl. deep ITM/OTM), call/put. Tolerances `TBD(Phase 2)` recorded in test config. `backend/tests/scientific/test_iv_recovery` | Ph2 |
| GR-QNT-07 | Surfaces/forecasts get sanity diagnostics (bounds, monotonic-in-variance checks, jumps) reported, not hidden. | Diagnostic functions with synthetic violating surfaces detected; diagnostics appear in snapshot metadata. (Constraints themselves are Phase 7.) | Ph2–3 |

## 3. Leakage prevention (`GR-LEAK`)

| ID | Rule | Enforcement | Due |
|---|---|---|---|
| GR-LEAK-01 | Time-series data is split chronologically; label horizon overlap is handled (gap/embargo as required). | Test: `max(train_ts) < min(val_ts) < … < min(test_ts)`; no shuffling API exists for primary evaluation; horizon-overlap case covered. `backend/tests/scientific/test_chronological_split` | Ph3 |
| GR-LEAK-02 | Scalers/transforms/imputers are fit only on eligible training data, re-fit per fold. | Sentinel test: extreme values injected into post-cutoff data do not change fitted parameters; fit functions receive only the training index. | Ph3 |
| GR-LEAK-03 | Features at origin *t* use only information available at *t*. | **Truncation invariance test:** features computed on data truncated at *t* equal features computed on the full dataset at *t* (for every feature in the catalog). | Ph3 |
| GR-LEAK-04 | No future information in labels, features, imputation, normalization or model selection. | Combination of GR-LEAK-02/03 tests; model-selection code reads only validation windows (test-window access raises unless explicitly authorized and logged). | Ph3–4 |
| GR-LEAK-05 | The final test period stays untouched until selection is frozen. | Test-window access log recorded in each run record (`test_accessed_count`); review rejects selection decisions made with test data. | Ph3 |
| GR-LEAK-06 | Primary historical performance claims use walk-forward (rolling-origin) validation. | Evaluation report schema requires `scheme = walk_forward` for any "primary result"; other schemes are labelled exploratory. | Ph3 |

## 4. Model integrity (`GR-MOD`)

| ID | Rule | Enforcement | Due |
|---|---|---|---|
| GR-MOD-01 | Persistence and statistical baselines exist before any neural model is trained. | Experiment runner refuses a neural run unless persistence and regression results exist for the same dataset version and split. | Ph3→4 |
| GR-MOD-02 | Report metrics by maturity, moneyness, period and regime where sample sizes permit. | Report-schema test; cells below the minimum sample size (`TBD(Phase 3)`) are shown as *insufficient*, never dropped silently. | Ph3 |
| GR-MOD-03 | Every metric reports sample count and missingness. | Metric table schema requires `n` and `n_missing`. | Ph3 |
| GR-MOD-04 | No improvement claim without out-of-sample evidence and variability. | Report generator derives comparative statements only from computed out-of-sample deltas, with spread across seeds/folds/periods; reviewers check experiment records. | Ph4 |
| GR-MOD-05 | Random seeds and full configuration are recorded; runs are reproducible where feasible. | Run-record validation; re-run test reproduces stored metrics within the documented tolerance (deterministic components exactly). | Ph3–4 |
| GR-MOD-06 | Uncertainty is labelled for what it is. | Field `uncertainty_kind ∈ {none, heuristic, empirical_interval}`; "calibrated" allowed only when a coverage/calibration report is attached; UI test for labels. | Ph4–5 |

## 5. Product integrity (`GR-PRD`)

| ID | Rule | Enforcement | Due |
|---|---|---|---|
| GR-PRD-01 | No automated trading. | No order-execution code or broker-trading dependency in the repo; dependency/PR review; grep check for order endpoints. | all |
| GR-PRD-02 | No personalized investment advice or profitability claims. | UI copy checklist; automated scan of user-visible strings against a maintained phrase list; disclaimer present on forecast views. | Ph5–6 |
| GR-PRD-03 | No misleading real-time labels. | See GR-DATA-07. | Ph5 |
| GR-PRD-04 | Forecast views show origin, target horizon, model version, assumptions, and limitation link. | Component tests + E2E: each forecast view renders those fields; missing metadata renders an error state, not blanks. | Ph5 |
| GR-PRD-05 | Historical backtests and prospective forecasts are labelled differently. | Schema enum `forecast_kind`; UI test for distinct labels. | Ph5 |

## 6. Security (`GR-SEC`)

| ID | Rule | Enforcement | Due |
|---|---|---|---|
| GR-SEC-01 | Never commit secrets or credentials. | `.gitignore` covers `.env*` (except `.env.example`), keys, tokens; secret-scanning check in CI/pre-commit (tool chosen with DEC-015); `.env.example` contains placeholders only. | now |
| GR-SEC-02 | Provider credentials never reach frontend code. | Frontend build check: no provider key variable names or values in the bundle/env; provider calls exist only in `backend/…/ingestion`. | Ph5–6 |
| GR-SEC-03 | Validate all external inputs. | API tests with malformed, oversized, out-of-range params; schema validation at every boundary; provider payload validation tests. | Ph1, Ph6 |
| GR-SEC-04 | Do not log secrets. | Test: logging a config containing a fake key never emits it (redaction filter). | Ph1 |
| GR-SEC-05 | Access control and limits before exposing expensive/privileged operations. | API tests: unauthenticated job start rejected; rate-limit and resource caps verified. | Ph6 |
| GR-SEC-06 | No destructive commands without explicit authorization. | [CLAUDE.md](CLAUDE.md) §11; scripts that delete or overwrite require an explicit confirm flag and dry-run default. | all |

## 7. Engineering (`GR-ENG`)

| ID | Rule | Enforcement | Due |
|---|---|---|---|
| GR-ENG-01 | No speculative abstractions. | PR review: each new abstraction cites a requirement ID and ≥2 concrete callers or a test need. | all |
| GR-ENG-02 | No unapproved dependencies. | PR template section "Dependencies"; manifest changes require justification and, if they settle a decision, a `DEC-` reference. | all |
| GR-ENG-03 | Modules stay independently testable; dependency direction is downstream-only. | Architecture test over imports (e.g., `pricing` must not import `surfaces`); `domain` has no I/O imports. | Ph1 |
| GR-ENG-04 | Scientific and architectural changes ship with tests. | PR checklist; CI requires `scientific/` suite to run on changes to pricing, surfaces, features, datasets, evaluation. | Ph1 |
| GR-ENG-05 | Affected documentation is updated in the same change. | PR checklist; docs link checker (once tooling exists). | all |
| GR-ENG-06 | Never claim tests passed without executing them. | CI logs / pasted command output in PR; CLAUDE.md §10. | all |
| GR-ENG-07 | Statuses are honest: nothing is `IMPLEMENTED`/`VALIDATED` without code+tests / recorded evidence. | Review of status tables ([README.md](README.md#project-status), [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)); exit gates require links to evidence. | all |

## 8. Coverage map to the master-plan test strategy (MP §21)

| MP §21 item | Guardrails |
|---|---|
| IV vs. synthetic known-vol prices | GR-QNT-01, 02, 06 |
| Chronological splits / leakage | GR-LEAK-01…06 |
| Persistence reproducible; metrics hand-checked | GR-MOD-01, 05; [EVALUATION_PROTOCOL](docs/research/EVALUATION_PROTOCOL.md) |
| Observed vs interpolated labelling | GR-DATA-05 |
| Implausible jumps / pricing inconsistencies | GR-QNT-07 |
| Visualization shows backend values & labels | GR-PRD-04, 05; [design.md](design.md) §17 |
| Missing data / failed forecast paths | GR-DATA-02/03, [design.md](design.md) §9 |
