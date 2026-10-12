# Design System

**Status:** PROPOSED (rules and token *roles*; no values, fonts or assets chosen) · **Canonical for:** token roles, component inventory, formatting rules · **Parent:** [design.md](../../design.md) (principles, status semantics, states). **Related:** [ACCESSIBILITY](ACCESSIBILITY.md), [VISUALIZATION_SPEC](VISUALIZATION_SPEC.md), DEC-008

No final branding, logos, or palette are defined here; choosing them is part of Phase 5 after the DEC-008 feasibility work.

## 1. Token roles (values `OPEN`)
| Group | Roles |
|---|---|
| Surface | `bg-base`, `bg-raised`, `bg-overlay`, `border-subtle`, `border-strong` |
| Text | `text-primary`, `text-secondary`, `text-muted`, `text-inverse`, `text-link` |
| Status (data) | `status-observed`, `status-interpolated`, `status-extrapolated`, `status-missing`, `status-forecast`, `status-historical` — each paired with a pattern/marker token |
| Semantic UI | `info`, `success`, `warning`, `danger`, `stale` — always with icon + text |
| Scales | `scale-sequential-iv`, `scale-diverging-diff` (zero-centred), `scale-categorical` (≤ N series; N set from CVD-safe palette) |
| Typography | `font-ui`, `font-numeric` (tabular figures), `size-xs…xl`, `line-height-*` |
| Spacing | 4-based scale `space-1…`, `radius-*`, `elevation-*` (minimal) |
| Motion | `duration-*`, `easing-*`; all collapse to none under reduced-motion |
| Focus | `focus-ring` (≥ 3:1 against adjacent colors) |

Both themes (dark/light) define every token; components never reference raw colors.

## 2. Formatting rules (apply everywhere)
- Numbers use `font-numeric`, right-aligned in columns, fixed decimals per quantity class (IV, moneyness, maturity, price, ratio, count) defined once in a formatting module of the frontend.
- Units are in headers/axis titles, not only in tooltips. Decimal IV vs percent vs vol points never mixed in one view.
- Missing = "—" + status; never `0`/`NaN`/blank.
- Timestamps: ISO-8601 date; with time ⇒ UTC and exchange-local both available.
- Counts always shown as "n = …" next to aggregates.

## 3. Component inventory (conceptual)
| Component | Purpose | Required behaviours |
|---|---|---|
| Context bar | Underlying, as-of date/origin, horizon, model, dataset, data mode | Always visible; URL-synced |
| Data-mode badge | `historical/delayed/latest available/real-time licensed` | Never "live" unless allowed |
| Status legend | Observed/interpolated/extrapolated/missing/forecast/historical | Identical in every chart; keyboard-focusable |
| Surface 3D view | Interactive surface | Readout, status styling, camera reset, table fallback link |
| Heatmap | Maturity × moneyness grid | Cell tooltip with value, n, status; table toggle |
| Slice chart | Smile / term structure | Linked to 3D selection |
| Time-series chart | ATM IV, skew, curvature, errors | Regime shading, event markers (as-of safe) |
| Metrics table | Region/period/regime metrics | `n`, `n_missing`, insufficient-n marker, sortable, exportable |
| Diff view | forecast − observed | Diverging scale with zero; comparable-cell count |
| Provenance card | SCI-013 fields | Copy-able; links to experiment |
| Lineage panel | Grid point → quote | Breadcrumb drill-down |
| State components | Loading / Empty / Partial / Error / Stale | Standard copy patterns, reference IDs |
| Limitation strip | View-specific caveats | Links to KNOWN_LIMITATIONS |
| Job status | Long-running work | Progress, cancel, logs link |
| Disclaimer | Research-only notice | Present on forecast views and Methodology |

## 4. Content style
Neutral, precise, no hype. No imperative trading language ("buy", "sell", "signal", "opportunity"). Uncertainty wording follows `uncertainty_kind` ([UNCERTAINTY_AND_CALIBRATION](../research/UNCERTAINTY_AND_CALIBRATION.md)). Prefer "model forecast" and "backtest" over "prediction of what will happen".

## 5. Validation
Token coverage check (every component style references tokens); contrast checks for all token pairs in both themes; visual-regression snapshots for status styling on synthetic masks; copy scan for banned phrases (GR-PRD-02).
