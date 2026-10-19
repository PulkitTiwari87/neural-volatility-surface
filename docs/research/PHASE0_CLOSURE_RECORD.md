# Phase 0 Closure Record

> **SYNTHETIC evidence only. Owner decision recorded 2026-10-13: CLOSED — NO-GO for the current synthetic inference methodology** (accepted by the owner in the session instruction of that date; **not** CLOSED — PASS). Built from existing records on 2026-10-13: **no experiment was run, no evidence file was modified** (recording the decision changed documentation only). This record does **not** declare Phase 0 PASSED: the real-data exit criteria were never tested. It is the single canonical closure summary; derivations stay in [decision.md](../../decision.md) (PA-1…PA-5), [PHASE0_AUDIT](PHASE0_AUDIT.md), [PHASE0_A2D_RESULTS](PHASE0_A2D_RESULTS.md) and [PHASE0_A2B_SCREENING_DIAGNOSTIC](PHASE0_A2B_SCREENING_DIAGNOSTIC.md).

## 1. What is being closed, and what is not

| # | Track | Proposed disposition |
|---|---|---|
| 1 | Synthetic audit of the spike (v1 run, reproduction, A2, A3, A6, A2b-v1 Stage 1, A2d) | **Complete.** Every declared analysis was executed; nothing further is needed to interpret it |
| 2 | Current inference methodology: the `improvement_detected` rule (`lo > 0` of a block-bootstrap or HAC interval) | **CLOSED — NO-GO** (owner-accepted 2026-10-13, §7); method not adopted; not CLOSED — PASS |
| 3 | Boundary-null / calibrated-inference research (A2b-v2, Stage 2, A2c, 300-seed extension, studentized bootstrap) | **Search closed by the owner 2026-10-13.** Not performed and not to be run; no claim of validation |
| 4 | Real-data feasibility (provider, licence, permitted sample, MVD, cost) | **Not established.** Separate open track; Phase 0 gate **not passed** |
| 5 | Future model-development readiness (neural or otherwise) | **Not ready.** Nothing neural was run; blocked by track 4 and DEC-012/DEC-015 |

## 2. Original objectives and exit criteria (sources, not redefined)
- **Objective** ([IMPLEMENTATION_PLAN](../../IMPLEMENTATION_PLAN.md) Phase 0): decide what is studied with which data and show the analytical path is feasible before building pipelines.
- **Exit gate (MP):** written data-source decision, documented scope, sample data sufficient to test the full analytical path, plus A3 (quantified MVD with measured availability) and A4 (pre-registered success criteria). "If A3 fails: stop and re-scope."
- **Criteria sets used below:** acceptance A1–A5; real-data exit evidence items 1–8 ([DATA_SOURCE_ASSESSMENT §10.4](../data/DATA_SOURCE_ASSESSMENT.md)); the v1 synthetic hypotheses H-S1…H-S8 pre-registered before any code existed ([PHASE0_FEASIBILITY_PLAN §9](PHASE0_FEASIBILITY_PLAN.md)). PA-1…PA-5 and A2b/A2c/A2d were added **after** the v1 run (POST HOC) and are listed separately.
- **Status words:** PASS · FAIL · NOT TESTED (evidence does not exist) · NOT APPROVED (proposal exists, owner has not signed).

## 3. Status of each criterion

### 3.1 Acceptance A1–A5 and the gate
| ID | Criterion | Status | Evidence |
|---|---|---|---|
| A1 | Written data-source decision with licence conclusions | **NOT TESTED** | No written provider reply; B1–B4 open; DEC-002 `PROPOSED`; Cboe email drafted, **not sent** ([CBOE_LICENSING_QUESTIONS](../data/CBOE_LICENSING_QUESTIONS.md)) |
| A2 | Documented scope (one market, universe, horizon, data mode) | **NOT APPROVED** | Proposed in the feasibility plan; DEC-001/DEC-003 `PROPOSED` (0 of 15 decided) |
| A3 | Quantified MVD and measured availability | **NOT TESTED** | MVD defined (plan §2); availability unmeasurable without a real sample |
| A4a | Pre-registered *synthetic* success criteria, dated | **PASS** | H-S1…H-S8 recorded 2026-10-12 before code; outcomes in §3.3 are as recorded |
| A4b | Frozen, owner-signed *real-data* thresholds (MVD density, c, ρ, regime rule) | **NOT APPROVED** | `TBD-pilot` values; PA-1…PA-4 unsigned |
| A5 | Sample exercises every stage at least once | **PASS (labelled synthetic only)** | `study_20261100_10.json` SHA-256 `ed748f18…3022`; seven v1 records (§5); `chainpipe` path, 145 tests OK ([IMPLEMENTATION_MATRIX](../engineering/IMPLEMENTATION_MATRIX.md)). Does **not** satisfy items 2–3 below |
| Gate | Exit gate | **NOT MET** | A1, A2, A3, A4b unsatisfied |

### 3.2 Real-data exit evidence (§10.4)
| # | Item | Status |
|---|---|---|
| 1 | Written licence evidence (B1–B4) | **NOT TESTED** |
| 2 | Permitted real sample, ≥ 20 pre-selected dates | **NOT TESTED** (none obtained) |
| 3 | Availability vs MVD | **NOT TESTED** |
| 4 | Cost evidence and spend approval | **NOT TESTED** (no price obtained; no spend authorised) |
| 5 | Frozen, owner-signed thresholds | **NOT APPROVED** |
| 6 | Synthetic feasibility run recorded | **PASS** (synthetic; failures disclosed in §3.3) |
| 7 | DEC-001/002/003 `DECIDED` with ADRs | **NOT APPROVED** |
| 8 | Exposure decision (Q-03) | **NOT APPROVED** |

### 3.3 Pre-registered synthetic hypotheses (v1 outcomes, unchanged)
Source: [PHASE0_SYNTHETIC_RESULTS §7–§8](PHASE0_SYNTHETIC_RESULTS.md). Root causes were design inconsistencies in the pre-registration, not pipeline defects; post-hoc remediations (PA-2, PA-3) are **not approved**, so the v1 failures stand.

| Hypothesis | v1 status | Result as recorded |
|---|---|---|
| H-S1 IV recovery ≤ 1e-8 at observed cells | **FAIL** | main runs pass; study 17 / 19 (2 failures from node-matching tolerance 1e-6 vs cell tolerance 1e-8) |
| H-S2 strict conservation / unalignable = 0 | **FAIL** | fast config fails both worlds; main and study 19 / 19 pass; strict form fails 13 of 390 full-config A3 worlds ([PHASE0_AUDIT §6.2](PHASE0_AUDIT.md)) |
| H-S3 no extrapolation | **PASS** | 19 / 19 |
| H-S4 persistence appropriate in RW | **FAIL** | study 8 / 9 |
| H-S5 predictability detected in AR | **PASS** | study 10 / 10; A3 (post hoc, 200 worlds) 200 / 200 |
| H-S6 analytic persistence MSE ±15 % | **FAIL** | study 18 / 19; ±15 % fails ≈ 4 % of correct runs by construction (PA-2) |
| H-S7 chronology (look-ahead rejected) | **PASS** | unit tests |
| H-S8 reproducibility | **PASS** | unit tests; regenerated v1 records identical ([PHASE0_AUDIT §1](PHASE0_AUDIT.md)) |

### 3.4 Post-hoc audit gates and amendments
| Item | Status | Evidence and limits |
|---|---|---|
| **PA-1 predefined method-selection gate** (A2b-v1, Stage 1, owner-approved) | **FAIL — gate not met; CLOSED — NO-GO (owner-accepted 2026-10-13); no method adopted** | `NO_METHOD_ADMISSIBLE`: 0 of 6 methods admissible; no method met the screening tolerances in all five gating cases (worst gating lower-tail rate 3.95–4.9 % vs ≤ 3.5 %); record valid, not void, `m0_first1000_regression_vs_stored_A2 = true`, `screening_valid = true`, `formal_valid = false`. SHA-256 `69291dd2…88ccc`; `protocol_sha256` `1e8aebe2…bd3fb` |
| A2b Stage 2 (confirmation) | **NOT TESTED** | no admissible method; not run; no lock claimed |
| A2 original M0 interval | **FAIL (post hoc)** | coverage 93.3 / 90.8 / 85.8 / 91.3 % vs 95 %; `lo > 0` rate 3.4–7.1 % vs 2.5 %; SHA-256 `84d3c241…6cd2`. "Detected" is a **screening rule, not a calibrated test** |
| **A2c** pipeline-realistic boundary null | **NOT TESTED** | design only; **no boundary-null or size claim exists** |
| A2b-v2, 300-seed extension, further bootstrap variants | **NOT TESTED** | not proposed for approval, not run |
| **A2d** diagnostic (seeds 40001–42000) | **Diagnostic only; no verdict** | see 3.5 |
| A6 stopped RW worlds | **Executed, exploratory** | 0 / 10 detections (Wilson [0, 27.8 %]); different estimand; never pooled; ledger SHA-256 `2831fae5…9b3a1` |
| **PA-4** invalid-world accounting | **NOT APPROVED** | see 3.6 |
| PA-2 (H-S6 z-criterion) | **NOT APPROVED** | 390 / 390 pass shows no false alarm, not power |
| PA-3 (tolerances) | **NOT APPROVED** (synthetic); **OPEN** for real data (Q-25) | synthetic data cannot test snapping |
| PA-5 synthetic ≠ real validation | **Policy in force** | no owner decision needed |

### 3.5 A2d: original execution versus corrected analysis
- **As executed** (summary SHA-256 `3f023425…`, module as executed `3db886ee…a5ce`): conformed to the frozen design (`design_sha256` `b23ba43c…`) **as coded**, which contained my unit error in the variance ratio (V̂/V_n instead of V̂/(n V_n)). That invalidated the mean-ratio clause of P2, all of P3 and the rescaling counterfactual **as executed**. The raw data (16,000 rows, SHA-256 `9315c5e4…4b92`) are unaffected.
- **Corrected analysis** (new file, SHA-256 `79e185d5…7367`; corrected module `diagnostics/a2d.py` `f0897720…7291`): same raw file, no rerun, **rules and thresholds unchanged**, original summary kept. P2 **not met**, P3 **not met (narrowly)**, the other signatures met. The correction was made after seeing results (design §9) and is disclosed as such.
- **Findings (synthetic AR(1)-type series, n = 240):** the exact-variance oracle interval is near nominal in normal cases; the HAC variance estimate has a downward bias ≈ −(L + 1)/n beyond truncation; its variability matches (4/3)(L + 1)/n; skewness acting through studentization produces a tail asymmetry opposite to the oracle's; kurtosis inflates both tails. If the pipeline's loss differences are left-skewed, HAC lower-tail size would be 5.3–8.0 % in these cases. **Cannot be concluded:** that any real procedure is valid, or anything about the pipeline, real data, other dependence, or bootstrap intervals.

### 3.6 PA-4 reporting rules
| Rule | State |
|---|---|
| R1 attempted / valid / invalid + Wilson | **Implemented and verified** (`ledger`, run 2026-10-13: 200 / 190 / 10, 5.0 % [2.7, 9.0]; `test_ledger_hand_values_for_the_a3_rw_counts`) |
| R3 conditional detections (labelled) | **Implemented and verified:** 3 / 190 = 1.6 % [0.5, 4.5], "conditional on world validity" |
| R4 identification bounds | **Implemented and verified:** [1.5 %, 6.5 %], union interval [0.51 %, 10.8 %] |
| R5 break-even invalid-world detection rate | **Implemented and verified:** 0.20 (for 2.5 %), 0.70 (for 5 %) |
| R6 stopped worlds on a separate line | **Implemented and verified** (`ledger --a6`; `test_ledger_cli_is_read_only_and_never_pools_a6`) |
| R2 rejection reasons | **Partly implemented:** counts and seeds only (A3 does not store the breach day or node; A6 stores stop days) — **unresolved** |
| R7 wording rules | **Convention only**, no automated check — **unapproved** |
| R8 v1 limit and outcome unchanged | **Verified** (v1 archive hashes, §5) |
| Overall PA-4 | **Reporting implementation verified (R1, R3–R6; format and arithmetic only). Semantic approval NOT GIVEN** — separate from, and unaffected by, the PA-1 closure. Unresolved: judge RW by the conditional rate or the worst case; the 300-seed extension (closed, not performed). These tests verify arithmetic and separation, **not** any false-positive claim or interval validity |

## 4. Key findings and their limits
1. The pipeline recovers known truths and detects a known predictable component on **synthetic** data (A3: 200 / 200 AR detections, MSE ratio 0.760 vs analytic 0.75). It says nothing about real surfaces, real quote noise, or any neural model.
2. "Improvement detected" is **not** a calibrated test. No method met the screening tolerances in all five gating cases; A2d separates at least three sources of the size distortion (bias, variability, skew-driven asymmetry), none with a validated remedy.
3. The 1.6 % RW rate is conditional on validity, measured away from the zero-mean boundary (MSE ratio 1.014), and is **not a size**.
4. Every number is synthetic, from one CPython 3.12.6 / Windows configuration.

## 5. Evidence integrity (verified 2026-10-13)
Recorded hashes equal the files on disk: the seven v1 records in `experiments/phase0_synthetic/archive_v1/` (hashes in [PHASE0_AUDIT §6.5](PHASE0_AUDIT.md); e.g. study `ed748f18…3022`), A2 `84d3c241…`, A3 `f33abbee…e937`, A2b record `69291dd2…88ccc`, A2b diagnostic `9d43ca2c…`, A2d raw / summary / corrected / module as executed (§3.5), A6 ledger `2831fae5…9b3a1`. The evidence folders are **git-ignored** (not versioned; owner's call, PHASE0_AUDIT §6.4). **Re-verified when the decision was recorded (2026-10-13):** every hash listed above, plus the A2d corrected module (`f0897720…7291`), matched the file on disk; the `phase0/` code hashes equal the `code_sha256` frozen in the A2b record (11 of 11) and the A2b `protocol_sha256` recomputes to the recorded value; `a2d.design_sha256()` recomputes to `b23ba43c…` (that value hashes the design's cases, seeds, lags and rules, not the Markdown file); the master plan is unmodified in the working tree; the suite runs 145 tests, OK.

## 6. Outstanding risks and deferred work
- **Risk:** the evidence lives only in git-ignored folders; losing them loses the audit trail.
- **Risk:** without real data, the `observed`-cell definition (Q-25), parity-forward (Q-06), AM/PM settlement (DEC-005), quote noise and the 15:45 snapshot structure are untested.
- **Closed by the owner 2026-10-13 (not to be run):** A2b-v2, Stage 2, A2c, the 300-seed extension, studentized-bootstrap research and any further statistical-method experiment. **Still open, not required by this closure:** PA-2/PA-3 sign-off; PA-4 semantic approval; R2 breach-day storage; versioning the evidence folders.
- **Independent of this record:** the real-data access track (Cboe inquiry, Databento terms, permitted ~20-date sample) and spike-scope engineering ([IMPLEMENTATION_MATRIX](../engineering/IMPLEMENTATION_MATRIX.md)).

## 7. Final decision (owner's, recorded 2026-10-13)
**Decision: CLOSED — NO-GO for the current synthetic inference methodology.** The owner accepted the recommendation that this section previously carried, in the session instruction of 2026-10-13. Basis: the owner-approved predefined gate (A2b-v1) was applied once and no method met it; the original interval was shown to be miscalibrated; the A2d diagnostic identified mechanisms but no validated remedy.

**Not claimed:** CLOSED — PASS, or that the Phase 0 exit criteria are satisfied. The exit gate is **NOT MET** (§3.1–§3.2); Phase 0 remains incomplete.

Boundaries of the decision:
1. **Search closed.** No A2b-v2, Stage 2, A2c, 300-seed extension or further statistical-method experiment. None is to be proposed again without a new, explicit owner decision.
2. **Evidence preserved.** The frozen A2b-v1 `NO_METHOD_ADMISSIBLE` record, all A2d raw data, the original A2d summary and the corrected analysis stand unchanged under their original hashes (§5). The A2d post-run analysis correction remains disclosed as made after seeing results (§3.5; design §9).
3. **PA-1** is CLOSED — NO-GO: gate not met, method not adopted. **PA-4**: the reporting implementation (R1, R3–R6) is verified for format and arithmetic (§3.6); its semantic approval is a separate, unresolved item.
4. **Claims.** The `lo > 0` rule (`improvement_detected`) remains only a labelled screening statistic. **Inferential claims, statistical significance, p-value-style statements and any nominal size or coverage claim are unsupported** until a suitable method is independently validated under a new owner-approved protocol ([KNOWN_LIMITATIONS](KNOWN_LIMITATIONS.md) L-22). **Descriptive** model comparisons (paired loss differences by region and period with sample counts) may proceed with explicit limitations.
5. **Separation.** What is closed is the *synthetic inference audit*. Real-data feasibility (provider, licence, permitted sample, cost), scope approval (DEC-001/002/003, Q-03), frozen owner-signed thresholds and real-market validation are **unresolved** and unaffected (§3.1–§3.2).

**Next milestone (owner):** an authorized real-options-data access decision and completion of the independent engineering roadmap ([IMPLEMENTATION_MATRIX](../engineering/IMPLEMENTATION_MATRIX.md)) — not another bootstrap investigation. The statistical research loop is stopped.

| Choice | Meaning | Select |
|---|---|---|
| **CLOSED — NO-GO** (current inference methodology) | The decision above | ☒ (owner, 2026-10-13) |
| **CLOSED — PASS** | Requires every mandatory criterion actually satisfied — **not available on this evidence** | ☐ (unavailable) |
| **OPEN** | Keep PA-1 open and name the mandatory decision still required | ☐ |

Recorded from the owner's chat instruction of 2026-10-13 (no separate signature artefact exists; the assistant did not choose the outcome).
