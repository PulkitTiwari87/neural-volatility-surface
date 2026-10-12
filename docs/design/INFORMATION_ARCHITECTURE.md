# Information Architecture

**Status:** PROPOSED · **Source:** MP §17 · **Canonical for:** navigation structure, route/state model, cross-links · **Parent:** [design.md](../../design.md) §4–§5 · **Related:** [API_CONTRACTS](../architecture/API_CONTRACTS.md), PR.md UI-001/010/011

## 1. Primary navigation (MP §17)
Overview · Surface Explorer · Forecast Lab · Backtesting · Research & Explainability · Data Quality · Experiments & Models · Methodology.

## 2. Shared selection state ("context")
State carried across sections and encoded in the URL (shareable, reproducible):
`underlying`, `snapshot_date` (or `origin`), `target_date`/`horizon`, `model_id@version`, `baseline_id`, `dataset_id`, `surface_id`, `region/slice selection`, `status filters`, `units`, `theme`.
Rules: the context bar always reflects the state; invalid combinations (e.g., origin without a forecast) produce an *empty* state with remedies, not an error.

## 3. Page responsibilities and primary questions
| Page | Primary questions answered (RQ) | Entry points | Exits (links) |
|---|---|---|---|
| Overview | What data/models exist; is data fresh? | Landing | Explorer, Forecast Lab, Data Quality |
| Surface Explorer | RQ-01, RQ-02: shape, skew by maturity, day-to-day stability | Overview, lineage | Data Quality (cell flags), Forecast Lab (same date) |
| Forecast Lab | RQ-04, RQ-07, RQ-08: how good, how plausible | Overview, Experiments | Backtesting (same model), Methodology |
| Backtesting | RQ-03, RQ-05, RQ-06, RQ-09: where, when, under what regime | Forecast Lab, Experiments | Research (residuals), Data Quality |
| Research & Explainability | RQ-03/07/08: why; residuals, ablations | Backtesting | Experiments |
| Data Quality | RQ-09: trust in inputs | Any chart flag | Methodology (quote policy) |
| Experiments & Models | Reproducibility | Any provenance card | Backtesting, Research |
| Methodology | Definitions, assumptions, limits | Footer/help on every view | KNOWN_LIMITATIONS, data disclosures |

## 4. Lineage navigation (UI-010)
Chain: Forecast/Surface cell → contributing IV observations (or interpolation parameters) → aligned quote → validated quote + flags → raw record metadata (subject to licence display limits). Each hop is a deep link; raw payload display is governed by DEC-002.

## 5. Taxonomy of labels
Status labels: observed / interpolated / extrapolated / missing / forecast / historical. Forecast kind: backtest / prospective. Data mode: historical / delayed / latest available / real-time licensed. Uncertainty: none / heuristic / empirical interval / calibrated. Terms match [GLOSSARY](../project/GLOSSARY.md).

## 6. Content model
Entities exposed to users: Underlying, Snapshot, Surface, Forecast, Model, Dataset, Experiment, Quality report, Job. Each has a stable ID, a detail view, and a provenance card.

## 7. Search and discovery
Selectors with availability hints (dates with data; models with forecasts for the selected origin). No free-text search is required in v1.

## 8. Acceptance
Every research question maps to ≥1 page and chart ([VISUALIZATION_SPEC](VISUALIZATION_SPEC.md)); deep links restore identical views; context bar shows all versions; breadcrumbs make lineage complete (UA-10).
