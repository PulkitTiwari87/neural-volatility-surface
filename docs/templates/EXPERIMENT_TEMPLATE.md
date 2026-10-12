# Experiment Record — `<EXP-ID>`

> Copy this template for every experiment. Fill **hypothesis, success criteria, and windows before running** (pre-registration). Never edit a completed record to change its outcome; add a new version with a reason. Status: `PLANNED | IN_PROGRESS | COMPLETE | INVALIDATED`.

## 1. Identification
- **Experiment ID / version:** 
- **Date registered (pre-run):** 
- **Author / role:** 
- **Phase:** 
- **Related requirement / research question / decision IDs:** (FR-, SCI-, RQ-, DEC-)
- **Type:** `confirmatory (frozen protocol)` | `exploratory (not evidence)`

## 2. Hypothesis and success criteria (pre-registered)
- **Hypothesis:** 
- **Null / acceptable outcomes:** (include "no improvement")
- **Primary comparison & metric (with unit):** 
- **Evidence threshold decided in advance:** 
- **Secondary analyses (exploratory):** 

## 3. Data (versions, not paths)
| Item | Value |
|---|---|
| Source & snapshot ID(s) | |
| Data mode | historical / delayed / latest available / real-time licensed |
| Processing / normalizer version | |
| Quote-policy config hash | |
| Pricing / IV method & assumption-set ID | |
| Coordinate convention & version | |
| Grid ID; interpolation method + version | |
| Feature catalog version; dataset ID | |
| Origin count; date range; cell counts; missingness | |
| Licence class of data used | |

## 4. Splits and protocol
- **Scheme:** `walk_forward` | other (state → exploratory)
- **Train / validation / test windows; gaps/embargo:** 
- **Folds and retrain cadence:** 
- **Leakage checks run (list tests + results):** 
- **Test-window access count (must be 0 during selection):** 

## 5. Models
| Model | Type | Config hash | Seeds | Parameters/size | Code version |
|---|---|---|---|---|---|
| Persistence (baseline) | | | n/a | | |
| Regression (baseline) | | | | | |
| … neural … | | | | | |

Hyperparameter search: space, budget, selection data (validation only):
Environment: dependency versions, hardware, training dates:

## 6. Results
Metrics **by region (maturity × moneyness), period, regime** with `n`, `n_missing`, unit (decimal / vol points). Compare to persistence and regression on identical cells/origins; report variability across seeds/folds/periods.

| Region / period / regime | n | n_missing | Persistence | Regression | Model | Δ vs persistence | Variability |
|---|---|---|---|---|---|---|---|

- **Robustness checks (periods, regimes, quote filters, interpolation, liquidity, ablations):** 
- **Failure cases (worst origins, links):** 
- **Uncertainty (kind; coverage evidence if any):** 

## 7. Interpretation (bounded by evidence)
- **What the evidence supports:** 
- **What it does not support:** 
- **Deviations from the pre-registered plan:** 

## 8. Limitations and threats to validity
(Data, model, leakage risk, sample size, regime coverage, multiple comparisons)

## 9. Reproducibility
- **Command / entry point and config reference:** 
- **Re-run result (reproduced within tolerance? date):** 
- **Artifacts (IDs/hashes):** 
- **Creation timestamp:** 

## 10. Sign-off
Reviewer / date / outcome:
