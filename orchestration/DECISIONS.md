# DECISIONS — orchestration view

Canonical decision register is [decision.md](../decision.md); this file only records what the **owner stated for the orchestration run** and the open items agents must not pre-empt. Do not copy decision text here; link.

## Owner-stated (master prompt, 2026-10-20; not yet reflected in decision.md → AP-006)
| ID | Statement | Relation to canonical record |
|---|---|---|
| OD-1 | Local research tool only | Matches CORE_STATUS §8 (DEC-007/008/013 scope decision, 2026-10-20) |
| OD-2 | Support both US and Indian options markets | **New / broader than** DEC-001 (SPY proposed). Not yet in decision.md; treat as separate studies (see Agent D) |
| OD-3 | Prefer free data sources | New; compare DEC-002 (provider) which is `PROPOSED` Cboe DataShop (paid) |
| OD-4 | Prefer raw quotes + underlying prices; build own surfaces | Consistent with current architecture (ingestion → IV → surfaces) |
| OD-5 | Calendar days / 365 | Matches DEC-005 closure (CORE_STATUS §8) |
| OD-6 | Do not use the withdrawn hosted dataset | Matches DEC-002 withdrawal 2026-10-20 |
| OD-7 | All project code executes only in Google Colab, never on the PC | New operating rule; earlier docs record PC runs (historical, now not to be repeated) |
| OD-8 | No data acquisition / training without explicit authorization | Matches DATA_ACQUISITION_AUTHORIZATION |

## Unresolved (do not decide without owner; see decision.md)
Provider/licence per market (DEC-001/002/003 replacement), DEC-004 (pricing model detail), DEC-009–012, software licence DEC-014, toolchain DEC-015 (Colab-only execution interacts with this), whether GR-MOD-01 becomes mandatory, Cboe inquiry send/edit. New: **is Colab acceptable as the CI-equivalent for release gates?** (S7).

## Owner decisions recorded 2026-10-21 (decision-closure prompt; documentation only)
Each row: **policy** (owner-approved in chat) · evidence · implementation status · outstanding verification · future approval. Nothing here acquires data, trains, runs inference or changes code. Canonical `decision.md` is **not** edited (AP-006 still pending); these are the orchestration record.

| ID | Policy | Evidence | Implementation | Outstanding | Future approval |
|---|---|---|---|---|---|
| OR-D1 | **Modular multi-source data strategy**, SPY set kept as the research baseline *reference*. Candidate roles and combination rules below | reports/DATA_SOURCE_RESEARCH, INDEPENDENT_REVIEW corr. 3 | **Planned only.** No adapter, manifest-schema change or pipeline built | All source licences/terms | Per-source acquisition (AP-002a/b); pipeline build; any manifest-schema change |
| OR-D2 | **Preserve SPY models, checkpoints, preprocessing, results, configs. New data never auto-triggers retraining.** Evaluate the frozen model on suitable new data first where valid; retrain only if comparable, valid evaluation shows meaningful deterioration, and only after explicit approval. Cross-market (e.g. NSE) evaluation of a SPY-trained model is **unsupported** until compatibility is shown | [SPY_BASELINE_INVENTORY](../docs/research/SPY_BASELINE_INVENTORY.md) | Policy recorded; inventory written | Dataset full hash and checkpoints are **not in the repo** (Kaggle account only); nothing re-verified | AP-003 (training) stays NOT REQUESTED; any evaluation run needs its own authorization |
| OR-D3 | **Scoring conventions preserved:** calendar days/365 (DEC-005), chronological evaluation, simple baselines retained, label semantics (fixed vs nearest expiry) stated, no cross-label/period comparisons, H-series labelled exploratory, no new thresholds. **600-origin rationale: unresolved** (documented only as a floor, PHASE0_FEASIBILITY_PLAN M3/M4) | DEC-005; PHASE4 review; reports/RESEARCH_DESIGN | Already in code/docs; no change | Fixed vs nearest primary scoring (AP-008); multiplicity/effect size | AP-008 owner decision |
| OR-D4 | **UI:** local research dashboard only; no implied live connectivity; fix "Live from run" (`frontend/index.html:317`, L-33, GR-DATA-07); replace hard-coded withdrawn-dataset content (E-1 panels, source identity, hero text); stay 2D (DEC-008; 3D still present at `index.html:545,734,755` → removal task); non-finite cells = JSON `null` per API_CONTRACTS §8 | reports/UI_INTEGRATION_REPORT; COLAB_VERIFICATION Addendum 7 | **Not implemented** (UI session) | **End-to-end null handling in the UI: unverified** (API side verified, Colab 278 OK); live-server HTTP probes, Playwright E2E (AP-007), CI: not done | UI session launch; AP-007 |
| OR-D5 | **Manifest / run key:** Patch 1 (dtype/manifest) closed by owner 2026-10-21 (AP-004) — strict manifest comparison unchanged, no schema change, no dataset regeneration to hide drift; AP-004 `run_key.json` fail-closed policy preserved (missing/malformed/incompatible key never reuses stale predictions nor overwrites results) | AP-004_PROPOSAL; reports/COLAB_VERIFICATION Addenda 7–10 | Patches 2–4 applied and Colab-verified (278 OK, 1 skipped); Patch 1 not applied | Float drift PC↔Linux (max 1.7e-14) unexplained; older-commit run and other CPU models not run; L-34 wording | Any drift fix is a new owner decision |
| OR-D6 | **Release:** local research tool; no hosting, hosted demo, public data access or redistribution of data/derived artifacts. A future release needs a separate decision plus licence review (data terms, public display, checkpoints/artifacts, dependency licences, local-API exposure, cost/access controls) | DEC-013, OD-1 | Policy recorded; nothing deployed | DEC-014 software licence open | New explicit decision + licence review |

**Conflict flagged, not resolved:** the instruction keeps the SPY dataset as the *primary research baseline*, while DEC-002 (2026-10-20) withdrew it from any further run, display or export and OD-6 says not to use it. Recorded reconciliation: "preserve" = never delete or overwrite artifacts; **use remains not authorized** until the owner lifts DEC-002 after a licence resolution (the instruction's own "unverified → unresolved" rule points the same way).

### OR-D1 candidate source roles (none acquired; none cleared for the intended use)
| Source | Intended role | Not to be described as | Open questions |
|---|---|---|---|
| Existing SPY set (Kaggle/OptionsDX) | Baseline reference for preserved results | Cleared or reacquirable | Upstream licence UNRESOLVED; full hash not recorded |
| Yahoo Finance (`yfinance`) | Underlying price history, market context | A historical options bid/ask source | Research-use terms not verified by F |
| Cboe DataShop / exchange data | Possible US options quotes | Free (separate free samples from paid products) | Access, price, coverage, licence; Cboe inquiry drafted, unsent |
| NSE reports / bhavcopy | Indian derivatives fields | Complete historical option bid/ask | Terms page never loaded (ban rests on a search excerpt); close/settlement only |
| Broker / market-data APIs | Optional future gap-filling | — | History depth, free-tier and rate limits, auth, research-use and redistribution terms (Alpaca/Tradier/IBKR/Databento not re-verified) |

Marketdata.app Free (B's best free candidate) stays `NEEDS_APPROVAL` (possible "professional use" exclusion).

### OR-D1 combination rules (planned; to be enforced by a future adapter layer, not built)
Never concatenate raw datasets blindly. Require: stable source and instrument identifiers; one timestamp/timezone convention; explicit option type, strike, expiry, underlying and quote-field semantics; units and currency; bid, ask, mid, last and underlying kept separate; duplicate and source-precedence rules; missing-value and stale-quote policy; point-in-time correctness (no look-ahead); provenance per ingested file. **Underlying prices never substitute for missing option quotes.** Direction: small source adapters → normalized internal schema → lightweight manifest (source, coverage, schema version, licence status, file hashes) → selective loading by date range → local caching; no database, streaming or orchestration service.

### OR-D2 future evaluation sequence (separately authorized; not started)
1 verify new data licence/provenance/schema/quality/compatibility → 2 freeze and identify baseline artifacts → 3 confirm feature, preprocessing and target compatibility → 4 time-aware protocol without leakage → 5 compare like-for-like metrics with simple benchmarks → 6 attribute any decline (new data vs schema change, missing fields, regime, evaluation mismatch) → 7 report evidence and proposed response → 8 request explicit approval before any retraining.

## Recorded 2026-10-21 (resume prompt): DEC-002 amendment and gate backlog
| ID | Policy | Status |
|---|---|---|
| OR-D7 | **Personal local research project.** No licence purchase, paid subscription or real-time feed is a prerequisite for documentation, engineering, reproducibility work or planning; no spending, no new data acquisition. **DEC-002 handled by append-only amendment DEC-002-A in [decision.md](../decision.md)**: private local-only, Colab-executed use of the already-held SPY artifacts permitted in principle (each run separately authorized); results shown only on the owner's machine with an "upstream licence unverified" label. **Remaining restriction:** no export/redistribution/publication/public display, no hosting, no new or replacement dataset, upstream terms still unverified. Wording confirmed by the owner 2026-10-21 (AP-011). Supersedes the "use not authorized" wording in the 2026-10-21 conflict note above (history kept). | CONFIRMED (owner, 2026-10-21); no run authorized by it |
| OR-D8 | **Patch 1 discrepancy:** the resume prompt calls Patch 1 "on hold"; the recorded owner decision (AP-004 D-1, 2026-10-21) is **closed, not needed under Colab-only operation, never implemented**. The recorded state governs; reopening needs a new owner decision (e.g. Windows execution expected again). | RECORDED |
| OR-D9 | **Float drift (≈1.7e-14 abs, 1.2e-13 rel, 0.2–1.2 % of values, PC vs Linux) = UNRESOLVED, informational.** Evidence: statuses, NaN masks, integer arrays and ledgers identical; library versions excluded (Addendum 10); cause (Windows vs Linux math, CPU, code changes since the PC store) not separated. It affects bit-exact hash identity across machines only, not reported results at any reported precision; this is a reading of the evidence, not a measured proof for downstream metrics. | UNRESOLVED |

### Outstanding gates, in priority order (each lists the evidence that closes it)
| # | Gate | Where it runs | Closing evidence | Status |
|---|---|---|---|---|
| 1 | Patched live-server API probes (HEAD/OPTIONS 405, foreign Host, non-finite → JSON `null`) | Colab (CPU) | P2 re-run on the final AP-004 archive: output of each curl with status codes; plus a run dir whose CSV has a `nan` cell returning 200 with `null` | **PASS 2026-10-21, AP-012 (COLAB_VERIFICATION Addendum 11)**: 405/405/400/200-with-null observed on a live loopback server |
| 2 | GPU plumbing test on the patched snapshot | Colab T4 | `test_gpu_guard` executes (not skipped) and passes; device/CUDA versions printed | **PASS 2026-10-21, AP-012 (Addendum 11)**: executed on a T4, 278 OK, no skips |
| 3 | UI null handling and label fixes (Q-U1–U3) | UI session edit, then Colab Playwright (AP-007) | Playwright run showing no "Live from run", no withdrawn-dataset hard-codes unlabeled, `null` cells rendered safely, no 3D | **UPDATE (Addendum 13, after the owner's UI edit): label and 3D removal VERIFIED, null cells still PASS, withdrawn-dataset cleanup PARTIAL (a few unlabelled mentions remain).** Earlier observation: **PARTLY OBSERVED 2026-10-21 (AP-007, Addendum 12):** null cells render `—` (PASS, synthetic); "Live from run" on 6 routes, withdrawn-dataset content and 3D still present (FAIL, unedited, awaiting owner ruling) |
| 4 | CI | GitHub runner | first green run of `tests.yml` | NOT RUN; requires owner push (AP-005) |
| 5 | Drift cause | Colab | run of code at the PC store's commit via `git archive` on the same host, and ≥1 other CPU model | OPTIONAL, UNRESOLVED (OR-D9) |
| 6 | Scientific open items (fixed vs nearest primary label, 600-origin rationale, multiplicity) | owner decision, no experiment | AP-008 answer | UNRESOLVED; no justification manufactured |
| 7 | Docs batch (A's contradictions, `tests.yml:3` wording) | local edit | diff reviewed | QUEUED |
Not gates but blockers to *new* work: source licences (AP-002a) and any new data (not needed to continue engineering).

## Orchestration-level decisions made by ORCH (reversible)
| ID | Decision | Reason |
|---|---|---|
| OR-1 | Thin `orchestration/` layer; reuse CORE_STATUS/IMPLEMENTATION_PLAN as canonical status | Avoid contradictory duplicates |
| OR-2 | Wave 1 agents are report-only; C and E propose diffs, no code edits | No verified Colab runtime → no change can be validated |
| OR-3 | AgentReach not used for coordination | Its description is internet research, not agent comms |
