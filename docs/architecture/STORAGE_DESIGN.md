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

## 8. Proposed: contract-level quote persistence (Q-F)

**Status: PROPOSED; design answers D1-D10 and D11a approved by the owner on 2026-10-21 (8.8, D11b deferred); implementation go-ahead given 2026-10-21 for synthetic data only (Q-D5); code written in `backend/src/volatility_lab/storage/quote_store.py` with tests, **NOT YET VERIFIED in Colab** (see INTEGRATION_QUEUE Q-D5).** The owner approved quote-level persistence *in principle* on 2026-10-21 and deferred implementation ([decision.md](../../decision.md) "AP-008 follow-up Q-F"; DECISIONS OR-D11). This section is the documentation the decision requires before any code: schema, lifecycle, a check against the approved AP-008 scoring requirements, and the remaining owner decisions. It authorizes no implementation, data acquisition, access to existing SPY artifacts, pilot, B0b execution, S-5, training, inference or evaluation. DEC-009 (file formats) stays `PROPOSED`. Drafted by Agent B (read-only architecture audit) and integrated by the Coordinator; items are labelled V (verified in the repository), P (proposed), I (inferred).

### 8.1 Current state (V)
- Per-quote fields exist only transiently: the wide frame date, expiry, strike, spot, call/put bid, ask and IV (`ingestion/optionsdx.py:177-182`); the OTM-side `quotes` frame with date, expiry, T, strike, k, iv, is_call, mid, rel_spread, F, DF, spot, vendor_iv, reprice_err (`validation/quotes.py:123-130`).
- Lost before persistence: individual bid and ask (only mid and relative spread survive), the non-OTM side, size/volume/open interest (never read), the per-row filter reason (only counts per date and reason are kept: `optionsdx.py:59-65`, `raw_store.py:123-125`), and the per-slice parity forward and discount factor (`quotes.py:31-69`, not persisted).
- The persisted panel holds grid arrays only (`surfaces/grid.py:123-127`); `quotes` is returned by the build (`runner.py:47`) but `save_panel` writes the panel only (`runner.py:50-52`).
- Contract identity today is the key (date, expiry, strike) (`optionsdx.py:33`). Dates are venue calendar dates, never converted to UTC (`optionsdx.py:132-135`); T = (expiry - date) / 365 calendar days (`quotes.py:50,79`); the OTM side is chosen per day by K >= F (`quotes.py:82`), so a strike side can flip between origin day and target day.

### 8.2 Proposed minimum schema (P)
Two tables per quote set, long format, one row per (date, expiry, strike, option type) that reaches the quote stage.

**quote_row**
| Field | Type / unit | Purpose |
|---|---|---|
| `contract_id` | str (hash) | sha256 of the canonical text `underlying|expiry_iso|strike_decimal|C/P`; provider-independent; identical on every day so origin-day and target-day rows join. Strike is a canonical decimal string to avoid float drift |
| `underlying`, `expiry`, `strike`, `option_type`, `settlement` | str, date, float64, enum, enum nullable | identity parts; settlement AM/PM unknown for OptionsDX (DEC-005 note) |
| `quote_date` | int32 epoch days + ISO | venue calendar date |
| `snapshot_kind`, `quote_time_local`, `tz` | enum, nullable | e.g. `eod_close`; time fields only if the provider supplies them |
| `bid`, `ask`, `mid` | float64 | raw bid and ask kept; mid derived |
| `spot`, `F`, `DF`, `T`, `k` | float64 | underlying, slice parity forward and discount factor, calendar-days/365 maturity, ln(K/F) |
| `iv`, `solver_status`, `reprice_err`, `vendor_iv` | float64 nullable, enum, float64, float64 nullable | market IV (null on any non-OK status), solver status, residual (GR-QNT-03), diagnostic only |
| `otm_selected`, `rel_spread` | bool, float64 | whether this is the side the surface used; spread relative to mid |
| `disposition`, `reason` | enum, enum nullable | retained / excluded; reason required when excluded (supports `n_missing` and exclusions-with-reasons) |

**slice_forward**, keyed by (date, expiry): `F`, `DF`, `n_pairs`, `regression`, `fstat`, `T`.

**Per-set provenance (set manifest, not repeated per row):** `origin` (synthetic / real, GR-DATA-04), source id, licence class, data mode, raw-file sha256 list, dataset `version_id`, ingestion timestamp, code version, filter-config hash (the `DataConfig` part of `cfg.sha256`), pricing/IV method version, grid and interpolation version, schema version, library and platform versions (L-34).

**Across days (P):** `contract_id` is stable; rows are per day; an absent contract is not backfilled; both option sides are stored with `otm_selected` marking the surface side; pre-filter rejects stay counts only unless the owner wants rows (D5).

### 8.3 Proposed storage lifecycle (P)
- **Location:** a sidecar store `<root>/quotes/<quote_set_id>/` with its own manifest, separate from `datasets/<version>/` and from run directories.
- **Why not inside existing stores (V):** `ingest` byte-compares `manifest.json` and raises `OverwriteError` on any difference (`raw_store.py:129-131`), so a new key in a dataset manifest breaks idempotent re-ingest; `write_manifest` hashes every file under a run directory (`runner.py:366-370`), so an added file changes that manifest; `Config.sha256()` hashes the whole dataclass (`config/settings.py:92-94`), so quote-persistence options must **not** go into `Config` (use a separate settings object); `run_key` fingerprints config, `Prepared` and folds (`runner.py:164-175`) and must stay untouched. The existing grid-panel format and all frozen artifacts are preserved.
- **Linkage:** the quote-set manifest references the dataset `version_id` and `panel_sha256`; new (not existing) run manifests may add the extra key `quote_set_id` through `write_manifest(extra=...)`.
- **Write-once and versioning:** stage, verify counts and hashes, then promote; manifest written last (as `raw_store.py:137`); `quote_set_id` = hash(dataset `version_id`, quote-policy config hash, schema version, code version); a correction is a new id with a `supersedes` link and a reason (GR-DATA-08); per-snapshot conservation re-checked (`rows_in == kept + rejects`).
- **Hashing:** hash logical content (sorted rows, fixed explicit little-endian dtypes, format-independent, like `panel_sha256`); derive identity from source-numeric columns plus config and code version, not from derived float bytes (L-34: up to 1.7e-14 differences across PC and Linux); record the file-bytes sha256 separately.
- **Format options (not decided; DEC-009):** (a) Parquet/Arrow partitioned by `quote_date` (efficient scans, immutable partitions, makes pyarrow a hard dependency); (b) compressed npz columns (stdlib/numpy only, matches the panel, awkward for strings and ad-hoc queries); (c) SQLite (lineage and joins, poor for large scans); (d) CSV (transparent, large, lossy for float64). §4 above already asks for a benchmark first.
- **Access and retention:** local only, under a git-ignored tree (`.gitignore:32,63`); never served by the API (keep outside the runs root, `API_CONTRACTS` §8); no credentials; no redistribution (DEC-002-A); `origin` label on every set, `.synthetic.` inputs cannot be stored as real (`raw_store.py:103-106`). Size and retention are owner decisions (no numbers proposed). Deletion is a documented purge procedure tested on synthetic data first (DATA_GOVERNANCE §6); a superseded set stays readable until the retention policy allows removal; dependent runs are flagged `source_unavailable`.

### 8.4 Check against the approved AP-008 contract-level scoring (RESEARCH_DESIGN §4.2)
| Requirement | Verdict | Why |
|---|---|---|
| B0a (origin surface at origin-day maturity) | PARTIAL | T_j(t) and k_j(t) come from stored rows and the surface from the panel; the off-node grid evaluation rule (hull per slice or whole grid) is an open specification item |
| B0b (origin surface at target-day maturity) | PARTIAL | as B0a, plus target-day T from stored expiry via the `contract_id` join across days |
| Contract-level forecast evaluation | SUPPORTED (data contract) | realised IV, k_j(t+1) = ln(K/F_t+1) and T_j(t+1) from stored target-day rows; the evaluator code does not exist (Q-D2) |
| `n_missing` | SUPPORTED | eligibility is `disposition = retained` at t+1; the hull test uses stored (k, T) against panel status |
| Hull coverage for the fallback | PARTIAL | data supports it; the definition (numerator, denominator, per origin or pooled) is unresolved |
| Trial-ledger inputs | NOT SUPPORTED by this schema | the ledger is a separate artifact with no schema yet; the quote set only supplies hashes |
| Per-origin MAE, equal weight | SUPPORTED | |
| Vega-weighted secondary | SUPPORTED | Black-76 vega is closed form from stored F, DF, K, T, iv |
| Target-day filter identity | PARTIAL | per-row reasons and the filter-config hash allow censored share by cause; M-07 (selection on post-origin quote quality) is a method issue the schema cannot remove |

Schema gaps closed by the proposal: origin-day F and DF for B0a/B0b (slice_forward), both option sides (side flips), and listed-but-rejected vs absent (reason rows, D5). Gaps left open: hull and coverage definitions and the trial-ledger schema (decision.md AP-008 specification-status table).

### 8.5 Risks (V/P)
M-07 selection on target-day filters (report retained and excluded counts by reason and regime; also score the unfiltered listing); look-ahead if a table mixes days (partition by `quote_date`, require origin-day features only, add a leakage test per CLAUDE.md §9); L-34 dtype and platform sensitivity (fix dtypes, no float bytes in the identity hash); float-key joins (canonical decimal strike); forward estimation by parity makes k not independent of same-day quotes (record method and fstat); American-style SPY priced with Black-76 on OTM quotes only (record method version); licence: the hosted SPY upstream licence is unverified and chain-level files are exactly what DEC-002-A forbids redistributing (keep local only).

### 8.6 Owner decisions D1-D11 (original question list; answered and approved 2026-10-21 in 8.8, D11b deferred)
D1 file format (Parquet / npz / SQLite / CSV; decide with the DEC-009 benchmark); D2 location and root (recommended: sidecar `quotes/` root outside the API runs root); D3 retention, purge and size cap (no default supported); D4 identity-hash policy (recommended: source-numeric columns plus config and code, file hash separate); D5 persist pre-filter rejects as rows or counts only (recommended: counts only unless coverage analysis needs rows); D6 store both option sides (recommended: yes); D7 timestamp convention (calendar date for EOD, nullable time and tz); D8 settlement AM/PM field and exercise style; D9 separate settings object rather than `Config` (recommended: yes); D10 which dataset is first persisted (needs its own data authorization); D11 the open AP-008 specification items (hull and coverage definitions, trial-ledger schema, numeric r\*, fallback threshold, N\*). **Answers to D1-D11 are in 8.8 (D1-D10 approved, D11a approved as specification text, D11b deferred; owner, 2026-10-21). This paragraph is the original question list; where it differs (D1, D5), 8.8 governs.**

### 8.7 Review corrections (Agent C research cross-review, 2026-10-21; integrated by the Coordinator)
- **Reading of the verdicts in 8.4:** SUPPORTED means only that the data fields exist (data contract). The evaluator is not built, nothing is validated, and the exact equal-weight and vega formulas, the definition for an origin with zero eligible contracts, the `n_missing` denominator, and which rows are eligible when a contract is listed at t+1 but not at t are all **open evaluator-specification items** (D11), not settled by this schema.
- **Hull and B0a/B0b inputs:** B0a and B0b need the origin-day surface and its cell status, which live in the panel (`panel_sha256`), not in `quote_row`. The hull test would use (k_j(t+1), T_j(t+1)) from the target-day row together with the origin-day panel; which table holds the hull test and whether it is per expiry slice or whole-grid is **open (D11)**. The hull stays PARTIAL.
- **Which day's F, DF, T, k:** RESEARCH_DESIGN §4.2 places the contract at the target-day coordinates k_j(t+1) = ln(K / F_{t+1}) and T_j(t+1) = (expiry - date_{t+1}) / 365. Whether the B0b k-coordinate uses F_t or F_{t+1} is **not specified by the record** and is an open specification item, not a supported capability.
- **Leakage rule (column level):** F, DF, k, T, iv, `otm_selected` and `disposition` on the **target-day** row (t+1) are label- and scoring-side quantities only and must never feed origin-day features (F_{t+1} is a function of target-day quotes). The required tests are LT-4 (label-construction isolation) and LT-5 (raw-field timing audit), not just "a leakage test".
- **Friday-to-Monday:** T is in calendar days / 365 (DEC-005), so a Friday-to-Monday step moves T by 3 days; the weekday dependence is intended by the convention and remains a DEC-005 sensitivity item (cf. the R-1 stop rule).

### 8.8 Answers to D1-D11 (2026-10-21; APPROVED by the owner as recorded below; not implemented, not run)

**Status: OWNER-APPROVED DESIGN ANSWERS (chat, 2026-10-21); NOT IMPLEMENTED, NOT RUN.** The owner's message read: "Approve D1-D10 as drafted, D11a as specification text, and D11b deferred (numbers stay unfrozen). Record them as approved in STORAGE_DESIGN 8.8, decision.md, INTEGRATION_QUEUE and CHANGELOG, documentation only. Do not implement anything; Q-D5 and Q-D2 still need separate go-aheads." Per item:
- **D1-D10: APPROVED as drafted.** D1 stays **conditional** on the synthetic benchmark of sections 4 and 7, which has not been run, so the file format is not yet fixed and DEC-009 stays `PROPOSED`.
- **D11a: APPROVED as specification text.** It lives in this section; RESEARCH_DESIGN section 11 and EVALUATION_PROTOCOL point to it (pointers, not copies, so this stays the one canonical text); no code implements it. It stays reversible until the first authorized evaluation.
- **D11b: DEFERRED.** r\*, the fallback threshold, N\*, c and rho stay unfrozen (`TBD-pilot`).

The tables below keep the drafting wording ("Recommended answer") and now read as the approved answers. Written from the code and records named in each row (read, not executed). No benchmark has been run, so every statement about size, speed or cost is unmeasured. Approval fixes the design on paper only. It does **not** authorize implementation (Q-D5 and Q-D2 each still need their own go-ahead), data acquisition, access to the held SPY artifacts, a pilot, or any evaluation. Two answers differ from the original recommendations in the 8.6 text: **D5** (rows for quote-quality rejects, not counts only) and **D1** (conditional on the benchmark that sections 4 and 7 already require).

**Open after this approval:** none of D1-D11 is unanswered (D11b is answered by deferral). What remains open is outside this list: the DEC-009 benchmark, the numbers in D11b, and the go-aheads for Q-D5 and Q-D2.

| ID | Decision | Recommended answer | Why (evidence) | If declined or changed |
|---|---|---|---|---|
| D1 | File format | **Parquet** (pyarrow), one partition per `quote_date`, explicit schema with nullable columns. **Conditional:** confirmed or reversed by the synthetic benchmark required by sections 4 and 7 before DEC-009 is decided | Strings and nullable columns (ids, enums, nullable time and tz) fit Parquet and are awkward in npz (8.3 option b); per-date partitions give the immutable partition of rule 5.1. pyarrow is already imported to read Parquet in `ingestion/optionsdx.py:187-189` and is one of the four libraries installed in `.github/workflows/tests.yml`, so it is no new library, but writing quotes makes it a hard requirement of this feature (CLAUDE.md section 13). Parquet bytes are not stable across pyarrow versions, hence D4 | Fallback: npz columns (no pyarrow, fixed-width byte strings for ids, no ad hoc queries). SQLite and CSV not recommended (8.3) |
| D2 | Location and root | **Sidecar** `<store_root>/quotes/<quote_set_id>/` beside `datasets/`, outside the API runs root, git-ignored, never served by the API. On Colab the store sits on the runtime disk and is **ephemeral**: a set is Derived-zone, rebuildable from raw + config + code only while the raw files stay reachable. Copying a **real-data** set to anything persistent (for example the owner's Drive) is a separate owner call, **not recommended** until the owner decides it counts as private local use under DEC-002-A. Synthetic sets may be kept anywhere | 8.3; DEC-002-A (decision.md) forbids publication and redistribution of chain-level derived files; `docs/operations/DEPLOYMENT.md:47` records that the E-1/E-2/H1-H6 outputs were not saved outside the runtimes, so ephemeral storage is the default risk to design around | Persisting real-data sets to Drive: needs an explicit owner statement; until then rebuild from raw each run |
| D3 | Retention, purge, size cap | **No numeric cap now** (any number would be invented). Sets are Derived-zone and deletable at any time. The small set manifest (hashes, counts, provenance) is **kept after rows are purged**, with status `purged`, so a run's `quote_set_id` still resolves. Purge triggers: owner request, a licence finding or termination, end of the study. The purge procedure is written and **tested on a synthetic set before the first real set exists** (DATA_GOVERNANCE section 6 requires this before collecting data). Each manifest records row count and bytes; the cap is set after the first synthetic sizing at the SPY-scale row count | 8.3 access and retention; DATA_GOVERNANCE section 6; dependent runs are flagged `source_unavailable` (8.3) | A fixed cap or retention period needs a number the record does not support yet |
| D4 | Identity-hash policy | **As proposed in 8.3.** `quote_set_id` = hash of the dataset `version_id`, quote-policy hash, schema version and code version; row-level identity from source-numeric inputs (date, expiry, strike, option type, raw bid, ask, spot). Derived floats (F, DF, k, iv, reprice_err) are **excluded** from identity. The file-bytes sha256 is recorded separately for integrity only. On a rebuild, derived columns are compared with a relative tolerance that must exceed the 1.7e-14 cross-platform difference in L-34; beyond it is a hard error, within it a note. The tolerance value is set when its test is written, not here | L-34; this keeps strict input comparison (the closed Patch 1 / D-1 decision is not reopened: no change to the existing manifests or `panel_sha256`) while keeping float bytes out of the identity | If identity included derived floats, a PC-vs-Linux rebuild would mint a different id for the same data |
| D5 | Persist pre-filter rejects (**revises 8.6**) | **Rows for quote-quality rejects, counts only for the rest.** Persist as `disposition = excluded` rows with `reason`: (a) all 13 `QUOTE_REASONS` of `validation/quotes.py:25-28` (each row's reason is already computed at `quotes.py:96-120`, so this adds no new logic), and (b) from the six ingest reasons only `no_usable_side` (neither call nor put passes the ingest usability test; the row has a valid identity). Minimal columns for these rows: identity, date, raw bid and ask, spot, reason. **Counts only** (the existing per-date ledger) for `bad_quote_date`, `bad_expiry`, `bad_strike_or_spot` (no valid identity to key), `dte_out_of_range` and `strike_far_from_spot` (configured universe boundaries, DTE 2-400 by default, not quality), and the two duplicate reasons (a conflicting key cannot be keyed) | 8.4 lists "listed-but-rejected vs absent" as a gap that reason rows close; 8.5 M-07 (selection on post-origin quote quality) can only be reported by cause, and `n_missing` can only separate absent from unusable contracts, if these rows exist. The earlier "counts only" recommendation in 8.6 would leave that gap open | Counts only: smaller store, but M-07 is reportable only in aggregate and absent vs unusable cannot be told apart |
| D6 | Store both option sides | **Yes.** `otm_selected` marks the side the surface used. The non-selected side stores raw bid, ask, mid only, with `iv` null and a new `solver_status` value `not_attempted`, because deep in-the-money American-style quotes are excluded from IV by design (`quotes.py:12-14`) | The OTM side is chosen per day by `K >= F` (`quotes.py:82`), so the same (expiry, strike) can be a call at t and a put at t+1; keeping both avoids losing the target-day quote and allows a labelled side-sensitivity check. About twice the rows (unmeasured) | One side only: smaller, but side flips between origin and target day lose information |
| D7 | Timestamp convention | **EOD:** `quote_date` is the venue calendar date (ISO string plus int32 epoch days, never converted to UTC, as `optionsdx.py:132-135`), `snapshot_kind = eod_close`, `quote_time_local` and `tz` **null** when the provider gives none (OptionsDX gives none) and never filled by assumption. A provider that supplies a time: store the UTC instant plus the source timezone in addition to the date (CLAUDE.md section 6). The set manifest carries the DATA-003 label "end-of-day / delayed, backtest only, not live" | 8.2; CLAUDE.md sections 6 and 7; the dtype is fixed in the schema (L-34) | Intraday data would need a revised convention; none is in scope |
| D8 | Settlement and exercise style | `exercise_style` (american or european) is recorded **per underlying in the set manifest**, not per row; for the SPY ETF it is american (stated in the `quotes.py:12` docstring). The pricing method stays recorded as Black-76 on the parity forward, OTM side only, an acknowledged approximation. `settlement` (AM or PM) stays a row-level nullable field: null for OptionsDX (unknown, DEC-005 note), required for a provider that supplies it | 8.2 and 8.5; L-23 | Per-row exercise style adds nothing while the underlying is fixed |
| D9 | Separate settings object | **Yes.** A separate frozen settings object for quote persistence; `Config` stays untouched. Its hash enters only `quote_set_id` and the set manifest | `Config.sha256()` hashes the whole dataclass (`config/settings.py:92-94`) and `run_key` fingerprints config (`runner.py:164-175`); adding fields would strand archived resume directories and manifests (8.3) | Putting options in `Config` would change every existing hash |
| D10 | First dataset persisted | **Synthetic only.** The generators already exist (`datasets/synthetic.py`, `scripts/phase0_synthetic`); sets carry `origin: synthetic`. This supports the storage benchmark of sections 4 and 7 and the known-answer checks S-1 and S-2 in Colab, and can say nothing about market data (PA-5). **No real-data set** until a dataset is separately authorized: not the held SPY artifacts (DEC-002-A permits private local use per run only with AP-003 or AP-009, names chain-level derived files as non-redistributable, and the dataset is not reachable from this session) and not a Marketdata.app sample until AP-002a replies exist (AP-002b) | decision.md DEC-002-A; APPROVALS AP-002a, AP-002b, AP-003, AP-009; Q-F text (no data acquisition, no access to the SPY artifacts) | Choosing the SPY dataset first needs its own authorization record |
| D11a | Open AP-008 **definitions** (no data needed) | See the sub-table below. **Approved by the owner 2026-10-21 as specification text** (canonical here; RESEARCH_DESIGN section 11 and EVALUATION_PROTOCOL point to it); reversible until the first authorized evaluation | 8.4, 8.7; decision.md "AP-008 specification status" | Any item left open keeps B0b and contract-level scoring unbuildable in that respect |
| D11b | Open AP-008 **numbers**: r\*, fallback threshold, N\*, c, rho | **Do not freeze now.** Keep `TBD-pilot`. Record each in a dated, owner-signed freeze note **before any model result is viewed** (IMPLEMENTATION_PLAN rule 0.3), r\* not derived from the archived H5/H6 gains, and never below the measured minimum detectable effect | decision.md AP-008 remaining work 1-3; PHASE0_FEASIBILITY_PLAN section 3.2 | They need an authorized dataset (R-0); freezing early would be a guess |

**D11a sub-table (recommended specification text; each is a design choice from the record's intent, with no evidence behind it yet):**

| # | Item | Recommended definition | Basis |
|---|---|---|---|
| 1 | Hull | A contract is **in hull** iff its target-day coordinates (k_j(t+1), T_j(t+1)) lie inside the grid's k and T range and all four nodes of the enclosing grid cell have status `observed` or `interpolated` on the origin-day surface. An `extrapolated` or `missing` corner means outside, counted in `n_missing`. Whole-grid, not per expiry slice | DEC-006 (no extrapolation); CLAUDE.md section 7 (observed, interpolated, extrapolated and missing cells stay distinguishable) |
| 2 | Hull coverage | In-hull contracts divided by contracts retained and IV-solved at t+1, reported per origin, pooled, and per tenor bucket. Called "hull coverage" to avoid the clash with interval coverage. The R-1 fallback test uses the development period only, never the final test period. The threshold number is D11b | RESEARCH_DESIGN R-1; decision.md specification table |
| 3 | Evaluation locations | The forecast surface and **B0b** are read at the contract's target-day coordinates (k_j(t+1), T_j(t+1)); **B0a** is read at the origin-day coordinates (k_j(t), T_j(t)). B0b and the forecast then differ only in which surface is read; B0a vs B0b isolates the roll-down effect | 8.4 (B0a coordinates), AP-008(a), M-02; the B0b k-coordinate is not fixed by the record (8.7), so this is a recommendation to confirm |
| 4 | One scored population | The primary contrast scores contracts retained at **both** t and t+1 and in hull, the same population for the forecast, B0a and B0b. Everything else gets a named count: `n_missing` (not in hull), `n_new` (not retained at t), `n_unusable` (not retained at t+1, by persisted reason, needs D5) | 8.7 open item on contracts listed at t+1 but not t; M-07 |
| 5 | Per-origin score | Equal-weight mean absolute error over scored contracts per origin; origins then averaged with equal weight. An origin with zero scored contracts is **dropped and counted** (`n_origins_empty`), never scored as zero. Secondary: Black-76 vega weights from stored F, DF, K, T, iv on the target-day row, normalised per origin | 8.4, 8.7 |
| 6 | Primary reference (Q-B) | The reference for the single primary contrast is the **stronger of B0a and B0b, determined on the development period only**; both are always reported. Declared per stage before any result is viewed | RESEARCH_DESIGN CF-2 (proposal); AP-008(a) says both are reported |
| 7 | Trial ledger (T6) | Append-only JSON lines, never edited or deleted. A line is written **before** each trial (`planned`) and a second line when it ends (`completed`, `aborted` or `failed`). Fields: trial_id, stage, parent_trial_id, contrast_id, is_primary, config hash, dataset and `quote_set_id`, fold and split ids, seed, code version, planned_at and finished_at (UTC), metrics, free-text rationale for any human choice. Granularity: config x fold x seed x contrast. The file's sha256 is recorded in the run manifest | CF-4 T6, CF-6, CF-7; decision.md specification table |

**Sequencing:** (1) owner approval: done, 2026-10-21; (2) recorded as approved in this section, decision.md, INTEGRATION_QUEUE and CHANGELOG (documentation only): done; (3) implementation stays blocked until the owner gives a separate go-ahead for Q-D5 (synthetic only, Colab only), then another for Q-D2 (B0b, contract-level scoring, trial ledger). None of these steps touches the grid-panel format, `panel_sha256`, `Prepared`, `run_key` or any archived run.

**What would reopen these answers (needs a new owner decision):** a benchmark result that favours npz over Parquet (D1); a licence finding on the held SPY data (D2, D10); a data authorization that arrives first (D10); evidence from the R-0 pilot (D11b).
