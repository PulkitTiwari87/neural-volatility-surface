# COLAB_VERIFICATION (V-1) — 2026-10-20

**Status:** IN_PROGRESS — backend suite VERIFIED in Colab; other checks not finished.
**Revision/manifest:** HEAD `306c01b` + uncommitted tree; archive `worktree_2026-10-20.tar.gz` (255 files, excl. `orchestration/`).

## Verified (output seen in the notebook)
| Item | Evidence |
|---|---|
| Archive integrity | sha256 computed in Colab = `0d5835e22f7650417486809875eabaf1c55092ebdeba2cb2d9757f5d50d4cb71`, equal to the value computed on the PC at build time |
| Environment | Python 3.13.15, Linux 6.6.122, numpy 2.1.3, pandas 2.2.3, scipy 1.16.3, pyarrow 23.0.1, torch 2.11.0+cu130, Tesla T4 |
| Backend suite | `cd backend && PYTHONPATH=src python -W error::ResourceWarning -m unittest discover -s tests -t .` → **Ran 252 tests in 205.768s, OK** (tail shows plain `OK`, no "skipped=" suffix; the CUDA test therefore ran on the T4 — inferred from the absence of a skip note, not separately confirmed) |

## Observed
- A `UserWarning` at `models/neural.py:138` (`float(loss)` on a tensor requiring grad) appears during the run; not an error, new to this environment, worth a `.detach()`/`.item()` follow-up (not queued yet).
- First execution outside the owner's PC, and on numpy 2.1.3 / pandas 2.2.3 / Python 3.13. Documented "251 passed + 1 skipped" becomes 252 executed here because a GPU was present.

## Not verified / defects in this check
- **Per-file manifest check did not run**: only the tar was uploaded (no `MANIFEST.sha256`), so `sha256sum -c` found nothing. Content identity rests on the archive hash alone (sufficient for the tarball); the 255-file listing was not re-checked in Colab.
- `-O` leakage run, Phase 0 spike suite (145 expected), foundation audit and a GPU-test confirmation were submitted in one cell; at last check it had printed only its first header and no result (the tool call timed out after 30s). **Not run / unknown.** Foundation audit will additionally report NOT EVALUATED for git-dependent checks (no `.git` in the archive; finding C-09).
- C's probes P1–P4 and the pinned numpy 1.26 stack: **not run**.

---
# Addendum — Phase 0 spike suite (2026-10-20, separate run; does not replace the sections above)

**Phase 0 spike suite status: PASS** (complete run, exit code 0). This is a different suite from the backend suite above and from the foundation audit; they are not interchangeable.

| Field | Value |
|---|---|
| Command | `cd scripts/phase0_synthetic && python -W error::ResourceWarning -m unittest discover -s tests -t .` (from CORE_STATUS §3 and `.github/workflows/tests.yml:45`; README variant omits `-W`) |
| Snapshot | `worktree_2026-10-20.tar.gz`, sha256 `0d5835e22f7650417486809875eabaf1c55092ebdeba2cb2d9757f5d50d4cb71` (re-hashed in Colab before this run), extracted fresh into `/content/tree_p0` |
| Environment | Colab, Python 3.13.15, 2 CPUs; numpy/pandas/scipy as recorded above (spike suite is stdlib per ADR-0003) |
| Result (runner output) | `Ran 145 tests in 25.715s` · `OK` (no failures, errors or "skipped=" suffix) → 145 run, 145 passed, 0 failed, 0 skipped |
| Exit code | **0**, captured by wrapping the run (`echo $?` to a file); wall time 26 s |
| Completed? | Yes, fully; no interruption |
| Data | Synthetic only (output labelled `SYNTHETIC - not market data`; files `*.synthetic.csv` written to temp dirs). No real data, no network use, no training |
| Warnings/errors | None seen in the captured output (tail inspected; first lines were 36 progress dots). The full output is on the runtime at `/content/p0_out.txt` |

**Why an earlier attempt was inconclusive:** the earlier combined cell (`-O` leakage + spike + audit + GPU test) was cut off by a 30 s tool timeout and its notebook was later replaced by a blank one; the old `/content/tree` directory kept test-written folders (`phase0/`, `chainpipe/`, `diagnostics/`), so this run used a fresh extraction and left that tree untouched. The outcome of the other three commands in that cell remains **unknown / not run**.

**Still not verified:** `-O` leakage run, foundation audit (and its git-dependent checks, finding C-09), GPU test confirmation, C's probes P1–P4, the numpy 1.26 comparison, per-file manifest check, CI. S0/S1 status is unchanged (S1 stays IN_REVIEW).

---
# Addendum 2 — Wave 2: `-O` leakage, foundation audit, manifest (2026-10-20; earlier results above are unchanged)

Snapshot for all jobs: `worktree_2026-10-20.tar.gz`, sha256 `0d5835e22f7650417486809875eabaf1c55092ebdeba2cb2d9757f5d50d4cb71` (re-hashed in Colab before Job A). Each job ran in its own fresh extraction (`/content/tree_a`, `/content/tree_b`); `/content/tree` and `/content/tree_p0` and earlier outputs were not touched. Each job was a separate cell, run in the background with its exit code captured to a file. Environment: Colab, Python 3.13.15, numpy 2.1.3, pandas 2.2.3, scipy 1.16.3. Synthetic fixtures only; no real data, no network, no training, no source edits.

## Job A — `python -O` leakage guards: **PASS**
| | |
|---|---|
| Command / cwd | `PYTHONPATH=src python -O -m unittest tests.unit.test_leakage_and_folds` in `/content/tree_a/backend` (from `.github/workflows/tests.yml:42`, CORE_STATUS §9) |
| Result | `Ran 9 tests in 39.941s` · `OK` → 9 run, 9 passed, 0 failed, 0 skipped |
| Exit code / wall time | **0** / 41 s (this ~40 s start-up is why the earlier combined cell looked stuck) |
| Warnings/errors | none in the captured output |
| Limits | proves these 9 tests pass with assertions stripped; it does not by itself prove every guard elsewhere uses a real raise |

## Job B — `scripts/foundation_audit.py`: **exit 0, but PARTIAL — not a full verification**
| | |
|---|---|
| Command / cwd | `python scripts/foundation_audit.py` in `/content/tree_b` (no `--json`, so it writes nothing) |
| Exit code / wall time | **0** / 1 s; stderr empty |
| Reported | `hard_failures: false`; required files missing: none; links checked 734, broken 0; secret hits 0; undefined ID references none; decisions n=15 (decided: DEC-002/005/006/007/008/013; interim: DEC-001/003); status-claim problems 0 |
| **NOT EVALUATED** | `data_and_env.tracked_data_files` and `tracked_env_files` printed `[]` **vacuously**: the archive has no `.git` (`git rev-parse` → "fatal: not a git repository"), so `git ls-files` (`foundation_audit.py:130,134,137`) returned nothing. Those two checks were not performed. `gitignore_covers_env: true` is a real text check. Substitute `find` checks from the plan were **not run** here. The audit also does not see `orchestration/` (not in the archive) |
| Reading | exit 0 means "no hard failure found among the checks that could execute", not that every property was verified. 734 links matches the PC-recorded count (CORE_STATUS §9), an independent consistency point |

## Job C — manifest integrity: **NOT VERIFIED — MANIFEST NOT UPLOADED**
`MANIFEST.sha256` is not on the runtime (searched `/content`, depth 3). Only the tarball was ever uploaded. The tarball hash matching the PC-built value proves the archive bytes are identical; it does **not** by itself validate the 255-entry file listing. A staged cell (Colab cell "JOB C") uploads only the manifest, checks its own hash against `82a8de14da11813186284b19bfef66280b936c11f3ed1140ac860abd6a892bfd`, then runs `sha256sum -c` in a fresh `/content/tree_m`. It has **not been run** (it blocks on the owner's upload widget).

## Prerequisites for the remaining probes (none run; source: ENGINEERING_REPORT §6 Steps 2b, 5, 6)
| Probe | Command (summary) | Prerequisite / blocker |
|---|---|---|
| NumPy 1.26 comparison (Step 2b) | venv with numpy 1.26.2 / pandas 2.1.3 / scipy 1.14.1 / pyarrow 17.0.0, rerun backend suite | **Needs Python 3.12; this runtime is 3.13.15** (numpy 1.26.2 has no 3.13 wheel). Requires installing a 3.12 interpreter in Colab (e.g. a separate toolchain) → treat as an environment change needing approval. Backend run ≈ 3.5 min |
| P1 (C-02/C-03) | print panel dtypes, `panel_sha256`, `reprice_err_max` under each stack | Read-only, synthetic; **useful only as a two-stack comparison**, so it waits on the 3.12 venv. Single-stack run gives dtypes only |
| P2 (C-05/C-11) | start API server on loopback in Colab, `curl` OPTIONS/HEAD/Host; `_num('nan')` | Executes the API server; read-only against an empty root; needs a temp empty dir and killing the server afterwards |
| P3 (C-09) | `git ls-files` failure | **Effectively observed already** in Job B (`fatal: not a git repository`); audit-JSON `git_available` field does not exist until a patch is applied |
| P4 (cross-env float drift) | run `scripts/phase2_surface_comparison.py` twice, compare SHA-256 to PC `ac8c57bd…c927db5` | Writes JSON to a path outside the tree (must not pre-exist); synthetic; CPU-only |
| Missing-git substitutes | the two `find` commands (Step 5) | none; cheap, read-only; not yet run |

## Overall V-1 evidence state (separate checks, not interchangeable)
Backend suite 252/252 OK · Phase 0 spike 145/145 OK · `-O` leakage 9/9 OK · foundation audit exit 0 with two checks NOT EVALUATED · manifest NOT VERIFIED · NumPy 1.26 comparison and P1/P2/P4 NOT RUN · CI never run. S1 remains IN_REVIEW; no stage status changes.

---
# Addendum 3 — Job C manifest integrity: **PASS** (2026-10-20; supersedes only the "NOT VERIFIED" line for Job C above)
Run by the owner's upload into the staged cell, output read from the notebook. Fresh extraction `/content/tree_m` of archive sha256 `0d5835e2…d4cb71`.
| | |
|---|---|
| Manifest identity | uploaded `MANIFEST.sha256` has sha256 `82a8de14da11813186284b19bfef66280b936c11f3ed1140ac860abd6a892bfd` = expected |
| Command | `sha256sum -c /content/MANIFEST.sha256` run in `/content/tree_m` |
| Result | manifest lines 255; `CHECK_EXIT=0`; 255 `OK`, 0 not-OK; files present in the extraction: 255 (no extra files) |
| Meaning | every file in the Colab snapshot matches the PC-built per-file SHA-256 list; the archive, the listing and the extraction are mutually consistent. It does not verify anything about PC files changed after the archive was built (e.g. ongoing UI-session edits) |
Remaining NOT RUN: NumPy 1.26 comparison (needs Python 3.12), P1, P2, P4, `find` substitutes for the two audit checks lacking `.git`; CI never run. No stage status changes.

---
# Addendum 4 — Colab reconnect (2026-10-20)
After the MCP disconnect the owner reconnected; `open_colab_browser_connection` returned true, but the runtime is **new** (Python 3.13.16, 2 CPUs): `/content` held only `.config` and `sample_data`, the archive and all extracted trees/outputs were gone. All results above remain valid records of the earlier runtime (archive sha256 `0d5835e2…d4cb71`). Further Colab work requires re-uploading the archive and re-verifying its hash first (upload cell staged in the notebook). Nothing was run on the new runtime except an environment/file-existence check.

---
# Addendum 5 — new runtime: re-upload, `find` substitutes, probe P4 (2026-10-20)
Runtime: Colab, Python 3.13.16, 2 CPUs (a different runtime from Addenda 1–3; numpy/pandas versions not re-printed here, expected as before but **not re-confirmed**). Snapshot: re-uploaded `worktree_2026-10-20.tar.gz`, sha256 re-computed in Colab = `0d5835e22f7650417486809875eabaf1c55092ebdeba2cb2d9757f5d50d4cb71` (**MATCH**). Fresh extraction `/content/tree_f` (255 files). `MANIFEST.sha256` not re-uploaded on this runtime; the per-file check in Addendum 3 was against the same archive hash. Synthetic only; no network, no training, no source edits.

## Job D — `find` substitutes for the git-dependent audit checks: **PASS (empty, as required)**
Commands in `/content/tree_f`: `find data artifacts -type f ! -name README.md ! -name .gitkeep` → no output; `find . -name '.env*' ! -name '.env.example'` → no output; return code 0. This substitutes for the audit's `tracked_data_files` / `tracked_env_files` on the transferred file set only; it says nothing about what is actually tracked in the PC repo (no `.git` here).

## Probe P4 — Phase 2 synthetic surface comparison, determinism and cross-environment drift
| | |
|---|---|
| Command / cwd | `python scripts/phase2_surface_comparison.py --out /content/out/p2{a,b}.json` run twice sequentially in `/content/tree_f` (outputs outside the tree) |
| Exit codes / time | both **0**; total 63 s (first run ≈ 30 s) |
| Determinism | **PASS**: both JSONs are 34,970 bytes with identical sha256 `d87774241978dccd831c3ba7e682d17cf51fafd331e418dd0871ab68e17f9dbd` |
| Versus PC value | PC-recorded hash (CORE_STATUS §3) `ac8c57bd…c927db5` ≠ Colab `d8777424…f9dbd`. **Not a defect by itself** (per the plan this measures cross-environment drift); the cause is **not established** (different Python/numpy/pandas/scipy, OS, CPU; or JSON content such as environment metadata). The PC file was not available to diff, so the *size* of the difference is **unknown** |
| Printed summary | `n_cells_scored` 4362 / 3821 / 4596 across the three compared policies (as printed in the log tail; not compared against the PC output) |
| Limits | one runtime, one run pair; says nothing about drift on the PC stack. Diagnosing the difference needs the PC JSON (owner upload, or a key-by-key diff) |

## Updated NOT RUN list
NumPy 1.26 comparison and P1 (need Python 3.12 interpreter), P2 (API server probes), pinned-stack runs, CI. S1 remains IN_REVIEW; no stage status changes.

---
# Addendum 6 — Probe P2 (API transport / input edges, C-05 and C-11) (2026-10-20)

**P2 status: EXECUTED — all documented expectations matched (the probes confirm the reported behaviours; they are not tests that "pass" a requirement).** Procedure source: `ENGINEERING_REPORT.md` §6 Step 6 "P2 / C-05, C-11"; findings C-05 and C-11 (§C-11, lines 212–216).

| | |
|---|---|
| Snapshot | `worktree_2026-10-20.tar.gz`, sha256 `0d5835e22f7650417486809875eabaf1c55092ebdeba2cb2d9757f5d50d4cb71` (re-hashed in the same job), fresh extraction `/content/tree_p2`; empty API root `/content/p2_root` |
| Environment | Colab, Python 3.13.16, numpy 2.1.3, pandas 2.2.3 |
| Job | its own cell; script `/content/p2_run.sh`, full output `/content/p2_out.txt`, server log `/content/p2_server.log` |
| Server | `PYTHONPATH=src python -m volatility_lab.api.server --root /content/p2_root --port 8765` in `/content/tree_p2/backend`; loopback bind (`server.py:91-94`), ready after 1.13 s |
| Read-only evidence | `PYTHONDONTWRITEBYTECODE=1`; hash over all 255 tree files identical before and after (`TREE UNCHANGED`: `1b1624b5…ec1f8`); API root still empty (0 entries) |
| Clean start/stop | started, answered 5 requests, `kill -TERM` → exit status 143 (terminated by SIGTERM, as expected for a signal kill; not a graceful shutdown path), then curl returned rc 7 (connection refused) → port released |

| Probe | Expected | Actual | Verdict |
|---|---|---|---|
| CONTROL `GET /api/runs` (added, not in the documented procedure) | 200 | 200, body `[]` | server works; empty root returns an empty list |
| CONTROL `POST /api/runs` (added) | 405 | 405 `{"error": "read-only API"}`, `Allow: GET` | as designed |
| P2 `OPTIONS /api/runs` | 501 (finding); contract says 405 | **501** `Unsupported method ('OPTIONS')`, HTML error body, no `Allow` header | C-11 **confirmed**: violates API_CONTRACTS §8 "every other method → 405" |
| P2 `HEAD /api/runs` | 501 (finding) | **501** `Unsupported method ('HEAD')` | C-11 **confirmed** |
| P2 `Host: evil.example` | 200 = no Host check | **200** `[]` | C-11 **confirmed**: no Host-header validation (DNS-rebinding exposure; data returned is empty only because the root is empty) |
| C-05 `_num` on `'nan'`, `'inf'`, `'1e999'` | non-finite floats | `[nan, inf, inf]`, rc 0 | precondition of C-05 **confirmed**: `_num` lets non-finite values through |

Curl return code 0 and response times ≈ 1 ms for every request; no timeouts.

## Limits / not evaluated
- **C-05's end effect was not probed**: the documented probe only shows `_num` returns non-finite floats. That `json.dumps(allow_nan=False)` then turns a whole table response into a 500 was confirmed by F by code reading (`server.py:35`), **not executed** here (it would need a run directory containing a CSV with a `nan` cell, which is not part of the documented P2).
- `/content/p2_server.log` is empty: the server's startup `print` is block-buffered when stdout is a file and the process was killed by SIGTERM before flush. Not a fault; it means no server-side traceback or log line was captured (the handler's `log_message` is also deliberately silent, `server.py:85`).
- The HEAD probe printed headers (curl `-I`), so its "body" in the log is the header block.
- Only the empty-root case; no real run directories, no fixtures; negative origin index and whole-CSV read (C-11 other points) not probed.
- Single runtime; loopback only; no Playwright/UI.

## Effect on readiness for AP-004
P2 turns C-11 (HEAD/OPTIONS 501, no Host check) and the `_num` half of C-05 from static readings into **observed behaviour on the Colab snapshot**, which supports applying Q-C4/Q-C5-type patches (test: new `test_api_edge_inputs.py`). It does not change AP-004's other prerequisites; no stage status changes (S1 stays IN_REVIEW).

---
# Addendum 7 — AP-004 Patches 2, 3, 4: red/green and full-suite verification (2026-10-21)
Patch 1 (dtype/manifest, `surfaces/grid.py`) is **HELD by owner decision D-1** and was not touched. Scope applied: `storage/raw_store.py` (Patch 2), `api/service.py` + `api/server.py` (Patch 3), `experiments/runner.py` (Patch 4); new tests `test_store_atomicity.py`, `test_api_edge_inputs.py`, `test_run_key.py`. No docs/PC execution/commit. Pre-images: `orchestration/patches/pre/`; reverse diffs `orchestration/patches/AP004-{2,3,4}.reverse.diff`.

**Snapshots.** Patched: `worktree_ap004_2026-10-21.tar.gz` sha256 `d85e2e30732e46c60a54a5edacd54194c84d94692c24e0f66e79ecfeefec3dce` (MATCH in Colab), `MANIFEST_ap004.sha256` sha256 `1d0ca30e78823c3d57719db23ca0e0ba64b80d77706352c435f573710a35b051` (MATCH); extraction: 258 files, `sha256sum -c` 258 OK, 0 not OK. Unpatched (red): the original archive `0d5835e2…d4cb71` (re-hashed) + only the three new test files copied from the patched archive (their sha256: atomicity `2d8cb2f0…`, api_edge `2ec6d039…`, run_key `d348a53b…`).
**Environment (both phases):** Colab CPU runtime, Python 3.13.16, numpy 2.1.3, pandas 2.2.3, scipy 1.16.3, torch 2.11.0+cpu, `cuda_available False`. All runs used `CUDA_VISIBLE_DEVICES=` and `PYTHONDONTWRITEBYTECODE=1`, `-W error::ResourceWarning`, each module as its own background job with exit code captured. Synthetic fixtures only; no real data; **no model training** (run-key tests stub `train_and_predict`).

## Red phase (UNPATCHED sources + new tests) — failures are the expected evidence
| Module | Result | What it showed |
|---|---|---|
| `test_api_edge_inputs` (exit 1, 1 s, 6 tests) | 4 FAIL, 2 ok | **H-API CONFIRMED (executed):** table CSV with `nan/inf/1e999` → **HTTP 500**, body `{"error": "the run data could not be read"}`; `HEAD` → **501** (contract 405); `Host: evil.example` → **200**; `_num('nan')` returned nan. (Loopback-host and unknown-path tests passed, as expected unpatched.) |
| `test_store_atomicity` (exit 1, 3 s, 5 tests) | 2 FAIL, 1 ERROR, 2 ok | interrupted copy **left a file under the object's hash name**; a source changing between hash and copy was **not refused** (`OverwriteError not raised`); `ingest` on a leftover dataset dir → **`FileExistsError`** |
| `test_run_key` (exit 1, 44 s, 7 tests in that run*) | 2 FAIL, 6 ERROR | a changed learning rate and a different target label **silently reused stale predictions** (`RuntimeError not raised`) — the C-01 hazard is real for same-shape experiments; the PCA-factor case failed loudly (matmul shape mismatch), the rest errored only because `RUN_KEY_FILE`/`RunKeyError` do not exist yet |
*The red run executed 7 tests (the `RunNeuralResumeTests` class): 2 FAIL (stale reuse not refused) and 4 ERROR. The other 2 errors are `setUpClass` failures of `RunKeyTests` and `ClaimOutDirTests` (they call the not-yet-existing `runner.run_key`), so those classes tests did not run; the patched module has 15 tests.

## Green phase (PATCHED archive)
| Command (cwd `/content/tree_ap004/backend`, prefix `CUDA_VISIBLE_DEVICES= PYTHONPATH=src python -W error::ResourceWarning`) | Result | Exit / time |
|---|---|---|
| `-m unittest tests.unit.test_store_atomicity -v` | Ran 5, **OK** | 0 / 3 s |
| `-m unittest tests.unit.test_api_edge_inputs -v` | Ran 6, **OK** | 0 / 2 s |
| `-m unittest tests.unit.test_run_key -v` | Ran 15, **OK** | 0 / 43 s |
| `-m unittest discover -s tests -t . -v` (full backend suite) | **Ran 278 tests in 191.653 s — OK (skipped=1)**: 277 passed, 0 failed, 0 errors | 0 / 197 s |
The 278 = previous 252 + 26 new (5 + 6 + 15). **No regression** in any pre-existing test; no warnings or tracebacks in the log (the `UserWarning` seen on the first T4 run came from the GPU test and did not occur here).

## GPU test status
The single skip is `tests.unit.test_gpu_guard.GpuTrainingTests.test_both_architectures_train_predict_and_checkpoint_on_gpu` (reason printed: "requires a real CUDA GPU"). **It was SKIPPED, not executed**, because this runtime had no CUDA (and `CUDA_VISIBLE_DEVICES=` was set). Its GPU-path execution is **not verified in this run**; the earlier 252-test run on a T4 is a separate record. Permitted tiny synthetic GPU test remains available on a GPU runtime if wanted.

## Limits
Patch 3's effect on a live server process (P2 re-run) was not repeated; the real-socket tests cover HEAD/OPTIONS/Host/non-finite behaviour. `run_neural` was exercised end-to-end only with training stubbed (no real network training). The key does not fingerprint LAPACK build identity beyond numpy/python/platform strings; cross-machine PCA-sign flips are therefore *refused* (fail closed), not *repaired*. P1 / NumPy 1.26 / drift evidence remain **NOT RUN** (blocks Patch 1). CI never run. S1 stays IN_REVIEW.

---
# Addendum 8 — P1 and NumPy 1.26 investigation, part 1 (2026-10-21; **INCOMPLETE — blocked on one approval and one upload**; earlier evidence unchanged)
Goal: evidence for the held AP-004 Patch 1 (dtype + manifest comparison). **Patch 1 was not implemented and no source/test file was changed.**

## Environment and artifact inspection (read-only)
- Colab runtime: Linux 6.6.122 x86_64, AMD EPYC 7B12, 2 CPUs, 12 GB RAM, no GPU, `/usr/local/bin/python` 3.13.16 with numpy 2.1.3 / pandas 2.2.3 / scipy 1.16.3 / pyarrow 23.0.1.
- **Python 3.12 is already installed** (`/usr/bin/python3.12`, 3.12.3, apt). It has numpy **1.26.4** (apt) but **no pandas, scipy, pyarrow, pip or `ensurepip`**, so a stdlib `venv` cannot be made. `uv` 0.13.1 is installed. No conda/pyenv. So a project-capable 3.12 environment **requires installing packages** (not done; see approval below).
- Dependency constraints in the repo: there is **no dependency manifest** (toolchain DEC-015 is open); CI installs unpinned numpy/pandas/scipy/pyarrow; the owner's PC stack recorded in CORE_STATUS is Python 3.12.6, numpy 1.26.2, pandas 2.1.3, scipy 1.14.1, pyarrow 17.0.0 (and a second PC venv numpy 2.5.4 / pandas 3.0.6 / scipy 1.18.1 / pyarrow 26.0.0).
- Artifacts on the runtime: original archive `0d5835e2…d4cb71` and the tested patched archive `d85e2e30732e46c60a54a5edacd54194c84d94692c24e0f66e79ecfeefec3dce` with `MANIFEST_ap004.sha256` (`1d0ca30e…b051`, 258 files, all OK again in this session). **The final archive (`worktree_ap004_final_2026-10-21.tar.gz`, `d56b04bd…6236`) and its manifest are NOT on this runtime.** Deviation, flagged: this investigation used the tested archive `d85e2e30…`; PC-side manifests show it differs from the final archive in exactly four documentation files (CHANGELOG, API_CONTRACTS, CORE_STATUS, KNOWN_LIMITATIONS), so all code involved is byte-identical. Nothing was reconstructed. If you require the final archive for the remaining runs, upload it.
- PC-side disclosure: to read the PC store's manifest I ran a three-line Python JSON print on the PC (no project code, no project data beyond a manifest); nothing else ran locally.

## P1 (documented probe, ENGINEERING_REPORT §6 Step 6) on the CURRENT stack — EXECUTED
| | |
|---|---|
| Command / cwd | `cd /content/tree_p1/backend && PYTHONPATH=src python - <<EOF … EOF` with the exact three-line body from the report (`from tests.unit._fixtures import pipeline`; `panel_sha256`; print dtypes, hash, `reprice_err_max`), run as **two separate processes** |
| Snapshot | `d85e2e30…` extracted fresh to `/content/tree_p1`; `sha256sum -c` 258 OK, 0 not OK |
| Stack | Python 3.13.16, numpy 2.1.3, pandas 2.2.3, scipy 1.16.3, pyarrow 23.0.1, Linux x86_64, AMD EPYC 7B12 |
| Output (both runs identical) | dtypes: `dates <i8, spot <f8, n_quotes <i8, iv <f8, status |i1, gap_tight <f8, anchor_expiry <i8, slice_row <i8, slice_expiry <i8, slice_iv <f8, slice_gap <f8, tenor_days <i8, k_nodes <f8`; `panel_sha256` **`ba38973042dd520159abc0d3ef25c6605fbfdf150410938796d14978f8e76b81`**; `reprice_err_max` **`2.9260097331197457e-15`** |
| Exit / time | both 0; 49 s and 37 s; stderr empty |
| Expected vs actual | expected (C-02 prediction): int64 for `n_quotes`/`tenor_days` on Linux/NumPy 2 → **matches (now measured, not inferred)**. Within-environment reproducibility: **yes** (hash, dtypes and residual identical across processes) |
| Not established by this run | the two-stack comparison P1 is designed for (NumPy 1.26 vs 2.x): **BLOCKED**, see below |

## Phase 2 comparison (P4) — what could be compared without installing anything
- The PC's original JSON (`ac8c57bd…c927db5`) is **not available anywhere** in the repo or `scratch/`. The Colab JSON (`d8777424…f9dbd`, two identical runs, Addendum 5) has **no environment metadata fields** (top-level keys `label, study, k, t, filters`; 1,057 leaves), so serialization/environment metadata cannot explain the hash difference.
- **Substitute that exists:** `PHASE2_SURFACE_COMPARISON.md` §4.1 prints the PC run's k-interpolation table (n and MAE at 3 decimals, 5 regions + ALL, 4 methods, dense and sparse = 48 cells). Compared programmatically to the Colab JSON: **48/48 cells match** (every `n` exactly; MAE equal after rounding to 3 d.p.; largest |Colab − doc| = 0.000492, inside the doc's rounding of 0.0005). §4.2–§4.3 were not compared.
- Meaning: the PC and Colab results agree **at the published precision**; any real difference is below 3 decimals of a vol point. The *cause* of the differing file hash (sub-rounding float drift vs another difference) and its *magnitude* remain **undetermined** without the PC JSON. This is a bounded, not an exact, statement; the doc table may also reflect an earlier code version.

## What is blocked and exactly what is needed
1. **NumPy 1.26 two-stack run (P1 and P4) — needs approval to install packages (nothing installed yet).** Proposed, isolated, reversible: `uv venv /content/v312 --python /usr/bin/python3.12`, then `uv pip install --python /content/v312/bin/python numpy==1.26.2 pandas==2.1.3 scipy==1.14.1 pyarrow==17.0.0` (the PC's recorded stack; wheels from PyPI, ~150–200 MB, no torch, no compiler). It creates only `/content/v312`; system Python 3.12/3.13 and the current packages are untouched; nothing is persisted outside the runtime; removing the directory undoes it. The only mismatch with the PC: Python 3.12.3 (Ubuntu) vs 3.12.6, and Linux vs Windows.
2. **PC-vs-Colab comparison of the actual stored artifact — needs one upload.** `scratch/demo_store` (synthetic, produced on the PC: raw CSV `303cc061…` + `panel.npz` `a42debc7…`) was packaged as `orchestration/colab_transfer/pc_demo_store_2026-10-21.tar.gz` (sha256 `c642e5ab12674ed9d4b5896f81ec8b1bf455b97279aa413defb2b5d6a88fc716`, 6.3 MB, synthetic data only). Plan: re-ingest its raw CSV in Colab on each stack and compare the new panel with the PC panel array by array (dtype, exact equality, max abs/rel difference, NaN positions). Caveat to be stated with the result: the PC store was written by an earlier code version (old manifest schema), so a difference there can be code or environment; a **match** (apart from dtype) would be strong evidence for no float drift, a **mismatch** will be attributed only as far as the NumPy 1.26 / current-stack comparison allows.

---
# Addendum 9 — PC-written artifact vs Colab re-ingest, current stack (2026-10-21; part 2 of the P1/NumPy investigation; NumPy 1.26 half still BLOCKED on the install approval)
**Method.** The owner uploaded `pc_demo_store_2026-10-21.tar.gz` (sha256 `c642e5ab…c716`, MATCH; inside: PC `panel.npz` `a42debc7…`, raw CSV `303cc061…`, both equal to the hashes taken on the PC). Harness `/content/pc_compare.py` (outside the project tree; synthetic data; no source change) re-ingested the store's own raw CSV with the verified code (tested archive `d85e2e30…`, code-identical to the final archive) via `ingest(...)` and compared the result with the PC-written panel and manifest. Stack: Colab, Python 3.13.16, numpy 2.1.3, pandas 2.2.3, scipy 1.16.3, pyarrow 23.0.1, Linux x86_64, AMD EPYC 7B12. The PC artifact was written on Windows with Python 3.12.6 / NumPy 1.26.x (CORE_STATUS) by **earlier code** (pre-2026-10-20 manifest schema). Exit 0, 3 s; report `/content/pc_cmp_cur/report.json` (sha256 `7afffaae…d199`); single run (within-environment reproducibility of this harness was not separately repeated; P1 itself was identical across two processes, Addendum 8).

| Item | PC artifact vs Colab re-ingest |
|---|---|
| Same input, same config | input sha256 identical; `config_sha256` identical (`eaa46df0…`); `version_id` identical (`d9f28e5d…`); `Config` dict diff empty |
| Array set | same 13 keys; no keys only on either side |
| **dtypes** | **`n_quotes` and `tenor_days` are `<i4` on the PC and `<i8` on Colab** (the only dtype differences); all other arrays identical dtype. Values of those two arrays are equal |
| Integer/status arrays | `dates, anchor_expiry, slice_row, slice_expiry, status` byte-identical; **every cell status identical**; `n_quotes`/`tenor_days` equal in value |
| Exactly equal floats | `spot` (60), `k_nodes` (9), `gap_tight` (1): bit-identical |
| **Float drift** | `iv`: 12 of 2,717 finite values differ bitwise (0.44 %), max abs **1.43e-14**, max rel **8.4e-14**; `slice_iv`: 41 of 16,932 (0.24 %), max abs 1.70e-14, max rel 1.15e-13; `slice_gap`: 207 of 16,932 (1.22 %), max abs 2.8e-17, max rel 7.7e-15. NaN counts and **NaN positions identical** (523 / 672 / 672); no infinities. Magnitude = a few ULP (IV is decimal, so 1e-14 ≈ 1e-12 vol points) |
| `panel_sha256` | PC `be21f0cd…` (recorded = recomputed) ≠ Colab `9c666d22…`. **After casting every integer array to int64 on both sides the hashes still differ** (`7fd462bc…` vs `06429afd…`) because of the float drift |
| Manifest | all ledger/diagnostic/status-count content equal. Differences: `panel_sha256` (above); input `name` (**artifact of my harness**: it ingested the stored object, whose file name is its hash, not the original `synthetic_chain_seed0_60d.csv`); and keys that exist only in the newer manifest schema (`quality_report_sha256`, `reprice_err_max`, `reprice_err_median`, `solver_status_rejects`, `reused`) — i.e. **the PC store cannot be re-ingested under current code regardless of dtype** |

## What this establishes, what it does not
- **Established (measured):** (1) the int32 panel dtype exists in a real PC-written artifact; (2) on Linux/NumPy 2.1.3 the same data gives int64; (3) the numerical results agree to ~1e-13 relative and every discrete outcome (statuses, NaN mask, integer arrays, ledgers) is identical; (4) exact `panel_sha256` equality across these two environments does **not** hold, and fixing the dtype alone would **not** restore it for this dataset.
- **Consistent with but not separately tested:** that the int32 comes from NumPy 1.x on Windows (default integer is C `long`); NumPy 2 and Linux both default to int64. No Windows run was possible.
- **Not determined:** the cause of the float drift. Candidates that cannot be separated by this comparison: NumPy 1.26 → 2.1 (SIMD/libm kernels), Windows vs Linux libm, CPU, Python 3.12.6 vs 3.13, pandas version, and **the code changes made since the PC store was written** (the old code was not run). The NumPy 1.26.2 run on this same Linux host (pending install approval) separates *NumPy version* from *OS/CPU*; it cannot remove the code-version confound.
- **Phase 2 JSON (P4):** unchanged — doc-table comparison 48/48 cells equal at 3 d.p.; PC JSON unavailable.

---
# Addendum 10 — NumPy 1.26.2 comparison, P1 and Phase 2 on both stacks (2026-10-21; completes the P1/drift investigation; Patch 1 NOT implemented)
Snapshot: tested archive `d85e2e30…3dce` (258 files, manifest OK; code-identical to the final archive, which was not on the runtime — upload it if you want the runs repeated on it). No source change; synthetic data only; Colab only.

## Environment (approved install)
`/content/v312`: system Python **3.12.3** (apt) + `uv 0.13.1`; `uv pip freeze`: numpy **1.26.2**, pandas **2.1.3**, scipy **1.14.1**, pyarrow **17.0.0** (+ python-dateutil 2.9.0.post0, pytz 2026.5, six 1.17.0, tzdata 2026.5); `uv pip check`: compatible. The venv matches the PC's recorded stack except Python 3.12.3 vs 3.12.6 and Linux vs Windows. Current stack for comparison: Python 3.13.16, numpy 2.1.3, pandas 2.2.3, scipy 1.16.3, pyarrow 23.0.1. Same host for both: Linux 6.6.122 x86_64, AMD EPYC 7B12, 2 CPUs. **Default environment untouched** (`pip freeze` sha256 `0195f889…ee01` before and after; default numpy still 2.1.3).
**Provenance disclosure:** `/content/v312` already existed when my install script ran (its `uv venv` reported "already exists"; directory created 19:10 UTC, my script 19:15 UTC; contents exactly the approved pins). I did not create it and do not know who did (most likely the same approved command run by the owner). I therefore ran `uv pip install --reinstall` of the four pins (8 packages reinstalled, served from the uv cache) and `uv pip check` before using it. The wheels' original download is not independently verified beyond uv's own hash checks.

## P1 (documented probe, ENGINEERING_REPORT section 6 Step 6) on numpy 1.26.2 — EXECUTED
| | |
|---|---|
| Command / cwd | `cd /content/tree_p1/backend && PYTHONPATH=src /content/v312/bin/python -` with the documented 3-line body supplied on stdin, two separate processes. An earlier attempt that ran the body as a *file* failed with `ModuleNotFoundError: tests` — my harness error: a script file puts its own directory on `sys.path`, stdin puts the working directory; not a project fault; both failed attempts are kept in `/content/v126_runs/p1_v126_run*.err` |
| Result (both runs identical) | dtypes all as on the current stack, **`n_quotes` and `tenor_days` `<i8`**; `panel_sha256` **`ba38973042dd520159abc0d3ef25c6605fbfdf150410938796d14978f8e76b81`**; `reprice_err_max` **`2.9260097331197457e-15`** |
| Exit / time / stderr | 0, 0; 35 s and 34 s; empty |
| vs current stack (Addendum 8) | **identical** dtypes, hash and residual: numpy 1.26.2 / pandas 2.1.3 / scipy 1.14.1 / Python 3.12.3 and numpy 2.1.3 / pandas 2.2.3 / scipy 1.16.3 / Python 3.13.16 give the same panel hash on this host |

## PC-written artifact vs re-ingest, four runs (current stack x2, numpy 1.26.2 x2) — EXECUTED
All four: exit 0, 3–4 s, stderr empty; `version_id` and `config_sha256` equal to the PC's; `panel_sha256` `9c666d22ed556d0a…` in **every** run. The re-ingested panels of the two stacks are **byte-identical to each other in all 13 arrays**, and identical between repeat runs. Relative to the PC-written panel every run shows exactly the same differences as Addendum 9: `iv` 12/2,717, `slice_iv` 41/16,932, `slice_gap` 207/16,932 values bitwise different (max abs 1.43e-14 / 1.70e-14 / 2.78e-17), `n_quotes`/`tenor_days` `<i8` vs the PC's `<i4`, statuses/NaN masks/ledgers identical, int64-normalised hash still different. Reports: `/content/v126_runs/pc_{v126_a,v126_b,cur_b}/report.json`, `/content/pc_cmp_cur/report.json`.

## Phase 2 surface comparison (P4), same snapshot, two runs per stack — EXECUTED
Exit 0 for all four (29–31 s each, stderr empty). **All four JSONs and the earlier Addendum-5 JSON (run on the original archive) are byte-identical**: sha256 `d87774241978dccd831c3ba7e682d17cf51fafd331e418dd0871ab68e17f9dbd`. Recursive comparison of every pair (cur-a/cur-b, 1.26-a/1.26-b, cur-a/1.26-a, earlier/cur-a): 689 numeric leaves, **689 exact, 0 differ**, no keys on one side only, no type mismatches, no non-finite values. The PC's JSON (`ac8c57bd…`) is unavailable, so the PC/Colab hash difference stays undetermined; the section 4.1 doc-table comparison (48/48 cells equal at 3 d.p., Addendum 8) stands.

## What the evidence supports
1. **The float drift is not caused by the NumPy / pandas / SciPy / PyArrow / Python (3.12 vs 3.13) versions:** swapping the whole library stack on one host changes nothing (byte-identical panels and JSON). Re-ingest and Phase 2 are **bit-reproducible across these two library stacks on this Linux/CPU**.
2. **The int32 panel dtype is not a NumPy-1.x effect alone:** NumPy 1.26.2 on Linux gives int64. The remaining explanation is the Windows platform default (C `long`, 32-bit, under NumPy < 2) — consistent with the evidence but **not tested on Windows**.
3. **The PC-vs-Linux float differences (max 1.7e-14 absolute, max 1.2e-13 relative, 0.2–1.2 % of values) remain unexplained.** Candidates not separable with the available evidence: Windows vs Linux math library, CPU microarchitecture, Python 3.12.6 vs 3.12.3, and the **code changes since the PC store was written** (old code not run). A run of the code as of the store's creation (for example rebuilt from an earlier commit by `git archive`, then uploaded) on this host would separate code from OS/CPU.
4. **Discrete outcomes are identical everywhere** (statuses, NaN positions, integer arrays, ledgers); numerical results agree far below any reported precision.

## Patch 1 assessment — **RECOMMENDATION ONLY; not approved, not implemented, hold retained**
- *Is explicit int64 enough?* It removes the (Windows-only, deterministic) dtype difference and is a no-op on Linux (already int64, same hashes there, verified by the unchanged `ba389730…`). It is **not enough for cross-environment hash equality**: with dtypes normalised, PC and Linux panels still differ by float drift.
- *Should strict manifest comparison stay?* Recommend **yes, unchanged**: on Linux it is measured to be stable across library versions, and a loud `OverwriteError` is the integrity-preserving behaviour. The only environments where it would misfire (PC Windows vs Colab) are, under the owner's Colab-only rule (OD-7), no longer producing project artifacts.
- *Manifest-schema change (Options B/C)?* **No evidence supports it.** Residual risk not measured: Colab CPU models vary between sessions; a cross-CPU drift test on Linux was not possible here.
- *Synthetic stores:* regenerate. The PC store cannot be re-ingested under current code regardless of dtype (new manifest keys `quality_report_sha256`, `reprice_err_*`, `solver_status_rejects`).
- *Suggested decision for the owner:* keep the hold and treat Patch 1 as **optional hygiene** (two explicit `dtype=np.int64` lines, zero effect on Colab results), to be applied only if Windows execution is ever expected again; otherwise close it as "not needed under Colab-only operation". The final choice is the owner's.

## Still open
Cause of the PC/Linux float drift (needs an older-commit run or a Windows run); PC Phase 2 JSON; behaviour across different Colab CPU models; the final archive was not used; KNOWN_LIMITATIONS L-34 (written before this evidence) still says dtype "inferred, not measured" and "P1 not run" — it needs a small correction in the next docs batch (not edited here).

---
# Addendum 11 — AP-012: final AP-004 archive, CPU suite, live-server probes, T4 suite (2026-10-20 UTC on the runtime clock / 2026-10-21 project date)
Authorized scope: engineering tests and API probes only (no research dataset/checkpoints, no data, no research inference/training). Earlier addenda are unchanged. **Deviation from the requested order:** the owner switched to a T4 runtime before the CPU run, and a runtime switch resets `/content` (a second upload). To avoid it, all three jobs ran on one **T4 machine**: the "CPU" suite with `CUDA_VISIBLE_DEVICES=` (GPU hidden), then the probes, then the same suite with the GPU visible. The T4 run also used `-v` (per-test names only; no semantic change).

## Archive and manifest — PASS
Uploaded by the owner (browser upload; the owner's upload also created `(1)`/`(2)` duplicate copies and an older patched archive, all unused; the duplicates hash identically). `worktree_ap004_final_2026-10-21.tar.gz` sha256 `d56b04bd5875a6199871b84f9fbdae2b1da9d5dbc1b460ce1c08808625db6236` = the full value recorded in SHARED_STATUS and equal to the hash of the local file; `MANIFEST_ap004_final.sha256` sha256 `96898744b04a86cd5b44604f3089ab28449b3ea8c9d0ac4c82f0072a80172efc` = recorded. Extracted into fresh `/content/ap012/tree`: 258 files; `sha256sum -c` **258 OK, 0 non-OK**. Source tree re-checked after the probes: 0 non-OK, 258 files, no file newer than the first check (excluding `__pycache__`).

## Runtime and dependencies
Ubuntu 24.04.4, Python 3.13.15, numpy 2.1.3, pandas 2.2.3, scipy 1.16.3, pyarrow 23.0.1, torch 2.11.0+cu130 (CUDA 13.0), Tesla T4 (driver 580.82.07, 15,360 MiB), 2 CPUs (Intel Xeon @ 2.00GHz).

## CPU backend suite (GPU hidden) — PASS
`cd backend && CUDA_VISIBLE_DEVICES= PYTHONPATH=src python -W error::ResourceWarning -m unittest discover -s tests -t .` → **Ran 278 tests in 198.521s, OK (skipped=1), exit 0**; stderr merged into the log: no warnings or errors printed. (The skip is the GPU test, as expected with CUDA hidden.) Log: `/content/ap012/logs/suite_cpu.txt`.

## Live-server API probes (patched code, loopback, synthetic fixture) — PASS
Server: `PYTHONPATH=src python -m volatility_lab.api.server --root /content/ap012/probe_root --port 8765`, `127.0.0.1` only; fixture `r1/panel.npz` (zeros) plus `r1/tables/nonfinite.csv` (`nan`, `NaN`, `inf`, `-inf`, `Infinity`, `1e999`, `7`, `hello`, empty). Full transcript: `/content/ap012/logs/probe.txt`.
| Request | Observed |
|---|---|
| `HEAD /api/runs` (curl -I) | 405, `Allow: GET` |
| `OPTIONS /api/runs` | 405, `Allow: GET`, body `{"error": "read-only API"}` |
| `POST /api/runs` (extra) | 405, `Allow: GET` |
| `GET /api/runs`, `Host: evil.example` | **400** `{"error": "unexpected Host header"}` |
| `GET /api/runs`, loopback Host (control) | 200 `[{"id": "r1", "origin": "unlabelled", "description": ""}]` |
| `GET /api/runs/r1/tables/nonfinite` | **200**; `nan_lower, NaN_upper, pos_inf, neg_inf, word_inf, overflow` → `null`; `finite` → `7.0`; `text` → `"hello"`; `empty` → `""` (no HTTP 500) |
Shutdown: SIGTERM, process exit code **143**, port 8765 released (0 listeners), `server.log` empty (no traceback). The server has no graceful-shutdown handler, so "clean" here means no error output and the socket freed. These probes confirm on a live process what Addendum 7 covered with in-process sockets; the pre-patch 501/200/500 behaviour was recorded in Addenda 6–7.

## T4 GPU suite — PASS
GPU confirmed by `torch.cuda.is_available() True` (CUDA 13.0, Tesla T4). `cd backend && PYTHONPATH=src python -W error::ResourceWarning -m unittest discover -s tests -t . -v` → **Ran 278 tests in 207.126s, OK (no skips), exit 0**. `tests.unit.test_gpu_guard.GpuTrainingTests.test_both_architectures_train_predict_and_checkpoint_on_gpu` **executed and passed** (it is the test skipped in Addendum 7). One warning in the log, not an error: `neural.py:138 UserWarning: Converting a tensor with requires_grad=True to a scalar` (`tot += float(loss) * ...`; benign PyTorch notice; **not changed** under this authorization). `-W error::ResourceWarning` raised nothing. Log: `/content/ap012/logs/suite_gpu.txt`. This is a software plumbing test on synthetic data, not a research run.

## Still open (unchanged by this addendum)
UI null handling end to end, Playwright (AP-007), CI (never run), cross-environment float drift cause (OR-D9), P1/Patch 1 (closed by owner), scientific questions (AP-008), dataset/licence matters. The runtime's files (`/content/ap012/`) are not persistent; this addendum is the preserved record.

---
# Addendum 12 — AP-007: Playwright UI checks (read-only observation; 2026-10-21)
Authorized: install Playwright + headless Chromium in the Colab VM and run UI checks only. No data, no source edits (the source tree was re-checked afterwards: 258 files, 0 non-OK against `MANIFEST_ap004_final.sha256`). Same T4 runtime as Addendum 11, so the archive is the verified final AP-004 snapshot.

## Install and setup
`pip install playwright` → playwright 1.64.0 (+ pyee 14.0.0, greenlet 3.5.6), exit 0; `python -m playwright install --with-deps chromium` exit 0 (chromium-1248, headless shell, ffmpeg-1013; apt dependencies installed). Fixture: `scripts/make_synthetic_run.py --out /content/ap012/ui_store` (labelled SYNTHETIC, exit 0, run `65f3822c…1129`, origin "synthetic") plus `tables/nonfinite.csv` (nan, NaN, inf, -inf, Infinity, 1e999, 7, hello, empty) added to that run only. Viewer served by `volatility_lab.api.server --root …/datasets --port 8766` on 127.0.0.1; stopped by SIGTERM, 0 listeners afterwards. Check scripts live in `/content/ap012/ui/` (outside the source tree).

## Observations (headless Chromium 1280x900, all `#` links followed, 17 distinct routes)
| Check | Observed | Verdict |
|---|---|---|
| JS page errors / console errors / failed requests | none / none / none | no runtime errors on these routes |
| JSON `null` cells → UI | the `nonfinite` table renders `—` for nan, NaN, inf, -inf, Infinity and 1e999 cells, `7` for the finite cell, `hello` for text; literal "null", "undefined", "Infinity" as text: 0 | **PASS (table path)** |
| Surface view missing cells | explorer: 162 grid cells, 27 marked missing, no "NaN"/"undefined" text, no page errors | PASS for the synthetic run; not tested with a forecast containing nulls |
| "Live from run" label | present on 6 routes (overview 2, data 4, evaluation 1, experiments 1, artifacts 1, explorer 6) | **FAIL — misleading label still shown (L-33, GR-DATA-07)** |
| Withdrawn-dataset content | `dudesurfin`, `OptionsDX` and `Kaggle` appear on the data route; `Kaggle` also on evaluation, experiments, artifacts, limitations; "E-1" on home, overview, methodology, experiments | **FAIL — hard-coded withdrawn-dataset content still present** (some is labelled historical; not changed) |
| 3D | one `canvas.s3d` on the home route and one on the explorer route | **FAIL against DEC-008** (3D still shipped) |
Not evaluated: forecast views with null predictions, keyboard/accessibility behaviour, narrow viewports, other browsers, error states (server down), runs with real-shaped data. Screenshot of the last route: `/content/ap012/ui/shots/last.png` (runtime only).

## Gate effect
UI **null handling for tables and the surface heat map: PASS on synthetic fixtures** (evidence above). The "Live from run" label, withdrawn-dataset content and 3D removal remain **open defects awaiting the owner's UI ruling (Q-U1, Q-U2)**; nothing was edited. Playwright now has a working install procedure; full E2E journeys, CI and the other gates stay open.

---
# Addendum 13 — UI ruling verification: edited `frontend/index.html` under Playwright (2026-10-21; observation only, no source edits during verification)
Same Colab T4 runtime and synthetic fixture as Addendum 12. The owner uploaded the edited page; staged copy sha256 `dea15a53c9a4cb540c929b35743339800b9a14d2b714c958e669cd0eebcadddf` = expected (MATCH). It was served **without touching the source tree** via `create_server(..., frontend=Path('/content/ap012/ui_new/index.html'))` on 127.0.0.1:8767; the verified AP-004 tree's own `frontend/index.html` stayed at the original `425a37a2…f02c5` and the manifest re-check shows 0 non-OK files. Server stopped (0 listeners). A first attempt ran before the upload had reached the runtime (server answered 404); it was discarded, not recorded. Check scripts: `/content/ap012/ui/ui_check_new.py`, `ui_followup.py`, `ui_ctx.py` (runtime only).

| Requested check | Observed (17 routes crawled + targeted interactions) | Verdict |
|---|---|---|
| JavaScript / page errors | none; no console errors; no failed requests | PASS |
| "Live from run" labels | 0 on every route; the label now reads "Stored run data" (overview 2, data 4, evaluation 1, experiments 1, artifacts 1, explorer 6) | PASS |
| 3D canvas / rendering | 0 `canvas` elements on home, explorer and every crawled route; explorer tabs are `Heatmap`, `Table` | PASS (rendering). **Leftover text:** explorer still says "Select a cell in the heatmap, the 3D surface or by arrow keys."; limitations L-15 mentions 3D intentionally ("3D view was removed") |
| `dudesurfin`, `OptionsDX`, `Kaggle` | 0 on every route | PASS |
| E-1/E-2 clearly historical/withdrawn | evaluation, overview, data, experiments carry "Historical record / withdrawn (DEC-002)" labels, banner on the evaluation page, "(historical)" in the experiment list. **Not fully met:** (a) the home hero caption still reads "SPY end-of-day options, 2010 to 2023 · Backtest only" (my text replacement for it did not match); (b) the home page "Recorded in experiment E-1: neither neural architecture beat the persistence…" and "Experiment E-1 results" link carry no historical label; (c) "Completed, hosted dataset" (home flow, experiments) and "Upstream licence of hosted dataset" (home) still describe the withdrawn source as if current; (d) methodology says "the documented E-1 run uses 6 tenors by 9 nodes" without a label | **PARTIAL — FAIL for (a)–(c); (d) minor** |
| Null cells | `nonfinite` table: nan, NaN, inf, -inf, Infinity, overflow, empty cells render `—`, finite 7, text hello; no literal "null"/"undefined"/"Infinity" | PASS |
| Heatmap and Table tabs; keyboard | default tab Heatmap; ArrowRight from Heatmap → Table (7 table rows = header + 6 tenors); ArrowRight again wraps → Heatmap; ArrowLeft → Table; URL hash updates to `view=table`; mouse click on Table and back to Heatmap works (216 heatmap cells, 36 missing, across the four grids on the page) | PASS |
| Legacy `?view=3d` | via hash change and via a fresh page load of `#/workbench/explorer?view=3d`: selected tab = Heatmap, 0 canvases | PASS |

**Gate effect.** Q-U1 (label) and the 3D removal (DEC-008) are verified on this synthetic run. Q-U2 (withdrawn-dataset content) is **not closed**: identifiers are gone, but items (a)–(c) above remain and need a further owner-authorized edit (not patched under this verification task). Not covered: forecast views with null predictions, narrow viewports, other browsers, server-down state, keyboard use of the heatmap grid, accessibility audit; CI not run. No data, SPY artifact, research inference or training was touched.

---
# Addendum 14 — AP-007 independent re-run of the edited `frontend/index.html` (`dea15a53…`): source greps, network, port release (2026-10-21; observation only)
Same Colab T4 runtime and synthetic run as Addenda 12–13; fresh scripts `/content/ap007b/{serve,check}.py` (runtime only; written outside the source tree). Page served from `/content/index.html`, full sha256 `dea15a53c9a4cb540c929b35743339800b9a14d2b714c958e669cd0eebcadddf` = expected (MATCH, 98,888 bytes), via `create_server(..., frontend=...)` on 127.0.0.1:8768 (verified AP-004 tree untouched). No source edit, no data, no research inference/training. This re-run **confirms Addendum 13** (17 routes crawled; same results) and adds the checks below that 13 did not record.
| Check | Observed | Verdict |
|---|---|---|
| Page/console errors, failed requests | 0 / 0 / 0 | PASS |
| Source greps (executable text, not just rendered) | `Live from run` 0, `dudesurfin` 0, `OptionsDX` 0, `Kaggle` 0, `s3d` 0, `WebGL` 0, `getContext` 0, `three` 0, `Rotate` 0. `canvas` 1 hit = CSS keyword `CanvasText` in a forced-colors rule (not a canvas) | PASS |
| Rendered 3D | 0 `<canvas>` on every route; explorer tabs `Heatmap` (selected), `Table` | PASS |
| Network | requests only to `/`, `/api/runs`, `/api/runs/<id>`, `…/surface/59`, `…/forecasts/persistence/59`, `…/tables/{nonfinite,persistence_by_tenor}` plus `/?view=3d`; **0 external requests** | PASS |
| Keyboard | focus on Table tab, ArrowLeft → Heatmap selected and focused (216 heat cells); ArrowRight → Table selected and focused, table rendered | PASS |
| Table tab / nulls | 7 table rows, 9 cells `—`; none of NaN/undefined/null/Infinity in the panel | PASS |
| Legacy `view=3d` | hash change, `/?view=3d#/workbench/explorer` (query string) and fresh load of `#/workbench/explorer?view=3d`: Heatmap selected, 216 cells, 0 canvas; URL rewritten to `view=heatmap` | PASS |
| Server shutdown | SIGTERM, exit −15, 0 listeners on 8768, log only `serving ('127.0.0.1', 8768)` | PASS |
| E-1/E-2 labelling | **Same open items as Addendum 13 (a)–(d)**: home pull-quote "Recorded in experiment E-1…" and "Experiment E-1/E-2 results" links unlabelled; methodology "documented E-1 run" unlabelled; explorer/limitations still say "3D" (text only). Overview, data, experiments, evaluation carry historical/withdrawn labels | **PARTIAL — unchanged; fix pending (decision-closure session owns the five text edits)** |
Any later edit to `index.html` changes its hash; the checks above apply only to `dea15a53…` and must be re-run on the new hash. Not covered: forecast views with null predictions, narrow viewports, other browsers, server-down state, CI.

---
# Addendum 15 — UI leftovers fixed and re-verified: `frontend/index.html` sha256 `33fdd70fa3e3cfc13798f55bf05f3ec7cc412c5971afcc1e1e6d2c02c068c4cf` (2026-10-21)
Supersedes the page-level verdicts of Addenda 13–14, which cover the earlier page `dea15a53…` only. Owner-approved text edits (chat): home hero caption, unlabelled E-1 pull-quote, "hosted dataset" phrases, explorer "3D surface" hint, methodology "documented E-1 run", plus "(historical)" on the E-1/E-2 docs links. Pre-image of this step: `orchestration/patches/pre/index.html.pre-ui-leftovers-2026-10-21`. Only `frontend/index.html` changed (`git diff --stat`: 33 insertions, 162 deletions against the working tree's previous state). Staged in Colab at `/content/ap012/ui_new2/index.html` (99,028 bytes), hash MATCH; served through `create_server(frontend=...)` on 127.0.0.1:8769 (this run) and 8768 (independent run by the "UI verification" session); the verified tree's own `index.html` was not touched (manifest re-check: 0 non-OK). Servers stopped, 0 listeners.

## Run A (decision-closure session; `ui_check_new2.py`, 17 routes, synthetic run)
| Check | Result |
|---|---|
| JS/page errors, console errors, failed requests | 0 / 0 / 0 — **PASS** |
| "Live from run" | 0 on every route — **PASS** |
| `canvas` / 3D | 0 on every route; explorer tabs `Heatmap`, `Table`; `?view=3d` falls back to Heatmap (hash change) — **PASS** |
| `dudesurfin`, `OptionsDX`, `Kaggle` | 0 on every route — **PASS** |
| Null cells | explorer table 7 rows; heatmap 216 cells, 36 missing; (table fixture rendering unchanged, see Addendum 12/13 and Run B) — **PASS** |
| E-1/E-2/SPY/hosted labelling (script flags a mention whose own line has no historical/withdrawn/DEC-00x/synthetic/unavailable word) | 28 labelled mentions; 5 flagged lines remain: overview link text "Read E-1 figures"; data-page pipeline step name "Hosted files" (inside a panel titled "Transformation history (historical E-1 run)"); document title "Hosted dataset assessment"; limitation L-23 "SPY options are American-style…" (a methodological limitation, not a data claim); experiments row note "Tested one hypothesis from E-1" (its row name carries "(historical)") — **PASS with minor residuals** |

## Run B (independent; "Neural Volatility Surface UI verification" session, port 8768, scripts `/content/ap007b/{serve2,check2}.py`, results `/content/ap007b/result2.json`; reported by message, attributed, not re-executed by me)
0 page errors/console errors/failed requests; "Live from run" 0 in source and routes; 0 `<canvas>` (source has no s3d/WebGL/getContext/three/Rotate); the "the 3D surface" hint is gone; "3D" text only on methodology/limitations (L-15 says "removed"); identifiers 0; `nonfinite` table → `—` for nan/NaN/inf/-inf/Infinity/overflow/empty, `7`, `hello`, no NaN/undefined/null/Infinity text; ArrowLeft/ArrowRight switch tabs with focus (Table rendered); `?view=3d` via hash, `/?view=3d#…` and fresh load → Heatmap selected, 216 cells, URL rewritten to `view=heatmap`; requests only to the local server (0 external); SIGTERM exit -15, 0 listeners. Its labelling heuristic (±2 rendered lines) flagged only: "Read E-1 figures", the document title "Hosted dataset assessment", and generic "Dataset version" field names.

## Verdict and residuals
**UI ruling: PASS on synthetic fixtures** (label, 3D, errors, identifiers, null cells, tabs/keyboard, legacy URL, labelling of E-1/E-2/hosted content). **Minor residuals, left unedited (not owner-requested):** the link text "Read E-1 figures", the document title "Hosted dataset assessment", step name "Hosted files". Not covered: forecast views with null predictions, narrow viewports, other browsers, server-down state, accessibility audit, a real-shaped run; CI not run. No data, SPY artifact, research inference or training; nothing committed or pushed.


---
# Addendum 16 — AP-007: Playwright re-check of the CURRENT `frontend/index.html`, sha256 `783c27a99b5040e18f523421a6b45685849510b216031670734106b6de29dc5a` (2026-10-21 project date; runtime clock 2026-10-20 21:05–21:06 UTC; observation only)
Supersedes the page-level verdicts of Addendum 15 for the **current** page; Addendum 15 remains the record for `33fdd70f…`. Operated by the Manager of the multi-agent master run (Colab T4 runtime, Python 3.13.15, playwright 1.64.0, numpy 2.1.3; same runtime and synthetic run `65f3822c…1129` as Addenda 12–15).

## Artifact identity
| Step | Evidence |
|---|---|
| Edit applied locally | `frontend/index.html` is 99,102 bytes, sha256 `783c27a9…29dc5a` (recomputed locally 2026-10-21; pre-image `orchestration/patches/pre/index.html.pre-ui-residuals-2026-10-21` = `33fdd70f…c068c4cf`, verified by local `sha256sum`). Local diff vs the pre-image (CRLF-normalised) = exactly three label strings: "Hosted dataset assessment" → "Withdrawn hosted dataset assessment (historical)"; "Read E-1 figures" → "Read historical E-1 figures (withdrawn dataset)"; "Hosted files" → "Hosted files (withdrawn dataset)". |
| Transfer | **Not uploaded as a file.** The staged Addendum 15 copy (`/content/ap012/ui_new2/index.html`, sha256 `33fdd70f…` re-verified in the runtime) was transformed in Colab by those three exact single-occurrence byte replacements into `/content/ap012/ui_new4/index.html`; every replacement asserted exactly one match. Resulting sha256 = `783c27a99b5040e18f523421a6b45685849510b216031670734106b6de29dc5a`, 99,102 bytes = the local file (**MATCH**). Identity rests on the hash equality, not on a byte-for-byte upload of the local file. |
| Served page | The live server's HTTP response body for `/` hashes to the same `783c27a9…` (served via `create_server(…, frontend=…)` on 127.0.0.1:8771; the verified AP-004 tree's own `frontend/index.html` was not touched; its manifest re-check: 0 non-OK of 258 against `MANIFEST_ap004_final.sha256`). |

## Procedure (existing conventions reused, only port/paths changed)
Run A = the Addendum 15 Run A script (`ui_check_new3.py` with port 8771 / `ui_new4`), Run B = the independent-run script (`/content/ap007b/check2.py` with port 8771 / `ui_new4`). Copies: `/content/ap012/ui4/{serve4,checkA,checkB}.py`; raw results `/content/ap012/ui4/ui_check_new4.json`, `result4B.json`, screenshot `explorer4B.png` (runtime only; this addendum is the preserved record). Both scripts exited 0 (17 routes each); server stopped by SIGTERM (exit −15), 0 listeners on 8771, server log only `serving on ('127.0.0.1', 8771)`.

## Results
| Check | Observed | Verdict |
|---|---|---|
| JS page errors / console errors / failed requests | none / none / none (Run A and Run B) | PASS |
| "Live from run" | 0 on every route, 0 in source; "Stored run data" 31 occurrences | PASS |
| 3D / canvas | 0 `<canvas>` on every route; source has no `s3d`, `WebGL`, `getContext`, `three`, `Rotate` (the single `canvas` source hit is the forced-colors CSS keyword, as in Addendum 14); "3D" text only on the limitations route (L-15 states the view was removed) | PASS |
| `?view=3d` fallback | hash change, `/?view=3d#…` and fresh load of `#/workbench/explorer?view=3d`: Heatmap selected, 216 cells, URL rewritten to `view=heatmap` | PASS |
| `dudesurfin`, `OptionsDX`, `Kaggle` | 0 on every route and in source | PASS |
| Null cells | `nonfinite` table: `nan`, `NaN`, `inf`, `-inf`, `Infinity`, `1e999`, empty → `—`; `7` and `hello` as written; explorer table 9 `—` cells, no NaN/undefined/null/Infinity text in the panel (Run B). Run A counted 3 occurrences of the string "NaN" across all routes; these are not inspected individually (inferred to be the fixture row label `NaN_upper`, not a cell value) | PASS (synthetic fixtures) |
| Heatmap/Table, keyboard | tabs `Heatmap` (selected), `Table`; ArrowLeft → Heatmap focused, ArrowRight → Table focused and rendered; 216 heat cells, 36 missing | PASS |
| Network | requests only to the local server; 0 external | PASS |
| E-1/E-2/SPY/hosted labelling (heuristics of Runs A and B) | The three residuals of Addendum 15 (link text "Read E-1 figures", document title "Hosted dataset assessment", step name "Hosted files") are no longer flagged. Remaining flags: L-23 "SPY options are American-style…" (methodological limitation); experiments row "Tested one hypothesis from E-1" (row name carries "(historical)"); the generic field name "Dataset version" and one methodology sentence containing "dataset" (heuristic false positives) | PASS with minor residuals |

## Verdict and limits
**UI check for the current page `783c27a9…`: PASS on synthetic fixtures; uploaded: no (reconstructed by hash-verified replacement); Playwright ran: yes; result recorded: yes (this addendum).** Not covered: forecast views with null predictions, narrow viewports, other browsers, server-down state, accessibility audit, a real-shaped run, human review (UA-01…UA-14), CI. No data, SPY artifact, research inference or training; no source file changed; nothing committed or pushed by this run. Any further edit to `frontend/index.html` changes the hash and voids this result for the new file.


---
# Addendum 17 — frontend-reading backend tests on the current page `783c27a9…` (2026-10-21 project date; runtime clock 2026-10-20 ~21:10 UTC; Colab T4 machine, GPU hidden)
Purpose: `frontend/index.html` changed after the archive tested in Addenda 7 and 11, and four backend test modules read or serve it. Agent E's local `sha256sum -c` of `MANIFEST_ap004_final.sha256` against the current tree (read-only, no code run) found 253 of 258 files matching; the 5 differing files are `CHANGELOG.md`, `decision.md`, `docs/engineering/CORE_STATUS.md`, `docs/research/KNOWN_LIMITATIONS.md` and `frontend/index.html`; **every file under `backend/src`, `backend/tests`, `scripts/` matched** (so the 278-test results cover the current source and tests byte-for-byte; the manifest excludes `orchestration/`, and `SPY_BASELINE_INVENTORY.md` is tracked but not in the manifest). Procedure: copy of the verified tree (`/content/ap012/tree_cur`) with `frontend/index.html` replaced by the staged `783c27a9…` file (hash re-verified), `cd backend && PYTHONPATH=src CUDA_VISIBLE_DEVICES= python -W error::ResourceWarning -m unittest -v tests.unit.test_viewer_static tests.unit.test_api_contract tests.unit.test_api tests.unit.test_api_edge_inputs`. Result: **Ran 40 tests in 4.604 s, OK, exit 0** (no skips shown). Scope: these 40 tests only, not the full suite; a full-suite rerun was not judged necessary because no source or test file changed since the 278-test runs. No data, no research inference or training.

---
# Addendum 18 — AP-018: backend and spike suites on the CURRENT working tree (2026-10-21; Colab **CPU** runtime; owner could not use a T4)
Authorized by the owner in chat: upload the current tree, verify hashes, run the backend suite and the spike tests, record the result; no data, no research inference or training. This is the first run covering the tree as it stands after the later edits (Addenda 7 and 11 covered archive `d56b04bd…`).

## Artifact identity
Built locally by `git ls-files -co --exclude-standard` minus `orchestration/` (261 files; includes the new `storage/quote_store.py` and `tests/unit/test_quote_store.py`, the modified `config/settings.py`, `ingestion/optionsdx.py`, `validation/quotes.py`, and `frontend/index.html` `783c27a9…`). `worktree_current_2026-10-21.tar.gz` sha256 `beb9cf4b56a3337bac1ead19adb4d44141971e3a86b2ea88b522deb58aa36df9` = the value computed locally (**MATCH** in Colab; 261 files extracted into a fresh `/content/ap018/tree`). `MANIFEST_current.sha256` (`26bad089…5c39`) was **not uploaded**, so the per-file `sha256sum -c` check was **NOT RUN**; identity rests on the archive hash alone. Archive, manifest and file list are in `orchestration/colab_transfer/` (not committed).

## Runtime
Ubuntu 24.04.5, Python 3.13.16, numpy 2.1.3, pandas 2.2.3, scipy 1.16.3, pyarrow 23.0.1, torch 2.11.0+cpu, `cuda_available False`, 2 CPUs. No GPU (T4 not used).

## Backend suite — **FAIL (1 failure, 1 skip)**
`cd backend && CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -W error::ResourceWarning -m unittest discover -s tests -t .` → **Ran 291 tests in 322.020s — FAILED (failures=1, skipped=1), exit 1**; 0 "Warning" lines in the log; run concurrently with the spike suite on 2 CPUs.
- **The failure:** `tests.unit.test_quote_store.QuoteStoreTests.test_config_hash_does_not_include_the_quote_policy` (`test_quote_store.py:87`): `assertNotIn("quote", json.dumps(Config().to_dict()).lower())` fails because the config JSON contains the existing key `SurfaceConfig.min_quotes_per_slice` (`config/settings.py:42`). The preceding assertion in the same test (line 86: `Config` fields are exactly data/surface/features/split/train) is not reported as failing. Reading: the new, untracked test's substring check is broader than its intent (the quote policy is not hashed into `Config`), so it cannot pass against the unchanged config key. This is a diagnosis from the traceback and source, not a separate run. **Not patched** (no source or test edits under this authorization); the owner/core session decides whether to narrow the assertion.
- **The skip (1):** the run did not use `-v`, so the skipped test is not named in the log; expected to be the GPU plumbing test (`test_gpu_guard`), but **not confirmed**.
- Net: 289 passed, 1 failed, 1 skipped of 291. The 278 OK of Addenda 7/11 is **not** the state of the current tree.

## Spike suite — PASS
`cd scripts/phase0_synthetic && PYTHONDONTWRITEBYTECODE=1 python -W error::ResourceWarning -m unittest discover -s tests -t .` → **Ran 145 tests in 65.848s, OK**, exit 0 (matches the 145 recorded earlier).

## UI shown to the owner
At the owner's request the viewer was served inside the Colab tab (`google.colab.output.serve_kernel_port_as_iframe`, port 8780) from the extracted tree: page sha256 `783c27a9…` (same as Addendum 16), labelled synthetic run `65f3822c…1129`, plus the `nonfinite` fixture table. `/` returned 200 and `/api/runs` listed the one synthetic run. No new Playwright run was made on this tree.

## Not run / still open
Per-file manifest check; T4 run (GPU plumbing test unverified for the current tree); `python -O` leakage guards; foundation audit; live-server API probes on this tree; CI. No data, SPY artifact, research inference or training; no source or test edited; nothing committed or pushed.
