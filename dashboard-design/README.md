# Dashboard design: Neural Volatility Surface, Quantitative Research Workbench

**Status:** design `PROPOSED`; a first implementation exists in `frontend/index.html`, recorded in [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) (what was built, how it differs from the plan, what was verified). Nothing here is `VALIDATED`. The design documents were produced 2026-10-16 in a design-only session; the model, data, backend and training code were not touched by either phase.

**Scope boundary:** this directory sits beside, and does not replace, the existing design docs ([../docs/design/](../docs/design/), [../design.md](../design.md)). Where they differ, the differences are listed in [WORKBENCH.md §7](WORKBENCH.md). Requirement IDs (`UI-0xx`, `SCI-`, `DATA-`) come from [../PR.md](../PR.md). Open decisions (DEC-008 frontend stack, DEC-007 API framework, DEC-009 storage) stay open; every stack statement here is a **proposal**.

## 1. Files

| File | Contents |
|---|---|
| [LANDING_PAGE.md](LANDING_PAGE.md) | Landing page structure, canonical copy, visual direction, interactions |
| [WORKBENCH.md](WORKBENCH.md) | Workbench information architecture, per-screen design, 3D explorer requirements |
| [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) | Tokens (dark and light), type, status system, cell encodings, components, accessibility |
| [DATA_WIDGET_MATRIX.md](DATA_WIDGET_MATRIX.md) | Every widget mapped to its source, availability and states |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | Proposed stack, 3D recommendation, sequence, acceptance, validation strategy |
| [MODEL_HANDOFF.md](MODEL_HANDOFF.md) | What the model session must deliver, and the exact gate before implementation |

## 2. Product vision and users

**Neural Volatility Surface, Quantitative Research Workbench** is where a researcher constructs, inspects and honestly evaluates implied-volatility (IV) surface forecasts. Guiding principle ([../CLAUDE.md](../CLAUDE.md) §1): *make every forecast inspectable, every experiment reproducible, and every limitation visible.* It is a research and education tool, not a trading product.

Users (from [../docs/project/VISION.md](../docs/project/VISION.md) and PR.md; not new personas): the project owner and collaborating quant researchers who need to read a surface, compare a forecast with the actual surface and with baselines, and trace any number to its data; and technically literate reviewers who need the limitations stated plainly.

Two experiences, one product:

1. **Landing page** (light, editorial) introduces the research problem and states what is and is not established.
2. **Research workbench** (dark, instrument-like) is the working environment: Overview, Surface Explorer, Evaluation, Data & Provenance, Experiments & Pipeline, Artifacts, Methodology & Documentation.

## 3. Audit of the current interface

**What exists (verified by reading the files):** `frontend/index.html`, 152 lines, no build, no dependencies, served by `backend/src/volatility_lab/api/server.py`. One 960px column: a run selector, a date slider, a banner, an IV table (status shown by symbol and colour), a forecast-versus-actual trio of tables, a lineage list, a result-table viewer. Tests: `backend/tests/unit/test_api.py`. It was opened once in the in-app browser against a synthetic demo run ([../docs/engineering/IMPLEMENTATION_MATRIX.md](../docs/engineering/IMPLEMENTATION_MATRIX.md) P5b). No screenshot file exists in the repository.

**Strengths to keep:** honest origin banner (synthetic, real, unlabelled); status by symbol as well as colour; units stated; lineage with a panel-hash check; no claim beyond "descriptive"; table as the accessible alternative to a surface.

**Weaknesses (design review, not a detector run):**

| Area | Finding |
|---|---|
| Hierarchy | Everything is an `h2` over a table; no focal point, no "what should I look at" entry. The most important object (the surface) has the same weight as a lineage list. |
| Information architecture | One scrolling page. No separation of exploring, evaluating, data provenance, project state. The eight sections in PR.md UI-001 are not reflected. |
| Density and legibility | Tables of unformatted numbers, 4px padding, 1px borders on every cell; status carried by a 15px glyph inside a cell. |
| Project state | Nothing tells a visitor that Phase 0 is incomplete, that the data licence is unverified or that models were evaluated only descriptively. The origin banner is the only honesty surface. |
| Surface perception | A grid of numbers cannot show skew or term structure. No heatmap, slices or 3D view. |
| Responsiveness | `max-width:960px`, horizontal scroll for tables, no layout adaptation. |
| Components | No shared tokens, status chips, empty/loading/error states (only a text banner). Errors render as raw `Error: <url> -> <status>` text. |
| Typography | `system-ui` only, one size scale, no distinction between identifiers and prose. |

**The earlier Stitch mock (deleted at the owner's request)** had the opposite fault: a cockpit-dense terminal look, 11px monospace labels, borders everywhere and invented content (a "FastAPI" label, parquet file names). Both are rejected: the target is calm and legible *and* strictly sourced.

## 4. Design thesis

- **Honesty is the visual language.** Cell status (observed, interpolated in tenor, interpolated in strike, missing, predicted) is encoded by colour **and** pattern everywhere. Every value carries a source chip: *Documented* (read from project documents), *Live from run* (read from the research API), *Not connected*.
- **Calm over cockpit.** Large type, tone steps instead of borders, one accent, generous space.
- **The idea of the landing page** (impeccable and design-taste-frontend "find the idea"): the project's own distinctive device, the per-cell status grid, becomes the hero. No competing vol tool shows a surface as *what was observed versus what was filled in*.
- **A 3D surface is never the only view.** Heatmap and table are mandatory equivalents (UI-009; ACCESSIBILITY.md §4).

## 5. Stitch artifacts (actual)

Stitch MCP was available and used. All designs are **private** to the owner's Stitch account. The tool does not return a shareable URL, so none is recorded; open by project id.

- **Project:** `projects/12422249893300284222`, "Neural Volatility Surface — Quantitative Research Workbench"
- **Design systems:** `assets/15502535519750022530` "NVS Workbench (dark)"; `assets/2088746606350607947` "NVS Landing (light)". Models: Gemini 3.5 Flash-Lite (3.8 Flash timed out).

| Screen | Device | Final screen id |
|---|---|---|
| Landing page | Desktop | `fd9bdd5b9ea848c5b170086cf396ff23` |
| Research overview | Desktop | `40cf2f6d0c444790b26bb856346823a7` |
| Surface Explorer | Desktop | `3cce6b6bc84a423eb9b5a6d3ebd17753` |
| Evaluation | Desktop | `eb6ec00c2f594488806a93c5209ea34d` |
| Data & Provenance | Desktop | `f215b07c70ca4be488c4a8914d341c3c` |
| Experiments & Pipeline | Desktop | `ce4c96df0a204394b692a7f457d9029d` |
| Components and states | Desktop board | `87b01e179b024dc69563d93847bef14d` |
| Surface Explorer | Mobile (390) | `c192bb55326a4450a3554f08b01d3b22` |

**Superseded versions** (Stitch has no delete-screen tool; ignore these): `236528edbf8d480984809d9d506051eb`, `5b72f4b3994c4e34b32204f2b2d5414c`, `326c554c2c9d44e9ade32003518368f9` (landing); `c3157c427def430c8bf7f20f1ec8a8bf` (overview); `bfd72e3b7211467fb58271b7ca94c178`, `cee8ff3cf1fc4ce19836f39a80875c21` (explorer); `16e3443d8188422dbf3c53381a23f30d` (evaluation); `e7555b8654a449198499d90d57d87cfb` (experiments); `2b0a37ea12524b9a964f6d3bdc8c543b` (components); `fc98a8af37834d4c99e502f4dc0e10d2` (mobile).

**Not designed in Stitch** (specified in text only, [WORKBENCH.md](WORKBENCH.md)): Artifacts, Methodology & Documentation, mobile landing, tablet layouts, light-theme workbench, pinned-cell lineage drill-down.

### Known limitations of the Stitch output (read before using the screens)

1. **Stitch text is not authoritative.** It repeatedly invented content (a FastAPI label, file names, extra nav items such as "Risk Matrix", "Run Model" buttons, footer legal links). These were removed by edit passes and the generated HTML was scanned for the known strings; the scan found none in the final Landing, Experiments and Components screens. The copy in these documents is canonical; a screen is evidence of layout and style only.
2. **The 3D surface is not convincingly rendered.** Stitch drew curved lines rather than a mesh on the Explorer and a near-empty frame in the landing preview. The intended 3D behaviour is specified in [WORKBENCH.md §5](WORKBENCH.md).
3. **Landing page support lines.** One edit to replace invented supporting lines under the capability names did not apply to every row (the "Experiment history view" line still reads "Archival record of past hyperparameter sweeps and model evaluations", which describes a planned feature in invented terms). Use the copy in LANDING_PAGE.md §3.
4. **Mock copy to correct in implementation:** the Experiments screen says "Failures recorded: none."; the canonical wording is "No failures are recorded in the project documents." (absence of a record is not a guarantee). The Data screen numbers the transformation steps 01 to 06; numbering is not used in the design language.
5. **Stitch mocks use first-pass status colours** that fail 4.5:1 as text on some surfaces. DESIGN_SYSTEM.md §2 holds the corrected, computed tokens; those win.
6. **Not re-inspected after the final edit pass:** Overview v2, Evaluation v2 (numbers confirmed by text extraction against E1_RESULTS), Components final and Mobile final (text scanned only). Stitch's stray `col-span-8) -->` text appears in the Explorer HTML source as a malformed comment from the first generation.
7. Spot checks only: the figures on the Evaluation and Data screens were compared with E1_RESULTS.md §2, §3 and §5. They are real documented numbers, labelled *Documented*, and are not live results.

## 6. Skills and tools actually used

| Skill or tool | What was done | What was not done |
|---|---|---|
| Stitch MCP | Created project, two design systems, 8 final screens, ~10 edit passes; downloaded screenshots and HTML to a scratch folder to review them | No export of assets into the repository |
| `ui-ux-pro-max` | Ran its `--design-system` and `--domain chart` searches (stdout only, nothing persisted). The chart result drove the "heatmap and table beside any 3D view" rule. The design-system result recommended a "Portfolio Grid" pattern, which is irrelevant here and was discarded; style and colour suggestions were not adopted | `--persist` (would have written `design-system/`) |
| `apple-design` | Read; applied: restraint, hierarchy through weight and spacing, reduced-motion and reduced-transparency, tracking by size, system-font fallback | Spring/gesture motion (no interactive prototype) |
| `impeccable` | Read SKILL.md and the critique reference; performed the critique manually (specificity, hierarchy, cognitive load, mode: *Persuade* for landing, *Operate* for workbench) | **Its launcher was not run** (it downloads and executes a binary on first use; the checked-in scripts folder has no binary). No detector, no sub-agent critique, no live browser pass |
| `stitch-design-taste` | Used its DESIGN.md structure for both design-system briefs (atmosphere, palette roles, type, components, layout, motion, anti-patterns) | |
| `design-taste-frontend` | Read; applied its house rules to the landing page (no eyebrows, numbering, hairline rules, gradients, icon-card rows; two-line headline; the "idea from the subject" step) | Its `draw`, `assets` and `inspect` scripts (no page was built) |
| `high-end-visual-design` | Read; **mostly rejected**: glass nav, double-bezel cards, mesh-gradient and heavy scroll motion conflict with a precise research tool and with the project's no-decoration rule. Kept: macro-whitespace, no hairline borders, GPU-safe motion | |
| `dataviz` | Read; applied: cell-status colour plus pattern, diverging zero-centred scale, legend and table fallback | Its palette validator was not run; contrast was computed directly instead |
| `webgpu-threejs-tsl` | Read SKILL.md; evaluated for the 3D explorer ([IMPLEMENTATION_PLAN.md §3](IMPLEMENTATION_PLAN.md)) | No example run, nothing installed |
| `playwright-cli` | Read; a validation strategy is in IMPLEMENTATION_PLAN.md §6 | Not run; whether it is installed was not checked |

Conflicts between skills were resolved by project rules first (honesty, accessibility, no decoration), then clarity.

## 7. Outstanding decisions and blockers

See [IMPLEMENTATION_PLAN.md §7](IMPLEMENTATION_PLAN.md) and [MODEL_HANDOFF.md §5](MODEL_HANDOFF.md). The largest: DEC-008 (frontend stack) is open; the API server serves one HTML file under a CSP that blocks external fonts, images and scripts; there is no endpoint for documents, experiments or project status; real derived data in a UI is gated by the unverified hosted-dataset licence.
