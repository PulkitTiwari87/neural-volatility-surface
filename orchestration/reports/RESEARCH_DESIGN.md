# RESEARCH_DESIGN — Agent D (Quantitative Research and Evaluation), stages S3-S5 design

**Status: READY_FOR_REVIEW**
**Revision/manifest:** git HEAD `306c01b` ("finishing all the training of models H1-H6"); working tree has 45 uncommitted paths at the time of reading (the owner's ~44 plus `orchestration/`); nothing was committed, staged or reverted by this report. `orchestration/SHARED_STATUS.md` (2026-10-20, Wave 1 launch) read and not judged stale. Contracts `S3.md`/`S4.md`/`S5.md` read. At the time of writing `reports/` held only `UI_INTEGRATION_REPORT.md`; **Agent B's data report was not present, so nothing here depends on it** (market-data facts for India/US below are marked `NEEDS RESEARCH` where the repository does not establish them).

**Owned file:** this file only. No project code was executed (no python, pytest, notebooks). All "tests" mentioned were **read, not run**.

**Legend used in every section (research design is kept apart from experiments that ran):**
- **[RAN]** a hosted-data experiment that executed in the past (E-1, E-2, H1-H6, H1b) on the withdrawn SPY dataset. History only; descriptive; not validated.
- **[CODE]** behaviour read from source; not executed by me.
- **[DESIGN]** a proposal in this report; **nothing in it has been run**; every number marked PROPOSED/owner-adopted/TBD-pilot is a convention, not evidence.

---

## 1. Verified (evidence I actually have)

Nothing was executed, so there is **no executed verification** in this report. What I did verify, by reading:

- The files exist and say what is quoted below (paths and line numbers in section 2).
- **Hand arithmetic** (re-derivable from numbers printed in `PHASE4_NEURAL_EVIDENCE_REVIEW.md`; the printed numbers are themselves transcriptions, see L-29):
  - relative MAE reduction vs persistence = (MAE_persist - MAE_model) / MAE_persist, with persistence MAE 1.4939 (fixed-expiry) and 1.3510 (nearest-expiry): H3 PCA-ridge fixed 1.4544 -> 2.64 %; H4 PCA-ridge fixed 1.4580 -> 2.40 %; H5 GRU fixed 1.4462 -> 3.19 %; H6 GRU fixed 1.4769 -> 1.14 %; H6 PCA-ridge fixed 1.4607 -> 2.22 %; H2 PCA-ridge nearest 1.3307 -> 1.50 %.
  - count of rule evaluations H1-H6 (model x label, my count from PHASE4 s3.2-3.10): H1 8, H1b 12, H2 10, H3 10, H4 6, H5 10, H6 10 = **66**; label-level passes = **7** (H2 PCA-ridge nearest; H3 PCA-ridge fixed; H4 PCA-ridge fixed; H5 PCA-ridge and GRU fixed; H6 PCA-ridge and GRU fixed). These are not 66 independent trials (the same baseline code is re-run in H3/H4/H5).
  - P(at least 6 of 8 years better | each year a fair independent coin) = (28 + 8 + 1) / 256 = 14.5 %. Illustration only; not a size claim (L-22).
  - minimum-detectable-effect arithmetic of section 4.4 (formula copied from `PHASE0_FEASIBILITY_PLAN.md` s1).

---

## 2. Observed (read, not executed): methodology audit of what exists

Severity: **C** critical to any future claim, **H** high, **M** medium, **L** low/doc. "Fix" lines are design recommendations; code changes are routed to Agent C (section 8).

### 2.0 What the pipeline does (so the findings are checkable) [CODE]

- Surface grid: 6 tenors (7, 14, 30, 60, 91, 182 days) x 9 log-moneyness nodes, `config/settings.py` `SurfaceConfig`. A cell is `OBSERVED` only if a listed expiry lies within max(1 day, 1.5 % of tenor) of the nominal tenor **and** the two bracketing quotes are within 0.02 in k (`surfaces/grid.py:73-83`, `gap_tight`); otherwise linearly interpolated in total variance across expiries (`INTERP_T`) or missing.
- Folds: expanding window; E-1/E-2 validation = previous calendar year; H2/H6 `tail_frac` = chronologically last 20 % of pre-test origins; labels purged against the next window; 8 test years 2016-2023 (`evaluation/walkforward.py:29-62`; `assert_no_overlap` raises, not asserts, lines 65-81).
- Baselines: persistence (causally forward-filled origin surface, <= 5 days), rolling mean (20 rows), per-cell ridge, PCA-ridge (3 factors); ridge penalty chosen on the validation window (`models/baselines.py`).
- Neural: compact MLP / GRU, fixed hyper-parameters (hidden 128 / 64, lr 1e-3, patience 15, max 150 epochs), seeds (0, 1, 2), AdamW, masked MSE, early stopping on the validation window; GPU-only guard (`models/neural.py`).
- Metrics: MAE/RMSE in vol points on cells with target `OBSERVED` and a real origin value (`evaluation/metrics.py:18-23`); pooled by cell count over folds; "MSE skill" = 1 - RMSE_model^2 / RMSE_persistence^2 (`experiments/runner.py:228-235`).
- Rule: `evaluation/decision_rule.py:31-85`: (a) pooled MSE skill > 0 and pooled MAE below persistence; (b) better by daily MAE in >= 6 of 8 test years; (c) every seed's pooled skill > 0; (d) skill > 0 in >= 2 of 3 realised-vol regimes each with n >= 100; label pass = all applicable; verdict vocabulary `improves_on_persistence_under_both_labels | holds_under_{nearest,fixed}_expiry_label_only | no_improvement_shown | not_evaluable`.

### 2.1 Findings

**M-01 (C) The 2016-2023 test period is consumed; "pre-registered" is pre-specification inside an adaptive series.** [RAN + CODE]
- Nine experiments (E-1, E-2, H1, H1b, H2, H3, H4, H5, H6) were all scored on the **same eight test years** (PHASE4 s3.1-3.10). Each design step was chosen after reading the previous test-year results: the H1 grid extension (prompted by the penalty sitting at the grid edge, but accepted/rejected by a test-skill "material change" test, s3.1 line 59); H3 calendar features (suggested by E-2 s8 item 2 after E-2 test results); H4 mean-reversion block; H5 PCA-factor targets; H6 the combination (PHASE4 s3.7).
- The decision-rule thresholds (6 of 8 years, 2 of 3 regimes, n >= 100, 0.01 "material") were fixed on 2026-10-16 (PHASE4 s3, s3.1), **after** E-1/E-2 (2026-10-13) had shown PCA-ridge ahead in 3 of 8 years. A threshold chosen knowing a candidate sits at 3/8 and 5/8 is not blind to the data.
- GR-LEAK-05 / EVALUATION_PROTOCOL s6 ("test window evaluated once per frozen configuration") is therefore not satisfied for any H-series verdict. The new `evaluation/access_log.py` records only per-run fit/select/predict events by code (`record`, lines 32-37); it cannot see a human choosing the next experiment from the last test result, and the executed notebooks did not use it (PHASE4 s1 gap table, line 26-27).
- Consequence: every H-series verdict is **exploratory / hypothesis-generating**. The vocabulary "pre-registered" in PHASE4 s3.7 and README row for H1-H6 should read "pre-specified before the run, on an already-consumed test period". Fix: sealed holdout + experiment ledger (design, section 4.1).

**M-02 (C) Label dependence is a benchmark problem, not (only) a model problem. Neither existing label is a defensible primary target as scored.** [RAN + CODE]

What each label measures:
| | nearest-expiry (E-1, "nearest") | fixed-expiry (E-2, "fixed") |
|---|---|---|
| Object | change of the quote level of "whatever listed expiry sits within ~1 day of the nominal tenor" on each date | change of the IV of the **same expiry slice** that anchored the cell at the origin |
| Built-in non-market components | **contract switching**: 39.6 % of eligible cells change anchor expiry (13 % in 2016 to 52 % in 2023); maturity jitter up to +-1 day (up to +-14 % of a 7-day tenor); persistence RMSE 3.7 at 7d vs 0.8 at 182d (E1 s3 line 56) | **deterministic roll-down**: maturity shortens by 1 trading day = 1 to 3 calendar days (Friday to Monday); 4.9 % of anchored cells censored when the expiry slice vanishes (E2 s4) |
| What plain persistence ignores | the known maturity jump on a switch | the known maturity decay (term-structure slope x elapsed calendar days) |
| Eligible set | observed on t+1 and available (any status) at t | anchored (status >= 2) at t, tight at t and t+1 |

Evidence that the sign flip is a benchmark/label artefact rather than skill:
- Same cells, different label: on the 28,525-cell **common sample** the H5 GRU is +0.0357 (fixed) and -0.0712 (nearest); PCA-ridge flips the other way in E-2 (PHASE4 s3.9 item 1; E2 s5.1). The sample is held constant, so composition does not explain it.
- Persistence is harder under the fixed label (RMSE 3.128 vs 2.700) and the gap is concentrated at 7d/14d (4.715 vs 3.822; 2.776 vs 2.615) and absent at >= 60d (E2 s5.1). That is the signature of a known deterministic drift in the label.
- Every H-series positive verdict came **after calendar features (days-to-expiry of the anchor, weekday one-hot) were added** (H3 onward; `features/panel.py:120-126`), and all 7 label passes sit in H2-H6 (6 of 7 in experiments with the calendar block). PCA-ridge + calendar is better than persistence in **8 of 8** test years under the fixed label in H3 (PHASE4 s3.5 item 4). 8/8 is not coin-flip behaviour (0.4 % for fair independent coins); the parsimonious reading is that **plain persistence is a mis-specified benchmark for a rolling contract**, so a model that is told "how many days remain" beats it mechanically (this is KNOWN_LIMITATIONS L-30).
- The weekday part is probably tied to the owner-decided day-count (DEC-005: T = calendar days / 365, no trading-day calendar): IV computed with calendar-time T embeds a Friday-to-Monday mismatch because total variance does not accrue on weekends. `Hypothesis, untested`; it can be examined on synthetic data (section 5, S-1) before it is blamed or credited.

Which is defensible?
- As a *forecast of the standardised constant-maturity surface* (the project's stated target, FORECASTING_STRATEGY s1; `grid.py` header "constant-maturity"): neither as scored. Nearest-expiry is closer in intent but its OBSERVED-only restriction imports contract-switch noise and a calendar-dependent eligibility rule.
- As a *forecast of a tradable-contract IV*: fixed-expiry is the cleaner object, but only against a **maturity-aware naive benchmark** (read today's surface at the contract's next-day maturity). Against plain persistence it measures whether the model knows that time passes.
- Recommended primary (section 4.2): **score at contract level** (forecast surface queried at the next-day contract coordinates, DEC-006 interpolation rules unchanged) against **two** naive benchmarks, plain and maturity-aware; keep both existing labels as secondary diagnostics. If that is rejected by the owner, the fallback is nearest-expiry scored on all non-missing cells (the `all` mask, already in E1 s3 line 41: PCA-ridge +0.037, ranking unchanged) with the switch-share reported, and fixed-expiry only against the maturity-adjusted benchmark. A sign flip between labels must be reported as "benchmark-dependent", never averaged away or resolved by choosing the flattering label after the fact.

**M-03 (H) The rule accepts arbitrarily small effects and produces no uncertainty; it is weaker than the project's own Phase 0 research criterion.** [CODE]
- Criterion (a) passes at any positive skill and any lower MAE (`decision_rule.py:36-37`). The Phase 0 proposed research criterion (PHASE0_FEASIBILITY_PLAN s3.2, lines 62-68) is a **minimum relative MAE reduction r\* (proposed 3 %)** **and** an interval excluding zero. By my arithmetic (section 1), the seven label passes have MAE reductions of 1.1-3.2 %; only the H5 GRU (3.19 %) is above a 3 % point-estimate threshold, and there is no interval for anything. "Passes the rule" therefore does not imply "meets the Phase 0 research success criterion".
- The inference gap is a known owner-closed item (PA-1 CLOSED - NO-GO, L-22): no p-value, interval or "significant" may be used. This report respects it; section 4.5 specifies what to store so a future owner-approved method can be applied retrospectively.
- Metric inconsistency: Phase 0 names **MAE** primary; the rule's (a) leads with pooled **MSE skill**. Errors are extremely heavy-tailed (residual excess kurtosis 56-66, E1 s3 line 58) and 2020 dominates pooled MSE (E1 s4: MLP/GRU pooled deficit "driven by 2020"). MSE skill is therefore a few-days statistic.
- Weighting: the pooled metrics weight by evaluated-cell count, and that count rises with regime (2,698 cells in 2016, 6,277 in 2022; E2 s4). The Phase 0 plan states "unit of inference = origin day" (s3.2), so pooled-by-cell metrics over-weight busy, volatile years.
- Fix (design): primary = per-origin mean absolute error (origin is the unit); report MSE skill, relative/log-IV error and a leave-worst-block-out variant as secondary; a minimum effect r\* inside the pass condition (section 4).

**M-04 (H) Multiplicity and forking paths across H1-H6.** [RAN]
- 66 model-by-label rule evaluations, 7 label passes (section 1). The verdict `holds_under_one_label_only` is a **disjunction over two labels** (`combine_labels`, `decision_rule.py:73-84`), which raises the chance of at least one pass relative to a single pre-chosen label.
- Criterion (b) alone passes 14.5 % of the time under a fair-coin illustration, and the passing sets are highly correlated (the same PCA-ridge code is repeated in H3/H4/H5; H5's PCA-ridge "repeats H4 exactly", PHASE4 s3.9 item 2), so the 7 passes are far fewer than 7 independent confirmations, and no multiplicity correction is defined.
- The configuration space was explored adaptively (grid, validation mode, calendar, MR window, factor target, label) with no log of the number of variants tried. For the future design a **trial ledger** is required (section 4.1, CF-6).

**M-05 (H) The baseline ladder is incomplete and the neural-vs-baseline comparison is asymmetric.** [CODE + RAN]
- FORECASTING_STRATEGY s3 rungs 2 (training-only mean change) and 4 (autoregressive on factors) are **not implemented**; the stronger zero-parameter benchmark (maturity-aware persistence) is missing. `rolling_mean` (RMSE 5.0 vs 2.6, E1 s3) is a straw baseline, not a mean-reversion benchmark: it replaces the level by a 20-day average and has no shrinkage weight.
- Tuning asymmetry: baselines were re-tuned after seeing test results (H1/H1b penalty grids, H3/H4 features), whereas the neural recipe was **never tuned** (fixed a priori, no search; PHASE4 s1 line 17) and ran near-untrained in **30-56 of 96 runs per experiment** (H3 30, H2 56, H5 38, H6 41; best epoch <= 3). The NO-GO on neural is a statement about one untuned recipe at ~1,200-2,950 training origins, not about neural capacity, and the "GRU ~ PCA-ridge + calendar" outcome (H5/H6) is "not interpretable" (README row; PHASE4 s3.10 item 3).
- Selection noise: one validation year chooses the ridge penalty and the stopping epoch; chosen penalties span 0.1 to 1e6 across folds (PHASE4 s3.2 item 4), and the validation loss for the 2020 validation year is 6.5-7.1 vs 0.6-0.8 training (E2 s9). H2's `tail_frac` did not help (PHASE4 s3.6 item 4).
- Fix: complete ladder + nested/blocked selection (section 4.3, R-2).

**M-06 (H) No positive control exists for the neural recipe.** [CODE + RAN]
- The synthetic runs in the repository exercise plumbing (`datasets/synthetic.py`: AR(1) level/skew with persistence 0.97 and 0.98; term slope 0.02 per year) and the stdlib Phase 0 spike tested only a factor-AR1 forecaster. No synthetic world with a **known, learnable, non-trivial signal** has ever been given to the MLP/GRU recipe, so a null on real data is uninformative about whether the recipe can learn at N ~ 2,000. PHASE4 s3.6 item 5 ("points to the target/features ... rather than which year is held out") is an inference not supported by a test: a training-recipe pathology (learning rate vs standardised targets, near-zero-change targets, weight decay) predicts the same early stopping.
- Fix: positive and negative controls before real data (section 5, S-3).

**M-07 (M) The evaluation population is selected on post-origin information.** [CODE]
- Primary cells require the **target-day** cell to be `OBSERVED` (tight bracket) and, for fixed-expiry, the same expiry tight on both days (`metrics.py:18-23`; `panel.py:113-116`). Whether a slice is tight tomorrow depends on tomorrow's quote density and liquidity, which correlate with tomorrow's volatility. The same cells are used for every model (fair among models, verified by unit tests, `test_every_model_is_scored_on_exactly_the_same_cells`), but absolute levels and skill magnitudes are conditional on that selection.
- Censoring (4.9 % of anchored cells under the fixed label, 1,959 cells) is not decomposed by cause nor by regime (E2 s2, s4); filter rejection is more likely in stressed sessions (relative spread > 0.35, zero bid, etc.), which is a survivorship-type bias toward calm outcomes. Cells eligible under one label only: 8,268 vs 7,313, composition not decomposed (E2 s4).
- Fix: report the same metrics on the `all` mask and contract-level scoring; report the censored share by regime and by tenor.

**M-08 (M) Selection criterion differs from reporting criterion; unlabeled cells are imputed as "no change".** [CODE]
- Ridge/PCA-ridge penalties are selected on the masked MSE over the `all` mask (observed + interpolated) (`baselines.py:49-52`), the networks stop on a loss over `ystat > 0` (`runner.py:157`), whereas results are scored on `OBSERVED` cells. Training labels include interpolated target cells, so models partly learn the interpolator.
- For the fixed label the PCA-ridge target is the origin surface wherever the label is missing (`baselines.py:105-106`); H5/H6 factor targets zero the missing-label cells (`runner.py:103-108`). Censored (near-expiry) cells thus enter training as "persistence was right", biasing PCA models toward persistence exactly at the short tenors where roll-down matters.

**M-09 (M) Regime definition is not a regime study.** [CODE]
- Regimes are terciles of **realised volatility of the underlying** (longest window), cut-offs re-estimated from each fold's training origins (`metrics.py:84-88`) and then pooled across folds, so "high" in 2016 and in 2022 are different thresholds. There is no stress definition on IV level, no event windows, and only two distinct stress blocks (2020, 2022). Phase 0 M5's regime rule is still `TBD-pilot` (PHASE0_FEASIBILITY_PLAN s7).
- Fix: a single past-only regime rule frozen before data is seen; report skill per regime **and** per block (section 4.1).

**M-10 (M) Dependence, seeds, provenance.** [CODE + RAN]
- Effective sample = origin days (~1,950 in 8 years), not 36,793 cells (about 19 evaluated cells per day). Criterion (c) (all seeds positive) tests optimiser noise only, not data variability; 3 seeds is minimal. Seeds were not selected post hoc (fixed (0,1,2)); good.
- The per-origin loss-difference series (needed for c and rho in the Phase 0 power formula) was **not stored outside the Colab/Kaggle runtimes**; `evaluate_all` keeps only means, shares and counts (`runner.py:237-254`). So even the effect-size scale c of the H-series is unknown (L-29).
- The config hash `28b90c2a` is identical for H2, H3, H4 (and shared with H5/H6) because `calendar`, `mr_window`, `val_mode`, `pca_factors`, `target` are notebook flags, not `Config` fields (PHASE4 s3.8). `evidence.py` records `label` and `val_mode` but cannot tell feature sets apart (`compare_records(same_features=None)` -> flagged non-equivalent, lines 79-94).

**M-11 (M) Leakage: what was actually checked, and what cannot be checked by the existing tests.** [CODE]
- Checked in code (read, not run): features at an origin are invariant to scrambling later rows incl. calendar and MR variants (`leakage.py:13-43`; `test_feature_leakage_variants`); fitted baselines (standardiser, PCA, ridge) unchanged when post-cut data is scrambled, with a negative control (`test_leakage_sentinels`); folds chronological and purged, test year absent from train/validation (`walkforward.py`); regime cut-offs, fill values, PCA basis, target scale all from training rows.
- Not covered: (i) **neural fitting path** (no sentinel for checkpoints; GPU-only, PHASE4 s1 line 10); (ii) **vendor/raw field timing** (L-11, L-32): an "underlying last" or vendor IV stamped later than the quote snapshot cannot be detected by truncation tests; (iii) **human selection on the test period** (M-01); (iv) the origin-inclusion rule `gap_ok` uses the existence of date t+h (`panel.py:142-143`), calendar information only, acceptable but should be listed; (v) `causal_fill` forward-fills up to 5 rows, so persistence may be a stale value (not leakage; it weakens or strengthens persistence depending on staleness, and is not reported).
- Leakage verdict: **no look-ahead path found in the code; the dominant bias in the evidence is selection on the test period (M-01), not information flow into fitted parameters.**

**M-12 (M) Reporting shape vs GR-MOD-02/03.** [CODE]
- `breakdowns()` returns four **marginals** (tenor, k, origin year, rv regime), each with `n_cells`, `n_missing`, `insufficient_n` (`metrics.py:54-81`). EVALUATION_PROTOCOL s4 and GR-MOD-02 ask for maturity x moneyness x period x regime. The notebook heatmaps give per-cell results, but the cross-tabulated table with `n` per cell and bucket edges (`TBD(Phase 3)`) does not exist. No relative (log-IV) error exists, so low-vol years (2017: RMSE 0.92) and high-vol years (2020: 4.86) are compared in absolute points only.

**M-13 (L) Statements in the docs that go beyond the evidence.**
- PHASE4 s3.9 item 5: "Reducing the target to 3 PCA factors is the first change that turned a neural model's fixed-expiry skill positive and consistent": the H3 cell-level GRU was already +0.0336 pooled (one seed negative), H6's cell-level GRU reaches +0.0479 with all seeds positive without any factor reduction, and H5 changed two things at once relative to H3 (factor target and MR block). The causal attribution is not supported; the "one change per run" principle (s3) is not met for the neural comparison H3 -> H5.
- PHASE4 s3.6 item 5 (see M-06) and s3.3 item 3 ("nothing the ridge/PCA features add beat 'persistence plus a constant change'", a plausible reading, untested; no constant-change baseline exists, M-05).
- "pre-registered" wording (M-01); README/IMPLEMENTATION_PLAN already carry the key caveats (one label, not general, not VALIDATED), so no rewrite of their conclusions is needed, only the term "pre-registered" for H4-H6.
- KNOWN_LIMITATIONS has no entry for: consumed test period (M-01), missing maturity-aware benchmark (M-02), no neural positive control (M-06), selection-on-outcome population (M-07). Proposed additions are in section 8 (routed; I may not edit that file).

### 2.2 What H1-H6 evidence is and is not  [RAN, history only]

**It is:** a descriptive record of nine single runs (E-1, E-2, H1, H1b, H2, H3, H4, H5, H6) on an end-of-day SPY options panel (2010-2023, 3,500 surface dates) from a hosted dataset of **unverified upstream licence, withdrawn on 2026-10-20 (DEC-002)** and "kept as unpublishable history". Provenance quality varies: E-1/E-2/H1/H1b/H2 were committed Kaggle versions with in-run reproduction gates and file hashes; **H3 is an uncommitted interactive session, H4-H6 were transcribed from cell outputs/screenshots by a browser agent**, outputs are not stored anywhere reachable (L-29). The owner waived independent verification on 2026-10-20; that waiver is recorded, it is not a validation.

**It is not:** validation (no `VALIDATED` claim is possible: `evidence.validated_problems` would reject it for licence, intervals, `test_accessed_count`, owner confirmation); statistical evidence (no interval or p-value, by the PA-1 closure); a statement about generalisation across vendors, underlyings, periods or markets; a statement about neural capability (untuned recipe, near-untrained runs, no positive control); evidence for a general improvement over persistence (best formal verdict: `holds_under_fixed_expiry_label_only`, negative under the other label, with the benchmark problem of M-02); publishable.

**It may legitimately be used for:** (1) generating hypotheses and priors for a new dataset (calendar block, factor-space targets, grid saturation behaviour), always re-pre-registered as hypotheses; (2) effect-size *scale* for planning (skill of order 0.02-0.05, MAE reductions 1-3 %), flagged as non-transferable; (3) finding pipeline pitfalls (near-untrained stopping, label switching, hash gaps). It must **not** be cited as validated evidence in any document or UI string.

---

## 3. Blocked, Not run, Failed

**Blocked:** every real-data step (R-0 onward in section 4): no authorized dataset (AP-002 not requested; DEC-002 withdrawal; MVD M10 licence unmet); neural steps additionally need AP-003 (training approval) and a verified GPU in Colab (DEC-015, OD-7). Statistical-inference work is closed by the owner (PHASE0_CLOSURE_RECORD s7 items 1 and 4).
**Not run:** everything. No code, test, notebook, simulation or data access was executed. The unit/scientific tests named in this report were read, not run; the totals in docs (252 OK / 1 skipped) are the owner's local PC counts from before the Colab-only rule and have not been re-run in Colab (SHARED_STATUS).
**Failed:** nothing executed, so nothing failed. Pre-existing disclosed failures (Phase 0 H-S1/H-S2/H-S4/H-S6 in 1-2 of 19 study runs; A2b `NO_METHOD_ADMISSIBLE`) are history in PHASE0_CLOSURE_RECORD.

---

## 4. Proposed: experiment sequence for a *future authorized* real dataset  [DESIGN, nothing run]

Everything below is a **proposal for the owner**. Thresholds are of three kinds, always labelled: **owner-adopted** (MVD values frozen 2026-10-20 from "Adopt the PROPOSED ones": M1-M5, M7, M9, M11, M12, M6 start 60 %; **not evidence-based**), **PROPOSED** (my convention, needs adoption), **TBD-pilot** (to be set from the R-0 pilot before any model is trained). Nothing here pre-empts DEC-001/002/003/006/011/012; the grid and interpolation rules stay DEC-006 option A.

### 4.1 Common frame (CF) applying to every stage

- **CF-1 Partition (chronological, sealed).** Split the first fixed snapshot set into **development D** and a **sealed confirmation holdout T = the final max(600, pilot-implied N\*) origins** (owner-adopted M4). No D-stage decision may read T. T is opened **once**, for one frozen configuration set (CF-7), by a person other than the one who tuned, with the config hash written to the access log **before** opening. Under owner-adopted M3 (>= 2,000 snapshots) this leaves about **1,400 dev origins**, which supports roughly: initial training >= 3 years (~750 origins) and **about 5 inner expanding folds of ~125 origins** (PROPOSED). That is thin for neural models (L-07): if the pilot says it is too thin, the study is declared *underpowered/limited in advance*, not widened afterwards.
- **CF-2 Target and benchmarks (frozen before data).** Primary scoring is **contract-level** (section 4.2). Benchmarks in the ladder: B0a plain persistence (cell-level), **B0b maturity-aware persistence** (today's surface read at tomorrow's contract maturity by the DEC-006 total-variance rule, zero parameters), B1 training-only mean change per cell (and per days-to-expiry bucket), B2 ridge, B3 PCA-ridge, B4 autoregressive on PCA factors (rung 4). The **skill reference is the stronger of B0a/B0b on dev**, named before T is opened.
- **CF-3 Metrics.** Primary: per-origin mean absolute error in vol points (decimal stored; both units labelled), averaged over origins; contrast = relative reduction r = (MAE_ref - MAE_model)/MAE_ref. Secondary: RMSE, MSE skill, relative (log-IV) MAE, leave-worst-block-out MAE, directional accuracy only if defined. Every table carries `n_origins`, `n_cells`, `n_missing`, exclusions.
- **CF-4 Required tables.** T1 pooled by origin; T2 maturity bucket x moneyness bucket (bucket edges fixed in R-0; `insufficient` if `n_origins` below TBD-pilot, never dropped); T3 by calendar block and by fold, with the **ranking per fold**; T4 by past-only regime (rule frozen in R-0; stress defined from past data only); T5 seed and fold dispersion; T6 **trial ledger** (every configuration evaluated, count of contrasts evaluated against T, search budget); T7 summary of the per-origin loss-difference series (mean, median, SD, c, first-order rho); T8 worst-N origins; T9 censored/excluded cell shares by tenor and regime; T10 reproduction hash of every number.
- **CF-5 Required leakage tests (all must be green in Colab before the stage's result is read).** LT-1 chronological split + purge incl. holdout never in train/val (exists, extend to T); LT-2 truncation invariance for **every** cataloged feature and for the calendar/days-to-expiry features (partly exists); LT-3 fitted-parameter sentinel for baselines (exists) **and for neural checkpoints** (new; GPU); LT-4 label-construction isolation: expiry anchoring and benchmark B0b use origin-day information only (partly exists); LT-5 raw-field timing audit: every vendor/underlying field's timestamp vs snapshot time, any field computed with later information is excluded (new, data-specific; cf. L-32); LT-6 test-access log with `test_accessed_count == 0` for selection and the frozen-config hash recorded before opening (module exists, never used by an executed run); LT-7 **negative control**: shuffle target dates inside training (or randomise labels) -> held-out skill ~ 0; LT-8 **leak canary**: inject a feature that equals tomorrow's value -> the harness must show absurd skill (proves the harness can detect leakage); LT-9 eligible-population independence report (metrics on origin-only-known vs target-dependent masks).
- **CF-6 Seeds and selection.** Neural: **>= 5 seeds** (PROPOSED; the H-series used 3), fixed list pre-registered, no redraw, no seed selection; ensemble is the primary prediction, every individual seed and the bottom-seed result reported. Deterministic baselines: seed n/a. Hyper-parameter search: declared space + budget K (trials) + the selection rule (nested/blocked: choose by the **mean over inner validation blocks**, not one year); every trial logged in T6.
- **CF-7 Multiplicity and confirmatory contrasts.** Exactly **one primary contrast per stage** (named model family vs named reference, one primary label/scoring, one metric). All other comparisons are secondary and labelled exploratory. At most one frozen configuration per model family is carried to T; a second candidate needs a new untouched period. If more than one primary contrast is declared they are a family corrected by Holm (conventional adjustment, not a validated size claim; PA-1 closure applies).
- **CF-8 Inference status.** Until the owner approves and independently validates a method (PHASE0_CLOSURE_RECORD s7 item 4, L-22), results are **descriptive**; the run record stores the per-origin loss series, the fold boundaries and the block indices so a later approved method can be applied retrospectively **without re-running** (this addresses M-10). An interval, if ever shown, carries `uncertainty_kind` per `UNCERTAINTY_AND_CALIBRATION.md`.
- **CF-9 Execution and provenance.** Colab only (OD-7); device, framework, CUDA, seeds, data version, config hash **including** target/val_mode/calendar/MR/factor flags, code hash recorded; neural runs raise rather than fall back to CPU (DEC-015).

### 4.2 Scoring definition (R-1 decides; owner approval needed) [AP-008 approved 2026-10-21 for the primary scoring and fallback; see section 11]

For each origin t and each contract j listed and passing the quote filters at t+1 (target day): forecast IV_hat(j) = forecast surface evaluated at (k_j, T_j(t+1)) by the production rules (linear IV in k, linear total variance in T, no extrapolation); contracts outside the origin-day hull of the forecast surface are counted as `n_missing`, not imputed. Realised = the target-day quote IV. B0a = origin surface evaluated at the contract's *origin-day* maturity (plain persistence); B0b = origin surface evaluated at the contract's *target-day* maturity (maturity-aware persistence). Per-origin loss = mean absolute error over contracts passing the filters (equal weight; vega-weighted as secondary). The label and the benchmark are thereby separated: roll-down belongs to the benchmark, not to the "model skill".

### 4.3 Stage sequence

For every stage: hypothesis, metric/threshold, split/folds, leakage tests, seeds, tables, stop/no-go.

**R-0 Data admissibility and pilot (no model).** *Hypothesis:* the authorized dataset meets the owner-adopted MVD M1-M12 and is long enough for a decisive test. *Metric:* MVD checklist with evidence (M10 licence in writing first); pilot estimates of c (SD of per-origin loss differences / mean reference loss), rho, per-snapshot observed-node share vs 60 % start target, solver convergence (proposed 90 % per feasibility S5), censoring share, regime rule, bucket edges, minimum `n` per cell. *Split:* none (data audit only); the sealed T is defined here by date, not by looking at performance. *Leakage tests:* LT-5. *Seeds:* n/a. *Tables:* MVD evidence table, power table (4.4), data audit. *Stop/no-go:* MVD unmet -> re-scope decision (never silent acceptance); licence unverified -> STOP; implied MDE for the sealed T above the owner's r\* -> the whole study is **declared underpowered in advance** and capped at wording tier D1 (4.6). These values freeze in the Freeze Record before any model result exists.

**R-1 Target and benchmark validation (still no learned model).** *Hypothesis:* H-R1a: B0b removes the deterministic maturity component that makes plain persistence unreasonably weak under the fixed label; H-R1b: contract-level scoring avoids anchor-switch noise. *Metric:* B0a vs B0b per-origin MAE by tenor and weekday; share of persistence MSE removed; fraction of target contracts inside the origin hull (coverage); anchor-switch share under nearest-expiry. *Threshold:* coverage of the contract-level scoring >= TBD-pilot (PROPOSED start 95 %); decision rule for the primary scoring named in advance: contract-level unless coverage fails, in which case nearest-expiry on the `all` mask with switch share reported. *Split:* dev only. *Leakage tests:* LT-4, LT-9. *Seeds:* none. *Tables:* T1-T4, T9. *Stop/no-go:* if neither scoring produces a stable reference (e.g. B0b residual strongly weekday-dependent, signalling a day-count/convention problem rather than a model problem) -> STOP and send to Agent C / owner (DEC-005 sensitivity), do not train models.

**R-2 Baseline ladder on dev (non-neural).** *Hypothesis:* H-R2: at least one fitted baseline (B1-B4) beats the stronger of B0a/B0b on dev by >= r\*_base. *Metric/threshold:* relative MAE reduction >= r\* (PROPOSED 3 %, from PHASE0 s3.2, which is itself unfrozen; revisit after R-0 so that r\* is above the MDE) in >= ceil(0.75 x m) of the m inner folds, with the same sign in >= 2 regimes. The H-series' 6-of-8 and 2-of-3 conventions may be kept as a secondary descriptive check. *Split:* inner expanding folds of D; validation = last block before each fold test (purged), penalties and PCA components chosen by the mean over inner blocks; ridge/PCA penalty grid extended automatically until the chosen penalty is not at either edge (rule stated in advance; H1/H1b showed edge saturation). *Features:* lags, rv, availability; calendar/days-to-expiry and mean-reversion blocks are **separate ablations** (not a bundle). *Leakage tests:* LT-1..4, LT-7, LT-8. *Seeds:* none. *Tables:* T1-T10. *Stop/no-go:* **no baseline beats B0b by r\*_base** -> write the go/no-go note (Phase 3 A5) as NO-GO for neural, report "maturity-aware persistence was not beaten on [dataset, period]"; end of the neural path unless the owner explicitly asks for a probe with a declared a-priori non-linear hypothesis.

**R-3 Baseline robustness battery on dev.** *Hypothesis:* the R-2 conclusion is not an artefact of a choice. *Checks (all secondary/exploratory, labelled so):* expanding vs rolling window; alternative quote filters; observed-only vs `all` mask vs contract-level; leave-worst-block-out; with/without calendar block; trading-day maturity convention sensitivity **only if the owner relaxes DEC-005** (otherwise reported as a limitation); liquid vs less-liquid regions; dependence on few dates (leave-k-dates-out). *Stop/no-go:* a conclusion that flips under a single such check is reported as "not robust" and carried forward as the weaker wording tier.

**R-4 Neural development on dev (GPU, Colab; requires AP-003).** *Pre-conditions (go/no-go note):* (i) the positive control of section 5 (S-3) passed at this dataset's N with the same recipe; (ii) R-2 gave a fitted baseline that beats B0b, or the owner approves an explicit a-priori non-linear hypothesis; (iii) DEC-012 decided. *Hypothesis:* H-R4: the MLP (then, only if it shows promise on dev, a GRU) beats the **best R-2 baseline** (not only persistence) by >= r\* in >= ceil(0.75 x m) inner folds, seed-consistent. *Model order:* MLP on the best baseline's feature set, in cell space and in PCA-factor space as two pre-declared variants (DEC-011 comparator); sequence model only after MLP evidence; no Transformer. *Search:* declared budget K (PROPOSED <= 20 trials per family), selection by mean inner-block validation, every trial logged. *Capacity diagnostic as a stop rule:* if more than 25 % (PROPOSED) of runs choose best epoch <= 3, the recipe is declared **not using its capacity** and the family stops (no further retuning outside the declared budget); the H-series figures were 31-58 %. *Seeds:* >= 5, fixed list. *Leakage tests:* LT-3 (neural), LT-6..8. *Tables:* T1-T10 plus per-seed table and training curves. *Stop/no-go:* family fails the threshold -> negative result recorded and reported ("honest negatives" S5 contract).

**R-5 Mechanism and ablation checks on dev.** *Question:* is any neural or baseline edge explained by the deterministic calendar? Run: (a) remove calendar features; (b) replace the label by the maturity-adjusted one; (c) score against B0b, not B0a; (d) feature-group ablations; (e) per-tenor and per-moneyness attribution with `n`. *Threshold:* an edge that disappears against B0b, or that exists under only one scoring definition, is reported as benchmark-dependent and **cannot be advanced to T as a model-skill claim**.

**R-6 Sealed confirmation (single opening).** *Frozen set:* {reference benchmark, best baseline from R-2, best neural model per family from R-4}, hashes recorded. *Hypothesis (one primary contrast):* the best neural model beats the best baseline by >= r\* in per-origin MAE on T; secondary: each vs the reference benchmark. *Reporting:* T1-T10 on T, no re-tuning, no second opening. *Outcome handling:* section 4.6 wording; any tuning after seeing T makes T consumed and requires a new untouched period.

**R-7 Prospective tracking (optional, only if licence allows ongoing collection).** Forward-only, `forecast_kind = prospective` (GR-PRD-05), origin timestamps written before targets exist. This is the only design element that produces evidence that cannot have been fitted post hoc.

### 4.4 Sample size and minimum detectable effect (illustrative; c and rho are unmeasured)

Formula (from `PHASE0_FEASIBILITY_PLAN.md` s1, two-sided 5 %, 80 % power, loss differences d_t per origin): r_min ~ 2.8 c / sqrt(N) x sqrt((1+rho)/(1-rho)). By hand, in % relative reduction of the mean loss:

| c (SD(d)/mean reference loss) | rho | N = 600 | N = 1,000 | N = 1,950 |
|---|---|---|---|---|
| 0.10 | 0 / 0.3 | 1.1 / 1.6 | 0.9 / 1.2 | 0.6 / 0.9 |
| 0.25 | 0 / 0.3 | 2.9 / 3.9 | 2.2 / 3.0 | 1.6 / 2.2 |
| 0.50 | 0 / 0.3 | 5.7 / 7.8 | 4.4 / 6.0 | 3.2 / 4.3 |
| 1.00 | 0 / 0.3 | 11.4 / 15.6 | 8.9 / 12.1 | 6.3 / 8.6 |

Origins needed to resolve r = 3 % with c = 0.5: about 2,180 (rho 0) or 4,050 (rho 0.3); with c = 1.0: 8,710 / 16,180. Consequences: (1) the owner-adopted floor of **600 test origins cannot resolve a 3 % effect unless c <= ~0.1-0.15**; with c unknown the default expectation is "underpowered in advance" and the default wording tier is D1 (4.6); (2) the H-series effect sizes (MAE 1-3 %) would have been undetectable at 600 origins for any c >= 0.25; (3) c for two highly correlated forecasters may be small, which is exactly why R-0 must measure it from the pilot rather than assume it. These are a planning arithmetic, not a significance claim, and are not validated for heavy-tailed errors (kurtosis 56-66 observed in the old data). The owner-adopted values are conventions, **not evidence-based**.

### 4.5 What the run record must store (so a later, owner-approved inference method needs no re-run)

Per origin: date, benchmark and model losses (primary and secondary), n evaluated contracts; fold and block ids; regime label; seeds and per-seed predictions hashes; the trial ledger; censored/excluded counts by cause; code/config/data hashes; `test_accessed_count` and the frozen-config hash with timestamp.

### 4.6 Minimum evidence before any model may be called "useful", and allowed wording

"Useful" is defined narrowly as **useful as a backtested forecaster of the next-session surface for a research display**, never as profitable or tradable. All of U1-U9 must hold:

U1 licence verified in writing for the intended use (MVD M10); U2 MVD M1-M12 evidenced (owner-adopted values; not evidence-based) with the study's own power table; U3 the sealed T unopened until the frozen set was written, `test_accessed_count == 0`; U4 the model beats the **best baseline and the maturity-aware benchmark**, not only plain persistence; U5 effect >= r\* in per-origin MAE on T and on the dev folds, with the same sign in >= ceil(0.75 x periods) blocks and in >= 2 regimes incl. one stress block; U6 seed-consistent (all >= 5 seeds same sign; bottom seed reported); U7 survives R-5 (no dependence on the calendar block alone, on one scoring definition, or on one block such as a single crash year); U8 all LT tests green in Colab, including the negative control and leak canary; U9 a validated inference method (owner-approved protocol, independently checked, L-22) supports the effect, otherwise tier D1 is the ceiling.

| Outcome | Allowed wording (and ceiling) | Not allowed |
|---|---|---|
| O1 No fitted model beats the maturity-aware benchmark on dev | "Maturity-aware persistence was not beaten on [dataset, market, period, n origins]; no improvement shown." | "neural networks cannot forecast IV" |
| O2 A baseline beats the benchmark; neural does not beat that baseline | "A [linear/PCA] baseline had X % lower per-origin MAE than persistence on [sample] (descriptive); the neural model did not beat it." | "the neural model improves" |
| O3 Neural beats on dev, not on T | "Did not replicate on the held-out period; dev result is exploratory." | quoting dev numbers as the result |
| O4 Neural beats on T but underpowered/no validated inference (tier D1) | "Descriptively lower error on the held-out period (n origins, label, benchmark); underpowered/no interval; backtest on [dataset]; not evidence of live skill." | "significant", "outperforms" without qualifiers, "validated" |
| O5 U1-U9 all met (tier D2) | "In a backtest on [dataset, period, market], model M had X % lower per-origin MAE than the best baseline (interval, method named); holds under [scoring]; limitations L-.." | "predicts", "beats the market", "alpha", "live", any profitability claim; transfer to another market |
| O6 Mixed by region/regime/label | Report the region/regime/label list with `n`; "benchmark-dependent" if the sign flips across scoring definitions | a pooled headline |

---

## 5. Proposed: what can be done on synthetic data only, and what it can and cannot show  [DESIGN, nothing run]

Synthetic data is labelled `SYNTHETIC - not market data` and **is never evidence about a market** (GR-DATA-04). Items S-1..S-3 need code or generator changes (Agent C) and Colab execution; S-3 needs a GPU. All are research-design items; none has run.

| ID | Study | What it can show | What it cannot show | Notes |
|---|---|---|---|---|
| S-1 | **Calendar-artefact negative control.** Synthetic chain whose factors follow a random walk (no predictability) but with a **steep short-end term structure**, calendar-day T, and variance accruing on trading days. Score a plain-persistence label, a fixed-expiry label, B0b, and a model with days-to-expiry/weekday features | whether a calendar-aware model gains "skill" over plain persistence with **zero market predictability** (the M-02 hypothesis), whether B0b removes it, and whether a DEC-005 calendar-day convention creates a weekday effect | the size of any such effect in real data; the true short-end term structure | The existing generator has `term = 0.02` per year (`datasets/synthetic.py:17`), i.e. a 1-3 day roll-down of about 0.005-0.016 vol points; far smaller than anything seen in the real 7d/14d errors (RMSE 3-5 vol points), so **the current synthetic tests could not detect this artefact** |
| S-2 | **Label/benchmark equivalence checks.** Where the generator's truth is known: verify contract-level scoring reproduces the known error of B0b exactly; compare nearest-expiry, fixed-expiry and contract-level on the same truth | correctness of the scoring and of anchor/switch accounting; magnitude of switch noise as a function of expiry density (weekly vs daily listings; `expiry_freq`) | real quote noise, real listing patterns | cheap; supports the R-1 decision |
| S-3 | **Neural positive/negative control (GPU, Colab).** World with a **known learnable signal** (AR factors with phi 0.5-0.9, plus a mild non-linear component) and a random-walk world; train the same MLP/GRU recipe at N = 500 / 1,000 / 2,000 / 3,000 origins; track skill vs the oracle, best-epoch distribution, seed spread | whether the recipe *can* learn at a given N (detects a recipe pathology behind the 30-56 near-untrained runs), the sample size at which the recipe reaches e.g. a fraction of the oracle gain, and that in the RW world it does **not** invent skill | whether real surfaces contain any learnable structure; the N needed on real data | **Prerequisite** to read any real-data neural null (M-06); the closest thing to a power study for the neural recipe |
| S-4 | **Harness self-tests for the future frame:** leak canary and negative-control (LT-7, LT-8) on synthetic panels; sealed-holdout access-log workflow with a mock opener; reproduction-hash round-trip | that the harness detects leakage when it exists and refuses a second holdout opening | leakage in raw vendor fields (needs the real data) | cheap, no GPU |
| S-5 | **Operating characteristics of the pre-specified descriptive rule** (a-d + r\*): how often it passes in RW worlds, in AR worlds, and with injected calendar artefact | an audit of the rule itself under known truth | a nominal size/coverage claim, a validated test | **Needs an explicit owner decision**: PHASE0_CLOSURE_RECORD s7 item 1 closes "any further statistical-method experiment"; this is an audit of a descriptive rule, not a new inference method, but the boundary is the owner's to call. Not proposed to run without that decision [Superseded 2026-10-21 by AP-008 (c) / OR-D10: S-5 stays inside the PA-1 closure and is NOT to be run; reopening needs a new explicit owner decision] |
| S-6 | **Metric-table and reporting-schema tests:** hand-calculated per-origin MAE, cross-tabulated maturity x moneyness x regime tables with `n`/`n_missing`, insufficient-`n` flagging | reporting correctness | anything about performance | consistent with GR-MOD-02/03 and M-12 |

Synthetic results can validate pipeline logic, scoring and harness behaviour and can motivate design choices; they cannot validate a model or a threshold for a market.

---

## 6. Proposed: US and India as separate studies  [DESIGN; market facts `NEEDS RESEARCH` unless the repo establishes them]

The market is **not decided here** (DEC-001; OD-2 states both are wanted, as separate studies). Each market gets its **own** pre-registration (R-0..R-6), MVD evidence, grid pilot, regime rule, sealed holdout, benchmarks and wording ceiling. **No pooled training or pooled evaluation**; a later cross-market transfer test (train on one, test on the other) would be a separate, labelled-exploratory study with its own protocol. DEC-006's grid (6 tenors x 9 nodes, +-0.20 k) was designed for SPY and is **not assumed** to fit either market.

**US-specific issues**
- Underlying choice drives the pricing assumptions: SPX/SPXW index options (European, cash-settled; AM vs PM settlement mix for monthly vs weekly/daily expiries) vs SPY (American, physically settled; early exercise and discrete dividends; L-06, L-23). SPX is the open DEC-001 alternative.
- Expiry structure is non-stationary: the number of listed expiries and weekly/daily cycles has grown, and the old panel's eligible-cell counts rose from 2.7k to 6.3k per year with anchor-switch share 13 % -> 52 % (E2 s4, repository evidence); any label or eligibility rule tied to "expiry near tenor" changes meaning over time. Short-dated (0DTE-type) activity growth `NEEDS RESEARCH`.
- Snapshot timing: end-of-day option quotes vs underlying close are not simultaneous (L-11); the time basis of the snapshot must be established per provider.
- Calendar: exchange holidays, early closes and time zone/DST; no calendar exists yet (DEC-005 keeps calendar days / 365; L-31). Weekday effects interact with this convention (M-02).
- Rates/dividends: sources and timing for the forward (put-call parity or index forward) must be evidenced per date (M9).
- Event structure: scheduled macro events, expiry/index-roll days, one big stress block (2020) and 2022 in recent history; regime rule must be past-only (M-09).
- Licensing: provider terms are the open blocker (DEC-002; AP-002).

**India-specific issues (all `NEEDS RESEARCH`; recollection, not repository fact; Agent B owns data/terms)**
- Contract style and cycle: index options are, to my recollection, European, cash-settled; **expiry weekday and the number of weekly expiries per index have been changed by regulators/exchanges over time**; lot sizes and contract specifications are revised periodically. Each change is a structural break that alters liquidity and the meaning of "expiry near tenor"; the break dates must be established and treated as period boundaries.
- Sessions and calendar: different trading hours (IST), holiday list (including special sessions), time-zone/day-count details; a calendar-days / 365 convention (OD-5) and weekday features mean something different from the US; the holiday-adjacent structure differs.
- Data content: free end-of-day exchange files may carry traded/settlement prices without **bid/ask** (`NEEDS RESEARCH`). If so, MVD M7 (bid, ask) and the quote-quality policy (spread filters, mid) cannot apply; IV would be built from last/settlement prices with stale-price risk in illiquid strikes, a different price type that must be labelled and may need its own threshold set. OD-4 (raw quotes) may therefore be unattainable from free sources; that is a data finding for Agent B, with the methodological consequence stated here.
- Liquidity profile: activity is typically concentrated at-the-money and in the nearest weekly; wing density and the 60 % observed-node target (M6) may not be met; the k-range and tenor set must be re-piloted rather than copied from SPY.
- History length: usable weekly-expiry history may be shorter than the US one; the owner-adopted M3 (>= 2,000 snapshots) and M4 (>= 600 never-selected origins) may be unattainable, which would cap the study at tier D1 or require re-scope. `NEEDS RESEARCH` for the actual dates.
- Taxes/exercise mechanics, rate and dividend sources (money-market/T-bill proxies; index dividend yield), tick size and price units, minimum-premium filters: all need market-specific values; US thresholds (`min_mid` 0.05 USD) are not transferable.
- Lot size and participation changes alter volume/open-interest filters; use of volume/OI as quality screens needs market-specific thresholds.

**Common to both:** separate calendars and holiday handling; separate day-count and weekday treatment; separate regime rules; separate benchmarks and holdouts; separate wording ceilings; no sentence that supports one market's claim with the other's data.

---

## 7. Observations on prior documents I will not edit (for the orchestrator)

- EVALUATION_PROTOCOL s7 (comparison of dependent forecasts) remains `NEEDS RESEARCH` and is closed by the owner for the synthetic search; this design does not reopen it (CF-8).
- FORECASTING_STRATEGY s3 ladder rungs 2 and 4 are absent in code (M-05); the plan is consistent with this design.
- PHASE0_FEASIBILITY_PLAN s7 freeze: the owner-adopted MVD values are not evidence-based; the plan itself (s1) implies underpowering at 600 origins (section 4.4). The adoption is not wrong, but it must be disclosed whenever it is used.

---

## 8. Routed to others

**To Agent C (engineering; proposals only, code may not be run locally):**
1. Add to `Config` (hashed) every experiment flag: `target`, `val_mode`, `val_frac`, `calendar`, `mr_window`, `pca_factors`; so the hash distinguishes H2/H3/H4 (M-10).
2. Store the per-origin loss series for every model and benchmark in the run record (needed for c, rho and any later inference; M-10, CF-8, 4.5).
3. Implement B0b (maturity-aware persistence), B1 (training mean change, per cell and per days-to-expiry bucket) and B4 (AR on PCA factors); contract-level scoring (4.2) as a scoring path, leaving DEC-006 rules unchanged (M-02, M-05).
4. Cross-tabulated metric tables (maturity x moneyness x regime x block) with `n`/`n_missing`; relative/log-IV error (M-12).
5. Align selection and reporting masks, or report both; do not zero missing/censored labels as "no change" without recording the effect (M-07, M-08).
6. Neural-path leakage sentinel (LT-3), negative control and leak canary (LT-7, LT-8); use `AccessLog` in every run and call `require_baselines` unconditionally for new runs (M-11, GR-MOD-01).
7. A generator extension for S-1/S-2/S-3 (steep short-end term structure, trading-time variance accrual, learnable non-linear signal; `datasets/synthetic.py`).
8. A leave-worst-block-out and per-block skill output in `evaluate_all`.

**To Agent A / documentation (the file owners):** `KNOWN_LIMITATIONS.md` proposed new entries: "H1-H6 test period consumed (M-01)", "no maturity-aware benchmark (M-02)", "no neural positive control (M-06)", "evaluation population selected on target-day quote tightness (M-07)", "decision rule has no minimum effect size (M-03)". PHASE4 s3.7 and README row for H4-H6: replace "pre-registered" by "pre-specified ... on a consumed test period"; PHASE4 s3.9 item 5: soften the causal attribution (M-13).

**To Agent B (data/governance):** (1) whether a free India source carries bid/ask or only traded/settlement prices (MVD M7, OD-4); (2) history start dates and structural-break dates per market (expiry cycle/lot-size changes); (3) per-provider snapshot timestamps and raw-field timing (LT-5); (4) rate and dividend sources per market (M9). I used none of Agent B's content.

**To Agent E (UI):** any displayed H-series result must carry the label "hosted dataset withdrawn; descriptive history; not validated" (already DEC-002/L-29); the viewer must not present a benchmark-dependent result as a single "model beats persistence" headline.

**To the owner (decisions, not pre-empted here):** (a) approve contract-level scoring + maturity-aware benchmark as primary (4.2) or choose the fallback; (b) whether S-5 falls inside the PA-1 closure; (c) r\* and the per-stage thresholds after R-0; (d) whether DEC-005 may be sensitivity-tested (trading-day maturity) as a labelled robustness check; (e) AP-003 gating for R-4; (f) acceptance that, with the owner-adopted 600-origin floor, the default outcome is likely "underpowered in advance" (tier D1). [Superseded 2026-10-21 for (a), (b), S-5 and the effect-size/multiplicity convention by AP-008 / OR-D10; still open: numeric r*, (d) DEC-005 sensitivity, (e) AP-003 gating]

---

## 9. Files changed

- `D:\Claude Code\Neural-Volatility-Surface\orchestration\reports\RESEARCH_DESIGN.md` (this file; created/overwritten, the only file written).

No other file was modified; no Git operation, no code execution, no data access, no training.

---

## 10. Handoff

**S4/S5 (and Agent F) may rely on:**
- The audit findings M-01..M-13 as *statically derived* observations with file/line evidence (unexecuted); the proposed design (4.1-4.6, 5, 6) as a proposal awaiting owner approval; the wording table (4.6) as the proposed ceiling for any claim.
- That the H1-H6 record is history: descriptive, single-run, unlicensed/withdrawn, partly transcribed; it motivates hypotheses, it is not evidence.

**They may not rely on:**
- Any H1-H6 number as validated or reproduced evidence; the decision rule's verdict vocabulary as a statement of skill; the owner-adopted MVD thresholds as evidence-based; my MDE table as measured (c and rho are unknown; heavy tails; formula copied from the Phase 0 plan); the US/India market facts marked `NEEDS RESEARCH`; any claim that tests pass (none were run by me).
- That a real dataset, a Colab runtime, GPU access or training approval exists (all blocked).

**Top methodological issues, in one line each:** (1) the 2016-2023 test period is consumed by nine adaptive experiments, so no H-series verdict is confirmatory (M-01); (2) the fixed-expiry/nearest-expiry sign flip is a benchmark/label problem (calendar roll-down and contract switching), and every positive verdict came with calendar features (M-02); (3) the pass rule has no minimum effect size and no uncertainty, and is weaker than the Phase 0 criterion (M-03); (4) 7 of 66 label evaluations passed with no multiplicity accounting (M-04); (5) the baseline ladder is incomplete and the neural recipe is untuned/near-untrained with no positive control, so a neural null is uninformative (M-05, M-06).

## 11. Owner decision status 2026-10-21 (appended; text above is unchanged)
Sections 4.1 (CF-2, CF-4 T6, CF-7), 4.2 and 4.3 R-1 are no longer only proposals for the three AP-008 points: the owner approved contract-level scoring against B0a and B0b with the predefined nearest-expiry fallback, 600 origins as a disclosed convention with the pilot-measured N* binding, and a prespecified minimum meaningful effect with one primary contrast per stage, a trial ledger and S-5 kept inside the PA-1 closure (not run). Canonical record: decision.md "AP-008"; APPROVALS AP-008; DECISIONS OR-D10. Numeric r* (3 percent is only a PROPOSED value), the R-1 coverage threshold and N* remain unfrozen; nothing in this report is validated.

Update 2026-10-21 (D11a): the open specification items of 4.2 and R-1 (hull, hull coverage, B0a/B0b evaluation locations, scored population, per-origin score, primary reference per CF-2, trial-ledger table T6) have owner-approved specification text in docs/architecture/STORAGE_DESIGN.md section 8.8 (D11a sub-table; decision.md "AP-008 follow-up Q-F, design answers D1-D11"). Where the text above differs, 8.8 governs. Not implemented; numbers deferred (D11b).
