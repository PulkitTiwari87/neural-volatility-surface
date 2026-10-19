# Implementation Matrix — chain → surface → baseline-evaluation engineering

**Status:** `IMPLEMENTED` for the synthetic spike path below (tests run, results in §4); **no real-data path exists**. Everything here is **spike-scope** (`scripts/phase0_synthetic/`, standard library only, [ADR-0003](../architecture/ADR/ADR-0003-phase0-spike-toolchain.md)); it is **not** product code and does not decide any open item in [decision.md](../../decision.md). **Phase 0 remains `BLOCKED`** (real-data feasibility, provider terms, PA-1/PA-4). Statistical-method research (PA-1 interval search, A2b-v2, A2c, Stage 2, seed extension) is **paused**; see [NEXT_STEPS](../research/NEXT_STEPS.md).

**Labels used:** `IMPLEMENTED` = code exists *and* tests were run (§4). `PARTIAL` = a working slice with named gaps. `PLANNED` = nothing built. Synthetic evidence never upgrades anything to `VALIDATED`.

## 1. Matrix

| # | Item | Status | Where (reused → new) | Depends on | Missing work | Acceptance tests |
|---|---|---|---|---|---|---|
| 1 | Provider interface | `PARTIAL` | New `chainpipe/schema.py`: `ChainProvider` protocol, `CsvChainProvider`, `ListChainProvider` (one parse path for both) | DEC-002 (provider) | No real-provider adapter, deliberately: field mappings are in [DATA_SOURCE_ASSESSMENT](../data/DATA_SOURCE_ASSESSMENT.md) §14 and nothing is built until a provider and a permitted sample exist | `Schema.test_in_memory_provider_uses_the_same_contract`, `test_file_level_problems_fail_fast` |
| 2 | Canonical schema | `IMPLEMENTED` (spike) | `chainpipe/schema.py`: `CANONICAL_COLUMNS`, `parse_row` with fixed check precedence, UTC conversion, option-type normalisation | — | Not yet reflected in [DATA_DICTIONARY](../data/DATA_DICTIONARY.md); no per-contract quote timestamp (Cboe EOD has none) or open interest column | `test_schema_precedence_normalisation_and_timezones`, `test_extra_columns_are_ignored_and_recorded` |
| 3 | Validation / cleaning | `IMPLEMENTED` (spike) | **Reused** `phase0.quotes.validate_day` (`Reason`, `QualityPolicy`); new per-row terminal disposition ledger in `chainpipe/pipeline.py` | 2 | Thresholds are defaults, not calibrated on real chains; no staleness test without per-quote timestamps | `test_every_malformed_fixture_row_gets_its_tagged_terminal_disposition` (every row has exactly one disposition; ledger conserved) |
| 4 | Implied vol | `IMPLEMENTED` (spike) | **Reused** `phase0.iv.implied_vol` (Brent, explicit `IVStatus`); `phase0.bsm.black76_price` | 3, 5 | European/forward-based only; American (SPY) needs DEC-004; solver bounds untested on real deep-OTM quotes | `test_iv_recovery_against_the_known_generating_vol` (max error < 1e-7), `test_solver_failures_are_explicit_and_no_iv_is_fabricated` |
| 5 | Strike / expiry normalisation | `PARTIAL` | `chainpipe/pipeline.py`: T = calendar days / 365, forward from **reused** `phase0.quotes.infer_forward` (put–call parity), k = ln(K/F̂), forward-vs-spot plausibility (±25 %) | DEC-005 | **AM vs PM settlement (SPX vs SPXW) is not modelled**; day-count is one stated assumption; no dividend/rate source (rate is a config constant) | `test_unalignable_and_implausible_expiries_are_reported_and_left_missing`, `test_config_is_recorded_with_the_day_count_and_is_stable` |
| 6 | Surface construction | `PARTIAL` | **Reused** `phase0.surface.build_surface` / `CellStatus`; per-expiry rows on a fixed k-node grid, linear in k, **no extrapolation** | 4, 5 | No constant-maturity interpolation in T; grid and interpolation are `PROPOSED`/`NEEDS RESEARCH`, not decided (DEC-006). See Q-25: when strikes lie on a K grid and nodes on forward log-moneyness, `observed` cells almost never occur | `test_surface_statuses_are_honest_and_never_extrapolated`, `test_strikes_on_the_node_grid_give_observed_cells_with_exact_values` |
| 7 | Serialisation / versioning | `IMPLEMENTED` (spike) | New `chainpipe/artifact.py`: schema `chainpipe-surface-1`, canonical JSON, content-hashed `version_id`, input/config/code hashes, tamper check on load, refuses overwrite and `experiments/` | 2–6 | JSON only (storage format undecided, DEC-009); no raw-store/immutability layer; code hashes are file-level | `test_deterministic_content_hash_and_provenance`, `test_round_trip_tamper_detection_and_refusals`, `test_nan_cannot_be_serialised`, `test_non_synthetic_origin_changes_the_label` |
| 8 | Synthetic fixtures + deterministic tests | `IMPLEMENTED` | New `chainpipe/fixtures.py` generates three labelled `*.synthetic.csv` files (normal snapshot, tagged-malformed rows, 12-day series); `tests/test_chainpipe.py` | — | Fixtures are clean generator output; they say nothing about real chain structure | `test_committed_fixtures_equal_the_generator_output_and_are_labelled_synthetic`, `test_fixture_writer_refuses_to_overwrite` |
| 9 | Persistence / statistical baselines | `PARTIAL` | **Reused** `phase0.forecast` baselines (synthetic-generator tasks, unchanged); new `chainpipe/evaluation.py`: *persistence* and *historical mean* on built artifacts | 7, 10 | Baselines only; no regression/factor baseline on artifacts; **no neural model, by design (GPU-only policy)** | `test_baseline_metrics_equal_a_hand_computation` |
| 10 | Chronological evaluation + leakage checks | `IMPLEMENTED` (spike) | `chainpipe/evaluation.py`: contiguous train/valid/test, `assert_chronology`, `AuditedHistory` (subclass of **reused** `HistoryView`) recording the largest index read; two tasks (contract-level; surface-cell-level stratified by target status) | 7 | Single split, no walk-forward refit loop (nothing is fitted yet); metrics by maturity/moneyness/regime not yet broken out | `test_chronological_split_…`, `test_chronology_violations_are_rejected`, `test_a_later_snapshot_cannot_change_an_earlier_prediction`, `test_history_guard_raises_on_lookahead_…`, `test_skipped_cells_are_counted_by_reason` |
| 11 | Surface-quality / no-arbitrage diagnostics | `PARTIAL` | New `chainpipe/diagnostics.py`: calendar total-variance, butterfly convexity, price-slope bounds; **flags only** (nothing is repaired or dropped); interpolated-cell involvement reported | 6 | Necessary conditions only, not a proof of arbitrage-freedom; tolerances are defaults; no repair/arb-free fitting | `Diagnostics.*` (5 tests: flat pass, calendar, butterfly, slope, missing cells skipped) |

## 2. What was reused and what is new

Reused unchanged (`phase0/` is untouched; its file hashes are embedded in frozen A2b records): validation (`quotes`), parity forward, OTM selection, Brent IV, Black-76, surface builder, history guard. New, under `chainpipe/`: the typed boundary (schema/providers), the orchestration with a conserved row ledger, the content-hashed artifact, the chain-level evaluation, the diagnostics and the fixtures. No second pricing or surface implementation exists.

## 3. Runnable synthetic end-to-end path

From `scripts/phase0_synthetic/` (outputs must be new files outside `experiments/`; existing files are refused):

```bash
python -m chainpipe.run build --input chainpipe/fixtures/chain_series12.synthetic.csv --out ../../scratch/chainpipe/series.json
python -m chainpipe.run evaluate --artifact ../../scratch/chainpipe/series.json --out ../../scratch/chainpipe/series_eval.json
```

Every output carries the label `SYNTHETIC - not market data` and the artifact `version_id` it came from. Regenerate fixtures only into a new directory: `python -m chainpipe.fixtures --out-dir <new dir>`.

## 4. Verification actually run (2026-10-13)

`python -m unittest discover -s tests -t .` from `scripts/phase0_synthetic` (with `-W error::ResourceWarning`): **145 tests, OK** (112 pre-existing + 33 in `tests/test_chainpipe.py`). Two initial failures in the new tests were wrong test assumptions (a 3-target split is legitimately 1/1/1; the deliberate `BAD_ORIGIN` fixture row is not `synthetic`), fixed in the tests; no production code was changed to pass them.

Observed on the 12-snapshot synthetic series (illustrative plumbing output, **not** evidence of model quality): contract-level persistence MAE 0.34 / 0.42 / 0.53 vol points (train / valid / test, n = 87 / 27 / 45), historical mean 0.38 / 0.50 / 0.62; leakage audit passed; historical-mean surface-cell task has n = 0 because the series yields no `observed` cells (Q-25).

## 5. Not done / not claimed

- No real data, provider adapter, network call or credential was used.
- No neural training, validation or inference was run (GPU-only policy).
- No claim about forecast skill, calibration or arbitrage-freedom is made.
- PA-1/PA-4 remain `OPEN`; A2b `NO_METHOD_ADMISSIBLE` and A2d raw evidence (with its disclosed post-run correction) are preserved.

## 6. Experiment E-1 hosted-data lab (2026-10-13)

`backend/src/volatility_lab/` (standard scientific stack: NumPy, pandas, SciPy, PyArrow; PyTorch for neural work on a CUDA GPU only). Unit tests: `backend/tests/unit` (CPU). The spike's `phase0/` code is the scalar reference the vectorised pricer is cross-checked against; `chainpipe/` stays as the stdlib synthetic path.

| # | Item | Status | Where | Notes |
|---|---|---|---|---|
| E1 | Hosted option-chain adapter (OptionsDX wide format, parquet/CSV, streaming) | `IMPLEMENTED` | `ingestion/optionsdx.py` | Conserved reject ledger; fingerprints; verified on 9.47 M real rows |
| E2 | Quote validation, parity forward and discount factor, OTM selection | `IMPLEMENTED` | `validation/quotes.py` | European model on American options: L-23 |
| E3 | Vectorised Black-76 and IV inversion | `IMPLEMENTED` | `pricing/bs.py` | Cross-checked against `phase0.iv` and `phase0.bsm` |
| E4 | Constant-maturity grid with observed / interpolated / missing status, no extrapolation | `IMPLEMENTED` | `surfaces/grid.py` | **Q-25 resolved for E-1** by redefining *observed* as anchored on a real expiry and tightly bracketed by real quotes |
| E5 | Static-arbitrage flags | `PARTIAL` | `surfaces/diagnostics.py` | Necessary conditions on a coarse grid only |
| E6 | Leakage-safe features, purged walk-forward folds, executable leakage audit | `IMPLEMENTED` | `features/panel.py`, `evaluation/walkforward.py`, `evaluation/leakage.py` | Audit also run on real data |
| E7 | Baselines (persistence, rolling mean, ridge, PCA-ridge) | `IMPLEMENTED` | `models/baselines.py` | |
| E8 | GPU-only neural models (MLP, GRU) with refusal and no CPU path | `IMPLEMENTED` | `models/neural.py` | GPU test skipped locally; executed on Colab and Kaggle T4 |
| E9 | Runner, descriptive evaluation, hashed artifacts, resume | `IMPLEMENTED` | `experiments/runner.py`, `evaluation/metrics.py` | No p-values or intervals by design (L-22) |
| E10 | Notebook generator | `IMPLEMENTED` | `scripts/build_colab_notebook.py` | Embeds the tested source; Colab and Kaggle modes |

Verification and results: [E1_RESULTS](../research/E1_RESULTS.md).

## 7. Experiment E-2 label comparison (2026-10-13)

| # | Item | Status | Where | Notes |
|---|---|---|---|---|
| E11 | Anchor expiry and per-expiry slices recorded per date | `IMPLEMENTED` | `surfaces/grid.py` | Computed from that date's quotes only |
| E12 | Same-expiry (fixed-expiry) label with explicit censoring | `IMPLEMENTED` | `features/panel.py` | Not a single-contract fixed-strike label; no maturity adjustment |
| E13 | Common-sample comparison, coverage and anchor-switch diagnostics | `IMPLEMENTED` | `evaluation/compare.py` | Descriptive only |
| E14 | E-2 notebook | `IMPLEMENTED` | `notebooks/Neural_Volatility_Surface_E2_FixedExpiry.ipynb` | Plain-text tables so they appear in the run log |

Tests: `backend/tests/unit/test_fixed_expiry.py` (15). Results: [E2_FIXED_EXPIRY_RESULTS](../research/E2_FIXED_EXPIRY_RESULTS.md).
## 8. Engineering pass (2026-10-14; no model trained)

| # | Item | Status | Where | Notes |
|---|---|---|---|---|
| P1 | Write-once raw store, versioned dataset, conserved ledgers | `IMPLEMENTED` (local, minimal) | `storage/raw_store.py`, `tests/unit/test_storage.py` (7) | Content-addressed; same inputs + config -> same version id; overwrite refused. No timezone/holiday fixtures, no CI; storage format is not a decision (DEC-009) |
| P3 | Small-sample flag in per-region metrics | `IMPLEMENTED` | `evaluation/metrics.py` `breakdowns(min_cells)`, 1 test | `MIN_CELLS = 100` is a research setting. Minimum-sample thresholds from Phase 0 and the go/no-go note do not exist |
| P5a | Read-only research API (stdlib) | `IMPLEMENTED` (local only) | `api/service.py`, `api/server.py`, `tests/unit/test_api.py` (9) | GET-only, loopback-only, name validation, strict JSON; no authentication (Phase 6) |
| P5b | Static 2D viewer | `IMPLEMENTED` (synthetic demo only) | `frontend/index.html`, `scripts/make_synthetic_run.py` | Status shown by symbol and colour, origin banner, lineage; no 3D, no actual-vs-forecast; opened once in the in-app browser |

Not done: Phase 0 gate items, Phase 4 (no training by instruction), Phase 6 (auth, CI, deployment, licence sign-off), 3D explorer, real-provider adapter.
| P5c | Forecast-vs-actual endpoint and viewer panel | `IMPLEMENTED` (synthetic demo only) | `api/service.py` `forecast`, route `/api/runs/<id>/forecasts/<model>/<index>`, `frontend/index.html`, 3 tests in `test_api.py` | Reads stored `forecasts/<model>.npz` (`target_index`, `origin_index`, `pred`); rejects files whose origin is not strictly before the target; difference = forecast - actual only where the actual cell is not missing; MAE on OBSERVED cells with n. Demo forecast is persistence (no model trained). No 3D, no model-forecast run produced by the runner yet |
| P6a | Known-volatility IV recovery grid, bounds and invalid-input tests (GR-QNT-01/02/06) | `IMPLEMENTED` (synthetic) | `backend/tests/scientific/test_iv_recovery.py` (9) | 2026-10-16. Tolerances written after E-1 ran on real data (L-28); per-quote solver diagnostics not stored |
| P6b | Interpolation / quote-filter comparison harness | `IMPLEMENTED` (research code, not adopted) | `surfaces/compare_methods.py`, `scripts/phase2_surface_comparison.py`, `tests/scientific/test_interpolation_comparison.py` (13) | 2026-10-16. Synthetic only, generator-dependent (L-27); DEC-006 open |
| P6c | Fitted-baseline leakage sentinels | `IMPLEMENTED` | `tests/scientific/test_leakage_sentinels.py` (3) | 2026-10-16. Baselines only; neural path not run |
| P6d | Import-direction test (GR-ENG-03) | `IMPLEMENTED` with 2 listed violations | `tests/unit/test_architecture_imports.py` (4) | models→evaluation, validation→pricing |
| P6f | H1 notebook and pre-registered decision rule | `IMPLEMENTED` (rule function, tested) / notebook **executed once on Kaggle 2026-10-19 (successful, see PHASE4 review §3.2)** | `evaluation/decision_rule.py`, `tests/unit/test_decision_rule.py` (7); `scripts/_notebook_cells/cells_h1.py`, `notebooks/Neural_Volatility_Surface_H1_RidgeGrid.ipynb` | 2026-10-16. Owner asked for no synthetic verification: static checks only; first execution = the Kaggle run. Baselines only, no neural training |
| P6e | Mechanical foundation audit | `IMPLEMENTED` | `scripts/foundation_audit.py`; [FOUNDATION_AUDIT](FOUNDATION_AUDIT.md) | Presence/consistency only; owner acceptance pending |
| P5d | Runner export of baseline forecasts for the viewer | `IMPLEMENTED` (function + test; wired into the generated notebooks 2026-10-15, notebooks not executed) | `experiments/runner.py` `export_forecasts`, 1 test in `test_metrics_and_end_to_end.py` | Writes the out-of-sample test-fold predictions exactly as evaluated (persistence, rolling_mean, ridge, PCA-ridge; neural `*_s*`/`*_ens` too if passed) to `<run>/forecasts/<model>.npz`; round trip through `RunStore.forecast` tested incl. origin < target and cell-for-cell equality. Under the E-2 label the viewer's actual is the surface at the target date, not the scored same-expiry label. No training added. Generated notebooks call it in the SAVE cell before the manifest (E-1: `<run>/forecasts/`; E-2: `<run>/e1_nearest/forecasts/` and `<run>/e2_fixed/forecasts/`); to view a run, put `surfaces/surface_panel.npz` as `panel.npz` next to a `forecasts/` folder in a runs root. Not executed since the change |
