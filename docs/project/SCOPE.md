# Scope

**Status:** PROPOSED · **Source:** MP §2, §22, §23 · **Canonical for:** scope boundaries per release and phase · **Related:** [PR.md](../../PR.md) §2, [IMPLEMENTATION_PLAN](../../IMPLEMENTATION_PLAN.md)

## In scope — initial version (MP §2)
- Historical option-chain ingestion for **one** clearly defined underlying and market (DEC-001: interim SPY for the private track, not final; the owner has also stated US and India as separate studies, `orchestration/DECISIONS.md` OD-2, not yet recorded in decision.md).
- Calls and puts; strikes, expirations; bid/ask; last price, volume, open interest where available.
- Underlying price and timestamp alignment; interest-rate and dividend assumptions where relevant.
- IV calculation from valid quotes; surface construction across moneyness/strike and maturity.
- Data-quality checks and missing-data handling.
- Forecasting one or more future horizons — starting with the **next valid trading session** (MP §12).
- Baseline and neural comparisons; walk-forward evaluation without leakage.
- Interactive visualizations and exportable research results; explicit warnings about data limitations and model uncertainty.

## Out of scope — initial version
Automated trade execution · personalized investment advice · profitability claims · scraping against terms · live exchange feeds without licence · treating all quotes as executable · real-time/streaming mode (historical first) · multi-underlying, multi-horizon, probabilistic, arbitrage-aware, regime-conditioned and intraday work (Phase 7) · hosted/paid infrastructure without documented need.

## Boundaries by phase
| Phase | Adds | Does not add |
|---|---|---|
| 0 | Decisions, assessment, sample, success criteria | Pipelines, models, UI |
| 1 | Data pipeline to validated quotes | IV, surfaces |
| 2 | IV & surfaces | Forecasts |
| 3 | Datasets, baselines, evaluation | Neural models |
| 4 | Neural models & experiments | UI |
| 5 | API & UI | Hardening/deployment |
| 6 | Reliability, release | New research features |
| 7 | Approved extensions | — |

## Scope-change rule
Anything not in a phase's scope goes to [OPEN_QUESTIONS](../planning/OPEN_QUESTIONS.md) or a proposal ([template](../templates/FEATURE_PROPOSAL_TEMPLATE.md)); it enters a phase only through a recorded decision. Scope creep toward live data, extra underlyings, or UI polish before the science is validated is explicitly discouraged.

## Open scope items
Market/underlying (DEC-001, interim SPY); forecast horizons beyond next session (Phase 7); export formats (FR-018). Public vs. private access is settled for now: DEC-013 (2026-10-20) is local research tool only, no public display.
