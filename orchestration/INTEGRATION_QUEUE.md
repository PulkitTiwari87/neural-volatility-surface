# INTEGRATION_QUEUE

Every proposed code/doc change is listed here before it touches the working tree. Rule: one file → one owner at a time; applied only after F review and owner approval (AP-004); executed verification only in Colab; no Git writes.

| ID | Source | Proposed change | Files | Conflict risk | Evidence | Review (F) | Decision | Applied | Colab-verified |
|---|---|---|---|---|---|---|---|---|---|
| Q-C01 | C | Add experiment flags to run key; canonicalise PCA SVD sign (C-01) | experiments/runner.py, models/* (+new test) | medium (owner-modified, uncommitted) | static | pending F | pending AP-004 | no | no |
| Q-C02 | C | Fix int dtype in panel (C-02) two-line + test | surfaces/grid.py (+new test) | medium | static; Colab probe P1 | pending F | pending AP-004 | no | no |
| Q-C05 | C | NaN/inf table cell handling in API (C-05) | api/service.py (+new test) | medium | static; probe P3 | pending F | pending AP-004 | no | no |
| Q-C04 | C | Crash-safe raw-store copy/mkdir (C-04) | storage/raw_store.py (+test) | medium | static | pending F | pending AP-004 | no | no |
| Q-C03 | C | Manifest compare design (C-03) | storage/raw_store.py | high | — | — | **closed with Patch 1 (owner 2026-10-21): strict comparison kept, no schema change** | no | no |
| Q-E (P1–P10) | E | UI fixes: rename "Live from run", status legend, notices, 3D removal etc. | frontend/index.html (UI session), API (core) | routed | static | pending F | UI session / owner | no | no |
| Q-A | A | ~20 doc contradictions (table in REPO_AUDIT §3) | README, IMPLEMENTATION_PLAN, CORE_STATUS, MILESTONES | high (shared docs, apply as one batch last) | static | pending F | pending | no | no |

## Wave 1 changes actually made to the working tree
Only new files under `orchestration/` (this directory). **No source, test, doc, or config file was modified by this run.** Verify with `git status`: expected = the 44 pre-existing entries + `orchestration/`.

## AP-004 outcome (2026-10-21)
| ID | Patch | Files | Status | Evidence |
|---|---|---|---|---|
| Q-C3 | C-04 raw-store atomicity | `storage/raw_store.py` + `test_store_atomicity.py` | **APPLIED, Colab-verified** (5 new tests red→green; full suite 278 OK/1 skipped) | COLAB_VERIFICATION Addendum 7 |
| Q-C4 | C-05 + C-11 API (null for non-finite, HEAD/OPTIONS 405, Host guard) | `api/service.py`, `api/server.py` + `test_api_edge_inputs.py` | **APPLIED, Colab-verified** (6 new tests red→green; HTTP 500 reproduced pre-fix) | Addendum 7 |
| Q-C2 | C-01 run_key guard (no PCA-sign change) | `experiments/runner.py` + `test_run_key.py` | **APPLIED, Colab-verified** with training stubbed (15 new tests) | Addendum 7 |
| Q-C1 | C-02/C-03 dtype + manifest | `surfaces/grid.py` | **CLOSED (owner D-1, 2026-10-21): not needed under Colab-only operation; never implemented** | COLAB_VERIFICATION Addenda 8–10; KNOWN_LIMITATIONS L-34 |
| Docs | API_CONTRACTS §8, CHANGELOG, CORE_STATUS §10, KNOWN_LIMITATIONS L-34..L-36 | 4 doc files | APPLIED after verification | final archive differs from the tested archive in exactly these 4 files |
## Recorded 2026-10-21 (decision closure) — tasks only, none applied, none approved for implementation
| ID | Task | Owner | Gate |
|---|---|---|---|
| Q-U1 | Replace "Live from run" label (`frontend/index.html:317`) with stored/generated wording | UI session | owner launch of UI session |
| Q-U2 | Remove hard-coded withdrawn-dataset results and the 3D view from the viewer | UI session | owner ruling (AP-007) |
| Q-U3 | **Verify UI null handling end-to-end** (API emits `null`; UI behaviour unverified) | UI session + Colab | Playwright approval (AP-007) |
| Q-D1 | Data adapters / lightweight manifest for multi-source strategy | core | **not approved**; needs source licences (AP-002a/b) |

**UI ruling applied locally 2026-10-21 (owner, chat), `frontend/index.html` only — Colab Playwright verification PENDING:** Q-U1 label "Live from run" → "Stored run data"; Q-U2 withdrawn-dataset identifiers (dudesurfin, OptionsDX, Kaggle, run id) removed, E-1/E-2 content kept only under "historical / withdrawn (DEC-002)" labels, home hero/Q&A no longer name a dataset; 3D view, its home-page preview, and its CSS removed (DEC-008; tabs are now Heatmap/Table, default Heatmap). Net 25 insertions / 154 deletions (`git diff --stat`). Pre-image: `orchestration/patches/pre/index.html.pre-ui-ruling-2026-10-21` (sha256 `425a37a2…f02c5`); edited file sha256 `dea15a53c9a4cb540c929b35743339800b9a14d2b714c958e669cd0eebcadddf`. **Colab Playwright verification DONE 2026-10-21 (COLAB_VERIFICATION Addendum 13):** Q-U1 label **VERIFIED**; 3D removal **VERIFIED** (0 canvases, `?view=3d` falls back to Heatmap, Heatmap/Table keyboard navigation works, no page errors, null cells still `—`). **Q-U2 NOT CLOSED:** identifiers gone, but the home hero still says "SPY end-of-day options, 2010 to 2023", the home E-1 pull-quote and "hosted dataset" phrases are unlabelled, explorer text still mentions "the 3D surface", and the methodology page says "the documented E-1 run" unlabelled — needs a further owner-authorized edit.

Q-C1 (Patch 1) remains closed by the owner, not queued.

Not queued / untouched: Q-C5 (C-12, C-13), Q-C6 (C-09), C-03 schema options B/C, UI items, A's doc-contradiction batch (README/IMPLEMENTATION_PLAN/MILESTONES still quote older counts).

**SUPERSEDED BY Addendum 15 (page `33fdd70f…`, two independent Playwright runs, 2026-10-21): Q-U1 label, 3D removal, Q-U3 null handling (synthetic) and Q-U2 withdrawn-dataset labelling are now VERIFIED; minor residuals only ("Read E-1 figures" link text, "Hosted dataset assessment" doc title, "Hosted files" step name). The paragraph below describes the earlier page `dea15a53…` and is kept as history.**

**Update 2026-10-21 (AP-007 closure; COLAB_VERIFICATION Addenda 13–14, page `dea15a53…`):** Q-U1 (label) **VERIFIED**; Q-U3 (null handling in UI) **VERIFIED on synthetic fixtures**; 3D removal **VERIFIED for rendering** (leftover "3D" wording in explorer text remains); Q-U2 withdrawn-dataset labelling **PARTIAL** (home pull-quote/links, "hosted dataset" phrases, methodology "documented E-1 run" outstanding; five text edits pending in the decision-closure session). Any edit changes the hash → re-run `/content/ap007b/check.py`-style checks on the new hash. Remaining after that: CI (needs a remote push — owner approval required; `.github/workflows/tests.yml` is modified locally and not pushed), keyboard/narrow-viewport/null-forecast journeys, A's doc-contradiction batch.
