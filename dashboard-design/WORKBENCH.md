# Research workbench

**Status:** `PROPOSED`. Mode: *Operate* (a researcher completes a task). Stitch screens are layout and style evidence only; copy and data mapping here and in [DATA_WIDGET_MATRIX.md](DATA_WIDGET_MATRIX.md) are canonical. Tokens: [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md).

## 1. Questions the first screen answers

The Overview answers, without scrolling: (1) What is the state of the research? (2) Which capabilities are implemented? (3) Is usable data available? (4) Is a model result available? (5) Has it been validated? (6) What should I inspect next? Each answer carries a state chip and a source chip. Where a source is a project document, the chip says *Documented*; where it would come from a run, *Live from run*; with no API, *Not connected*.

## 2. Shell and navigation

Left sidebar (232px), icon plus full text label, in this order: **Overview, Surface Explorer, Evaluation, Data & Provenance, Experiments & Pipeline, Artifacts, Methodology & Documentation**; "Back to home" at the bottom. No other items (the generator's invented items, such as Settings, Model Calibration, Risk Matrix, API Status, were rejected).

Top bar: page title; context (all plain Geist text): `Run: <id | none selected>`, `Data origin: <synthetic | real | unlabelled | not loaded | documentation>`, `Research API: <connected | not connected>`. The origin value comes from the run's `meta.json`; "unlabelled" must read as a warning, never as real or synthetic. "Connected" means a successful `GET /api/runs`; the project has no health endpoint (API_CONTRACTS proposes one; not implemented), so connection is inferred client-side.

Proposed URL state (hash routes keep the stdlib server unchanged): `#/overview`, `#/explorer?run=<id>&i=<index>&view=<heatmap|table|3d>&model=<name>`, `#/evaluation?run=<id>`, `#/data`, `#/experiments`, `#/artifacts?run=<id>`, `#/methodology`. State in the URL makes views shareable and reproducible (PR UI-001 and the docs/design IA rule).

## 3. Screens

### 3.1 Overview (Stitch `40cf2f6d0c444790b26bb856346823a7`)
Layout: wide "Status at a glance" panel (the six questions as rows: question in secondary text, answer in primary text, state chip, quiet source chip); right column "Latest recorded experiment: E-1" and "Available artifacts"; full-width "Research pipeline" timeline. Canonical copy for the six rows:

| Question | Answer | State |
|---|---|---|
| What is the state of the research? | Phase 0 is incomplete. Real-data feasibility with licensed sources is pending. | In progress |
| Which capabilities are implemented? | Surface construction, baselines, neural models, leakage audit, two-dimensional viewer. (Three-dimensional explorer and experiment history view: Planned.) | Completed |
| Is usable data available? | A hosted dataset of SPY end-of-day options, 2010 to 2023. The upstream licence is unverified. | Unverified |
| Is a model result available? | Experiment E-1 is recorded with descriptive results only. | Completed |
| Has the result been validated? | No. No significance, calibration or trading claim is made. | Unverified |
| What should I inspect next? | Open Surface Explorer; Review Evaluation. | n/a |

E-1 panel rows: Data; Coverage 2010-01-04 to 2023-12-29; Surface dates 3,500; Test years 2016 to 2023; Run date 2026-10-13, reproduced 2026-10-16. Artifacts panel when no run is loaded: "No run is loaded. Artifacts appear here when the research API lists a run." with the *Not connected* chip. Pipeline stage labels as on the landing page, plus Viewer "Partial: two-dimensional only".

### 3.2 Surface Explorer (Stitch `3cce6b6bc84a423eb9b5a6d3ebd17753`, mobile `c192bb55326a4450a3554f08b01d3b22`)
The central screen; requirements in §5. Context row: Run, Date ("Date n of N"), Forecast model, Units ("implied volatility in vol points"). Workspace tabs: 3D surface, Heatmap, Table (phones default to Heatmap). Right inspector: Selected cell; Smile at selected tenor; Term structure at selected moneyness. Lower row: Actual, Forecast, Difference (forecast minus actual). Lineage strip: Dataset version, Configuration hash, Panel hash matches manifest.

### 3.3 Evaluation (Stitch `eb6ec00c2f594488806a93c5209ea34d`)
Purpose: measured results, planned metrics and unavailable evaluation are visibly different. Panels: "Pooled error on observed cells, in vol points" (Model, RMSE, MAE, MSE skill versus persistence, with `n`); "Root-mean-square error by tenor, in vol points"; "Not concluded"; "Metric status"; "Reproducibility". Live data comes from result tables (names are listed per run by the API); the screen's *Documented* mode shows the figures in [../docs/research/E1_RESULTS.md](../docs/research/E1_RESULTS.md) §3 with a banner "Figures below are recorded in the E-1 results document. They are not read from a live run." Metric status (state): RMSE Measured; MAE Measured; Skill versus persistence Measured; Error by tenor Measured; Error by moneyness Measured; Error by volatility regime Measured; Calibration diagnostics (no intervals by design) Unavailable; Statistical significance Not pursued. "Measured" is a label for *a value exists in a recorded result*, not for "validated". Not concluded (E1_RESULTS §4): that neural networks cannot forecast implied-volatility surfaces; that PCA-ridge is better than persistence in any statistical sense; any trading, hedging or profit value.

Planned additions (UI-006, VISUALIZATION_SPEC V7), shown only when their data exist: training and validation curves per seed, error heatmaps, skill by year, residual distribution, cumulative difference.

### 3.4 Data & Provenance (Stitch `f215b07c70ca4be488c4a8914d341c3c`)
Panels: Source identity (dataset, upstream provider, host, dataset identifier in monospace, coverage, storage, last access); Licence status (Unverified: "The uploader labels the dataset MIT. The upstream OptionsDX terms are unverified."; Licensed provider access: Unavailable); Transformation history (hosted files, streaming pre-filter, one out-of-the-money quote per row, parity forward and discount, implied-volatility inversion, surface grid; each Completed, Documented; **no step numbers**); Data-quality checks (rows removed and why, conserved ledger, duplicates zero); Surface cell mix; static-arbitrage flag counts ("necessary conditions only"); vendor-IV comparison ("sanity check only"). Never describe a source as verified because it is referenced in documents.

### 3.5 Experiments & Pipeline (Stitch `ce4c96df0a204394b692a7f457d9029d`)
Two-row pipeline of large nodes (Data acquisition, Validation, Implied-volatility inversion, Surface construction, Feature extraction, Models, Evaluation, Viewer: Partial two-dimensional only, Licensed data acquisition: Blocked); Recorded experiments table (E-1, E-2, Phase 0 synthetic spike, Phase 0 inference audit: Closed, Neural models on licensed data: Unavailable); Configuration of E-1; Blockers and failures (Blocked: real-data feasibility with a licensed provider; Unverified: licence of the hosted dataset's upstream source; "No failures are recorded in the project documents."). No experiment registry exists (DEC-010 `PROPOSED`); the history is documented, not tracked.

### 3.6 Artifacts (text specification; not designed in Stitch)
Structured list of what exists for the selected run, each with a source chip, size or hash where known, and its state: surface panel (`panel.npz`), metadata (`meta.json`), manifest (`manifest.json`), result tables (names from the API), stored forecasts (names from the API), notebooks (static: `notebooks/Neural_Volatility_Surface_Colab.ipynb`, `notebooks/Neural_Volatility_Surface_E2_FixedExpiry.ipynb`), report and plots (present in the Kaggle output but **not served by the API**: Unavailable). Expected future outputs appear only with the label *Expected, not yet produced*. Empty state: "No run is loaded."

### 3.7 Methodology & Documentation (text specification; not designed in Stitch)
Reading layout (*Read* mode): left in-page contents, a single measure of 68 characters, light or dark by system preference. Sections map to existing documents (UI-011): research methodology, surface construction, IV methodology, evaluation protocol, forecasting strategy, uncertainty and calibration, known limitations, data governance and dictionary, reproducibility (notebooks, run ids, config hashes). Each section shows its status label and last-reviewed date from the document header. Delivery mechanism is an open decision ([IMPLEMENTATION_PLAN §7](IMPLEMENTATION_PLAN.md)).

## 4. Research workflows

1. **Inspect a surface:** Explorer, pick run and date, read the heatmap, check statuses, select a cell, compare the smile and term-structure slices, drill into lineage (planned).
2. **Judge a forecast:** Explorer, pick a model, read Actual, Forecast, Difference for one date with the comparable-cell count; then Evaluation for pooled, by-tenor and by-year results against persistence, with `n`.
3. **Trace a number to its data:** from a cell, to its run lineage (dataset version, config hash, panel hash match), to Data & Provenance (ledger, licence), to Methodology. A mismatch of the panel hash shows the validation warning and marks the run Unverified.

## 5. Surface Explorer requirements

**Views.** Heatmap and Table are mandatory and always available when a run is loaded; 3D is an enhancement ([../docs/design/ACCESSIBILITY.md](../docs/design/ACCESSIBILITY.md) §4; UI-009).

**3D surface (UI-002).** X = log-moneyness k, Y = tenor (days), Z = IV (vol points). Colour = IV (sequential); status by pattern or marker overlay on cells and hidden-by-default extrapolation. Rotate, pan, zoom, Reset view; hover and focus readout (tenor, k, IV, status, quote count); status-layer toggles; slice planes linked to the smile and term-structure panels; keyboard: arrow keys move the selected cell, Rotate, Zoom, Reset buttons. Missing cells render as gaps with a dashed outline marker, never interpolated across. Camera and selected cell are in the URL.

**Data size.** Documented E-1 grid is 6 tenors by 9 nodes per date (54 cells); the panel shape is whatever `tenor_days` and `k_nodes` contain. Rendering cost is therefore not a constraint today ([IMPLEMENTATION_PLAN §3](IMPLEMENTATION_PLAN.md)).

**Forecast comparison (UI-003).** Modes: side by side (linked scale and limits), overlay, difference. Headers show origin date, target date and horizon in panel steps, model, and "backtest". Difference shown only where the actual cell is not missing; MAE reported on observed cells with the count. All from the existing forecast endpoint.

**Slices.** Smile (IV versus k at selected tenor) and term structure (IV versus tenor at selected k), derived client-side from one row or column of the surface payload; observed as markers, interpolated as differently styled segments, forecast overlay in the forecast hue; no band unless an uncertainty kind other than none exists.

**States.** Loading (skeleton), Empty ("No run is loaded"), Partial (some cells missing; never filled), Error (inline with Retry), Unlabelled origin (warning). Stale does not apply (historical backtest only). Never present an invented surface as data: any pre-data illustration is labelled "Conceptual illustration, no run loaded".

## 6. Deviations and open items against existing docs

- **Section set:** PR.md UI-001 (a *recommendation*, `REC`) lists eight sections: Overview, Surface Explorer, Forecast Lab, Backtesting, Research & Explainability, Data Quality, Experiments & Models, Methodology. This design merges Forecast Lab, Backtesting and Research & Explainability into **Evaluation**, renames Data Quality to **Data & Provenance** and Experiments & Models to **Experiments & Pipeline**, and adds **Artifacts**. Rationale: only baseline and descriptive evaluation exists; splitting into three sections would show three mostly empty pages. Owner approval is needed to adopt this in place of UI-001; the split can be restored when content exists.
- **Evaluation "Measured" label** is not `VALIDATED`; nothing is validated (CLAUDE.md status line).
- **API gaps** that this design depends on are listed in [DATA_WIDGET_MATRIX](DATA_WIDGET_MATRIX.md) and [IMPLEMENTATION_PLAN §7](IMPLEMENTATION_PLAN.md).

## 7. Acceptance (future implementation)

1. All screens render the honesty states (loading, empty, partial, error, unavailable, unlabelled origin) without fabricated values.
2. Every number on a screen traces to a row in the widget matrix with a source.
3. A surface shown in 3D has the same data, statuses and units in the heatmap and the table.
4. Keyboard-only walkthrough of the three workflows in §4 completes.
5. No external network request is made by any page (the CSP enforces this).
