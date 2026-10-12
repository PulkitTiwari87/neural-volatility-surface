# Uncertainty and Calibration

**Status:** PROPOSED (Phase 4 "where feasible"; Phase 7 for probabilistic forecasting) · **Canonical for:** uncertainty labelling rules and calibration evidence · **Source:** MP §14, §15, §23 Ph4/Ph7 · **Related:** guardrail GR-MOD-06, SCI-010, [EVALUATION_PROTOCOL](EVALUATION_PROTOCOL.md)

## 1. Principle
Uncertainty outputs are labelled for **what they are**. "Calibrated" is claimed only with evidence. Absent uncertainty is shown as absent (`none`), not as a zero-width band.

## 2. Taxonomy (`uncertainty_kind`)
| Kind | Meaning | Allowed wording |
|---|---|---|
| `none` | Point forecast only | "Point forecast" |
| `heuristic` | Spread derived from ad-hoc rules (e.g., recent residual scale, ensemble spread) without coverage validation | "Indicative spread — not calibrated" |
| `empirical_interval` | Intervals constructed from out-of-sample residuals/conformal-style procedure with coverage measured on a held-out chronological window | "Empirical interval, nominal X%, measured coverage Y% over N origins in region R" |
| `calibrated` (requires attached calibration report) | Coverage/calibration evidence across regions, periods and regimes within stated tolerance | "Calibrated within … for …; not guaranteed outside" |

## 3. Candidate methods (none selected)
Ensemble spread (seeds/models); residual-based intervals per region; quantile regression/loss; conformal prediction adapted for time series (exchangeability caveats); Monte-Carlo dropout (known to be a heuristic); latent-space distributions. Selection in Phase 4/7 by evidence; complexity must be justified.

## 4. Evidence required to label an interval empirical/calibrated
1. Chronological calibration window distinct from the evaluation window.
2. Coverage at several nominal levels, by region (maturity × moneyness), period, regime, with sample counts.
3. Interval width alongside coverage (sharpness).
4. Check of coverage under distribution shift (stressed regimes).
5. Reported dependence caveats: serial dependence of origins and spatial dependence across cells reduce effective sample size.

## 5. Display requirements
Label with `uncertainty_kind` and nominal level; show measured coverage when available; never imply guarantees; tooltips state method (UI: [design.md](../../design.md) §10, §13).

## 6. Tests
Synthetic data with known noise → intervals attain nominal coverage within tolerance; mislabeled-kind detection (a `calibrated` label without a report fails validation); coverage computation checked against hand examples.

## 7. Limitations
Coverage in tails/stress regimes is hard to validate with limited history; arbitrage-consistent probabilistic surfaces are Phase 7 research.
