# Visualization Specification

**Status:** PROPOSED. DEC-008 DECIDED 2026-10-20 (owner): static 2D viewer, no 3D, no frontend framework; **V1 (3D surface) below is out of scope and not built**; the 2D views are partly implemented in `frontend/index.html` · **Source:** MP §15–§16 · **Canonical for:** per-visualization specs (data, encodings, interactions, alternatives, tests) · **Parent:** [design.md](../../design.md) · **Related:** [DESIGN_SYSTEM](DESIGN_SYSTEM.md), [ACCESSIBILITY](ACCESSIBILITY.md), PR.md UI-002…009

Common to all: context bar visible; axes with units/conventions; status encoding per design.md §8; tooltip fields per design.md §10; table/2D alternative; states per design.md §9; values originate from the API (UA-01).

## V1. 3D volatility surface (UI-002)
- **Data:** surface snapshot (grid, values, status, convention).
- **Encoding:** X = moneyness (convention shown), Y = maturity, Z = IV, color = IV (sequential scale) — status via pattern/marker/opacity; extrapolated hidden by default.
- **Interactions:** rotate/pan/zoom/reset; hover/focus readout; click pin → lineage; toggle status layers; slice planes; compare two dates (linked/overlay/diff).
- **Alternatives:** heatmap (V3) and table; keyboard navigation of nodes (arrow keys move across grid cells, readout announced).
- **Performance:** geometry downsampling with factor displayed; targets from DEC-008 feasibility.
- **Tests:** value-fidelity vs API; status rendering on fixture masks; camera reset; keyboard traversal; empty/partial states.

## V2. Slices (UI-005)
- **Smile** (IV vs *k* at selected *T*) and **term structure** (IV vs *T* at selected *k*); observed points as markers, interpolated as line segments with different style; forecast overlay in forecast hue; confidence band only if `uncertainty_kind ≠ none`, labelled.
- Linked to V1 selection; exact values in tooltip and table.

## V3. Heatmaps (UI-005)
Quantity selector: IV level, forecast, difference (forecast − observed), absolute error, quote-quality, coverage status. Axes = grid; cell tooltip: value, status, n; cells below minimum n hatched "insufficient"; sequential or diverging scale per quantity (diverging centred at zero, limits symmetric by default).

## V4. Actual vs. forecast (UI-003)
Modes: side-by-side (linked camera/axes/scale), overlay, difference. Headers show origin, target, horizon, model@version, baseline, `forecast_kind`. Comparable-cell count and excluded count displayed. Persistence baseline shown alongside.

## V5. Surface evolution (UI-004)
Chronological animation with play/pause/step/scrub; date visible; status styling retained per frame; no tween across missing dates that implies continuity (gaps shown as gaps); reduced-motion ⇒ step only.

## V6. Time series
ATM IV, skew, curvature, term slope over time (observed vs interpolated styling); regime shading; event markers only from as-of-safe calendars; error-over-time with baseline overlay.

## V7. Research charts (UI-006, MP §15–§16E)
| Chart | Content | Required annotations |
|---|---|---|
| Training/validation loss | Per epoch, per seed | Seed spread; early-stop point |
| Baseline vs. model comparison | Metric per region/period | `n`, variability, unit |
| Predicted vs. actual | Scatter with identity line | Cell count, region filter, units |
| Residual distribution & over time | Histogram/QQ + time series | Bin definition, n |
| Error heatmap | Maturity × moneyness | Insufficient-n hatch |
| Regime performance | Table + bars | Regime definition link |
| Feature correlation | Heatmap | Method; collinearity caveat |
| Feature importance / SHAP-style | Bars/beeswarm | Method + stability caveat (SCI-012) |
| Ablation comparison | Metric deltas by feature group | Variability |
| Hyperparameter / experiment comparison | Parallel table | Run IDs, seeds |
| Calibration / coverage | Reliability curve, coverage by region | Only when intervals exist; kind label |
| Data-quality diagnostics | Exclusion waterfall, solver status, missingness | Reconciliation (retained + excluded = ingested) |

## V8. Lineage / provenance views
Breadcrumb chain, side panel with record fields, flags, assumption set, method versions; raw-record display subject to licence.

## V9. Export
Figures and tables export with embedded title, versions, data mode, units, and licence note; export refuses forbidden classes (SEC-006).

## V10. Acceptance
UA-01…UA-14 in design.md §17 applied per visualization; each visualization has: a fixture-based rendering test, an accessibility test (name, description, table alternative, keyboard), and a statuses test (no interpolated-as-observed).
