# Landing page

**Status:** `PROPOSED` design. Stitch screen `fd9bdd5b9ea848c5b170086cf396ff23` (light system `assets/2088746606350607947`) shows layout and style only; **the copy below is canonical** (see [README §5](README.md) for the Stitch deviations). Mode: *Persuade* (a visitor decides whether and where to go next). Tokens: [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md).

## 1. Intent and idea

The landing page introduces the problem before users enter the workbench, and uses transparency as the product's differentiator.

**The idea.** On this page, *the per-cell status of an implied-volatility surface (observed, interpolated, missing)* becomes *the hero graphic*. The project's own rule, that a filled-in value must never look like an observation, is also the thing no other vol tool draws. The competitor test: another volatility dashboard cannot reuse the sentence, because they colour a surface by level, not by evidence.

**One live thing** (preview section): choose a tenor and see which row of the grid it highlights, with the cell-status legend. It is a conceptual illustration, not data.

## 2. Page structure

| Order | Section | Composition | Purpose |
|---|---|---|---|
| A | Navigation | Plain bar (no glass, no pill): wordmark + subtitle; Home, Workbench, Methodology, Data & Provenance, Documentation; one primary button | Orientation; every link maps to a supported destination |
| B | Hero | Left text column, large two-line headline; right, a dark graphite "instrument plate" with the conceptual 6 by 9 status grid; metadata line under it | First impression, one call to action |
| C | What this project investigates | Two-column split: heading and the documented-finding statement left, plain paragraphs right | The research problem, evaluation approach, limits |
| D | What the workbench does | Open list on the page ground (no card container): capability, one muted line, state chip aligned right | Capabilities with honest state |
| E | Research workbench preview | Full-width dark plate: tenor control, conceptual wireframe surface, "Cells by status" panel, one button | Product preview without fabricated numbers |
| F | Research workflow | Single horizontal timeline: line, node icon, stage name, state under the name | The real pipeline |
| G | Data integrity and limitations | Soft tone-step field: cell-kinds legend left, status list right | Provenance and what is unverified |
| H | Documentation and footer | Two-column text-link list; plain footer | Resources and disclaimer |

Rules inherited from the design language (design-taste-frontend house rules): no eyebrow labels, no 01/02 numbering, no hairline rules, no gradients, no shadows at rest, no icon-topped card rows, no three equal cards, headline at most two lines at every width. Monospace only for identifiers.

## 3. Canonical copy

**A. Navigation.** Wordmark "Neural Volatility Surface"; subtitle "Quantitative Research Workbench". Links: Home, Workbench, Methodology, Data & Provenance, Documentation. Button: "Open Research Workbench".

**B. Hero.**
- Headline: "See the structure behind volatility."
- Support: "Explore implied-volatility surfaces, examine model behavior, and evaluate quantitative forecasts through a transparent research workflow."
- Primary: "Open Research Workbench". Secondary text link: "Explore Methodology".
- Plate heading: "Surface status grid, conceptual illustration". Axes: "Tenor (days)" (rows 7, 14, 30, 60, 91, 182), "Log-moneyness k" (9 nodes). Legend: Observed, Interpolated in tenor, Interpolated in strike, Missing. Caption: "Conceptual illustration. Not a model output."
- Metadata line (source: [../docs/research/E1_RESULTS.md](../docs/research/E1_RESULTS.md) §1): "SPY end-of-day options, 2010 to 2023 · Backtest only · Upstream data licence unverified".

The grid dimensions (6 tenors by 9 nodes) are the documented E-1 grid ([E1_RESULTS §2](../docs/research/E1_RESULTS.md)); the actual shape is whatever the run's panel contains.

**C. What this project investigates.**
"An implied-volatility surface describes how the market prices options across strikes and expiries. This project constructs those surfaces from option quotes, forecasts how they change from one day to the next, and compares every forecast against simple baselines such as persistence."

"Forecasts are judged out of sample, in chronological order, with the number of cells behind every figure shown. Results so far are descriptive: no claim of statistical significance, calibration or trading value is made."

Statement (chip "Documented, descriptive only"): "Recorded in experiment E-1: neither neural architecture beat the persistence baseline on pooled error." Source: E1_RESULTS §4. This is a snapshot of a recorded result; revisit it whenever the model session changes the results.

**D. What the workbench does.** State vocabulary: Completed, In progress, Planned ([DESIGN_SYSTEM §2](DESIGN_SYSTEM.md)). Source for each row: [../docs/engineering/IMPLEMENTATION_MATRIX.md](../docs/engineering/IMPLEMENTATION_MATRIX.md).

| Capability | Supporting line | State |
|---|---|---|
| Surface construction | Quote validation, parity forward and implied-volatility inversion. | Completed |
| Per-cell surface status | Every cell is observed, interpolated or missing, and never extrapolated. | Completed |
| Baseline and neural forecasts | Evaluated walk-forward against simple baselines. | Completed |
| Leakage audit | Checks that features use only information available at the forecast date. | Completed |
| Static-arbitrage flags | Calendar and butterfly checks. Necessary conditions only. | In progress |
| Two-dimensional surface viewer | A table of one stored run, shown locally. | Completed |
| Three-dimensional surface explorer | Planned. | Planned |
| Experiment history view | Planned. | Planned |

Note: today's viewer is a table of one stored run (plus forecast-versus-actual tables). The heatmap belongs to the redesign; extend the viewer row to mention it only when it ships.

**E. Preview.** Heading "Research workbench preview". Tenor control: 7d, 14d, 30d, 60d, 91d, 182d. Badge "Conceptual preview, no run loaded". Panel "Cells by status": Observed, Interpolated in tenor, Interpolated in strike, Missing, each "—". Button "Open Research Workbench". The mesh is a clearly labelled static illustration; there are no numbers anywhere in it.

**F. Research workflow** (stage, state; source IMPLEMENTATION_MATRIX §6 and E1_RESULTS §2): Data acquisition (Completed, hosted dataset); Validation (Completed); Implied-volatility inversion (Completed); Surface construction (Completed); Feature extraction (Completed); Model training and evaluation (Completed, descriptive); Three-dimensional explorer (Planned). Do not show licensed-provider acquisition as completed; it is blocked ([DATA_WIDGET_MATRIX](DATA_WIDGET_MATRIX.md) D3).

**G. Data integrity and limitations.** Left, "Surface-cell kinds": Observed; Interpolated in tenor; Interpolated in strike; Missing; Predicted (each with its pattern swatch). Right, status list:

| Item | State |
|---|---|
| Upstream licence of hosted dataset | Unverified |
| Licensed provider access | Unavailable |
| Real-data evaluation | Completed, one underlying, descriptive |
| Statistical inference | Not pursued |
| Model validation | Unverified |

Sources: [../docs/data/HOSTED_DATASET_ASSESSMENT.md](../docs/data/HOSTED_DATASET_ASSESSMENT.md), [../docs/research/PHASE0_CLOSURE_RECORD.md](../docs/research/PHASE0_CLOSURE_RECORD.md), KNOWN_LIMITATIONS L-22 to L-25. "Not pursued" reflects the owner's 2026-10-13 stop of the statistical-method search ([../CLAUDE.md](../CLAUDE.md) status line).

**H. Documentation.** Links: Research methodology, Known limitations, Data dictionary, Experiment E-1 results, Experiment E-2 results, Reproducibility notebooks (targets: `docs/research/RESEARCH_METHODOLOGY.md`, `KNOWN_LIMITATIONS.md`, `docs/data/DATA_DICTIONARY.md`, `E1_RESULTS.md`, `E2_FIXED_EXPIRY_RESULTS.md`, `notebooks/`). Footer: wordmark; "Research and education only. Not investment advice and not a trading product."; links Methodology, Data & Provenance, Documentation. **No** Privacy, Terms, Security or System Status links: those destinations do not exist.

How these links resolve (the API does not serve documents) is an open integration decision, [IMPLEMENTATION_PLAN §7](IMPLEMENTATION_PLAN.md).

## 4. Visual direction

Light mineral-grey ground (`#F3F5F7`), graphite ink, one accent (Deep Ice `#1F6F99`), one dark instrument plate per viewport at most. Geist throughout; headline 72 to 88px desktop, tracking -0.035em, leading 0.98; body 18px/1.6, 62 characters maximum. Section gaps 120 to 160px; large things run to the margins. Each section uses a different composition from its neighbour. See DESIGN_SYSTEM.md for values and contrast.

The hero plate reuses the workbench's tokens exactly so the transition into the workbench is continuous (the plate is the product).

## 5. Interactions

- Entrance: each section's heading, then text, then plate fades up 16px, staggered 60 to 90ms, once. Content is visible without script. `prefers-reduced-motion`: no travel, content shown.
- The tenor control in the preview highlights the corresponding row of the conceptual grid; keyboard operable (arrow keys), 44px targets, visible focus.
- Primary button pressed state: 1px translate. No hover-only information.
- No autoplay, no parallax, no scroll-jacking, no cursor effects.

## 6. Accessibility

Conceptual grid: `role="img"` with a text description ("Conceptual 6 by 9 grid of cell statuses; not model output") and the legend as real text; the grid is not in the tab order (the tenor control is). The headline is a real `h1`. Status chips: icon and text. Contrast values in DESIGN_SYSTEM §2.

## 7. Acceptance (future implementation)

1. Every sentence in §3 appears verbatim; no number appears that is not in §3.
2. The conceptual illustration carries its visible label at every viewport.
3. Headline at most two lines at 390, 768 and 1440 px; no horizontal scroll at 390.
4. No link to a non-existent destination.
5. Automated accessibility scan clean for the page (tools chosen with DEC-008).
