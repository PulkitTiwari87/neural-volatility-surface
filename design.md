# design.md — Product and Interaction Design Specification

**Status:** PROPOSED. Specification; a static 2D research viewer (`frontend/index.html`) implements part of it. **No brand assets are defined; DEC-008 was DECIDED 2026-10-20 (owner): static 2D viewer, no 3D, no frontend framework**, so the 3D passages below are retained as the original specification but are out of scope (see PR.md UI-002). Colors, fonts and layouts below are semantic rules and constraints, not final visual design.
**Canonical for:** UI behaviour, information hierarchy, status semantics, chart conventions, UI acceptance criteria.
**Related:** [PR.md](PR.md) UI-001…012 · [docs/design/DESIGN_SYSTEM.md](docs/design/DESIGN_SYSTEM.md) (tokens & components) · [docs/design/INFORMATION_ARCHITECTURE.md](docs/design/INFORMATION_ARCHITECTURE.md) · [docs/design/VISUALIZATION_SPEC.md](docs/design/VISUALIZATION_SPEC.md) (per-chart specs) · [docs/design/ACCESSIBILITY.md](docs/design/ACCESSIBILITY.md) · [guardrails.md](guardrails.md) GR-PRD · MP §16–§17

---

## 1. Intent

A professional **quantitative research terminal**: dense but legible, numerically exact, evidence-first. The interface exists to let a researcher move from a surface to its quotes, IV calculation, construction method, forecast, baseline and evidence (UI-010) — not to impress. Visual effects must never make numerical comparison harder (MP §17).

## 2. Design principles

1. **Evidence over decoration.** Every chart answers a research question (RQ-xx) and shows how it was produced.
2. **Status is always visible.** Observed / interpolated / extrapolated / missing / forecast / historical are visually distinct everywhere, including animation and exports (SCI-009).
3. **Exact values on demand.** Any plotted value is inspectable with coordinates, units, timestamp, status and source version.
4. **Context travels with the number.** Axes, units, timestamp, forecast origin & horizon, model version, dataset version, and data mode are never hidden behind interaction.
5. **No chart-only information.** Every 3D or color-coded result has a table or 2D equivalent (UI-009).
6. **Honest uncertainty & limitations.** Absence, failure and weak evidence are shown, not smoothed away.
7. **Restrained motion, calm density.** Animation only where it encodes time order (surface evolution) and respects reduced-motion settings.
8. **Consistency over novelty.** One component vocabulary, one set of formats, one legend for status.

## 3. Information hierarchy

Per view, top to bottom: (1) **context bar** — underlying, data mode & freshness, dataset version, model version, forecast origin/horizon; (2) **primary visualization** — the thing being inspected; (3) **linked secondary views** — slices, tables, diagnostics; (4) **evidence & lineage panel** — selected point's details, quality flags, methodology links; (5) **limitations strip** — view-specific caveats with link to [KNOWN_LIMITATIONS](docs/research/KNOWN_LIMITATIONS.md).

## 4. Navigation

Eight primary sections (MP §17, UI-001), persistent left rail (collapses to icons; labelled for assistive tech):

1. Overview · 2. Surface Explorer · 3. Forecast Lab · 4. Backtesting · 5. Research & Explainability · 6. Data Quality · 7. Experiments & Models · 8. Methodology.

A persistent **context bar** (underlying, date/origin, model, data mode) is shared across sections and reflected in the URL so views are linkable and reproducible. Breadcrumbs support lineage drill-down (surface → grid point → IV observation → quote → raw record).

## 5. Page inventory

| Page | Purpose | Key content | Reqs |
|---|---|---|---|
| Overview | Orientation: dataset status, latest surface, latest forecast, freshness | Status cards (data mode, last snapshot, coverage), mini surface (2D heatmap), latest forecast vs. baseline error summary, active warnings | UI-001, UI-007 |
| Surface Explorer | Inspect a surface | 3D surface, smile/term-structure slices, heatmap, date selector, two-date compare, status toggles, grid-point inspector, table view | UI-002, UI-005, UI-009, UI-010 |
| Forecast Lab | Inspect a forecast | Origin/target/model selectors; side-by-side, overlay, difference views; baseline comparison; uncertainty (with kind label) | UI-003 |
| Backtesting | Walk-forward evidence | Error heatmap (maturity × moneyness), metrics tables with n, error over time, regime breakdown, failure cases | UI-005, UI-006 |
| Research & Explainability | Understand behaviour | Feature correlation, importance (with method & caveat), ablations, residuals, predicted-vs-actual, calibration (if intervals) | UI-006 |
| Data Quality | Trust the inputs | Source status, exclusion counts by reason, missingness maps, quote-quality heatmap, solver failure breakdown, filter sensitivity | UI-005, DATA-005 |
| Experiments & Models | Reproducibility | Run table, configs, windows, seeds, versions, metric comparison, reproduce instructions | SCI-013 |
| Methodology | Definitions & limits | Equations, conventions (coordinates, day-count), pricing assumptions, data-source disclosures, limitations, disclaimers | UI-011 |

## 6. Layout conventions

- Grid-based, information-dense layout; primary visualization occupies the dominant region; secondary panels are resizable/collapsible.
- Fixed placement of recurring elements: context bar (top), status legend (consistent corner of every chart), lineage panel (right).
- Side-by-side comparison panels share axes ranges, color scale and camera (linked) by default; unlinking is explicit.
- Whitespace is for grouping, not decoration; no full-bleed hero imagery.

## 7. Typography and numerical formatting

- Proportional sans-serif for UI text; **monospace/tabular figures for all numbers** so columns align. Final typefaces are chosen in the design system (open).
- **IV units:** the data layer is decimal (0.2000). Displays state the unit explicitly in the axis title or column header — "IV (%)" or "IV (vol pts)" — and a view never mixes the two. Errors are labelled "vol pts" or "decimal" explicitly (MP §14).
- Fixed decimal places per quantity class (IV, moneyness, maturity, price, metric) defined in the design system; consistent rounding mode; never rounding that hides differences being compared.
- Maturity shown with its convention (e.g., "T (yrs, ACT/365)" — actual convention per DEC-005); moneyness shows its definition (e.g., "k = ln(K/F)").
- Timestamps: ISO-8601 date for daily data; timezone always stated for intraday/quote times (UTC and exchange-local); never ambiguous local time.
- Missing values render as an explicit "—" with status "missing", never `0`, `NaN`, or blank. Sample sizes accompany every aggregate ("n = …").

## 8. Color and semantic status conventions

Color is **never the sole carrier** of meaning: each status also has a distinct pattern/marker/line style, and text labels in tooltips and tables. Palette must pass contrast checks in both themes and be color-vision-deficiency safe (verified at implementation, see [ACCESSIBILITY](docs/design/ACCESSIBILITY.md)).

| Status | Meaning | Required visual treatment (semantics, not final styling) |
|---|---|---|
| **Observed** | Value derived from an eligible market quote at this coordinate | Solid fill/marker; highest visual weight |
| **Interpolated** | Computed between observed points by a named method | Lighter/hatched fill; hollow markers; method name in tooltip |
| **Extrapolated** | Computed outside the observed hull | Distinct hatch + warning marker; hidden by default in 3D; always labelled |
| **Missing** | No reliable value | Empty cell with explicit marker; never filled by color scale |
| **Forecast** | Model output for a target time | Distinct hue family and dashed/contrasting line; model & version in label |
| **Historical** | Realized/observed past data or backtest output | Neutral/primary hue family; "backtest" tag when a forecast made in the past |

Additional semantic roles: *error/difference* uses a diverging scale centred at zero with the zero point stated (forecast − observed); *sequential* scale for IV level; *warning/stale/failed* use icon + text, not color alone. A prospective forecast carries a "prospective" tag; a historical backtest carries "backtest — forecast made at origin T". Data-mode badge: `historical`, `delayed`, `latest available`, `real-time licensed` (GR-DATA-07).

## 9. Application states

Every data-driven component implements all of these (UI-008, NFR-008):

| State | Behaviour |
|---|---|
| **Loading** | Skeleton matching final layout; non-blocking; chart axes/context shown once known; long jobs show progress/status and are cancellable. |
| **Empty** | Explains *why* (no data for selection / not computed / out of coverage), shows what exists nearby (available dates), and links to remedy. No blank panels. |
| **Partial** | Renders what exists with a banner stating what is missing and the share of cells affected; missing cells use the "missing" treatment; aggregates show n and exclusions. |
| **Error** | Human-readable cause category (invalid request, data unavailable, model failed, server error), a reference ID for logs, retry where safe; no stack traces or secrets. |
| **Stale** | Shows age of data relative to expectation and data mode; stale data is never styled as current; "live" wording prohibited unless real-time licensed with known latency. |
| **Unauthorized / rate-limited** (when applicable) | Clear message; no partial data leakage. |

## 10. Chart conventions (all charts)

- **Title** states quantity, instrument, and as-of; **subtitle** states dataset/model version and data mode.
- **Axes:** labelled with quantity, unit and convention; ranges stated; shared ranges in comparison panels; log scales explicit.
- **Legends:** always include the status legend (§8) when status is encoded; legends are interactive but never the only way to toggle series (keyboard accessible).
- **Tooltips / readouts (hover and keyboard focus):** coordinates (both conventions where useful: k and strike), IV with unit, status, timestamp(s), source version, contributing quote count (or "interpolated by <method>"), and for forecasts: origin, horizon, model version, baseline value and difference.
- **Annotations:** events (earnings, macro) only from timestamped sources available at the time shown (MP §11).
- **Export:** images/tables embed context (title, versions, data mode, licence note); exports respect licence limits (SEC-006).
- **Sample sizes:** all aggregated charts expose n and exclusions.

## 11. Surface Explorer interactions (UI-002, UI-004)

- 3D: rotate, pan, zoom, reset camera; X = standardized moneyness (convention shown), Y = maturity, Z = IV with color mapped to IV; status mask rendered per §8; extrapolated hidden by default.
- Hover/focus: nearest grid node readout (§10); click pins the point and opens lineage panel (UI-010).
- Slices: choose a maturity → smile; choose a moneyness → term structure; slice plane indicated on the 3D view and the 2D chart is linked.
- Toggle observed-only / include interpolated / show extrapolated.
- Compare two dates: side-by-side (linked camera) or overlay with distinct styles; difference (B − A) available.
- Surface evolution animation (UI-004): chronological only, play/pause/step, date label always visible, status styling preserved each frame, reduced-motion → step controls only, no auto-play.
- Always-available **table view** of the same grid (keyboard navigable) and 2D heatmap alternative (UI-009).
- Graceful degradation for large grids: geometry downsampled with the downsampling factor displayed; exact values remain in readouts/table (NFR-005).

## 12. Actual vs. forecast, difference surfaces and heatmaps (UI-003, UI-005)

- Selectors: forecast origin, target date, horizon, model version, baseline for comparison. Selection state is shown in the context bar and URL.
- Modes: side-by-side (linked), overlay (distinct forecast styling, opacity control), **difference = forecast − observed** (diverging scale, zero stated, symmetric limits by default, unit stated).
- Compute differences only on cells observed in the target surface; other cells show "missing/not comparable" with count.
- Forecast label: "backtest" vs "prospective" (GR-PRD-05). Baseline (persistence) shown alongside; improvement over persistence displayed with n and variability, never as a lone headline number.
- Heatmaps: maturity × moneyness error/difference/quality with annotated cell counts available on hover and in a table; cells below minimum n marked "insufficient".

## 13. Research and backtesting charts (UI-006)

Training/validation loss; baseline-vs-model metric comparison (per region, with n); predicted vs. actual scatter (identity line, region coloring optional); residual distribution and over-time; error over time with regime shading; regime performance table; feature correlation heatmap; feature importance with method & stability caveat (SCI-012); ablation comparison; calibration/coverage plots only when intervals exist, labelled by `uncertainty_kind`. Failure cases are first-class: a "worst cases" list links to the corresponding surfaces. Each chart links to the experiment record that produced it.

## 14. Data quality diagnostics

Source status & freshness; counts of ingested/retained/excluded by reason; stale/crossed/zero-bid maps; solver status breakdown and failure reasons; theoretical-bound violations; coverage (share observed/interpolated/missing) by maturity & moneyness over time; quote-filter sensitivity comparison (RQ-09). All counts reconcile (retained + excluded = ingested) and the UI shows the reconciliation (GR-DATA-02).

## 15. Model and experiment metadata

A compact, always-reachable **provenance card** on every forecast/metric view: source & snapshot, processing/filter versions, pricing/IV method, grid & interpolation version, feature version, train/val/test windows, model config & weights version, seed, evaluation code version, created-at (SCI-013). The Experiments page lists runs with these fields, diff between runs, and a reproduce note.

## 16. Responsive behaviour, accessibility, themes

- **Responsive:** primary target is desktop research use. Tablet: single-column stacking with collapsible panels. Phone: read-only summaries (Overview, key metrics, tables); 3D explorer is not required on small screens — the heatmap/table alternative is provided. Horizontal page scroll is not acceptable; wide tables scroll within their container with sticky headers.
- **Accessibility** (details: [ACCESSIBILITY](docs/design/ACCESSIBILITY.md)): WCAG 2.2 AA as the working target (to be verified at implementation); full keyboard operation including chart navigation; focus-visible; screen-reader names/descriptions for charts with summary text and the data table; no color-only encoding; respects `prefers-reduced-motion` and contrast preferences; text resizable without loss.
- **Themes:** dark and light (UI-012) from one token set; status semantics and contrast verified in both; charts do not rely on theme-specific hues; default follows system preference with explicit override.

## 17. UI acceptance criteria

A view is accepted only when **all** apply (verification method in parentheses). Status of every item: `PLANNED`.

| # | Criterion | Verification |
|---|---|---|
| UA-01 | Each displayed number matches the backend API value for the same selection (within display rounding) | Automated test comparing rendered values to API fixtures (synthetic) |
| UA-02 | Axes, units (decimal/% /vol pts), timestamps, convention definitions, data mode, forecast origin/horizon, model & dataset version are visible without interaction | Component/E2E assertions |
| UA-03 | Observed, interpolated, extrapolated, missing, forecast, historical statuses are distinguishable by more than color, in 3D, 2D, tables, animation, and exports | Visual regression + manual review on synthetic mask fixtures |
| UA-04 | Interpolated/extrapolated cells never render as observed in any mode (incl. animation and overlay) | Test with fixture masks |
| UA-05 | Loading, empty, partial, error, stale states exist and render correctly for every data-driven view | E2E with mocked failures |
| UA-06 | Every 3D view has an equivalent keyboard-accessible table or 2D alternative | Accessibility test |
| UA-07 | Differences are labelled "forecast − observed", zero stated, computed only on comparable cells with count shown | Unit/E2E |
| UA-08 | Backtests vs. prospective forecasts are labelled differently; no "live" wording unless real-time licensed with known latency | E2E + string scan |
| UA-09 | Aggregates display n and exclusions; cells below minimum n marked insufficient | Component tests |
| UA-10 | Lineage drill-down from a grid point reaches quote(s), IV calculation, construction method, and forecast/baseline | E2E |
| UA-11 | Keyboard-only operation, focus order, screen-reader labels, contrast, reduced-motion pass checks in both themes | Automated a11y checks + manual audit |
| UA-12 | No credentials, provider keys, or licensed bulk data exposed to the browser beyond what licence allows | Build/bundle inspection |
| UA-13 | Forecast views carry the disclaimer and limitation link; no advice or profitability language | String scan + review |
| UA-14 | Performance on target grid sizes meets thresholds `TBD(DEC-008 feasibility)`; UI never blocks during load | Measured benchmark |

## 18. Out of scope for this document

Final branding/logo/typography selection, component library choice, framework, and implementation. These follow DEC-008 and Phase 5 ([IMPLEMENTATION_PLAN](IMPLEMENTATION_PLAN.md)).
