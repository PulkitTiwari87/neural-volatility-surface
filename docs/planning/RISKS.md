# Risk Register

**Status:** PROPOSED · **Source:** MP §25 plus risks identified while structuring requirements · **Canonical for:** project risks, likelihood/impact, mitigation, triggers · **Related:** [IMPLEMENTATION_PLAN](../../IMPLEMENTATION_PLAN.md), [KNOWN_LIMITATIONS](../research/KNOWN_LIMITATIONS.md)

Likelihood/Impact are **initial qualitative judgments** (Low/Med/High), not measurements; re-assess at each gate. IDs are referenced from the implementation plan.

| ID | Risk | Origin | L | I | Mitigation | Trigger / early signal | Owner role |
|---|---|---|---|---|---|---|---|
| RISK-01 | Historical option data is expensive, incomplete, or too short for a credible study | MP §25 | High | High | Decide provider and scope first (Phase 0); quantify minimum viable dataset; synthetic-first development; reduce scope (different underlying/frequency) rather than proceed | Fewer usable snapshots than the MVD; unaffordable pricing | Project owner |
| RISK-02 | Silent data loss or corruption in the pipeline | Foundation | Med | High | Conservation test (retained + excluded = ingested); write-once raw; hashes; quality reports | Counts don't reconcile; hash mismatch | Data engineer |
| RISK-03 | Pricing model mismatch (e.g., European model on American options; dividend/rate errors) biases IV | MP §9 | Med | High | DEC-004 decision with evidence; reject unsupported instruments; assumption sets versioned; sensitivity study | IV bias in deep ITM/short maturity; parity violations | Quant lead |
| RISK-04 | Interpolation creates false structure | MP §25 | Med | Med | Masks; interpolate only within hull; evaluate on observed cells; method comparison | Large differences between methods; high interpolated share | Quant lead |
| RISK-05 | Look-ahead leakage inflates results | MP §25 | Med | High | GR-LEAK tests (truncation invariance, sentinels); test-window access log; code review | Too-good-to-be-true gains; failing invariance test | ML engineer |
| RISK-06 | Timestamp/timezone/calendar misalignment between quotes, underlying, and rates | MP §8 | Med | Med | Explicit timestamps; alignment policy and recorded gaps; calendar tests (holidays, early closes, DST) | Spurious IV jumps at session boundaries | Data engineer |
| RISK-07 | Too few independent daily surfaces for neural models; weak statistical power | MP §12–§13 | High | Med | Baselines first; low-dimensional representation; go/no-go note; honest null results; origin-level inference | Wide variability across folds/seeds | ML engineer |
| RISK-08 | Neural overfitting / selection bias / seed luck | MP §25 | Med | High | Chronological walk-forward; multi-seed reporting; limited search budget recorded; frozen config before test | Large validation–test gap | ML engineer |
| RISK-09 | Misleading visuals (3D scaling, interpolated shown as observed, aggregate-only metrics) | MP §25 | Med | High | Design rules (status semantics, 2D alternatives, n shown); UA tests | Reviewer misreads in usability check | Frontend lead |
| RISK-10 | Licensing prevents storage, display or publication | MP §25 | Med | High | Licence review before collecting; restrict exposure level; aggregate-only display if required | Ambiguous/forbidding ToS | Project owner |
| RISK-11 | "Live"/real-time mislabelling of delayed data | MP §25 | Low | High | Data-mode enum and UI rule; provider latency documented | Any "live" string without real-time licence | Frontend lead |
| RISK-12 | Arbitrage violations in surfaces/forecasts | MP §25 | Med | Med | Diagnostics now; constraints in Phase 7 | Diagnostic flags on forecast surfaces | Quant lead |
| RISK-13 | Performance of regime-stressed periods differs; apparent skill vanishes | MP §25 | Med | High | Regime/period reporting; failure cases | Regime-wise sign flips | Quant lead |
| RISK-14 | Scope creep / premature infrastructure or UI before science is validated | Foundation (NFR-012) | Med | Med | Phase gates; YAGNI review; out-of-scope lists | PRs outside active phase | Project owner |
| RISK-15 | Documentation drifts from reality (claims of implemented/validated without evidence) | Foundation | Med | Med | Status labels; GR-ENG-07; audit at each gate | Mismatch found in audit | All |
| RISK-16 | Credential or licensed-data leakage | MP §20 | Low | High | GR-SEC-01/02/04; secret scan; `.gitignore`; incident procedure | Secret scan alert | Backend lead |
| RISK-17 | Dependency/toolchain instability (numeric/ML wheels, platform differences) | Foundation | Med | Med | DEC-015 clean-machine test; pinned lockfile | Install failures across machines | Backend lead |
| RISK-18 | Single point of expertise / bus factor | Foundation (A-3) | Med | Med | Documentation, ADRs, reproducible records | Knowledge only in one head | Project owner |

## Review cadence
At every gate and whenever a decision changes. Closed risks are marked with date and evidence; new risks are appended, never renumbered.
