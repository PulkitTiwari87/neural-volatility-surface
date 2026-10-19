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
| 4 Neural | `IN_PROGRESS` (partial; was mislabelled `PLANNED`) | GPU-only MLP/GRU with CUDA guard | E-1/E-2 executed on Kaggle T4 (descriptive); **no model beat persistence**; [PHASE4_NEURAL_EVIDENCE_REVIEW](../research/PHASE4_NEURAL_EVIDENCE_REVIEW.md) audit and plan; GPU test skipped locally | **NOT MET** (Phase 3 unmet; no test-access log; GR-MOD-01 not enforced in code) | Phase 3; GPU access; DEC-012 | approve H1; the decision rule; GPU/CUDA route |
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
| GR-QNT-03 | – | **gap**: no per-quote solver status/iterations stored, only aggregate ledger counts |
| GR-QNT-04 | – | gap: no `UNSUPPORTED_INSTRUMENT`; European model used on SPY OTM quotes only (L-23) |
| GR-QNT-05 | – | gap: no timezone/holiday/DST fixtures; year fraction is calendar days / 365 |
| GR-QNT-07 | `test_surfaces.DiagnosticsTests` | partial (necessary conditions only) |
| GR-DATA-02/03/08 | `test_storage`, ledger conservation tests | enforced for the local store |
| GR-DATA-05 | `test_surfaces` (status, no extrapolation) | enforced to the API; no UI test |
| GR-LEAK-01/03 | `test_leakage_and_folds` | enforced |
| GR-LEAK-02, -04 | `tests/scientific/test_leakage_sentinels.py` | enforced for baselines (negative control included) |
| GR-LEAK-05, GR-MOD-05 | – | **gap**: no test-window access log |
| GR-MOD-01 | – | **gap**: not enforced in `run_neural` |
| GR-MOD-02/03 | `test_metrics_and_end_to_end` | enforced (`n`, `insufficient_n`) |
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
