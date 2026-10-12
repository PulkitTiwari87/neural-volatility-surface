# Open Questions

**Status:** IN_PROGRESS · **Purpose:** capture questions that are not (yet) formal decisions: unknowns, items needing research, and out-of-phase ideas. Formal choices live in [decision.md](../../decision.md). Resolve a question by linking the resolving evidence/ADR; do not delete it.

| ID | Question | Why it matters | Needed to answer | Related | Phase | Status |
|---|---|---|---|---|---|---|
| Q-01 | Which (market, underlying, provider) satisfy licence + history + density? | Gates the project | Assessment + licence review + sample | DEC-001/002/003, RISK-01 | 0 | OPEN |
| Q-02 | How many independent daily surfaces constitute a minimum viable dataset for the planned comparisons? | Determines neural feasibility | Power-style reasoning on baselines; data availability | RISK-07 | 0 | OPEN |
| Q-03 | What is the intended audience/exposure (single researcher, team, public)? | Drives security, licence, deployment | Owner decision | DEC-013, SECURITY §5 | 0–5 | OPEN |
| Q-04 | What software licence is intended? | Public release, contributions | Owner decision + dependency audit | DEC-014 | before release | OPEN |
| Q-05 | Which dividend/rate treatment suits the chosen instrument? | IV correctness | Contract specs + sensitivity study | DEC-004 | 0–2 | OPEN |
| Q-06 | Is put-call parity useful for quote cross-checking or forward inference? | Quality & IV robustness | Experiment on sample | QUOTE_QUALITY_POLICY §7 | 1–2 | NEEDS RESEARCH |
| Q-07 | How should regimes be defined (rule, data, thresholds) without leakage? | Regime reporting | Literature/sample study; pre-registration | EVALUATION_PROTOCOL §4 | 3 | OPEN |
| Q-08 | Which statistical test/bootstrapping approach suits dependent daily forecasts? | Valid claims | Synthetic validation of options | EVALUATION_PROTOCOL §7 | 3 | NEEDS RESEARCH |
| Q-09 | What export formats are required? | FR-018 | User needs | PR.md | 5 | OPEN |
| Q-10 | Which background-job mechanism is the simplest that meets NFR-004? | Architecture | Spike | architecture §9 | 5–6 | OPEN |
| Q-11 | Is prospective forecasting (storing forecasts before outcomes) in scope for v1? | Distinguishes backtest vs prospective claims | Owner decision | MP §16B | 4–6 | OPEN |
| Q-12 | How are event calendars (earnings, macro) sourced with as-of-safe timestamps? | RQ-06, F-M08 | Source assessment | FEATURE_CATALOG | 3 | NEEDS RESEARCH |
| Q-13 | What is the artifact format policy for model weights (safety, portability)? | Security & reproducibility | Spike | DEC-010, SECURITY §3 | 3–4 | OPEN |
| Q-14 | Should the forecast target be absolute IV, change, or factors by default? | Metrics comparability | Phase 3 baselines | DEC-011 | 3 | OPEN |
| Q-15 | Minimum sample thresholds per region for reporting? | Avoid over-reading sparse cells | Data density statistics | GR-MOD-02 | 3 | OPEN |

New questions: append with the next ID; link to an issue/proposal if one exists.
