# Neural Volatility Surface Forecasting Lab
## Project Master Plan — Mapping Phase

**Project status:** Planning and architecture only  
**Implementation status:** Not started  
**Primary objective:** Design a research-grade web application that builds implied-volatility surfaces from options data, forecasts how those surfaces may evolve, evaluates forecast quality, and presents the results through interactive 2D and 3D visualizations.

> **Important:** This is a research and educational analytics platform, not investment advice or a trading recommendation engine. Forecasts are uncertain, market data may be delayed or incomplete, and all results must be evaluated against simple baselines.

---

## 1. Project Vision

The Neural Volatility Surface Forecasting Lab studies how the implied volatility of options changes across **strike price** and **time to expiration**, and whether a neural time-series model can forecast those changes.

The application should feel like a professional quantitative-research terminal rather than a basic student dashboard. It should make the complete workflow inspectable: source data, cleaning, option-price validation, implied-volatility calculation, surface construction, feature engineering, model training, evaluation, uncertainty, and limitations.

### Core question

Given the option market observed at time *t*, how accurately can a model forecast the implied-volatility surface at a future horizon, such as the next trading day?

### Main deliverables

1. Historical options-data ingestion and validation pipeline.
2. Implied-volatility calculation and surface-construction engine.
3. Research dataset and feature-engineering pipeline.
4. Neural forecasting model with strong statistical baselines.
5. Backtesting and model-evaluation framework.
6. Interactive 3D surface explorer and forecast comparison.
7. Research dashboard explaining model behavior and forecast errors.
8. Reproducible experiment tracking and documentation.

---

## 2. Scope and Boundaries

### In scope

- Historical option-chain ingestion for a clearly defined underlying and market.
- Calls and puts, strikes, expirations, bid/ask quotes, last prices where available, volume, and open interest.
- Underlying price and timestamp alignment.
- Interest-rate and dividend assumptions where relevant to pricing.
- Implied volatility (IV) calculation from valid option quotes.
- Surface construction across moneyness/strike and maturity.
- Data quality checks and missing-data handling.
- Forecasting one or more future horizons.
- Baseline and neural-model comparisons.
- Walk-forward evaluation without future-data leakage.
- Interactive visualizations and exportable research results.
- Explicit warnings about data limitations and model uncertainty.

### Out of scope for the initial version

- Automated trade execution.
- Personalized investment advice.
- Claims of guaranteed profitable forecasts.
- Unrestricted scraping of sites whose terms prohibit it.
- Using live exchange feeds without the required license or permission.
- Treating every observed option quote as a reliable executable price.

### Initial market choice

Choose one market and one underlying universe for the first milestone. For example, US-listed equity or index options may be used if an appropriate data source and its licensing are available. Do not assume free access to complete historical option chains or real-time OPRA data. Source coverage, timestamps, adjustment policies, cost, and redistribution rights must be checked before implementation.

---

## 3. Key Concepts

### Option chain

An option chain lists contracts for an underlying asset. Each contract has a strike price, expiration date, call/put type, and market observations such as bid, ask, volume, and open interest.

### Implied volatility

Implied volatility is the volatility value that makes an option-pricing model's theoretical price match an observed option price. It is inferred from price; it is not directly observed.

### Volatility surface

A volatility surface represents implied volatility across two dimensions:

- **Strike or moneyness:** where the option strike lies relative to the underlying price.
- **Maturity:** how much time remains until expiration.

The third dimension, or color scale, represents implied volatility. In practice, the surface is sparse and noisy, so data validation and carefully documented interpolation are essential.

### Forecasting target

The target is not the underlying asset's future price. The target is the future implied-volatility surface, or a representation of that surface, at a defined forecast horizon.

A sensible first target is the next trading day's surface at standardized moneyness and maturity coordinates. This makes comparisons across dates more meaningful than using raw strike prices alone.

---

## 4. Users and Research Questions

The primary user is a quantitative researcher or developer who wants to understand and test volatility forecasting methods.

The platform should help answer:

- How does the volatility smile/skew differ by maturity?
- How stable are surface shapes from one day to the next?
- Which regions of the surface are hardest to forecast?
- Does the neural model outperform persistence and statistical baselines?
- How do results change in calm versus high-volatility regimes?
- Are forecast errors concentrated around earnings, macroeconomic events, or market stress?
- Does the model produce smooth, plausible surfaces?
- Do any forecasts violate basic option-price or no-arbitrage sanity checks?
- How sensitive are results to data quality, quote filters, and interpolation choices?

---

## 5. System Architecture

The platform should be divided into independently testable layers.

```text
Approved Data Sources
        |
        v
Data Ingestion and Source Metadata
        |
        v
Raw Data Store (immutable snapshots)
        |
        v
Validation, Cleaning, and Quote Filtering
        |
        v
Underlying / Rates / Dividends Alignment
        |
        v
Implied-Volatility Solver
        |
        v
Surface Construction and Standardization
        |
        v
Feature Engineering and Dataset Versioning
        |
        v
Baseline Models + Neural Forecasting Models
        |
        v
Walk-Forward Evaluation and Diagnostics
        |
        v
Forecast Store + Model / Experiment Registry
        |
        v
API / Query Layer
        |
        v
Research Dashboard + Interactive 3D Surface Viewer
```

### Architectural principles

- Keep raw source observations separate from cleaned and derived data.
- Preserve source timestamps and ingestion timestamps.
- Make every transformation reproducible and versioned.
- Keep data processing, model training, inference, and visualization separate.
- Record assumptions rather than hiding them in code.
- Do not allow the frontend to perform heavy model training.
- Make historical backtests reproducible from saved data and configuration.
- Build a useful historical-data mode before attempting live updates.

---

## 6. Data Sources and Data Governance

The first technical decision is the data provider. Compare options before choosing one.

Potential categories include:
- Licensed market-data vendors with historical option-chain snapshots.
- Broker APIs, subject to account access, history limits, and terms.
- Academic or research datasets with documented coverage.
- Public datasets for prototyping, provided the schema and usage rights are suitable.

For every candidate source, document:

| Requirement | Questions to answer |
|---|---|
| Coverage | Which underlyings, contracts, exchanges, and dates are included? |
| Granularity | End-of-day snapshots, intraday snapshots, or streaming updates? |
| Quote fields | Bid, ask, sizes, last, volume, open interest, Greeks, IV? |
| Timestamps | Exchange time, timezone, quote timestamp, snapshot timestamp? |
| Adjustments | How are splits, dividends, symbol changes, and adjusted contracts handled? |
| Historical depth | How far back does the data go? |
| Reliability | What are the known gaps and correction policies? |
| Licensing | Can the data be stored, displayed, and redistributed? |
| Cost and limits | What are the subscription, API, and rate-limit constraints? |

### Data-source rule

Do not label data as “live” unless the provider actually supplies sufficiently current data and its latency is known. Clearly distinguish **historical**, **delayed**, **latest available**, and **real-time licensed** data.

---

## 7. Data Model

A normalized conceptual schema should include the following entities.

### Underlying snapshot

- Underlying identifier
- Timestamp and timezone
- Last or reference price
- Source
- Market-session status, if available

### Option quote

- Contract identifier
- Underlying identifier
- Quote timestamp
- Call/put
- Strike
- Expiration
- Bid and ask prices
- Bid/ask sizes, if available
- Last price, if available
- Volume and open interest, if available
- Contract multiplier and adjustment metadata
- Source and data-quality flags

### Market assumptions

- Risk-free rate curve or selected rate assumption
- Dividend yield, known dividends, or documented dividend model
- Day-count convention
- Pricing-model assumptions

### Derived IV observation

- Contract identifier and source timestamp
- Mid-price and quote-selection method
- Calculated IV
- Solver status and iteration count
- Pricing model
- Input assumptions
- Quality flags

### Surface snapshot

- Snapshot timestamp
- Underlying price
- Coordinate system: strike, log-moneyness, or forward moneyness
- Time-to-expiration convention
- Grid coordinates and IV values
- Observed-versus-interpolated mask
- Construction method and version

### Forecast and experiment

- Forecast origin time and target horizon
- Model name, version, and configuration
- Input-data snapshot/version
- Forecast grid and values
- Uncertainty estimates, if available
- Baseline results and evaluation metrics
- Reproducibility metadata

---

## 8. Data Ingestion and Quality Pipeline

Each data snapshot should pass through explicit checks before it is used.

1. **Ingest:** retrieve data through an approved provider interface.
2. **Preserve raw input:** save the original response or normalized raw records with source metadata.
3. **Normalize:** standardize field names, units, timezones, contract identifiers, and missing-value representation.
4. **Deduplicate:** identify repeated records using contract, timestamp, and source rules.
5. **Validate quotes:** flag negative prices, crossed markets, zero or implausible bid/ask values, stale timestamps, and inconsistent contract metadata.
6. **Align underlying:** associate the option quote with an appropriate underlying reference price and timestamp.
7. **Check market calendar:** handle holidays, weekends, early closes, and expiration conventions.
8. **Create quality flags:** preserve why a quote was retained, excluded, or down-weighted.
9. **Publish a dataset version:** make the processed snapshot reproducible.

Do not silently discard bad records. Retain a record of exclusions and report how many observations were affected.

### Quote-selection policy

The bid/ask midpoint is a common starting point, but it is not always reliable, especially for illiquid options. Define a configurable policy for minimum quote quality, spreads, staleness, and zero bids. Compare reasonable filtering choices in sensitivity analysis.

---

## 9. Implied-Volatility Calculation

The IV engine is a central scientific component and should be independently tested.

### Proposed process

1. Select an eligible option quote using the documented quote policy.
2. Compute the selected market price, often the midpoint of bid and ask.
3. Determine time to expiration using the selected calendar and day-count convention.
4. Supply underlying price, strike, interest-rate assumptions, dividend assumptions, and option type.
5. Select the pricing model appropriate to the instrument and assumptions.
6. Solve for volatility numerically.
7. Check solver convergence and whether the market price is within valid theoretical bounds.
8. Save the IV, solver diagnostics, inputs, and quality flags.

### Numerical methods

A bracketed method such as Brent's method is a robust starting point when a valid root can be bracketed. Newton-style methods can be faster but need sensible safeguards. The implementation should define bounds, convergence tolerances, and failure statuses.

### Important edge cases

- Very short time to expiration.
- Deep in-the-money or deep out-of-the-money contracts.
- Tiny or zero bids.
- Wide bid/ask spreads.
- Invalid or stale prices.
- Prices outside theoretical bounds.
- Rates, dividends, or exercise style inconsistent with the chosen model.
- American-style options where a simple European Black–Scholes assumption may be inappropriate.

The system must not fabricate IV when the solver fails. Store a missing value and a clear reason.

---

## 10. Surface Construction

A raw option chain is irregular: strikes and expirations differ, and many grid points may be missing or unreliable.

### Coordinate choices

- **Raw strike:** intuitive but changes meaning as the underlying price changes.
- **Moneyness:** strike relative to underlying price.
- **Log-moneyness:** commonly expressed as `ln(K / S)` or a forward-based equivalent.
- **Maturity:** time remaining to expiration, in years or a documented unit.

For comparing surfaces across dates, use a standardized coordinate system such as log-moneyness and time to maturity, with the exact convention recorded.

### Construction steps

1. Group eligible IV observations by snapshot.
2. Convert strikes and expirations to standardized coordinates.
3. Remove or flag unreliable observations.
4. Apply a documented interpolation method only where justified.
5. Keep observed values distinguishable from interpolated values.
6. Avoid extrapolating far beyond observed strikes or maturities without explicit warnings.
7. Save both the original observations and the standardized surface grid.
8. Generate quality summaries for sparse areas and unstable regions.

### Candidate methods

- Nearest-neighbor or linear interpolation for transparent initial baselines.
- Shape-preserving interpolation where appropriate.
- Spline-based approaches with smoothness controls.
- Parametric volatility-smile/surface fits as a comparison.
- More advanced arbitrage-aware parameterizations as a later research milestone.

Interpolation is not new market data. The UI should visibly distinguish observed, interpolated, and unavailable regions.

---

## 11. Feature Engineering

Feature engineering must use only information that would have been available at the forecast origin.

### Surface-derived features

- IV at standardized moneyness/maturity grid points.
- ATM implied volatility by maturity.
- Put-side and call-side skew measures.
- Smile curvature.
- Term-structure slope.
- Changes in IV from previous sessions.
- Rolling realized volatility, computed without future observations.
- Surface-level summaries such as average level, skew, and curvature.

### Market-context features

Where reliable data is available:
- Underlying returns and realized volatility.
- Volume and open-interest summaries.
- Bid/ask spread and quote-quality measures.
- Trading-session and calendar features.
- Interest-rate and dividend inputs.
- Broad market volatility indicators.
- Event-calendar flags, only from timestamped sources available at the time.
- Liquidity and market-regime indicators.

### Feature governance

- Store feature definitions and versions.
- Fit scalers and transformations on training data only.
- Handle missingness explicitly.
- Prevent target leakage from future prices, future Greeks, or revised data unavailable at the time.
- Perform ablation tests to measure whether feature groups actually help.

---

## 12. Forecasting Targets and Horizons

Start with one clear target: forecast the next valid trading session's standardized IV surface.

Later horizons may include:
- Next-session surface.
- Several trading sessions ahead.
- Multiple horizons predicted separately or jointly.

Possible output representations:

1. **Grid forecasting:** predict IV at each standardized grid point.
2. **Surface-factor forecasting:** reduce the surface to latent factors and forecast the factors.
3. **Parametric forecasting:** predict parameters of a fitted volatility surface.
4. **Change forecasting:** predict changes from the latest surface rather than absolute IV.

The initial version should compare at least grid forecasting with a lower-dimensional representation. A lower-dimensional model can be more stable when historical data is limited.

---

## 13. Modeling Strategy

A neural network should not be assumed to be better merely because it is more complex. Establish simple baselines first.

### Baseline models

- **Persistence:** tomorrow's surface equals today's surface.
- **Historical average/change:** predict using a training-only historical reference.
- **Linear or regularized regression:** predict grid changes or surface factors.
- **Statistical time-series model:** where the target representation supports it.
- **Parametric surface baseline:** forecast the parameters of a conventional surface fit.

### Neural model candidates

- **Multilayer perceptron (MLP):** useful for a first model on engineered lagged features.
- **Temporal convolutional network (TCN):** captures local temporal patterns.
- **LSTM/GRU:** sequence models for historical surface and context features.
- **Transformer-style time-series model:** consider only if data volume, diversity, and compute justify the complexity.
- **Autoencoder plus temporal model:** encode the surface into a lower-dimensional latent representation, forecast the latent factors, and decode back to a surface.

### Recommended experiment order

1. Validate the target and persistence baseline.
2. Build a simple regression model.
3. Train an MLP on lagged surface and context features.
4. Test a TCN or GRU if the dataset supports sequence learning.
5. Test latent-factor forecasting if grid dimensionality is high.
6. Evaluate model complexity against out-of-sample improvement, stability, and runtime.

Use PyTorch or another selected framework consistently. Record random seeds, dependency versions, training dates, hyperparameters, and hardware where relevant.

---

## 14. Training, Validation, and Backtesting

Financial time series must be evaluated chronologically.

### Data splitting

- Train on the earliest period.
- Validate on a later period for model selection.
- Test on a final untouched period.
- Use walk-forward or rolling-origin evaluation for repeated historical forecasts.
- Ensure that all features and preprocessing parameters are derived only from data available before each forecast.

Never randomly shuffle dates across train and test sets for the primary time-series evaluation.

### Evaluation metrics

Use several complementary metrics:

- MAE for average absolute IV error.
- RMSE to penalize larger errors.
- Error in volatility points, clearly distinguished from decimal IV.
- Error grouped by maturity and moneyness.
- Directional accuracy for changes, if direction is a defined target.
- Performance relative to persistence and other baselines.
- Coverage and calibration metrics for prediction intervals, if uncertainty is estimated.
- Error and stability during different market regimes.

Do not rely on a single aggregate score. Show per-region results and sample counts, and disclose missing or excluded grid cells.

### Robustness checks

- Compare multiple historical periods.
- Evaluate calm and stressed market regimes.
- Test different quote filters and interpolation policies.
- Measure performance on liquid versus less-liquid regions.
- Check whether results depend on a small number of dates or contracts.
- Run feature ablations.
- Report failure cases as well as successful examples.

---

## 15. Model Explainability and Research Diagnostics

The research layer should explain what was tested and how conclusions were reached, without presenting explanations as proof of causality.

Recommended views:
- Feature correlation heatmap.
- Feature importance for suitable model types.
- SHAP-style explanations where computationally and methodologically appropriate.
- Feature-ablation comparison.
- Predicted-versus-observed IV plots.
- Residual distribution and residual-over-time plots.
- Error heatmap across moneyness and maturity.
- Forecast errors by volatility regime.
- Learning curves and training/validation loss.
- Hyperparameter and experiment comparison.
- Forecast interval coverage and calibration, if intervals are produced.
- Data-quality and exclusion diagnostics.

For correlated features, feature importance can be unstable. Clearly state the method and its limitations.

---

## 16. Interactive 3D and 2D Experience

The visual interface is a major part of the product, but every visualization must remain scientifically interpretable.

### A. 3D Volatility Surface Explorer

Display implied volatility as a 3D surface:
- X-axis: standardized moneyness or strike.
- Y-axis: time to expiration.
- Z-axis and/or color: implied volatility.

Interactions:
- Rotate, pan, and zoom.
- Hover to inspect exact coordinates, IV, timestamp, and data status.
- Switch between observed and interpolated points.
- Select an expiration or moneyness slice.
- Compare two dates.
- Reset camera and use accessible 2D alternatives.

### B. Actual vs. Forecast Surface

- Show observed and forecast surfaces side by side.
- Provide an overlay mode with clear visual separation.
- Show a difference surface: forecast minus observed.
- Let users choose forecast origin, target date, and model version.
- Clearly label historical backtest results versus genuinely prospective forecasts.

### C. Surface Evolution

Animate surface changes through historical snapshots. The animation must respect chronological order and must not imply that interpolated points are observations.

### D. 2D slices and heatmaps

- Volatility smile at selected maturity.
- Term structure at selected moneyness.
- Error heatmap across maturity and moneyness.
- Quote-quality heatmap.
- Surface-difference heatmap.
- Historical time-series charts for ATM IV, skew, and curvature.

### E. Research charts

- Training and validation loss.
- Baseline/model metric comparison.
- Predicted versus actual scatter plot.
- Residual distribution.
- Error over time.
- Feature importance and correlation.
- Regime-level performance.

### Visualization technology

A web stack may use React with a charting library for 2D charts and Three.js through React Three Fiber for interactive 3D surfaces. The exact stack should be selected during technical design after a small feasibility test.

Performance requirements:
- Downsample or simplify geometry when needed.
- Avoid blocking the interface during data loading.
- Display loading, empty, and error states.
- Keep axes, units, timestamps, and model version visible.
- Provide accessible tables or 2D alternatives for key results.

---

## 17. Application Information Architecture

Suggested primary navigation:

1. **Overview** — latest dataset status, selected underlying, current surface, latest forecast, and data freshness.
2. **Surface Explorer** — 3D surface, slices, date selection, and observed/interpolated status.
3. **Forecast Lab** — forecasts, forecast horizon, baseline comparisons, and uncertainty.
4. **Backtesting** — walk-forward results, error metrics, and regime analysis.
5. **Research & Explainability** — feature diagnostics, residuals, ablations, and experiment comparisons.
6. **Data Quality** — source status, missingness, quote filters, and IV solver failures.
7. **Experiments & Models** — model versions, configurations, training windows, and reproducibility metadata.
8. **Methodology** — assumptions, equations, definitions, limitations, and data-source disclosures.

The interface should use a consistent visual system, clear typography, restrained motion, dark and light themes if feasible, and research-grade chart labels. Avoid visual effects that make numerical comparisons harder.

---

## 18. API and Service Boundaries

The final implementation may use a Python backend for data science and a separate web frontend. The precise framework is a later decision.

Conceptual service boundaries:

- **Data service:** provider integration, source metadata, and snapshot status.
- **IV service:** quote validation, pricing inputs, and IV solver.
- **Surface service:** standardized coordinates, interpolation, and quality masks.
- **Feature service:** reproducible feature generation.
- **Model service:** training, model registry, and inference.
- **Evaluation service:** walk-forward backtests and metrics.
- **Research API:** surface, forecast, experiment, and diagnostics queries.
- **Frontend:** visualization and user interaction.

Possible conceptual endpoints:
- Retrieve available underlyings and dates.
- Retrieve an option-chain snapshot and its quality report.
- Retrieve a surface snapshot.
- Retrieve a forecast by model, origin, and horizon.
- Retrieve evaluation metrics for an experiment.
- Retrieve feature and residual diagnostics.
- Start or inspect a training/evaluation job, subject to access controls.

These are planning-level interfaces, not a finalized API contract.

---

## 19. Storage and Reproducibility

Select storage according to dataset size and query patterns. A relational database can hold metadata, experiment records, and normalized observations; columnar files can be useful for larger analytical datasets. The final choice should follow a small benchmark rather than premature infrastructure complexity.

Every published result should identify:
- Source and source snapshot.
- Data-processing version.
- Quote-filter configuration.
- Pricing and IV methodology.
- Surface-grid and interpolation version.
- Feature version.
- Training, validation, and test windows.
- Model configuration and weights/version.
- Random seed where applicable.
- Evaluation code version.
- Creation timestamp.

Raw data should be immutable where licensing allows. Corrections should create a new version instead of silently changing the data behind a historical result.

---

## 20. Security, Reliability, and Operations

- Keep provider credentials and secrets on the server, never in frontend code.
- Use environment-based configuration and secret management appropriate to the deployment.
- Apply authentication and rate limiting if the application is exposed publicly.
- Validate all external inputs.
- Log ingestion, solver, training, and API failures without exposing secrets.
- Monitor data freshness and provider/API failures.
- Make long-running training jobs asynchronous.
- Cache expensive queries where appropriate.
- Add graceful handling for unavailable data and model failures.
- Respect data-provider licensing and redistribution restrictions.
- Avoid claiming a feed is live when the data is delayed.

---

## 21. Testing Strategy

### Unit tests

- Quote normalization and validation.
- Time-to-expiration calculations.
- Pricing functions and IV solver behavior.
- Invalid price bounds and solver failures.
- Coordinate conversion and surface-grid logic.
- Feature generation and missing-value handling.
- Evaluation metrics.

### Integration tests

- Provider adapter to raw storage.
- Raw data through IV and surface construction.
- Dataset through feature generation and model inference.
- Forecast results through API and frontend visualizations.

### Scientific validation

- Compare IV calculations against trusted reference cases.
- Verify that known synthetic prices recover their generating volatility within tolerances.
- Check chronological splits and prevent leakage.
- Confirm that persistence baseline results are reproducible.
- Verify forecast metrics against hand-calculated examples.
- Check that observed and interpolated points are labeled correctly.
- Test for implausible surface jumps and pricing inconsistencies.

### End-to-end tests

- Select an underlying and date.
- Open the surface explorer.
- Compare actual and forecast surfaces.
- Inspect a grid point's data lineage.
- View backtest metrics and experiment metadata.
- Handle missing data and failed forecast scenarios.

---

## 22. Deployment and Performance

Deployment should follow successful local validation and data licensing review.

Planning requirements:
- Separate frontend and backend configuration.
- Background jobs for ingestion, training, and backtests.
- Scheduled ingestion only at a cadence supported by the data source.
- Versioned model artifacts and reproducible environment definitions.
- Health checks for services and data pipelines.
- Error monitoring and logs.
- Caching for repeated surface queries.
- Resource limits for expensive visualization and model jobs.
- A documented recovery procedure for failed jobs.

The first release should favor a reliable, reproducible historical workflow over a fragile real-time architecture.

---

## 23. Phased Roadmap

### Phase 0 — Research and feasibility

- Select the initial market and underlying.
- Compare data vendors and confirm licensing, history, granularity, and cost.
- Choose forecast horizon and standardized coordinates.
- Define a minimum viable dataset and success criteria.
- Validate that enough clean historical snapshots are available.

**Exit criteria:** written data-source decision, documented scope, and sample data sufficient to test the full analytical path.

### Phase 1 — Data foundation

- Implement the provider adapter.
- Preserve raw snapshots and metadata.
- Normalize and validate option quotes.
- Align underlying prices and pricing assumptions.
- Generate quality reports.

**Exit criteria:** repeatable ingestion and auditable quality checks.

### Phase 2 — Implied volatility and surfaces

- Implement and test the IV solver.
- Record failures and theoretical-bound violations.
- Standardize moneyness and maturity coordinates.
- Construct surfaces with observed/interpolated masks.
- Compare interpolation and filtering policies.

**Exit criteria:** verified IV calculations and reproducible surface snapshots.

### Phase 3 — Research dataset and baselines

- Build lagged surface and contextual features.
- Version datasets and feature definitions.
- Implement persistence and regression baselines.
- Create chronological splits and walk-forward evaluation.
- Establish metrics by surface region.

**Exit criteria:** trustworthy baseline performance with leakage checks.

### Phase 4 — Neural forecasting

- Train the initial MLP or selected neural baseline.
- Compare with persistence and regression.
- Test sequence or latent-factor models only when justified.
- Track experiments and save model artifacts.
- Quantify uncertainty where feasible.

**Exit criteria:** reproducible out-of-sample results and clear evidence of where the neural model helps or fails.

### Phase 5 — Visualization and research UI

- Build the 2D surface slices and heatmaps.
- Add interactive 3D surface rendering.
- Add actual-versus-forecast and difference views.
- Add backtest charts, residuals, and explainability.
- Expose data lineage and model metadata.

**Exit criteria:** users can inspect how a forecast was produced and evaluate it without reading source code.

### Phase 6 — Reliability and release

- Add API validation, authentication where needed, and rate limiting.
- Complete unit, integration, scientific, and end-to-end tests.
- Validate licensing and disclosures.
- Test deployment, logging, and recovery.
- Publish methodology and known limitations.

**Exit criteria:** stable, documented application with reproducible results and honest limitations.

### Phase 7 — Advanced research extensions

Only after the core system is reliable:
- Multi-underlying modeling.
- Multiple forecast horizons.
- More advanced temporal models.
- Probabilistic forecasting and calibrated prediction intervals.
- Arbitrage-aware parameterizations and penalties.
- Regime-conditioned models.
- Intraday surfaces if suitable data is licensed.
- Additional market-context features.
- Model drift and data-quality monitoring.

---

## 24. Definition of Done

The project is not complete merely because a neural network trains or a 3D surface renders.

A credible first release must:
- Ingest documented, permitted data.
- Preserve timestamps and data lineage.
- Calculate IV with tested numerical behavior.
- Clearly distinguish observed, interpolated, and missing regions.
- Construct comparable surfaces across dates.
- Prevent look-ahead leakage in evaluation.
- Compare neural results with simple baselines.
- Report out-of-sample metrics by region and time period.
- Provide useful 2D and 3D visualizations.
- Show model version, forecast origin, horizon, and assumptions.
- Explain failure cases and limitations.
- Reproduce a historical experiment from saved configuration and data versions.

---

## 25. Principal Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Historical option data is expensive or incomplete | Decide provider and scope before committing to the architecture |
| Illiquid quotes produce noisy IV | Use transparent quality filters and sensitivity analysis |
| Surface interpolation creates false structure | Preserve masks and show observed points separately |
| Neural model overfits | Use chronological walk-forward tests and simple baselines |
| Look-ahead leakage inflates results | Enforce timestamp-aware feature generation and preprocessing |
| Apparent performance disappears in stressed periods | Report regime-specific metrics and failure cases |
| Arbitrage violations appear in fitted surfaces | Add explicit diagnostics and advanced constraints as a later phase |
| 3D visuals are impressive but misleading | Keep units, axes, timestamps, data status, and 2D alternatives visible |
| “Live” data is actually delayed | Disclose provider latency and label freshness accurately |
| Data licensing restricts display or storage | Review provider terms before collecting or publishing data |

---

## 26. Final Product Standard

The final product should communicate both quantitative depth and visual clarity. A researcher should be able to move from an attractive 3D surface to the underlying quote, inspect the IV calculation, identify how the surface was constructed, see the model's forecast, compare it against a baseline, and understand the historical evidence supporting or contradicting the result.

**Guiding principle:** make every forecast inspectable, every experiment reproducible, and every limitation visible.

**Current status:** mapping phase only. No implementation, provider selection, model training, or deployment is implied by this document.
