# Core engineering status and workstream coordination

**Status:** maintained by the core research/engineering session. First written 2026-10-16. Authoritative phase scope and gates stay in [IMPLEMENTATION_PLAN](../../IMPLEMENTATION_PLAN.md); this file records *what is actually true now* per phase (implementation, evidence, tests, gate, dependencies, owner decisions) and how the core session coordinates with the UI session. Statuses use the repository vocabulary (`PLANNED`, `IN_PROGRESS`, `BLOCKED`, `DEFERRED`; `IMPLEMENTED`/`VALIDATED` only with tests/evidence). A gate is never `MET` here without linked evidence.

## 1. Workstreams and ownership

| Workstream | Session | Owns | Must not |
|---|---|---|---|
| Core research & engineering | this session | `backend/**`, `scripts/**` (except notebooks' UI), research docs, `docs/engineering/**`, API payload semantics (§8 of [API_CONTRACTS](../architecture/API_CONTRACTS.md)), `MODEL_STATUS.json`, core tests and CI proposal | edit `frontend/**`, `dashboard-design/**`, Stitch assets; change model outputs to suit a chart |
| UI | "Neural Volatility Surface dashboard design" | `frontend/**`, `dashboard-design/**`, UI-journey tests | train or change models; change payload semantics unilaterally |
| Shared | both, via documents | [API_CONTRACTS](../architecture/API_CONTRACTS.md) §8, [MODEL_STATUS.json](MODEL_STATUS.json), [MODEL_HANDOFF](../../dashboard-design/MODEL_HANDOFF.md), visualization data contracts | edit each other's files |

**Coordination evidence (what actually happened).** No message was exchanged with the UI session; the channel is repository files only. Observed on 2026-10-16: `dashboard-design/` (7 documents incl. `MODEL_HANDOFF.md`) exists and was read; `frontend/index.html` was **rewritten by the UI session while core tests were running** (new title "Neural Volatility Surface · Quantitative Research Workbench", mtime 01:32 IST), which made `tests/unit/test_api.py` fail once on a stale UI-wording assertion. The core test now checks transport only (served bytes equal the file on disk). No UI file was edited by the core session.

**Status protocol.** Core updates this file, [IMPLEMENTATION_PLAN](../../IMPLEMENTATION_PLAN.md) and [MODEL_STATUS.json](MODEL_STATUS.json) after meaningful changes. `MODEL_STATUS.json` is *never* set to `complete` by the core session: [MODEL_HANDOFF](../../dashboard-design/MODEL_HANDOFF.md) §4 requires the owner's confirmation and an owner instruction to the UI session.

## 2. Per-phase state (2026-10-16)

| Phase | Status | Implemented (code) | Evidence / tests | Exit gate | External dependencies | Owner decisions needed |
|---|---|---|---|---|---|---|
| F Foundation | `ACCEPTED` (owner, 2026-10-19) | docs scaffold; `scripts/foundation_audit.py` | [FOUNDATION_AUDIT](FOUNDATION_AUDIT.md): all mechanical checks pass | **MET** (owner accepted; "no code" criterion superseded) | none | none |
| 0 Feasibility | `IN_PROGRESS`, real-data track `BLOCKED` | synthetic spike `scripts/phase0_synthetic` | spike suite 145 tests OK; A5 synthetic only; A1–A3, A4b not tested/approved ([PHASE0_CLOSURE_RECORD](../research/PHASE0_CLOSURE_RECORD.md)) | **NOT MET** | licence replies, permitted sample, price, provider choice | send/edit the unsent Cboe inquiry; DEC-001/002/003; MVD thresholds |
| 1 Data foundation | `IN_PROGRESS` (partial) | OptionsDX-format adapter with conserved ledger, write-once raw store, versioned datasets, quote validation | unit tests (ingestion/validation/storage); no provider adapter, no timezone/holiday/DST fixtures (GR-QNT-05), CI only proposed | **NOT MET** (Phase 0 unmet) | Phase 0 | DEC-002, DEC-009, DEC-015 |
| 2 IV & surfaces | `IN_PROGRESS` (partial; was mislabelled `PLANNED`) | vectorised Black-76 + IV, constant-maturity grid with cell status, diagnostics, **comparison harness (new)** | 9 recovery + 13 comparison scientific tests, plus the existing pricing/surface unit tests; [PHASE2_SURFACE_COMPARISON](../research/PHASE2_SURFACE_COMPARISON.md) (synthetic) | **NOT MET**: A1 met on synthetic (ordering caveat), A2 partial (no per-quote solver diagnostics stored), A3 met, A4 met on synthetic, **A5 not met (DEC-006 undecided)** | Phase 1 exit; DEC-004/005 decided | DEC-006 option A/B/C, DEC-004, DEC-005 |
| 3 Dataset & baselines | `IN_PROGRESS` (partial) | features, purged walk-forward, leakage audit, persistence/rolling-mean/ridge/PCA-ridge, per-region metrics with `insufficient_n` | unit tests + **3 new fitted-model leakage sentinels**; real-data run E-1/E-2 (off-machine) | **NOT MET** (thresholds and fold count `TBD(Phase 0)`; no go/no-go note) | Phase 2 exit; Phase 0 thresholds | freeze minimum-sample thresholds after Phase 0 |
| 4 Neural | `IN_PROGRESS` (partial; was mislabelled `PLANNED`) | GPU-only MLP/GRU with CUDA guard | E-1/E-2 and H1–H6 executed on Kaggle/Colab GPUs (descriptive); **GRU beats persistence under the fixed-expiry label only (H5/H6; not a general improvement, negative under the nearest-expiry label)**; [PHASE4_NEURAL_EVIDENCE_REVIEW](../research/PHASE4_NEURAL_EVIDENCE_REVIEW.md) audit and plan; GPU test skipped locally | **NOT MET** (Phase 3 unmet; no test-access log; GR-MOD-01 not enforced in code) | Phase 3; GPU access; DEC-012 | approve H1; the decision rule; GPU/CUDA route |
| 5 UI | `IN_PROGRESS` (UI session) | read-only API v0 (core) | 12 API tests; contract in [API_CONTRACTS](../architecture/API_CONTRACTS.md) §8 | **not claimed** | real Phase 3–4 outputs; DEC-007/008 | licence decision for showing real runs |
| 6 Reliability | `PLANNED` (independent pieces started) | audit script, import-direction test (GR-ENG-03), scientific test directory, proposed CI | see §3 | **NOT MET** | Phase 5; DEC-013/014 | CI/toolchain (DEC-015), authentication, deployment, licence |
| 7 Advanced | `DEFERRED` | – | – | – | – | – |

## 3. Verification actually run (2026-10-16, Windows, Python 3.12.6, NumPy 1.26.2, pandas 2.1.3, SciPy 1.14.1, PyArrow 17.0.0, torch 2.13.0+cpu, CUDA unavailable)

| Command (from) | Result |
|---|---|
| `PYTHONPATH=src python -W error::ResourceWarning -m unittest discover -s tests -t .` (`backend/`) | see §3.1 |
| `python -W error::ResourceWarning -m unittest discover -s tests -t .` (`scripts/phase0_synthetic/`) | **145 tests, OK** (before this session's changes; those do not touch this directory) |
| `python scripts/foundation_audit.py` (repo root) | exit 0, no hard failures; 712 relative links checked, 0 broken (664 on the first run, before this session's documents existed) |
| `python scripts/phase2_surface_comparison.py --out <new file>` run twice | identical JSON SHA-256 `ac8c57bd…c927db5` |

### 3.1 Backend suite

Final full run (started before `test_architecture_imports.py` existed): **110 tests, OK, 1 skipped** (the CUDA test; no GPU), 362 s. Then `tests.unit.test_architecture_imports` separately: **4 tests, OK**. Total 114 backend tests, 113 executed. Breakdown of this session's additions: 9 (IV recovery) + 13 (comparison harness) + 3 (leakage sentinels) + 4 (import direction) = 29 new tests; the pre-existing unit suite was 85 (84 run + 1 skipped) before them.

Failures found and handled this session: one transient failure of `test_api` (UI-wording assertion; the UI session rewrote `frontend/index.html` mid-run) → test now asserts the served bytes equal the file; the import-direction test initially tripped on a git-ignored `.ruff_cache` directory in the source tree → test now considers only directories with `__init__.py`. No test was weakened to pass; the first change replaces a UI-copy assertion with a stricter byte-equality assertion.

## 4. Guardrail enforcement now in code

| Guardrail | Check | State |
|---|---|---|
| GR-QNT-01, -02, -06 | `tests/scientific/test_iv_recovery.py` | enforced (synthetic) |
| GR-QNT-03 | `tests/unit/test_quote_diagnostics.py` | **partial (2026-10-20)**: every kept quote carries `reprice_err` (solver residual, < 1e-10 on synthetic data) and the diagnostics hold `reprice_err_max/median` and per-status reject counts; **gap**: rejected quotes are not stored per quote (only counted), no iteration count (fixed 48 bisection steps) |
| GR-QNT-04 | – | gap: no `UNSUPPORTED_INSTRUMENT`; European model used on SPY OTM quotes only (L-23) |
| GR-QNT-05 | `tests/unit/test_ingestion_robustness.py` | **partial (2026-10-20)**: date parsing is strict ISO, tz-aware dates are not shifted through UTC, DST/leap-day day-counts tested; **gap**: no exchange-holiday / early-close calendar (needs DEC-005); year fraction is calendar days / 365 |
| GR-QNT-07 | `test_surfaces.DiagnosticsTests` | partial (necessary conditions only) |
| GR-DATA-02/03/08 | `test_storage`, `test_snapshot_ledger`, ledger conservation tests | enforced for the local store, **per snapshot as well as globally (2026-10-20)**; `verify_dataset` re-checks panel hash, report hash and conservation |
| GR-DATA-05 | `test_surfaces` (status, no extrapolation) | enforced to the API; no UI test |
| GR-DATA-04 | `tests/unit/test_origin_label.py` | **partial (2026-10-20)**: `ingest(origin="synthetic"\|"real")` records the label in the manifest and `meta.json`, refuses `.synthetic.` files as real, the API falls back to the manifest label and reports `origin_conflict`; **gap**: optional (older datasets are unlabelled and cannot be relabelled through `ingest`), `RawStore.put()` itself still accepts any file |
| GR-LEAK-01/03 | `test_leakage_and_folds` | enforced; `assert_no_overlap` now raises `LeakageError` (a real raise, subclass of `AssertionError`) so `python -O` cannot disable it, and an empty fold set fails instead of passing vacuously |
| GR-LEAK-02, -04 | `tests/scientific/test_leakage_sentinels.py` | enforced for baselines (negative control included) |
| GR-LEAK-05, GR-MOD-05 | `tests/unit/test_access_log.py` | **partial (2026-10-20)**: `evaluation/access_log.AccessLog` records train/val/test use per fold via optional `access_log=` on `run_baselines`/`run_neural` (`test_accessed_count`, fit/select on test raises unless authorized); **gap**: an audit trail of what callers report, not an enforced boundary; the executed notebooks do not pass it; `run_neural` path not exercised (no GPU) |
| GR-MOD-01 | `tests/unit/test_governance_guards.py` | **partial (2026-10-20)**: `runner.require_baselines` and the optional `run_neural(baseline_preds=...)` refuse a neural run without persistence + a regression baseline per fold; **gap**: optional, because the executed H1–H6 notebooks call `run_neural` without it (making it mandatory means regenerating notebooks, which changes executed-notebook provenance: owner decision) |
| GR-MOD-02/03 | `test_metrics_and_end_to_end`, `test_metric_edge_cases` | enforced (`n_cells`, **`n_missing` added 2026-10-20**, `insufficient_n`); hand-calculated values and empty / NaN / zero-variance inputs tested |
| GR-ENG-03 | `tests/unit/test_architecture_imports.py` | enforced, **2 known violations listed** (models→evaluation, validation→pricing) |
| GR-SEC-01 | `scripts/foundation_audit.py` | local only; no CI/pre-commit hook |
| GR-SEC-03 | `test_api` (path traversal, bad names) | enforced for the API |
| GR-SEC-04, -05 | – | gap (no redaction test; no authentication, loopback-only bind enforced) |

## 5. Items prepared for the owner (nothing here was applied beyond a file)

- **CI:** [`.github/workflows/tests.yml`](../../.github/workflows/tests.yml) runs the backend suite, the spike suite and the audit on push/PR. **Unverified** (no runner available; only run on Windows). It installs numpy/pandas/scipy/pyarrow unpinned, so it brushes against DEC-015 (toolchain); delete it if you prefer to decide the toolchain first. Nothing was pushed.
- **API gaps G1–G6:** [API_CONTRACTS](../architecture/API_CONTRACTS.md) §8, with the smallest proposed changes for the UI session to review. Not implemented.
- **Machine-readable status for the UI session:** [MODEL_STATUS.json](MODEL_STATUS.json), `status: "in_progress"`, `confirmed_by: null`.

## 6. Next core task

1. Phase 1 independent work: provider-neutral schema notes, timezone / holiday / early-close / DST fixtures and tests for the current maturity convention (GR-QNT-05), without choosing DEC-005.
2. Per-quote solver diagnostics in the quotes frame (closes the GR-QNT-03 gap) – a schema change, to be reviewed with the UI contract first.
3. **Phase 4 H1: EXECUTED 2026-10-19 (Kaggle v1, CPU, 183.8 s, successful; reproduction OK; ridge material, PCA-ridge not; grid still binding under the fixed-expiry label; all verdicts `no_improvement_shown`; details in [PHASE4_NEURAL_EVIDENCE_REVIEW](../research/PHASE4_NEURAL_EVIDENCE_REVIEW.md) §3.2).** **H1b (grid to 1e9, fixed-expiry label only) EXECUTED 2026-10-19 (Kaggle v2, CPU): not material vs H1 (skill change −0.0001 ridge, −0.000003 PCA-ridge); the folds that hit 1e6 now saturate at 1e9 (PCA-ridge 3/8, ridge 2/8); all verdicts `no_improvement_shown`; the H1 baselines stand, details in the review §3.3 (215.4 s, 63 files re-hashed OK, 0 plot errors).** Next: owner decision on H2/H3 (GPU); a stray queued GPU Kaggle Version 1 may still need cancelling in the Kaggle UI. History: approved 2026-10-16, notebook `notebooks/Neural_Volatility_Surface_H1_RidgeGrid.ipynb` prepared with static checks only (no synthetic run, by the owner's instruction), first executed 2026-10-19 on Kaggle by the assistant in the owner's browser session. Not a statement about any neural model; H2/H3 need a GPU session and a separate go-ahead.

4. **H3 EXECUTED 2026-10-19 (Kaggle GPU T4 x2, interactive session, outputs read from the page; not a committed version).** Calendar features (days-to-expiry per tenor + weekday): PCA-ridge fixed-expiry skill +0.0436 (was +0.0068 in H1), passes the decision rule under the fixed-expiry label only (`holds_under_fixed_expiry_label_only`); gru_ens fixed +0.0336 but fails criterion (c) (one seed negative); mlp_ens negative; 30 of 96 neural runs picked epoch <= 3. All neural verdicts `no_improvement_shown`; NO-GO for neural stands. **H2 EXECUTED 2026-10-19 (Kaggle GPU, committed version #1, 238 s, manifest verified):** hypothesis not supported, 56 of 96 neural runs still stop at epoch <= 3; only PCA-ridge nearest-expiry passes the rule (6/8 years, `holds_under_nearest_expiry_label_only`); all neural verdicts `no_improvement_shown`; PCA-ridge is slightly worse than with the previous-year validation. NO-GO for neural stands; details review §3.6. Details: review §3.5. Fix this session: Colab mis-detected as Kaggle (empty `/kaggle/input`), `ON_KAGGLE` now also needs `KAGGLE_KERNEL_RUN_TYPE`.

5. **H4 EXECUTED 2026-10-19 (Colab T4, baselines only, outputs read from the notebook):** the mean-reversion block does not help (PCA-ridge skill change -0.0029 fixed / -0.0088 nearest vs H3, both < 0.01), so the H3 baseline (PCA-ridge + calendar block, skill about +0.04 under both labels, 8/8 years under the fixed-expiry label) is the bar for H5/H6. Note: the config hash is the same for H2/H3/H4 (flags are not part of `Config`). Review §3.8. H5/H6 running.

6. **H5 EXECUTED 2026-10-19 (owner, Colab T4, outputs read by a browser agent):** PCA-factor GRU ensemble clears the pre-registered rule under the fixed-expiry label (skill +0.0351, 8/8 years, all 3 seeds positive) but not under the nearest-expiry label (-0.0610): verdict `holds_under_fixed_expiry_label_only`; it stays below the H4/H3 PCA-ridge baseline (+0.0407). MLP negative. 38/96 runs stop at epoch <= 3. First neural result of this kind; not an improvement claim. Review §3.9. H6 pending.

7. **H6 EXECUTED 2026-10-19 (owner, Colab T4, outputs read by a browser agent):** cell-level GRU with calendar features + tail-fraction validation: fixed-expiry skill +0.0479, 7/8 years, all seeds positive (verdict `holds_under_fixed_expiry_label_only`); nearest-expiry -0.0109; cell-level MLP strongly negative (-0.41 fixed; 2020 blow-up). H3-H6 summary table in review §3.11: no model clears the rule under both labels; GRU and PCA-ridge both about +0.04 to +0.05 under the fixed-expiry label, no robust difference. Phase 4 experiment plan H1-H6 complete; next steps need an owner decision.

## 7. Completion pass 2026-10-20 (offline engineering only; no data acquired, no model trained, no Git operation)

**Owner instructions this pass:** complete the feasible work of Phases 0–6 under the no-data / no-training rule; "no need to verify the results of H1 - H6" (so the H-series figures are carried as recorded in the review, see L-29).

**Verification actually run (Windows, Python 3.12.6, CPU torch 2.13.0):** backend `unittest discover` **158 tests OK, 1 skipped** (CUDA) — baseline before the pass was 131 OK, 1 skipped; Phase 0 spike **145 OK**; `foundation_audit.py` exit 0 (732 links, 0 broken, 0 status-claim problems); leakage tests also run under `python -O` (9 OK); `ruff --isolated --select E9,F63,F7,F82` clean; `git diff --check` clean. **Not run:** CI on a runner (never run), any GPU test, any real-data ingest.

| Phase | Change | Evidence |
|---|---|---|
| 1 | Strict ISO date parsing (non-ISO rejected as `bad_quote_date`/`bad_expiry`, never guessed by `dateutil`); tz-aware dates keep the written calendar date; duplicate contract rows: exact copies collapsed, conflicting copies all rejected, both ledgered | `tests/unit/test_ingestion_robustness.py` (9) |
| 2 | **Defect fixed:** a price inside the no-arbitrage bounds whose root lay outside [1e-4, 5] was reported `BELOW_LOWER_BOUND` (e.g. a price of 95 on a forward of 100); it now has `BELOW_SOLVER_FLOOR` / `ABOVE_SOLVER_CEILING` and its own ledger reasons | `tests/scientific/test_iv_recovery.py` (+1) |
| 3 | `assert_no_overlap` raises `LeakageError` instead of bare `assert` (survived `python -O` no longer), empty fold sets fail | `test_leakage_and_folds` (+1) |
| 4 | GR-MOD-01 guard `require_baselines` and optional `run_neural(baseline_preds=)`; no-network-import / no-download-pattern test for the package; `MODEL_STATUS.json` cannot say `complete` without `confirmed_by` | `test_governance_guards` (8) |
| 5 | Corrupt/empty/hostile run files give predictable 400/404 and a generic 500 (no path leak); missing spot is `null`; symlinks out of a run folder are not served | `test_api` (+8) |
| 6 | CI draft gains a correctness-only lint and a `-O` leakage step (still never run); audit now parses bold decision statuses and checks status claims against the tree; release-checklist state table in `DEPLOYMENT.md` §4a | audit run, diff check |
| 0 | `DATA_ACQUISITION_AUTHORIZATION.md`: terms-review process, owner-authorization record, register (only the interim private-use of the hosted dataset is authorized, licence unverified). Cboe email remains drafted and **unsent** | document; foundation audit |

**Still open after this pass (no gate claimed):**
- *Owner decisions:* send/edit the Cboe inquiry; resolve the hosted-dataset upstream licence; MVD minimum-sample thresholds (not invented here); DEC-005 (maturity convention, blocks holiday/early-close calendar), DEC-007/008 (UI stack/3D: **no 3D or framework added**, decision stands open), DEC-012, DEC-013/014/015; whether GR-MOD-01 becomes mandatory (regenerates executed notebooks); whether to re-ingest the hosted file under the hardened ingestion and compare ledgers (L-31).
- *Added later the same day by three parallel agents (reviewed by the lead; see §4 for the remaining gaps):* per-quote `reprice_err` (GR-QNT-03), window access log (GR-LEAK-05), dataset `origin` label (GR-DATA-04) — each partial, none mandatory for the executed notebooks.
- *Not implemented:* rejected-quote storage and iteration counts (GR-QNT-03), enforced (rather than reported) test-window access, mandatory `origin` (GR-DATA-04), authentication / deployment (no approved target), the two known import-direction exceptions (`models→evaluation`, `validation→pricing`).
- *Scientific:* the inference audit stays `CLOSED — NO-GO`; nothing here is a new scientific claim.

## 8. Owner decisions of 2026-10-20 (recorded from chat; supersede the "owner decisions needed" cells above)

| Decision | Outcome | Effect |
|---|---|---|
| MVD / minimum-sample thresholds | **Adopt the PROPOSED values** (`PHASE0_FEASIBILITY_PLAN` §7 freeze record) | Frozen as *owner-adopted, not evidence-based*; TBD-pilot values stay open; M10 (licence) unmet, so the MVD is **not met** |
| Hosted dataset and Cboe (DEC-002) | **Stop using the hosted Kaggle dataset** | No real dataset is authorized; E-1/E-2/H1–H6 are unpublishable history, not to be re-run or displayed; real-data track `BLOCKED`; the Cboe inquiry remains drafted and unsent (a future sample needs a new owner decision per `DATA_ACQUISITION_AUTHORIZATION`) |
| Maturity convention (DEC-005) | **Keep calendar days / 365** | Closes the holiday / early-close calendar gap by decision; no re-run needed |
| Scope (DEC-007/008/013) | **Local research tool only** | Stdlib loopback API + static 2D viewer kept; no 3D, framework, authentication or deployment; Phase 6 reduces to a CI run and the local release checklist |

Consequences for the phases: Phases 1–5 can now only advance on synthetic data, so their gates remain unclaimed; Phase 6 can become engineering-complete for a local tool once CI has run on a runner (needs your push); Phase 0 cannot pass without an authorized real sample. Remaining open decisions: provider/licence (DEC-002 replacement), DEC-004, DEC-009–012, software licence (DEC-014), toolchain (DEC-015).

## 9. Acceptance-criteria audit, Phases 1–5 (2026-10-20; synthetic data only)

Legend: **MET-L** = met locally by a deterministic offline test on synthetic data (not CI-verified, not a gate); **PART** = partly met; **BLOCKED** = needs an authorized real sample or an owner action; **N/A** = removed by an owner decision. No row is a gate pass.

| Phase | Criterion | State | Evidence / what is missing |
|---|---|---|---|
| 1 | A1 same window twice → identical hashes or new version | MET-L | `test_storage` (reuse, changed bytes/config → new version) |
| 1 | A2 ingested = retained + excluded **for every snapshot**, reason codes, report | MET-L (new) | `test_snapshot_ledger`: per-snapshot ledgers at prefilter, duplicate and quote stages; `quality_report.json` hashed in the manifest; `verify_dataset` |
| 1 | A3 raw store rejects overwrite; correction = new version | MET-L | `test_storage` (`OverwriteError`, altered report refused) |
| 1 | A4 weekend / holiday / early-close / DST fixtures | MET-L as decided | DST, leap-day, weekend, holiday, early-close day counts tested; **by DEC-005 they are plain calendar days** (no calendar), so the fixtures assert the absence of special handling |
| 1 | A5 no secrets/data tracked; CI green | PART | audit exits 0 locally; **CI never run on a runner** |
| 2 | A1 recovery tolerances recorded before real-data runs | PART | tolerances live in `tests/scientific`, not config; written after E-1 (L-28) |
| 2 | A2 every IV record: no fabricated IV, diagnostics present | PART | statuses + per-quote `reprice_err` for kept quotes; rejected quotes are only counted; 14 edge-case tests (`test_iv_edge_cases`) |
| 2 | A3 rebuild gives identical content hash | MET-L | `test_reproducibility`, `test_storage` |
| 2 | A4 every cell has a status, no silent extrapolation | MET-L | `test_surfaces`, API contract tests |
| 2 | A5 ≥2 interpolation × ≥2 filter policies compared; DEC-006 decided | MET-L (synthetic) | `PHASE2_SURFACE_COMPARISON`; DEC-006 option A |
| 3 | A1 leakage tests for every cataloged feature and split | PART | truncation-invariance audit over the produced feature blocks, scaler sentinels, `LeakageError`; no per-catalog-entry mapping test |
| 3 | A2 baselines reproduce exactly from stored run records | PART | bit-identical rerun (`test_reproducibility`); no stored run records from H1–H6 |
| 3 | A3 metrics per maturity × moneyness × period × regime with `n`, `n_missing`, insufficient-n flags | MET-L (new `n_missing`) | `test_metric_edge_cases` (hand-calculated values, partitions, empty/NaN/zero-variance cases) |
| 3 | A4 folds ≥ Phase 0 number; test window not accessed for selection (audit log) | PART / BLOCKED | access log exists (`test_access_log`, caller-reported); MVD M4 adopted but no real data to meet it |
| 3 | A5 go/no-go note on neural experiments | BLOCKED | needs real data; existing H1–H6 are unpublishable history |
| 4 | A1 results reproducible from run record | PART | manifest hash verification; H1–H6 raw outputs not saved (L-29) |
| 4 | A2 per-region/period comparison with n and seed variability | PART | in the executed notebooks / review, not re-verified (owner waived) |
| 4 | A3 test window evaluated once per frozen config, logged | PART | optional `access_log`, optional `require_baselines`; executed notebooks use neither |
| 4 | A4 failure cases documented | MET | `PHASE4_NEURAL_EVIDENCE_REVIEW`, `KNOWN_LIMITATIONS` |
| 4 | A5 uncertainty outputs typed and calibrated only with coverage | N/A | no uncertainty output exists |
| 4 | evidence governance (not a plan criterion) | MET-L (new) | `evaluation/evidence.py`: protocol/label required, `validated` refused without real+licensed data, intervals, owner confirmation, untouched test window; H6-vs-H3 style comparisons flagged non-equivalent (`test_evidence_governance`) |
| 5 | A1 UA-01…UA-14 pass | **NOT MET** | manual journeys / accessibility audit not run; API contract (`test_api_contract`) and static viewer checks (`test_viewer_static`) pass |
| 5 | A2 reviewer can state origin, horizon, versions, baseline, limitation from the UI alone | NOT ASSESSED | needs a human reviewer |
| 5 | A3 accessible alternative for every 3D view | N/A | no 3D (DEC-008) |
| 5 | A4 no credentials / non-permitted data in the browser | MET-L (static) | `test_viewer_static`; no real data is authorized or stored |

**Verification actually run for this audit (Windows, Python 3.12.6; each command run alone, from the repo root or `backend/` as shown):**

| Command | Result |
|---|---|
| `cd backend && PYTHONPATH=src python -W error::ResourceWarning -m unittest discover -s tests -t .` (local stack: numpy 1.26.2, pandas 2.1.3) | **252 tests OK, 1 skipped (CUDA)**, 293 s |
| same, with a clean venv of the latest unpinned packages (numpy 2.5.4, pandas 3.0.6, scipy 1.18.1, pyarrow 26.0.0) | **252 tests OK, 1 skipped**, 181 s |
| `cd backend && PYTHONPATH=src python -O -m unittest tests.unit.test_leakage_and_folds` | 9 OK |
| `python -m ruff check --isolated --select E9,F63,F7,F82 backend scripts` | All checks passed |
| `cd scripts/phase0_synthetic && python -W error::ResourceWarning -m unittest discover -s tests -t .` | 145 OK |
| `python scripts/foundation_audit.py` | exit 0; 734 links (now case-exact), 0 broken, 0 status-claim problems, 0 secret hits |
| `git diff --check` | clean |

Not run: CI on a runner (**never run**), any GPU test, `run_neural` end to end, the UA-01…UA-14 journeys, any real-data ingest, any notebook. Two earlier attempts to run three suites at once were stopped by hand because thread oversubscription made them far slower than a solo run (not a test failure).

**Findings for the UI workstream (not edited here):** the viewer labels data read from a stored run **"Live from run"** (`frontend/index.html`, `src("live")`); GR-DATA-07 reserves "live" for real-time licensed data, so the wording can mislead and should be renamed (for example "From run files"). **Findings fixed in core:** `verify_dataset` crashed on a malformed report (found by its own test); `daily_mae` emitted a spurious `RuntimeWarning` on days without evaluable cells.

## 10. AP-004 patches 2–4 and first Colab verification (2026-10-21; owner-approved; earlier sections unchanged)

**Owner decisions recorded from chat:** D-1 **hold Patch 1** (dtype/manifest, `surfaces/grid.py`) until P1 and cross-environment drift evidence exist; D-2 separate `run_key.json` guard, fail-closed, no PCA-sign change; D-3 non-finite table cells are JSON `null`. The tiny synthetic GPU plumbing test is permitted (not research training); research training and real-data experiments remain unauthorized; no Git operation was performed.

| Patch | Files | Result |
|---|---|---|
| 2 raw-store atomicity | `storage/raw_store.py`; `tests/unit/test_store_atomicity.py` (5) | red on the unpatched sources (hash-named half-written file, changed source not refused, `FileExistsError` on a leftover directory), green after |
| 3 API | `api/service.py`, `api/server.py`; `tests/unit/test_api_edge_inputs.py` (6) | red: table with `nan/inf/1e999` → **HTTP 500** (reported finding reproduced), `HEAD` 501, foreign `Host` 200; green: 200 with `null`, `HEAD`/`OPTIONS` 405, foreign `Host` 400 |
| 4 resume-cache identity | `experiments/runner.py`; `tests/unit/test_run_key.py` (15, training stubbed) | red: changed learning rate and changed label silently reused stale predictions; green: refused with `RunKeyError`, identical rerun resumes with zero training |
| 1 dtype/manifest | `surfaces/grid.py` — **not touched** | **CLOSED by the owner 2026-10-21** (not needed under Colab-only operation; strict manifest comparison kept; evidence in `orchestration/reports/COLAB_VERIFICATION.md` Addenda 8–10); see KNOWN_LIMITATIONS L-34 |

**Verification actually run (Colab, **not** the PC; CPU runtime, Python 3.13.16, numpy 2.1.3, pandas 2.2.3, scipy 1.16.3, torch 2.11.0+cpu; snapshot `worktree_ap004_2026-10-21.tar.gz` sha256 `d85e2e30…3dce`, manifest of 258 files all OK):** full backend suite `CUDA_VISIBLE_DEVICES= PYTHONPATH=src python -W error::ResourceWarning -m unittest discover -s tests -t .` → **278 tests, OK, 1 skipped** (the CUDA plumbing test; no GPU on that runtime), exit 0, 191.7 s. 278 = the previous 252 + 26 new. Earlier Colab records stand: backend 252 OK on a T4 runtime (the GPU test then executed), Phase 0 spike 145 OK, `-O` leakage 9 OK, foundation audit exit 0 (two git checks not evaluated), manifest 255 OK, P2 and P4 as recorded in `orchestration/reports/COLAB_VERIFICATION.md` (Addenda 1–7). Counts quoted in older sections of this file (110/158/179/252) are historical PC-side figures.

**Still not run / open:** P1 and the NumPy 1.26 comparison (need Python 3.12 in Colab; they decide Patch 1), the GPU plumbing test on this snapshot, a live-server P2 re-run after Patch 3, CI on a runner, C-12/C-13/C-09 and the other reviewed findings not in AP-004 scope. No phase gate changes; S1 remains in review.
