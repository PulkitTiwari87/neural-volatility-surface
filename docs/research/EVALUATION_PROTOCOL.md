# Evaluation Protocol

**Status:** PROPOSED · **Canonical for:** data splitting, walk-forward procedure, metrics, regional/regime reporting, robustness checks, success criteria template · **Source:** MP §14, §15, §21, §24 · **Related:** guardrails GR-LEAK, GR-MOD · [FORECASTING_STRATEGY](FORECASTING_STRATEGY.md)

## 1. Splitting (MP §14)
- Train on the earliest period → validate on a later period (model selection) → test on a **final untouched** period. Never shuffle dates.
- **Horizon-aware gap:** if the label for origin *t* is observed at *t+h*, no training label may extend into the validation/test period; insert a gap/embargo of at least the label horizon plus any feature lookback overlap where features and labels overlap (GR-LEAK-01).
- Window lengths, number of folds: set in Phase 0 from the minimum viable dataset (`TBD(Phase 0)`).

## 2. Walk-forward (rolling-origin) procedure
For each origin *t* in the evaluation period: fit (or update) using data strictly before *t* (respecting the gap) → predict the target at *t+h* → score against the realized surface → advance. Scalers/preprocessing are fit inside each fold on the fold's training view only. Retrain cadence (every origin vs periodic) is a recorded configuration. Expanding vs rolling training windows are compared as a robustness check.

## 3. Metrics (MP §14)
Let *C_t* be the set of comparable cells at origin *t* (grid cells `observed` in the realized target surface and available in the forecast). Notation: ŷ forecast IV, y realized IV, N = Σ|C_t|.

- **MAE** = (1/N) Σ |ŷ − y|; **RMSE** = √((1/N) Σ (ŷ − y)²).
- Unit: computed on **decimal IV**; also reported in **vol points** (×100) with the unit in every header — never mixed.
- **Relative to persistence:** ratio and difference of model vs persistence for the same cells/origins (e.g., MAE_model / MAE_persistence); persistence is the reference baseline.
- **Directional accuracy** (only if "direction of change" is a defined target): share of cells where sign(ŷ − y_t) = sign(y_{t+h} − y_t), with ties and tolerance rules defined.
- **Interval metrics** (only if intervals are produced): empirical coverage vs nominal, interval width, calibration plots ([UNCERTAINTY_AND_CALIBRATION](UNCERTAINTY_AND_CALIBRATION.md)).
- **Stability:** dispersion across folds, seeds, and periods.

Every metric table includes `n` (cells), `n_origins`, `n_missing` (cells excluded as not comparable) and what was excluded.

*Phase 0 synthetic note ([PHASE0_SYNTHETIC_RESULTS](PHASE0_SYNTHETIC_RESULTS.md) §7, hypothesis Q-27):* when the target surface carries quote noise, a structure-aware forecaster can beat raw persistence slightly even where persistence is optimal for the latent surface. Reports should therefore state whether targets are raw observed cells or denoised, and keep persistence-on-raw as the primary reference.

## 4. Regional and regime reporting
- **Regions:** maturity buckets × moneyness buckets (bucket edges set from grid, `TBD(Phase 3)`), plus overall. Cells with `n` below the minimum (`TBD(Phase 3)`) are labelled *insufficient*, not dropped.
- **Periods:** by calendar blocks / folds.
- **Regimes:** calm vs stressed, defined by a documented rule using only past data (e.g., trailing realized or implied volatility level thresholds — specification `OPEN`); event windows (earnings/macro) only from as-of-known calendars.
- **Liquidity:** liquid vs less-liquid regions defined by quote-quality measures.

## 5. Robustness checks (MP §14)
Multiple historical periods · calm vs stressed regimes · alternative quote filters · alternative interpolation policies · liquid vs illiquid regions · dependence on few dates/contracts (leave-k-dates-out influence) · feature-group ablations · expanding vs rolling windows · report failure cases (worst-N origins with links to surfaces).

## 6. Test-window discipline
The test window is evaluated **once per frozen configuration**; accesses are logged in the run record (GR-LEAK-05). If the test window is consumed for a decision, a new untouched period is required or the result is relabelled exploratory.

## 7. Comparing models with dependent forecasts
Daily surfaces are serially dependent, so naive cell-level t-tests overstate significance. Approach to be selected in Phase 3 (`NEEDS RESEARCH`): block bootstrap over origins and/or Diebold–Mariano-type tests on per-origin loss differentials with an appropriate long-run variance estimator. Whatever is chosen is documented, tested on synthetic data with known differences, and reported alongside effect sizes. Do not claim "significant" without it.

## 8. Success criteria (pre-registered in Phase 0; template)
*Proposed values for this project (unfrozen) are in [PHASE0_FEASIBILITY_PLAN](PHASE0_FEASIBILITY_PLAN.md) §3; the template below is the record format.*
```
Date registered: ____    Registered by: ____
Primary comparison: model X vs persistence (and vs regression) on dataset version __
Primary metric & unit: ____   Cells: ____   Period/folds: ____
Evidence threshold (decided now, not later): ____ (e.g., effect-size and uncertainty rule)
Secondary analyses (labelled exploratory): ____
Acceptable outcomes: improvement / no improvement / mixed by region — all reported
Deviations log: ____
```

## 9. Report schema (minimum fields)
Experiment ID · hypothesis · dataset/feature/surface/filter versions · windows and gaps · scheme (`walk_forward` | other, labelled exploratory) · models and seeds · metrics by region/period/regime with `n`,`n_missing` · comparison vs baselines with variability · robustness results · failure cases · limitations · test-access count · code/config hashes.

## 10. Validation of this protocol
Hand-calculated metric examples (MP §21); synthetic data where the true best model is known (e.g., AR process → AR beats persistence; random walk → persistence unbeatable) to verify the pipeline neither invents nor hides improvement; determinism test; leakage tests (GR-LEAK).

> Note 2026-10-21: the statistical-method search for dependent forecasts is CLOSED - NO-GO (PA-1, decision.md; PHASE0_CLOSURE_RECORD section 7); no inferential claim is made, so the text above that leaves the test "to be selected in Phase 3" describes a closed question. AP-008 (owner-approved) fixes contract-level scoring against B0a and B0b as the primary protocol for a future authorized evaluation, one primary contrast per stage with a trial ledger, and a prespecified minimum effect r* (numeric value not frozen); see decision.md "AP-008".

> Note 2026-10-21 (D11a): the owner approved, as specification text, the contract-level definitions needed by that protocol: hull, hull coverage, evaluation locations (forecast and B0b at target-day coordinates, B0a at origin-day coordinates), one scored population with named counts (`n_missing`, `n_new`, `n_unusable`), the per-origin equal-weight score with a vega-weighted secondary, the primary reference (stronger of B0a and B0b on the development period) and the trial-ledger schema. The canonical text is docs/architecture/STORAGE_DESIGN.md section 8.8 (D11a sub-table); it is not repeated here. Not implemented; the numbers (r*, fallback threshold, N*, c, rho) stay deferred.
