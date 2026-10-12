# Glossary

**Status:** PROPOSED · **Canonical for:** terminology used across all documents. Definitions marked *(convention OPEN)* depend on an unresolved decision; use the term only with the convention recorded.

| Term | Definition |
|---|---|
| **Option chain** | The set of listed option contracts on an underlying, each with strike, expiration, call/put type and market observations (MP §3). |
| **Underlying** | The asset on which options are written (e.g., an index, ETF, or stock). *Which one: OPEN (DEC-001).* |
| **Quote** | A bid/ask (and optional last/volume/open-interest) observation for a contract at a timestamp. A quote is not an executable price. |
| **Midpoint** | (bid + ask)/2; common starting price for IV but unreliable for illiquid contracts (MP §8). |
| **Implied volatility (IV)** | The volatility that makes a pricing model's theoretical price equal an observed price. Inferred, not observed. |
| **IV observation** | A derived record: IV (nullable), solver status, iterations, pricing model, inputs, quality flags. |
| **Solver status** | Outcome of IV solving: e.g., converged, price below lower bound, above upper bound, no bracket, max iterations, unsupported instrument. *Enum finalized in Phase 2.* |
| **Theoretical price bounds** | No-arbitrage limits within which an option price must lie for IV to exist under the model. |
| **Forward price (F)** | Underlying price adjusted for carry (rates, dividends) to the option's maturity. *Definition per DEC-004/005.* |
| **Moneyness** | Strike relative to underlying/forward. Variants: K/S, ln(K/S), ln(K/F) *(convention OPEN, DEC-005)*. |
| **Log-moneyness** | Natural log of the moneyness ratio (e.g., `ln(K/F)`). |
| **Maturity / time to expiration (T)** | Remaining time to expiry in years under a documented day-count and calendar *(convention OPEN)*. |
| **Day-count convention** | Rule converting dates to year fractions (e.g., ACT/365). |
| **Volatility smile / skew** | IV as a function of strike/moneyness at fixed maturity; skew is its asymmetry/slope. |
| **Term structure** | IV as a function of maturity at fixed moneyness. |
| **Volatility surface** | IV over (moneyness, maturity). |
| **Surface snapshot** | A standardized surface at one timestamp with grid, values, status mask, construction method and version. |
| **Grid** | The fixed set of (moneyness, maturity) coordinates on which surfaces are standardized *(resolution OPEN, DEC-006)*. |
| **Cell status** | `observed` (from eligible quote), `interpolated` (between observed points by named method), `extrapolated` (outside the observed hull), `missing` (no reliable value). |
| **Observed hull** | Region of coordinate space spanned by observed points; basis for deciding interpolation vs extrapolation. |
| **ATM IV, skew, curvature, term-structure slope** | Surface summaries defined precisely in [FEATURE_CATALOG](../research/FEATURE_CATALOG.md). |
| **Persistence baseline** | Forecast equals the latest observed surface (MP §13). |
| **Forecast origin** | Time *t* at which the forecast is made; only information available at *t* may be used. |
| **Target horizon / target time** | How far ahead (and the specific time) the forecast refers to; first: next valid trading session. |
| **Look-ahead leakage** | Use of information unavailable at the forecast origin in features, labels, preprocessing, or model selection. |
| **Chronological split** | Train < validation < test in time order, never shuffled. |
| **Walk-forward (rolling-origin) evaluation** | Repeated forecasting where the model/state is updated using only data prior to each origin. |
| **Embargo / gap** | Period excluded between training and evaluation to prevent label-horizon overlap leakage. |
| **Backtest** | Evaluation of forecasts on historical data as if made at past origins. Not evidence of future performance. |
| **Prospective forecast** | A forecast made before its target time is observed, stored with its creation time. |
| **Regime** | A market state (e.g., calm vs stressed) defined by a documented rule using data available at the time *(definition OPEN)*. |
| **Grid forecasting / latent-factor forecasting / parametric forecasting / change forecasting** | Output representations from MP §12 (see [FORECASTING_STRATEGY](../research/FORECASTING_STRATEGY.md)). |
| **MAE / RMSE** | Mean absolute / root-mean-square error of IV differences. Units must be stated (decimal vs vol points). |
| **Vol point** | One percentage point of volatility (0.01 in decimal IV). |
| **Coverage / calibration** | For prediction intervals: fraction of outcomes inside nominal intervals / agreement of nominal and empirical frequencies. |
| **Uncertainty kind** | Label of how uncertainty was obtained: `none`, `heuristic`, `empirical_interval`; "calibrated" requires evidence. |
| **Data mode** | `historical`, `delayed`, `latest_available`, `real_time_licensed`. |
| **Raw snapshot** | Immutable, source-faithful record set with source and ingestion metadata. |
| **Dataset version** | Immutable identifier (content hash + config) of a processed dataset. |
| **Provenance / lineage** | Traceable chain from a displayed value back to quotes, assumptions, and code/config versions. |
| **Run record** | Stored experiment metadata sufficient to reproduce a result (see [EXPERIMENT_TEMPLATE](../templates/EXPERIMENT_TEMPLATE.md)). |
| **MP** | The baseline master plan document. |
| **ADR** | Architecture Decision Record. |
| **OPEN / PROPOSED / NEEDS RESEARCH** | Decision/status labels defined in [decision.md](../../decision.md). |
