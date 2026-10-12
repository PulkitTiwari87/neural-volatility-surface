# Data Dictionary

**Status:** PROPOSED — **conceptual** entities from MP §7. Field types and exact names are finalized after the provider is chosen (DATA-008, Phase 1/2). Nothing here is implemented. · **Canonical for:** entity fields, enums, nullability and invariants. · **Related:** [DATA_FLOW](../architecture/DATA_FLOW.md), [QUOTE_QUALITY_POLICY](QUOTE_QUALITY_POLICY.md), [IV_METHODOLOGY](../research/IV_METHODOLOGY.md)

## Common fields (every persisted record)
| Field | Type (conceptual) | Null | Notes |
|---|---|---|---|
| `origin` | enum `provider \| synthetic` | no | GR-DATA-04 |
| `source` | string | no | Provider/dataset identifier |
| `data_mode` | enum `historical \| delayed \| latest_available \| real_time_licensed` | no | GR-DATA-07 |
| `source_timestamp` | timestamp with timezone | no (if provider supplies) | As given by the source |
| `ingested_at` | timestamp UTC | no | When Atlas stored it |
| `version_id` | string | no | Content-derived ID of the artifact |
| `upstream_ids` | list of IDs | no (except raw) | Lineage |

## E1. Underlying snapshot
`underlying_id`, `timestamp` (+ timezone), `price` (last/reference; `price_kind`), `session_status` (nullable), plus common fields.

## E2. Option quote
| Field | Null | Notes |
|---|---|---|
| `contract_id` | no | Normalized, provider-independent |
| `underlying_id` | no | |
| `quote_timestamp` | no | Distinct from snapshot timestamp |
| `option_type` | no | `call \| put` |
| `strike` | no | Currency units stated |
| `expiration` | no | Date (+ settlement convention) |
| `bid`, `ask` | yes | `bid ≥ 0`; zero is meaningful and flagged |
| `bid_size`, `ask_size`, `last`, `volume`, `open_interest` | yes | |
| `multiplier`, `adjustment_metadata` | yes | Corporate-action adjusted contracts |
| `exercise_style` | no (once known) | `european \| american` (needed by DEC-004) |
| `quality_flags` | no | List of reason codes (see QUOTE_QUALITY_POLICY) |
| `disposition` | no | `retained \| excluded \| down_weighted` |
| `exclusion_reason` | when excluded | Enumerated |

## E3. Market assumptions (versioned assumption set)
`assumption_set_id`, `rate_source/curve`, `rate_value(s)` (as used), `dividend_model` (continuous yield / discrete / implied forward), `dividend_values`, `day_count`, `calendar_version`, `pricing_model`, `valid_from/valid_to`.

## E4. Derived IV observation
| Field | Null | Notes |
|---|---|---|
| `contract_id`, `quote_timestamp` | no | Link to quote |
| `price_used`, `price_selection_method` | no | e.g., midpoint |
| `time_to_expiry`, `convention_version` | no | |
| `forward_or_spot_used` | no | Aligned underlying value and timestamp |
| `iv` | **yes** | Decimal; null iff not converged |
| `solver_status` | no | Enum, see IV_METHODOLOGY |
| `iterations`, `residual` | yes | |
| `failure_reason` | required when `iv` null | |
| `pricing_model`, `assumption_set_id` | no | |
| `quality_flags` | no | |

Invariant: `iv ≠ null ⇒ solver_status = CONVERGED`.

## E5. Surface snapshot
`surface_id`, `snapshot_time`, `underlying_id`, `underlying_price`, `coordinate_system` (+ definition & version), `maturity_convention`, `grid_id` (axes values), `values[k][T]` (decimal IV, nullable), `status[k][T]` (`observed|interpolated|extrapolated|missing`), `source_observation_links`, `construction_method`, `method_version`, `diagnostics` (coverage, gaps, roughness), `iv_observation_set_id`.

## E6. Feature table / dataset version
`dataset_id`, `feature_catalog_version`, `surface_set_ids`, `quote_policy_hash`, `split_definition` (windows, gaps), `fold_definitions`, `row_index` (origin time, target time), `feature_columns` (ID/version), `missing_indicators`.

## E7. Forecast
`forecast_id`, `forecast_origin`, `target_time`, `horizon`, `forecast_kind` (`historical_backtest|prospective`), `model_id`, `model_version`, `dataset_id`, `grid_id`, `values[k][T]`, `uncertainty_kind` (`none|heuristic|empirical_interval|calibrated`), `uncertainty_payload` (nullable), `created_at`, `run_id`.

## E8. Experiment / run record
SCI-013 fields: source & snapshot IDs, processing version, quote-filter config hash, pricing/IV method, grid & interpolation version, feature version, train/val/test windows (+gaps), model config & weights version, seed(s), evaluation code version, creation timestamp; plus hypothesis, metrics (with `n`,`n_missing`), `test_accessed_count`, environment (dependency versions, hardware).

## E9. Quality report
Per snapshot: counts ingested/retained/excluded by reason, stale/crossed/zero-bid counts, timestamp gaps, solver status counts, coverage by status. Invariant: retained + excluded = ingested.

## Enumerations (initial)
Cell status; solver status (IV_METHODOLOGY); `disposition`; exclusion reasons (QUOTE_QUALITY_POLICY); `forecast_kind`; `uncertainty_kind`; `data_mode`; `origin`; `option_type`; `exercise_style`.

## Conventions
IV decimal; times UTC with source timezone preserved; dates ISO-8601; money in source currency with currency code recorded; IDs opaque and content-derived.

## Validation
Schema tests for required/nullable fields and invariants; enum exhaustiveness; round-trip through storage and API preserves statuses and nulls (no sentinel values).
