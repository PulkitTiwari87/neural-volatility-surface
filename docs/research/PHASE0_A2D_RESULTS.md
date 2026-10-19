# Phase 0 A2d — Diagnostic Results

> **SYNTHETIC. DIAGNOSTIC ONLY.** No method was selected, no threshold or formal verdict was applied, and nothing here is evidence that any inference procedure is valid. The oracle-variance interval is a simulation device, not a procedure. A2b-v2, Stage 2, A2c, the 300-seed extension and neural work were **not** run. PA-1 was OPEN at the time of the run — **superseded 2026-10-13: PA-1 CLOSED — NO-GO by owner decision ([PHASE0_CLOSURE_RECORD](PHASE0_CLOSURE_RECORD.md) §7); the content of this report is unchanged**; Phase 0 BLOCKED. Frozen design: [PHASE0_A2D_DIAGNOSTIC_DESIGN](PHASE0_A2D_DIAGNOSTIC_DESIGN.md) (read its §9 amendment first). Context: [PHASE0_A2B_SCREENING_DIAGNOSTIC](PHASE0_A2B_SCREENING_DIAGNOSTIC.md).

## 1. Execution, conformance and integrity
| Item | Result |
|---|---|
| Completed | yes: 8 cases × 2000 replications attempted, **2000 completed, 0 invalid** in every case; 24.4 s; Python 3.12.6 |
| Seeds | series 40001–42000 (replication *i* → seed 40001 + *i*); bootstrap range 140001–142000 reserved and unused (no bootstrap draws); 20 disjointness checks recorded; the A2b confirmation range 20001–25000 untouched |
| Design / hashes | `design_sha256` `b23ba43c…` as frozen; `phase0/*.py` hashes equal the A2b screening record's; A2b `protocol_sha256` `1e8aebe2…` unchanged |
| Outputs (scratch, git-ignored, new) | `A2d_seed40001_reps2000_raw.csv` (16,000 rows, SHA-256 `9315c5e4…`), `A2d_seed40001_reps2000_summary.json` (SHA-256 `3f023425…`), `A2d_seed40001_reps2000_corrected_analysis.json`, `A2d_module_as_executed.py` |
| Independent check | the summary was reproduced from the raw CSV alone (identical) |
| Preserved | A2b screening record `69291dd2…` and diagnostic `9d43ca2c…`, v1 archive, A2/A3, A6 ledger: unchanged |
| **Conformance** | the run conformed to the frozen design **as coded**, which contained a unit error in the variance-ratio definition (V̂/V_n instead of V̂/(n V_n)), found when the mean ratios printed as ≈ 235. It invalidated the mean-ratio clause of P2, all of P3 and the rescaling counterfactual **as executed**. The raw data are unaffected. A corrected analysis of the same raw file (no rerun, no rule or threshold changed) is used for those items; the original summary is kept unchanged. See design §9 |

## 2. Core results: tails by interval (lower = `lo > 0`, the "detected" tail; upper = `hi < 0`; coverage)
Oracle = exact variance of the simulated process. 2000 replications; SE of a 2.5 % tail 0.35 pp, of coverage 0.49 pp. Cases share series seeds, so cases are **not independent**; intervals within a case are paired. Values in %.
| Case | Oracle lo / hi (cov) | HAC L4 | HAC L9 | HAC L19 |
|---|---|---|---|---|
| G1 normal 0 | 2.80 / 2.20 (95.00) | 2.90 / 2.55 (94.55) | 3.05 / 3.20 (93.75) | 4.10 / 3.80 (92.10) |
| G2 normal 0.3 | 2.85 / 2.15 (95.00) | 3.65 / 3.55 (92.80) | 3.50 / 3.50 (93.00) | 4.45 / 4.10 (91.45) |
| G3 normal −0.2 | 2.85 / 2.30 (94.85) | 2.50 / 2.40 (95.10) | 2.80 / 2.80 (94.40) | 3.85 / 3.65 (92.50) |
| S1 normal 0.6 | 2.90 / 2.25 (94.85) | 6.20 / 6.20 (87.60) | 4.70 / 4.80 (90.50) | 5.00 / 4.50 (90.50) |
| G4 skewed (lag-1 0.09) | **3.15 / 1.90** (94.95) | **1.40 / 5.30** (93.30) | 1.65 / 5.60 (92.75) | 2.10 / 6.40 (91.50) |
| G5 skewed (lag-1 0.30) | **3.60 / 1.30** (95.10) | **1.55 / 7.90** (90.55) | 1.35 / 7.95 (90.70) | 1.65 / 8.00 (90.35) |
| C4 symmetric heavy tail (matches G4) | 2.55 / 2.10 (95.35) | 3.25 / 2.95 (93.80) | 3.60 / 3.15 (93.25) | 3.90 / 3.65 (92.45) |
| C5 symmetric heavy tail (matches G5) | 2.90 / 2.50 (94.60) | 4.05 / 3.60 (92.35) | 3.80 / 3.40 (92.80) | 4.35 / 3.80 (91.85) |
Mirror (Y → −Y, an identity, not evidence): for a left-skewed series the HAC lower-tail ("detected") rate equals the table's upper tail: G4m 5.3 / 5.6 / 6.4 % and G5m 7.9 / 7.95 / 8.0 % for L4 / L9 / L19, against ≤ 1.9 % for the oracle.

## 3. Variance-estimator diagnostics (corrected ratio r = V̂ / (n V_n))
Mean ratio | CV² of the ratio. Iid asymptotic CV² prediction (4/3)(L + 1)/n = 0.0278 / 0.0556 / 0.1111. corr = correlation of the sample mean with r (L4).
| Case | L4 | L9 | L19 | corr(mean, r), L4 | captured fraction f (L4 / L9 / L19) |
|---|---|---|---|---|---|
| G1 | 0.980 \| 0.0285 | 0.959 \| 0.0574 | 0.918 \| 0.1190 | −0.02 | 1 / 1 / 1 |
| G2 | 0.849 \| 0.0340 | 0.893 \| 0.0643 | 0.885 \| 0.1272 | −0.02 | 0.868 / 0.934 / 0.967 |
| G3 | 1.063 \| 0.0251 | 1.001 \| 0.0531 | 0.939 \| 0.1139 | −0.02 | 1.083 / 1.042 / 1.021 |
| S1 | 0.636 \| 0.0442 | 0.774 \| 0.0758 | 0.825 \| 0.1413 | −0.01 | 0.654 / 0.814 / 0.906 |
| G4 | 0.944 \| 0.1039 | 0.945 \| 0.1378 | 0.918 \| 0.2010 | **+0.66** | 0.964 / 0.982 / 0.991 |
| G5 | 0.853 \| 0.1803 | 0.901 \| 0.2347 | 0.899 \| 0.3152 | **+0.72** | 0.868 / 0.934 / 0.967 |
| C4 | 0.943 \| 0.0766 | 0.939 \| 0.1067 | 0.908 \| 0.1691 | −0.01 | 0.963 / 0.982 / 0.991 |
| C5 | 0.844 \| 0.0897 | 0.891 \| 0.1224 | 0.884 \| 0.1843 | −0.02 | 0.862 / 0.931 / 0.965 |
t-statistic skewness (L4): G4 −0.48, G5 −0.63 for HAC versus +0.22, +0.32 for the oracle; controls +0.08, +0.08 (HAC) and +0.09 (oracle).

**Variability-only counterfactual** (V̂ rescaled to unit mean ratio, using the oracle V_n; a diagnostic, not a procedure): coverage in % for L4 / L9 / L19 versus observed HAC coverage.
| Case | Rescaled | Observed |
|---|---|---|
| G1 | 94.65 / 94.40 / 93.30 | 94.55 / 93.75 / 92.10 |
| G2 | 94.65 / 94.25 / 93.10 | 92.80 / 93.00 / 91.45 |
| G3 | 94.75 / 94.40 / 93.50 | 95.10 / 94.40 / 92.50 |
| S1 | 94.15 / 94.05 / 92.85 | 87.60 / 90.50 / 90.50 |
| G4 | 94.00 / 93.40 / 93.05 (L4: lower 1.15, upper 4.85) | 93.30 / 92.75 / 91.50 |
| G5 | 92.50 / 92.15 / 91.60 (L4: lower 0.95, upper 6.55) | 90.55 / 90.70 / 90.35 |
Effective-df arithmetic for the iid normal case: the residual miss after removing bias, 5.35 / 5.60 / 6.70 %, against P(|t_ν| > 1.96) = 5.39 / 5.78 / 6.57 % for ν = 72 / 36 / 18 (differences ≤ 0.2 pp).

## 4. Pre-registered signatures
| Id | As executed | Corrected analysis | Detail |
|---|---|---|---|
| P1 oracle exact in normal cases | met | met | oracle coverage 95.00 / 95.00 / 94.85 / 94.85 %; all tails within 3 SE: generator and exact variance validated |
| P2 (H1) | not met | **not met** | ordering miss(L4) < miss(L9) < miss(L19): met in G1 and G3; CV² within ±25 % of the formula: met for all L (0.0285 / 0.0574 / 0.1190 vs 0.0278 / 0.0556 / 0.1111); mean ratio within ±0.03 of 1 in G1: met for L4 (0.980), **not** for L9 (0.959) and L19 (0.918) |
| P3 (H3) | not met (invalid) | **not met, narrowly** | window f − 0.08 … f + 0.02 met for L4 and L9 in G2 and S1; L19 misses by 0.002 (G2: 0.885 vs ≥ 0.887) and 0.001 (S1: 0.825 vs ≥ 0.826) |
| P4a oracle opposite sign | met | met | oracle lower > upper in G4 (z_asym −2.5) and G5 (−4.6); HAC the reverse |
| P4b HAC replicates the screening asymmetry on fresh seeds | met | met | z_asym +6.6 … +9.7 for HAC L4, L9 in G4, G5 |
| P4c controls symmetric | met | met | \|z_asym\| ≤ 0.9 for the oracle, HAC L4 and L9 in C4 and C5 |
| P4d correlation mechanism | met | met | corr +0.66 / +0.72 in G4 / G5; \|corr\| ≤ 0.02 in C4, C5, G1 |
| P5 kurtosis inflates estimator variability | met | met | CV²(C4)/CV²(G1) = 2.69 |
| P6 mirror identity | met | met | exact |

## 5. What the evidence supports, leaves open, and cannot show
**Gained support (diagnostic, synthetic, n = 240, these AR(1)-type series)**
1. *Estimator variability behaves as the effective-df arithmetic predicts for normal data.* CV² matches (4/3)(L + 1)/n within 3 % (L4), 3 % (L9), 7 % (L19), and after removing bias the residual miss matches the t_ν prediction within 0.2 pp. This resolves most of the previously "unexplained" excess in the screening: it was variability **plus bias**.
2. *The variance estimate carries a downward finite-sample bias beyond truncation, close to −(L + 1)/n.* In G1 (no truncation) the mean ratio is 0.980 / 0.959 / 0.918 against 1 − (L + 1)/n = 0.979 / 0.958 / 0.917; in G2 and S1 the shortfall from f has the same size. It was not pre-registered (hence P2 and P3 not met at L9, L19) and is an observed regularity, not a derived result.
3. *Skewness, studentization and the tail asymmetry.* The upper-tail excess appears only in the skewed cases and replicates the screening on fresh seeds. The oracle interval (variance known) has the **opposite** asymmetry (G4: 3.15 % lower / 1.90 % upper, near the Edgeworth orientation 3.05 / 1.95); HAC reverses it; the correlation between the sample mean and the variance estimate is +0.66 / +0.72 under skew and about 0 elsewhere. In the symmetric, kurtosis- and lag-matched controls the tails are symmetric (|z_asym| ≤ 0.9). Together: the asymmetry is produced by skewness acting through the studentization, **not** by kurtosis alone.
4. *Kurtosis separately inflates both tails symmetrically:* HAC tails in C4/C5 exceed the oracle by about 0.7–1.6 pp each, with estimator CV² 2.7× that of G1.
5. *Bias and skew are separate mechanisms:* removing the variance bias leaves the skewed-case asymmetry intact (G4 L4: lower 1.15 %, upper 4.85 %).
6. *Mirror implication, now on fresh seeds:* if the loss-difference skew is left-handed, HAC lower-tail size is 5.3–8.0 % for these cases.

**Unresolved**
- Whether the *residual* in heavy-tailed data follows an effective-df rule: it does not at L4 in C4 (ν ≈ 26 predicts a miss of about 6 %; the bias-removed miss is 5.35 %).
- The sign and size of the skew of the pipeline's per-origin loss differences (the mirror question is conditional on it).
- Whether bootstrap or studentized-bootstrap intervals reproduce, reduce or remove the tail asymmetry and the variability term (not run).

**Cannot be concluded**
- That any real procedure is valid: the oracle and the rescaling counterfactual use the true variance, which no procedure has; the counterfactual coverage figures are not attainable.
- Anything about the pipeline, real data, other dependence structures (volatility clustering, long memory, non-stationarity), n ≠ 240, or block-bootstrap intervals.
- That the sinh control equals "kurtosis alone": it matches the 4th moment and lag-1 only.
- Any ranking or pass/fail of methods; no threshold was applied.

## 6. Monte Carlo uncertainty and limitations
- 2000 replications per case: SE 0.35 pp for a 2.5 % tail, 0.49 pp for coverage; Wilson 95 % intervals and distribution-free order-statistic intervals for t quantiles are in the summary. Cases reuse the same series seeds, so the apparent consistent oracle asymmetry across normal cases (lower 2.8–2.9 %, upper 2.15–2.3 %) is **one noise realisation**, not four confirmations.
- Paired HAC-versus-oracle discordance is stored (for instance G2 L4 upper tail 28 HAC-only versus 0 oracle-only); sample means match the exact SD within 1–2 %.
- Synthetic AR(1)-type series only; the analysis correction (design §9) was made after seeing results, with the rules and thresholds unchanged; the unit error was mine.

## 7. Does the evidence justify proposing a new protocol?
**Yes, to *propose* one (not to run it).** A2d replaced the earlier hypotheses with a measured decomposition of the HAC under-coverage into (i) a downward bias (truncation plus about −(L + 1)/n), (ii) estimator variability that grows with L and with kurtosis, and (iii) a skew-driven, studentization-induced tail asymmetry with a sign opposite to the oracle's. Any candidate for a future A2b-v2 should be judged against that decomposition: a bias-aware or fixed-b HAC addresses (i) and (ii) but not (iii); a studentized bootstrap targets (iii) and (ii) but not truncation; neither has been tested. The unknown sign of the skew argues for gating both tails (mirror cases). **Nothing has been proposed or started**; any v2 needs your separate approval and fresh seed ranges (40001–42000 and 140001–142000 are consumed; 20001–25000 remains unclaimed).

## 8. Decisions requiring your review
1. Accept the post-run analysis correction (design §9) as documented, or require the A2d run to be repeated on new seeds with the corrected definition (the data would not change in substance; cost about 25 s but consumes another seed range)?
2. Do you want a written A2b-v2 proposal (candidate classes above, mirror-skew gating principle, stopping rule), for a later separate approval?
3. Should the skew of the pipeline's per-origin loss differences be measured first (A2c prerequisite) so the mirror question is settled on project data?
4. Keep the wording "improvement detected is a screening result" meanwhile (default: yes).

## 9. Status
A2d executed and analysed; PA-1 and PA-4 OPEN; no selection, no verdict; Stage 2, A2c, extensions, neural work not run; **Phase 0 BLOCKED.**
