# AP-004 — implementation plan for owner approval

**Status:** PROPOSED. **Nothing in this document has been implemented, and no source, test, config or doc file outside `orchestration/` was changed.** Recommendations here are the orchestrator's; only the owner's answers in §7 are decisions. Evidence base: reviewed engineering findings ([ENGINEERING_REPORT](reports/ENGINEERING_REPORT.md)), independent review ([INDEPENDENT_REVIEW](reports/INDEPENDENT_REVIEW.md)), Colab runs ([COLAB_VERIFICATION](reports/COLAB_VERIFICATION.md), snapshot `worktree_2026-10-20.tar.gz` sha256 `0d5835e2…d4cb71`). S1 stays IN_REVIEW.

## 0. Disclosure before approval (affects the approval boundary)
The first Colab backend run (252 tests, OK) happened on a runtime with a **Tesla T4 attached**. `tests/unit/test_gpu_guard.py:61-80` (`GpuTrainingTests`) is skipped only without CUDA, and the run reported no skip, so that test **did execute**: it trains tiny MLP and GRU networks for at most 8 epochs on random Gaussian noise (not project or market data) and asserts device `cuda:0`. This is plumbing, not research training, and the run preceded your later "no model training" instructions, but Agent C had flagged that this test should run only with explicit approval and I did not ask. I am telling you now so you can decide how to treat it. For every run proposed below, GPU use is avoided with `CUDA_VISIBLE_DEVICES=` (empty) so the test skips (§6). The Phase 0 spike, `-O` leakage, audit, P4 and P2 jobs were CPU-only and unaffected.

## 1. Reconciled patch queue (this approval covers Patches 1–4 only)
Merged per F: dtype + manifest = one decision; HEAD/OPTIONS = one change (C-11 = E-P9f); `run_key` (C) chosen over `Config` flags (D) as the smaller diff (decision D-2). **Out of AP-004 scope and not proposed here:** C-03 schema redesign (Options B/C below), C-06, C-07, C-08, C-10, C-12/C-13 (Q-C5), C-09 (Q-C6), UI fixes (UI session), A's doc-contradiction batch.

All five target files are **owner-modified and uncommitted**; edits are minimal in-place hunks, not rewrites. Finding numbers refer to the ENGINEERING_REPORT.

| # | Finding | Files (functions) | Confirmed behaviour (evidence level) | Minimal fix | New tests | Depends on |
|---|---|---|---|---|---|---|
| 1 | C-02 dtype | `surfaces/grid.py` `build_surface_panel` (lines 123, 127) | `n_quotes`, `tenor_days` get NumPy's default int. A stored PC panel is `<i4` (**observed by F**); Colab/NumPy 2 gives int64 (inferred from NumPy rules, **not yet measured**). `raw_store.py:48` hashes `dtype.str` | `dtype=np.int64` on `n_quotes` and `tenor_days` (spot and k_nodes are already float64 from Python floats; C's diff also makes them explicit, optional and harmless) | `tests/unit/test_panel_dtype_stability.py` (explicit dtype table for every panel key; see §2 limits) | Decision D-1 |
| 2 | C-04 raw store | `storage/raw_store.py` `RawStore.put` (lines 66–67), `ingest` (line 132) | Statically read: `copyfile` straight to the hash-named path; `mkdir(parents=True)` without `exist_ok`. A crash leaves a truncated object or an un-repairable dataset dir. **Not executed** | `put`: copy to `<dest>.part`, re-hash, `os.replace`; `ingest`: `mkdir(..., exist_ok=True)` (manifest is written last, so a dir without it is an interrupted ingest) | `tests/unit/test_store_atomicity.py` (3 cases in C-04) | Patch 1 (same decision area; both alter what a re-ingest sees) |
| 3 | C-05 + C-11 API | `api/service.py` `_num` (lines 53–58, needs `import math`); `api/server.py` `make_handler` (`do_GET`, `_refuse`, new `_host_ok`) | **Observed in Colab P2:** OPTIONS 501, HEAD 501 (contract: 405), `Host: evil.example` gives 200, `_num` returns `[nan, inf, inf]`. **Not executed:** non-finite CSV cell leading to HTTP 500 (hypothesis H-API; F read `server.py:35,60-63`) | see §3 | `tests/unit/test_api_edge_inputs.py` (new; avoids editing owner-modified `test_api.py`) | none (independent; sequenced after 1–2 by F's rule) |
| 4 | C-01 resume cache | `experiments/runner.py` `pca_factor_targets` (~103–107), new `run_key` and `_claim_out_dir`, one call after the three `mkdir`s in `run_neural` (~148) | Statically read: resume keyed only by (fold, model, seed); experiment flags absent from `Config.sha256()` (CORE_STATUS §6 item 5 records the same hash for H2/H3/H4); SVD sign not canonical. **Not executed**; whether any H-series run was affected is **unknowable from the repo** | `run_key.json` guard + canonical PCA sign (C-01 diff) | `tests/unit/test_run_key.py` (CPU, no GPU) | none |

Verified against the code: `runner.py` already imports `hashlib`, `json`, `Path`, `Prepared`, `Fold`; `Prepared` has `dates`, `status`, `horizon`, `target_name`, `calendar`, `mr_window` (features/panel.py:21-47). The `Fold` attributes the key uses (`test_year, train, val, test, train_rows_end`) are **to be confirmed against `walkforward.py` at implementation**.

## 2. Decision D-1 — dtype and manifest comparison (resolve first)
**Existing behaviour (read from `raw_store.py`).** `version_id = sha256({sorted input hashes, config_sha256})`: it contains **no code version**. `ingest` builds the manifest (including `panel_sha256`, `quote_diagnostics` with `reprice_err_*`, status counts, `quality_report_sha256`), serialises it, and if `datasets/<version>/manifest.json` exists it **requires byte equality** (`:124-126`), otherwise `OverwriteError("…a correction needs a new version")`; it also byte-compares the quality report. `verify_dataset` instead re-hashes the **stored** arrays, so it is unaffected by a dtype change.

**Invariant to protect.** Stored datasets are immutable and verifiable; a re-ingest must either reproduce the stored dataset exactly or fail loudly; it must never silently replace content. Any change to manifest content under the same `version_id` is, by design, a refusal.

**What dtype alone changes.** On Windows with NumPy 1.x, new panels would get int64 where old stores hold int32, so a re-ingest of an *old* store raises `OverwriteError`, while verification of the old store still passes. On Colab (int64 already) nothing changes. This is in addition to the refusal the current uncommitted code already causes for any store written before 2026-10-20 (the manifest gained `quality_report_sha256` and diagnostic keys). Only synthetic stores exist; no real dataset is authorized.

| Option | Change | Pros | Cons / risk |
|---|---|---|---|
| **A (recommended)** | Patch 1 only: explicit int64. Keep strict byte-compare. Document that cross-environment re-ingest is unsupported and that a store is regenerated into a new root after a code change. | Smallest diff; keeps immutability semantics unchanged; removes the one *deterministic* platform difference (dtype) | Does not address C-03 float drift (unmeasured). Old PC-written synthetic stores cannot be re-ingested (regenerate) |
| B | A + move `reprice_err_*` and `vendor_iv_median_*` out of the compared manifest region (an uncompared diagnostics file) | Removes the known-noisy values from the equality test | Manifest schema change (`dataset-1` to a new id); API and verify must read both; no measurement yet of whether `panel_sha256` itself drifts |
| C | B + a second `panel_structure_sha256` (ints, status, shape, floats rounded to 1e-6) | Cross-machine structural check | Largest schema change; rounding-straddle risk analysed in C-03; premature without drift data |

**Why not choose B or C now.** The evidence that would justify them (P1: same code, numpy 1.26 vs 2.x, compare hash and `reprice_err_max`) has **not been run**: it needs a Python 3.12 interpreter in Colab (not installed; Colab is 3.13). Choosing B or C would be guessing. **Recommendation: A now; revisit B/C only if P1 (once approved) shows drift.** If you prefer evidence first, hold Patch 1 until P1 has run.

**Tests demonstrating integrity under A.**
(a) `test_panel_dtype_stability`: explicit dtype table for every key built by `build_surface_panel` (`dates, n_quotes, tenor_days, slice_row, slice_expiry, anchor_expiry` `<i8`; `status` `|i1`; `iv, spot, k_nodes, slice_iv, slice_gap, gap_tight` `<f8`), to be re-derived from the code at implementation.
(b) Existing `test_storage`, `test_snapshot_ledger`, `test_reproducibility` stay green: same-environment re-ingest still `reused: True`, changed bytes or config still a new version, altered manifest still `OverwriteError`.
(c) A new case asserting `verify_dataset` still passes on a dataset whose stored `n_quotes` is int32 (built by saving a panel with int32 arrays), so old stores remain verifiable.
**Limit:** Colab (Linux, NumPy 2) cannot show the red phase for (a) because the default is already int64 there. The premise rests on the stored PC panel `<i4` (F-observed), and the test is a regression guard in Colab.

## 3. API change set (Patch 3): one owner, one file pair plus one new test file
- **3a `_num` finite guard** (`service.py`): parse, then return the float only if `math.isfinite`; otherwise keep the original text. Covers `nan`, `inf`, `-inf`, `Infinity` and overflow-derived `1e999`. *Design choice for you (D-3):* strings (C's proposal, preserves the original text) or `null`. Recommendation: strings. F-06 warns that the viewer's handling of a string inside a numeric column was **not checked** (UI session).
- **3b HEAD/OPTIONS return 405** (`server.py`): `do_HEAD = do_OPTIONS = _refuse` (same as POST/PUT/DELETE/PATCH; `Allow: GET`). Matches API_CONTRACTS §8 "every other method → 405"; P2 observed 501.
- **3c Host-header guard** (`server.py`): in `do_GET` only, reject with 400 when `Host` names anything other than `127.0.0.1`, `localhost` or `::1` (port stripped; bracketed IPv6 handled; absent `Host` allowed for HTTP/1.0 clients). Threat model: local-only tool, loopback bind already enforced (`create_server`), residual risk is DNS rebinding by a web page the researcher visits. Risk: legitimate access through another alias (`127.0.0.2`, the machine name, a reverse proxy) is refused, which fits the decided "local research tool only" scope (OD-1).
- **3d Non-finite CSV response path: an unverified hypothesis (H-API).** *"A table CSV containing `nan` or `inf` makes the whole table endpoint return 500 before the fix and 200 with those cells as text after it."* Test-first procedure in Colab: add `test_api_edge_inputs.py` alone to the **unpatched** snapshot; the 3d case must **fail** (expect 500). If it does not, H-API is refuted and 3a's claimed effect is withdrawn. Then apply 3a and require it to pass.
- **Test cases** (`test_api_edge_inputs.py`, real socket following `test_api.py:161-182`; `http.client` with `putrequest(skip_host=True)` so a custom `Host` can be sent): HEAD and OPTIONS return 405 with `Allow: GET`; `Host: evil.example` returns 400; `Host: 127.0.0.1:<port>`, `localhost`, `[::1]:<port>` and absent Host return 200; `Host: 127.0.0.1.evil.example` returns 400; a table CSV with cells `nan, inf, -inf, Infinity, 1e999, 7` returns HTTP 200 with the first five as strings and `7` as 7.0 (H-API).
- **Docs in the same change, per CLAUDE.md §12:** `API_CONTRACTS.md` §8 (405 for HEAD/OPTIONS, Host 400, non-finite cells) and CHANGELOG, applied as the single last docs batch (§5).

## 4. Patch 4 — neural resume cache (`experiments/runner.py`, decision D-2)
Apply C-01's diff: canonical sign of each row of the PCA basis `V` in `pca_factor_targets`; `run_key()` over {config hash, target label, calendar flag, `mr_window`, `pca_factors`, horizon, an int-only `panel_structure_sha256` of `dates` and `status`, per-fold sizes and boundaries}; `_claim_out_dir()` raises `RuntimeError` if `run_key.json` differs, or if `predictions/*.npy` exist without a key (legacy), else writes the key.

**D-2 (choose one):** `run_key` (recommended; the hash of existing configs is unchanged) or D's alternative of putting the experiment flags into `Config.sha256()`, which changes the hash of every future run and breaks comparability with the recorded `28b90c2a`.

**Consequences to accept:** (i) new runs are not bit-identical to the H5/H6 numbers because the PCA sign is canonicalised (those results are withdrawn history); (ii) existing output directories become "legacy" and cannot be resumed (by design); (iii) no executed notebook is affected, since the notebooks embed a stale copy of the package (REPO_AUDIT) until regenerated.

**Test:** `test_run_key.py` as in C-01: same inputs give the same key and are accepted; each of target, calendar, `mr_window`, `pca_factors`, seeds, fold change raises `RuntimeError`; a stray `predictions/x.npy` without a key raises `RuntimeError`; `V`'s largest-magnitude entry per row is positive and invariant under a sign flip of the training matrix. CPU only; `runner` imports torch lazily.

## 5. Sequence, rollback and the per-patch loop
Order: **D-1, D-2, D-3 answered, then Patch 1, Patch 2, Patch 3, Patch 4, then one docs batch** (API_CONTRACTS §8, CHANGELOG, CORE_STATUS counts, KNOWN_LIMITATIONS lines C asks for). Per patch:
1. **Pre-image and rollback artifact:** record `sha256` of each file to be touched and compare with `MANIFEST.sha256` (proves it is still the archived version; if the owner or the UI session changed it since, stop and ask). Save the exact reverse patch to `orchestration/patches/AP004-<n>.reverse.diff`. **Rollback = apply the reverse diff to the touched files only**, or restore just those files from the verified archive (`tar xzf worktree_2026-10-20.tar.gz <path>`). Unrelated owner work is never touched. Nothing is stashed, reset or committed.
2. **Tests first:** add the new test file(s) alone and run them in Colab on the **unpatched** snapshot to record the red phase where the behaviour is reproducible (Patches 2, 3, 4; not Patch 1, see §2).
3. **Patch** with minimal `Edit` hunks.
4. **Rebuild the snapshot** from the PC tree (tar plus sha256 manifest, as before: file operations only, no project code on the PC), upload to Colab, verify the archive hash and `sha256sum -c`.
5. **Colab verification:** targeted tests, then the full backend suite; record in a new COLAB_VERIFICATION addendum; update INTEGRATION_QUEUE.

## 6. Colab commands
All in Colab, each in its own cell, run in the background with a captured exit code. `CUDA_VISIBLE_DEVICES=` keeps the GPU test skipped; a skip is the *expected* result and is reported as such. Working directory = `<extracted tree>/backend`.
```bash
CUDA_VISIBLE_DEVICES= PYTHONPATH=src python -W error::ResourceWarning -m unittest tests.unit.test_panel_dtype_stability -v
CUDA_VISIBLE_DEVICES= PYTHONPATH=src python -W error::ResourceWarning -m unittest tests.unit.test_store_atomicity -v
CUDA_VISIBLE_DEVICES= PYTHONPATH=src python -W error::ResourceWarning -m unittest tests.unit.test_api_edge_inputs -v
CUDA_VISIBLE_DEVICES= PYTHONPATH=src python -W error::ResourceWarning -m unittest tests.unit.test_run_key -v
# regression: full backend suite; expected = previous 252 + new cases, 1 skipped (CUDA); NOT comparable to the earlier 252 / 0 skipped run
CUDA_VISIBLE_DEVICES= PYTHONPATH=src python -W error::ResourceWarning -m unittest discover -s tests -t .
# after Patch 1, additionally
CUDA_VISIBLE_DEVICES= PYTHONPATH=src python -W error::ResourceWarning -m unittest tests.unit.test_storage tests.unit.test_snapshot_ledger tests.unit.test_reproducibility -v
# after Patch 3, additionally: re-run probe P2 (the same script as Addendum 6), expecting HEAD/OPTIONS 405 and a foreign Host 400
```
That `CUDA_VISIBLE_DEVICES=` makes the existing test skip is **an assumption** (it makes `torch.cuda.is_available()` False in current PyTorch); the first run reports the actual skip count.

## 7. Risks, unresolved items and approvals needed
**Risks.**
1. All touched files are owner-modified and uncommitted: minimal in-place hunks, hash pre-check, reverse diffs.
2. The `grid.py` change makes new panels non-reproducible against old PC-written synthetic stores (regenerate; no real data exists).
3. The Host guard may refuse non-loopback aliases.
4. Strings in numeric table cells may display poorly in the viewer (UI session to check).
5. Canonical PCA sign changes future neural outputs relative to H5/H6.
6. New tests raise the count (252 to 252+N); docs that quote counts must be updated from the Colab result, not estimated.
7. The dtype red phase is not demonstrable on Linux.
8. `test_viewer_static` reads `frontend/`, which the UI session may be editing concurrently; a failure there would not be caused by these patches but must be triaged.

**Unresolved / not covered.** C-03 float drift and P1 (blocked on Python 3.12); the non-finite CSV 500 path (hypothesis until test 3d); whether any H3–H6 run reused a persisted `OUT_DIR` (unknowable); manifest schema redesign (Options B/C).

**Approvals requested (answer each; silence is not approval):**
1. **D-1:** Option A (recommended) / B / C / "hold Patch 1 until P1 has run".
2. **D-2:** `run_key` (recommended) or `Config` flags, and acceptance of consequences (i)–(iii).
3. **D-3:** non-finite table cells returned as strings (recommended) or `null`.
4. **Edit scope:** permission to make minimal in-place edits to exactly `surfaces/grid.py`, `storage/raw_store.py`, `api/service.py`, `api/server.py`, `experiments/runner.py`, and to create exactly `test_panel_dtype_stability.py`, `test_store_atomicity.py`, `test_api_edge_inputs.py`, `test_run_key.py` under `backend/tests/unit/`.
5. **Docs batch:** permission to update `API_CONTRACTS.md` §8, `CHANGELOG.md`, `CORE_STATUS.md` counts and `KNOWN_LIMITATIONS.md` as the last step.
6. **GPU test:** acknowledge §0, and either require GPU-free runs (`CUDA_VISIBLE_DEVICES=`) or say that the tiny random-data GPU plumbing test is acceptable.
7. **Snapshot rebuilds:** permission to rebuild and re-upload the code archive after each patch (file operations on the PC only; you do the upload step).

**Not approved by this document:** any other patch (Q-C5, Q-C6, C-03 redesign), real-data acquisition, model training, commits or pushes, UI changes, or installing Python 3.12 or Playwright in Colab.

**No implementation changes were made in preparing this proposal.**

---
## Evidence update 2026-10-21 for D-1 (no decision recorded; hold retained)
P1 and the NumPy 1.26.2 comparison have now run: see `reports/COLAB_VERIFICATION.md` Addenda 8–10. Summary: Linux gives int64 on both numpy 1.26.2 and 2.1.3 (the PC's int32 is consistent with Windows plus NumPy<2 only); the two library stacks give byte-identical panels and Phase 2 JSON on one host; the PC-vs-Linux float drift (max 1.7e-14 abs) persists on both stacks and is not explained by library versions; the dtype fix alone would not equalise PC and Linux hashes. **Recommendation (not a decision):** keep strict manifest comparison unchanged, treat Options B/C as unsupported by evidence, and treat the two-line int64 change as optional hygiene. **Owner decision, 2026-10-21 (chat): Patch 1 is CLOSED as not needed under Colab-only operation.** Consequences: `surfaces/grid.py` stays untouched (no dtype change), the strict manifest comparison stays unchanged, Options B/C are not adopted, and synthetic stores written before 2026-10-20 are simply regenerated. This was the owner's call; the evidence above informed it but did not make it.
