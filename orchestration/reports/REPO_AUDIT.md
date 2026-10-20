# REPO_AUDIT — Agent A (Repository Auditor), stage S1, task T-A1

**Status:** READY_FOR_REVIEW
**Revision/manifest:** git HEAD `306c01b` ("finishing all the training of models H1-H6", 2026-10-20), branch `main`. Working tree dirty at time of reading (2026-10-20, ~17:30 local): 28 modified tracked files (`git diff --stat`: 685 insertions, 83 deletions), 15 untracked source/test files + `docs/data/DATA_ACQUISITION_AUTHORIZATION.md` + the new `orchestration/` tree (the "44 uncommitted paths" of SHARED_STATUS, plus `orchestration/`). Nothing was executed, committed, reverted or fetched. Evidence labels: **Verified** = a read-only command I ran and whose output I saw; **Observed** = read in files, not executed.

---

## 0. Executive summary (the 5 things the orchestrator most needs)

1. **No test result in this repository has ever been produced outside the owner's Windows PC, and CI has never run.** Every "252 OK" (CORE_STATUS §9, MODEL_STATUS.json, CHANGELOG, workflow header) is a local owner-session transcription. Static count of `def test_*` in `backend/tests` = **252**, which equals the "252 tests OK, 1 skipped" figure, so the doc wording most plausibly means 252 collected of which 1 was skipped (i.e. 251 executed), not 252 passed + 1 skipped. Colab re-execution (V-1) is the only way to turn any of this into evidence.
2. **The H1-H6 notebooks are stale snapshots and still point at the withdrawn dataset.** Each `notebooks/*.ipynb` embeds the package source as `%%writefile` cells generated on 2026-10-19 23:29 (before all of the 2026-10-20 core changes: no `LeakageError`, `BELOW_SOLVER_FLOOR`, `access_log`, `reprice_err`, `quality_report` strings in them). They carry no outputs (`execution_count: null` everywhere), default to `RUN_MODE = "kaggle"` (real hosted data), and `DataConfig.kaggle_dataset` still hard-codes `dudesurfin/spy-options-eod-...` which DEC-002 (2026-10-20) says may not be used. The "executed notebooks" of CORE_STATUS are therefore not in the repo; the H-series numbers exist only as transcriptions (L-29) and the code that produced them differs from the working tree (ingestion, validation, IV status, walkforward, metrics).
3. **A 3D surface view exists in the frontend although every status document says there is none.** `frontend/index.html:545` ("3D surface: Canvas 2D projection") and `:755` implement and expose a 3D tab; `frontend/README.md:3` advertises it; yet DEC-008 (owner, 2026-10-20), README, CLAUDE.md, IMPLEMENTATION_PLAN Phase 5 and CORE_STATUS §8 say "static 2D viewer, no 3D". Not a defect in code, a doc/decision contradiction (UI-owned file; routed).
4. **The status documents contradict each other in at least 20 places** (table in §3), the worst being: IMPLEMENTATION_PLAN Phase 4 still says "no test-access log" while `evaluation/access_log.py` exists; README row 43 says everything under `backend/` "remains PLANNED" while the next rows say IMPLEMENTED; `docs/planning/MILESTONES.md` has M-1/M-3/M-5 `PLANNED`, M-F `IN_PROGRESS`, M-4 "no neural model beat persistence"; CORE_STATUS §7 line 102 says the hosted dataset's interim use "is authorized" while §8 and DATA_ACQUISITION_AUTHORIZATION say the opposite.
5. **A re-ingest hazard introduced by the uncommitted changes:** `storage/raw_store.ingest` compares the new manifest text byte-for-byte with any existing one under the same `version_id`; `version_id` = hash(input hashes, config hash) only (no code/processing version), while the manifest now gains `quality_report_sha256` and new `quote_diagnostics` keys. Any store written before 2026-10-20 (e.g. `scratch/demo_store`, `scratch/demo_store_fc`, which have no `quality_report.json`) will raise `OverwriteError` on re-ingest ("a correction needs a new version" is impossible: nothing in the version id changes). Also CLAUDE.md §8 "processing version" provenance is not recorded anywhere. (Observed by reading; not executed.)

---

## 1. Verified (read-only commands actually run)

| Fact | Command | Result |
|---|---|---|
| Branch/HEAD | `git log --oneline` | `306c01b` > `5ccb8c7` > `3d520f5` > `da837ab` (4 commits total, 2026-10-12 to 2026-10-20) |
| Tracked files | `git ls-files \| wc -l` | 239 |
| Dirty tree | `git status --short` | 28 `M`, 15 untracked files + `docs/data/DATA_ACQUISITION_AUTHORIZATION.md` + `orchestration/` |
| Diff size | `git diff --stat` | 28 files, +685 / -83 |
| Static test-method count, backend | `grep -rE '^\s+def test_' backend/tests \| wc -l` | **252** (unit 212 + scientific 40; per-file list in §2.2) |
| Static test-method count, Phase 0 spike | same on `scripts/phase0_synthetic/tests` | **145** (18+37+13+33+12+9+5+10+8) |
| No dependency manifest / lockfile / Dockerfile / LICENSE tracked | `git ls-files \| grep -iE ...` | none (only `.env.example`, placeholders) |
| No data tracked | `git ls-files data experiments scratch artifacts` | only READMEs / `.gitkeep` |
| Notebooks carry no outputs | `grep -c '"execution_count": null'` per file | all cells null in all 10 notebooks |
| H-series package snapshot is pre-2026-10-20 | `grep -c LeakageError/BELOW_SOLVER_FLOOR/access_log/reprice_err/quality_report` in `Neural_Volatility_Surface_H6_...ipynb` and `..._Colab.ipynb` | 0 for each |
| Hosted dataset still hard-coded | `grep kaggle_dataset` | `backend/src/volatility_lab/config/settings.py:17`; `scripts/_notebook_cells/cells*.py` |
| No test touches the notebook generator or cell code | `grep -rln "_notebook_cells\|build_colab_notebook\|cells_h" backend/tests scripts/phase0_synthetic/tests` | no match (exit 1) |
| `experiments/phase0_synthetic/*` and `scratch/` are git-ignored | `git check-ignore -v` | `.gitignore:67` and `.gitignore:142` |
| `integration/` and `fixtures/` test dirs are empty | `ls backend/tests/integration` | `.gitkeep` only; no `backend/tests/integration` tests exist |
| `configs/` is empty | `ls configs/*` | empty subdirs; configuration lives in code (`config/settings.py` frozen dataclasses) |

**Not Verified (no executable evidence obtained by anyone but the owner, on their PC):** every test pass, every metric, the audit script's exit code, CI.

---

## 2. Observed

### 2.1 Pipeline map (ingestion → ... → frontend) with module state

Package `backend/src/volatility_lab/` (2,868 lines in 33 `.py` files incl. 12 trivial `__init__`), tests 3,104 lines (unit 26 files / 2,644 lines; scientific 5 / 453; integration 0). Dependency order enforced statically by `tests/unit/test_architecture_imports.py` (AST scan; 2 listed violations: `models -> evaluation`, `validation -> pricing`).

```
raw files -> ingestion/optionsdx (wide table, RejectLedger)        [adapter for ONE format: OptionsDX-style wide parquet/csv]
  -> storage/raw_store (write-once raw objects, versioned dataset)  [also calls validation+surfaces: storage is a producer, not only a store]
  -> validation/quotes (parity forwards, OTM selection, filters)   + pricing/bs (Black-76, bisection IV) [merged stage]
  -> surfaces/grid (6 tenors x 9 log-moneyness, linear-in-IV, status per cell; fixed_expiry anchors)
  -> features/panel (Prepared: causal fill, tabular/sequence features, calendar/mean-reversion blocks, 2 target labels)
  -> models/baselines (persistence, rolling mean, ridge, PCA-ridge) | models/neural (MLP/GRU, CUDA-only guard)
  -> evaluation (walkforward purged folds, leakage invariance, metrics by tenor/k/year/regime, decision_rule, compare, access_log, evidence)
  -> experiments/runner (build_surfaces, run_baselines, run_neural, evaluate_all, export_forecasts, write/verify_manifest)
  -> api/ (stdlib read-only loopback server + RunStore reading run folders) -> frontend/index.html (1,057-line single file)
```

| Module | Purpose | Files / lines | Tests that exercise it (mirror) | Status (repo vocabulary, my assessment) |
|---|---|---|---|---|
| `config` | frozen dataclass configs + `sha256()` | 2 / 95 | via `test_reproducibility` (hash), most fixtures | IMPLEMENTED (configs in code, **not** in `configs/` as CLAUDE.md §6 says) |
| `datasets` | synthetic chain generator (known truth) | 2 / 70 | used by ~all tests | IMPLEMENTED (synthetic only, by design) |
| `ingestion` | OptionsDX-format adapter, strict-ISO dates, dedupe, per-snapshot ledger | 2 / 237 | `test_ingestion_validation`(10), `test_ingestion_robustness`(9, untracked), `test_snapshot_ledger`(13, untracked) | PARTIAL: one provider format; real-file schema path (`_iter_raw_batches`, pyarrow) only ever run by the owner off-machine |
| `validation` | forward inference, quote filters, IV call, `reprice_err` | 2 / 153 | `test_ingestion_validation`, `test_quote_diagnostics`(4, untracked), `test_fixed_expiry` | IMPLEMENTED (synthetic); merged with IV stage (known violation) |
| `pricing` | Black-76 price/vega/greeks, vectorised bisection IV, statuses | 2 / 110 | `test_pricing`(4), `scientific/test_iv_recovery`(10), `test_iv_edge_cases`(14, untracked) | IMPLEMENTED (synthetic known-answer) |
| `surfaces` | grid builder, diagnostics, method-comparison harness | 4 / 358 | `test_surfaces`(11), `scientific/test_interpolation_comparison`(13) | IMPLEMENTED; no stored arbitrage flags per cell (API gap G4) |
| `features` | `Prepared` panel, causal fill, features, targets, labels | 2 / 215 | `test_leakage_and_folds`, `test_feature_leakage_variants`(4, untracked), `test_fixed_expiry`(15), `test_h2_h3`(10) | IMPLEMENTED; FEATURE_CATALOG mostly PLANNED (L-32) |
| `models` | baselines; GPU-only MLP/GRU | 3 / 286 | baselines: `scientific/test_leakage_sentinels`(3); neural: `test_gpu_guard`(5, one needs CUDA) | baselines IMPLEMENTED; **neural `train_and_predict` has no CPU-executed test at all** (only the guard and a skipped CUDA test) -> PARTIAL/UNVERIFIED locally |
| `evaluation` | walk-forward, leakage audit, metrics, decision rule, access log, evidence | 8 / 535 | `test_leakage_and_folds`(9), `test_metrics_and_end_to_end`(13), `test_metric_edge_cases`(8), `test_decision_rule`(7), `test_access_log`(5), `test_evidence_governance`(14) | IMPLEMENTED; `access_log`, `evidence`, `require_baselines` are **opt-in and unused by any pipeline/notebook** (guards exist, enforcement does not) |
| `experiments` | orchestration of runs + manifests | 2 / 302 | `test_metrics_and_end_to_end`, `test_governance_guards`(8), `test_reproducibility`(7), `test_gpu_guard`; `run_neural` only through stubs | PARTIAL; writes artifacts itself (CLAUDE.md §4 "only storage/ touches persistence" not followed) |
| `storage` | write-once raw store, versioned datasets, `verify_dataset` | 2 / 172 | `test_storage`(8), `test_origin_label`(10, untracked), `test_snapshot_ledger` | IMPLEMENTED; see re-ingest hazard (§0.5) |
| `api` | stdlib read-only loopback HTTP + `RunStore` | 3 / 335 | `test_api`(21), `test_api_contract`(6, untracked), `test_viewer_static`(7, untracked) | IMPLEMENTED (local); no auth by decision; computes forecast MAE in the service layer; no Host-header check (DNS-rebinding on loopback not considered) |
| `domain` | (planned) pure domain types | 0 (`.gitkeep`) | - | PLANNED |
| `observability` | (planned) | 0 (`.gitkeep`) | - | PLANNED |

Other code: `frontend/index.html` (1,057 lines, UI session-owned, tested only by static string checks + served-bytes equality); `scripts/` (foundation_audit 188, build_colab_notebook 194, make_synthetic_run 71, phase2_surface_comparison 58, `_notebook_cells/*` 1,628 lines of cell-text strings); `scripts/phase0_synthetic/` stdlib spike (phase0 1,821 + chainpipe 753 + diagnostics 365 + tests 1,673 lines); 10 notebooks (9 generated + 1 exploratory).

### 2.2 Static test-method counts (not execution)
Backend unit: access_log 5, api 21, api_contract 6, architecture_imports 4, decision_rule 7, evidence_governance 14, feature_leakage_variants 4, fixed_expiry 15, governance_guards 8, gpu_guard 5, h2_h3 10, ingestion_robustness 9, ingestion_validation 10, leakage_and_folds 9, metric_edge_cases 8, metrics_and_end_to_end 13, origin_label 10, pricing 4, quote_diagnostics 4, reproducibility 7, snapshot_ledger 13, storage 8, surfaces 11, viewer_static 7 = 212. Scientific: interpolation_comparison 13, iv_edge_cases 14, iv_recovery 10, leakage_sentinels 3 = 40. **Total 252**, matching the tree-wide `grep` (re-added by hand after a first mis-sum). Caveat: a static `def test_` count ignores inherited tests, sub-tests and generated tests, so it can differ from the number unittest reports.

### 2.3 Classification of every claimed capability

| Capability (as claimed in README / CORE_STATUS / IMPLEMENTATION_PLAN) | My class | Basis |
|---|---|---|
| Phase 0 synthetic spike (stdlib), 145 tests | **implemented (synthetic), unverified in clean env** | code + 145 test methods exist; run only on owner PC; evidence JSONs it cites are git-ignored (`experiments/**`) so hashes cannot be checked from a clean checkout |
| Phase 0 real-data feasibility | **planned / blocked** | no sample, no terms, Cboe email unsent |
| OptionsDX-format ingestion + conserved ledger (global + per snapshot) | **implemented (synthetic tests); real-file path unverified** | |
| Write-once raw store, versioned datasets | **implemented**, with re-ingest hazard | `raw_store.py:~125` |
| Quote validation / forward estimation | **implemented (synthetic)** | |
| Black-76 IV + recovery | **implemented (synthetic)** | tolerances written after E-1 (L-28) |
| Per-quote solver diagnostics (GR-QNT-03) | **partially implemented** | `reprice_err` for kept quotes only; rejected quotes counted not stored; no iteration count (docs disagree, §3 row 5) |
| Constant-maturity surfaces, cell status | **implemented** | |
| Interpolation/filter comparison (DEC-006 A5) | **implemented (synthetic), decision decided as option A** | A5 replacement rule "pre-registration-only" |
| Purged walk-forward + leakage audit | **implemented** | `LeakageError` now raises (uncommitted) |
| Baselines (persistence, rolling mean, ridge, PCA-ridge) | **implemented** | sentinels incl. negative control |
| Neural MLP/GRU, GPU-only guard | **partially implemented / unverified**: guard tested; training path untested on CPU; results exist only as off-machine transcriptions | |
| H1-H6 results ("GRU beats persistence under fixed-expiry label only") | **unverified** | no outputs in notebooks, no run dirs saved, owner waived verification (L-29) |
| Pre-registered decision rule | **implemented (code)**; pre-registration itself is documentation only | |
| Access log (GR-LEAK-05), `require_baselines` (GR-MOD-01), origin label (GR-DATA-04), evidence governance | **partially implemented**: present, tested, **optional and not wired into the notebooks/pipeline** | |
| Read-only stdlib API + static 2D viewer | **implemented (local); viewer is not 2D-only** (3D canvas exists) | |
| UA-01..UA-14 journeys / accessibility audit | **planned** (never run) | |
| CI | **planned/drafted, never run** | |
| Provider adapters other than OptionsDX-format | **planned** | none |
| Experiment tracking / forecast store (DEC-010) | **planned**; `write_manifest`/`verify_manifest` is a minimal file-hash manifest | |
| Uncertainty / calibration | **planned / N/A** | no model emits intervals |
| Authentication, deployment, 3D framework | **out of scope by owner decision (DEC-007/008/013)**; 3D canvas nevertheless present | |
| Phase 6 reliability pieces (audit script, import test, CI draft) | **partially implemented, unverified** | `foundation_audit.py` status-claim check is a regex heuristic |

---

## 3. Contradictions, stale numbers and doc drift

### 3.1 Test counts
| Source (file:line) | Figure | Comment |
|---|---|---|
| `docs/engineering/CORE_STATUS.md:42` | 110 OK, 1 skipped, 362 s; +4 separately = "114 total, 113 executed" | 2026-10-16 |
| `CORE_STATUS.md:92` | 158 OK, 1 skipped (baseline before pass 131) | 2026-10-20 completion pass |
| `docs/engineering/MODEL_STATUS.json:18` and `CHANGELOG.md:58` | 179 OK, 1 skipped | after three agents' additions |
| `CORE_STATUS.md:157-158`, `MODEL_STATUS.json:19`, `.github/workflows/tests.yml:3` | 252 OK, 1 skipped (local stack 293 s; clean latest-deps venv 181 s) | static `def test_` count is also 252 (so "252 OK + 1 skipped" is probably "252 collected, 1 skipped") |
| `docs/research/PHASE0_A2D_DIAGNOSTIC_DESIGN.md:12`, `docs/planning/MILESTONES.md:9` | spike 110 / 112 tests | pre-chainpipe; spike is now 145 (57+37+18+33) while A2d doc says 16 A2d tests (actual 18) |
| `CORE_STATUS.md:27` | "12 API tests" | now 21 (+6 contract +7 viewer) |
| `MODEL_STATUS.json:15-21` | seven `completed_validation` entries, cumulative, no "current" marker | a consumer reading the file cannot tell 110 from 252 without dates |
| Foundation audit links | 712 (§3), 732 (`CORE_STATUS.md:92`, MODEL_STATUS), 734 (§9, `:162`) | different dates, same command |

### 3.2 Status / scope contradictions
| # | Statement A | Statement B | Verdict |
|---|---|---|---|
| 1 | `README.md:43` "everything else under `backend/` remains PLANNED" | `README.md:~52` "Research code `backend/src/volatility_lab` ... IMPLEMENTED" | README stale row |
| 2 | `IMPLEMENTATION_PLAN.md:26` Phase 4 "no test-access log" | `evaluation/access_log.py` + `test_access_log.py`; `CORE_STATUS.md:60` "partial" | plan stale |
| 3 | `IMPLEMENTATION_PLAN.md:24` Phase 2 "per-quote solver diagnostics not stored" | `CORE_STATUS.md:51` `reprice_err` per kept quote; `docs/operations/DEPLOYMENT.md:43` still lists it as a gap | partial truth: kept quotes yes, rejected quotes no |
| 4 | `CORE_STATUS.md:26` (Phase 4 row) "no test-access log; GR-MOD-01 not enforced in code" | `CORE_STATUS.md:60-61` partial | file mixes 2026-10-16 table (§2 header date) with 2026-10-20 facts |
| 5 | `CORE_STATUS.md:102` "register (only the interim private-use of the hosted dataset is authorized)" | `CORE_STATUS.md:115`, `DATA_ACQUISITION_AUTHORIZATION.md:36` "None ... REFUSED" | §7 table row stale |
| 6 | `decision.md:44` "continue with the hosted SPY ... dataset as the private research dataset" | `decision.md:22` DEC-002 withdrawn 2026-10-20 | narrative paragraph stale |
| 7 | `frontend/README.md:3` "surface explorer with 3D surface"; `frontend/index.html:545,755`; `dashboard-design/IMPLEMENTATION_STATUS.md:7,39` Canvas 3D | `decision.md` DEC-008, `README.md`, `CLAUDE.md`, `CORE_STATUS.md:117` "static 2D viewer, no 3D" | real contradiction; UI-owned |
| 8 | `frontend/README.md:5` "DEC-008 still open" | `decision.md` DEC-008 DECIDED 2026-10-20 | stale |
| 9 | `docs/planning/MILESTONES.md:8,10,12,14` M-F `IN_PROGRESS`, M-1 / M-3 / M-5 `PLANNED` | `IMPLEMENTATION_PLAN.md:19,23,25,27` F accepted; 1, 3, 5 `IN_PROGRESS` | stale |
| 10 | `MILESTONES.md:13` M-4 "no neural model beat persistence" | H5/H6 `holds_under_fixed_expiry_label_only` (`README.md`, `CLAUDE.md`) | stale; `PHASE4_NEURAL_EVIDENCE_REVIEW.md:3` headline ("no neural model has been shown to beat persistence") is the same pre-H5 wording atop a document that later records H5/H6 |
| 11 | `docs/engineering/TESTING_STRATEGY.md:3` "no product tests exist"; `tests/README.md:3` PLANNED; `architecture.md:3` "Nothing described here is implemented" | 252 backend tests; research package exists | stale headers |
| 12 | `notebooks/README.md:3` "Status: PLANNED"; `:9,13,15` H1-H6 "NOT yet executed" | `CORE_STATUS.md` H1-H6 executed 2026-10-19; `configs/README.md` PLANNED but config lives in code | stale |
| 13 | `scripts/README.md:3` "one disposable spike"; table omits `build_colab_notebook.py`, `make_synthetic_run.py` | both exist | stale |
| 14 | `CORE_STATUS.md:110-119` "H1-H6 are unpublishable history, not to be re-run or displayed" (DEC-002) | `README.md` status table, `CLAUDE.md`, CORE_STATUS, KNOWN_LIMITATIONS display the H5/H6 skill figures (+0.035, +0.048 ...) | policy vs prose conflict; needs owner/B ruling on what "display" covers |
| 15 | `CORE_STATUS.md:78` ("Next: owner decision on H2/H3 (GPU); a stray queued GPU Kaggle Version 1 may still need cancelling") under "§6 Next core task" | items 4-7 below it record H2-H6 executed | §6 is a chronological log, not a to-do |
| 16 | `README.md` H5 vs "best baseline H3 PCA-ridge +0.0436"; `CORE_STATUS.md:84` H5 "below the H4/H3 PCA-ridge baseline (+0.0407)" | two different baseline numbers for the same comparison (H3 vs H4) | minor, both recorded in review |
| 17 | `CORE_STATUS.md` "executed notebooks" (`:61`, `:144`) and `docs/operations/DEPLOYMENT.md` | L-29: notebooks in repo carry no outputs and no run dir saved | "executed" refers to off-machine copies not in the repo |
| 18 | `docs/research/PHASE0_AUDIT.md:174`, `PHASE0_CLOSURE_RECORD.md:27` "0 of 15 decided" | `README.md` "6 of 15 decided, 2 interim" | historical records; fine if dated, but undated phrase |
| 19 | `README.md` and others say 2D / "no 3D" while `CLAUDE.md` (project) says "no 3D, framework undecided" | same as row 7 | |
| 20 | `CLAUDE.md` §6 "Config lives in `configs/`" | `configs/` empty; config in `config/settings.py` | convention not followed |

### 3.3 Other consistency notes
- `CORE_STATUS.md` §2 table header is "(2026-10-16)" yet rows include 2026-10-19/20 content; §3 is 10-16 verification; §7-§9 are 10-20. There is no single "current state" table; a reader must reconcile five time slices.
- `foundation_audit.py:check_status_claims` only greps for a few phrases (`GATE_PASSED`, `(none exist)`, `NOT IMPLEMENTED, NOT VALIDATED`); it cannot detect the contradictions above, so "0 status-claim problems" is weak evidence.
- Statuses in README use `IMPLEMENTED` for the research package, while CLAUDE.md §6 says `IMPLEMENTED` requires "code merged and tested". The code is **not merged** (uncommitted) and the tests have only run locally. Per the repo's own rule, `IMPLEMENTED` for the 2026-10-20 additions is premature; `IN_PROGRESS` would be exact.

---

## 4. Uncommitted working tree (what each change does; docs/tests accompany?)

Modified source (all synthetic-tested only, per docs):
| File | Change | Tests | Docs |
|---|---|---|---|
| `ingestion/optionsdx.py` | strict ISO dates (non-ISO -> NaT -> `bad_*`), tz-aware dates keep written date, duplicate handling (`duplicate_row_exact`, `conflicting_duplicate_key`), per-snapshot ledger (`by_date`, `check_by_date`, `by_date_report`) | `test_ingestion_robustness`, `test_snapshot_ledger` (both untracked) | CHANGELOG, CORE_STATUS §7/§9, L-31 |
| `validation/quotes.py` | two new reject reasons, per-snapshot terminal disposition, per-quote `reprice_err`, `reprice_err_max/median`, `solver_status_rejects` | `test_quote_diagnostics`, `test_snapshot_ledger` | CHANGELOG, CORE_STATUS §4 |
| `pricing/bs.py` | defect fix: in-bounds price whose root is outside [1e-4, 5] was `BELOW_LOWER_BOUND`; now `BELOW_SOLVER_FLOOR`/`ABOVE_SOLVER_CEILING` | `scientific/test_iv_recovery` (+1), `test_iv_edge_cases` | CHANGELOG |
| `storage/raw_store.py` | optional `origin` label, `quality_report.json` + hash in manifest, `verify_dataset`, `_write_meta` | `test_storage` (+), `test_origin_label`, `test_snapshot_ledger` | CORE_STATUS; **behaviour change: manifest format**, old stores un-reusable (§0.5) |
| `evaluation/walkforward.py` | `assert` -> `LeakageError` raise; empty folds fail | `test_leakage_and_folds` (+1; also run with `-O`) | CHANGELOG |
| `evaluation/leakage.py` | perturbation also scrambles the calendar block | `test_feature_leakage_variants` | L-32 |
| `evaluation/metrics.py` | `n_missing` in `overall`/`breakdowns`; warning-free `daily_mae` | `test_metric_edge_cases` | CORE_STATUS §4 |
| `experiments/runner.py` | `require_baselines`/`BaselineGateError`, optional `baseline_preds`/`access_log` on `run_neural`/`run_baselines`, opt-in `evidence.require_valid` in `write_manifest` | `test_governance_guards`, `test_access_log`, `test_evidence_governance` | CORE_STATUS §4 ("optional, not mandatory") |
| `api/service.py`, `api/server.py` | robust errors (generic 500), `panel.npz` key check, symlink containment, null spot, manifest/meta origin reconciliation + `origin_conflict` | `test_api` (+8), `test_api_contract`, `test_origin_label` | CORE_STATUS; **API contract doc (§8 of API_CONTRACTS) not updated for `origin_conflict` or the 500 body** (not in the diff) |
| `.github/workflows/tests.yml` | timeout, ruff correctness lint, `python -O` leakage step | none (never run) | header comment |
| `scripts/foundation_audit.py` | case-exact link check, bold-status parsing, status-claim check | none (script; no unit test) | CHANGELOG |
| Docs: README, CLAUDE.md, IMPLEMENTATION_PLAN, decision.md, guardrails.md, CORE_STATUS, MODEL_STATUS.json, KNOWN_LIMITATIONS, DEPLOYMENT, DATA_GOVERNANCE, PHASE0_FEASIBILITY_PLAN, CHANGELOG | status refresh + owner decisions of 2026-10-20 | n/a | see §3 for what was **not** refreshed |

New untracked source: `evaluation/access_log.py` (44 lines), `evaluation/evidence.py` (100 lines); 13 test files (109 test methods by static count) and `docs/data/DATA_ACQUISITION_AUTHORIZATION.md`. Observation: the **tests that cover the tracked source changes are untracked**, so committing only the modified tracked files would leave the repo with untested behaviour changes and (for `runner.py`) an import of an untracked module (`evaluation/evidence`), i.e. a broken checkout. The owner must commit source + new modules + tests together (owner-only action; not for any agent).

Diff content issues I could see (not fixed, routed): `ingest()` docstring says re-ingest with different origin is refused "by the manifest overwrite check", but the check compares the *entire* manifest text, including floating-point diagnostics (`reprice_err_max`, `vendor_iv_*`) that are platform/BLAS-dependent, so a Linux re-ingest of a Windows-written store can spuriously raise `OverwriteError`.

---

## 5. Duplication, dead code, inconsistent docs

**Duplication**
- Two parallel pipelines: stdlib spike (`phase0/{bsm,iv,quotes,surface,forecast}`, `chainpipe/`) and the NumPy/pandas package re-implement Black-76, IV, parity forward, quote filters, surface grid, ledgers. By design (ADR-0003 "disposable"), but there is no cross-check test asserting the two agree on the same chain.
- Notebook cell text (`scripts/_notebook_cells/*.py`, 1,628 lines) holds experiment logic (H1..H6 variants, plots, rule tables) that has no tests and is not imported by the package; the generator embeds the whole package in every notebook (~210 KB each, 10 notebooks in git).
- `surfaces/grid.py`: `build_day_surface` (test-only reference, 0 non-test callers) vs `build_day_surface_ex` (used).

**Dead / test-only code** (0 non-test references found by grep): `pricing.black76_greeks`, `evaluation.evidence.assert_all_labelled` (0 references anywhere), `experiments.runner.load_panel` (test only), `evaluation.evidence.check_verdict` / `compare_records` / `validated_problems` (used only by tests or docstrings; the governance module is not used by any pipeline except an opt-in `claim_level` branch in `write_manifest`).

**Boundary deviations from CLAUDE.md §4 / architecture.md §4:** `storage` imports `validation`/`surfaces` (producer-side logic inside the "store"); `experiments/runner.py` and `api/service.py` read/write the filesystem directly ("only `storage/` touches persistence"); API service computes a metric (`mae_observed_vol_points`). Two edges listed in `KNOWN_VIOLATIONS`.

**Doc drift:** see §3. In addition `docs/architecture/API_CONTRACTS.md` §8 gaps G1-G6 are proposals awaiting both sessions; none implemented. The `origin_conflict` field is in the payload but not in the contract table (not seen in the diff).

**Ignored evidence:** `experiments/phase0_synthetic/**` (hash-recorded Phase 0 evidence: A2/A3 JSONs, archive_v1, v2) and `scratch/**` are git-ignored; docs (`PHASE0_CLOSURE_RECORD.md:100` "Recorded hashes equal the files on disk") cite hashes of files that exist only on the owner's disk.

---

## 6. Actual causes of the listed blockers

Source: `docs/engineering/MODEL_STATUS.json:24-29` and `CORE_STATUS.md` §8-§9.

| Blocker | Class | Actual cause (as read) | Who can clear it |
|---|---|---|---|
| Phase 0 real-data feasibility blocked | **External-access (data licence) + owner decision** | no provider terms/price/permitted sample; Cboe inquiry drafted and unsent (`CORE_STATUS.md:102`, `DATA_ACQUISITION_AUTHORIZATION.md:37`); MVD M10 (licence) unmet; MVD thresholds only owner-adopted | owner (send inquiry / authorise a source); agent B can only research terms |
| Hosted dataset withdrawn | **Owner decision** (licence unverified upstream) | DEC-002 2026-10-20. Engineering residue: dataset id hard-coded in `config/settings.py:17` and in every notebook; E-1..H6 history unreproducible/unpublishable | owner; engineering follow-up = remove/relocate the default, regenerate notebooks (changes provenance: owner decision) |
| Phase 2 gate not met (A5 replacement rule pre-registration-only; DEC-006 option A) | **Engineering + process** | gate also needs Phase 1 exit (itself blocked by Phase 0); A1 tolerances written after E-1 (cannot be made retroactively true, L-28); A2 rejected quotes not stored per quote; the 2026-10-20 `reprice_err` closes only half | partly engineering (store rejected-quote records: schema change coordinated with API contract), partly unfixable by design (A1 timing) |
| Neural work needs verified GPU (local torch CPU build) | **Owner decision (CUDA install) / environment** | local PyTorch 2.13.0+cpu; DEC-015 allows Colab GPU, so this blocks only *local* neural runs. Colab/Kaggle runs are possible but need the data that is now withdrawn, so neural work is *de facto* blocked by the data blocker, not the GPU | owner |
| API gaps G1-G6 proposals | **Engineering coordination** (two sessions) | proposals in `API_CONTRACTS.md:95-100`; need UI-session review; G4 needs a panel-schema change | core + UI sessions |
| (not listed, but real) Colab execution | **Environment** | no test has executed anywhere but owner's PC; orchestrator owns Colab connection (AP-001) | orchestrator/owner |
| (not listed) Phase 6 "CI run" | **Owner action** | needs a push (owner-only); workflow unverified, unpinned installs, no manifest (DEC-015 open) | owner |
| (not listed) provenance gap | **Engineering** | no code/processing version in manifest or `version_id` (CLAUDE.md §8, SCI-013); notebooks carry code snapshots by text only | engineering |

---

## 7. Orchestration / subagent / CI / scripts / notebooks inventory

- **CI:** `.github/workflows/tests.yml` (one job: Ubuntu, Python 3.12, `pip install numpy pandas scipy pyarrow` unpinned, ruff `E9,F63,F7,F82`, backend unittest, `python -O` leakage test, spike unittest, foundation audit). **Never run.** No torch installed (neural tests stub or skip). No pinning, no cache, no matrix; no job for notebooks or frontend.
- **Pre-commit / hooks:** none tracked. `.claude/` not tracked (`.gitignore:136-137`).
- **Orchestration:** `orchestration/` (new, untracked, orchestrator-owned): MASTER_PLAN, SHARED_STATUS, AGENT_REGISTRY, APPROVALS, DECISIONS, INTEGRATION_QUEUE, `contracts/S0-S7.md`, `prompts/A-F + _COMMON`, `colab_transfer/` (tarball + SHA-256 manifest of the working tree, 1.16 MB), `reports/` (empty before this file). No `AGENTS.md`.
- **Scripts:** `foundation_audit.py` (executes `git`), `build_colab_notebook.py` (needs `nbformat`: undeclared dependency), `make_synthetic_run.py`, `phase2_surface_comparison.py` (writes new file only), spike `phase0/run.py` etc. (default output dir under git-ignored `experiments/`).
- **Notebooks:** 9 generated (`Colab`, `E2`, `H1`, `H1b`, `H2`, `H3`, `H4`, `H5`, `H6`; ~207-220 KB each) + `exploratory/Neural_Volatility_Surface_Colab.ipynb`. Never executed in a reproducible way in-repo; `notebooks/README.md` says "never cited as evidence" while CORE_STATUS/README cite their off-machine runs.
- **Empty/placeholder dirs:** `backend/tests/integration`, `backend/tests/fixtures`, `tests/{end_to_end,fixtures,regression}`, `data/*`, `configs/*`, `domain/`, `observability/`, `artifacts/`.
- **Dependency manifest:** none (DEC-015 open); versions only in prose. Local stack numpy 1.26.2 / pandas 2.1.3 / scipy 1.14.1 / pyarrow 17 / torch 2.13.0+cpu; "clean venv" numpy 2.5.4 / pandas 3.0.6 / scipy 1.18.1 / pyarrow 26.0.0 (as claimed, not verified by me).

---

## 8. Claims that lack executable evidence in a clean environment

| # | Claim (where) | Why not evidenced | What would count |
|---|---|---|---|
| 1 | backend suite "252 tests OK, 1 skipped" (`CORE_STATUS.md:157`, `MODEL_STATUS.json:19`, workflow header) | only owner-PC transcription; count ambiguity (§0.1) | Colab/Linux `unittest discover` log with the Ran/OK/skipped line |
| 2 | "clean venv of latest unpinned packages passed" (`CORE_STATUS.md:158`) | local Windows venv, not a runner; versions unverifiable by me | Colab fresh runtime with a recorded `pip freeze` |
| 3 | spike "145 tests OK" (`README.md`, `scripts/README.md`) | same | Colab run |
| 4 | foundation audit "exit 0, 734 links, 0 broken" | local; case-exact check is new; depends on untracked files existing (`DATA_ACQUISITION_AUTHORIZATION.md`, new tests) | audit run on a clean export of the intended commit |
| 5 | CI green | CI never run | a runner log (owner push) |
| 6 | `python -O` leakage tests (9 OK) | local | Colab |
| 7 | ruff correctness lint clean | local; ruff version unrecorded | Colab |
| 8 | Phase 2 comparison JSON hash `ac8c57bd...` reproducible twice | same machine only; cross-platform float reproducibility unknown | Colab twice + compare to recorded hash |
| 9 | GPU test / `run_neural` end to end | skipped locally (CPU torch) | Colab T4 (requires data or synthetic plumbing mode, which exists) |
| 10 | E-1/E-2/H1-H6 numbers (skill +0.0351, +0.0479, ...) | no outputs in notebooks, no run dir, transcribed, owner waived | not reproducible without the withdrawn dataset; at most `synthetic_plumbing` mode checks the pipeline runs |
| 11 | "every 2026-10-20 hardening effect on real data" (L-31) | never measured | needs an authorized real sample |
| 12 | Phase 0 evidence hashes (`PHASE0_CLOSURE_RECORD.md:100`) | files git-ignored, exist only on owner disk | files committed or re-derived in Colab |
| 13 | viewer behaviour (UA-01..14, accessibility) | never run; only static string tests | browser journeys (agent E) |
| 14 | notebooks "static checks (schema, syntax, undefined names)" only | no test of cell code; generator untested | Colab `synthetic_plumbing` run of one notebook |
| 15 | neural `train_and_predict` correctness (seeding, masked loss, early stopping) | no CPU test executes it | small CUDA test in Colab |
| 16 | Cross-implementation agreement (spike vs package IV / surfaces) | no such test | a Colab comparison on one synthetic chain |

---

## 9. Proposed (for the orchestrator; nothing applied)

1. Add to V-1 (Colab) in this order: backend suite, spike suite, `python -O` leakage test, foundation audit on the *transferred* tree, then one notebook in `synthetic_plumbing` mode on a T4 (covers #1-3, 6, 9, 14, 15). Record the Ran/OK/skipped lines and `pip freeze`.
2. Ask the owner to commit source + new modules + tests together (owner-only); otherwise `runner.py` imports an untracked module.
3. Fix the `ingest` re-ingest hazard by design, not workaround: put a processing/code version in the manifest and `version_id`, and exclude platform-dependent float diagnostics from the byte-for-byte comparison (agent C proposal; touches stored-data semantics, so owner-visible).
4. One status reconciliation pass over the 20 contradictions in §3.2 after Colab results arrive (rows 1-4, 7-13 are pure doc edits; rows 5, 6, 14 need an owner ruling on "display" of withdrawn-data results).
5. Decide the notebook policy: regenerate with the hardened source and a non-Kaggle default (owner: provenance change) or mark every notebook "historical snapshot, do not run".

## 10. Blocked
- Executable verification of anything: **BLOCKED — COLAB NOT CONNECTED** (SHARED_STATUS) and prohibited locally.

## 11. Not run
Everything executable: no `python`, `pytest`, `unittest`, scripts, notebooks, linters, `foundation_audit.py`. No network, no data access.

## 12. Failed
Nothing failed. Disclosure: my first hand-sum of the per-file test counts was wrong (232/272); corrected in §2.2 to 212 + 40 = 252. Also: I did not read `models/neural.py`, `models/baselines.py`, `features/panel.py`, `surfaces/grid.py` or `evaluation/compare.py`/`decision_rule.py` line by line; findings on those modules come from their definitions, callers, imports and tests only.

## 13. Could not be inspected
- Contents of `orchestration/colab_transfer/worktree_2026-10-20.tar.gz` (binary; only existence/size checked).
- Kaggle/Colab runtimes, the withdrawn dataset, real-file schema behaviour, any output of H1-H6.
- `dashboard-design/*` and the UI session's own verification claims (agent E's scope); `docs/**` beyond the files cited (65 `.md` under `docs/`, 126 in repo excluding `scratch/`).
- CRLF/LF: `git diff` warns that 20 files will be converted LF->CRLF "next time Git touches it" (autocrlf in effect on the owner's PC); I could not assess whether this affects byte-compared tests on Linux.

## 14. Routed to others
- **B (data/governance):** rows 5, 6, 14 of §3.2 (what "not authorized for display" means for README/CLAUDE.md/CORE_STATUS prose quoting H5/H6 figures); hard-coded dataset id in `config/settings.py:17` and notebooks vs DEC-002; `DATA_ACQUISITION_AUTHORIZATION.md` is untracked.
- **C (engineering):** re-ingest/`version_id` provenance hazard (§0.5, §4); platform-dependent floats in the manifest text comparison; untested neural training path; untested notebook generator/cells; opt-in guards (`require_baselines`, `access_log`, `evidence`) not wired into any pipeline; `storage`/`runner`/`api` persistence boundary; `api/service.py` has no Host-header check; `origin_conflict` and generic-500 body missing from `API_CONTRACTS.md` §8; `foundation_audit.py` status-claim check is a weak regex.
- **D (quant):** pre-registration is documentary only; H5 compared against H3 (+0.0436) in README but H4 (+0.0407) in CORE_STATUS; GR-MOD-01 not binding for any executed run; A1 tolerance timing (L-28).
- **E (UI):** 3D view exists despite DEC-008 "no 3D" and `frontend/README.md` claims it (§3.2 rows 7-8, 19); "Live from run" wording (L-33); `frontend/README.md:5` stale "DEC-008 still open".
- **F (reviewer):** please spot-check the §3.2 rows and the §0.2 snapshot claim (`grep` the notebooks for `LeakageError`), and the re-ingest hazard reading of `raw_store.py` (§0.5), since I could not execute to confirm it.

## 15. Files changed
- `orchestration/reports/REPO_AUDIT.md` (this file; only file written). No product file, no other report, no Git state touched.

## 16. Handoff
**May rely on:** the module map and sizes (§2.1); the verified facts in §1 (HEAD, dirty-tree counts, no manifest/lockfile, notebooks hold pre-hardening source and no outputs, hosted dataset id still hard-coded, `experiments/**` and `scratch/**` ignored); the classification in §2.3; the contradiction list in §3 (each cites file:line); the claims-without-evidence table in §8 as the V-1 (Colab) work list; blocker classification in §6.
**May not rely on:** any pass/fail or test count (nothing was executed; counts are static or owner transcriptions); the H1-H6 figures; CI behaviour; that `IMPLEMENTATION_PLAN`/README/CORE_STATUS agree with each other or with the code today; my reading of the re-ingest hazard and of `models/*` behaviour (static reading only).
