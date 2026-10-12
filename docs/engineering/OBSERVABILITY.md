# Observability

**Status:** PROPOSED (nothing implemented; tools `OPEN`) · **Source:** MP §20, §22 · **Canonical for:** logging, metrics, health checks, alerts · **Related:** NFR-006/008/011, GR-SEC-04, [RECOVERY](../operations/RECOVERY.md), [architecture.md](../../architecture.md) §11

## 1. Goals
Detect and diagnose data, solver, training and API problems quickly; make data freshness and quality visible as part of the product; never leak secrets or licensed payloads.

## 2. Logging
- **Structured** (key-value/JSON), with: timestamp (UTC), level, module, `run_id`/`job_id`, `dataset_id`/`snapshot_id`/`model_id` where relevant, stage, outcome, duration.
- **Redaction filter** removes secrets and configured sensitive keys (tested, GR-SEC-04).
- **Do not log** raw provider payloads when licence forbids retention, API keys, auth tokens, or full request bodies.
- Levels: DEBUG (development only), INFO (stage start/finish, counts), WARNING (degraded: stale data, high exclusion rate), ERROR (job/stage failure with cause and context).
- Log ingestion, solver, training and API failures (MP §20).

## 3. Metrics (candidate set)
| Domain | Metrics |
|---|---|
| Data freshness | Age of latest snapshot per underlying vs expected cadence; provider API error rate/latency |
| Quote quality | Ingested/retained/excluded counts and rates by reason; zero-bid/crossed/stale rates |
| IV | Solver status counts; failure rate; iterations distribution; bound-violation count |
| Surface | Coverage by status (observed/interpolated/missing); diagnostics flags |
| Training/evaluation | Duration, epochs, loss curves, resource use; evaluation completion |
| API | Request rate, latency, error categories, job queue depth |
| Reproducibility | Count of runs with complete records; failed reproduction checks |

Thresholds/alerts are defined after baselines are measured (`TBD`); no numeric SLOs are asserted now.

## 4. Health checks (NFR-011)
`/health` (service up), `/health/pipelines` (latest successful run per stage, data age, last quality status). Failing or stale pipelines are shown in the UI Overview and Data Quality pages as warnings with the "stale" treatment (design.md §9).

## 5. Alerts and operations
Local use: summarized warnings in job output and UI. Shared/public use: notifications on pipeline failure, stale data beyond tolerance, repeated provider errors, auth anomalies; runbook links in [RECOVERY](../operations/RECOVERY.md).

## 6. Tracing job lineage
Every log line from a job carries the job ID, and the job's run record links logs, inputs and outputs, enabling "why did this surface look odd?" investigations.

## 7. Validation
Redaction test; presence tests for required log fields; synthetic failure injection verifies error logs and health state; metrics exist for each domain by Phase 6.
