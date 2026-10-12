# Research Methodology

**Status:** PROPOSED · **Canonical for:** the overall scientific method and reporting standard · **Source:** MP §1, §4, §13–§15, §19, §24 · **Details:** [IV_METHODOLOGY](IV_METHODOLOGY.md), [SURFACE_CONSTRUCTION](SURFACE_CONSTRUCTION.md), [FEATURE_CATALOG](FEATURE_CATALOG.md), [FORECASTING_STRATEGY](FORECASTING_STRATEGY.md), [EVALUATION_PROTOCOL](EVALUATION_PROTOCOL.md), [UNCERTAINTY_AND_CALIBRATION](UNCERTAINTY_AND_CALIBRATION.md), [KNOWN_LIMITATIONS](KNOWN_LIMITATIONS.md)

## 1. Research question and hypotheses
**Question (MP §1):** given the option market at time *t*, how accurately can a model forecast the IV surface at a future horizon (first: next valid trading session)?

| ID | Hypothesis | Status | Falsified by |
|---|---|---|---|
| H-1 | A lower-dimensional surface representation forecasts more stably than raw grid forecasting when history is limited (MP §12). | HYPOTHESIS | Grid model equal/better out of sample across periods |
| H-2 | A neural model improves on persistence/regression in some surface regions or regimes (MP §13). | HYPOTHESIS | No out-of-sample improvement beyond variability across seeds/folds |
| H-3 | Forecast errors concentrate in short maturities, wings, stressed regimes, and event dates (MP §4). | HYPOTHESIS | Errors uniformly distributed |

The null outcome for H-2 ("the neural model does not help") is a valid, reportable result.

## 2. Principles
1. **Pre-register** hypotheses, metrics, success criteria and data windows before looking at evaluation results; record the date. Deviations are documented.
2. **Baselines first**; complexity must earn its place with out-of-sample evidence (MP §13).
3. **Chronological evaluation only** for primary claims; final test window used once per frozen configuration.
4. **Report distributions, not single numbers:** per-region, per-period, per-regime, with sample counts, across seeds and folds.
5. **Separate exploration from confirmation.** Exploratory analyses (notebooks) are labelled and never cited as evidence; confirmatory runs use frozen configs and recorded versions.
6. **Show failure:** worst cases, instability, and negative results are part of the record.
7. **No causal language** from explainability outputs (MP §15).

## 3. Workflow
```
Define question & success criteria (pre-registered)
 → select data & verify licence (Phase 0)
 → build validated quotes → IV → surfaces (Phases 1–2), sensitivity analysis on filters/interpolation
 → build leakage-safe dataset & baselines (Phase 3)
 → neural experiments with frozen protocol (Phase 4)
 → robustness: periods, regimes, quote filters, interpolation, liquidity, ablations
 → report incl. limitations → reproduce from record
```

## 4. Experimental design rules
- Unit of analysis: a (forecast origin, grid cell) pair; the unit of *independence* is the origin date (surfaces on consecutive days are highly dependent). Uncertainty about performance comparisons must account for this dependence (method in EVALUATION_PROTOCOL).
- Compare models on **identical** origins, cells, and masks.
- Hyper-parameter search uses validation windows only; the search budget is recorded to limit selection bias.
- Seeds: multiple seeds for stochastic models; report spread.
- Any change to data, filters, grid, or features creates a new dataset/feature version; results are never silently re-labelled.

## 5. Reporting standard
Every result is an experiment record ([EXPERIMENT_TEMPLATE](../templates/EXPERIMENT_TEMPLATE.md)) containing the SCI-013 fields, hypothesis, baselines, metrics with `n`/`n_missing`, results (positive and negative), failure cases, and limitations. Narrative claims are bounded by the evidence ("In period X on grid region Y, model M's MAE was lower than persistence by …, across N origins; not significant in …").

## 6. Validation of the methodology
Phase gates in [IMPLEMENTATION_PLAN](../../IMPLEMENTATION_PLAN.md); guardrails GR-LEAK and GR-MOD; reproduce-from-record test (AC-12).

## 7. Open items
Regime definitions (OPEN); minimum sample sizes (`TBD(Phase 3)`); choice of statistical comparison method for dependent forecasts (NEEDS RESEARCH, see EVALUATION_PROTOCOL §7).
