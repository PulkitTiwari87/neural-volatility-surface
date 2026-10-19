# Phase 2 evidence: IV recovery, interpolation methods and quote-filter policies (2026-10-16)

> **SYNTHETIC data only. This document decides nothing.** DEC-006 stays `NEEDS RESEARCH`; the Phase 2 gate is **not met**. No real market data was read, downloaded or generated. All numbers below were produced by the commands in §7 and are reproducible (identical SHA-256 on two runs). Descriptive only: no significance claim (L-22).

## 1. What was added

| Item | Where | Tests run |
|---|---|---|
| Known-volatility recovery grid, bounds and invalid-input tests (GR-QNT-01/02/06) | `backend/tests/scientific/test_iv_recovery.py` | 9 tests, OK |
| Candidate interpolators and comparison harness (research code, **not adopted**) | `backend/src/volatility_lab/surfaces/compare_methods.py` | 13 tests in `tests/scientific/test_interpolation_comparison.py`, OK |
| Reproduction script | `scripts/phase2_surface_comparison.py` | run twice, identical output hash |
| Fitted-baseline leakage sentinels (GR-LEAK-02/04) | `backend/tests/scientific/test_leakage_sentinels.py` | 3 tests, OK |

`surfaces/grid.py` (production behaviour: linear in k on IV, linear in total variance in T, no extrapolation) was **not changed**.

## 2. IV recovery (GR-QNT-06, Phase 2 A1)

**Fixture.** Black-76 prices on a deterministic grid: σ ∈ {0.05, 0.10, 0.20, 0.40, 0.80, 1.50, 3.00} × T ∈ {1, 2, 7, 30, 91, 182, 365, 730} days × ln(K/F) ∈ {−0.5 … +0.5} (9 nodes) × call/put = 1,008 cells, at F = 100 and F = 4500.

**Tolerances (declared in the test file, derived from float64 conditioning, set before the results were viewed).** Reprice residual ≤ 1e-10·F for every `OK`; recovery error < 1e-7 wherever vega ≥ 1e-4·F (the quote identifies σ); every other `OK` cell must be explained by vega below that floor; non-`OK` only when the price is indistinguishable from a no-arbitrage bound.

**Observed (both F):**

| Quantity | Value |
|---|---|
| Cells | 1,008 |
| Status `OK` / `BELOW_LOWER_BOUND` / `ABOVE_UPPER_BOUND` / `INVALID_INPUT` | 886 / 122 / 0 / 0 |
| Identifiable cells (`OK`, vega ≥ 1e-4·F) | 702 |
| Max \|iv − σ\| over identifiable cells | 2.2e-12 (F = 100), 2.7e-12 (F = 4500) |
| `OK` but not identifiable (deep in-the-money, tiny vega) | 184; max error 1.4e-3 (F = 100) |
| Scale invariance F = 100 vs 4500 | passes |

All 122 non-`OK` cells are prices that equal intrinsic value to float precision (deep ITM, low vol, short maturity): an explicit status, never a fabricated IV. The 184 imprecise `OK` cells are the reason the pipeline inverts out-of-the-money quotes only; on that OTM domain recovery is below 1e-5 wherever the price exceeds 1e-8·F (tested).

**Mutation check.** Cutting the solver to 20 bisection halvings makes 2 tests fail (reprice residual 1.3e-6·F; recovery error 2.4e-6), so the tests can fail.

**Bounds and invalid input (GR-QNT-01).** Prices at or beyond lower/upper bounds for ITM and OTM calls and puts return `BELOW_LOWER_BOUND` / `ABOVE_UPPER_BOUND` with `iv = NaN`; F ≤ 0, K ≤ 0, T ≤ 0, ∞, NaN give `INVALID_INPUT`; a mixed array shows no cross-contamination.

**Ordering caveat (recorded, not hidden).** Phase 2 A1 requires tolerances "set in this phase *before* running on real data". Experiment E-1 had already run on real SPY data (2026-10-13) before these tolerances were written, so that ordering requirement **cannot be claimed**.

## 3. Comparison design (fixed before results were viewed)

| Item | Setting |
|---|---|
| Data | `make_chain(120 days, seed 3, noise_free=False)`: weekly SPY-like expiries, mid prices rounded to cents (the only noise model), generating surface `true_sigma` known. Dense chain = strike step 1/5; sparse = 5/25. Every 4th date, interior quotes only, stride 3 (k) / 4 (T) |
| k methods | `linear_iv` (production), `linear_total_variance`, `pchip_iv` (shape-preserving), `cubic_spline_iv` (not-a-knot) |
| k criterion | leave-one-out: hide one interior quote, predict from the rest of its expiry slice, error vs the hidden quote (vol points). Interior only, so nothing extrapolates |
| T methods | `linear_total_variance` (production), `linear_iv`, `nearest_expiry` |
| T criterion | leave-one-expiry-out: hide expiry j, predict its quotes from j±1 (≈ 7-day gap) or j±4 (≈ 28-day gap); neighbours' IV at the quote's k by the same linear rule for every T-method |
| Reporting | MAE, RMSE, p95 in vol points **per moneyness region with n and n_missing**; below n = 100 flagged `insufficient_n` (none were) |
| Filter policies | `default` (min mid 0.05, rel. spread ≤ 0.35), `strict` (0.25, 0.10), `loose` (0.01, 0.80), run through `build_otm_quotes` and the production surface builder; scored against the generating surface |

## 4. Results

### 4.1 Interpolation in k (MAE in vol points; n = held-out quotes)

| Region | n dense | linear_iv (prod.) | linear_tv | pchip | cubic spline | n sparse | linear_iv | linear_tv | pchip | cubic |
|---|---|---|---|---|---|---|---|---|---|---|
| k < −0.10 | 8,671 | 0.030 | 0.047 | 0.024 | 0.028 | 1,323 | 0.068 | 0.150 | 0.034 | 0.044 |
| −0.10 ≤ k < −0.02 | 4,391 | 0.020 | 0.032 | 0.013 | 0.015 | 804 | 0.047 | 0.099 | 0.016 | 0.016 |
| \|k\| < 0.02 | 2,404 | 0.014 | 0.021 | 0.009 | 0.009 | 377 | 0.038 | 0.074 | 0.009 | 0.009 |
| 0.02 ≤ k < 0.10 | 4,313 | 0.019 | 0.023 | 0.015 | 0.016 | 586 | 0.037 | 0.061 | 0.016 | 0.016 |
| k ≥ 0.10 | 2,376 | 0.036 | 0.040 | 0.031 | 0.035 | 207 | 0.039 | 0.046 | 0.031 | 0.034 |
| **All** | 22,155 | **0.025** | 0.036 | **0.019** | 0.022 | 3,297 | **0.052** | 0.106 | **0.023** | 0.028 |

### 4.2 Interpolation in T (MAE in vol points)

| Neighbour spacing | n dense / sparse | linear total variance (prod.) | linear_iv | nearest expiry |
|---|---|---|---|---|
| ± 1 expiry (≈ 7 d) | 15,633 / 2,220 | 0.015 / 0.017 | 0.015 / 0.017 | 0.044 / 0.046 |
| ± 4 expiries (≈ 28 d) | 11,919 / 1,072 | 0.057 / 0.076 | **0.013 / 0.018** | 0.155 / 0.157 |

### 4.3 Quote-filter policies vs the generating surface

| Metric | default | strict | loose |
|---|---|---|---|
| Quotes kept, dense (of 397,280 rows) | 270,904 (68.2 %) | 243,167 (61.2 %) | 283,792 (71.4 %) |
| Quote IV error MAE / p95 / max (vol pts) | 0.017 / 0.063 / 0.601 | 0.010 / 0.033 / 0.160 | 0.025 / 0.105 / 1.396 |
| Grid cells observed / missing, dense | 39.2 % / 13.0 % | 36.3 % / 20.2 % | 40.4 % / 10.3 % |
| Grid cell error MAE / max (vol pts), dense | 0.012 / 0.408 | 0.009 / 0.081 | 0.016 / 0.744 |
| Quotes kept, sparse (of 81,030) | 51.8 % | 46.1 % | 54.5 % |
| Grid cells observed / missing, sparse | 28.1 % / 32.7 % | 24.9 % / 41.0 % | 29.2 % / 29.1 % |
| Grid cell error MAE, sparse | 0.014 | 0.011 | 0.017 |

## 5. What this evidence does and does not support

**Supported (descriptive, synthetic):**
1. The harness is correct: on constructed truths each method is exact where theory says it must be and has the predicted chord error otherwise (curvature test: linear error = curv·h² to 9 decimals; cubic exact on a quadratic; total-variance interpolation exact for linear-in-T total variance).
2. Stricter quote filters lower the IV error of kept quotes and cells by about 40 % (MAE 0.017 → 0.010) and cut the worst case by 3–4× (0.601 → 0.160), at the price of 7 points fewer kept quotes and **7 points more missing grid cells** (13.0 % → 20.2 %, dense; 32.7 % → 41.0 %, sparse). Loosening does the opposite. That trade-off is real; **where to sit on it cannot be set from synthetic spreads**: the generator's bid/ask structure (±1 %, floor 0.005) is not a market microstructure.
3. In k on this generator, PCHIP and not-a-knot spline beat linear interpolation, with the gap widening on a sparse chain (all-region MAE 0.052 vs 0.023).

**Not supported / must not be concluded:**
1. **Any method ranking for real markets.** The generating surface is a smooth quadratic in k and *linear in IV* in T. Smooth truth favours higher-order k interpolation; linear-in-IV term structure favours linear-IV interpolation in T. The known-answer tests prove the T ranking *flips* when the truth is linear in total variance instead. In the T table the production rule (total variance) looks worse at ±28 days purely because the generator is not linear in total variance. Real chains have kinks, wing sparsity and noisy quotes that this generator does not produce.
2. That the differences matter. Every difference above is ≤ 0.15 vol points; the real E-1 data had a median vendor-vs-own IV difference of 0.31 vol points and median relative spread 2.3 % ([E1_RESULTS](E1_RESULTS.md) §2), so quote noise exceeds these method differences.
3. That PCHIP is arbitrage-safe or better for forecasting. Neither no-arbitrage behaviour nor downstream forecast metrics (RQ-09) were evaluated.

## 6. Trade-offs and limitations (for DEC-006)

| Method | Strength | Weakness / risk |
|---|---|---|
| Linear IV in k (production) | Transparent, never overshoots, trivially exact at observed nodes, mask semantics are simple | Chord bias ∝ curvature × gap², visible on sparse wings; kinks at each quote |
| Linear total variance in k | Natural for variance-based arbitrage conditions | Worst k-error here; no benefit demonstrated |
| PCHIP in IV | Shape-preserving (no new extrema between quotes), smooth first derivative, lowest error here | Needs ≥ 2 points; not C²; behaviour at noisy adjacent quotes untested on real data |
| Not-a-knot cubic spline | Smoothest, exact on quadratics | Can overshoot on noisy or sparse wings (worse than PCHIP in the put wing here); needs ≥ 4 points |
| Linear total variance in T (production) | Monotone total variance gives calendar-consistent interpolation by construction | Looks worse than linear IV on this generator; evidence says nothing for real term structures |
| Nearest expiry | Never interpolates | 3–10× the error here; invents a step function |

**Boundary behaviour (tested):** PCHIP and spline return NaN outside the quote hull; `numpy.interp` silently clamps, which is why production keeps its explicit inside-hull mask and why any adopted method must keep it. No candidate extrapolates in the harness.

**Invalid-input behaviour:** the spline returns NaN with fewer than 4 points; slices below `min_pts` (8) are skipped, not guessed; NaN predictions are counted in `n_missing`, never dropped.

## 7. Reproduce

From the repository root (outputs must be a new file):

```bash
python scripts/phase2_surface_comparison.py --out scratch/phase2_comparison.json
cd backend && PYTHONPATH=src python -m unittest tests.scientific.test_iv_recovery tests.scientific.test_interpolation_comparison tests.scientific.test_leakage_sentinels
```

Two runs of the script produced JSON files with identical SHA-256 (`ac8c57bd…c927db5`) and identical printed tables.

## 8. DEC-006: what is needed from the owner (not decided)

Synthetic evidence cannot settle DEC-006, and Phase 2 cannot pass without it (A5). Decision options:

| Option | Meaning | Consequence |
|---|---|---|
| **A (recommended)** | Keep the production rules (linear IV in k, linear total variance in T, no extrapolation) as the **documented comparison baseline**, not an adopted method; run this harness unchanged on the first permitted real sample; adopt an alternative only under the rule below | No code change; DEC-006 stays open until real data exists, which Phase 0 already blocks |
| B | Provisionally adopt PCHIP in k | Based on synthetic evidence the document itself says is generator-dependent; would need an ADR and a risk note |
| C | Choose a different candidate set to compare (e.g. smoothing spline, parametric SVI-type fit) | Adds scope; SVI-type fits are Phase 7 per the plan |

**Proposed pre-registered rule for the real-sample comparison (owner to approve before any real data is viewed):** an alternative replaces the baseline only if, on the permitted sample, (i) its leave-one-out RMSE is lower in at least 4 of the 5 moneyness regions each with n ≥ 100, (ii) its worst-case absolute error is not larger, (iii) it creates no new calendar or butterfly flags (`surfaces/diagnostics.py`), and (iv) downstream persistence/ridge metrics are not worse on the same folds. Otherwise the baseline stays. Quote-filter thresholds are chosen the same way from the observed spread distribution, using the coverage-vs-error trade-off in §4.3.
