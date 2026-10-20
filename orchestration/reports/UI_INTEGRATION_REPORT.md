# UI and End-to-End Integration Report (Agent E, wave 1, stages S1 inspection / S6 design)

Status: READY_FOR_REVIEW
Revision/manifest: git HEAD `306c01be5afa934d563f85e0d93afef4bb978121` (branch `main`), read 2026-10-20. `frontend/` and `dashboard-design/` are **unmodified** versus HEAD (not in `git status`). The API files are **modified in the working tree** versus HEAD (`api/server.py` +5 lines: generic-500 safety net; `api/service.py` +66/-: panel/JSON validation, symlink check, `origin_conflict`, `_finite_or_none`); the viewer at HEAD predates these changes (they are additive; checked below). `orchestration/contracts/` and `orchestration/reports/` did not exist when I started; `SHARED_STATUS.md` (dated 2026-10-20, Wave 1 launch) is current. Nothing was executed: no Python, no server, no browser. Every statement below is **Observed** (read from files) unless it says otherwise.

Files read: `frontend/index.html` (1,057 lines, all of it), `frontend/README.md`, `backend/src/volatility_lab/api/{server,service}.py`, `storage/raw_store.py` (ingest/meta), `docs/architecture/API_CONTRACTS.md`, `dashboard-design/{MODEL_HANDOFF,IMPLEMENTATION_STATUS}.md` (plus grep of `IMPLEMENTATION_PLAN.md`), `design.md` UA table, `backend/tests/unit/{test_api,test_api_contract,test_viewer_static}.py`, `scripts/make_synthetic_run.py`, `decision.md` DEC-002/007/008/013, `docs/data/DATA_ACQUISITION_AUTHORIZATION.md`, `guardrails.md` GR-DATA/PRD rows.

## Verified
Nothing. No check in this report was executed; static reading is not verification. No UA-01…UA-14 journey has been run by anyone (the repo says the same: `IMPLEMENTATION_PLAN.md` row 5, `test_viewer_static.py` docstring, `dashboard-design/IMPLEMENTATION_STATUS.md` §6/§7). The 2026-10-16 in-app-browser checks recorded in IMPLEMENTATION_STATUS §6 are the UI session's own manual claims; they predate the 2026-10-19/20 owner decisions and were never committed as tests.

## Observed

### 1. Screen to endpoint to module to stored file, and what is real

Server: `api/server.py` `dispatch()` maps URL to `api/service.py` `RunStore`; `RunStore` reads files under `--root` (one dir per run). Frontend served at `/` and `/index.html` (byte-identical file read, `server.py:41`). Hash routing, so every deep link is `GET /`.

| Screen (hash route) | Endpoint(s) used | Backend module | Stored file(s) | Classification |
|---|---|---|---|---|
| Landing `#/` | `GET /api/runs`, `/api/runs/{id}`, `/surface/{last}` (first run only) | `RunStore.list_runs/run_info/surface` | `panel.npz`, `meta.json`, `manifest.json` | Marketing copy = **documented placeholder** (hard-coded `D`); preview = real stored surface if any run, else **conceptual** synthetic formula (`index.html:1020`, labelled "Conceptual") |
| Overview `#/workbench/overview` | `/api/runs`, `/api/runs/{id}` | `list_runs`, `run_info` | `panel.npz` (status counts, dates), `meta.json`, `manifest.json`, dir listing of `tables/`, `forecasts/` | Status Q&A, E-1 box, pipeline = **documented placeholder** (static text, "As of 2026-10-16", `index.html:363`); "Available artifacts" = **real functionality** |
| Surface Explorer `#/workbench/explorer` | `/api/runs`, `/api/runs/{id}`, `/surface/{i}`, `/forecasts/{model}/{i}` | `list_runs`, `run_info`, `surface`, `forecast` | `panel.npz`, `forecasts/<model>.npz`, `manifest.json` | **Real functionality** (heatmap, table, slices, actual/forecast/difference, MAE+n, lineage). Works on **synthetic-only demo data in practice**: the only run that exists is the `make_synthetic_run.py` output with a persistence "forecast" (no model forecast has ever been loaded). **3D tab = real code but out of scope (DEC-008), see Gap 2** |
| Evaluation | `/api/runs/{id}/tables/{name}` | `RunStore.table` | `tables/*.csv` | Live table viewer = **real functionality, generic** (column names unknown until a real run, API_CONTRACTS G6). Pooled/by-tenor E-1 figures, metric-status list = **documented placeholder** hard-coded from `docs/research/E1_RESULTS.md` (`index.html:366-370`) |
| Data & Provenance | `/api/runs/{id}` (lineage, ledgers, status_counts) | `run_info` | `manifest.json`, `panel.npz` (hash recomputed `panel_sha256`) | Lineage/ledger/hash panels = **real functionality**; source identity, licence, transformation history, row-removal table, cell mix = **documented placeholder** about the withdrawn hosted dataset (`index.html:905-911`) |
| Experiments & Pipeline | `/api/runs/{id}` | `run_info` | `manifest.json` | Pipeline, experiments list, E-1 config, blockers = **documented placeholder** (`D.experiments`, `D.e1cfg`); only "Configuration of the selected run" is real (3 fields) |
| Artifacts | `/api/runs/{id}` | `run_info` | directory listing | Run artifacts = **real functionality**; notebooks / "not available" lists = static |
| Methodology (+`/limitations`, `/documents`) | none | none | none | **Documented placeholder** (repo paths shown as text, no links; API serves no documents) |

Not used from the API payloads: `status_labels`, `spot`, `iv_units`, `origin_conflict`. Not present in the API (G1-G6): `data_mode`, `forecast_kind`, `uncertainty_kind`, `target_definition`, model version, per-cell lineage, arbitrage flags, experiment/pipeline status route.

Payload-key check (UI reads vs `service.py`): every field the UI dereferences exists in the golden key sets of `test_api_contract.py` (`dates`, `tenor_days`, `k_nodes`, `tables`, `forecasts`, `lineage.{version_id,config_sha256,inputs[name,bytes,sha256],ledgers_conserved,ledger_prefilter/ledger_quotes{rows_in,kept,rejects},panel_hash_matches}`, `status_counts` keys `observed/interpolated_T/interpolated_k/missing`, forecast `actual/forecast/difference/status/n_difference_cells/n_observed_cells/mae_observed_vol_points/origin_date/target_date/horizon_panel_steps`, `table.{columns,rows,truncated}`). I found **no key mismatch**. Value-level mismatches are listed in section 2.

### 2. Contract / state / provenance findings (file:line in `frontend/index.html` unless noted)

**Known finding CONFIRMED: "Live from run".** `index.html:317`: `live: "Live from run"`. Rendered via `src("live")` as a chip on 20+ panels (Overview 702/713/717, Explorer 750/803/807/819-821/826, Evaluation 870/874/900/922/924, Data, Experiments 939, Artifacts) next to stored, historical, backtest-only data. GR-DATA-07 reserves "live" for `real_time_licensed` with known latency; UA-08 requires a string scan. Fails by wording; the `live` CSS class name is internal. The API has no `data_mode` (G1), so the UI cannot derive the right label; "Stored run" is truthful without it. No test covers this string (`test_viewer_static.py` has no wording scan).

**F1. Displays results of the withdrawn hosted dataset (DEC-002).** `decision.md` DEC-002 (2026-10-20) and `DATA_ACQUISITION_AUTHORIZATION.md:36`: hosted Kaggle SPY dataset is "not authorized for any further runs, display or export; E-1/E-2/H1-H6 ... unpublishable history". The served page hard-codes and displays E-1 figures (RMSE/MAE/skill table, by-tenor table, rows-removed table, cell mix, dataset identifier `dudesurfin/...`, run id `kaggle_eaa46df0_76bf2f94`, "Last access 2026-10-13") on Landing hero meta (1007), Overview (705-712), Evaluation (861-868), Data (905-911), Experiments (`D.experiments`, `D.e1cfg`). Also a `real` run would be displayed with no licence gate: the banner text hard-codes "Real data (hosted, upstream licence unverified)" (695), and nothing in `service.py`/`server.py` refuses `origin: real` although API_CONTRACTS §8 says display of real runs "is gated by the owner's licence decision". Decision for owner; not a UI-only call.

**F2. Documented content is stale against 2026-10-19/20 state.** `ASOF = "2026-10-16"` (363). Overview "Is usable data available?" (707, chip Unverified) and landing "Real-data evaluation: Completed" (1012) predate the withdrawal. Evaluation/Landing say neural models did not beat persistence (1008, 868); `CLAUDE.md` records the H5/H6 GRU ensemble beating persistence **under the fixed-expiry label only** (formal verdict `holds_under_fixed_expiry_label_only`). H1-H6 appear nowhere in the viewer. The UI therefore both displays withdrawn history and misstates the latest research state. Status vocabulary conflicts with `CLAUDE.md` ("Phases 0-5 partial", "Never imply otherwise"): D.flow shows most stages "Completed" (383).

**F3. Scope decision not respected (3D).** DEC-008 (2026-10-20, owner): "keep the static 2D viewer; no 3D, no frontend framework". `index.html` still ships a 3D Canvas renderer (`mountSurface3D`, 546-634, ~90 lines), the **default Explorer view on desktop** (`734`), a 3D tab (755), camera controls (794), the landing preview (1018), landing/overview copy "Three-dimensional surface explorer ... Completed" (380), ledes (727), limitation L-15 (398), and `frontend/README.md` ("3D surface"). `CLAUDE.md`, `IMPLEMENTATION_MATRIX.md:87`, CORE_STATUS §8 say "no 3D". The 3D code is also untested (canvas contents cannot be asserted by DOM). Other scope items are respected (see section 5).

**F4. Silent substitution on invalid input.** `ensureRun` (681): unknown/unlisted `?run=` falls back to the first run with no notice (the UI session recorded this as a passing check). A deep link to a deleted run can therefore show a **different run, possibly of a different origin**, unannounced (the origin banner does show the substituted run's origin, which mitigates but does not warn). Similar silent fixes: `?i=` out of range clamps to last (733), unknown `?model=` becomes the first model (735-736), bad `?table=` becomes first (881), `?j/c` out of range cleared (837), `?view=` invalid becomes default (734). Non-numeric `?i=` ignored (435). No "invalid parameter" state exists.

**F5. Forecast panels: label and legend gaps (GR-DATA-05, UA-03/04/07).** `drawLower` (810-822): the Actual/Forecast/Difference heatmaps have **no status legend** (`legend4()` is used only in the main view). Forecast cells with `keep=true` (817) are painted with the **actual cell's** status; where the actual is missing (`st===0`) a finite forecast value is shown with **no pattern**, i.e. it looks like an observed cell, and its `aria-label` says "..., missing" (496) while showing a number. The caption says patterns are the actual's (820) but it is easy to misread. Colour range of Actual/Forecast panels is shared (`surfaceRange(fc.actual, fc.forecast)`), which is fine, but forecast-only cells extend it silently.

**F6. GR-PRD-04 / UA-02 / UA-13 not met on forecast views.** Visible without interaction today: units (hard-coded text 746), axes, target date, origin date, horizon in "panel steps" (820), model *name*, "Backtest" (hard-coded, 820), MAE + n (821), dataset version (lineage panel, only if manifest). Missing: model **version**, target definition (`nearest_expiry`/`fixed_expiry`, G2; API_CONTRACTS §8 notes the displayed `actual` under E-2 is not the scored value), assumptions, uncertainty kind (G2), data mode / forecast kind from data (G1; "Backtest" is a UI constant, not read from the API), the definition of "Observed" that §8 says must be available (grid.py rule), the convention definitions (k = ln(K/F), tenor = calendar days, T = days/365; DEC-005). **The workbench has no disclaimer and no "Known limitations" link anywhere** (disclaimer lives only in the *landing* footer, 1014); the Explorer forecast foot says "Descriptive, one date, no significance" only. UA-13 requires disclaimer + limitation link on forecast views.

**F7. `origin_conflict` not surfaced.** `service._label` returns `origin: "unlabelled", origin_conflict: true` when `meta.json` and `manifest.json` disagree (GR-DATA-04). The UI shows the generic "UNLABELLED run. Its origin is unknown" (695) and never reads `origin_conflict`, so a *contradictory* label is indistinguishable from a *missing* one. (`API_CONTRACTS.md` §8 also does not document this key; the golden key sets exclude it because it is conditional: doc drift for core.)

**F8. UA-05 states.** Present: loading skeletons with `aria-busy`, empty (no runs, no tables, no forecasts, no dates), error (`role="alert"` + Retry), unavailable (API down), partial (forecast 404 message), invalid grid shape (`checkSurface`, 343-350), hash mismatch banner (826). Absent: **stale** state (api results are cached forever in a `Map`, 330-340; only Retry or full reconnect clears it, so a run added or changed while the page is open is never seen); a status value outside 0-3 would throw a TypeError (`STATUS[st][1]`) and fall to the generic "This page could not be drawn" box; `lineage.version_id` null would throw at `Experiments` (939: `.slice` on null). All caught by the router's try/catch (1047), so degrade to an error box, not a blank page.

**F9. A11y structure (static observation, needs axe to confirm).** `heatmap()` (487-520) uses `role="grid"` with `columnheader`/`rowheader`/`gridcell` but **no `role="row"` wrappers** (cells are direct grid children): likely `aria-required-children` violation. No theme toggle: landing is forced light (989), workbench forced dark (656), `prefers-color-scheme` is not read, so UA-11 "both themes" is satisfied only as "each page in its one theme". Good: skip link, `:focus-visible`, arrow-key grid navigation, `forced-colors` rule (251), `prefers-reduced-motion` handling (249, 450), non-colour status cue (pattern + text).

**F10. Misc.** (a) Run shown as `id.slice(0,8)` (ctxBar 644, selectors 650): ids are sha256 hex, so collisions are improbable but two synthetic reruns differ only by tail. (b) `ctxBar` has a dead ternary (`: null : null`, 641). (c) `info.lineage` null renders "No manifest stored" (correct, never "verified"). (d) Table `insufficient_n` chip depends on the cell text `True`/`true` (850): `make_synthetic_run.py` writes Python bools (`True`); the runner's writer is not verified here. (e) A listed run with an unreadable `panel.npz` still appears in `/api/runs` (`list_runs` only checks existence) and, if first, is the default and also the landing-preview source (error then silently falls back to the conceptual preview, 1034).

### 3. UA-01…UA-14: does the journey exist, and what executing it needs

"Exists" = UI behaviour is present in code. None executed. Colab column assumes a Linux VM, same-VM localhost server, headless Chromium.

| ID | Exists in UI? | What is needed to execute | Where |
|---|---|---|---|
| UA-01 values equal API | Yes (table view, heatmap text, MAE/n, difference) | Synthetic run + Playwright reading DOM vs `GET` JSON (tolerance: JS `toFixed(2)` of `iv*100`; heatmap 1 dp; diff 2 dp with unicode minus; MAE 3 dp; counts `toLocaleString`) | Colab |
| UA-02 axes/units/mode/origin/horizon/versions visible | Partial: units, axes, dates, horizon, model name, dataset version yes; data mode, model version, convention definitions, Observed definition **no** (F6) | Same + a list of required strings; expect FAIL on the missing ones until G1/G2 land | Colab (results), owner (judging "without interaction") |
| UA-03 status distinguishable by more than colour | Yes in heatmap (pattern + text in table + aria), slices (hollow vs filled, dashed); forecast panels weak (F5); animation/exports N/A (none) | DOM assertion per cell: API status vs pattern/`aria-label`/table text; screenshots | Colab for DOM, **owner** for human/colour-blind judgement |
| UA-04 interpolated never shown as observed | Yes by construction (status-driven); forecast-over-missing case ambiguous (F5) | Assert for every status 1/2 cell: backgroundImage non-empty and label not "observed" | Colab |
| UA-05 loading/empty/partial/error/stale | All but **stale** (F8) | Playwright `page.route` fault injection (500, abort, `[]`, 404 forecast, 400 corrupt forecast, malformed JSON, shape mismatch, delayed response) | Colab |
| UA-06 table/2D alternative for every 3D view | Yes (heatmap, table tabs). **Moot if 3D removed (DEC-008); A3 recorded N/A in CORE_STATUS** | Tab exists + same numbers as heatmap | Colab (or N/A) |
| UA-07 difference labelled forecast - observed, zero stated, n shown | Yes: title "Difference (forecast minus actual)", "Zero", n cells and n observed (821) | Text assertions + diff cell = API diff x 100; missing-actual cells show "—" | Colab |
| UA-08 backtest vs prospective; no "live" | **Fails** on "Live from run" (Confirmed). "Backtest" present; prospective kind does not exist | Body-text scan on every route/state for `\blive\b` and `real-time` | Colab |
| UA-09 n and exclusions; insufficient-n marked | Yes for tables (`insufficient_n` chip, counts column); exclusions only as documented static text | Synthetic table with n<100 and n>=100 rows | Colab |
| UA-10 lineage drill-down grid point to quotes/IV/method/forecast | **No**: explicitly "Per-cell quote lineage is not stored" (803); G4 | Needs core data (panel schema change). Test can only assert the *Unavailable* state | Colab (state only) |
| UA-11 keyboard, focus, SR labels, contrast, reduced motion, both themes | Partial (F9) | axe-core scan + keyboard script + emulated `reduced-motion`/`forced-colors`; screen reader and measured contrast on real rendering | Colab (automated part); **owner** (NVDA/VoiceOver, real contrast, real keyboard feel) |
| UA-12 no credentials / bulk licensed data | Static test exists (`test_viewer_static.py`) | Runtime: record all requests (same-origin only), `localStorage`/cookies empty, response header check | Colab (static test + runtime) |
| UA-13 disclaimer + limitation link on forecast views | **No** in workbench (F6) | String scan on Explorer forecast panel; phrase-list scan needs negation-aware review ("Not a trading product", "Any trading, hedging or profit value" appear as negations) | Colab scan + owner review |
| UA-14 performance vs thresholds | Thresholds are `TBD(DEC-008)`; grid is 54 cells | Record timings only; no pass/fail can be defined | Colab for numbers; **owner's browser/GPU** for perceived performance |

### 4. Colab E2E plan (design only; Not run)

Prerequisites (orchestrator-owned): Colab connected and working tree transferred (`COLAB_VERIFICATION.md`). Python deps of `make_synthetic_run.py` are numpy and pandas (preinstalled on Colab); the API is stdlib + numpy. Browser tooling (`pip install playwright`, `playwright install --with-deps chromium`; optionally `axe-core` JS from a pinned package) is installed **in the Colab VM only, not the repo**, and needs orchestrator/owner approval (IMPLEMENTATION_STATUS notes installation was never authorised; `CLAUDE.md` §13/§5 forbid adding manifests to the repo, so the E2E script lives in Colab/scratch, not committed, until the owner decides).

Steps and assertions:

1. **Fixture runs** (script written in the Colab cell, labelled SYNTHETIC, nothing downloaded):
   `python scripts/make_synthetic_run.py --out /content/store --days 60` then copy/derive extra runs under `/content/store/datasets/`:
   - `good` (the generated run, label synthetic, manifest, 1 table, `persistence` forecast);
   - `bare_run` (panel only: unlabelled, no manifest);
   - `conflict_run` (meta `real` vs manifest `synthetic`, expect `origin_conflict`);
   - `tampered_run` (panel `spot+1`, manifest copied: `panel_hash_matches=false`);
   - `corrupt_fc_run` (`from_future.npz`: API 400) and `no_forecast_run` (none);
   - `allmissing_run` (one date with all `status=0`, `iv=NaN`);
   - `bigtable_run` (>5,000-row CSV: `truncated=true`) and `empty_table` / `bad_meta` runs as in `test_api.py`;
   - `noisy_fc` (persistence plus fixed-seed Gaussian noise, labelled synthetic, to exercise non-trivial differences; never described as a model).
2. **Start server**: `PYTHONPATH=backend/src python -m volatility_lab.api.server --root /content/store/datasets --port 8765 &`; poll `GET /api/runs` until 200 (assert non-empty, origins as expected).
3. **Browser**: Playwright Python, Chromium headless, viewports 1440x900, 768x1024, 375x812. Global listeners for the whole session: `console` errors, `pageerror`, `requestfailed`, every request URL (assert origin == `http://127.0.0.1:8765`), responses' `Content-Security-Policy` header present. Allow-list the `/favicon.ico` 404 (server returns JSON 404, a browser will log it; not a viewer fault).
4. **Journeys** (each ends with a screenshot saved under `/content/e2e_shots/` for the orchestrator/owner to view):
   - J1 UA-01/02/03/04/07: open `#/workbench/explorer?run=<good>&view=table&i=30`; read all 54 cells; compare to `GET surface/30` (|text - round(iv*100,2)| <= 0.005, status text equals label map); switch to heatmap, assert each cell's `aria-label` contains the status label, status 1/2 cells have non-empty `backgroundImage`, status 0 cells show "—"; with model `persistence`, compare Actual/Forecast/Difference to `forecasts/persistence/30` (1 dp, 2 dp), `n_difference_cells`, `n_observed_cells`, MAE (3 dp). Record the expected FAILs for UA-02 missing fields (data mode, model version, definitions).
   - J2 UA-05: for each of: `/api/runs` aborted, `[]`, surface 500, forecast 404 (date 0), forecast 400 (`corrupt_fc_run`), invalid grid shape, malformed JSON, 3 s delayed surface: assert the matching state (`role=alert`, "Not connected", "No run is loaded", skeleton with `aria-busy`, Retry restores). Record absent "stale" as FAIL/N-A.
   - J3 provenance GR-DATA-04/05: `good` shows "synthetic" banner; `bare_run` shows UNLABELLED; `conflict_run` (expect today: generic UNLABELLED, F7); `tampered_run` shows the hash-mismatch alert; manifest-less run says "No manifest stored", never "verified".
   - J4 UA-08/13 wording: for every route, with and without a run, scan `document.body.innerText` for `/\blive\b/i`, `real-time`, `buy|sell|profit|alpha`; assert disclaimer text and a limitations link exist inside the Explorer when a forecast is shown. Expected today: `live` hits (Confirmed), no disclaimer (F6).
   - J5 UA-09: Evaluation on the table run; rows with `n_cells < 100` show "Insufficient n"; counts visible; `bigtable_run` shows "truncated".
   - J6 invalid input (F4): `?run=doesnotexist`, `?i=999`, `?i=abc`, `?model=zzz`, `?view=zzz`, `?table=zzz`, `?j=99&c=99`: assert whether a visible notice appears (today: none; record as finding).
   - J7 UA-11 (automated part): axe-core on each page at 1440 and 375 (expect the `grid` row structure violation, F9); keyboard-only: Tab order, skip link, arrow keys in heatmap, Escape closes the mobile drawer, tabs arrow keys; `emulate_media(reduced_motion="reduce")` and `forced_colors="active"`; horizontal-overflow check (`scrollWidth <= innerWidth`) at 375/768/1440.
   - J8 UA-12 runtime: after all journeys, `localStorage`, `sessionStorage`, `document.cookie` empty; no non-same-origin request; run `pytest backend/tests/unit/test_viewer_static.py test_api_contract.py test_api.py` in Colab too (that is COLAB_VERIFICATION territory; listed for completeness).
   - J9 UA-14 numbers only: `performance.now()` deltas for initial route, date-slider change (n=20), `PerformanceResourceTiming` for API calls, long-task observer. Colab CPU numbers are not user-perceived performance; thresholds are TBD so no pass/fail.
5. **Expected result record**: a table PASS / FAIL / BLOCKED / N-A per assertion with the raw logs. Because several assertions are expected to fail today (F5-F8), the orchestrator should treat J1-J9 as a **baseline run**, then re-run after UI fixes.

Needs the **owner's own browser** (cannot be done headless in Colab): human judgement on "more than colour" and colour-vision simulation (UA-03), screen-reader pass (NVDA/VoiceOver) and focus-order feel (UA-11), real-device touch at 375 px, rendering on the owner's GPU/display if 3D is kept, Firefox/Safari checks, and the licence/wording sign-off for any real-origin display.

### 5. Scope decision check (local research tool, no 3D, no framework, no auth/deployment)

| Item | Respected? | Evidence |
|---|---|---|
| Local only, no deployment | Yes | `create_server` refuses non-loopback host (`server.py:92`); `--port` only; CSP `default-src 'none'`, `connect-src 'self'` |
| No auth | Yes (none exists, bind guard instead) | no auth code; API_CONTRACTS §8 |
| No framework / dependencies in frontend | Yes | single HTML file, no `<script src>`, no `<link>`; guarded by `test_viewer_static.py` (not run) |
| Stdlib API, read-only | Yes | GET only, others 405; `RunStore` reads files, no compute |
| **No 3D** | **No** | F3 above |
| Frontend does not compute IV/train/hold credentials | Yes | only `fetch` GETs; client computes display formatting, slices and a colour scale only; no storage APIs |
| Hosted-data display (DEC-002) | **No** | F1 above (not strictly the scope decision, but a binding owner decision the viewer contradicts) |

## Proposed

Diffs against **UI-owned files are routed to the UI session**; API-semantics changes to core. None applied (I may edit only this file). Line numbers refer to `frontend/index.html` at HEAD.

**P1 (UI; GR-DATA-07, UA-08): rename the "live" chip.**
```diff
-  const t = { doc: "Documented", live: "Live from run", none: "Not connected" }[kind];
+  const t = { doc: "Documented", live: "Stored run", none: "Not connected" }[kind];
```
Plus a test in `test_viewer_static.py` (core/tests owner, new assertion): no visible string matches `\bLive\b` (case-insensitive) in `index.html`.

**P2 (UI, subject to owner confirming DEC-008 stands): remove 3D.**
```diff
-  if (!["3d", "heatmap", "table"].includes(sel.view)) sel.view = matchMedia("(max-width:700px)").matches ? "heatmap" : "3d";
+  if (!["heatmap", "table"].includes(sel.view)) sel.view = "heatmap";
...
-    const order = [["3d", "3D surface"], ["heatmap", "Heatmap"], ["table", "Table"]];
+    const order = [["heatmap", "Heatmap"], ["table", "Table"]];
...
-      b.addEventListener("keydown", e => { ... go(order[(order.findIndex(o => o[0] === v) + k + 3) % 3][0]); });
+      b.addEventListener("keydown", e => { ... go(order[(order.findIndex(o => o[0] === v) + k + order.length) % order.length][0]); });
```
Then delete `mountSurface3D` (546-634), the 3D branch of `drawWork` (787-796), `view3d` references (752, 766, 772), the landing preview 3D mount (1018-1034, replace by `heatmap({... sm:true})`), `D.caps` row 380, limitation L-15 (398), lede line 727 ("Rotate and inspect..."), and `frontend/README.md` wording. If the owner instead reverses DEC-008, the docs (`decision.md`, CLAUDE.md, CORE_STATUS, IMPLEMENTATION_MATRIX) must change instead; that is an owner call, not mine.

**P3 (UI; F4): never substitute a run silently.** In `ensureRun` (681) record a notice when `sel.runId` was set but not listed, and render it with `originBanner`'s sibling `banner` (`role="status"`), e.g.
```diff
-  if (!sel.runId || !conn.runs.some(r => r.id === sel.runId)) { sel.runId = conn.runs[0].id; sel.i = null; sel.model = null; sel.j = null; sel.c = null; }
+  if (!sel.runId || !conn.runs.some(r => r.id === sel.runId)) {
+    if (sel.runId) conn.notice = `Run ${sel.runId.slice(0, 8)} is not listed by the API; showing ${conn.runs[0].id.slice(0, 8)} instead.`;
+    sel.runId = conn.runs[0].id; sel.i = null; sel.model = null; sel.j = null; sel.c = null;
+  }
```
and show `conn.notice` (then clear it) at the top of every page that calls `ensureRun`. Same idea for out-of-range `i`, unknown `model`, `table` (one-line banner each).

**P4 (UI; F5, UA-03/04): legend and label for forecast panels.** Append `h("div", { style: "margin-top:12px" }, legend4())` to the Actual panel kids in `drawLower`, and in `heatmap()` line 496 replace the status clause so forecast-over-missing is not called "missing" and is visibly distinct:
```diff
-`... vol points, ${STATUS[st][1].toLowerCase()}`
+`... vol points, ${o.keep && st === 0 ? "forecast value; the actual cell is missing" : STATUS[st][1].toLowerCase()}`
```
and give those cells a distinct border/dash class (e.g. `.hc.fonly{outline:1px dashed var(--ink2)}`) so the cue is non-colour.

**P5 (UI; F6, UA-13, GR-PRD-02/04): disclaimer and limitation link in the workbench shell.** In `shell()` after `main`:
```diff
+  main.append(h("p", { class: "foot", style: "margin-top:32px" }, "Research and education only. Not investment advice and not a trading product. All forecasts shown are historical backtests. ", h("a", { class: "link", href: href("methodology", null, "limitations") }, "Known limitations")));
```
(`main` is returned; append in `route()` after the page function resolves so it is last.)

**P6 (UI; F7): show label conflicts.** `originBanner(origin, desc)` -> `originBanner(origin, desc, conflict)`; when `conflict` print "CONFLICT: meta.json and manifest.json name different origins; the run is treated as unlabelled." Callers pass `info.origin_conflict`.

**P7 (UI + owner; F1/F2): documented snapshot.** Minimum: update `ASOF`, replace "Is usable data available?" and the E-1 panels with the withdrawal state ("hosted dataset withdrawn 2026-10-20; figures retained as unpublishable history, not displayed"), remove the dataset identifier and run id strings, and add H1-H6 / fixed-expiry-only status from `docs/research/PHASE4_NEURAL_EVIDENCE_REVIEW.md` **only if** the owner allows displaying them (DEC-002 says no display). Needs an owner decision before any edit.

**P8 (UI; F9): ARIA grid structure.** Wrap each tenor row's `rowheader` + `gridcell`s in a `div role="row" style="display:contents"` (keeps the CSS grid), or drop `role=grid` and use a labelled `table`. Confirm with axe in J7.

**P9 (core; API semantics; G1/G2/G3 stay as in API_CONTRACTS §8 gaps).**
 (a) Implement G1: optional `meta.json` keys `data_mode`, `forecast_kind` echoed in run info/surface/forecast payloads; then P5/F6 can read instead of hard-coding "Backtest". (b) G2: `target_definition`, `uncertainty_kind`, model version. (c) Document `origin_conflict` and the generic `500 {"error": "the run data could not be read"}` in §8 ("Unavailable states" lists only 404/400). (d) Decide whether `origin: real` display is refused unless the owner records a licence decision (e.g. server flag), since §8 claims a gate that the code does not enforce. (e) Optionally have `list_runs` skip or flag runs whose `panel.npz` is unreadable (F10e). (f) Add a handler for `/favicon.ico` (204) so browser consoles stay clean, and `do_HEAD`/`do_OPTIONS` return 405 instead of 501 (cosmetic).

**P10 (tests; owner of tests = core/C).** The existing `test_viewer_static.py` checks no external origins/secrets only. Add static wording assertions mirroring GR-DATA-07/PRD-02 (no `Live`, disclaimer string present, `3D`/`mountSurface3D` absent if DEC-008 holds) so P1/P2/P5 cannot regress; real UA coverage requires the Colab Playwright suite in section 4, committed only if the owner approves a test-tooling decision.

## Blocked
- Executing any journey: Colab not connected (SHARED_STATUS), and local execution is forbidden.
- A real-run view test: no run beyond synthetic exists; real data is not authorized (DEC-002). Real table column names remain unknown (G6).
- UA-10 and UA-02 mode/version fields: need core/data changes (G1, G2, G4).
- UA-14 pass/fail: thresholds `TBD(DEC-008)`.

## Not run
Everything in sections 3-4: all UA-01…UA-14, the Playwright plan, axe, keyboard walkthrough, backend API tests, `test_viewer_static.py`, the synthetic-run generator, the server, the viewer. I also did not verify that `make_synthetic_run.py` still works with the modified `raw_store.py` (static read only: it calls `ingest(...)` without `origin`, so no manifest origin and no conflict with its own `meta.json`; reads consistently).

## Failed
Nothing was run, so nothing "failed". Static findings that I expect to fail when run: UA-08 (wording), UA-13 (disclaimer), UA-02 (missing fields), UA-10 (by design), UA-11 grid-row ARIA, DEC-008 scope check (3D), DEC-002 display check (F1).

## Routed to others
- **Owner:** (1) F1 and P7: may the viewer still display E-1/H1-H6 history and the hosted dataset's identifiers at all (DEC-002 says no display)? (2) F3/P2: confirm DEC-008 "no 3D" is to be enforced in code now (vs. reversing it). (3) Real-origin display gate (P9d).
- **UI session (owns `frontend/`, `dashboard-design/`):** P1-P8; update `frontend/README.md` and `dashboard-design/IMPLEMENTATION_STATUS.md` (they still say 3D "Completed" and refer to a stale 12-test API run and 2026-10-16 state); `MODEL_HANDOFF.md` §3 item 4 ("frontend/README says empty") and item 1 are themselves stale.
- **Core (Agent C) / API owner:** P9; add `origin_conflict` and generic 500 to `API_CONTRACTS.md` §8; contract question of whether `iv_units`, `status_labels`, `spot` stay (unused by the viewer; harmless).
- **Repo auditor (Agent A) / docs:** documentation drift on 3D: `IMPLEMENTATION_MATRIX.md:87` ("no 3D") and `CORE_STATUS.md` §8 vs `frontend/index.html` + `dashboard-design/`; `docs/engineering/IMPLEMENTATION_MATRIX.md` P5b says "no actual-vs-forecast" though P5c implemented it.
- **Orchestrator:** a Colab Playwright tool-install approval; fixture location convention; where the baseline-run results are recorded (`COLAB_VERIFICATION.md`).
- **Data researcher (B):** whether any replacement dataset could change the "real" banner wording; nothing for me to do until DEC-002 is resolved.

## Files changed
- `orchestration/reports/UI_INTEGRATION_REPORT.md` (created; `orchestration/reports/` directory created with it). No other file touched.

## Handoff
Safe to rely on: the screen-to-endpoint-to-file map (section 1), the finding that frontend field use matches the API golden key sets (no key mismatch), the confirmation of "Live from run" at `index.html:317`, and the list of statically observed gaps with file:line. The scope-decision verdict (3D and withdrawn-dataset display contradict owner decisions) rests on `decision.md` DEC-002/008 as written on 2026-10-20.
May not rely on: any claim that a UA journey, the UI, an API test or a browser check passed (none run; the 2026-10-16 manual QA in IMPLEMENTATION_STATUS is the UI session's unreproduced claim and predates the decisions); any inference about rendering (colour, layout, contrast, performance) since no page was opened; the exact output text of any table (real column names unknown); my diffs, which are unapplied and untested sketches against HEAD line numbers and must be re-checked by the UI session against the file as it then stands.
