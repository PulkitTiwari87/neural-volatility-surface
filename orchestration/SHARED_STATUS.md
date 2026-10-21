# SHARED_STATUS — orchestration state

**Updated:** 2026-10-20 (Wave 1 launch) · **Owner of this file:** Master Orchestrator only. Agents report via their own `reports/*.md`; the orchestrator integrates.
**Canonical phase state is NOT duplicated here** — see [CORE_STATUS](../docs/engineering/CORE_STATUS.md), [IMPLEMENTATION_PLAN](../IMPLEMENTATION_PLAN.md), [decision.md](../decision.md), [MODEL_STATUS.json](../docs/engineering/MODEL_STATUS.json). This file holds only coordination state.

## Starting state (observed 2026-10-20, Windows, branch `main`)
- Git HEAD `306c01b` ("finishing all the training of models H1-H6"); **44 uncommitted paths** (28 modified, 16 untracked — owner's work, preserved; no Git write is permitted to any agent).
- Project is documentation + research package + stdlib API + static 2D viewer; every phase gate is **unmet** (Phase F accepted by owner 2026-10-19). Real-data track **BLOCKED** (hosted dataset withdrawn 2026-10-20; no replacement authorized).
- Test totals in the docs are the owner-session's *local PC* runs (252 OK/1 skipped on 2026-10-20). **None has been re-run in Colab**; CI workflow exists but has never run.
- No pre-existing `orchestration/`, `AGENTS.md`, or `.claude/` agent definitions. Existing coordination channel = repo files (CORE_STATUS §1).

## Execution environment
- Rule (owner): project code runs **only in Google Colab**. Local = read/edit only.
- Colab: `colab-mcp` server present with one tool `open_colab_browser_connection` (more tools unlock after a browser connection). **Connection status: see "Colab" below.**

### Colab
**Connected** (orchestrator, `open_colab_browser_connection` → true, 2026-10-20). Runtime observed: Python 3.13.15, numpy 2.1.3, pandas 2.2.3, scipy 1.16.3, pyarrow 23.0.1, torch 2.11.0+cu130, Tesla T4. (Differs from the PC stack in CORE_STATUS — results are a new, separate data point.) Only an environment-info cell has run; **no project code has run anywhere in this orchestration.**
**Working-tree transfer:** the archive of the exact tree (tracked + untracked non-ignored, 255 files, excludes `orchestration/`) is at `orchestration/colab_transfer/` (`worktree_2026-10-20.tar.gz` sha256 `0d5835e2…d4cb71`, `MANIFEST.sha256` sha256 `82a8de14…2bfd`; HEAD `306c01b`, 45 `git status` entries at archive time). Pushing it through the cell API would cost ~100k+ tokens, so **it needs one manual owner step: run Colab cell 2 (upload both files)**; cell 3 then runs the backend suite. Status: `BLOCKED — AWAITING OWNER UPLOAD`. Do not commit the `colab_transfer/` folder. [Update 2026-10-21: superseded; uploads were done and hash-verified (COLAB_VERIFICATION Addenda 1-17, 258/258 manifest OK). This paragraph is history.]

## Wave 1 assignments (stage S1; all report-only, none edits product code)
| Task | Role | Owned file | Mode | Status |
|---|---|---|---|---|
| T-A1 | A Repo Auditor | reports/REPO_AUDIT.md | subagent | **READY_FOR_REVIEW** (static only; unverified until F). Key claims: no test ever run outside owner PC, CI never run; "252" may be a collected count (static `def test_` count = 252, 1 skipped → 251 executed); H1–H6 notebooks stale and still point at withdrawn dataset (`config/settings.py:17`); ~20 doc contradictions (e.g. CORE_STATUS:102 vs §8); re-ingest hazard: manifest byte-compare would raise OverwriteError on pre-2026-10-20 stores; new untracked modules are imported by tracked code (commit together) |
| T-B1 | B Data/Governance | reports/DATA_SOURCE_RESEARCH.md | subagent (web docs only) | **NEEDS_APPROVAL** (web facts dated 2026-10-20, unverified until F; NSE terms page never loaded—ban rests on a search excerpt; Databento terms unread). Claims: US—no free multi-year raw bid/ask found; best free candidate Marketdata.app Free (1 yr history, personal use, "derivative works" barred → needs written reply; pipeline test only, far below MVD ≥2,000 surfaces). India—no compliant free raw-quote source found; NSE bhavcopy is close/settlement only; recommend written query to NSE Data & Analytics, no acquisition now |
| T-C1 | C Engineering | reports/ENGINEERING_REPORT.md | subagent (proposals only) | **READY_FOR_REVIEW** (static; 16 findings, no S1 found, not proof none exist). Claims: C-01 neural resume cache can reuse another experiment's predictions (config hash omits flags); C-02 panel hash depends on platform int size (int32 PC vs int64 Colab, inferred not measured); C-03 byte-compare manifest may refuse cross-machine re-ingest (owner decision); C-06 `test_accessed_count==0` true by construction; C-05 NaN/inf CSV cell → API 500 |
| T-D1 | D Quant research | reports/RESEARCH_DESIGN.md | subagent | **READY_FOR_REVIEW** (static; unverified until F). Key claims: test years reused across 9 experiments so H1–H6 verdicts are exploratory; fixed vs nearest label flip is a benchmark problem (plain persistence wrong for rolling contracts); pass rule has no min effect size/uncertainty; 66 rule evaluations, no multiplicity accounting; neural comparison not interpretable; no look-ahead path found in code; owner-adopted 600-origin floor likely "underpowered in advance". Owner decisions requested: contract-level maturity-aware primary scoring (AP-008) |
| T-E1 | E UI/E2E | reports/UI_INTEGRATION_REPORT.md | subagent | **READY_FOR_REVIEW** (static only; claims unverified until F). Key claims: "Live from run" at frontend/index.html:317 (GR-DATA-07); viewer still hard-codes withdrawn-dataset E-1 results (needs owner decision); 3D shipped despite DEC-008; forecast views lack model/target/data-mode (API gaps G1/G2). Playwright-in-Colab E2E plan needs approval to install (AP-007) |
| T-F1 | F Independent reviewer | reports/INDEPENDENT_REVIEW.md | subagent, after A–E | **READY_FOR_REVIEW** — verdicts: A, B, C, D, E all **ACCEPT WITH CORRECTIONS** (below). Stage S1 is therefore `IN_REVIEW`, not `ACCEPTED` |

## Corrections applied from F (these supersede the claims in the per-agent rows above)
1. **Tests:** "252 OK" in the docs = 252 *discovered*; 251 passed + 1 skipped (CUDA, `test_gpu_guard.py:61`), owner PC only, never run in Colab/CI. `tests.yml:3` wording ("passed all 252") should be fixed (queued).
2. **C-02 (int dtype):** the claim that existing stores show `panel_hash_matches == false` is **wrong**; the real effect is re-ingest raising `OverwriteError`. The dtype fix and the manifest/`version_id` design (C-03) are **one owner decision**, sequenced first because it changes `panel_sha256` for every stored dataset. int32 on the PC panel is now observed (`panel.npz` is `<i4`).
3. **B:** Marketdata.app **does** give a per-row `updated` timestamp (B said none); `openInterest` is prior-session, `volume` full-day. New licence risk: the terms summary lists "research" under *professional* use, which may exclude the owner from the free tier — **owner must read the terms in a browser**. NSE terms page never loaded by B or F (scraping ban = search excerpt only). Indian brokers/Alpaca/Tradier/IBKR/Yahoo/Databento facts not re-verified by F.
4. **E:** 3D is built (`index.html:545,734,755`) but contradicts DEC-008 → present as an **owner ruling**, not a defect.
5. **D/H1–H6:** exploratory on a consumed test period and benchmark-dependent; do not call H4–H6 "pre-registered". D's M-02 roll-down causal wording is stronger than the evidence.
6. **"No S1 defect"** (C) and all patch behaviour are single-reviewer static readings; F did not read `bs.py`, `quotes.py`, `panel.py`, `neural.py`, `baselines.py`, `metrics.py` line by line. **Nothing has been executed.**
7. Overlapping proposals to merge before applying: manifest/dtype design; HEAD/OPTIONS 405 (C-11 vs E-P9f); `Config` flags vs `run_key`.

## Stage status after Wave 1
S0 IN_REVIEW · S1 **IN_REVIEW** (reports delivered and reviewed; nothing executed) · S2–S5 BLOCKED · S6 READY pending Colab upload + Playwright approval · S7 NOT_STARTED.

## Next recommended wave (Wave 2)
1. **Owner uploads the archive (Colab cell 2)** → orchestrator runs V-1 (backend suite, `-O` leakage, spike suite, foundation audit; C's probes P1–P4) → `reports/COLAB_VERIFICATION.md`. Highest value: converts "owner-PC transcription" into evidence.
2. Owner decisions (see APPROVALS): AP-002a send licence questions; AP-006/AP-008; 3D ruling and withdrawn-dataset content in the viewer; C-03 manifest design. [Update 2026-10-21: AP-008 is approved (OR-D10); this Wave 2 list is history.]
3. After V-1 and AP-004: apply merged C patches in order (dtype+manifest → run_key → API NaN → raw-store), one file owner at a time, re-verify in Colab. Docs fixes (A's table, `tests.yml:3`) as one last batch.
4. UI session launch (`prompts/S6_ui_e2e.md`) for E's UI-owned items after the owner rules on 3D and withdrawn-dataset display.

## Blockers / pending approvals
See [APPROVALS.md](APPROVALS.md). Real-data work needs owner approval; Colab needs a browser connection.

## Update 2026-10-21 — AP-004 (Patches 2–4 applied and verified in Colab; Patch 1 held)
- Local working tree: 4 source files edited, 3 new test files, 4 docs updated; no commit, no Git operation. Rollback: `orchestration/patches/` (pre-images + reverse diffs).
- Colab (CPU runtime, Python 3.13.16): red phase reproduced the findings on unpatched sources (non-finite CSV → HTTP 500; HEAD 501; foreign Host 200; stale resume reuse; store atomicity); green: targeted 5+6+15 OK; **full backend suite 278 OK, 1 skipped (GPU plumbing test: no GPU), exit 0**. See COLAB_VERIFICATION Addendum 7.
- Final archive for upload (if a fresh runtime needs it): `colab_transfer/worktree_ap004_final_2026-10-21.tar.gz` sha256 `d56b04bd5875a6199871b84f9fbdae2b1da9d5dbc1b460ce1c08808625db6236`, `MANIFEST_ap004_final.sha256` sha256 `96898744b04a86cd5b44604f3089ab28449b3ea8c9d0ac4c82f0072a80172efc` (258 files; differs from the tested archive in the 4 doc files only). Not committed.
- Stages unchanged: S0/S1 IN_REVIEW; S2–S5 BLOCKED; S6 ready pending Playwright approval; S7 not started. Remaining blockers: P1/NumPy 1.26/drift (needs Python 3.12 in Colab → Patch 1), data-source decisions (AP-002a), CI never run, GPU plumbing test not executed on the patched snapshot.

## Update 2026-10-21 (later) — P1/drift investigation, part 1+2 (Colab only; no source change; Patch 1 still HELD)
Measured: P1 on Linux/NumPy 2.1.3 gives int64 and is reproducible; the PC-written synthetic store has `<i4` for `n_quotes`/`tenor_days`; re-ingesting its raw CSV on Colab gives identical statuses/NaN masks/ledgers and floats equal to ~1e-13 relative, but a different `panel_sha256` even after int64 normalisation. NumPy 1.26 two-stack run is **blocked on an install approval** (`uv venv` + pinned wheels). Details: COLAB_VERIFICATION Addenda 8–9. Recommendation (not a decision) is in the chat reply; Patch 1 stays on hold.

## Update 2026-10-21 (decision closure; documentation only) — see DECISIONS OR-D1..OR-D6
Recorded: multi-source data strategy (planned only), SPY preservation / no automatic retraining, scoring conventions, UI and manifest directions, local-only release policy. **No** data acquired, no model trained, no inference or project test run, no code/test/schema/dataset/checkpoint touched, no Git operation. Path notes: AP-004 proposal is `orchestration/AP-004_PROPOSAL.md`; Colab verification is `orchestration/reports/COLAB_VERIFICATION.md`.
- **SPY artifacts:** inventory in [docs/research/SPY_BASELINE_INVENTORY.md](../docs/research/SPY_BASELINE_INVENTORY.md). The dataset and all 48 checkpoints / prediction files are **not in the repository or on this PC** (owner's Kaggle account, Colab runtime only); only hash prefixes are recorded. Dataset use stays withdrawn (DEC-002); "preserve" ≠ "authorized to use".
- **Gates, current status:** P1 / cross-environment drift — measured in Colab (Addenda 8–10), cause of PC↔Linux 1.7e-14 float drift **unexplained**, Patch 1 closed by owner, not applied · UI null handling end-to-end — **not verified** · live-server API probes, Playwright E2E, CI — **not run** · licence/provenance of any source — **unresolved** · 600-origin rationale — **unresolved** (AP-008) [Superseded 2026-10-21 by AP-008 / OR-D10: 600 = disclosed convention, not a power guarantee; AP-008 DECIDED; open specification items: numeric r*, fallback coverage threshold, N*, B0b / contract-level scoring implementation (Q-D2, Q-D3)] · release/hosting — **not authorized**.

## Update 2026-10-21 (resume; documentation only) — DEC-002-A and gate backlog (DECISIONS OR-D7–OR-D9)
DEC-002 amended append-only in decision.md (private local Colab use of the held SPY artifacts permitted in principle; no export/public display/hosting/new data/spend; upstream terms unverified; owner to confirm wording). Gate backlog with closing evidence is in DECISIONS. Next Colab task: patched live-server probe + full suite on the final AP-004 archive (CPU), then a T4 run for the GPU test. No code, test, dataset, checkpoint or manifest was touched; nothing run; no Git operation. SPY dataset/checkpoints remain **unverified and inaccessible from this session** (Kaggle account only).

## Update 2026-10-21 (AP-012 executed in Colab; see COLAB_VERIFICATION Addendum 11)
Final AP-004 archive verified (full sha256 `d56b04bd…db6236` MATCH; 258/258 manifest OK). On one T4 machine: backend suite with GPU hidden 278 OK, 1 skipped (exit 0); live loopback API probes PASS (HEAD/OPTIONS 405 `Allow: GET`, foreign Host 400, non-finite CSV cell → 200 with JSON `null`); suite with GPU visible 278 OK, **0 skipped — the GPU plumbing test executed and passed**. Closes gates 1 and 2 only. Still open: UI null handling and Playwright (AP-007), CI, drift cause, scientific items. No source/test/dataset changed; nothing committed.

## Update 2026-10-21 (AP-007 executed; COLAB_VERIFICATION Addendum 12)
Playwright 1.64.0 + Chromium installed in Colab; viewer checked against a synthetic run, observation only. PASS: JSON `null` cells render as `—`, no JS errors. FAIL (unedited, awaiting owner ruling): "Live from run" on 6 routes, withdrawn-dataset names (dudesurfin/OptionsDX/Kaggle, E-1) still in the viewer, 3D canvas still present on home and explorer. No source changed; no commit.

## Update 2026-10-21 (AP-018: current working tree run in Colab CPU; COLAB_VERIFICATION Addendum 18)
Archive `beb9cf4b…36df9` (261 files, current tree incl. new `quote_store`) uploaded and hash-matched; per-file manifest check not run (manifest not uploaded). Backend suite: **291 run, 1 failure, 1 skipped** (`test_quote_store…test_config_hash_does_not_include_the_quote_policy` — the assertion `"quote" not in Config json` collides with the existing key `min_quotes_per_slice`; not patched, owner/core to decide). Spike suite 145 OK. No T4 run, so the GPU plumbing test is unverified for this tree. The earlier "278 OK" does not describe the current tree. Nothing committed.

## Update 2026-10-21 (later still) — P1/NumPy 1.26 investigation complete (Colab only; Patch 1 still HELD, no decision recorded)
numpy 1.26.2 (venv `/content/v312`, Python 3.12.3) and numpy 2.1.3 give byte-identical panels and Phase 2 JSON on one Linux host; P1 identical (`ba389730…`, int64); PC-vs-Linux float drift (max 1.7e-14) not explained by library versions; recommendation in COLAB_VERIFICATION Addendum 10 and the AP-004_PROPOSAL evidence update. Open: older-commit run to separate code from OS/CPU, other Colab CPU models, KNOWN_LIMITATIONS L-34 wording. `/content/v312` pre-existed my install (provenance unknown); reinstalled and checked.

## Update 2026-10-21 (decision) — **Patch 1 (dtype/manifest) CLOSED by the owner**: not needed under Colab-only operation. No dtype change, strict manifest comparison kept, Options B/C not adopted; never implemented. AP-004 therefore ends with Patches 2, 3 and 4 applied and Colab-verified (278 tests, 1 skipped). Remaining open items: cause of the PC-vs-Linux float drift (informational only now), Colab CPU-model variance, data-source decisions (AP-002a), Playwright approval (AP-007), CI never run, the GPU plumbing test not executed on the patched snapshot. S0/S1 stay IN_REVIEW.

## Update 2026-10-21 (master run; Manager + agents D/E/R; execution ledger)
**Starting state:** branch `main`, HEAD `cd8d246` ("changes", the owner's commit 02:28 IST, 103 files); working tree clean. This supersedes "HEAD `306c01b` / 44 uncommitted" above (history kept). Nothing was committed, pushed or deployed by this run; no data acquired; no SPY artifact, training or research inference touched.
| Task | Owner | Status | Evidence |
|---|---|---|---|
| UI current-hash verification | Manager (Colab) | **PASS (synthetic fixtures)** for `frontend/index.html` `783c27a9…29dc5a` (99,102 B) | COLAB_VERIFICATION Addendum 16 (Runs A+B, 17 routes each; hash matched by replacement from the Addendum 15 copy, not file upload) |
| Frontend-reading backend tests on the current page | Manager (Colab) | **PASS**: 40 tests OK | Addendum 17 |
| Does the 278-test result cover current source? | Agent E (read-only provenance) | **Yes for backend/src, backend/tests, scripts/** (byte-identical to `MANIFEST_ap004_final.sha256`); 5 differing files are docs + frontend | Addendum 17 |
| Engineering static audit (C-01..C-16) | Agent E | no new demonstrable defect; open low items C-06, C-07, C-09, C-12, C-16 remain as recorded | agent E report (summarised in the final handover); source unchanged |
| CI workflow review | Agent E | header wording corrected only (252 = PC-era; 278 Colab); **CI NEVER RUN**, needs an owner push (AP-005) | `.github/workflows/tests.yml` header |
| Documentation reconciliation | Agent R | DEC-002-A confirmation status, L-33/L-36, CORE_STATUS §11, README/IMPLEMENTATION_PLAN/MILESTONES, CHANGELOG | git diff |
| Decision inventory | Agent D | see `reports/DECISION_INVENTORY.md` | file |
**Stage status:** unchanged (S0/S1 IN_REVIEW; S2–S5 BLOCKED; S6 PARTIAL — synthetic Playwright PASS, UA-01…14 not run; S7 not started, CI unrun).


## Update 2026-10-21 (AP-008 approved; documentation only)
The owner approved all three AP-008 parts (APPROVALS AP-008; decision.md "AP-008"; DECISIONS OR-D10). Earlier lines in this file calling the 600-origin rationale or AP-008 "unresolved" or "pending" (the Wave 2 recommendation and the OR-D3 gate summary) are history. Nothing was run: no pilot, evaluation, S-5, training, inference, data access or test; no code changed; no Git operation. Open specification items: numeric r*, fallback coverage threshold, N*, implementation of B0b / contract-level scoring (INTEGRATION_QUEUE Q-D2/Q-D3). Other approvals (AP-002a/b, AP-003, AP-005, AP-006, AP-009, AP-010) are unchanged.
