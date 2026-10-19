# API Contracts (planning level)

**Status:** §1–§7 are PROPOSED / **NOT A FINALIZED CONTRACT** — MP §18 states these are "planning-level interfaces". No framework (DEC-007), authentication scheme, or schema language is chosen; §1–§7 are not implemented. **§8 documents the local read-only research API that *is* implemented (2026-10-14/15, `backend/src/volatility_lab/api/`), as read from the code and its tests on 2026-10-16, and lists the gaps against §1–§7.** Shared artefact: the core session owns the payload semantics, the "Neural Volatility Surface dashboard design" session consumes them; changes to §8 are proposed here and reviewed by both before code changes.
**Canonical for:** conventions and the endpoint catalogue to be formalized in Phase 5. **Related:** [architecture.md](../../architecture.md) §8, §10; [PR.md](../../PR.md) FR-016/017, SEC-002…004; [design.md](../../design.md)

## 1. Principles
- The API is a **thin transport** over domain modules; no science or IV/surface computation in handlers.
- Read-mostly. Expensive/privileged operations (training, backtests, ingestion) are **jobs**, authorized, rate-limited, asynchronous (FR-017, SEC-004).
- Every payload that carries data includes the **context needed for honest display**: version IDs, data mode, units, status per cell.
- Contract is machine-readable (schema generated/validated by the chosen framework) and covered by contract tests (Phase 5).

## 2. Conventions (proposed)
| Topic | Convention |
|---|---|
| Versioning | URL or header version prefix; breaking changes → new version; schema changes logged in CHANGELOG |
| Identifiers | Opaque version/content IDs (dataset, surface, model, experiment); never filesystem paths |
| Time | ISO-8601 with explicit timezone/UTC; dates for daily data |
| Units | IV in **decimal**; response includes `iv_unit: "decimal"`; presentation conversion is client-side or explicit param |
| Missing | JSON `null` with a status field; never sentinel numbers |
| Cell status | `observed \| interpolated \| extrapolated \| missing` on every surface/forecast cell (GR-DATA-05) |
| Data mode | `historical \| delayed \| latest_available \| real_time_licensed` in every data response (GR-DATA-07) |
| Errors | Envelope: `{error: {code, category, message, reference_id}}`; categories: `invalid_request`, `not_found`, `data_unavailable`, `model_failed`, `forbidden`, `rate_limited`, `internal`; no stack traces/secrets |
| Pagination | Cursor-based for lists; documented maximum page size |
| Validation | All parameters validated (type, range, enum, length); unknown params rejected |
| Caching | Immutable by version ID ⇒ cacheable; "latest" aliases not cacheable (NFR-010) |

## 3. Endpoint catalogue (conceptual, MP §18)
Paths are illustrative.

| Capability | Illustrative endpoint | Notes | Auth |
|---|---|---|---|
| List underlyings & available dates | `GET /underlyings`, `GET /underlyings/{id}/dates` | includes coverage and data mode | read |
| Option-chain snapshot + quality report | `GET /chains/{snapshot_id}`, `GET /chains/{snapshot_id}/quality` | quote data may be restricted by licence (DEC-002); may return aggregates only | read (licence-gated) |
| IV observations for a snapshot | `GET /snapshots/{id}/iv` | includes solver status, failures | read |
| Surface snapshot | `GET /surfaces/{surface_id}` | grid, values, status mask, convention, method/version | read |
| Surface slice | `GET /surfaces/{id}/slice?maturity=…` / `?moneyness=…` | derived from stored grid | read |
| Forecast | `GET /forecasts?model=…&origin=…&horizon=…` | includes `forecast_kind`, `uncertainty_kind`, baseline | read |
| Difference | `GET /compare?forecast=…&target=…` | computed only on comparable cells; returns counts | read |
| Experiment metrics | `GET /experiments/{id}`, `/metrics` | by region/period/regime with `n`, `n_missing` | read |
| Diagnostics | `GET /experiments/{id}/diagnostics/{kind}` | feature/residual/calibration | read |
| Lineage | `GET /lineage/{artifact_id}` | upstream IDs & config versions (UI-010) | read |
| Jobs | `POST /jobs` (train/backtest/ingest), `GET /jobs/{id}`, `DELETE /jobs/{id}` | authorized; rate-limited; resource-limited | privileged |
| Health | `GET /health`, `/health/pipelines` | service and pipeline freshness | public/ops |

## 4. Illustrative response shape (structure only; no market values)
```jsonc
{
  "surface_id": "<id>", "snapshot_time": "<ISO-8601 with tz>", "data_mode": "historical",
  "convention": {"moneyness": "<definition>", "maturity": "<definition>", "version": "<id>"},
  "iv_unit": "decimal",
  "grid": {"moneyness": [/* floats */], "maturity": [/* floats */]},
  "values": [[/* float | null */]],
  "status": [[/* "observed" | "interpolated" | "extrapolated" | "missing" */]],
  "lineage": {"iv_observations": "<id>", "method": "<name>", "method_version": "<id>"}
}
```

## 5. Security requirements for the API
Validate inputs (SEC-002); authentication and rate limiting before any non-local exposure (SEC-003); privileged endpoints separately authorized (SEC-004); no provider credentials in any response (SEC-001); responses respect licence limits (SEC-006). Tests: GR-SEC-03/05.

## 6. Open questions
Framework (DEC-007); auth mechanism (DEC-013); whether raw/validated quotes may be served at all (DEC-002); streaming/WebSocket needs (none assumed — historical mode); export format (FR-018).

## 7. Acceptance
Contract tests generated from the schema; UI fixtures derived from the same schema; UA-01 verifies UI values equal API values.

## 8. Implemented contract: local research API v0 (status `IMPLEMENTED`, local only; tests `backend/tests/unit/test_api.py`)

**Transport.** Standard-library HTTP, `GET` only (other methods → 405 `{"error": "read-only API"}`), bind refused unless loopback, no authentication (Phase 6), `Cache-Control: no-store`, CSP `default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'`. JSON is strict (`NaN` is never emitted; missing numbers are `null`). Names (`run_id`, model, table) must match `^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$`; surface index is 1–7 digits. The API reads files only: it never computes IV, trains or forecasts.

**Runs root layout** (one directory per run): `panel.npz` (required), `meta.json`, `manifest.json`, `tables/*.csv`, `forecasts/<model>.npz` (all optional). A run without a valid `meta.json` is `origin: "unlabelled"` and must be shown as such.

| Route | Returns |
|---|---|
| `GET /` | the single static HTML file |
| `GET /api/runs` | `[{id, origin, description}]`; `origin ∈ {synthetic, real, unlabelled}` |
| `GET /api/runs/{id}` | `{id, origin, description, dates[ISO date], tenor_days[], k_nodes[], status_labels{"0".."3"}, status_counts{label:int}, tables[], forecasts[], lineage}` ; `lineage` is `null` without a manifest, else `{version_id, config_sha256, inputs, ledgers_conserved, ledger_prefilter, ledger_quotes, panel_sha256_recorded, panel_sha256_actual, panel_hash_matches}` |
| `GET /api/runs/{id}/surface/{index}` | `{run, origin, description, index, date, spot, n_quotes, tenor_days, k_nodes, iv[T][K], status[T][K], iv_units}` |
| `GET /api/runs/{id}/forecasts/{model}/{index}` | `{run, origin, description, model, index, target_date, origin_date, horizon_panel_steps, tenor_days, k_nodes, actual[T][K], status[T][K], forecast[T][K], difference[T][K], n_difference_cells, n_observed_cells, mae_observed_vol_points, iv_units}` |
| `GET /api/runs/{id}/tables/{name}` | `{run, table, columns[], truncated, rows[][]}` (first 5,000 rows; numeric cells parsed, empty cells stay text) |

**Semantics the UI must honour.**
- **Axes.** `tenor_days` = constant-maturity tenors in calendar days (E-1: 7, 14, 30, 60, 91, 182). `k_nodes` = forward log-moneyness `ln(K/F)`, F from put–call parity per (date, expiry) (E-1: −0.20 … +0.08). Arrays are indexed `[tenor][k]`. `index` is the position in `dates`, **not** a calendar date; dates are trading days (end-of-day snapshots), ISO `YYYY-MM-DD`, no time zone because the data are daily.
- **Units.** `iv` is decimal (0.20 = 20 %). `mae_observed_vol_points` is in vol points (×100). `difference = forecast − actual`.
- **Cell status** (integer in `status`, label in `status_labels`): `0 missing`, `1 interpolated_T`, `2 interpolated_k`, `3 observed`. There is **no `extrapolated` status because nothing is ever extrapolated**; §2's four-value vocabulary maps as: observed=3, interpolated=1 or 2, missing=0. `iv` is `null` exactly where `status` is 0.
- **"Observed" is a defined term**, not "a quote sits exactly on the node": an expiry lies within about a day (or 1.5 % of the tenor) of the tenor **and** the two real quotes bracketing the node are closer than 0.02 in k; the value is a linear interpolation between those two quotes (`surfaces/grid.py`). Show it as observed-on-grid, with this definition available.
- **Forecast comparability.** `difference` exists only where the actual cell is not missing and the forecast is finite; `n_difference_cells` and `n_observed_cells` are returned, and the MAE uses OBSERVED cells only. A stored forecast whose origin is not strictly before its target is rejected with 400. Under the E-2 label the displayed `actual` is the surface at the target date, **not** the same-expiry value that was scored.
- **Unavailable states.** Missing run/table/forecast/index → 404 `{"error": "<message>"}`; bad name or malformed file → 400; no `lineage` → manifest absent (render "not recorded", never "verified"). `panel_hash_matches == false` → the run is unverified. An absent forecast list means the comparison view is unavailable, not empty.
- **Provenance.** `origin: real` data come from a hosted dataset whose upstream licence is unverified; display of real runs is gated by the owner's licence decision (DEC-002, SEC-006). Everything is a backtest; nothing is real-time.

**Gaps against §1–§3 (core owner's list; no endpoint is invented here).**

| # | Missing | Impact on UI | Smallest proposed contract (for review, **not implemented**) |
|---|---|---|---|
| G1 | `data_mode` (GR-DATA-07) and `forecast_kind` (GR-PRD-05) in payloads | UI cannot show "historical backtest" from data | Optional `meta.json` keys `data_mode: "historical"` and `forecast_kind: "backtest"`, echoed in run info, surface and forecast payloads; absent → UI states "not recorded" |
| G2 | `uncertainty_kind` (GR-MOD-06), model version/target definition (GR-PRD-04) in the forecast payload | Forecast view cannot show assumptions or label the target | Forecast payload adds `uncertainty_kind: "none"` (constant until a model emits intervals) and `target_definition: "nearest_expiry" | "fixed_expiry"` read from the `.npz`, absent → `"unknown"` |
| G3 | Error envelope of §2 (`{error:{code,category,message,reference_id}}`) | Current error is `{"error": "<string>"}` | Keep the string form for v0; migrate with the framework decision (DEC-007) |
| G4 | Per-cell quote lineage (UI-010) and stored arbitrage flags | Widgets stay `UNAVAILABLE` | Needs a panel schema change; out of scope until Phase 2/3 gates move |
| G5 | Experiment / pipeline-stage / project status | No route | Static `docs/engineering/MODEL_STATUS.json` (core-owned, created 2026-10-16); delivery route is the dashboard session's decision |
| G6 | Result-table column names | Unknown until a real run is read | Core will list the actual `pooled.csv` / `per_fold.csv` / region-table columns once a run is available locally |

Core will not change model outputs to simplify the UI, and the UI should not ask the core to alter the surface or forecast definitions to match a chart format.
