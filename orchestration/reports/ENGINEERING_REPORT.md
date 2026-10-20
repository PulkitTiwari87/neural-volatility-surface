# ENGINEERING_REPORT — Agent C (Engineering and Numerical Correctness), Wave 1, stage S1/S3

**Status:** READY_FOR_REVIEW

**Revision/manifest:** git HEAD `306c01b` (branch `main`); working tree has 45 paths in `git status --short` (44 owner paths + untracked `orchestration/`), all read **as they are on disk**, so line numbers below refer to the uncommitted working tree, not to HEAD. All 255 entries of `orchestration/colab_transfer/MANIFEST.sha256` still match the working tree (checked with `sha256sum -c`: 255 OK, 0 mismatch; tarball `worktree_2026-10-20.tar.gz` sha256 `0d5835e2…d4cb71`, manifest file sha256 `82a8de14…2bfd`). The transfer set contains **no `.git`, no `orchestration/`, no `scratch/`** (see C-09, Colab plan).

**Scope honoured:** static reading only. No project code, test, script, linter or interpreter was run. No file other than this report was written. Every finding is therefore **Observed (static only)** unless it cites an executed result, and executed results cited from `docs/engineering/CORE_STATUS.md` are the owner session's *local-PC* runs (not re-run, not Colab).

---

## 1. Headline

No **S1** (silent wrong science / leakage / data loss) defect was found by static reading. The walk-forward purge arithmetic, train-only fitting (fill values, scalers, PCA basis, ridge penalty, regime cut-offs), the strict-ISO date handling, calendar-days/365 usage and the reject-ledger conservation all read as correct. The material defects are about **reproducibility and provenance honesty** (resume cache, platform-dependent dtypes in the hashed panel, float drift in a byte-compared manifest, a self-reported test-access log), plus a handful of API/robustness edges.

| ID | Sev | One line |
|---|---|---|
| C-01 | S2 | `run_neural` resume reuses saved predictions keyed only by (fold, model, seed); experiment flags are not in the config hash, so a different experiment in the same `out_dir` is silently reused; PCA-factor deltas are saved without their basis (SVD sign is not canonical) |
| C-02 | S2 | `build_surface_panel` leaves `n_quotes`/`tenor_days` at the platform default integer: int32 on Windows+NumPy 1.x (the owner's PC), int64 on Linux/NumPy 2 (Colab). `panel_sha256` hashes `dtype.str`, so the same data hashes differently across the two environments |
| C-03 | S3 | Even with identical dtypes, `panel_sha256` and the manifest text (incl. `reprice_err_max`, a rounding-noise number) are byte-compared; ULP-level libm/BLAS/pandas differences make `ingest` refuse a re-ingest on another machine (`OverwriteError`) |
| C-04 | S3 | Raw-store `put` is not atomic and does not re-hash the copy; `ingest` `mkdir` has no `exist_ok`: a crash (Colab disconnect) leaves a store that can never be repaired by re-running |
| C-05 | S3 | API table endpoint: a CSV cell `nan`/`inf` makes `_num` return a non-finite float, `json.dumps(allow_nan=False)` raises, the whole table returns a generic 500 |
| C-06 | S3 | `AccessLog` events are written by the caller *before* the work; `test_accessed_count == 0` is true by construction and cannot support the `validated` gate it feeds |
| C-07 | S3 | `combine_labels` maps "not evaluable" (`None`) under one label to "holds under the other label only"/"no_improvement_shown" |
| C-08 | S3 | Forward/discount-factor estimation: DF=1 fallback for T>=30d slices without a usable regression; very loose F/S and DF bounds; no outlier handling |
| C-09 | S3 | `foundation_audit.py` ignores `git` failures, so the tracked-data/env checks pass vacuously in any tree without `.git` (the Colab transfer set) |
| C-10 | S3 | Row-gap protection exists only for the target (`gap_ok`); lag features, sequence windows and realised vol are in panel rows; dates with no surface are dropped without any ledger entry |
| C-11 | S4 | API: HEAD/OPTIONS return 501 (contract: "every other method -> 405"); no Host-header check (DNS rebinding); whole-file CSV read; negative origin index not rejected |
| C-12 | S4 | `validated_problems`: `test_accessed_count: False` passes as 0 |
| C-13 | S4 | Selection loops/early stopping crash with an opaque `TypeError` when validation is not evaluable |
| C-14 | S4 | Conflicting-duplicate rule runs after the prefilter: a duplicate that the prefilter already rejected is never seen as a conflict |
| C-15 | S4 | Minor numerics/config: uncentred parity normal equations, butterfly curvature not normalised by node spacing, absolute-USD `min_mid`, `min_quotes_per_slice` can be set to 1, `.PARQUET` suffix case |
| C-16 | S4 | Manifest `default=str`, `verify_manifest` ignores unlisted files; GPU determinism is `cudnn.deterministic` only |

Import-direction assessment and the Colab plan are in sections 5 and 6; change manifest in section 8.

---

## 2. Verified

Nothing executed by this agent. Facts established by direct file reading / system utilities that do not execute project logic:

- HEAD `306c01b`; `git status --short` = 45 paths; the 255-file Colab transfer manifest matches the on-disk tree (above).
- Day-count: every use is calendar days / 365.0 (`validation/quotes.py:50,79`, `surfaces/grid.py:74-75`, `surfaces/diagnostics.py:13,22`, `datasets/synthetic.py:44`, `surfaces/compare_methods.py:170`, `config/settings.py:33`); no other day-count constant exists in `backend/src`. The only `sqrt(252)` is realised vol annualisation over panel rows (`features/panel.py:66`). Dates are integer epoch days (`ingestion/optionsdx.py:129-147`), so time-of-day and timezone cannot enter T. Same-day/1-day expiry is excluded by `DataConfig.min_dte = 2` (`config/settings.py:19`), and if `min_dte` were lowered, T<=0 is `INVALID_INPUT` in the solver (`pricing/bs.py:84`), not NaN.
- Import graph: both known violations are single, acyclic edges (section 5).

## 3. Observed (static only) — findings, with evidence, proposed diffs and the test that would prove each

Diffs are unified, **proposals only**, against the working tree as read. Hunk headers are approximate (`@@`); context is trimmed to the changed lines. Each change needs a CHANGELOG entry and, where noted, a KNOWN_LIMITATIONS line (core session owns those files).

### C-01 (S2) `run_neural` resume cache is not tied to the run that produced it

**Evidence.** `experiments/runner.py:172-185`: resume condition is only `pf.exists() and ck.exists() and hf.exists()` with `tag = f"fold{test_year}_{kind}_seed{seed}"`; nothing else identifies the producer. The notebooks claim "the run id encodes both [config and dataset bytes]" (`scripts/_notebook_cells/cells.py:630`), but `RUN_ID = mode + cfg.sha256()[:8] + data_hash[:8]` (`cells.py:178`) and `Config.sha256()` does **not** contain experiment flags: target label, calendar block, `mr_window`, `pca_factors`, validation mode (CORE_STATUS section 6 item 5 itself records "the config hash is the same for H2/H3/H4"). So two different experiments run against the same dataset resolve to the same `OUT_DIR`; if that directory persists (`USE_DRIVE = True`, `cells.py:50`, or a Colab runtime that is simply reused), the second experiment silently loads the first one's `delta` arrays whenever shapes agree (cell-level H3/H6; nearest vs fixed label in a non-E-2 notebook). Shape mismatch (H5 factor-space `(N,3)` vs cell-space `(N,C)`) fails loudly, but H3 vs H6 or label changes do not.
Second defect on the same path: for `pca_factors`, `delta` is stored in factor space and reconstructed as `delta @ V` (`runner.py:185`) with `V` recomputed on resume from `np.linalg.svd` (`runner.py:107`). SVD singular-vector signs are not canonical across LAPACK builds/CPUs, so a resume on a different runtime can flip the sign of a row of `V` and silently flip the corresponding forecast component.
Whether any executed H-series run was affected cannot be determined from the repo (USE_DRIVE default is False; H1-H6 outputs are not saved, L-29). **Recommend the owner confirm whether any H3-H6 run reused a persisted `OUT_DIR`.**

**Proposed diff** (`backend/src/volatility_lab/experiments/runner.py`; new helpers before `run_neural`, one call inside it, one line in `pca_factor_targets`):

```diff
--- a/backend/src/volatility_lab/experiments/runner.py
+++ b/backend/src/volatility_lab/experiments/runner.py
@@ def pca_factor_targets(s_all, D, M_, train, k):
     mean_s = s_all[train].mean(axis=0)
     V = np.linalg.svd(s_all[train] - mean_s, full_matrices=False)[2][:k]
+    V = V * np.where(V[np.arange(V.shape[0]), np.abs(V).argmax(axis=1)] < 0, -1.0, 1.0)[:, None]  # canonical sign: resume-safe
     return np.where(M_, D, 0.0) @ V.T, np.ones((D.shape[0], k), dtype=bool), V
@@ before def run_neural
+def run_key(p: Prepared, folds: List[Fold], cfg: Config, pca_factors=None) -> dict:
+    """What makes saved (fold, model, seed) predictions reusable. Experiment flags are NOT part of ``cfg.sha256()``."""
+    struct = hashlib.sha256(p.dates.tobytes() + p.status.tobytes()).hexdigest()   # exact ints only: env-stable
+    return {"config_sha256": cfg.sha256(), "target": p.target_name, "calendar": p.calendar is not None,
+            "mr_window": p.mr_window, "pca_factors": pca_factors, "horizon": p.horizon,
+            "panel_structure_sha256": struct,
+            "folds": [[f.test_year, len(f.train), len(f.val), len(f.test), f.train_rows_end] for f in folds]}
+
+
+def _claim_out_dir(out_dir: Path, key: dict) -> None:
+    kf = out_dir / "run_key.json"
+    if kf.exists():
+        if json.loads(kf.read_text()) != key:
+            raise RuntimeError(f"{out_dir} holds predictions of a different run (config, label, features or folds); use a new out_dir")
+    elif any((out_dir / "predictions").glob("*.npy")):
+        raise RuntimeError(f"{out_dir} has predictions but no run_key.json (older version); use a new out_dir")
+    else:
+        kf.write_text(json.dumps(key, sort_keys=True, indent=1))
+
+
@@ def run_neural, after the three mkdir calls
+    _claim_out_dir(out_dir, run_key(p, folds, cfg, pca_factors))
```

**Test that proves it** (new file `backend/tests/unit/test_run_key.py`, CPU only, no GPU needed because it exercises the helpers): same `(p, folds, cfg)` twice -> same key and `_claim_out_dir` accepts; `prepare(panel, cfg.features, target="fixed_expiry")` / `calendar=True` / `mr_window=5` / `pca_factors=3` / different `cfg.train.seeds`... -> key differs and `_claim_out_dir` raises `RuntimeError`; a dir with a stray `predictions/x.npy` and no key raises; `pca_factor_targets` returns `V` whose largest-|.| entry per row is positive and is unchanged if the training matrix is negated through an SVD (sign canonicalisation).
*Note:* the new `run_key.json` becomes part of `write_manifest`'s file list (harmless). Existing Colab/Kaggle output directories become "legacy" and must not be resumed (by design).

### C-02 (S2) Platform-dependent integer dtypes enter the content hash

**Evidence.** `surfaces/grid.py:123` `"n_quotes": np.asarray(nq)` (list of Python ints) and `grid.py:127` `"tenor_days": np.asarray(cfg.tenor_days)` (tuple of ints) take NumPy's default integer: **int32 on Windows with NumPy 1.x** (the owner's PC: NumPy 1.26.2) and **int64 on Linux and on NumPy >= 2** (Colab, and the PC's second venv with 2.5.4 — whose sha is therefore not comparable to the first). `storage/raw_store.py:46-49` hashes `a.dtype.str` (`<i4` vs `<i8`) and bytes, and the value goes into the manifest (`raw_store.py:113`) which is byte-compared on re-ingest (`raw_store.py:124-126`) and re-checked by the API (`api/service.py:140-146`, `panel_hash_matches`). Consequence: the same synthetic input yields different `panel_sha256` on PC (numpy 1.x) vs Colab; a dataset stored on one and re-ingested or verified on the other is refused or reported as hash mismatch; any "rebuild gives identical content hash" evidence (S3 acceptance criterion) is only valid inside one environment. CORE_STATUS records both NumPy stacks passing the suite, but every reproducibility test compares two runs inside one process (`tests/unit/test_reproducibility.py:21-34`, `test_storage.py:33-40`), so this was invisible.

**Proposed diff** (`backend/src/volatility_lab/surfaces/grid.py`; every other panel array already has an explicit dtype):

```diff
--- a/backend/src/volatility_lab/surfaces/grid.py
+++ b/backend/src/volatility_lab/surfaces/grid.py
@@ -123 @@ def build_surface_panel
-    return {"dates": np.asarray(dates, dtype=np.int64), "spot": np.asarray(spots), "n_quotes": np.asarray(nq),
+    return {"dates": np.asarray(dates, dtype=np.int64), "spot": np.asarray(spots, dtype=np.float64),
+            "n_quotes": np.asarray(nq, dtype=np.int64),
@@ -127 @@
-            "tenor_days": np.asarray(cfg.tenor_days), "k_nodes": np.asarray(cfg.k_nodes)}
+            "tenor_days": np.asarray(cfg.tenor_days, dtype=np.int64), "k_nodes": np.asarray(cfg.k_nodes, dtype=np.float64)}
```

**Test** (new `backend/tests/unit/test_panel_dtype_stability.py`): assert `panel[k].dtype.str` equals an explicit table (`dates, n_quotes, tenor_days, slice_row, slice_expiry, anchor_expiry` `<i8`; `status` `|i1`; `iv, spot, k_nodes, slice_iv, slice_gap, gap_tight` `<f8`). It fails before the fix **only on Windows + NumPy<2**; on Colab it is a regression guard. Side effect: panels/datasets already stored on the PC under NumPy 1.x will report `panel_hash_matches == false` (synthetic only; regenerate). No downstream consumer depends on int32 (all uses are `astype(float)`, `np.repeat`, `.tolist()`).

### C-03 (S3) Float drift across environments is byte-compared

**Evidence.** Hashing/comparison uses raw float bytes: `raw_store.py:43-50` (`panel_sha256`), `raw_store.py:121-126` (`mf.read_text() != text`), and the manifest text includes `quote_diagnostics` (`raw_store.py:113`) — `reprice_err_max/median` (`validation/quotes.py:143-144`) are the solver's rounding residual (~1e-16 of F), i.e. the *least* reproducible numbers in the pipeline, plus `vendor_iv_median_*` (`quotes.py:149-150`). NumPy's `log/exp` dispatch to different SIMD kernels per CPU, pandas `groupby.sum/median` implementations differ across 2.1/3.0, BLAS threading changes reduction order. Result: bit-identical inputs can give different `panel_sha256`/manifest text on different machines/versions, and `ingest` then raises `OverwriteError` ("a correction needs a new version") for what is not a correction. The same-machine claim (CORE_STATUS section 9, Phase 2 A3 MET-L) is fine; a cross-machine claim is unsupported.

**Proposed (no diff yet — design choice for the owner):** keep `panel_sha256` as the exact same-environment check, add a second `panel_structure_sha256` over integer/status/shape arrays plus floats rounded to 1e-6 (per-element straddle probability ~1e-10, expected failures over 1e6 cells ~1e-4; rounding at 1e-10 would *not* be safe, expected ~1 straddle), and make the re-ingest equality check compare the manifest with the volatile diagnostics removed. This changes the `dataset-1` manifest schema, so it is routed (section 7) rather than diffed. **Probe** V-C1/V-C6 in the Colab plan measures the actual drift (same code, numpy 1.26 vs numpy 2.x, same Linux host).

### C-04 (S3) Raw store / dataset write is not crash-safe

**Evidence.** `raw_store.py:66-67` `shutil.copyfile(path, dest)` writes straight to the hash-named destination: an interrupted copy leaves a truncated file whose name claims a hash; every later `put` takes the `dest.exists()` branch, re-hashes, and raises `OverwriteError` forever (`raw_store.py:62-64`). The file could also change between `sha256_file(path)` (`:60`) and the copy, producing an object whose bytes do not match its name. `raw_store.py:132` `out.mkdir(parents=True)` (no `exist_ok`) raises `FileExistsError` for a dataset directory left by an interrupted ingest (manifest is written last, `:135`, so such a directory has no manifest). Both are realistic on Colab (runtime disconnect mid-ingest).

**Proposed diff** (`backend/src/volatility_lab/storage/raw_store.py`):

```diff
--- a/backend/src/volatility_lab/storage/raw_store.py
+++ b/backend/src/volatility_lab/storage/raw_store.py
@@ imports
 import json
+import os
 import shutil
@@ RawStore.put
             dest.parent.mkdir(parents=True, exist_ok=True)
-            shutil.copyfile(path, dest)
+            part = dest.with_name(dest.name + ".part")
+            shutil.copyfile(path, part)
+            if sha256_file(part) != digest:                      # the source changed between hashing and copying
+                part.unlink()
+                raise OverwriteError(f"{path.name} changed while it was being stored")
+            os.replace(part, dest)                               # atomic: a half-written object never has a hash name
@@ ingest
-    out.mkdir(parents=True)
+    out.mkdir(parents=True, exist_ok=True)   # manifest.json is written last; a directory without it is an interrupted ingest
```
**Test** (new `backend/tests/unit/test_store_atomicity.py`): (1) pre-create `datasets/<version_id>/` empty, `ingest` succeeds and a second `ingest` reports `reused`; (2) patch `shutil.copyfile` to write half the bytes then raise -> `dest` does not exist, a retry with the real copy succeeds, `verify()` reports only the leftover `.part` (stem mismatch); (3) mutate the source between hash and copy (patched `copyfile` appends a byte) -> `OverwriteError`.

### C-05 (S3) API table endpoint: `nan`/`inf` cell -> whole table returns 500

**Evidence.** `api/service.py:53-58` `_num` returns `float(s)`; `float("nan")`, `float("inf")`, `float("1e999")` succeed. `api/server.py:35` serialises with `allow_nan=False`, which raises `ValueError`; `server.py:60-63` converts it to the generic 500 "the run data could not be read". Contract (`API_CONTRACTS.md` section 8) says numeric cells are parsed and JSON is strict; neither says a single `inf` (e.g. an MSE-skill ratio with a zero denominator written by pandas as `inf`) may take the table down. `test_api.py:38` covers only empty cells; `test_api_contract.py:108` checks the JSON of one fixture.

```diff
--- a/backend/src/volatility_lab/api/service.py
+++ b/backend/src/volatility_lab/api/service.py
@@ imports
 import json
+import math
 import re
@@ def _num(s: str):
     try:
-        return float(s)
+        x = float(s)
     except ValueError:
         return s
+    return x if math.isfinite(x) else s     # "nan"/"inf" cells stay text: JSON has no NaN/Infinity
```
**Test** (extend `test_api_contract.py` or new `test_api_edge_inputs.py`): table CSV with cells `nan, inf, -inf, Infinity, 1e999, 7` -> HTTP 200, those cells returned as strings (except `7` -> 7.0), no 500.

### C-06 (S3) The test-window access log cannot show what it is used to show

**Evidence.** `experiments/runner.py:83-88` records `("fit","train")`, `("select","val")`, `("predict","test")` once per fold, *before* any fitting happens, from constants the caller chose; nothing wraps the arrays or the model code, and nothing ever calls `record("select"|"fit", "test", ...)` (the guard in `evaluation/access_log.py:27-30` therefore never fires in any real path). So `test_accessed_for_selection` is 0 by construction, even if a future change fitted on test rows. The module says as much ("audit trail, not a security boundary", `access_log.py:6-8`; CORE_STATUS section 4 GR-LEAK-05 gap), but `evaluation/evidence.py:62` makes `test_accessed_count == 0` a *requirement for the `validated` claim*, which lends it evidential weight it does not have. The `predict/test` event is also logged before the predictions exist (a failed fold is still logged as predicted). The real protection is `assert_no_overlap` (`walkforward.py:71-81`) plus the sentinel tests (`tests/scientific/test_leakage_sentinels.py`), both of which read correct.

**Proposal (small, no code):** treat `test_accessed_count` as a declaration in docs/evidence rules (say so in `evidence.py` docstring and KNOWN_LIMITATIONS), and if an enforceable number is wanted, record in each event the data it was *derived from*: `max(odate[fold.train])`, `max(tdate[fold.train])`, `min(odate[fold.test])` from the arrays `assert_no_overlap` already computes. Routed to D/F for the evidence-process decision (section 7).

### C-07 (S3) "Not evaluable" collapses into "holds under the other label only"

**Evidence.** `evaluation/decision_rule.py:73-84`: `nearest.label_pass is True and fixed.label_pass is None` -> `holds_under_nearest_expiry_label_only`; `False`/`None` -> `no_improvement_shown`. In `improvement_rule` a `None` arises when criterion b or d is not evaluable (`decision_rule.py:66-67`). The vocabulary in `evidence.py:20-21` has no value for "passes under one label, unevaluated under the other"; the tests (`test_decision_rule.py:70-77`) encode only `(N,T)` and `(N,N)` and do not cover `(T,N)`/`(F,N)`. The pre-registered rule is owner-approved, so no code change is proposed; the ambiguity should be recorded. **Routed (D, owner).**

### C-08 (S3) Parity-forward / discount-factor estimation: fallbacks and bounds

**Evidence.** `validation/quotes.py:59-66`: regression is used only if `n >= 5`, `T >= 30/365`, `den > 0` and `DF in [0.90, 1.01]` (`settings.py:34`); otherwise **`DF = 1`** and `F = median(C - P + K)` which equals `DF*F + K(1-DF)`, not `F`. For a slice with `T >= 30d` that has 3-4 usable pairs (`min_parity_pairs = 3`, `settings.py:31`) the whole slice is priced undiscounted: at 5 % rates and 1y that is a ~5 % price scale error (≈1 vol point at 20 % vol) for every quote of the slice, with `regression=False` recorded only as a count (`quotes.py:138`). The plausibility check `forward_ratio_bounds = (0.85, 1.15)` (`settings.py:35`) cannot catch a mis-estimated forward at short T (true F/S is within ±1 % for T<=30d). DF is weakly identified for short T (slope of C-P vs K over ±6 % strikes) yet accepted anywhere in [0.90, 1.01]. OLS is unweighted over mid prices of pairs that only need `bid>0, ask>bid` (`quotes.py:36-37`), so a single wide/stale pair biases F and DF. The normal equations are uncentred (`quotes.py:53-55`): fine at SPY scale (~3 digits lost of 16) but a nit. American-exercise bias is documented (L-23).
**Proposal:** no code change without owner approval (changes the dataset). Route to D: add a per-slice diagnostic of `|F/S-1|` vs T and of DF vs a rate prior, report the share of `T>=30d` slices on the DF=1 fallback, then decide tighter T-scaled bounds. Not proposed as a diff.

### C-09 (S3) Foundation audit passes vacuously without Git

**Evidence.** `scripts/foundation_audit.py:129-130` `git()` returns `stdout.splitlines()` and ignores the return code; `check_data_and_env` (`:133-136`) therefore reports `tracked_data_files: []` and `tracked_env_files: []` when `git` fails ("not a git repository", "dubious ownership", git absent). The Colab transfer set has no `.git` (255 files, 0 under `.git/`), so the audit's "no data tracked / no `.env` tracked" checks will report clean without evaluating anything. Proposed diff (`scripts/foundation_audit.py`):

```diff
--- a/scripts/foundation_audit.py
+++ b/scripts/foundation_audit.py
@@ def git(*args)
-    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.splitlines()
+    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
+    if r.returncode != 0:
+        raise RuntimeError(f"git {' '.join(args)} failed ({r.returncode}): {r.stderr.strip()[:200]}")
+    return r.stdout.splitlines()
@@ def check_data_and_env()
-    tracked_data = [f for f in git("ls-files", "data", "artifacts") if Path(f).name not in {"README.md", ".gitkeep"}]
+    try:
+        tracked_data = [f for f in git("ls-files", "data", "artifacts") if Path(f).name not in {"README.md", ".gitkeep"}]
+        tracked_env = [f for f in git("ls-files") if re.search(r"(^|/)\.env($|\.)", f) and not f.endswith(".example")]
+    except (RuntimeError, OSError) as e:
+        return {"git_available": False, "not_evaluated": str(e), "tracked_data_files": [], "tracked_env_files": [],
+                "gitignore_covers_env": ".env" in ((ROOT / ".gitignore").read_text() if (ROOT / ".gitignore").is_file() else "")}
```
(and use `tracked_env` in the existing return dict, with `"git_available": True`). **Test:** a unit test is awkward for a script; verification is the Colab probe P3 (`git -C … ls-files` fails; audit JSON must now say `git_available: false`). Until applied, the Colab executor must record the two checks as **NOT EVALUATED**.

### C-10 (S3) Row gaps are guarded for the target only; dropped dates are silent

**Evidence.** `features/panel.py:142` rejects origins whose *target* is more than `h+4` calendar days away, but lag features (`panel.py:190-193`, lag = 5 rows), the 20-row sequence window (`:206-207`), `trailing_mean` (`:182-184`), `causal_fill`'s `ffill_days` (rows, `:167-179`) and realised vol (`:63-66`, annualised with sqrt(252) per row) all count *rows*. If `build_surface_panel` skips dates (`grid.py:110-111`: a date with no valid cell is dropped, and the drop is neither counted nor ledgered), "5 rows" can span weeks and "1 day" realised vol is a multi-day move. `runner.data_audit` reports `max_calendar_gap_days` (`runner.py:67`), so the gap is visible after the fact, but no test asserts the feature code is gap-aware. Not wrong for a gap-free calendar; wrong in exactly the degraded-data case. **Proposal:** (a) count/ledger skipped dates in `build_surface_panel` (return `skipped_dates` in diagnostics, not in the hashed panel); (b) extend the `gap_ok` rule to the longest lag and the sequence window. Behaviour change for features -> routed to D with a leakage test (`tests/unit/test_feature_leakage_variants.py` pattern).

### C-11 (S4) API transport/input edges

- **HEAD/OPTIONS -> 501.** `server.py:77-83` defines `do_GET` and `do_POST/PUT/DELETE/PATCH = _refuse` only; `BaseHTTPRequestHandler` answers other verbs with 501 and an HTML body. `API_CONTRACTS.md` section 8 (line 69) says every other method -> 405; `test_api.py:176-179` tests POST only.
- **No Host-header validation.** The bind is loopback (`server.py:91-94`), but a browser page on an attacker domain can use DNS rebinding to read `/api/runs/...` (read-only, but it may hold licensed data once real runs exist).
- **`table()` reads the whole CSV** before truncating to 5,000 rows (`service.py:218-219`); **`forecast()`** rejects `org >= tgt` but not a negative origin index (`service.py:188`), which would index `dates` from the end.

```diff
--- a/backend/src/volatility_lab/api/server.py
+++ b/backend/src/volatility_lab/api/server.py
@@ make_handler
         def do_GET(self):  # noqa: N802
+            if not self._host_ok():
+                return self._send(*_json(400, {"error": "unexpected Host header"}), {})
             self._send(*dispatch(store, self.path, frontend), {})
 
+        def _host_ok(self) -> bool:      # DNS-rebinding guard: only a loopback name may address this server
+            host = (self.headers.get("Host") or "").strip()
+            if host.startswith("[") and "]" in host:
+                host = host[1:host.index("]")]
+            elif host.count(":") == 1:
+                host = host.rsplit(":", 1)[0]
+            return host == "" or host in LOOPBACK
+
         def _refuse(self):
             self._send(*_json(405, {"error": "read-only API"}), {"Allow": "GET"})
 
-        do_POST = do_PUT = do_DELETE = do_PATCH = _refuse  # noqa: N815
+        do_POST = do_PUT = do_DELETE = do_PATCH = do_HEAD = do_OPTIONS = _refuse  # noqa: N815
```
**Test** (in the new `test_api_edge_inputs.py`, real socket as in `test_api.py:161-182`): HEAD and OPTIONS -> 405 with `Allow: GET`; `GET` with `Host: evil.example` (via `http.client`) -> 400; `Host: 127.0.0.1:<port>` and `localhost` -> 200.

### C-12 (S4) `validated_problems` accepts `False` for the access count
`evaluation/evidence.py:62` `rec.get("test_accessed_count") != 0` — `False != 0` is False, so `test_accessed_count: False` passes. Diff:
```diff
--- a/backend/src/volatility_lab/evaluation/evidence.py
+++ b/backend/src/volatility_lab/evaluation/evidence.py
-    if rec.get("test_accessed_count") != 0:
+    tac = rec.get("test_accessed_count")
+    if isinstance(tac, bool) or tac != 0:
```
Test: `validated_problems({..., "test_accessed_count": False})` contains the access-count problem (extend `test_evidence_governance.py` or put in the new file).

### C-13 (S4) Opaque crashes when validation is not evaluable
`models/baselines.py:74-82` and `:108-116`: if every validation MSE is `inf` (no evaluable val cell) or NaN, `best[2]` stays `None` and `a, (W, b) = best[1], best[2]` raises `TypeError: cannot unpack non-iterable NoneType`. `models/neural.py:154`: if `val` is never finite, `best_state` is `None` and `load_state_dict(None)` fails the same way. `experiments/runner.py:67` `np.diff(...).max()` fails on a single-date panel. Diff (baselines + neural):
```diff
--- a/backend/src/volatility_lab/models/baselines.py
+++ b/backend/src/volatility_lab/models/baselines.py
@@ after each penalty loop (twice)
+    if best[1] is None:
+        raise ValueError("no validation cell is evaluable: cannot select a penalty (val MSE is inf/NaN for every alpha)")
--- a/backend/src/volatility_lab/models/neural.py
+++ b/backend/src/volatility_lab/models/neural.py
@@ before net.load_state_dict(best_state)
+    if best_state is None:
+        raise RuntimeError("validation loss was never finite; no checkpoint to restore")
```
Test: a fold whose `val` positions are all unevaluable (all target statuses 0) -> `predict_baselines` raises `ValueError` with that text.

### C-14 (S4) Duplicate handling runs after the prefilter
`ingestion/optionsdx.py:211-214` dedupes after `prefilter_batch`; the module/docstring rule ("rows sharing (date, expiry, strike) but differing in any quote are all dropped", `:222-225`) therefore does not apply when one of the copies was already rejected by the prefilter (e.g. `no_usable_side`): the surviving copy is kept as if it were unique. Defensible, but not what the docstring says. Record in KNOWN_LIMITATIONS or move the key check before the prefilter (changes the ledger; routed).

### C-15 (S4) Smaller numerics / config nits
- `surfaces/diagnostics.py:34` butterfly "curvature" is the difference of slopes, not divided by node spacing; with the non-uniform `k_nodes` the fixed `tol = 1e-6` means different things per node triple. Sign test is unaffected.
- `settings.py:42` `min_quotes_per_slice` has no lower bound; with 1, `grid._slice_nodes` (`grid.py:32-33`) gets `np.clip(…, 1, 0)` and reports gap 0 -> `OBSERVED` from a single quote. Guard `>= 2` in `SurfaceConfig.__post_init__` (not proposed as diff: frozen dataclass config change; trivial).
- `settings.py:24` `min_mid = 0.05` is an absolute USD number (SPY tick); not portable to other underlyings/currencies (relevant to the multi-market direction in `orchestration/DECISIONS.md`).
- `settings.py:17` `kaggle_dataset` still defaults to the withdrawn hosted dataset and is part of `Config.sha256()` (routed).
- `ingestion/optionsdx.py:106-111,187`: `rglob("*.parquet")` is case-insensitive on Windows, `_iter_raw_batches` tests `path.suffix == ".parquet"` case-sensitively, so `X.PARQUET` is found and then parsed as CSV.
- `surfaces/grid.py:117`: panel `spot` is the first row of the day (nearest expiry/lowest strike); harmless while `underlying_last` is constant per date.

### C-16 (S4) Provenance nits
`runner.py:287` `json.dumps(..., default=str)` silently stringifies NumPy integers; `verify_manifest` (`runner.py:291-302`) checks listed files only, so a file added afterwards is not detected; `models/neural.py:98-99` sets `cudnn.deterministic` but not `torch.use_deterministic_algorithms`, and TF32 stays at PyTorch defaults — bitwise reproducibility is therefore claimed only per GPU model (T4 vs L4/A100 differ); `torch.save` stores NumPy arrays (`neural.py:162`) so a future `torch.load` under torch >= 2.6 needs `weights_only=False` (no loader exists in the repo today — grep).

### Checked and found sound (so reviewers need not re-derive)
- Walk-forward: `make_folds` (`walkforward.py:29-62`) purges train labels strictly before the first validation origin and validation labels strictly before the first test origin, in both `prev_year` and `tail_frac`; `assert_no_overlap` raises `LeakageError`, not `assert`, and rejects empty sets. Train-only: cell means (`runner._fold_inputs`, rows <= `train_rows_end` = last train *label* row), `standardize_fit`, PCA basis/mean, ridge penalty on validation only, `rv_terciles(train)`, neural normalisation and target scale. `causal_fill`, `trailing_mean`, `realized_vol`, `calendar_block` (weekday arithmetic `(d+3)%7`, epoch day 0 = Thursday) are causal. `fixed_expiry_targets` chooses the expiry from origin-date quotes only and censors (never imputes) when the expiry disappears.
- Units: IV decimal everywhere in storage/API; vol points only at `metrics.PTS`, `compare_methods` and `mae_observed_vol_points`; moneyness is forward log-moneyness `ln(K/F)` with F from the same slice used for OTM selection and grid nodes; undiscounted price = `mid / DF` against Black-76 on F (`quotes.py:102`).
- Solver: bracket `[1e-4, 5]`, 48 bisections (width ~1.8e-14), explicit statuses, bracket failures are `BELOW_SOLVER_FLOOR/ABOVE_SOLVER_CEILING` not arbitrage statuses, NaN/inf/non-positive inputs are `INVALID_INPUT`, no IV is ever invented. OTM-only use keeps call/put cancellation benign.
- Ledgers: conservation is checked globally and per snapshot at prefilter, duplicate and quote stages; `QUOTE_REASONS` order matches the `np.select` order and the `.index()`-based terminal codes.
- Surfaces: no extrapolation, status semantics match the API contract, total-variance interpolation weight `w = (Tt - T_lo)/(T_hi - T_lo)` correct.
- API: names regex-validated and resolved to direct children, symlinks out of a folder not served, `np.load` with `allow_pickle=False`, strict JSON, generic 500 text (no paths).

## 4. Proposed (summary of what the orchestrator may queue in INTEGRATION_QUEUE)

| Queue candidate | Finding | Needs Colab verification of | Risk |
|---|---|---|---|
| Q-C1 explicit panel dtypes (grid.py, 2 lines) + dtype test | C-02 | new test + full backend suite + hash probe P1 | low |
| Q-C2 run key + canonical PCA sign (runner.py) + test | C-01 | new test + backend suite | low-medium (touches an owner-modified file) |
| Q-C3 atomic put + `exist_ok` (raw_store.py) + test | C-04 | new test + `test_storage` | low |
| Q-C4 `_num` finite guard; HEAD/OPTIONS 405; Host guard (service.py, server.py) + tests | C-05, C-11 | new test + `test_api*` | low |
| Q-C5 evidence bool guard; selection guards (evidence.py, baselines.py, neural.py) + tests | C-12, C-13 | targeted tests | low |
| Q-C6 audit git failure handling (scripts/foundation_audit.py) | C-09 | audit run with and without `.git` | low |
| Not queued: C-03 manifest/hash schema, C-06 evidence process, C-07 verdict vocabulary, C-08 forward/DF method, C-10 gap-aware features | owner/D decisions | | |

## 5. Import-direction violations (assessed, not fixed)

Edges are exactly the two listed in `tests/unit/test_architecture_imports.py:17-22` (the AST scan covers lazy imports; no relative imports exist, grep clean).
1. **`models -> evaluation`** (`models/baselines.py:19-20` imports `evaluation.metrics.eval_mask` and `evaluation.walkforward.Fold`). Acyclic: `evaluation/*` imports only `config`, `features`, `surfaces` (and itself), never `models`. Impact: `baselines` cannot be unit-tested or reused without importing the evaluation package (and `metrics` pulls in pandas); the real coupling is `Fold` (a data holder) and one mask function used for validation MSE. Risk of leaving: low (S4). If fixed later: move `Fold`/`eval_mask` (or pass the mask in) rather than inverting the dependency; this changes import paths used by the generated notebooks, hence the owner-decision note in the test.
2. **`validation -> pricing`** (`validation/quotes.py:23` imports `pricing.bs`). Acyclic (`pricing` imports nothing in the package). This one has a functional cost: `build_otm_quotes` fuses quote validation, forward estimation, OTM selection and IV inversion, so quote-quality reasons and solver statuses share one ledger/enum (`QUOTE_REASONS`) and validation cannot be tested without the solver. Impact on S3 acceptance ("explicit handling of invalid/crossed/stale/missing quotes"): satisfied functionally, but the stage boundary in architecture.md section 4 is not real. Risk of leaving: low (S4); the cheaper honest remedy is to document that the stage is "validation + IV" (or rank `validation` after `pricing` in the test) instead of splitting a function whose ledger is already hashed into manifests.
No circular import exists, and `models.neural`/torch is imported lazily (`runner.py:143`), so CPU-only imports are safe.

## 6. Colab verification plan (for the orchestrator / `S_colab_executor`)

Preconditions: a connected Colab runtime (CPU runtime is sufficient and **preferred**: with a GPU runtime `tests/unit/test_gpu_guard.py::GpuTrainingTests` would train two tiny random-data networks for 8 epochs; that is plumbing, not project data, but it is still "training", so run it only with explicit owner approval). Record the date/time, runtime type and the Python version: the project is tested only on 3.12.6 (ADR-0003); if Colab is 3.13, NumPy 1.26.2 has no wheel, so skip the pinned-stack run and say so. All paths below are in the Colab VM; none touches the PC.

**Step 0 — environment record** (proves what stack the later numbers come from)
```bash
mkdir -p /content/out && cd /content
python --version | tee out/env.txt
python - <<'EOF' | tee -a out/env.txt
import numpy, pandas, scipy, pyarrow, platform; print(platform.platform(), numpy.__version__, pandas.__version__, scipy.__version__, pyarrow.__version__)
EOF
nproc | tee -a out/env.txt; lscpu | grep -E "Model name|avx512" | head -3 | tee -a out/env.txt
```
Install only what is missing: `pip install -q numpy pandas scipy pyarrow` (these are the only imports of the CPU path; do **not** install torch for the CPU run).

**Step 1 — transfer and integrity** (proves the Colab tree is the PC working tree; the repo's own S_colab_executor rule)
```bash
# upload orchestration/colab_transfer/{worktree_2026-10-20.tar.gz,MANIFEST.sha256} to /content/in (Colab file API or the owner)
mkdir -p /content/nvs && tar -xzf /content/in/worktree_2026-10-20.tar.gz -C /content/nvs
cd /content/nvs && sha256sum -c /content/in/MANIFEST.sha256 | grep -vc ': OK$'   # must print 0 ; expect 255 OK
sha256sum /content/in/worktree_2026-10-20.tar.gz /content/in/MANIFEST.sha256        # expect 0d5835e2…d4cb71 and 82a8de14…2bfd
```
Record the PC side: HEAD `306c01b…`, 45 `git status` paths. The tree has **no `.git`**.

**Step 2 — backend suite** (proves: 250-ish unit/scientific tests incl. leakage sentinels, ledgers, IV recovery, API on the first Linux/Colab run)
```bash
cd /content/nvs/backend && PYTHONPATH=src python -W error::ResourceWarning -m unittest discover -s tests -t . -v 2>&1 | tee /content/out/backend.log | tail -n 8
```
Expected for comparison only (owner-reported on the PC, not equivalent evidence): `Ran 252 tests ... OK (skipped=1)` (CUDA test), 181-293 s. Run the suites **sequentially** (CORE_STATUS section 9: concurrent runs oversubscribe BLAS threads). Report the exact counts, runtime, and any failure verbatim. Triage a failure as OS/stack difference vs product defect with a minimal repro; do not edit code. First-time-on-Linux risks to watch: `test_api` real-socket and symlink tests, `ResourceWarning` timing under `-W error`, case-sensitive paths.

**Step 2b — second stack, same host** (proves "passes on both stacks" on Linux and gives the C-03 drift measurement) — only if Python 3.12:
```bash
python -m venv /content/v126 && /content/v126/bin/pip install -q numpy==1.26.2 pandas==2.1.3 scipy==1.14.1 pyarrow==17.0.0
cd /content/nvs/backend && PYTHONPATH=src /content/v126/bin/python -W error::ResourceWarning -m unittest discover -s tests -t . 2>&1 | tee /content/out/backend_np126.log | tail -n 5
```

**Step 3 — leakage guards survive `-O`**: `cd /content/nvs/backend && PYTHONPATH=src python -O -m unittest tests.unit.test_leakage_and_folds` (expect 9 OK; proves the guards are real raises).

**Step 4 — Phase 0 spike suite** (standard library only; proves the separate spike is intact and Linux-clean): `cd /content/nvs/scripts/phase0_synthetic && python -W error::ResourceWarning -m unittest discover -s tests -t .` (expect 145 OK per CORE_STATUS; note the spike may write run records under `experiments/phase0_synthetic/` inside the Colab copy only).

**Step 5 — foundation audit** (proves doc/link/ID/secret consistency of the transferred files)
```bash
cd /content/nvs && git -C /content/nvs ls-files 2>&1 | head -2          # expect "fatal: not a git repository" -> see C-09
python scripts/foundation_audit.py --json /content/out/audit.json ; echo exit=$?   # path must not exist; expect exit 0
find data artifacts -type f ! -name README.md ! -name .gitkeep ; find . -name ".env*" ! -name ".env.example"   # both must print nothing
```
Because `.git` is absent, **record `tracked_data_files`/`tracked_env_files` as NOT EVALUATED** (the audit would print `[]` regardless) and use the two `find` commands as the substitute. Also note the audit does not see `orchestration/` (not in the transfer set).

**Step 6 — proof probes for the findings above** (each is a few lines, read-only, synthetic data from the repo's own generator; none is a new test):
- **P1 / C-02 + C-03** (run under Step 0's stack and again under `/content/v126/bin/python`; compare the printed hash and dtypes):
  ```bash
  cd /content/nvs/backend && PYTHONPATH=src python - <<'EOF'
  from tests.unit._fixtures import pipeline
  from volatility_lab.storage.raw_store import panel_sha256
  P = pipeline()["panel"]; print({k: v.dtype.str for k, v in P.items()}); print(panel_sha256(P)); print(pipeline()["diag"]["reprice_err_max"])
  EOF
  ```
  Expected: int64 dtypes on Linux in both stacks; **if the two hashes or the `reprice_err_max` differ, C-03 is confirmed** (cross-version float drift); if equal, C-03 is not observed on this host (it can still differ across CPUs). The PC's Windows/NumPy 1.26 `n_quotes`/`tenor_days` dtype (`<i4` predicted) cannot be measured without running code on the PC; it can be read from a stored panel in Colab if the owner uploads one.
- **P2 / C-05, C-11** (server probes): `PYTHONPATH=src python -m volatility_lab.api.server --root /content/emptyroot --port 8765 &` then `curl -s -o /dev/null -w "%{http_code}\n" -X OPTIONS http://127.0.0.1:8765/api/runs` (observed: 501; contract: 405), `curl -I http://127.0.0.1:8765/api/runs` (501), `curl -s -o /dev/null -w "%{http_code}\n" -H "Host: evil.example" http://127.0.0.1:8765/api/runs` (200 = no Host check). For C-05: `PYTHONPATH=src python -c "from volatility_lab.api.service import _num; print([_num(x) for x in ('nan','inf','1e999')])"` prints non-finite floats. Kill the server afterwards.
- **P3 / C-09**: the `git ls-files` line in Step 5.
- **P4 / cross-environment float drift of the synthetic Phase 2 study**: `cd /content/nvs && python scripts/phase2_surface_comparison.py --out /content/out/p2a.json >/dev/null && python scripts/phase2_surface_comparison.py --out /content/out/p2b.json >/dev/null && sha256sum /content/out/p2a.json /content/out/p2b.json`. The two Colab files must match each other (determinism); compare with the PC-recorded `ac8c57bd…c927db5` (CORE_STATUS section 3, PHASE2_SURFACE_COMPARISON) — **inequality with the PC value is not a defect, it quantifies cross-environment drift** (C-03); say which.

**Step 7 — what to report** (per command: environment line, manifest hash, exact result counts, failures verbatim, differences from the PC numbers listed separately). `BLOCKED — COLAB NOT CONNECTED` remains the status until Step 1 completes.

What these steps do **not** prove: GPU/CUDA behaviour (the guard test skips on a CPU runtime), any real-data behaviour, CI on GitHub Actions, or the UA-01…UA-14 journeys.

## 7. Routed to others

- **Orchestrator / owner:** C-01 — confirm whether any H3-H6 run reused a persisted `OUT_DIR`; C-03 manifest/hash design; C-06 whether `test_accessed_count` should remain a `validated` precondition; `Config.kaggle_dataset` default still names the withdrawn dataset (policy, `settings.py:17`).
- **Agent D (quant/research):** C-07 verdict vocabulary for "unevaluated under one label"; C-08 forward/DF diagnostics and bounds; C-10 gap-aware lag/sequence features and ledgering of dropped dates; absolute-USD `min_mid` for non-SPY underlyings; AM- vs PM-settled and intraday expiry handling if India/other markets are added (T = integer calendar days equates quote time with expiry time, which is right for PM-settled EOD data and not for other conventions).
- **Agent E (UI/API):** the HEAD/OPTIONS/Host findings affect the viewer only through the API; the viewer's "Live from run" wording is already noted in CORE_STATUS section 9.
- **Agent F (reviewer):** please attack C-02's claim that the PC's NumPy 1.26 panel is int32 (inference from NumPy 1.x/Windows defaults; not measured), and the "no S1" conclusion.
- **Agent A (repo audit):** CORE_STATUS section 9 "A3 rebuild gives identical content hash MET-L" is true only within one environment (C-02, C-03).

## 8. File-level change manifest (proposed, none applied)

| File | Change | Finding | Owner | Conflict risk |
|---|---|---|---|---|
| `backend/src/volatility_lab/surfaces/grid.py` | explicit dtypes on 3 panel entries | C-02 | core (Agent C / S3) | medium: file is modified-uncommitted by the owner |
| `backend/src/volatility_lab/experiments/runner.py` | `run_key`, `_claim_out_dir`, PCA sign | C-01 | core | medium: modified-uncommitted; notebooks call `run_neural` |
| `backend/src/volatility_lab/storage/raw_store.py` | atomic `put`, `exist_ok` | C-04 | core | medium: modified-uncommitted |
| `backend/src/volatility_lab/api/service.py` | `_num` guard | C-05 | core (API semantics) | medium: modified-uncommitted; UI consumes payloads |
| `backend/src/volatility_lab/api/server.py` | HEAD/OPTIONS 405, Host guard | C-11 | core | medium: modified-uncommitted |
| `backend/src/volatility_lab/evaluation/evidence.py` | bool guard | C-12 | core | low (untracked new file, owner-authored) |
| `backend/src/volatility_lab/models/baselines.py`, `models/neural.py` | selection guards | C-13 | core | low |
| `scripts/foundation_audit.py` | git failure handling | C-09 | core | medium: modified-uncommitted |
| `backend/tests/unit/test_panel_dtype_stability.py` (new) | dtype table | C-02 | core | none (new) |
| `backend/tests/unit/test_run_key.py` (new) | key + sign tests | C-01 | core | none |
| `backend/tests/unit/test_store_atomicity.py` (new) | crash-safety tests | C-04 | core | none |
| `backend/tests/unit/test_api_edge_inputs.py` (new) | `_num`, HEAD/OPTIONS, Host | C-05, C-11, C-12 | core | none (new file avoids editing `test_api.py`, which is modified-uncommitted) |
| `CHANGELOG.md`, `docs/research/KNOWN_LIMITATIONS.md`, `docs/engineering/CORE_STATUS.md`, `docs/architecture/API_CONTRACTS.md` (section 8: 405 for HEAD/OPTIONS, Host rule) | doc updates required by CLAUDE.md section 12 | all applied items | core | high: all modified-uncommitted; apply last, as one batch |
| `orchestration/INTEGRATION_QUEUE.md` | queue Q-C1..Q-C6 | — | orchestrator | none |

Apply order suggested: Q-C1 (smallest, enables clean cross-stack hash comparison) -> Q-C3 -> Q-C4 -> Q-C5 -> Q-C2 -> Q-C6; each followed by the targeted new test and then the full Step 2 in Colab.

## 9. Blocked
Executable verification of anything above: `BLOCKED — COLAB NOT CONNECTED` per `orchestration/SHARED_STATUS.md` at the time of reading (state may have changed; a transfer tarball already exists).

## 10. Not run
Everything: no test, script, probe or linter was executed by this agent; no GPU; no real data; no CI. The numbers 252/145/9/734 quoted above are the owner's recorded PC results (CORE_STATUS sections 3 and 9) and are listed only as comparison targets.

## 11. Failed
Nothing attempted failed. One statically predicted failure mode on the first Colab run: none found for the test suite itself; the foundation audit will pass without evaluating its Git checks (C-09).

## 12. Files changed
`orchestration/reports/ENGINEERING_REPORT.md` (this file; the `reports/` directory already existed). No other file.

## 13. Handoff
**May rely on:** the severity-ranked defect list with file:line evidence; that no S1 defect was found by static reading (not a proof of absence); the proposed diffs as queue candidates (each needs F review, owner approval and Colab verification of its test); the Colab plan, including the C-09 caveat that Git-based audit checks cannot be evaluated on the transfer set; the import-direction assessment (both edges acyclic, S4).
**May not rely on:** any statement that a test passes, a hash is reproducible across machines, or a finding is "confirmed" — all are static readings until the Step 6 probes run in Colab; the PC dtype claim in C-02 is inference from NumPy/Windows defaults; the diffs have not been applied or syntax-checked.
