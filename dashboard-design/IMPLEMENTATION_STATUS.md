# Implementation status

**Status:** `IMPLEMENTED` for the items marked so below, verified only as stated in §6. Nothing here is `VALIDATED`. Recorded 2026-10-16. This file is the record of what was built; [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) remains the plan and differs where §2 says so.

## 1. What exists

One self-contained file, [../frontend/index.html](../frontend/index.html) (about 1,100 lines: CSS, a small DOM helper, the pages, a Canvas 3D renderer). No build step, no dependency, no network call except `GET` routes of the same origin. Served unchanged by `backend/src/volatility_lab/api/server.py` at `/` and `/index.html`.

| Route (hash) | Page | Data |
|---|---|---|
| `#/` | Landing page | Documented content; the preview uses the first stored run if the API lists one, otherwise a labelled conceptual surface |
| `#/workbench/overview` | Research overview | Documented status rows; live artifacts of the selected run |
| `#/workbench/explorer` | Surface Explorer (3D surface, heatmap, table; selected cell; smile and term-structure slices; actual, forecast, difference; lineage) | `GET /api/runs`, `/api/runs/{id}`, `/surface/{i}`, `/forecasts/{model}/{i}` |
| `#/workbench/evaluation` | Evaluation | Live: any result table of the run (`/tables/{name}`); Documented: E-1 figures |
| `#/workbench/data` | Data & Provenance | Documented source identity, licence, transformations, row ledger; live lineage and ledgers from the run manifest |
| `#/workbench/experiments` | Experiments & Pipeline | Documented; live configuration hash of the run |
| `#/workbench/artifacts` | Artifacts | Live: what the selected run contains; static notebook list |
| `#/workbench/methodology`, `/limitations`, `/documents` | Methodology & Documentation | Documented summaries and repository paths (not links; the API serves no documents) |

URL state: `run`, `i` (date index), `view` (`3d`, `heatmap`, `table`), `model`, `j` and `c` (selected cell), `table`. Deep links and refresh work because `/` always returns the file.

## 2. Differences from the plan, and why

| Plan | Built | Reason |
|---|---|---|
| Vite, TypeScript, React, built bundle | Single no-dependency HTML file | The server serves exactly one file under `default-src 'none'` (no second script, stylesheet, font or image). The owner's instructions forbid backend changes and unauthorised dependency installs. A static route and CSP change remain open ([IMPLEMENTATION_PLAN §7](IMPLEMENTATION_PLAN.md) item 2) |
| Geist and JetBrains Mono | System font stack (Geist and JetBrains Mono apply only if installed on the viewer's machine) | Font files are blocked by the CSP |
| 3D: Canvas 2D prototype first, Three.js if inadequate | Canvas 2D projection, kept | The grid is 54 cells; no dependency; WebGPU and TSL not used (no benefit at this size). The Three.js spike (DEC-008) has not been run, so the choice is not recorded as a decision |
| Documented content as a typed snapshot with source and date | Implemented as a `D` object, with source paths in each panel and "As of 2026-10-16" | As planned. It will not update itself; a changed document means editing this file |
| Document links | Repository paths shown as text | The API serves no documents; dead links were avoided |
| Landing capabilities | "Two-dimensional viewer" and "Three-dimensional explorer" now read Completed | Built and checked on the synthetic run (§6). Real data has not been loaded |

## 3. Model gate

`docs/engineering/MODEL_STATUS.json` does not exist, so the [MODEL_HANDOFF §4](MODEL_HANDOFF.md) gate was **not** satisfied. Following the owner's instruction for an incomplete model, only model-independent work was built: everything reads the existing API. Features that need real model output (a real run, stored forecasts of a real model) show their unavailable states; forecast comparison works with whatever `forecasts/*.npz` a run holds (the synthetic run holds a persistence forecast only). No real run was loaded and no data was downloaded.

## 4. Visualization

3D: `mountSurface3D` draws the surface on a Canvas 2D context with its own projection (yaw, pitch, zoom), painter's-algorithm quad ordering, vertex markers by status (filled circle observed, hollow circle interpolated in tenor, square interpolated in strike), gaps wherever a corner cell is missing (never interpolated across), tick and axis labels with units, hover readout, click selection, drag to rotate, and buttons and keys for rotate, tilt, zoom and reset. A `ResizeObserver` and the canvas are released when the page changes. Fallback: the Heatmap and Table views show the same values; if canvas is unavailable the explorer switches to the heatmap. Tenor nodes are spaced evenly for display, and the caption says so. Heatmap and slices are HTML and SVG.

## 5. Components

Status chips (icon plus text for the seven states), source chips (Documented, Live from run, Not connected), panels, key-value lists, tables with insufficient-n flags, loading skeletons, empty, error and unavailable states with Retry, banners (origin and hash mismatch), tabs, segmented control, heatmap grid (colour and pattern), slice charts, responsive navigation drawer with Escape and focus handling, skip link and a polite live region for selection readouts.

## 6. Verification actually performed

Environment: the in-app browser (Chromium-based) against `python -m volatility_lab.api.server` serving a labelled SYNTHETIC run generated by `scripts/make_synthetic_run.py` (60 dates, 6 tenors by 9 nodes, one table, one persistence forecast, manifest). `playwright-cli` is not installed (installation was not authorised), so all browser checks used the in-app browser.

- All 12 route variants rendered without console errors, error states or horizontal page overflow at 1440, 768 and 375 px.
- Scripted in-page checks all passed: the landing call to action opens the workbench; browser back and forward; an unknown run id falls back to the first run; an out-of-range date clamps; arrow keys move the heatmap selection and update the inspector and URL; the slider loads another date; forecast panels render (54 cells each, MAE with n); the first date shows "No forecast of this model for this date"; tab keyboard navigation; the 3D canvas mounts and a click selects a cell; Evaluation shows the run table (6 rows, insufficient-n flags); Artifacts links resolve; Data shows both ledgers reconcile.
- Failure states were exercised by replacing `fetch` in the page: API unreachable (not-connected states on Overview, Explorer and Evaluation; the landing preview falls back to the conceptual label), HTTP 500 on a surface (inline error with Retry), and a surface whose grid shape disagrees with its axes (rejected as invalid). Normal behaviour was restored afterwards.
- Visual comparison with the Stitch screens was by eye (landing, overview, explorer, evaluation, data, mobile navigation). Differences: system fonts; the 3D surface is a real projected mesh (Stitch could not draw one); no step numbering.
- A real bug found and fixed during QA: the secondary-button class collided with the landing section class and stretched the mobile menu button.
- Existing backend API tests: `PYTHONPATH=src python -m unittest tests.unit.test_api` run from `backend/`: 12 tests, OK. One of them requires the served page to contain the text "Volatility Surface Viewer"; the new page keeps that through its meta description.
- Not run: build, lint and type check (none exist for the frontend), frontend unit tests (none exist), Playwright end to end (not installed). The wider backend suite was not rerun (no backend change).

## 7. Known limitations and open items

- No automated frontend tests exist; the checks in §6 were run by hand in one browser engine and are not committed. Firefox and Safari were not checked. No real touch device was used.
- No screen-reader or automated accessibility scan was run. Contrast was computed for the tokens ([DESIGN_SYSTEM.md](DESIGN_SYSTEM.md)), not measured on rendered pages. WCAG 2.2 AA is targeted, not claimed.
- The real E-1 run, real forecasts and real table names are unverified (nothing was loaded). The Evaluation page handles any table generically.
- The selected cell persists in memory across pages within a session even when a link omits it.
- Documented figures are a snapshot dated 2026-10-16 and must be re-checked if `E1_RESULTS.md` changes.
- Open integration items from [IMPLEMENTATION_PLAN §7](IMPLEMENTATION_PLAN.md) remain: static serving and CSP, fonts, a documents route, per-cell quote lineage, stored arbitrage flags, plots and report files, the licence decision for real data, and the DEC-008 decision.
- Shared project documents (CHANGELOG, README status table, IMPLEMENTATION_MATRIX, the CLAUDE.md status line) were not edited because the model session is changing them; the owner should add an entry for this work.

## 8. How to run

```bash
python scripts/make_synthetic_run.py --out scratch/demo_store
PYTHONPATH=backend/src python -m volatility_lab.api.server --root scratch/demo_store/datasets
```

The first command creates a labelled synthetic run (no model, no download). Open http://127.0.0.1:8765/ . No environment variables or secrets are used.
