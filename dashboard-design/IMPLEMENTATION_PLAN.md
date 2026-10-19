# Implementation plan (future phase)

**Status:** `PROPOSED`. **Do not start until the gate in [MODEL_HANDOFF.md §4](MODEL_HANDOFF.md) is satisfied and the owner explicitly authorises implementation.** Nothing here is built. The frontend stack is an open decision (DEC-008 `NEEDS RESEARCH`; [../CLAUDE.md](../CLAUDE.md) §5: "do not add a dependency, manifest, lockfile, framework scaffold ... that silently decides one of these"); every stack statement is a proposal to be confirmed by a feasibility prototype and an owner decision.

## 1. Verified starting point

- `frontend/index.html` (152 lines, no build, no dependencies); `frontend/README.md` says the directory is intentionally empty pending DEC-008 (now stale: the file exists).
- Server: `backend/src/volatility_lab/api/server.py`, Python standard library, GET only, loopback only. It serves **one** file at `/` and `/index.html` and nothing else statically. Response headers include `Content-Security-Policy: default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; form-action 'none'`. Consequences: no external scripts, fonts, images or stylesheets; no bundle from a second file; `data:` images are blocked (no `img-src`).
- Data routes and payloads: [DATA_WIDGET_MATRIX.md](DATA_WIDGET_MATRIX.md) (header). Payload shapes (read from `api/service.py`), as a contract sketch only:

```ts
type RunSummary = { id: string; origin: "synthetic" | "real" | "unlabelled"; description: string };
type RunInfo = RunSummary & {
  dates: string[];                       // ISO dates
  tenor_days: number[]; k_nodes: number[];
  status_labels: Record<string, string>; // "0":"missing" "1":"interpolated_T" "2":"interpolated_k" "3":"observed"
  status_counts: Record<string, number>; // whole run, keyed by label
  tables: string[]; forecasts: string[];
  lineage: null | { version_id: string; config_sha256: string; inputs: unknown;
                    ledgers_conserved: unknown; ledger_prefilter: unknown; ledger_quotes: unknown;
                    panel_sha256_recorded: string; panel_sha256_actual: string; panel_hash_matches: boolean };
};
type SurfacePayload = { run: string; origin: string; description: string; index: number; date: string;
  spot: number; n_quotes: number; tenor_days: number[]; k_nodes: number[];
  iv: (number | null)[][]; status: number[][]; iv_units: string };   // iv decimal; rows = tenor, cols = k
type ForecastPayload = { run: string; model: string; index: number; target_date: string; origin_date: string;
  horizon_panel_steps: number; tenor_days: number[]; k_nodes: number[];
  actual: (number | null)[][]; status: number[][]; forecast: (number | null)[][]; difference: (number | null)[][];
  n_difference_cells: number; n_observed_cells: number; mae_observed_vol_points: number | null; iv_units: string };
type TablePayload = { run: string; table: string; columns: string[]; truncated: boolean; rows: (string | number)[][] };
```

Types of the ledger and input fields are `UNKNOWN` until read from a real manifest.

## 2. Recommended architecture (proposal)

**Smallest maintainable stack:** Vite, TypeScript, React, plain CSS custom properties (the tokens in DESIGN_SYSTEM.md). No UI kit, no CSS framework, no chart library, no state library, no router package.

| Concern | Choice | Why |
|---|---|---|
| Build and language | Vite + TypeScript, strict | Typed payloads from §1; fast tests; static output |
| UI | React with function components and hooks | Seven screens plus shared components; a smaller code path than hand-written DOM; widely maintained |
| Routing and shared state | Hash routes; selection state (run, index, model, view) in the URL | Works with a one-file static server; shareable views; no router dependency |
| Data access | One typed `api/client.ts` using `fetch`, plus a `useResource` hook returning `{ status: "loading" \| "ready" \| "empty" \| "error" \| "unavailable", data }` | Makes every state explicit and testable; no cache library |
| Charts | Hand-written SVG components: `Heatmap`, `SmileSlice`, `TermSlice`, `DiffLegend`, `ErrorBars` | The grid is tiny; patterns and tooltips need control; avoids a chart dependency |
| 3D | See §3 | |
| Styling | `tokens.css` (dark and light) plus plain component CSS | |
| Tests | Vitest, Testing Library; Playwright for browser checks (§6) | |

If the owner prefers zero framework (a DEC-008 option), the same structure works with TypeScript and native web components; the cost is rebuilding hooks, chips and tables by hand. This plan prefers React for that reason, and the choice should be recorded as an ADR only after the feasibility prototype.

Every new dependency needs the CLAUDE.md §13 note (need, alternatives, licence, maintenance, size). Candidate list for the first milestone: `react`, `react-dom`, `typescript`, `vite`, `vitest`, `@testing-library/react`, `playwright` (dev). Exact versions are chosen at implementation time with a maintenance check; none are installed.

**Proposed layout** (not created): `frontend/src/{app, pages, components, viz, api, content, styles}` with `pages/` = Landing, Overview, Explorer, Evaluation, Data, Experiments, Artifacts, Methodology; `components/` = StatusChip, SourceChip, Panel, Table, Tabs, Segmented, Slider, Tooltip, Banner, Dialog, Skeleton, EmptyState, ErrorState, UnavailableState; `content/` = typed static content, each item carrying `{ text, sourceFile, section, asOf }` so every documented claim traces to a document.

**Documented content** (everything marked `Docs` in the matrix): proposed as a typed snapshot in `content/`, authored from the cited documents, shown with the *Documented* chip and an "as of" date. Alternatives (an API route that serves rendered documents; linking out only) need a backend change; see §7.

## 3. Three-dimensional surface: recommendation

**Requirement facts.** Data per surface: rows by columns of IV with a status code; the documented E-1 grid is 6 by 9 = 54 cells per date; the shape is whatever the run contains. Needs: rotate, pan, zoom, reset, hover and focus readout, status patterns, slice planes, a table equivalent, keyboard control. Dependency budget: minimal (CLAUDE.md §13). Browser support requirements: not stated by the owner.

| Option | Fit | Accessibility | Dependencies and size | Compatibility and risk | Verdict |
|---|---|---|---|---|---|
| Heatmap and table only | Fully meets "useful without 3D"; ships first | Best | none | none | **Required in v1** |
| Canvas 2D with a hand-written projection (rotation matrix, painter's algorithm) | Adequate for tens to a few hundred vertices; hover by nearest-vertex pick; patterns drawn directly | Needs the same ARIA, buttons and table | none | Works wherever Canvas works; quality ceiling (no lighting; sorting artefacts if the grid grows) | **Prototype first** |
| Three.js with `WebGLRenderer` and `OrbitControls`, lazy-loaded only on the 3D tab | Best visual quality and camera behaviour; scales if the grid becomes dense | Same fallback requirement | One dependency; size to be measured, not assumed | Broad WebGL support (current support not researched here) | **Adopt if the Canvas prototype is judged inadequate** |
| Three.js `three/webgpu` plus TSL (the `webgpu-threejs-tsl` skill) | TSL's value is compute shaders, node materials and post-processing for large workloads; none is needed to draw tens of vertices | Same | Same dependency, newer API surface | WebGPU availability not researched here; a WebGL or Canvas fallback would still be needed | **Not recommended for v1**; no benefit at this scale |
| Plotly 3D surface | Built-in hover, colour bar, camera | Needs a fallback too | Large dependency | Status patterns on a surface are awkward | Not recommended |

Decision path: build Heatmap and Table in the first milestones; run a bounded DEC-008 feasibility spike comparing Canvas 2D with Three.js (WebGL) on the synthetic run for interaction quality, keyboard operation, status legibility and bundle impact; record the result in `decision.md` and an ADR. Reconsider WebGPU and TSL only if a future grid is dense or a compute-heavy view (many surfaces at once) is required, and only after checking browser support at that time.

## 4. Component hierarchy

`App` > `Shell` (Sidebar, ContextBar, outlet) > `Page` > `Panel` > (`StatusChip`, `SourceChip`, `Table`, `Heatmap`, `Slice`, `Surface3D` (lazy)). Pages own data fetching through `useResource`; components are presentational. Business logic never lives in components: the frontend never computes IV or surfaces, never trains, never holds credentials ([../CLAUDE.md](../CLAUDE.md) §4). Client-side derivations are limited to slicing a row or column, unit display (x100) and formatting.

## 5. Implementation sequence

| Step | Scope | Exit evidence |
|---|---|---|
| M0 | Gate satisfied ([MODEL_HANDOFF §4](MODEL_HANDOFF.md)); owner decisions in §7 made; ADR for the stack | Owner message; ADR |
| M1 | Tokens, fonts, shell, all shared components and states; Landing page (static content only) | Component tests; landing acceptance ([LANDING_PAGE §7](LANDING_PAGE.md)); automated accessibility scan |
| M2 | Typed API client; Explorer with Heatmap, Table, selected cell, slices on the synthetic run | Tests against the `scripts/make_synthetic_run.py` fixture; keyboard walkthrough |
| M3 | Forecast comparison (Actual, Forecast, Difference, counts) | Test with a stored persistence forecast; origin-before-target rejection shown as an error state |
| M4 | Overview, Evaluation, Data & Provenance, Experiments & Pipeline from run tables, manifest and the typed documented content | Matrix traceability check: every number has a source row |
| M5 | Artifacts, Methodology (once the serving route exists) | Links resolve; no dead links |
| M6 | 3D spike, decision, then implementation | Spike report; decision record |
| M7 | Audit: accessibility, responsive, performance, Playwright suite | Recorded results; open issues to KNOWN_LIMITATIONS |

Out of scope throughout: authentication, deployment, training or inference in the UI, any job endpoint, real provider adapters, trading language.

## 6. Testing and validation strategy

- **Unit and component (Vitest):** status chips (icon, label, never colour alone), formatting (decimal to vol points, missing as em dash), `useResource` states, cell-status rendering (every status has its pattern), slice derivation, URL-state round trip.
- **Contract:** the fixture run from `scripts/make_synthetic_run.py` is the only data used in tests; payload types are checked against recorded responses. A real run is never used in CI and never committed (data rules; licence unverified).
- **Browser (Playwright; the `playwright-cli` skill was read, its availability was not checked):** against the local stdlib server with the synthetic run: (1) no console errors and no network request outside the origin (CSP violations are test failures); (2) viewports 390, 768 and 1440 with no horizontal page scroll; (3) `set-color-scheme` dark and light, `set-reduced-motion reduce`, `set-forced-colors active`; (4) keyboard-only walkthrough of the three workflows ([WORKBENCH §4](WORKBENCH.md)); (5) role-based snapshot assertions of empty, error and unlabelled-origin states; (6) a test that every cell status renders a distinct non-colour cue; (7) screenshots of the landing page and the components board for human review (a visual diff alone is not a pass criterion).
- **Accessibility:** automated scan plus a manual keyboard and screen-reader spot check; WCAG 2.2 AA is *targeted*, not claimed, until audited ([../docs/design/ACCESSIBILITY.md](../docs/design/ACCESSIBILITY.md)).
- **Copy scan:** banned phrases (buy, sell, signal, opportunity, "live" for historical data); the landing copy equals LANDING_PAGE §3.
- **Never claim a check passed unless it was run and its output seen** ([../CLAUDE.md](../CLAUDE.md) §10).

## 7. Integration decisions and blockers (none decided here)

1. **DEC-008** frontend stack and 3D technology: open; owner decision after a feasibility prototype.
2. **Static serving and CSP:** the server must gain a path-safe static route for a built bundle and fonts, and the CSP must allow `font-src 'self'` (and `img-src 'self'` if images are used), or the UI must be one self-contained file. This is a backend change; the model session may be editing `api/`; coordinate and obtain owner approval. Not performed here.
3. **Fonts:** self-hosting Geist and JetBrains Mono (licence confirmation needed) or the system fallback stack.
4. **Delivery of documented content** (Docs rows): typed snapshot in the bundle, an API route serving documents, or links out only.
5. **Missing endpoints:** project and pipeline status, experiment history (DEC-010 `PROPOSED`), health (proposed in API_CONTRACTS), plots and report files, per-cell quote lineage (UI-010), stored arbitrage flags.
6. **Run layout:** the notebook's output layout (`surfaces/surface_panel.npz`, nested E-2 folders `e1_nearest/forecasts` and `e2_fixed/forecasts`) differs from the API's expected layout (`panel.npz` with `forecasts/` beside it); a copy step or an API change is required ([IMPLEMENTATION_MATRIX P5d](../docs/engineering/IMPLEMENTATION_MATRIX.md)).
7. **Licence gate for real data:** displaying or storing surfaces derived from the hosted dataset (upstream terms unverified, DEC-002, SEC-006) needs an owner decision. Development uses synthetic runs.
8. **Section set:** owner approval of the Evaluation, Data & Provenance, Experiments & Pipeline, Artifacts structure versus UI-001 ([WORKBENCH §6](WORKBENCH.md)).
9. **Brand assets:** wordmark glyph, icon set.
10. **Housekeeping the owner may want** (CLAUDE.md §12 asks for these with a change; not done here to avoid editing files the model session is changing): a CHANGELOG entry for this directory; a README status-table row; an update of `frontend/README.md`; reconciling the stale statements noted in [MODEL_HANDOFF §3](MODEL_HANDOFF.md).

## 8. Acceptance criteria for the whole implementation

1. The LANDING_PAGE and WORKBENCH acceptance lists pass.
2. Every widget in DATA_WIDGET_MATRIX renders its documented empty and failure states; no placeholder number appears anywhere.
3. Cell status is distinguishable without colour in every view and in forced-colours mode.
4. 3D (if built) and the heatmap show the same values; the table equals both.
5. No external request; CSP intact (or deliberately extended and recorded).
6. Dependencies listed with the §13 notes; no unapproved additions.
7. Tests and scans actually run and their results recorded; gaps recorded in KNOWN_LIMITATIONS.
8. The model, data, training and backend code are unchanged except for the owner-approved static-serving change.
