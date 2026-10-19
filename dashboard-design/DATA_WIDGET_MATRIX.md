# Data widget matrix

**Status:** `PROPOSED` mapping. Every widget in the landing page and workbench, with its authoritative source and honest availability. No endpoint is invented: an endpoint that does not exist is marked, and "pending integration decision" means the delivery route is undecided, not that it exists.

## Classification

| Class | Meaning here |
|---|---|
| `VERIFIED` | The information is confirmed in an existing project artifact (a document, test or code) today. Says nothing about runtime delivery. |
| `AVAILABLE` | The source exists and the information can be fetched at runtime from an implemented route. |
| `PLANNED` | Part of documented future scope; not implemented. |
| `UNKNOWN` | The repository gives insufficient evidence. |
| `UNAVAILABLE` | The source or capability is absent. |

**Implemented API routes (verified in `backend/src/volatility_lab/api/server.py` and `service.py`; GET only, loopback only, no auth):** `GET /` (the one HTML file), `GET /api/runs` (list: `id`, `origin`, `description`), `GET /api/runs/{id}` (dates, tenor_days, k_nodes, status_labels, status_counts, tables, forecasts, lineage), `GET /api/runs/{id}/surface/{index}`, `GET /api/runs/{id}/forecasts/{model}/{index}`, `GET /api/runs/{id}/tables/{name}` (first 5000 rows). **There is no route** for documents, experiments, pipeline status, project status, health, images or plots, notebooks, or per-cell quote detail.

**Delivery codes:** `API` = an implemented route above; `Client` = derived in the browser from API data without modelling (slicing a row or column, formatting); `Docs` = static content authored from the named document, delivery route pending decision ([IMPLEMENTATION_PLAN §7](IMPLEMENTATION_PLAN.md)); `None`.

All "empty" behaviours use the design-system states (loading skeleton, empty, partial, error, unavailable). "Failure" is what the widget shows when its source errors; it never shows a stale or placeholder number.

## Shell

| ID | Widget | Information | Authoritative source | Delivery | Class | Empty / failure |
|---|---|---|---|---|---|---|
| S1 | Run selector | Run ids with origin label | `GET /api/runs`; `service.list_runs` (tested in `test_api.py`) | API | AVAILABLE | Empty: "No runs found." Failure: inline error with Retry; connection indicator flips to Not connected |
| S2 | Data-origin badge | `synthetic`, `real` or `unlabelled` | `meta.json` via `/api/runs` and run info | API | AVAILABLE | Unlabelled renders as a warning, never as real or synthetic |
| S3 | Research API indicator | Connected or not | Success of `GET /api/runs` (client inference). A health route is only proposed in [../docs/architecture/API_CONTRACTS.md](../docs/architecture/API_CONTRACTS.md) | Client | AVAILABLE (inferred) | Failure: "Research API: not connected" |
| S4 | Units label | Stored as decimal (0.20 = 20%); displayed in vol points | `iv_units` in the surface payload; [../CLAUDE.md](../CLAUDE.md) §6 | API | VERIFIED | Always shown with any IV |

## Landing page

| ID | Widget | Information | Authoritative source | Delivery | Class | Empty / failure |
|---|---|---|---|---|---|---|
| L1 | Hero status grid | Conceptual 6 by 9 grid of cell statuses (no values) | Documented E-1 grid ([../docs/research/E1_RESULTS.md](../docs/research/E1_RESULTS.md) §2); status vocabulary `surfaces/grid.py` | Static illustration | VERIFIED (vocabulary, dimensions); the pattern itself is conceptual and labelled | Always labelled "Conceptual illustration. Not a model output." |
| L2 | Hero metadata line | SPY EOD, 2010 to 2023, backtest only, licence unverified | E1_RESULTS §1; [../docs/data/HOSTED_DATASET_ASSESSMENT.md](../docs/data/HOSTED_DATASET_ASSESSMENT.md) | Docs | VERIFIED | n/a (static) |
| L3 | Documented-finding statement | Neural architectures did not beat persistence on pooled error | E1_RESULTS §4 (reproduced §7) | Docs | VERIFIED (snapshot; revisit on any new run) | Remove if the recorded result changes |
| L4 | Capability list | Eight capabilities with state | [../docs/engineering/IMPLEMENTATION_MATRIX.md](../docs/engineering/IMPLEMENTATION_MATRIX.md) E1 to E10, P1 to P5 | Docs | VERIFIED; 3D explorer and experiment history `PLANNED` | n/a |
| L5 | Preview plate | Conceptual surface mesh, tenor control, "Cells by status" with em dashes | None (illustration) | Static | PLANNED (the real explorer) | Labelled "Conceptual preview, no run loaded" |
| L6 | Workflow timeline | Stage names and states | IMPLEMENTATION_MATRIX §6; E1_RESULTS §2 | Docs | VERIFIED | n/a |
| L7 | Integrity and limitations list | Licence, provider access, real-data evaluation, inference, validation | HOSTED_DATASET_ASSESSMENT; [../docs/research/PHASE0_CLOSURE_RECORD.md](../docs/research/PHASE0_CLOSURE_RECORD.md); KNOWN_LIMITATIONS L-22 to L-25 | Docs | VERIFIED | n/a |
| L8 | Documentation links | Links to six documents and notebooks | Files exist in the repo; **no route serves them** | Docs (decision pending) | VERIFIED (files) / PLANNED (serving) | Until served, links must not be rendered as live |

## Overview

| ID | Widget | Information | Authoritative source | Delivery | Class | Empty / failure |
|---|---|---|---|---|---|---|
| O1 | Status at a glance (6 rows) | Project state, capabilities, data, result, validation, next step | CLAUDE.md status line; IMPLEMENTATION_MATRIX; E1_RESULTS; PHASE0_CLOSURE_RECORD | Docs | VERIFIED | Source chip *Documented*; if docs unavailable: Unavailable "Project documents not available" |
| O2 | Latest recorded experiment E-1 | Data, coverage, surface dates, test years, run dates | E1_RESULTS §1, §2, §7; manifest `version_id`, `config_sha256` when a run is loaded | Docs + API | VERIFIED (docs) / AVAILABLE (manifest) | No run: documented values only, labelled *Documented* |
| O3 | Available artifacts | Tables and forecasts of the selected run; manifest presence | `GET /api/runs/{id}` (`tables`, `forecasts`, `lineage`) | API | AVAILABLE | "No run is loaded." chip *Not connected* |
| O4 | Pipeline strip | Stage states | IMPLEMENTATION_MATRIX §6 | Docs | VERIFIED | n/a |

## Surface Explorer

| ID | Widget | Information | Authoritative source | Delivery | Class | Empty / failure |
|---|---|---|---|---|---|---|
| X1 | Date control | `dates` list | `GET /api/runs/{id}` | API | AVAILABLE | "Date 0 of 0" with disabled stepper when no run |
| X2 | Heatmap | `iv` (decimal), `status`, `tenor_days`, `k_nodes` for one date | `GET /api/runs/{id}/surface/{i}` (NaN becomes null) | API; display conversion x100 in Client | AVAILABLE | Empty: "No run is loaded." Missing cells: dashed outline and em dash. Failure: inline error with Retry |
| X3 | Table view | Same payload | same | API | AVAILABLE | same; the keyboard and screen-reader equivalent |
| X4 | 3D surface | Same payload rendered in 3D | same data; renderer undecided (DEC-008 `NEEDS RESEARCH`) | API | PLANNED | "The 3D view is planned. The heatmap and table are available whenever a run is loaded." |
| X5 | Selected cell | Tenor, k, IV, status | surface payload | Client | AVAILABLE | em dashes with no selection |
| X6 | Quotes behind the cell | Count and quotes feeding one cell (UI-010 lineage) | **Not in any payload** (only `n_quotes` per date exists) | None | UNAVAILABLE | "—" with "Not available. Source: per-cell quote lineage is not stored." |
| X7 | Smile slice | IV versus k at selected tenor | row of surface payload | Client | AVAILABLE | "No data. Load a run to see this slice." |
| X8 | Term-structure slice | IV versus tenor at selected k | column of surface payload | Client | AVAILABLE | same |
| X9 | Actual, Forecast, Difference | Actual, forecast and difference grids; origin and target dates; horizon in panel steps | `GET .../forecasts/{model}/{i}`; a file with origin not before target is rejected | API | AVAILABLE (route); whether a run has any forecast file is `UNKNOWN` until exported (see MODEL_HANDOFF) | "Not available" per panel; the message names the cause (no forecast file, no forecast for this date) |
| X10 | Comparable-cell count and MAE | `n_difference_cells`, `n_observed_cells`, `mae_observed_vol_points` | forecast payload | API | AVAILABLE | em dash and "n = —" |
| X11 | Status legend and counts | Four statuses, whole-run counts | run info `status_labels`, `status_counts` | API | AVAILABLE | counts "—" |
| X12 | Forecast model selector | Names of stored forecasts | run info `forecasts` | API | AVAILABLE | "None loaded" |
| X13 | Lineage strip | Dataset version, config hash, panel hash match | run info `lineage` (present only when `manifest.json` exists) | API | AVAILABLE when a manifest is present; else UNAVAILABLE ("No manifest stored for this run.") | A hash mismatch shows the validation warning and marks the run Unverified |
| X14 | Two-date comparison, evolution animation | Overlay or difference of two surfaces; chronological playback | VISUALIZATION_SPEC V4 and V5; UI-004 | Client over the surface route | PLANNED | n/a |
| X15 | Arbitrage-flag overlay | Calendar and butterfly flags per cell | `surfaces/diagnostics.py` computes flags; **not stored in the panel or exposed** | None | UNKNOWN | Hidden |

## Evaluation

| ID | Widget | Information | Authoritative source | Delivery | Class | Empty / failure |
|---|---|---|---|---|---|---|
| E1 | Pooled error table | Model, RMSE, MAE, MSE skill vs persistence, `n` | A run table (the notebook writes `tables/pooled.csv`) via `GET .../tables/{name}`; documented values E1_RESULTS §3 | API for a run; Docs otherwise | AVAILABLE (route; column names UNKNOWN until a run is read) / VERIFIED (documented values) | Documented-mode banner; no run and no docs: Unavailable |
| E2 | Error by year | Per fold or year results | `tables/per_fold.csv`; E1_RESULTS §3 | API / Docs | same as E1 | same |
| E3 | Error by tenor | RMSE by tenor and cells | E1_RESULTS §3 (by region); region breakdown table names are set by the runner (UNKNOWN until listed) | Docs / API | VERIFIED (docs) | same |
| E4 | Error by moneyness and regime | By k node; by realised-volatility tercile | E1_RESULTS §3 | Docs / API | VERIFIED (docs) | same |
| E5 | Metric status list | Measured, Unavailable, Not pursued per metric | E1_RESULTS §3 and §4; KNOWN_LIMITATIONS L-22; [../docs/research/UNCERTAINTY_AND_CALIBRATION.md](../docs/research/UNCERTAINTY_AND_CALIBRATION.md) | Docs | VERIFIED | n/a |
| E6 | Not concluded | Three statements | E1_RESULTS §4 | Docs | VERIFIED | n/a |
| E7 | Reproducibility | Run id, config hash, compute, run dates | Manifest (`version_id`, `config_sha256`) via run info; run id and compute in E1_RESULTS §1 and §7; `metadata/run_metadata.json` is not exposed | API (partial) / Docs | AVAILABLE (hashes) / VERIFIED (docs) / UNAVAILABLE (device metadata) | Missing fields show "—" with the cause |
| E8 | Calibration diagnostics | Coverage, reliability | None (no intervals by design, L-22) | None | UNAVAILABLE | Row shown as Unavailable "(no intervals by design)" |
| E9 | Training curves, error heatmaps, skill plots | Figures | `plots/*.png` and `tables/plot_data.npz` in the Kaggle output (E1_RESULTS §7); `tables/training_summary.csv` | None for images; CSV via tables if copied | UNAVAILABLE (images) / AVAILABLE (CSV, if present) | Unavailable "Plots are produced by the run but not served" |

## Data & Provenance

| ID | Widget | Information | Authoritative source | Delivery | Class | Empty / failure |
|---|---|---|---|---|---|---|
| D1 | Source identity | Dataset, upstream provider, host, dataset identifier, coverage, 14 parquet files, last access | E1_RESULTS §1; HOSTED_DATASET_ASSESSMENT | Docs | VERIFIED | n/a |
| D2 | Licence status | Uploader label MIT; upstream terms unverified | HOSTED_DATASET_ASSESSMENT; E1_RESULTS header | Docs | VERIFIED (that it is unverified) | Never shown as verified |
| D3 | Licensed provider access | Not obtained: provider terms, pricing, permitted sample | CLAUDE.md status line; [../docs/data/DATA_SOURCE_ASSESSMENT.md](../docs/data/DATA_SOURCE_ASSESSMENT.md); DEC-002 `PROPOSED` | Docs | VERIFIED (absence) | State Unavailable |
| D4 | Transformation history | Six steps with row counts | E1_RESULTS §2; IMPLEMENTATION_MATRIX §6 | Docs | VERIFIED | n/a |
| D5 | Rows removed and why | Per-reason counts, conserved ledger | Manifest `ledger_prefilter`, `ledger_quotes`, `ledgers_conserved` (run info); documented values E1_RESULTS §2 | API when a manifest is present / Docs | AVAILABLE / VERIFIED | No manifest: documented values, labelled |
| D6 | Surface cell mix | Whole-run status counts and shares | run info `status_counts`; documented 26.2, 54.2, 1.6, 18.0 percent | API / Docs | AVAILABLE / VERIFIED | counts "—" |
| D7 | Arbitrage-flag counts | Calendar and butterfly counts | E1_RESULTS §2 (documented); not exposed at runtime | Docs | VERIFIED (docs) / UNKNOWN (runtime) | Labelled "necessary conditions only" |
| D8 | Input hashes | Input names and SHA-256 | run info `lineage.inputs` | API | AVAILABLE when a manifest is present | "No manifest stored for this run." |
| D9 | Vendor-IV comparison | Median ratio and absolute difference, "sanity check only" | E1_RESULTS §2 | Docs | VERIFIED | n/a |

## Experiments & Pipeline

| ID | Widget | Information | Authoritative source | Delivery | Class | Empty / failure |
|---|---|---|---|---|---|---|
| P1 | Pipeline nodes | Nine stages and states | IMPLEMENTATION_MATRIX §6 to §8; DATA_SOURCE_ASSESSMENT for the blocked stage | Docs | VERIFIED | n/a |
| P2 | Recorded experiments | E-1, E-2, Phase 0 spike, Phase 0 audit, neural on licensed data | E1_RESULTS, E2_FIXED_EXPIRY_RESULTS, PHASE0_CLOSURE_RECORD, PHASE0_SYNTHETIC_RESULTS | Docs | VERIFIED (history); no registry (DEC-010 `PROPOSED`), so a live history is UNAVAILABLE | "Recorded in project documents" |
| P3 | Configuration of E-1 | Test design, horizon, seeds, hyper-parameter policy, compute, durations, run id, config hash | E1_RESULTS §1, §3, §5, §7 | Docs | VERIFIED | n/a |
| P4 | Blockers | Real-data feasibility blocked; hosted licence unverified | CLAUDE.md status line; PHASE0_CLOSURE_RECORD; NEXT_STEPS | Docs | VERIFIED | n/a |
| P5 | Failures | "No failures are recorded in the project documents." | Absence of a failure log; no source records failures | None | UNKNOWN (absence of a record is not evidence that none occurred) | The wording must not claim none occurred |

## Artifacts and Methodology

| ID | Widget | Information | Authoritative source | Delivery | Class | Empty / failure |
|---|---|---|---|---|---|---|
| A1 | Run artifact list | `panel.npz`, `meta.json`, `manifest.json`, tables, forecasts | run info and the directory contract in the `api/service.py` docstring | API | AVAILABLE | "No run is loaded." |
| A2 | Notebooks | Two generated notebooks | Files in `notebooks/` | Docs | VERIFIED (files) / PLANNED (listing route) | n/a |
| A3 | Report and plots | `report.md`, `plots/*.png` | Kaggle output only (E1_RESULTS §1, §7) | None | UNAVAILABLE | "Not available. Source: produced by the run, not served." |
| A4 | Expected future outputs | e.g. forecasts from a later run | MODEL_HANDOFF | None | PLANNED | Labelled "Expected, not yet produced" |
| M1 | Methodology sections | Rendered documents | `docs/research/*.md`, `docs/data/*.md` | Docs | VERIFIED (files) / PLANNED (serving) | Link disabled until served |
