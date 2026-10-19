# Phase 4 evidence review and experiment plan (2026-10-16)

> **Conclusion preserved: no neural model has been shown to beat persistence.** E-1 and E-2 ([E1_RESULTS](E1_RESULTS.md), [E2_FIXED_EXPIRY_RESULTS](E2_FIXED_EXPIRY_RESULTS.md)) are descriptive backtests on hosted SPY data of unverified upstream licence; the statistical-inference search is CLOSED — NO-GO ([PHASE0_CLOSURE_RECORD](PHASE0_CLOSURE_RECORD.md)). This review re-read the code behind those results and added tests; **no model was trained and no number below is new evidence about forecasting skill.** Phase 4 gate: **not met** (Phase 3 gate unmet, DEC-012 undecided, no CUDA approval for local runs).

## 1. Audit of the evidence pipeline (code read 2026-10-16)

| Question | Finding | Evidence |
|---|---|---|
| **Leakage in features** | None found. Features at origin *t* use rows ≤ *t*; fill values come from training rows only; rolling realised vol is backward-looking | `features/panel.py`, `evaluation/leakage.py`; unit tests `test_features_at_an_origin_ignore_everything_after_it`, `test_library_invariance_audit_passes_and_would_catch_a_leak`; audit also passed on the real panel (1,730 origins, E1_RESULTS §2) |
| **Leakage in fitting** | Previously only the chosen ridge penalty was tested against a scrambled future. **New:** the fitted baselines (standardiser, PCA, ridge weights) are unchanged when everything after the validation period is scrambled, with a negative control that does fail when test-year origins enter training | `tests/scientific/test_leakage_sentinels.py` (3 tests, OK). Applies to ridge/PCA-ridge/rolling mean; **the neural training path was not run here** (CUDA only) |
| **Data splits** | Expanding window; validation = preceding year; training labels purged against validation start, validation labels against test start; `assert_no_overlap` asserted in every fold; 8 test years 2016–2023 | `evaluation/walkforward.py`; `test_folds_are_chronological_and_purged`, new `test_every_fold_keeps_the_test_year_out_of_training_and_validation` |
| **Feature availability at prediction time** | Features include the origin-day closing surface and its availability mask. Anything unavailable at the origin is filled causally (≤ 5 days forward fill, then training-period cell means). The primary metric requires a real value at the origin | `causal_fill`, `eval_mask`; unit tests. Days-to-expiry of the anchoring expiry and weekday are **not** features (E2 §8) |
| **Forecast horizon** | One panel row (≈ 1 trading day); calendar gaps > h+4 days are excluded so a gap cannot pass as a 1-day horizon | `prepare`, `test_gap_in_the_calendar_cannot_create_a_fake_horizon` |
| **Target definition** | Label = 1-day change of a grid cell. E-1: the surface at the target day (nearest-expiry anchor, about constant maturity). E-2: the same expiry as at the origin (roll-down included). Persistence = zero change. Both reproduced exactly on re-run | `features/panel.py`; E2 §2, §9 |
| **Baseline correctness** | Persistence is the causally filled origin surface, scored on exactly the same cells as every model; zero skill by construction; hand-computed MAE/RMSE tests pass; ridge penalty and PCA selected on the validation year | `models/baselines.py`; `test_every_model_is_scored_on_exactly_the_same_cells`, `test_mae_rmse_equal_a_hand_computation` |
| **Model complexity vs data** | 1,198–2,953 training origins per fold; MLP/GRU with tens of thousands of weights. Early stopping chose epoch 0–3 in many folds, i.e. a near-untrained network (E1 §4, §7; E2 §9) | run logs as recorded |
| **Hyper-parameter methodology** | Fixed a priori, **no search**; 3 seeds; ridge penalty at the top of its grid (1000) in 8 of 8 folds, so the strongest baseline may itself be under-regularised | E1 §4 item 4 |
| **Out-of-sample evaluation** | Descriptive only, 8 yearly test blocks; pooled RMSE is dominated by 2020 and by heavy tails (residual excess kurtosis 56–66) | E1 §3 |
| **Reproducibility** | E-1 numbers reproduced exactly in two later Kaggle sessions (E1 §7, E2 §9); config and dataset hashes in the manifest. Not reproducible locally (data and GPU are off-machine) | as recorded |

### Gaps against the guardrails (recorded, not fixed here)

| Guardrail | Gap | Why not fixed now |
|---|---|---|
| GR-MOD-01 (runner refuses neural runs without baselines) | `run_neural` does not check that persistence and regression results exist; ordering relies on the notebook | Changing the runner signature affects the generated notebooks; neural runs need owner/GPU anyway. Propose with the next neural experiment |
| GR-LEAK-05 / GR-MOD-05 (test-window access log, `test_accessed_count`) | No access log exists in code (grep: 0 hits) | Needs a run-record schema change |
| GR-MOD-04 (improvement claims only with variability) | Descriptive tables report seed spread and years-better counts, but there is no pre-registered decision rule | Proposed in §3 below |
| GR-MOD-06 (uncertainty labelled) | No uncertainty output exists, so nothing to label | n/a |
| Heavy-tailed errors | Headline RMSE/MSE-skill is outlier-dominated; MAE, median daily difference and years-better are reported but not used as co-primary | §3 makes them co-primary |

## 2. What the existing results do and do not say

*Unchanged from E1/E2:* under the nearest-expiry label neither MLP (MSE skill −0.207) nor GRU (−0.077) beat persistence pooled; only low-capacity PCA-ridge was ahead (+0.051, better in 3 of 8 years by daily MAE). Under the same-expiry label the ranking changes (GRU +0.014 on the common sample, PCA-ridge −0.003). Rankings that flip with the label are not evidence of skill. Seed spread (GRU RMSE 2.666–2.722) is smaller than the gap to persistence, so the neural shortfall is not a single-seed accident, but this is **not** a significance statement.

## 3. Proposed experiment plan (needs owner approval; nothing has been run)

**Principle:** one hypothesis per run, each with its decision rule fixed before the run. No architecture changes, no repeated training "to see".

**Common decision rule (descriptive; proposed for GR-MOD-04):** a model is reported as *improving on persistence* only if **all** hold on the pre-registered test years under the stated label: (a) pooled MSE skill > 0 **and** pooled MAE below persistence; (b) better than persistence by daily MAE in at least 6 of 8 test years; (c) every seed's pooled MSE skill > 0 (no sign flip across seeds); (d) skill > 0 in at least 2 of the 3 realised-volatility regimes with n ≥ 100 cells each; (e) the result holds under both the nearest-expiry and the fixed-expiry labels, or the report says it holds under one label only and does not call it a general improvement. Otherwise the report says "no improvement shown". This is a descriptive standard, not a hypothesis test; no p-value or interval is produced (L-22).

| ID | Hypothesis (from E1/E2 untested list) | Change vs E-1/E-2 (one thing only) | Success / null |
|---|---|---|---|
| H1 | The baseline comparison is unfair because the ridge penalty hit the grid edge (1000) in 8/8 folds | Extend `ridge_alphas` upward (e.g. 10³–10⁶) for ridge and PCA-ridge only; **no neural training** | CPU suffices (no neural training), **but the real E-1 surface panel is on the owner's Kaggle account, not on this machine**: run it as a Kaggle notebook session (owner-run), or after the owner copies the panel here (hosted-data licence unverified, see HOSTED_DATASET_ASSESSMENT). Outcome: new persistence-vs-ridge numbers; if PCA-ridge's margin changes materially, every later neural comparison uses the new baseline |
| H2 | Early stopping on the preceding year selects an untrained network because of regime shift (2020 → 2021 fold) | Validation set = last 20 % of training origins (chronological, purged) instead of the previous calendar year; same models, seeds, features | Needs GPU (owner's Kaggle/Colab). Success per the common rule; null if the best epoch stays at 0–3 and skill stays negative |
| H3 | The GRU lacks the deterministic roll-down/weekly-cycle signal under the fixed-expiry label | Add anchoring-expiry days-to-expiry and weekday as features (E2 §8 item 2); all models | Needs GPU for neural models; baselines can run on CPU. Success per the common rule under the fixed-expiry label |

Run order H1 → H2 → H3, each only after the previous result is recorded. A neural result worse than persistence is reported as such and **retains the NO-GO**. The final test years are evaluated once per frozen configuration (GR-LEAK-05); because no access log exists, each run record must state the configuration hash and that no selection used the test years.

**Compute constraints (CLAUDE.md §13, DEC-015):** neural runs only on a verified, explicitly selected GPU (Colab/Kaggle T4, or local RTX 4060 8 GB after the owner approves a CUDA PyTorch install). Local PyTorch is currently `2.13.0+cpu`, `cuda.is_available() == False` (checked 2026-10-16, read-only). I did not install anything.

### 3.1 Approval and H1 pre-registration (2026-10-16)

The owner approved H1 and the common decision rule in chat on 2026-10-16 and asked that the notebook be prepared for execution on Kaggle, **without verification on synthetic data**. Status: **H1 notebook prepared, not executed.** What was done instead of a synthetic run: schema validation, syntax parse of every cell, an undefined-name scan (clean; the same scan is clean on the E-2 notebook that has run), hand-computed unit tests of the new decision-rule function (`tests/unit/test_decision_rule.py`, 7 tests), and a re-run of the existing unit tests that touch the changed code (59 tests, OK). Neither the notebook's data path nor its plots have ever executed; the first run on Kaggle is therefore also its first test, and a failure there is a notebook bug, not a finding.

Fixed before the run (also printed at the top of the notebook):
- **Grid:** old `(0.1, 1, 10, 100, 1000)` → new `(0.1, 1, 10, 100, 1000, 3000, 1e4, 3e4, 1e5, 3e5, 1e6)`; `ridge` and `pca_ridge` only; everything else identical to E-1/E-2 (config hash must equal `eaa46df0…`).
- **Reproduction gate:** with the old grid the published E-1 RMSEs (persistence 2.5686, ridge 2.5883, pca_ridge 2.5020, rolling_mean 5.0162, tolerance 6e-4) and E-2 RMSEs (3.002, 3.127, 3.004, 5.428, tolerance 1.1e-3) must be reproduced; a mismatch is flagged and the run is read as unverified.
- **Binding check:** if the chosen penalty is still at 1e6 the grid is reported as still binding and is *not* extended in this experiment.
- **Material change** (a convention, not a derived threshold): |Δ pooled MSE skill| ≥ 0.01 under either label for `ridge` or `pca_ridge`, or a change of decision-rule verdict. Material → later neural comparisons use the new baselines; otherwise the E-1/E-2 baselines stand.
- **Decision rule:** implemented in `evaluation/decision_rule.py` exactly as in this section (criteria a, b ≥ 6 of 8 years, c not applicable to deterministic baselines, d ≥ 2 of 3 regimes with n ≥ 100, e both labels). A criterion that cannot be evaluated is reported as such, never passed.
- **Curves saved for reference:** validation error vs penalty for every fold × model × label, chosen penalty per fold, skill by year (old vs new), pooled bars, regime skill, rule scoreboard, plus the shared set (per-cell MAE/bias/RMSE/skill heatmaps, level/count heatmaps, daily error and cumulative-difference curves, RMSE by tenor/moneyness/year/regime, actual-vs-forecast surfaces), for both labels; numbers in `tables/*.csv` and `tables/*plot_data.npz`.
- **Code change that supports it:** `models/baselines.py` now also returns the validation-error-per-penalty dictionaries in `chosen` (`ridge_val_mse`, `pca_ridge_val_mse`), and `run_baselines` logs only the chosen penalties. Numerical behaviour of E-1/E-2 is unchanged (existing tests pass); the E-1/E-2 notebooks were regenerated from the current source.

### 3.2 H1 result (executed 2026-10-19 on the owner's Kaggle account; descriptive only)

**Run:** private notebook `notebook00c6dc025c`, version 1, CPU (*Accelerator: None*), dataset `dudesurfin/spy-options-eod-volatility-surface-2010-2023` attached as an input (nothing downloaded locally), "Successfully ran in 183.8 s", run id `kaggle_eaa46df0_76bf2f94` (config hash `eaa46df0…` = E-1/E-2), 58 output files re-hashed OK, output 19.75 MB, 23 figures, 0 plotting errors, no neural model trained. It was the notebook's first execution and it ran without a code error. Observed in the log: the benign `UserWarning` about a redundant linestyle in one plot call (cosmetic, not fixed so the repository copy stays identical to what ran). The 23 figures were not inspected by eye here (the Kaggle viewer was too heavy to render in the automated browser); they and the CSV/NPZ data behind them are in the version's output.

**Final line of the run:** `RESULT SUMMARY -> reproduction OK: True | grid still binding: True | material change: True | verdicts: {ridge_old, ridge_new, pca_ridge_old, pca_ridge_new: all no_improvement_shown}`.

1. **Reproduction gate: OK.** With the old grid, E-1 RMSE reproduced to ≤ 4.3e-5 (persistence 2.5686, ridge 2.5883, pca_ridge 2.5020, rolling_mean 5.0162) and E-2 to ≤ 5.0e-4 (3.0021 / 3.1273 / 3.0035 / 5.4283 vs 3.002 / 3.127 / 3.004 / 5.428).
2. **Pooled out-of-sample, observed cells, vol points (MSE skill vs persistence):**

| Label | persistence | ridge old | ridge **new** | PCA-ridge old | PCA-ridge **new** |
|---|---|---|---|---|---|
| nearest-expiry (n = 36,793) | RMSE 2.5686 / MAE 1.3510 | 2.5883 / 1.4111 (−0.0154) | 2.5307 / 1.3383 (**+0.0293**) | 2.5020 / 1.3299 (+0.0512) | 2.5052 / 1.3263 (+0.0488) |
| fixed-expiry (n = 35,838) | 3.0021 / 1.4939 | 3.1273 / 1.5806 (−0.0852) | 2.9820 / 1.5455 (**+0.0133**) | 3.0035 / 1.5127 (−0.0010) | 2.9919 / 1.5036 (+0.0068) |

3. **Material-change test (pre-registered): `ridge` is material, `pca_ridge` is not.** Skill change of `ridge`: +0.0447 (nearest) and +0.0985 (fixed), well above 0.01; of `pca_ridge`: −0.0025 and +0.0077, below 0.01. No decision-rule verdict changed. By the pre-registered "either family" wording, **H1 counts as material**, so later neural comparisons use the `*_new` baselines. In substance: the *old plain ridge* was badly under-regularised; the *strongest baseline, PCA-ridge, was not*: its nearest-expiry skill even fell slightly (+0.0512 → +0.0488), i.e. selecting the penalty on the validation year did not transfer perfectly to the test years.
4. **The new grid is still binding under the fixed-expiry label** (chosen penalty at 1e6: PCA-ridge in 3 of 8 folds, ridge in 2 of 8; none under the nearest-expiry label). Per pre-registration the grid was **not** extended; the fixed-expiry baselines may still be under-regularised. Chosen penalties vary across folds from 0.1 to 1e6 (for example PCA-ridge, fixed-expiry: 0.1, 0.1, 1e6, 1e4, 1e6, 1e6, 3e3, 1e4), a sign that one validation year selects noisily.
5. **Decision rule: no model improves on persistence under the pre-registered standard.** All four variants return `no_improvement_shown`. The closest, PCA-ridge new under the nearest-expiry label, passes (a) pooled skill + MAE and (d) regimes (all three positive) but fails (b): better by daily MAE in 5 of 8 test years, 6 are required. Under the fixed-expiry label no variant passes (a) except ridge-new on skill (MAE is higher than persistence), and years-better are 1–3 of 8.
6. **Neural implication (unchanged):** H1 says nothing about MLP/GRU. It removes one objection to the baseline (grid edge) for the nearest-expiry label and leaves it open for the fixed-expiry label. The NO-GO conclusion for neural models stands.

Where it lives: Kaggle notebook `notebook00c6dc025c` v1 output (`report.md`, `tables/`, `plots/`, `forecasts/`); not in Git, not on this computer. Next in the plan: H2 and H3 (GPU) need a separate go-ahead; an optional H1b (extend the grid beyond 1e6 for the fixed-expiry label only, same rules) would close the "still binding" gap and needs your approval because it was pre-registered as out of scope for H1.

### 3.3 H1b: fixed-expiry grid extended to 1e9 (approved 2026-10-19; executed 2026-10-19; descriptive only)

**Design (pre-registered in the notebook's overview cell before the run; this section was written after it).** Baselines only, no neural training. For the *fixed-expiry label only* the ridge/PCA-ridge penalty grid was extended from the H1 grid (≤ 1e6) to ≤ 1e9, the point where ridge is effectively intercept-only, so the search ends there. The nearest-expiry label kept the H1 grid so the both-label decision rule stays evaluable. Gates: reproduction of the published numbers (old grid), reconciliation with the recorded H1 numbers (`*_h1` models), saturation count, and a material-change test **against the H1 baseline** (|Δ pooled MSE skill| ≥ 0.01 under the fixed-expiry label, or a verdict change). Notebook: `notebooks/Neural_Volatility_Surface_H1b_FixedExpiryGrid.ipynb` (`scripts/_notebook_cells/cells_h1b.py`).

**Run.** The owner's Kaggle notebook `neural-volatility-surface-h1b-fixedexpirygrid`. Version 1 was committed with the notebook's default GPU T4 x2 accelerator and sat in "Queued…" for 15+ minutes with no log, so it was abandoned (Kaggle offers no stop control; it may still start and use GPU quota, cancel it from the Kaggle UI if it does). **Version 2** was committed with *Accelerator: None* (CPU), dataset `dudesurfin/spy-options-eod-volatility-surface-2010-2023` attached; run id `kaggle_eaa46df0_76bf2f94`; started at once. The numbers below are from its Logs page. Final status: **"Successfully ran in 215.4s", 63 files written and re-hashed OK, 0 plot errors (H1b and shared sets, both labels)**; final line: `RESULT SUMMARY -> reproduction OK: True | H1 reconciliation OK: True | fixed-expiry saturated at 1e9: True | material vs H1: False | verdicts: all six variants no_improvement_shown`. The plot-stage UserWarning (redundant linestyle) is cosmetic. Figures not inspected by eye; outputs stay on Kaggle (not in Git, not downloaded).

**Result.**
1. *Reproduction* OK (same tolerances and numbers as H1). *H1 reconciliation* OK (`*_h1` RMSE reproduces the recorded H1 values to ≤ 3.3e-5).
2. **Material vs H1: no.** Pooled MSE skill vs persistence, fixed-expiry label: ridge H1 +0.0133 → H1b +0.0133 (change −0.0001; RMSE 2.9820 → 2.9821); PCA-ridge +0.0068 → +0.0068 (change −0.000003; RMSE 2.9919 → 2.9919). Nearest-expiry unchanged by construction. No verdict changed, so **the H1 baselines stand**.
3. **Saturation.** Under the fixed-expiry label the folds that chose 1e6 in H1 now choose the new top **1e9** (PCA-ridge 3 of 8 folds, ridge 2 of 8; the other folds' choices are unchanged, 0.1 to 3e5). A choice at 1e9 means the validation year preferred an effectively intercept-only model, i.e. in those folds nothing the ridge/PCA features add beat "persistence plus a constant change". So the earlier "grid still binding" concern is resolved *as saturation*, not as hidden skill: the penalty grid is not what limits these baselines. By pre-registration the grid is not extended further.
4. **Decision rule:** all six ridge/PCA-ridge variants (old, H1, H1b) return `no_improvement_shown`. Best case unchanged: PCA-ridge (H1 = H1b), nearest-expiry label, passes (a) and (d) but is better in 5 of 8 test years (6 required); under the fixed-expiry label PCA-ridge is better in 3 of 8 years and ridge in 1 of 8.
5. **Consequence for Phase 4.** The baseline question raised by E-1/E-2 (penalty at the grid edge) is now closed: use the H1 baselines (`ridge_new`/`pca_ridge_new` of H1) for any later neural comparison; widening the grid further would change nothing. Still no model shown to beat persistence, and nothing here concerns a neural model.

Open: H2/H3 (GPU) remain unapproved/not run.

## 4. Owner decisions requested

1. ~~Approve H1~~ **Approved 2026-10-16; notebook prepared** (§3.1). Next: run it on Kaggle and report the result summary.
2. ~~Approve the common decision rule~~ **Approved 2026-10-16** as the descriptive standard for any "improves on persistence" wording.
3. For H2/H3: approve another owner-run Kaggle/Colab GPU session, or approve a local CUDA install (the assistant will not install it).
4. DEC-012 (initial neural architecture) remains `PROPOSED`; nothing here decides it.
