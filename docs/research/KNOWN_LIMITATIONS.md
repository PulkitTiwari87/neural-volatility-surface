# Known Limitations

**Status:** IN_PROGRESS — living document; currently lists limitations known **before any implementation** (design-time). Items must be updated with measured evidence as work proceeds. · **Source:** MP header, §3, §6, §8–§10, §14, §25 · **Surfaced in:** Methodology page (UI-011), forecast views, release notes (AC-11)

| ID | Limitation | Origin | Effect | Mitigation / how it is surfaced | Status |
|---|---|---|---|---|---|
| L-01 | Not investment advice; not a trading system. Forecasts are uncertain. | MP header | Misuse risk | Disclaimers (README, UI, GR-PRD-02) | Documented |
| L-02 | IV is inferred from a model and inputs, not observed. | MP §3 | Model/assumption dependence | Record model, rates, dividends, calendar per observation | Documented |
| L-03 | Observed quotes are not executable prices; midpoint unreliable for illiquid options. | MP §2, §8 | Noisy IV | Quote policy + sensitivity analysis | Planned |
| L-04 | Historical option data may be incomplete, expensive, or licence-restricted; free complete history cannot be assumed. | MP §2, §6, §25 | May limit coverage, history, publication | Phase 0 assessment; licence review | Open (DEC-001/002) |
| L-05 | Surfaces are sparse; interpolation adds structure that is not market data. | MP §10 | False structure | Status masks; evaluation on observed cells only | Planned |
| L-06 | European pricing may be inappropriate for American-style options. | MP §9 | Biased IV, especially deep ITM / short maturity | DEC-004; reject unsupported instruments | Open |
| L-07 | Data volume (number of independent daily surfaces) may be small relative to neural model capacity. | MP §12–§13 | Overfitting; weak power | Baselines first; go/no-go note; lower-dimensional comparator | To be measured (Phase 0) |
| L-08 | Daily forecasts are serially dependent; effective sample size is smaller than cell count. | Methodology | Overstated significance | Origin-level inference methods (EVALUATION_PROTOCOL §7) | Planned |
| L-09 | Results may differ across regimes; apparent performance can vanish under stress. | MP §25 | Non-stationarity | Regime/period reporting; failure cases | Planned |
| L-10 | Historical backtests are not prospective evidence. | MP §16B | Overconfidence | Label forecast_kind; prospective tracking only if collected | Planned |
| L-11 | End-of-day snapshots may mix quote times across contracts and the underlying. | MP §8 | Timestamp misalignment noise | Alignment policy and recorded gaps | Planned |
| L-12 | Explainability outputs (importance, SHAP-style) are unstable under correlated features and are not causal. | MP §15 | Misinterpretation | State method & caveats in UI | Planned |
| L-13 | No-arbitrage violations may appear in fitted/forecast surfaces; v1 reports diagnostics only. | MP §25 | Implausible surfaces | Diagnostics; Phase 7 constraints | Planned |
| L-14 | Single market/underlying in v1; conclusions do not transfer automatically. | MP §2 | Limited generality | Scope statements in reports | Planned |
| L-15 | 3D rendering can mislead (perspective, scaling). | MP §25 | Misreading | 2D alternatives; visible axes/units | Planned |
| L-16 | Data freshness: provider data may be delayed; no real-time capability assumed. | MP §6 | Mislabeling risk | Data-mode label (GR-DATA-07) | Planned |
| L-17 | Documentation currently precedes implementation: no component is implemented or validated. | Foundation | Over-reading docs | Status labels; honest status tables | Active |

**Rule:** a limitation is removed only with evidence that it no longer applies; otherwise it remains and may be refined. New limitations discovered in experiments are added with the experiment ID.
