# API Contracts (planning level)

**Status:** PROPOSED / **NOT A FINALIZED CONTRACT** — MP §18 states these are "planning-level interfaces". No framework (DEC-007), authentication scheme, or schema language is chosen. Nothing here is implemented.
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
