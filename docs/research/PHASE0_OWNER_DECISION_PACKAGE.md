# Phase 0 Owner Decision Package

> **SYNTHETIC evidence only. Nothing here is approved.** This package prepares owner decisions on PA-1, PA-4, A2b, A2c and the real-data feasibility gap. **Phase 0 is BLOCKED.** *Update 2026-10-13: the PA-1 decisions requested below are superseded by [PHASE0_CLOSURE_RECORD](PHASE0_CLOSURE_RECORD.md), which records the owner's acceptance (2026-10-13) of CLOSED — NO-GO for the current synthetic inference methodology; no further A2b-v2, Stage 2 or A2c approval is being sought.* Canonical derivations stay in [decision.md](../../decision.md) (PA-1…PA-5) and [PHASE0_AUDIT](PHASE0_AUDIT.md); this page summarises, audits traceability, and lists the approvals needed. Prepared 2026-10-13.

## 1. Verified state (read from the repository on 2026-10-13)

| Item | Finding |
|---|---|
| Git | `main`, HEAD `3d520f5`; 19 modified tracked files and 1 untracked file (`notebooks/exploratory/Neural_Volatility_Surface_Colab.ipynb`); nothing committed by the assistant |
| Tests | standard-library suite: **94 tests, OK** (57 original + 37 regression), unchanged execution environment (CPU, stdlib) |
| Evidence | 7 archived v1 hashes match [PHASE0_AUDIT §6.5](PHASE0_AUDIT.md); stored A2 and A3 are identical to independent re-runs; A6 ledger SHA-256 `2831fae5…9b3a1`, 10 run files, prefix checks 10/10; `block_bootstrap_ci` body byte-identical to HEAD |
| Absent instruction files | `humanizer.md` and `agent.md` do not exist; `CLAUDE.md`, `decision.md`, `architecture.md`, `guardrails.md`, ADR-0003 were read |
| ADR-0003 / DEC-012 / DEC-015 | ADR-0003 `Proposed`, spike scope only (stdlib); DEC-012 `PROPOSED`; DEC-015 `OPEN`; neither neural architecture nor toolchain is decided |

**Discrepancies found and what was done**

| # | Discrepancy | Handling |
|---|---|---|
| 1 | The proposed confirmation seed `--seed0 8001` reuses series seeds 8001–9000 of the screening run (7001–9000), so the confirmation was not independent | Runner now refuses any `--seed0` ≠ 7001 whose range overlaps 7001–9000 (test added); proposal changed to `--seed0 20001` (series 20001–25000, bootstrap 120001–125000) in decision.md. **Owner must approve the new value** |
| 2 | A2b records had no explicit attempted / completed / invalid replication counts | Added `replications` per case (a failure aborts the run, so invalid is 0 by construction; stated as a limitation) |
| 3 | PA-4 R1–R5 could not be produced from stored outputs (A3 stores no reasons, no union interval, no break-even; R3 is not labelled conditional) | Added `invalid_world_ledger()` and a read-only `ledger` command that derives R1–R5 from the stored A3 record and shows A6 separately; no stored record was changed |
| 4 | decision.md and the changelog quoted earlier test counts | Updated where they describe the current state; historical statements kept |

## 2. PA-1 — bootstrap / interval protocol proposal (OPEN; for approval)

1. **Estimand and null.** Series level (A2b): θ = E[Yₜ] of a stationary series. The rule "detected" is `lo > 0`, where [lo, hi] is the 95 % two-sided interval for the mean, i.e. a one-sided test of H₀: θ ≤ 0 against H₁: θ > 0 at nominal level 2.5 %. Size is measured at the boundary θ = 0 (largest for a one-sided rule). Pipeline level: θ_pipe = equal-origin-weight mean of dₜ = MSE_persistence − MSE_model, same rule. **A2b does not establish pipeline-level size.**
2. **Methods (identifiers read from `phase0/audit.py`).** `M0_block5`, `M1_block10`, `M2_block20`: unchanged `block_bootstrap_ci`, moving-block percentile bootstrap, B = 1000, tails at `sorted[25]` / `sorted[974]`. `M3_hac_L4`, `M4_hac_L9`, `M5_hac_L19`: mean with Newey–West/Bartlett weights, lag L, divisor n, normal quantile 1.95996, no small-sample factor. Lag L truncates dependence like a block of L + 1, so the design is a 2 × 3 factorial (interval construction × truncation).
3. **Data-generating processes and dependence.** Series length 240 (S2: 120), exactly zero true mean, stationary start. `normal`: unit-variance AR(1) with ρ. `skewed`: z² − 1 with z a unit-variance AR(1) (its own lag-1 autocorrelation is ρ²). Gating: G1 normal 0; G2 normal 0.3; G3 normal −0.2; G4 skewed ρ_z 0.3 (effective 0.09); G5 skewed ρ_z √0.3 (effective 0.30). Stress (reported, not gating): S1 normal 0.6; S2 normal 0.3 with n = 120. Short-memory AR(1) only; no volatility clustering, non-stationarity or long memory.
4. **Metrics and calculation.** *Coverage* = share of replications with lo ≤ 0 ≤ hi. *Size* = share with lo > 0 (upper tail: share with hi < 0). *Efficiency* = mean half-width / empirical SD of the sample mean, and ratio to the first method. *Robustness* = the same metrics across the cases. *Power* is **not** measured in A2b (stage 3, A3b).
5. **Thresholds and rationale.** *Screening* (tolerance bands, not certification): coverage ≥ 93.6 % and size ≤ 3.5 % in every gating case = 95 % − 2 SE and 2.5 % + 2 SE at 1000 replications. *Formal* (certification): one-sided 95 % Wilson bounds, size upper bound ≤ 3.5 % and coverage lower bound ≥ 93.5 %, every gating case. 3.5 % is a convention (≤ 1.4× nominal); it is not derived from project needs and never means "nominal".
6. **Selection rule.** Among screening-admissible methods whose geometric-mean half-width ratio over gating cases is ≤ 1.5× the narrowest admissible, choose the smallest worst-case gating size; ties within 0.35 pp go to the lowest identifier (`M0` < … < `M5`). **Rejected:** "narrowest admissible wins" (width correlates with liberal size). No pipeline detection count enters.
7. **Multiplicity and selection bias.** Six methods are screened on shared series, so the winner's apparent calibration is optimistic; five gating cases × two metrics must all pass. Handled by confirming the single selected method on independent seeds, used once, with no re-selection. Cases share seeds, so errors are correlated across cases; independence-based operating characteristics in decision.md are approximate.
8. **Design.** *Stage 1 screening:* all methods, 2000 replications, seeds 7001–9000. *Stage 2 confirmation:* selected method only, **5000 replications, `--seed0 20001`**, formal gate. Stage 3 (A3b): power check ≥ 95 % in World AR and RW rates under the PA-4 ledger.
9. **Monte Carlo uncertainty.** SE of a 2.5 % rate: 0.35 pp at 2000 replications, 0.22 pp at 5000; SE of 95 % coverage: 0.49 / 0.31 pp. Simulated acceptance (five independent cases, 100,000 draws): the screening gate accepts a perfect method 98 % and a method with true size 3.0 % 59 % of the time at 2000 replications; the formal gate accepts a perfect method 29 % at 2000 but 96 % at 5000 replications and a 3.0 % method 9 %. Screening therefore cannot certify; only confirmation can.
10. **Command specification (future, after approval; not run).** From `scripts/phase0_synthetic/`:
    ```bash
    python -m phase0.audit sensitivity --out ../../scratch/phase0_audit/A2b_screening_seed7001_reps2000.json
    # read selected_by_proposed_rule, m0_first1000_regression_vs_stored_A2 (must be true), screening_valid (must be true)
    python -m phase0.audit sensitivity --out ../../scratch/phase0_audit/A2b_confirmation_seed20001_reps5000.json --seed0 20001 --reps 5000 --methods <selected> --screening ../../scratch/phase0_audit/A2b_screening_seed7001_reps2000.json
    ```
    Screening ≈ 8 min; confirmation ≈ 1 min (HAC) to 10 min (M0). A run with fewer than 2000 replications is labelled a plumbing check and names no selection.
11. **Approvals needed:** the gate type and thresholds (5), the selection rule and its 1.5× cap (6), 2000 / 5000 replications (8), confirmation seed 20001 (discrepancy 1), and permission to run both stages.

## 3. PA-4 — rule-by-rule traceability

Quantities kept separate: **(a)** 3 false improvements among 190 valid RW worlds (conditional on validity; denominator 190); **(b)** 10 invalid of 200 attempted RW worlds, with the worst-case reading (13/200 = 6.5 % if all invalid worlds were detections; a bound, not an estimate); **(c)** A6: 0 detections among 10 worlds stopped at their first implausible-IV day (shorter series, 68–208 origins, a different estimand). (a)–(c) have different denominators and estimands and must not be pooled; 1.6 % is a conditional rate, not the unconditional false-positive rate and not a size.

| Rule | Current implementation | Evidence | Gap | Proposed fix | Verification | Approval |
|---|---|---|---|---|---|---|
| R1 attempted / valid / invalid, invalid rate + Wilson | A3 record holds `n_seeds`, `n_valid`, `n_invalid`, Wilson; `invalid_world_ledger()` / `ledger` derive R1 | A3 JSON; ledger output 200/190/10, 5.0 % [2.7, 9.0] | `attempted` not an explicit stored key | done: derived by ledger | `test_ledger_hand_values_for_the_a3_rw_counts` | no (format) |
| R2 rejection reasons | one catchable reason, `IMPLAUSIBLE_IV`, counted by the ledger; A3 stores only world and seed; v1 stores the message | ledger reason counts; v1 summary | per-world breach day and node not stored (A6 stores stop days; D1 diagnostic is ad hoc) | optional later: store stop day per invalid world via `stopped_world_days` | not yet | yes if the study record schema changes |
| R3 conditional detections + Wilson, labelled | A3 `detections`, `detection_wilson95`; ledger adds the label | ledger: 3/190 = 1.6 % [0.5, 4.5] | label was absent from stored output | done in ledger | same test | no |
| R4 identification bounds + union interval | ledger: [1.5 %, 6.5 %], union [0.51 %, 10.8 %] | ledger output; stored A3 `worst_case_*` | union interval was not stored | done in ledger | same test | no |
| R5 break-even invalid-world detection rate and table | ledger: 0.20 (for 2.5 %), 0.70 (for 5 %); table for f = 0 … 1 | ledger output | absent from outputs | done in ledger | same test; zero-invalid case returns `None` | no |
| R6 stopped worlds on a separate line | A6 ledger separate file; `ledger --a6` prints it under its own key | A6 ledger; `test_ledger_cli_is_read_only_and_never_pools_a6` | none for formatting | none | CLI test: A6 detections never enter RW R3/R4 | no |
| R7 wording rules | documentation convention only; no automated check | manual scan 2026-10-13: no bare "false-positive rate is 1.6 %" outside decision.md / audit / changelog quoting the rule | not machine-enforced | none proposed (a text lint would be disproportionate) | manual scan repeated per release | owner to accept as convention |
| R8 v1 limit and outcome unchanged | `TOL["rw_false_positive_max"] = 2` in `run.py`; v1 records in `archive_v1/` | `run.py` unchanged vs HEAD; archive hashes match | none | none | hash check | no |

Reporting-format tests establish that the ledger arithmetic and separation are correct; they do **not** validate any interval method or the false-positive claim. **PA-4 is not signed off.** Disputed semantics for the owner: judge RW by the conditional rate with the bound as sensitivity (default), or by the bound; whether to authorise the 300-seed extension (about 15 invalid worlds, roughly 10 minutes) to try to certify the break-even rate.

## 4. A2c — pipeline-level boundary null (design only; not implemented, not run)

1. **No exact-equal-loss pair exists.** Fitted factor-AR(1) vs persistence has E[d] < 0 in World RW (MSE ratio 1.014, estimation noise) and E[d] > 0 in World AR; oracle-AR vs persistence in World RW gives d ≡ 0 (degenerate). No generator parameter yields E[d] = 0 with non-degenerate d.
2. **Demeaning is not enough.** Subtracting the sample mean sets the sample mean to zero, not the population mean; the interval then contains 0 almost by construction, so coverage of 0 is uninformative, and it discards the dependence-estimation noise that matters. The null must be a generating **model** with zero mean by construction.
3. **Null and estimand.** H₀c: surrogate series Y⁽ʷ⁾ built from each valid A3 world's own d series, with E[Y] = 0. Estimand: rejection probability of the selected PA-1 rule on Y⁽ʷ⁾, per world and averaged over worlds.
4. **Preserved properties.** Length; marginal distribution of the AR residuals (skew, kurtosis); linear dependence and its between-world estimation spread; scale. *Not preserved:* nonlinear dependence (volatility clustering), non-stationarity inside a world, dependence beyond the fitted order, the link to the forecasters, and the pipeline's own non-zero E[d].
5. **Validating the construction (before size is measured).** (i) surrogate mean is 0 within Monte Carlo error over many replicates; (ii) autocorrelations 1–5 and skewness/kurtosis of surrogates match the source d within pre-set tolerances; (iii) known-answer test: apply the construction to a synthetic series with known ρ and marginal; (iv) the M0 interval on observed d reproduces the stored A3 `ci_lo`/`ci_hi` bit for bit.
6. **Statistic, resampling, rejection.** The selected PA-1 method's interval for the mean of Y; rejection when `lo > 0`.
7. **Type-I error and uncertainty.** size_w over R = 100 replicates per world; world-equal-weight mean; SE from between-world variation (replicates in a world are not independent); report the distribution of size_w; same formal bounds as A2b (size upper ≤ 3.5 %, coverage lower ≥ 93.5 %), separately for RW-derived (190 worlds) and AR-derived (200 worlds) surrogates.
8. **Untestable from synthetic evidence.** Stationarity of d within a world; adequacy of a linear short-memory model; that these worlds' d series represent real-data d; absence of volatility clustering; that estimation error in φ̂ does not bias the surrogate.
9. **Minimal changes.** An additive `origin_d(world_cfg)` in `audit.py` that repeats the first lines of `run_single` (no edit to `run.py`, `evaluate.py`, `synth.py`), a surrogate generator (about 20 lines), a runner and subcommand (about 30 lines), tests; about 7 minutes to regenerate the 390 valid A3 worlds.
10. **Acceptance for admissible evidence.** A2b stage 2 passed; all construction checks in item 5 pass; formal bounds in item 7 pass for both surrogate families; power on AR + observed effect ≥ 95 %; output labelled synthetic; a pass supports only "the interval method holds its size on surrogates with the pipeline's observed marginal and lag-1 dependence".
- **Owner choices before any coding:** surrogate family (AR(1) sieve with residual resampling, proposed; AR(p) by information criterion; stationary bootstrap of the demeaned series, which preserves more short-range nonlinear structure but not long-range dependence); R; whether to include the power alternative; acceptance thresholds.

## 5. A2b safeguards and regression coverage (audited without running the protocol; the frozen A2b-v1 protocol and later fixes are in §9)

| Requirement | Status | Evidence |
|---|---|---|
| Refuse to overwrite existing output | implemented, tested | `test_sensitivity_smoke_structure_and_refusals`; CLI check |
| Refuse to write under `experiments/` | implemented, tested | same test; `_fresh_path` |
| Deterministic configuration and seeds | implemented; **gap in tests, now covered** | `test_sensitivity_is_deterministic_and_records_its_settings` (two runs identical apart from timings) |
| Complete recording of settings and results | implemented; now asserted | same test (config keys, methods, thresholds, counts, `code_sha256`, Python) |
| Attempted / valid / invalid replications | **gap, fixed** (`replications` per case); a failure aborts the run, so no partial or invalid results are written | same test |
| Smoke output separated from evidence | implemented, tested | `plumbing_check_only`, label "PLUMBING CHECK ONLY - NOT EVIDENCE", no selection below 2000 replications; smoke file `A2b_PLUMBING_CHECK_NOT_EVIDENCE_reps20.json` untouched |
| Confirmation seeds independent of screening | **gap, fixed** | `test_confirmation_seeds_may_not_reuse_screening_or_a2_seeds` |
| Compatible with the audit-reporting contract | implemented (label, analysis, `code_sha256`, Python, seconds) | same determinism test |
| M0 reproduces stored A2 (first 1000 replications) | implemented; checked at protocol settings only; small-scale equality tested | `test_m0_inside_sensitivity_is_the_unchanged_a2_bootstrap` |
| Existing bootstrap unchanged | verified | body hash equal to HEAD |

Not run: A2b at protocol settings, A2c, the 300-seed extension.

## 6. Real-market feasibility — evidence still missing (research plan only)

Grades follow [DATA_SOURCE_ASSESSMENT §1.1](../data/DATA_SOURCE_ASSESSMENT.md): G1 text read; G2 provider page via summary tool; G3 third-party; U unknown. Nothing below was downloaded, bought or requested; no real-market claim is made.

| Item | What is known | Missing evidence |
|---|---|---|
| Provider and licence | Lead: SPX/SPXW × Cboe DataShop EOD quotes; internal-research use permitted by the Subscriber Agreement text actually read (G1); public display/publication unresolved (B1); fallback Databento OPRA (terms unread, B3) | Written Cboe reply (draft questions **not sent**); Databento terms; professional status (B4); intended audience (B5) |
| Historical coverage | Cboe EOD history stated from 2012 (G2/G3); regimes by assessor knowledge (U) | Provider listing or sample showing actual dates, gaps, SPX/SPXW presence, stressed periods |
| Bid/ask quality, stale/crossed quotes | Cboe: fixed 15:45 ET snapshot, no per-quote timestamp (G1/G2) | Measured crossed/zero/wide-quote rates and exclusion counts on a permitted sample |
| Expiry, strike, underlying, timestamp, rate | Fields expected at snapshots; SPX European, AM/PM settlement mix (G3); rate source Treasury/FRED terms unread (B6) | Field-level confirmation on a sample; forward-from-parity feasibility (Q-06/Q-26) |
| Corporate actions, underlying alignment | SPX is an index (no splits); dividends handled through put–call parity forwards (design); SPY would add American-exercise and dividend issues (U) | Timestamp alignment audit between option quotes and index level |
| Survivorship / selection | Availability of quotes may correlate with volatility (finding F7) | Quote-presence rates by regime on real data |
| Cost and access | Cboe price not published on pages read (U); Cboe Global Indices licence ≥ $1,000/month stated (G2); Databento per-GB, rate not retrieved (G2) | Written price; account-level estimate for a minimal pilot; owner spend approval |
| Reproducibility | Cboe files with no corrections provided (G1) | Hash and version the permitted sample; keep it out of Git |
| Minimum sample for the methodology | MVD proposed: ≥ 2000 daily snapshots, ≥ 95 % of trading days, ≥ 2 volatility regimes (PROPOSED, unfrozen); pilot ≥ 20 pre-selected dates | Pilot-measured *c* and ρ; frozen thresholds and a power table |

## 7. Owner decisions required

| # | Decision | Choices | Recommended default |
|---|---|---|---|
| 1 | PA-1 gate type and thresholds | (a) screening 93.6 % / 3.5 % then formal confirmation (proposed); (b) formal only; (c) stricter, e.g. size ≤ 3.0 % (needs ≥ 5000 replications at screening) | (a) |
| 2 | PA-1 selection rule | calibration-first with 1.5× cap (proposed) / fixed method M0 / other | calibration-first |
| 3 | Replications | 2000 screening + 5000 confirmation (proposed) / larger | proposed |
| 4 | Confirmation seed | 20001 (proposed; 8001 is refused) / other disjoint value | 20001 |
| 5 | Permission to run A2b stages 1 and 2 | yes / no | yes after items 1–4 |
| 6 | PA-4 semantics | judge RW by conditional rate with bound as sensitivity (proposed) / by the bound | proposed |
| 7 | PA-4 reporting rules R1–R8 | adopt / amend | adopt |
| 8 | 300-seed extension | authorise / not now | not now |
| 9 | A2c null family, R, power alternative, thresholds | see §4 | AR(1) sieve, R = 100, include power, same thresholds |
| 10 | Permission to implement A2c | yes after stage 2 passes / no | after stage 2 |
| 11 | Real-data path | send Cboe questions / read Databento terms / neither yet | owner decision (no contact made) |
| 12 | Local CUDA install (for local neural runs only) | approve / keep Colab only | keep Colab only until a neural model is approved |

## 8. Phase 0 gate

**BLOCKED.** Remaining: PA-1 and PA-4 unsigned; A2b not run at protocol settings; A2c not implemented or run; real-data evidence (licence, sample, availability, cost, frozen thresholds, ADRs for DEC-001/002/003, exposure decision) absent. See [PHASE0_AUDIT §6](PHASE0_AUDIT.md) and [NEXT_STEPS](NEXT_STEPS.md).

## 9. Frozen A2b-v1 protocol for approval (pre-run review, 2026-10-13; nothing executed)

**Identity.** Schema `A2b-v1`. `protocol_sha256 = 1e8aebe20823597e2295165ce6b56b153f36794e84c5c78e3d8681b1324bd3fb`, computed by `phase0.audit.protocol_sha256()` from the methods, cases, thresholds, width cap, tie band, seeds, replication counts and reserved ranges. Every record carries it; a confirmation run rejects a screening record whose protocol hash or `phase0/*.py` hashes differ from the current code. Re-check: `python -c "import phase0.audit as a; print(a.protocol_sha256())"` from `scripts/phase0_synthetic/`.

> **Outcome (2026-10-13):** Stage 1 was approved and executed; result `NO_METHOD_ADMISSIBLE`, valid and not void; see [PHASE0_A2B_SCREENING_DIAGNOSTIC](PHASE0_A2B_SCREENING_DIAGNOSTIC.md). Stage 2 is not possible under this protocol (nothing was selected) and was not run.

### 9.1 The five pre-run checks

| # | Check | Result |
|---|---|---|
| 1 | Confirmation seeds do not overlap screening | **Verified.** Screening: series 7001–9000, bootstrap 107001–109000 (A2: 7001–8000 and 107001–108000, inside these). Confirmation `--seed0 20001`: series 20001–25000, bootstrap 120001–125000. All pairs disjoint (`test_frozen_confirmation_seeds_are_disjoint_from_screening_and_a2`). Two enforcement gaps were found and **fixed**: the guard checked only series seeds, and an exploratory run could still read the confirmation range. Now (a) any `--seed0` ≠ 7001 overlapping the screening series or bootstrap ranges is refused, and (b) any non-confirmation run touching 20001–25000 or 120001–125000 is refused (`test_no_other_run_may_touch_the_single_use_confirmation_seeds`) |
| 2 | Selection rule deterministic and fully specified; failure behaviour | **Verified and tightened.** Rule below (9.2). Gaps found and fixed: a float comparison `best + 0.0035` could flip an exact 7-count tie (now `+ 1e-12`, inclusive); the M0-vs-A2 regression only recorded a mismatch (now it **voids** the screening); selection was also computed inside confirmation runs (now never). Tests: tie and cap boundaries, dict-order independence, no-admissible case |
| 3 | Screening thresholds labelled as tolerances, separate from formal criteria | **Verified and tightened.** `config.threshold_semantics` states the screening bands are "NOT a certification" and the formal bounds are "the only certification criterion; stage 2 only". Verdicts are stage-specific: `screening_admissible` is `null` in confirmation and `formal_pass` is `null` outside confirmation, so one cannot be read as the other. The record's `analysis` string names the stage |
| 4 | Confirmation uses fresh seeds and cannot silently replace the method | **Gaps found and fixed.** Confirmation must be exactly one method, 5000 replications, `B = 1000`, `--seed0 20001`, and must pass `--screening <record>`. That record must be schema `A2b-v1`, stage `screening`, protocol-conformant, not void, with the same `protocol_sha256` and code hashes, and its `selected_by_proposed_rule` must equal the requested method; otherwise the run is refused with "a replacement method cannot be chosen at confirmation". The confirmation never computes a selection (`selected_by_proposed_rule = null`, `outcome.replacement_selection = "not performed … forbidden"`). Seeds are single-use: an exclusive lock file `<screening record>.confirmation_used` is created before computing (`test_confirmation_is_single_method_linked_to_its_screening_record_and_single_use`) |
| 5 | Output schema, replication counts, PA-4 consistency | **Verified.** Schema in 9.4. Each case records `replications.attempted / completed / invalid`; a series is always valid, a failure aborts the run and writes nothing, so completed = attempted and invalid = 0 by construction. The PA-4 ledger (R1–R5) concerns world studies (A3, A6) and is unaffected: A2b has no invalid worlds and never feeds the ledger; A6 and the 3/190 result are not used by A2b |

### 9.2 Selection rule (exact)
1. *Admissible* = methods passing the **screening tolerances** in every gating case (G1–G5): coverage ≥ 0.936 and size (`lo > 0` rate) ≤ 0.035. None admissible → outcome `NO_METHOD_ADMISSIBLE`, no selection, no confirmation, M0 stays a "screening rule", PA-1 stays OPEN.
2. *Candidates* = admissible methods whose geometric-mean half-width ratio over the gating cases (relative to `M0_block5`) is ≤ 1.5 × the smallest such ratio among admissible methods (inclusive).
3. *best* = the smallest worst-case gating size among candidates; *tied* = candidates with worst-case size ≤ best + 0.0035 + 1e-12 (7 counts at 2000 replications, inclusive).
4. *Selected* = the tied method that comes first in the order `M0_block5, M1_block10, M2_block20, M3_hac_L4, M4_hac_L9, M5_hac_L19`.
The record stores `selection_trace` (admissible, narrowest geo, candidates, best, tied, selected). No pipeline detection count enters. Deterministic on one machine and Python version; floating-point ties across platforms are only protected to 1e-12.

### 9.3 Failure behaviour
| Situation | Behaviour |
|---|---|
| Exception during any run | no output file is written; in confirmation the lock stays and the seeds count as claimed (removing it needs owner approval) |
| M0 does not reproduce the stored A2 coverages in the first 1000 replications (G1, G2, S1, G4) | screening `VOID`: `void_reason` set, `screening_valid = false`, no selection, not confirmable |
| No admissible method | `NO_METHOD_ADMISSIBLE` (see 9.2) |
| Confirmation formal gate fails | `outcome.formal_pass = false` with per-case bounds; PA-1 stays OPEN; **no replacement method on these seeds**; any new candidate needs a new proposal, new approval and a **new fresh seed range** |
| Confirmation formal gate passes | the owner may propose closing PA-1; stage 3 (A3b) and the rest of the approval list still apply; not automatic |
| Existing output path, path under `experiments/`, reused or reserved seeds, wrong method, different code or protocol hash, second claim of the confirmation seeds | refused before computing |

### 9.4 Output schema (`A2b-v1`)
Top level: `label`, `schema`, `protocol_sha256`, `stage` (`plumbing` / `exploratory` / `screening` / `confirmation`), `protocol_conformant`, `analysis`, `plumbing_check_only`, `screening_valid`, `formal_valid`, `void_reason`, `config` (reps, B, seed0, methods, cases, `series_seeds`, `bootstrap_seeds`, `screen`, `formal_one_sided_95`, `threshold_semantics`, `width_cap`, `tie`, `tie_eps`), `null`, `m0_first1000_regression_vs_stored_A2`, `verdict` (per method), `selected_by_proposed_rule`, `selection_trace`, `outcome`, `confirmation_link` (screening file, its SHA-256, lock file), `cases` (per case: `replications`, `sd_of_sample_mean`, per-method coverage/size counts and rates, half-width metrics, timings), `code_sha256`, `python`, `seconds`. Only `screening` and `confirmation` stages are protocol-conformant; anything else is labelled plumbing or exploratory and carries no selection or formal verdict.

### 9.5 Exact commands (from `scripts/phase0_synthetic/`; not run)
```bash
# Stage 1 - screening: all six methods, seed0 7001, 2000 replications, B 1000; about 8 min
python -m phase0.audit sensitivity --out ../../scratch/phase0_audit/A2b_screening_seed7001_reps2000.json
# Required before stage 2: stage == "screening", protocol_conformant == true, void_reason == null,
# m0_first1000_regression_vs_stored_A2 == true, protocol_sha256 == the value above, selected_by_proposed_rule != null

# Stage 2 - confirmation of exactly that method; fresh seeds 20001-25000; 5000 replications; about 1 min (HAC) to 10 min (M0)
python -m phase0.audit sensitivity --out ../../scratch/phase0_audit/A2b_confirmation_seed20001_reps5000.json \
  --seed0 20001 --reps 5000 --methods <selected_by_proposed_rule> \
  --screening ../../scratch/phase0_audit/A2b_screening_seed7001_reps2000.json
```
Outputs: the two JSON records, plus `A2b_screening_seed7001_reps2000.json.confirmation_used` (the single-use lock) after stage 2 starts.

### 9.6 Limitations that remain (honest)
- The lock is an honour-system guard: someone with file access can delete it or copy the screening record. It prevents accidents, not tampering.
- Screening shares series seeds 7001–8000 with A2, so screening is not independent of A2 by design (that overlap is the regression check); only confirmation is independent.
- Runs on seeds outside the reserved ranges are allowed as plumbing or exploratory checks; they cannot be prevented from informing choices informally, only from being labelled evidence.
- The code hash covers `phase0/*.py`, not the standard library or Python build.
- Thresholds (93.6 % / 3.5 % screening tolerance; 93.5 % / 3.5 % formal bounds), the 1.5× cap, the 0.35 pp tie band and the replication counts are conventions awaiting approval; the formal gate certifies "size ≤ 3.5 %, coverage ≥ 93.5 %" on these AR(1) and skewed series only, not nominal size, not ρ ≥ 0.6, not the pipeline.

### 9.7 Unresolved choices and owner decisions required before execution
1. Approve the screening tolerances 0.936 / 0.035 (or choose stricter, with more replications).
2. Approve the formal confirmation criteria 0.935 (coverage LCB) / 0.035 (size UCB) at one-sided 95 %.
3. Approve the selection rule in 9.2, including the 1.5× cap and the 0.35 pp tie band.
4. Approve 2000 / 5000 replications and confirmation seed 20001 (disjoint from every earlier range).
5. Accept "VOID on M0 regression mismatch" and "no re-selection on confirmation seeds; a failed confirmation needs a new proposal and new seeds".
6. Accept the single-use lock as sufficient, or require a stronger procedure.
7. Permit exploratory runs outside the reserved ranges (default: yes, labelled non-evidence).
8. Authorise executing stage 1, and separately stage 2 after reading the screening record (default: separate approvals).
9. Say who runs it (the assistant under instruction, or the owner).
Not requested here: A2c, the 300-seed extension, local CUDA, PA-4 sign-off. **Phase 0 remains BLOCKED.**
