# Phase 0 Audit — Reproduction, Scientific Review, and Readiness

> **SYNTHETIC — not market data.** This audit concerns the synthetic feasibility spike only. Nothing here is evidence about real markets. **Phase 0 is NOT complete.**

**Status:** IN_PROGRESS (audit started 2026-10-12 after the spike's first execution; results sections are filled only after the pre-declared analyses run) · **Audited artefacts:** `scripts/phase0_synthetic/`, [PHASE0_SYNTHETIC_RESULTS](PHASE0_SYNTHETIC_RESULTS.md) (**v1**, preserved unchanged), [PHASE0_FEASIBILITY_PLAN §9](PHASE0_FEASIBILITY_PLAN.md) · **Rules:** the v1 pre-registered outcomes stay in the record; every new analysis below is labelled **POST HOC** or **EXPLORATORY**; no threshold or generator parameter is changed to improve an outcome; failed v1 checks stay failed.

## 1. Reproduction of the reported results (executed 2026-10-12, before any code change)

| Item | Result |
|---|---|
| Environment | CPython 3.12.6 · Windows-11-10.0.26300-SP0 · AMD64 · standard library only |
| Documented test command | `python -m unittest discover -s tests -t .` (from `scripts/phase0_synthetic/`) → **Ran 57 tests, OK, 0 failures, 0 errors**; 6.2 s (earlier runs 3.8–4.0 s: machine variance) |
| Regeneration commands | the 7 documented commands (`single` RW/AR, `--noise` RW/AR, `--fast --days 150` RW/AR, `study --first-seed 20261100 --n-seeds 10`) → wall time 1.2 / 1.4 / 1.3 / 1.4 / 0.5 / 0.6 s and **69.2 s** (study); total 82.2 s |
| Source hashes vs recorded | all 7 v1 records (19 study runs included): recorded `code_sha256` **equals** the hashes of the files on disk |
| Cross-process reproducibility | the 7 regenerated records are **field-for-field identical** to the archived v1 records (`data_sha256`, `metrics_sha256`, `code_sha256`, `results`, both comparisons, `hypotheses`, `pipeline_diagnostics`, `config`, `min_true_iv`); the study `summary` is identical (invalid world 20261102 included). Only timing differs |
| Results document vs records | 63 quoted numbers checked programmatically (counts, MAE/RMSE, MSE ratios, per-seed study ratios, hash prefixes, scorecard counts 17/19, 18/19, 8/9, fast-config unalignable/above-bound counts) → **0 mismatches**. Not machine-checked: noise-mode medians and confidence-interval digits (spot-read only) |
| v1 records preserved | copied unchanged to `experiments/phase0_synthetic/archive_v1/` (git-ignored) before regeneration |

**Conclusion:** the *reported* results were reproduced exactly. That establishes *reproducibility of the computation*, not scientific validity — §2–§4 assess that.

## 2. Scientific review — findings

Three things must not be conflated:
1. **Numerical correctness** — do the functions compute what they claim (pricing, bounds, solver, metrics, bootstrap)?
2. **Synthetic scenario recovery** — can the pipeline recover known truths and detect a known predictable component in worlds we built?
3. **Predictive value on market data** — does any model forecast real surfaces better than persistence? **Nothing in the spike addresses (3).** (2) is a necessary precondition for (3), not evidence for it.

| # | Finding | Where | Impact | Classification | Handling |
|---|---|---|---|---|---|
| F1 | A cell is marked `observed` when an observation lies within `tol_k` of the node, but the cell value is that observation's IV **at its own k**, not at the node. Status says "observed at the node"; value is off by slope × Δk (≤ 4.3×10⁻⁷ seen). Explains v1 H-S1/H-S4 failures. Relaxing the recovery tolerance would hide the inconsistency instead of fixing it | `surface.py:60-62` | Value/status mismatch; bias bounded by `|dIV/dk| × tol_k` | **Genuine logic defect** (design, not arithmetic) | Fix by changing semantics (§3), not tolerances |
| F2 | Pre-registered recovery tolerance (1e-8) was inconsistent with the matching tolerance (1e-6) | protocol §9.4 | v1 H-S1 false alarms | Protocol error (mine) | Recorded; consistency rule added (§3) |
| F3 | H-S6 ±15 % tolerance came from a rough standard-error guess; **no prior analytical derivation existed** | protocol §9.4 | 1 of 19 study runs failed; tolerance too tight for AR | Protocol error (mine) | Analytic SD derived post hoc (§4, A3); original criterion and outcome retained |
| F4 | Bootstrap CI and pooled `mse_ratio` use different weightings: CI is on **equally weighted per-origin MSE**, the ratio is **pooled over cells** | `evaluate.py:compare` | Small, but "detected" and "ratio" are not exactly the same estimand | Reporting inconsistency | Added `mse_ratio_origin_mean` (equal-weight) next to the pooled ratio; documented |
| F5 | The percentile bootstrap's block length (5) was not justified, and its coverage was never tested on dependent data | `evaluate.py:block_bootstrap_ci` | CI validity unverified (only 9–10 seeds) | Unverified assumption | Coverage simulation (§4, A2); autocorrelation of per-origin loss differences recorded |
| F6 | `HistoryView` blocks reads past the origin but is a **cooperative** guard (Python cannot forbid access to `history._s`) | `forecast.py` | A malicious/buggy forecaster could bypass it | Design limitation | Documented; invariance test shows the shipped forecasters do not use future days |
| F7 | Evaluation conditions on "cell observed at t+1". In the synthetic worlds observability is independent of values; **on real data availability can correlate with volatility** (wide/missing quotes in stress) | `evaluate.py:walk_forward` | Selection effect invisible in synthetic worlds | Scope limitation | Added to limitations / NEXT_STEPS (measure on real sample) |
| F8 | Invalid random-walk worlds are removed by a plausibility guard that depends on the **whole path** (IV ≤ 0.02 somewhere): conditioning on bounded excursions makes the retained RW paths slightly more mean-reverting, which if anything favours a fitted AR(1) — i.e., it can **inflate** RW false positives, not hide them | `synth.py` guard; study | The 0/9 result is not biased *toward* "persistence safe"; but the denominator is a selected subset | Selection effect | Invalid rate and a worst-case count (invalid treated as detections) reported in A3 |
| F9 | RW and AR worlds with the **same seed share the same innovation stream** (paired); bootstrap seed `seed+1` equals the dynamics seed of the adjacent world | `synth.py`, `run.py` | RW and AR study results are paired, not independent; no leakage within a run | Design note | Seeds in A3 span disjoint ranges; each world's rate is estimated on its own |
| F10 | Quote noise (noise mode) is tick rounding only; the node tolerance of 5×10⁻⁴ in noise mode lets forward error (~1e-4 in k) move observations between cells | `run.py`, `surface.py` | Noise-mode numbers are exploratory and sensitive to that tolerance | Exploratory only | Already labelled H-S9 / exploratory; separation re-verified (§5) |
| F11 | Fitted AR(1) uses the true functional form of the surface (3 factors + known term shape) | `forecast.py` | Power measured is for a **well-specified** forecaster | Scope limitation | Stated in limitations |
| F12 | Unit-root bias: OLS φ̂ is biased low when the truth is φ=1, so the fitted forecaster is nominally worse than persistence in World RW (ratio ≈ 1.01–1.025) | `forecast.py` | Explains the "persistence significantly better" seeds; not a bug | Expected statistics | Documented |

**Looked at and found correct:** Brent implementation (NR zbrent; solver failure statuses; invariants), Black-76 and bounds (hand values, parity), validation conservation and precedence, parity forward, walk-forward ordering (forecast made before the target is read), AR(1) fit uses only days ≤ origin, percentile index arithmetic, analytic persistence-MSE formula (κ = 1 for RW; 2/(1+φ) for AR).

## 3. Changes made (POST HOC; each with regression tests)

| Change | Why | Effect on v1 outcomes | Backward compatibility |
|---|---|---|---|
| `SurfaceConfig.tol_k` default **1e-6 → 1e-9** (clean mode); a nearby observation beyond that is **not** `observed` and contributes through interpolation | F1: status/value consistency; makes bias ≤ `|slope| × 1e-9`, consistent with the 1e-8 recovery criterion (**consistency rule: recovery tolerance ≥ max|dIV/dk| × tol_k**) | v1 records untouched; v2 re-runs reported separately | `--tol-k 1e-6` reproduces v1 behaviour exactly (verified, §4 A4) |
| `Surface.max_snap_dk` + pipeline `max_snap_dk` / `n_snapped_cells` diagnostics | Make the matching bias bound visible in every record | none (additive) | additive keys only |
| New post-hoc hypotheses `H-S1b_POST_HOC` (cell error ≤ slope bound × max snap + 1e-11) and `H-S6z_POST_HOC` (deviation within 3 analytic SDs) | Analytic, tolerance-consistent versions of the criteria that failed | Original H-S1 / H-S6 retained unchanged alongside | additive |
| `analytic_rel_sd()` in `evaluate.py` | F3: derive the sampling SD of the realized/expected persistence-MSE ratio | none | additive |
| `compare()` adds `mse_ratio_origin_mean` and `lag1_autocorr_d` | F4, F5 | none | additive |
| `phase0/audit.py` and `tests/test_audit_regressions.py` | Run the declared post-hoc analyses; regression tests for F1, F4, bootstrap, analytic SD | none | additive |

Not changed: the generator, the pre-registered tolerances in `run.TOL`, the forecasters, the bootstrap algorithm, the seeds of v1.

## 4. Pre-declared post-hoc analyses (declared BEFORE they were run)

| ID | Analysis | Design (fixed now) | Reporting rule |
|---|---|---|---|
| **A2** | Bootstrap CI coverage | Series of length 240 with **true mean 0**: AR(1) normal with ρ ∈ {0, 0.3, 0.6}, and a skewed case `z²−1` where `z` is unit-variance AR(1) (ρ = 0.3). Block 5, B = 1000, 1000 replications per case, seeds 7001…. Record: coverage of the 95 % interval; rate of `lo > 0` (nominal 2.5 %) | Report coverage ± binomial SE (≈ 0.7 pp); no pass/fail threshold; interpret departures > 2 SE as evidence of mis-calibration |
| **A3** | Extended study (**EXPLORATORY, POST HOC**) | Seeds **20262000 … 20262199**, both worlds, N = 300, clean quotes, **v2 code** (tol_k 1e-9). Record per world: invalid-world count; detection rate with Wilson 95 % interval; MSE-ratio distribution; mean lag-1 autocorrelation of per-origin loss differences; H-S6 relative deviations (empirical SD) vs the **analytic SD**; fraction within ±15 % and within 3 analytic SD; H-S1 and H-S1b pass rates | Report rates with intervals. For RW report (i) rate over valid worlds and (ii) worst case with invalid worlds counted as detections. Descriptive support rule for the H-S6 analytic argument: empirical SD within ±30 % of the mean analytic SD |
| **A4** | Backward-compatibility check | Re-run the 7 v1 commands with `--tol-k 1e-6` on the new code | Legacy fields (`results`, comparisons' original keys, `hypotheses` original keys, diagnostics original keys, `data_sha256`) must equal the archived v1 records exactly; any difference is reported |
| **A5** | v2 re-run of the v1 seeds | Pre-registered main runs and the 10-seed study re-run with v2 defaults | **Predicted in advance:** H-S1 passes for RW 20261104 and AR 20261106 (bias bound ≈ 1e-9); no other hypothesis outcome changes; differences confined to the few near-node cells. Any other change is reported as unexpected |

Sample-size note for A3: with 200 valid seeds the Wilson 95 % interval for an observed 2.5 % rate is about [1.1 %, 5.7 %], enough to distinguish a size near the nominal 2.5 % from one above ~8 %, and far tighter than the 9–10 seeds of v1 (where 0/9 is compatible with any true rate up to ≈ 28 %).

## 5. Results

*(the declarations above are not edited afterwards)*

**Code verification after the changes:** `python -m unittest discover -s tests -t .` → **74 tests (57 original + 17 new regression tests), OK, 27.9 s**.

**A4 (backward compatibility) — DONE:** with `--tol-k 1e-6` the new code reproduces **all legacy fields** (data hash, `results`, original comparison keys, original hypothesis keys, original diagnostics) of **all 7 archived v1 records, including the 19-run study**, exactly. v1 results remain reproducible.

**A5 (v2 defaults on the v1 seeds) — DONE; prediction held:** only the two predicted runs changed. RW 20261104: H-S1 False→True, H-S4 False→True; AR 20261106: H-S1 False→True; near-node cells were reclassified (cell-status totals changed, point metrics changed slightly), detection outcomes unchanged; study summary unchanged (0 false positives, 10/10 detections, invalid world 20261102). Unchanged failures: fast-config H-S2, AR 20261105 H-S6, invalid world. v2 records are in `experiments/phase0_synthetic/v2/` (git-ignored).

**A2 (bootstrap coverage, POST HOC) — DONE** (series length 240, true mean 0, block 5, B = 1000, 1000 replications; coverage SE ≈ 0.7 pp; 206 s):

| Case | Coverage of 0 (nominal 95 %) | Rate of `lo > 0` (nominal 2.5 %) |
|---|---|---|
| iid normal | 93.3 % | 3.4 % |
| AR(1) ρ = 0.3 | 90.8 % | 4.9 % |
| AR(1) ρ = 0.6 | 85.8 % | 7.1 % |
| skewed `z²−1`, ρ = 0.3 | 91.3 % | 2.2 % |

By the declared rule (> 2 SE departure = mis-calibration) the block-5 percentile interval **under-covers** in all four cases, worsening with positive serial dependence; the "detected" rule is therefore somewhat liberal against its nominal 2.5 % one-sided size. Whether the real per-origin loss differences are that dependent is addressed by A3 (below): their mean lag-1 autocorrelation is small/negative, which limits the practical impact on this spike but does not remove it. A longer block or a different interval method is a candidate dated amendment (not applied).

**A3 (extended study, EXPLORATORY, POST HOC) — DONE** (seeds 20262000–20262199, N = 300, v2 code, 545 s):

| | World RW | World AR |
|---|---|---|
| Valid / invalid worlds | 190 / **10** (5.0 %, Wilson 95 % [2.7 %, 9.0 %]) | 200 / 0 |
| Improvement detected (fitted AR1 vs persistence) | **3 / 190 = 1.6 %** (Wilson [0.5 %, 4.5 %]) | **200 / 200** (Wilson lower bound 98.1 %) |
| Worst case, invalid RW worlds counted as detections | 13 / 200 = 6.5 % (Wilson [3.8 %, 10.8 %]) | — |
| Persistence significantly better than fitted AR1 | 25 / 190 (13 %) | 0 |
| MSE ratio, mean (SD) [min, max] | 1.014 (0.016) [0.952, 1.067] | 0.760 (0.023) [0.702, 0.823]; analytic oracle 0.75 |
| Mean lag-1 autocorrelation of per-origin loss differences | +0.048 | −0.167 |
| H-S6 relative deviation: empirical SD vs analytic SD | 7.17 % vs 7.07 % | 7.78 % vs 7.65 % |
| Within ±15 % / within 2 / 3 analytic SD | 96.3 % / 94.7 % / 100 % | 96.0 % / 96.0 % / 100 % |
| H-S1 (v2) / H-S1b | 190 / 190 and 190 / 190 | 200 / 200 and 200 / 200 |
| Strict H-S2 (unalignable = 0) / H-S2a identity | **178 / 190** / 190 / 190 | **199 / 200** / 200 / 200 |
| H-S6 (±15 %) / H-S6z (3 analytic SD) | 183 / 190 / 190 / 190 | 192 / 200 / 200 / 200 |
| Runs with snapped near-node cells (v2) | 0 | 0 |

Reading (bounded by the evidence; all synthetic):
- **Sample size:** 190–200 seeds give usable intervals; the v1 9–10 seeds did not. The RW detection rate over valid worlds (1.6 %) is compatible with the nominal 2.5 %; the **worst case with invalid worlds counted as detections (6.5 %) is not**, so the invalid-world exclusion (5 % of RW worlds) cannot be dismissed as irrelevant — it is the main uncertainty on the RW false-positive rate.
- **AR detection** is 200/200 with MSE ratios centred on the analytic 0.75 (mean 0.760), confirming the pipeline detects a known predictable component when the forecaster is well-specified. This says nothing about real data.
- **H-S6:** the analytic derivation is supported — empirical SDs (7.2 %, 7.8 %) match the analytic SDs (7.1 %, 7.7 %) within a few percent and z has SD ≈ 1.02. The v1 "AR SD ≈ 10 %" came from 10 runs and was sampling noise. The original ±15 % criterion would still fail in ≈ 4 % of runs by construction; a z-based criterion is the justified replacement (a dated amendment, not applied to v1 outcomes).
- **Strict H-S2 fails in the full configuration too** (12 of 190 RW runs, 1 of 200 AR) because thin 30-day slices occasionally have < 3 put–call pairs. v1's "passes on the full configuration" held only for the two pre-registered seeds; the exact identity H-S2a holds in 100 % of runs.
- **Dependence:** loss differences are only weakly (RW) or negatively (AR) autocorrelated, so the A2 under-coverage at ρ ≥ 0.3 is less relevant here; the iid-case size distortion (3.4 % vs 2.5 %) still applies.
- **v2 node fix:** no run had a snapped cell and none failed H-S1 — consistent with the F1 diagnosis.

**Still not claimed:** anything about real data, a neural model, or the nominal size of the procedure under realistic (non-synthetic) dependence.

## 6. Readiness audit of the repository

*(pending)*
