# Phase 0 A2b Screening Diagnostic and Next-Protocol Proposal

> **SYNTHETIC evidence only. Read-only diagnostic of one completed screening run; nothing was rerun. No method is selected, no gate is redesigned, nothing here is approved.** PA-1 was OPEN when this was written — **superseded 2026-10-13: PA-1 CLOSED — NO-GO by owner decision ([PHASE0_CLOSURE_RECORD](PHASE0_CLOSURE_RECORD.md) §7); the content of this report is unchanged** — and **Phase 0 is BLOCKED**. Related: [PHASE0_OWNER_DECISION_PACKAGE](PHASE0_OWNER_DECISION_PACKAGE.md) §9 (the frozen A2b-v1 protocol), [decision.md](../../decision.md) PA-1. Prepared 2026-10-13.

## 1. Record verification
| Item | Result |
|---|---|
| Record | `scratch/phase0_audit/A2b_screening_seed7001_reps2000.json`, SHA-256 `69291dd27fcde2ee1ca7131de2d8d4a238c8f1bf6340b14fd2c9226110188ccc` (equals the hash reported after the run) |
| Protocol / code | `protocol_sha256` `1e8aebe2…bd3fb` and all `phase0/*.py` hashes in the record equal the current files |
| Status | stage `screening`, protocol-conformant, not void, M0 reproduced stored A2 (G1, G2, S1, G4); outcome `NO_METHOD_ADMISSIBLE` |
| Counting identity | in all 42 cells, coverage count + lower-tail count + upper-tail count = 2000 |
| Diagnostic output | `scratch/phase0_audit/A2b_screening_diagnostic.json` (new file; the record was not modified) |

## 2. Metric definitions and denominators (read from `phase0/audit.py` and `evaluate.py`)
- Every rate is a count over **2000 replications** of the same case (series seeds 7001–9000, bootstrap seeds 107001–109000); the six methods are applied to the **same** series (paired), and the cases reuse the same seeds, so cells are not independent.
- *Coverage* = share with `lo ≤ 0 ≤ hi`. *Lower-tail rejection (size)* = share with `lo > 0` (the "detected" rule). *Upper-tail rejection* = share with `hi < 0`. They partition the replications, so coverage = 1 − lower − upper. The upper-tail **count** is not stored; it is the rate × 2000, an exact integer (identity checked above).
- *Half-width* = mean of (hi − lo)/2 over replications. `half_width_over_sd_of_mean` divides it by `pstdev` of the 2000 sample means; its own relative error is about 1.6 % (1/√(2·2000)), so ratios carry ±1.6 %. `half_width_ratio_vs_first_method` = summed half-widths relative to M0.
- Bootstrap intervals (`M0`–`M2`): moving-block percentile, B = 1000, limits `sorted[25]` and `sorted[974]` (25 resample means beyond each limit). HAC intervals (`M3`–`M5`): mean ± 1.95996·√(V̂/n), Bartlett lag L = 4, 9, 19, divisor n, no small-sample factor. Both procedures are exactly equivariant to Y → −Y: (lo, hi) → (−hi, −lo) (verified on 5 series).
- Gate cells: coverage ≥ 0.936 and lower-tail rate ≤ 0.035 in each of G1–G5 (screening **tolerances**, not certification).

## 3. Diagnostic table — gating cases
`lo` = lower tail (`lo > 0`), `hi` = upper tail (`hi < 0`). `z_lo`, `z_hi` = (rate − 2.5 %)/0.349 pp. `z_asym` = (hi_count − lo_count)/√(hi_count + lo_count) (symmetric tails ⇒ 0). **C** = coverage < 0.936, **S** = lower tail > 0.035; *m* = marginal (the 95 % Wilson interval of that rate contains the threshold). Pattern is a deterministic rule on the stored counts: |z_asym| > 3 ⇒ asymmetric tails; both tails > 2.5 % + 1.96 SE ⇒ both tails inflated.

| Case | Method | Cov | lo | hi | z_lo | z_hi | z_asym | hw/sd | Fails | Pattern |
|---|---|---|---|---|---|---|---|---|---|---|
| G1 | `M0_block5` | 0.9360 | 0.0310 | 0.0330 | +1.7 | +2.3 | +0.4 | 1.883 | - | - |
| G1 | `M1_block10` | 0.9305 | 0.0360 | 0.0335 | +3.2 | +2.4 | -0.4 | 1.857 | Cm Sm | both tails inflated |
| G1 | `M2_block20` | 0.9080 | 0.0455 | 0.0465 | +5.9 | +6.2 | +0.1 | 1.801 | C S | both tails inflated |
| G1 | `M3_hac_L4` | 0.9395 | 0.0300 | 0.0305 | +1.4 | +1.6 | +0.1 | 1.893 | - | - |
| G1 | `M4_hac_L9` | 0.9330 | 0.0330 | 0.0340 | +2.3 | +2.6 | +0.2 | 1.868 | Cm | both tails inflated |
| G1 | `M5_hac_L19` | 0.9220 | 0.0390 | 0.0390 | +4.0 | +4.0 | +0.0 | 1.819 | C Sm | both tails inflated |
| G2 | `M0_block5` | 0.9140 | 0.0445 | 0.0415 | +5.6 | +4.7 | -0.5 | 1.753 | C S | both tails inflated |
| G2 | `M1_block10` | 0.9135 | 0.0445 | 0.0420 | +5.6 | +4.9 | -0.4 | 1.792 | C S | both tails inflated |
| G2 | `M2_block20` | 0.9025 | 0.0490 | 0.0485 | +6.9 | +6.7 | -0.1 | 1.768 | C S | both tails inflated |
| G2 | `M3_hac_L4` | 0.9170 | 0.0430 | 0.0400 | +5.2 | +4.3 | -0.5 | 1.761 | C Sm | both tails inflated |
| G2 | `M4_hac_L9` | 0.9225 | 0.0395 | 0.0380 | +4.2 | +3.7 | -0.2 | 1.801 | C Sm | both tails inflated |
| G2 | `M5_hac_L19` | 0.9150 | 0.0420 | 0.0430 | +4.9 | +5.2 | +0.2 | 1.785 | C Sm | both tails inflated |
| G3 | `M0_block5` | 0.9470 | 0.0260 | 0.0270 | +0.3 | +0.6 | +0.2 | 1.962 | - | - |
| G3 | `M1_block10` | 0.9345 | 0.0335 | 0.0320 | +2.4 | +2.0 | -0.3 | 1.895 | Cm | both tails inflated |
| G3 | `M2_block20` | 0.9125 | 0.0440 | 0.0435 | +5.4 | +5.3 | -0.1 | 1.821 | C S | both tails inflated |
| G3 | `M3_hac_L4` | 0.9475 | 0.0250 | 0.0275 | +0.0 | +0.7 | +0.5 | 1.973 | - | - |
| G3 | `M4_hac_L9` | 0.9380 | 0.0310 | 0.0310 | +1.7 | +1.7 | +0.0 | 1.909 | - | - |
| G3 | `M5_hac_L19` | 0.9240 | 0.0385 | 0.0375 | +3.9 | +3.6 | -0.2 | 1.841 | C Sm | both tails inflated |
| G4 | `M0_block5` | 0.9210 | 0.0240 | 0.0550 | -0.3 | +8.6 | +4.9 | 1.839 | C | asymmetric tails (hi-lo) |
| G4 | `M1_block10` | 0.9125 | 0.0290 | 0.0585 | +1.1 | +9.6 | +4.5 | 1.831 | C | asymmetric tails (hi-lo) |
| G4 | `M2_block20` | 0.8940 | 0.0345 | 0.0715 | +2.7 | +13.3 | +5.1 | 1.784 | C | asymmetric tails (hi-lo) |
| G4 | `M3_hac_L4` | 0.9220 | 0.0160 | 0.0620 | -2.6 | +10.6 | +7.4 | 1.850 | C | asymmetric tails (hi-lo) |
| G4 | `M4_hac_L9` | 0.9175 | 0.0200 | 0.0625 | -1.4 | +10.7 | +6.6 | 1.844 | C | asymmetric tails (hi-lo) |
| G4 | `M5_hac_L19` | 0.9100 | 0.0225 | 0.0675 | -0.7 | +12.2 | +6.7 | 1.807 | C | asymmetric tails (hi-lo) |
| G5 | `M0_block5` | 0.8970 | 0.0275 | 0.0755 | +0.7 | +14.5 | +6.7 | 1.727 | C | asymmetric tails (hi-lo) |
| G5 | `M1_block10` | 0.8950 | 0.0275 | 0.0775 | +0.7 | +15.0 | +6.9 | 1.765 | C | asymmetric tails (hi-lo) |
| G5 | `M2_block20` | 0.8810 | 0.0315 | 0.0875 | +1.9 | +17.9 | +7.3 | 1.738 | C | asymmetric tails (hi-lo) |
| G5 | `M3_hac_L4` | 0.9020 | 0.0190 | 0.0790 | -1.7 | +15.5 | +8.6 | 1.739 | C | asymmetric tails (hi-lo) |
| G5 | `M4_hac_L9` | 0.9035 | 0.0170 | 0.0795 | -2.3 | +15.6 | +9.0 | 1.779 | C | asymmetric tails (hi-lo) |
| G5 | `M5_hac_L19` | 0.8945 | 0.0205 | 0.0850 | -1.3 | +17.2 | +8.9 | 1.764 | C | asymmetric tails (hi-lo) |

Stress cases (not gating): **S1 normal ρ = 0.6, n = 240** (cov / lo / hi): M0 0.861 / 0.073 / 0.066; M1 0.891 / 0.059 / 0.050; M2 0.890 / 0.054 / 0.056; M3 0.868 / 0.070 / 0.062; M4 0.898 / 0.054 / 0.048; M5 0.903 / 0.047 / 0.050. **S2 normal ρ = 0.3, n = 120** (cov / lo / hi): M0 0.916 / 0.043 / 0.041; M1 0.906 / 0.044 / 0.049; M2 0.868 / 0.068 / 0.064; M3 0.923 / 0.040 / 0.037; M4 0.918 / 0.040 / 0.042; M5 0.899 / 0.046 / 0.054.

## 4. Monte Carlo uncertainty (from the stored counts only)
- SE of a 2.5 % tail rate at 2000 replications: 0.349 pp; of 95 % coverage: 0.487 pp. A cell is **marginal** when its Wilson 95 % interval contains the gate threshold; the table flags those. All other failures are clear on this sample.
- Marginal failures: G1 M1 (C, S), M4 (C), M5 (S); G2 M3, M4, M5 (S only; their coverage failures are clear); G3 M1 (C), M5 (S). Every G4/G5 coverage failure and every M0/M1/M2 failure in G2 is clear.
- Not computable from the record: paired differences between methods and between cases (per-replication outcomes were not stored), so statements such as "M3 beats M0" are descriptive only; all M0-versus-M3 differences are within about one SE except where stated.

## 5. Findings — confirmed versus hypotheses
**Confirmed from the stored counts**
1. *Skewed cases (G4, G5): the failure is upper-tail only.* Lower-tail rates are 1.6–3.45 % (z −2.6 … +2.7), at or below nominal; upper-tail rates are 5.5–8.75 % (z +8.6 … +17.9); |z_asym| 4.5–9.0 for all six methods. Coverage fails because of the upper tail; the "detected" rule is conservative in this orientation.
2. *Normal ρ = 0.3 (G2): both tails are inflated, symmetrically, for every method.* Lower 3.95–4.9 %, upper 3.8–4.85 %, |z_asym| ≤ 0.5. Every method fails the size gate; for M3, M4, M5 the failure is within Monte Carlo noise of 3.5 %.
3. *Longer truncation is worse where dependence is absent or negative.* G1 and G3: coverage M0 0.936/0.947 → M2 0.908/0.9125 and M3 0.9395/0.9475 → M5 0.922/0.924, with both tails inflated equally. Same pattern for the bootstrap and the HAC family.
4. *Longer truncation helps only at strong dependence* (stress S1, ρ = 0.6): lower tail M0 7.3 % → M5 4.7 %, still above 3.5 %. At n = 120 (S2) M2 is worst (6.8 %).
5. *Intervals that under-cover are narrower.* Half-width/SD falls from about 1.88–1.97 (adequate cells) to 1.73–1.82 (failing cells); it is a symptom, not a separate cause.
6. *M0 and M3 (same truncation) behave alike* (coverage within about 0.5 pp in each gating case); each fails 4 of 10 criteria; M4 fails 5, M1 7, M2 and M5 8.
7. *Even a lower-tail-only gate would reject every method:* all fail the size criterion in G2 (3.95–4.9 %).

**Supported by arithmetic or analysis, not yet measured**
8. *Variance-estimator variability (effective degrees of freedom) explains part of the symmetric inflation.* A Bartlett estimator with lag L has relative variance ≈ (4/3)(L + 1)/n, i.e. effective df ν ≈ 72, 36, 18 for L = 4, 9, 19 at n = 240. The predicted two-sided miss P(|t_ν| > 1.96·√f), with f the captured fraction of the long-run variance, is 5.4 / 5.8 / 6.6 % in G1 against 6.05 / 6.7 / 7.8 % observed, and 7.2 / 6.6 / 7.0 % in G2 against 8.3 / 7.75 / 8.5 %: it explains roughly 40–70 % of the excess miss. The remainder is unexplained. (The same variability argument applies qualitatively to block length b: fewer, longer blocks.)
9. *Mirror skew would invert the conclusion.* By exact equivariance, a left-skewed series (Y → −Y) has lower-tail size equal to these upper-tail rates: about 5.5–8.75 % for every method. The conservatism seen in G4/G5 depends on the unknown sign of the skew of the pipeline's per-origin loss differences; the screening design had no mirror case.

**Hypotheses requiring experiments**
- H1: symmetric inflation in G1, G3 and long truncation is estimator variability (test: record per-replication studentized statistics and compare with t-like quantiles).
- H2: the upper-tail excess in G4/G5 is skewness, not kurtosis — z² − 1 has skewness 2.83 **and** excess kurtosis 12, so the design cannot separate them (test: mirror case and a symmetric heavy-tailed control).
- H3: the G2 and S1 shortfall is truncation bias plus estimator variability; an **oracle** interval using the known long-run variance (analytic for AR(1): σ²(1+ρ)/(1−ρ); for z² − 1: 2(1+ρ²)/(1−ρ²)) would separate variance estimation from the shape of the mean's distribution.

## 6. Attribution of the failures
| Failure | Demonstrated cause | Evidence level |
|---|---|---|
| G4, G5 coverage (all methods) | upper-tail excess in right-skewed data | pattern confirmed; skew vs kurtosis is H2 |
| G2 size and coverage (all methods) | both tails inflated: variance under-estimation (truncation) plus estimator variability | direction confirmed; split between the two is H3 |
| G1, G3 failures of M1, M2, M4, M5 | both tails inflated: variance-estimator variability grows with block length or lag | confirmed pattern; ~40–70 % explained by the df arithmetic (finding 8), remainder open |
| Under-coverage and narrow intervals | narrow intervals accompany every failing cell; not an independent cause | confirmed association |
| Size distortion limited to the lower tail | G2 only (and long truncation in G1, G3); never in G4/G5 | confirmed |

## 7. Candidates compared (existing versus the studentized-bootstrap fallback)
Nothing below selects a method; it records assumptions and expectations so the owner can decide what, if anything, to test.

| | Block bootstrap, percentile (M0–M2) | HAC / Newey–West (M3–M5) | Studentized (bootstrap-*t*) block bootstrap (fallback, **not implemented**) |
|---|---|---|---|
| Statistic | resample mean; limits are quantiles of the resample means | mean ± 1.96·√(V̂/n) | *t\** = (mean\* − mean)/se\* with se\* from the **same variance estimator applied to each resample**; interval = mean − q\*·se |
| Assumptions | stationarity, weak dependence, block length ≪ n | same, finite fourth moments, smooth kernel | same, plus a consistent variance estimator tied to the block length (Götze–Künsch type), finite moments of higher order for second-order accuracy |
| Truncation bias in the variance | present (captures 65–87 % at ρ = 0.3–0.6 for b = 5) | present (same truncation as the block bootstrap with b = L + 1) | **not removed** (se and se\* are biased in the same direction) |
| Variability of the variance estimate | ignored (percentile) | ignored (normal quantile) | absorbed into the *t\** distribution |
| Skew / tail asymmetry | not corrected (first-order error) | not corrected (symmetric interval) | corrected to second order **if** its assumptions hold |
| Cost (measured, one core) | 17.6 ms per interval (B = 1000) | 0.1 ms | ≈ 0.12 s per interval (B = 1000 × (resample + 0.1 ms)); ≈ 0.5 h for a 2000-replication, 7-case screening and ≈ 1.1–1.2 h for one method at 5000 |
| Failure modes | long blocks give few blocks (n/b), noisier | long lags give low effective df | se\* near zero gives extreme *t\**; instability at small n (S2); block-join artefacts; truncation bias at strong dependence remains; sensitive to b and L |
| Expected effect on what failed | none beyond what was observed | none beyond what was observed | may fix G4/G5 asymmetry and the variability-driven inflation in G1/G3; **not expected to fix G2/S1** (truncation) — it could well still fail the same gate |

Also noted, **not proposed**: a fixed-b HAC critical value would address only the effective-df point (finding 8) in closed form; it would be a new candidate needing its own approval.

## 8. Proposed next protocol (PROPOSAL; nothing started)
**Step A — diagnostic A2d (no method selection).** On a *fresh* seed range disjoint from 7001–9000 and from the unclaimed confirmation range 20001–25000 (proposed series seeds 40001–42000), record per-replication studentized statistics and tail indicators for M3, M4, M5, the **oracle-variance** normal interval (known long-run variance), and for the cases G1–G5 plus a **mirror-skew** case (Y → −Y) and a **symmetric heavy-tailed** control with matching kurtosis. Purpose: test H1–H3 and measure the pure skew effect. HAC-only, runs in seconds; requires a small additive code change and tests. The 20001–25000 range must not be touched.

**Step B — only if approved after reading A2d: a new frozen protocol A2b-v2** (new schema, new protocol hash, new screening seeds, confirmation range chosen before any run), with these properties proposed *before* seeing any v2 data:
1. Candidate list frozen in advance: at most the existing M0 and M3 as references plus studentized candidates T1 = (b = 5, L = 4) and T2 = (b = 10, L = 9), B = 1000 (T-candidates only if approved).
2. Cases: G1–G5, the mirror-skew case(s) and the heavy-tailed control as gating; S1, S2 stress. Reason for mirror cases: the sign of the pipeline's loss-difference skew is unknown, so a direction-agnostic size statement needs both orientations.
3. Screening tolerances unchanged in value (coverage ≥ 0.936; each one-sided tail ≤ 0.035); formal confirmation unchanged in value (coverage LCB ≥ 0.935; each tail UCB ≤ 0.035 at one-sided 95 %), single method, fresh seeds, single use, same selection rule, 1.5× cap, tie band and VOID rule.
4. Computational cap: a candidate that cannot run screening in ≤ 1 h and confirmation in ≤ 2 h on one core is excluded in advance.
5. **Stopping rule:** v2 is the last search round. If no candidate is admissible, PA-1 closes as a documented limitation: "detected" stays a screening rule, with its measured size range (lower-tail 3–5 % in normal ρ = 0.3 cases, up to ≈ 5.5–8.75 % if the loss-difference skew is left-handed) recorded in KNOWN_LIMITATIONS and the evidence reports.

**Not proposed:** changing 0.936/0.035/0.935 after seeing these results; dropping two-sided coverage or the upper tail merely so that M0 or M3 passes (with the right-skew-only gate, every method still fails G2); redefining the cases to favour a method.

## 9. Decisions requiring your approval
1. Authorise Step A (A2d diagnostic, no selection) and the fresh seed range 40001–42000?
2. Should Step B include studentized candidates T1/T2 (new code, about 0.5 h per screening)? Or stop at diagnosis?
3. Approve the *principle* that the next gate be direction-agnostic (each one-sided tail, with mirror-skew cases) — to be decided **before** any v2 data — or keep the two-sided coverage gate as is?
4. Approve the stopping rule (v2 is the last search round; otherwise close PA-1 as a documented limitation)?
5. May the unclaimed confirmation range 20001–25000 be reused by v2, or should a new range be assigned?
6. Meanwhile, keep the wording "improvement detected is a screening result" everywhere?
7. Should the sign and size of the skew of the pipeline's per-origin loss differences be measured first (needs the per-origin d series stored, the A2c prerequisite) so the mirror-skew question is decided on the project's own data?

## 10. Status
No experiment was rerun; no code, record or evidence was changed (the only new file besides this page is the diagnostic output in scratch). Stage 2, A2c, the 300-seed extension and neural work were not run. **PA-1 and PA-4 OPEN; Phase 0 BLOCKED.**
