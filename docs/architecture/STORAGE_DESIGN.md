# Storage Design

**Status:** PROPOSED (zones & rules); physical format/engine `OPEN` (DEC-009) · **Source:** MP §5, §19, §20 · **Related:** [DATA_FLOW](DATA_FLOW.md), [DATA_VERSIONING](../data/DATA_VERSIONING.md), [DATA_GOVERNANCE](../data/DATA_GOVERNANCE.md), [RECOVERY](../operations/RECOVERY.md)

## 1. Requirements driving the design
Immutable raw data where licence allows (DATA-004); reproducible derived data (NFR-002); lineage queries (UI-010); efficient query by date/snapshot/contract; licence-compliant retention and deletion (SEC-006); no premature infrastructure (NFR-012, MP §19).

## 2. Zones
| Zone | Contents | Mutability | Rebuildable? | In Git? |
|---|---|---|---|---|
| **Raw** | Source-faithful snapshots + source/ingestion metadata | Write-once; corrections = new version | No (re-fetch only if provider allows) → **backup priority** | No |
| **Derived** | Normalized/validated quotes, IV observations, surfaces, features, datasets | Immutable per version; deletable | Yes, from raw + config + code version | No |
| **Serving** | Forecasts, evaluation reports, experiment records, lineage index, job metadata | Append/version; job state mutable | Forecasts/reports rebuildable from derived + run record | No |
| **Config & docs** | `configs/`, docs, code | Versioned in Git | — | Yes |

## 3. Entity → zone mapping (MP §7 entities)
Underlying snapshot, option quote → Raw (then Derived normalized); market assumptions → Derived (versioned assumption sets); derived IV observation → Derived; surface snapshot → Derived; forecast & experiment → Serving.

## 4. Physical options (decision pending — DEC-009)
| Option | Fit | Concerns |
|---|---|---|
| Columnar files (Parquet/Arrow) + embedded SQL engine | Large analytical scans; easy immutability by file/partition; no server | Metadata/lineage queries need an index; concurrent writers |
| Embedded relational DB (SQLite) | Metadata, experiments, lineage index; zero ops | Not ideal for large analytical tables |
| Server RDBMS (e.g., PostgreSQL) | Multi-user, transactions | Operational burden; unnecessary for single researcher (NFR-012) |
| Object store | Remote/shared storage | Cost, credentials, licence egress concerns |

**Proposed starting point:** immutable partitioned files for raw/derived tables plus an embedded metadata/lineage store; no server database in Phases 1–4. **Benchmark before committing:** synthetic dataset sized from the Phase 0 estimate; measure (a) load all quotes for one date, (b) load a time range of surfaces, (c) lineage lookup from a surface cell to its quotes, (d) rebuild cost. Record in the ADR for DEC-009.

## 5. Rules
1. **Atomic publish:** write to staging, verify (counts, hashes), then promote to a version ID; readers only see promoted versions.
2. **Content-addressed IDs:** version ID = hash of content + producing config/code version; identical re-runs yield identical IDs or are detected as duplicates.
3. **No in-place edits** in Raw or Derived; correction ⇒ new version + supersession link.
4. **Lineage index:** each artifact records direct upstream IDs.
5. **Paths are internal:** API and UI use IDs, never paths.
6. **Licence tags:** every raw/derived dataset records source and licence class; export and display check the tag.
7. **Retention & deletion:** a documented procedure to purge provider data on licence termination, including derived data where required (see DATA_GOVERNANCE).
8. **Backups:** Raw zone and Serving experiment records are backed up; Derived is rebuildable but backup may save time. Restore procedure tested in Phase 6.
9. **Secrets** never stored with data; logs never contain payloads that licence forbids retaining.

## 6. Layout sketch (illustrative; not a commitment)
```text
<VOLLAB_DATA_DIR>/
  raw/<source>/<underlying>/<date>/<snapshot_id>/…
  interim/…     (scratch; safe to delete)
  processed/<stage>/<version_id>/…
  external/…    (reference data: calendars, rates; licence-tagged)
  samples/*.synthetic.*   (tiny labelled synthetic fixtures only)
```
Repository directories `data/{raw,interim,processed,external,samples}` mirror this; their contents are git-ignored.

## 7. Acceptance
Immutability test (second write fails); atomic-publish test (crash mid-write leaves no visible version); determinism test (same inputs ⇒ same ID); restore drill (Phase 6); benchmark recorded before DEC-009 is decided.
