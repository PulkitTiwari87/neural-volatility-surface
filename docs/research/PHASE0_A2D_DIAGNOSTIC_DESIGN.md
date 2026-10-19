# Phase 0 A2d — Frozen Diagnostic Design

> **SYNTHETIC. DIAGNOSTIC ONLY.** A2d selects no method, applies no threshold, issues no formal or screening verdict, and is not evidence for any inference procedure. Authorised by the owner on 2026-10-13 for A2d **only**; A2b-v2, Stage 2, A2c, the 300-seed extension and neural work are **not** authorised. This design was frozen **before any A2d result was generated**. PA-1 OPEN; Phase 0 BLOCKED. Context: [PHASE0_A2B_SCREENING_DIAGNOSTIC](PHASE0_A2B_SCREENING_DIAGNOSTIC.md) §5 and §8 (Step A), [decision.md](../../decision.md) PA-1.

## 1. Identity and preserved evidence
| Item | Value |
|---|---|
| Schema | `A2d-v1`, code `scripts/phase0_synthetic/diagnostics/a2d.py` (outside `phase0/`, so the frozen A2b code hashes are unchanged), tests `tests/test_a2d.py` (16 tests, passing) |
| `design_sha256` | `b23ba43cd68356e978831c0c112cc902e57b323710bdfe9a07003461e0bc9f55` (from `a2d.design_sha256()`: cases, seeds, lags, rules, reserved ranges) |
| Frozen A2b protocol (reference) | `protocol_sha256` `1e8aebe20823597e2295165ce6b56b153f36794e84c5c78e3d8681b1324bd3fb`; `phase0/*.py` hashes equal those in the screening record (verified 2026-10-13) |
| Preserved, must stay byte-identical | screening record `scratch/phase0_audit/A2b_screening_seed7001_reps2000.json` SHA-256 `69291dd27fcde2ee1ca7131de2d8d4a238c8f1bf6340b14fd2c9226110188ccc`; screening diagnostic `A2b_screening_diagnostic.json` SHA-256 `9d43ca2c5dd90e4c53336461cf33ae4e8760c4dbf02c3ddd1da4343d1ce08e82`; the 7 v1 archive records; stored A2/A3; the A6 ledger (`2831fae5…`) |
| Existing tests | full suite 110 tests passing (57 original + 37 audit regression + 16 A2d) before the run |

## 2. Seed streams (all disjoint; verified in code and recorded in the output)
Replication *i* (0 ≤ i < 2000) of every case: series seed = 40001 + *i*, series = `random.Random(seed)`. **No bootstrap draws are made**; the bootstrap seed stream 140001–142000 (= series seed + 100000, the A2b convention) is reserved and unused.
| Stream | Seeds | A2d overlap |
|---|---|---|
| A2 series / bootstrap | 7001–8000 / 107001–108000 | none |
| A2b screening series (also the plumbing runs) / bootstrap | 7001–9000 / 107001–109000 | none |
| A2b confirmation (reserved, **unclaimed**) series / bootstrap | 20001–25000 / 120001–125000 | none |
| A3 worlds and their bootstrap (+1) | 20262000–20262200 | none |
| v1 single runs / v1 study | 20261012–20261014 / 20261100–20261110 | none |
| Unit-test series seeds | 50001–50003 | none |
| **A2d series / A2d bootstrap (reserved, unused)** | **40001–42000 / 140001–142000** | — |
After the run both A2d ranges are **consumed**: no later protocol may reuse them for confirmation. The A2b confirmation range 20001–25000 is **not touched** (A2d refuses to run on it).

## 3. Cases (n = 240, 2000 replications each; stationary start; true mean exactly 0)
| Id | Series | ρ_z | Lag-1 | exact sd of the mean | captured fraction of long-run variance, L = 4 / 9 / 19 |
|---|---|---|---|---|---|
| G1 | normal AR(1) | 0 | 0 | 0.06455 | 1 / 1 / 1 |
| G2 | normal AR(1) | 0.3 | 0.30 | 0.08785 | 0.868 / 0.934 / 0.967 |
| G3 | normal AR(1) | −0.2 | −0.20 | 0.05275 | 1.083 / 1.042 / 1.021 |
| S1 | normal AR(1) | 0.6 | 0.60 | 0.12859 | 0.654 / 0.814 / 0.906 |
| G4 | skewed z² − 1 (z AR(1)) | 0.3 | 0.09 | 0.09987 | 0.964 / 0.982 / 0.991 |
| G5 | skewed z² − 1 | √0.3 = 0.54772 | 0.30 | 0.12423 | 0.868 / 0.934 / 0.967 |
| C4 | **symmetric heavy-tail control** sinh(a z), matched to G4 | 0.09809 | 0.09 | 0.09066 | 0.963 / 0.982 / 0.991 |
| C5 | symmetric heavy-tail control, matched to G5 | 0.32421 | 0.30 | 0.11354 | 0.862 / 0.931 / 0.965 |
- **Mirror skew** (G4m, G5m) is not a separate simulation: it is the series negated (Y → −Y). Both procedures are exactly equivariant ((lo, hi) → (−hi, −lo)), so mirror tails equal the original opposite tails **by identity** (checked by P6). It translates the stored results to a left-skewed series; it is not independent evidence.
- **Control construction.** Y = sinh(a z), z a Gaussian AR(1) with unit variance and coefficient ρ_z; a = 0.8534157642 is solved so the marginal kurtosis equals 15 (excess 12, that of z² − 1: u = exp(2a²) = 4.2915; kurtosis = (u⁴ − 4u + 3)/(2(u − 1)²)). Y is symmetric (skewness 0). Its autocovariance is exactly γ_k = e^{a²} sinh(a² ρ_z^k), so the lag-1 autocorrelation is sinh(a²ρ_z)/sinh(a²); ρ_z is chosen so it equals G4's 0.09 and G5's 0.30. It matches the 4th moment and the lag-1 autocorrelation; **not** the 6th and higher moments or the tail shape beyond kurtosis.
- **Exact moments.** Normal: γ_k = ρ^k. Skewed: γ_k = 2ρ^{2k}. Control: as above. Exact variance of the sample mean V_n = (1/n)[γ_0 + 2Σ_{k=1}^{n−1}(1 − k/n)γ_k] (computed, and cross-checked against simulation and the AR(1) closed form in tests).

## 4. Exact implementations
- **Raw per replication:** the sample mean and the half-widths of the Bartlett HAC interval for L = 4, 9, 19, taken from the **unchanged** `phase0.audit.hac_ci` (half = z·√(V̂/n), z = 1.959963984540054, divisor n, no small-sample factor). Stored: `mean, half_L4, half_L9, half_L19`.
- **Studentized statistic:** t_L = z·mean/half_L = mean/√(V̂_L/n), with V̂_L = n(half_L/z)² (reconstruction verified against an independent Bartlett computation to 1e-12). Lower tail ⇔ t > z (⇔ lo > 0, "detected"); upper tail ⇔ t < −z (⇔ hi < 0); coverage otherwise.
- **Oracle-variance interval:** mean ± z·√V_n with the exact V_n of the simulated process; t_oracle = mean/√V_n. It uses information no real procedure has.
- **Variance-estimator diagnostics:** r_L = V̂_L/V_n: its mean (bias), CV² = Var(r)/mean(r)², effective df ν = 2/CV², and corr(mean, r_L). Iid-case asymptotic prediction CV² ≈ (4/3)(L + 1)/n = 0.0278 / 0.0556 / 0.1111.
- **Variability-only counterfactual (diagnostic, not a procedure):** V̂_L rescaled by 1/mean(r_L) so its mean ratio is 1, then the same tail/coverage rates. It uses V_n and separates bias from variability.
- **Metrics per case and interval (HAC L4, L9, L19, oracle):** lower-tail, upper-tail and coverage counts and rates with Wilson 95 % intervals; z_asym = (hi − lo)/√(hi + lo); mean, SD and skewness of t; t quantiles at 2.5, 5, 50, 95, 97.5 % with distribution-free order-statistic 95 % intervals; paired HAC-vs-oracle discordant counts and z for each tail; mirror values for G4, G5.
- **Replication accounting:** attempted, completed, invalid per case. A replication is invalid when any value is non-finite or a half-width ≤ 0; invalid replications are excluded from every statistic and reported.
- **Not computed:** any bootstrap interval, any selection, any `formal_pass` or `screening_admissible` field (a test asserts these strings are absent from the output).

## 5. Pre-registered expectations (frozen; descriptive support flags only, not gate verdicts)
| Id | Hypothesis | Rule (as coded) | Falsified or unresolved if |
|---|---|---|---|
| P1 | generator and exact variance are correct | oracle in G1, G2, G3, S1: coverage within 3 SE of 0.95 and each tail within 3 SE of 0.025 | any normal-case oracle misses: **interpretation of every other signature is void**; report as a design failure |
| P2 (H1) | HAC under-coverage in G1/G3 grows with lag because the variance estimator is noisier | miss(L4) < miss(L9) < miss(L19) in G1 and G3; in G1 CV² within ±25 % of 0.0278/0.0556/0.1111 and mean r within ±0.03 of 1 | ordering fails or CV² is far from the formula: H1's arithmetic is not supported |
| P3 (H3) | in G2 and S1 the variance estimator is biased low by truncation | captured_fraction − 0.08 ≤ mean r_L ≤ captured_fraction + 0.02 for every L | the bias is larger (additional finite-n bias) or absent |
| P4a | the oracle interval's skew effect has the **opposite sign** to HAC's | oracle in G4, G5: lower-tail rate > upper-tail rate and z_asym ≤ −2 (Edgeworth orientation for iid right skew: oracle ≈ 3.0 % lower / 2.0 % upper; studentized ≈ 1.0 % lower / 4.0 % upper) | oracle asymmetry same sign or absent |
| P4b | HAC asymmetry replicates the screening on fresh seeds | HAC L4, L9 in G4, G5: upper > lower and z_asym ≥ 3 | not replicated |
| P4c | the asymmetry is skewness, not kurtosis | C4, C5: \|z_asym\| < 3 for oracle, HAC L4, HAC L9 | asymmetry appears in the symmetric control: not skewness alone |
| P4d | mechanism: large means come with large variance estimates under skew | corr(mean, r_4) > 0.10 in G4, G5 and \|corr\| < 0.10 in C4, C5, G1 | no such correlation |
| P5 | heavy tails inflate variance-estimator variability | CV²(r_4)[C4] / CV²(r_4)[G1] > 1.5 | ratio ≤ 1.5 |
| P6 | mirror identity | lower-tail(mirror) = upper-tail(original), exactly | (code error) |
Attribution of the screening's G4/G5 asymmetry to skewness requires P4b **and** P4c; the studentization mechanism requires P4a **and** P4d.

## 6. What each comparison can and cannot identify
- **Oracle vs HAC (same series, paired).** Identifies the contribution of *estimating* the variance (bias + variability + dependence between the mean and V̂) versus the shape of the mean's own distribution. **Cannot** show that any real procedure is valid: the oracle uses the true variance of a simulated process, is available only here, and exact coverage for normal cases is a property of the generator, not of an inference method. An oracle result is never evidence for an interval used on data.
- **Skewed vs symmetric heavy-tailed control.** Separates skewness from kurtosis *to the extent the control matches*: only kurtosis and lag-1 are matched. Cannot isolate skewness from other third-order or tail-shape differences, and says nothing about other heavy-tailed shapes.
- **Mirror skew.** An identity; it only restates tails for the opposite orientation.
- **Across lags.** Truncation bias and estimator variability both change with L; they are separated only through the bias (mean r) versus CV² decomposition and the rescaling counterfactual, which uses the oracle V_n.
- **Not identified:** behaviour of block-bootstrap or studentized-bootstrap intervals (not run); non-AR dependence, volatility clustering, non-stationarity, n ≠ 240; the pipeline's own loss differences; anything about real data. Monte Carlo error: SE of a 2.5 % rate 0.349 pp and of coverage 0.487 pp at 2000 replications; cases share series seeds (not independent), lags and the oracle are paired within a case.

## 7. Outputs, schema, refusals, failure behaviour
- **Command (from `scripts/phase0_synthetic/`):** `python -m diagnostics.a2d --out-prefix ../../scratch/phase0_audit/A2d_seed40001_reps2000`
- **Files (new; the run refuses existing paths and anything under `experiments/`):** `A2d_seed40001_reps2000_raw.csv` (columns `case, rep, series_seed, mean, half_L4, half_L9, half_L19`; 16,000 rows; floats written with `repr`) and `A2d_seed40001_reps2000_summary.json` (`schema, label, analysis, stage, selection_performed = false, formal_verdicts_issued = false, design_sha256, a2b_protocol_sha256_reference, code_sha256_phase0, a2d_module_sha256, python, config` (seed mapping, definitions, case parameters), `seed_check`, `raw_file` (SHA-256), `cases` (metrics above), `signatures`, `limitations`, `seconds`).
- **Independent check:** `a2d.analyze_raw(<raw csv>, 2000)` recomputes every case summary from the raw file alone (tested).
- **Failure behaviour:** an exception writes no summary; an invalid replication is counted and excluded; a non-frozen configuration (other seed or replication count) is a plumbing check labelled "NOT EVIDENCE" and may not touch the A2d, A2b or reserved streams; failing P1 voids the interpretation of the rest.
- **Cost:** about 0.7 ms per replication → under 15 s for the full run.

## 8. Pre-run checklist (all satisfied before execution)
Design documented and hashed ✔ · seed streams disjoint from every used and reserved stream (20 checks, in code and tests) ✔ · A2b screening record and diagnostic preserved (hashes above) ✔ · `phase0/*.py` and protocol hashes equal the frozen A2b record ✔ · output paths and schema defined, overwrite refused ✔ · existing regression suite plus 16 new tests pass ✔ · no thresholds, selection or verdicts in the output schema ✔.

**Not authorised:** A2b-v2, Stage 2, A2c, the 300-seed extension, neural work, any change to canonical evidence.

## 9. Post-run amendment (2026-10-13; appended after execution; the frozen text above is unchanged)
**What was executed.** The frozen run completed (8 cases × 2000 replications, 0 invalid, 24.4 s) with module hash `3db886ee…` (a copy is kept at `scratch/phase0_audit/A2d_module_as_executed.py`), design hash `b23ba43c…`, summary SHA-256 `3f02342580a2b3aedc9bb240d69d6a51f85361b85e7a35226da918a792d48b49`, raw SHA-256 `9315c5e4ee57833594df69f1f7bf11f35943b3e4c4c705205ac30bfea3fb4b92`.
**Defect found after the run (my error, in the frozen definition and code).** Section 4 defines the variance ratio as r_L = V̂_L / V_n with V̂_L = n(half_L/z)². V_n is the variance of the sample **mean**; V̂_L estimates the **series-scale** long-run variance. The correct ratio is V̂_L / (n V_n). The executed mean ratios were therefore too large by exactly n = 240 (they printed about 235 instead of about 0.98), which was noticed on reading the results. The unit tests had checked the V̂ reconstruction but not the ratio scale.
**Consequences.** *Invalid as executed:* `variance_estimator.*.mean_ratio_Vhat_over_Vn`, the whole `counterfactual_rescaled_variance` block, the mean-ratio clause of P2 and the whole of P3 (flags `false` for the wrong reason). *Unaffected* (scale-free or independent of r): all rates, t statistics and quantiles, CV², effective df, corr(mean, r), paired contrasts, mirror quantities, and signatures P1, P4, P5, P6 (P1 passing also confirms V_n itself is correct).
**Correction (analysis only).** The raw file was not regenerated or altered. `a2d.reanalyze` verifies the raw hash against the original summary, applies the corrected ratio, and writes a **new** file `A2d_seed40001_reps2000_corrected_analysis.json` (corrected module `f0897720…`); the original summary stays as executed. No rule or threshold was changed: the pre-registered windows (mean ratio within ±0.03 of 1 in G1; captured_fraction −0.08 … +0.02 in G2/S1) are applied to the corrected quantity. A regression test now fixes the ratio scale. Both sets of flags are reported in [PHASE0_A2D_RESULTS](PHASE0_A2D_RESULTS.md).
**Conformance statement.** The run conformed to the frozen design as coded and as documented, including the defective ratio definition; it did **not** conform to the intended design for P2/P3, which the corrected analysis restores without new data. The A2d seed ranges 40001–42000 and 140001–142000 are consumed.
