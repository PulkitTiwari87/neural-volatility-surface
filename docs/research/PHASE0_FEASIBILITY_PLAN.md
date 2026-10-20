# Phase 0 Feasibility Plan — Minimum Viable Dataset, Success Criteria, Feasibility Experiment

**Status:** PROPOSED — every threshold below is a *proposal for the owner to confirm or change before it is frozen*. Nothing here has been measured on real data. · **Date drafted:** 2026-10-12 · **Canonical for:** the minimum viable dataset (MVD), Phase 0 and research success criteria, synthetic-sample specification, and the minimal end-to-end feasibility experiment. · **Related:** [DATA_SOURCE_ASSESSMENT](../data/DATA_SOURCE_ASSESSMENT.md) · [EVALUATION_PROTOCOL](EVALUATION_PROTOCOL.md) §7–§8 · [IMPLEMENTATION_PLAN](../../IMPLEMENTATION_PLAN.md) Phase 0 · [decision.md](../../decision.md) DEC-001/003 · Q-02 in [OPEN_QUESTIONS](../planning/OPEN_QUESTIONS.md)

## 0. Pre-registration rules
1. Thresholds in §2–§3 become **frozen** when the owner signs them and the date is recorded (§7). After freezing, they change only by a dated amendment with a reason.
2. Where a threshold depends on an unmeasured quantity (variability of loss differences, serial correlation), the rule says *how it will be set from the pilot*, not a guessed value.
3. No model result (neural or otherwise) may be viewed before §7 is signed.

## 1. Why a sample-size argument is needed
The unit of statistical independence is the **forecast-origin day**, not the number of grid cells (cells within a day are strongly dependent, and consecutive days are serially dependent — [EVALUATION_PROTOCOL](EVALUATION_PROTOCOL.md) §7). So the question "is there enough data to tell a model from persistence?" reduces to the number of **test origins**.

**Illustrative power calculation (assumptions, not measurements).** Let *d_t* be the per-origin difference in loss (persistence − model), and let `c = SD(d_t) / mean(persistence loss)`. For a two-sided 5 % test with 80 % power, treating origins as independent, the number of origins needed to detect a relative improvement *r* is approximately

`N ≈ (2.8 · c / r)²`

and, with first-order serial correlation ρ in *d_t*, multiply by `(1+ρ)/(1−ρ)`.

| c (assumed) | r = 5 % | r = 10 % |
|---|---|---|
| 0.5 | 784 | 196 |
| 1.0 | 3,136 | 784 |

Inverting for a given number of test origins *N*: minimum detectable improvement `r ≈ 2.8·c/√N`. With **N = 600** test origins and c = 1, r ≈ 11 %; with c = 0.5, r ≈ 5.7 %; a serial correlation of ρ = 0.3 inflates these by about 36 % (√1.86). **c and ρ are unknown**; the pilot (§5) estimates them, and the numbers above are shown only to demonstrate the order of magnitude: a few hundred daily test origins can detect only fairly large improvements.

## 2. Proposed minimum viable dataset (MVD)

All items **PROPOSED**; "TBD-pilot" = set from the pilot before freezing.

| # | Dimension | Proposed requirement | Rationale |
|---|---|---|---|
| M1 | Universe | One underlying (proposed: S&P 500 index options, DEC-001), one data source, one snapshot definition | MP §2 one market/universe |
| M2 | Snapshot | One fixed daily snapshot time, identical definition across the whole history (e.g., 15:45 ET) | Comparable surfaces; MP §12 next-session target |
| M3 | History length | ≥ 2,000 daily snapshots in total, with ≥ 95 % of scheduled trading days present and no unexplained gap longer than 5 consecutive trading days | Allows roughly 600 test origins plus training/validation windows; **floor, not a guarantee of power** (§1) |
| M4 | Test origins | ≥ 600 walk-forward test origins that are never used for selection, **or** the number implied by the pilot-measured *c* and ρ for the minimum improvement r* the owner cares about, whichever is larger. If the available data gives fewer, the neural-vs-baseline comparison is labelled *underpowered* in advance | §1 |
| M5 | Regime coverage | History includes ≥ 2 distinct volatility regimes and ≥ 1 stress episode, identified by a pre-registered rule using only the underlying's own past data (rule TBD-pilot; e.g., trailing realized volatility percentile) | MP §14 regimes; SCI-006 |
| M6 | Per-snapshot density | On the proposed coarse grid (grid fixed in the pilot, e.g., ~7 maturities × ~9 forward-log-moneyness nodes), median share of grid nodes with `observed` status ≥ TBD-pilot (**proposed starting target 60 %**) and 5th-percentile ≥ TBD-pilot | Sparse surfaces would make evaluation mostly interpolation |
| M7 | Quote fields | For every retained quote: bid, ask, strike, expiration, option type, a snapshot timestamp, and an underlying/forward reference obtainable at the snapshot | MP §7 |
| M8 | Quote quality | After the quote policy, ≥ TBD-pilot % of snapshots have enough eligible quotes to produce ≥ the density in M6; share of zero-bid / crossed / stale quotes measured and reported | MP §8 |
| M9 | Reference data | Rate source and a forward/dividend method identified for **every** date in the history, with a documented timestamp relation to the snapshot | MP §9 |
| M10 | Licence | Written licence conclusion covering the intended use (storage, internal analysis, any display, any publication) for the full history | DATA-002 |
| M11 | Reproducibility | Raw files stored locally and hashed; a second extraction/pull yields identical content or a new explicit version | DATA-004 |
| M12 | Exercise style | Exercise style and settlement of every included contract known from specifications and consistent with the pricing model (DEC-004) | MP §9 |

**MVD verdict rule:** the MVD is *met* only if M1–M12 are each evidenced; any shortfall produces an explicit *re-scope* decision (different source/underlying/history, or reduce claims), never silent acceptance.

## 3. Proposed success criteria

### 3.1 Phase 0 feasibility criteria (pipeline can work; no model quality claims)
| # | Criterion | Measure | Pass |
|---|---|---|---|
| S1 | Licence | Written conclusion per [DATA_GOVERNANCE](../data/DATA_GOVERNANCE.md) §3 for the intended use | All eight checklist items answered; blockers listed |
| S2 | MVD | §2 checklist | Met, or re-scope recorded |
| S3 | Conservation | On the pilot sample, `ingested = retained + excluded` per snapshot | 100 % of snapshots |
| S4 | Known-answer IV | Synthetic world: IV recovered from noise-free mid prices | Max absolute error within the solver tolerance that Phase 2 will fix; value **recorded**, tolerance not invented here |
| S5 | Real-sample IV | Share of eligible quotes with `CONVERGED` status, status counts by reason | Reported; investigate if below TBD-pilot (**proposed 90 %**); failures never filled |
| S6 | Surface | Every cell has a status; observed cells trace to quotes; rebuild yields an identical hash | 100 % |
| S7 | Persistence | Persistence forecasts and metrics computed twice give identical results | Exact equality |
| S8 | Sanity of pipeline | In the synthetic *random-walk* world the persistence baseline cannot be beaten by any honest predictor; in the *AR* world an oracle AR predictor beats persistence by the analytically implied margin | Within the sampling interval (§4.3) |
| S9 | Pilot variability | Estimate *c* (SD of per-origin loss differences ÷ mean persistence loss) and ρ from the pilot or synthetic analogue, and compute the implied power table for the real MVD | Reported with uncertainty; feeds M4 |

### 3.2 Research success criteria (pre-registered for Phases 3–4; PROPOSED)
- **Primary comparison:** neural model vs **persistence**, with regression reported alongside, on **identical origins and observed target cells**.
- **Primary metric:** MAE of IV on observed target cells, computed in decimal and reported in vol points; unit of inference = origin day.
- **Evidence rule:** the 95 % interval for the mean per-origin MAE difference (block-bootstrap or equivalent chosen in Phase 3, Q-08) excludes zero in favour of the neural model **and** the point estimate is a relative reduction of at least **r\*** (proposed 3 %, to be revised after S9 so that r\* is detectable with the available N; if r\* is below the minimum detectable effect, the study is declared underpowered in advance).
- **Outcomes that are all acceptable and reported:** neural better / no detectable difference / persistence better / mixed by region or regime.
- **Secondary (exploratory, labelled as such):** by maturity × moneyness region, by regime, calm vs. stress, liquid vs. less liquid, ablations.
- **Guardrails:** GR-LEAK-01…06, GR-MOD-01…06 hold; test window opened once per frozen configuration.

## 4. Synthetic sample (labelled; the default if no permitted real sample exists)

A real, permitted sample has **not** been obtained ([DATA_SOURCE_ASSESSMENT](../data/DATA_SOURCE_ASSESSMENT.md) §9). The synthetic alternative below is specified here; building it is a Phase 0 spike and requires the owner's go-ahead because it is code.

### 4.1 Labelling
Every synthetic file is named `*.synthetic.*`, carries `origin = synthetic` in every record, and a header stating "SYNTHETIC — not market data". Synthetic data is **never** used to claim anything about markets (GR-DATA-04).

### 4.2 Generator specification (conceptual)
- **Underlying:** geometric random walk with constant drift/vol for the spot path; constant risk-free rate and continuous dividend yield (so the forward is known exactly).
- **Surface:** IV(k, T) = level_t + slope_t·k + curvature_t·k² + term_t·g(T), with factors (level, slope, curvature, term) evolving over days under two **worlds**:
  - **W-RW:** each factor is a random walk → persistence is the optimal one-step predictor of the surface *in expectation*.
  - **W-AR:** each factor is a mean-reverting AR(1) with known φ < 1 and noise → the optimal predictor and the expected improvement over persistence are analytically computable.
  Parameters are chosen so IV stays in a plausible positive range; exact values are recorded in the generating config (hashed).
- **Chain:** European prices from the Black–Scholes–Merton / forward form (IV_METHODOLOGY §3) on an irregular strike/expiry set with randomly missing strikes (known sparsity).
- **Quotes:** bid/ask around the true price with a spread that depends on vega and moneyness; **injected defects with known counts** (crossed, zero-bid, negative, duplicates, stale-timestamp, wide-spread, out-of-bound prices).
- **Size:** ~500 days for fast iteration; larger runs for power-table checks.
- **Ground truth retained:** true σ per quote and the true surface per day.

### 4.3 What the synthetic worlds can and cannot show
They can show that the pipeline conserves records, recovers known volatilities, preserves masks, reproduces results, and neither invents nor hides improvement. They cannot show anything about real-market data quality, liquidity, or whether a neural model helps on real surfaces.

## 5. Minimal end-to-end feasibility experiment

**Goal:** run the *entire* analytical path once, end to end, on either the synthetic sample (always) or a permitted real sample (when available), and record what breaks. Scope is deliberately tiny: no neural model, no hyper-parameter search, no UI.

| Step | Input | Operation | Output | Checks |
|---|---|---|---|---|
| F0 | Sample files (hashed) | Ingest as raw; record metadata (source, snapshot time, ingestion time, `origin`) | Raw snapshot IDs | Hash stable; second ingest identical |
| F1 | Raw | Normalize; validate quotes with the proposed policy ([QUOTE_QUALITY_POLICY](../data/QUOTE_QUALITY_POLICY.md)); flag/exclude with reason codes | Quote table + exclusion log + quality report | S3 conservation; injected-defect counts match exactly (synthetic) |
| F2 | Quotes + reference data | Align forward/rate per expiry; compute time to expiry under the draft convention | Aligned quotes | Timestamp relation recorded; unalignable quotes flagged |
| F3 | Aligned quotes | Compute IV with bounded solver; store status/diagnostics | IV observations | S4/S5; no IV for out-of-bound prices |
| F4 | IV observations | Map to forward log-moneyness × maturity on the pilot grid; assign cell status (`observed`/`interpolated`/`extrapolated`/`missing`) using the simplest transparent method inside the observed hull | Surface per day + coverage stats | S6; no cell mislabelled |
| F5 | Surfaces | **Persistence forecast** for origin *t* → target *t+1* on the grid | Forecast surfaces | S7 |
| F6 | Forecast vs realized | MAE, RMSE (decimal and vol points) on cells **observed at t+1**; report separately (a) cells observed at both *t* and *t+1*, (b) cells observed at *t+1* but interpolated at *t*; counts `n`, `n_missing`; per maturity × moneyness bucket | Error tables | Sample counts present; no cell dropped silently |
| F7 | Per-origin losses | Estimate *c*, ρ, implied power (S9) | Power table | Uncertainty shown |
| F8 | Everything | Write a run record ([EXPERIMENT_TEMPLATE](../templates/EXPERIMENT_TEMPLATE.md)) including versions, seeds, exclusions, failures | Run record | Reproduces from the record |

**Real-sample variant (only if permitted data is in hand):** ≥ 20 snapshot dates chosen *before looking at results* by a stated rule — at least 5 in calm periods, at least 3 in high-volatility periods, and at least 2 pairs of consecutive trading days (so F5–F6 can run); the dates and the selection rule are recorded. Additionally measure per date: contracts per snapshot, strikes per expiry, share zero-bid/crossed/stale, timestamp gaps, whether SPX/SPXW (or the chosen root) and all expected expiries are present.

**Failure handling:** every failure (parse error, missing field, solver failure) is logged and counted, not patched over; the experiment's purpose is to find them.

## 6. Resources and approvals needed (owner)
- ~~Go-ahead to write the synthetic generator and pilot scripts~~ — **given by the owner on 2026-10-12** (toolchain: [ADR-0003](../architecture/ADR/ADR-0003-phase0-spike-toolchain.md); protocol: §9).
- A decision on obtaining a real sample (accounts, terms acceptance, any spend) — see [DATA_SOURCE_ASSESSMENT](../data/DATA_SOURCE_ASSESSMENT.md) §10.
- DEC-015 toolchain choice before any code is written.

## 7. Freeze record (to complete)
```
MVD thresholds frozen on: 2026-10-20   by: project owner (in chat, "Adopt the PROPOSED ones")
  Frozen as owner-adopted (NOT evidence-based): M1-M5, M7, M9, M11, M12 as written in section 2, and the
  starting M6 target of 60 % observed nodes (M3: >= 2,000 snapshots, >= 95 % of trading days, no gap > 5 days;
  M4: >= 600 never-selected test origins or the pilot-implied number, whichever is larger).
  Still open: every "TBD-pilot" value (regime rule M5, M6 5th percentile, M8 share, c, rho). M10 (licence) is UNMET.
Amendments: 2026-10-20 the hosted dataset is no longer authorized (DEC-002), so no real data exists against which
  the MVD can be evidenced; the real-data track stays BLOCKED.
Pilot-derived values (c, ρ, density targets, regime rule): ____ (no pilot possible without an authorized sample)
Primary comparison & r*: ____
Signed before any model result was viewed: yes / no
```

## 8. Validation of this plan
Reviewed by the owner; each criterion is a testable statement; S4/S8 are verifiable on synthetic data with known answers; M-items map to evidence in the assessment document. Open items: regime rule (Q-07), statistical comparison method (Q-08), grid design (DEC-006).

## 9. Execution protocol for the synthetic experiment — PRE-REGISTERED 2026-10-12

**Everything in this section was written before any spike code existed or was run.** It is **SYNTHETIC**: no real market data, provider, or account is involved. Authorization: owner instruction of 2026-10-12. Toolchain: [ADR-0003](../architecture/ADR/ADR-0003-phase0-spike-toolchain.md) (Python 3.12.6, standard library only, `unittest`). Code: `scripts/phase0_synthetic/` (disposable spike). **Results:** [PHASE0_SYNTHETIC_RESULTS](PHASE0_SYNTHETIC_RESULTS.md), recorded whatever the outcome. If a pre-registered check fails it is reported as failed; any later re-analysis is labelled *post hoc*; seeds are never re-drawn to obtain a preferred result.

### 9.1 Generating assumptions (frozen)
| Item | Value |
|---|---|
| Instrument | European options on a forward, priced by the Black-76 form; constant rate `r = 0.02`; dividend yield `q = 0.01` (only used to generate the forward `F = S·e^{(r−q)T}`) |
| Spot | `S₀ = 100`; daily log-return sd `0.01`; independent of the volatility factors |
| Maturities (years) | `(30, 60, 91, 182, 273, 365) / 365` — the same six every day |
| True IV | `IV(k,T) = L + S·k + C·k² + g(T)`, `k = ln(K/F)`, `g(T) = 0.03·(√T − 0.7)` (fixed, assumed known to the factor forecaster) |
| Factors `x = (L, S, C)` | means `μ = (0.22, −0.30, 0.40)`; innovation sd `σ = (0.002, 0.010, 0.020)`; Box–Muller normals from `random.Random(seed).random()` |
| **World RW** | `x_{t+1} = x_t + σ·ε`, start at `μ` (random walk → persistence is the Bayes-optimal one-step predictor of every factor) |
| **World AR** | `x_{t+1} = μ + φ(x_t − μ) + σ·ε`, `φ = 0.5` for all three factors, start from the stationary distribution (sd `σ/√(1−φ²)`) → known predictable component |
| Chain | strikes at `k ∈ {−0.30, −0.275, …, +0.30}` (25 values) each kept with probability 0.8, plus 3 random off-grid strikes per expiry with `k ~ U(−0.25, 0.25)`; a strike is listed only if its true OTM price ≥ 0.05; both call and put quoted at every listed strike |
| Quotes (clean mode) | bid/ask symmetric around the exact true price, half-spread `max(0.005, 0.02·P)`; no rounding |
| Quotes (noise mode, exploratory) | same, with bid rounded down and ask rounded up to a 0.01 tick |
| Injected defects | each quote independently with probability 0.02; type uniform among `NEGATIVE_PRICE, CROSSED_MARKET, ZERO_BID, MISSING_FIELD, DUPLICATE` and (OTM-side only) `ABOVE_UPPER_BOUND`; ground-truth counts kept in a ledger the validator never sees |
| Grid | `k` nodes `−0.20…+0.20` step `0.05` (9) × the six maturities (54 cells) |
| Solver (spike values; not adopted for the product) | bracket `[1e-6, 5.0]`, Brent, `xtol = 1e-12`, `max_iter = 200` |
| Surface rules | cell `observed` iff an eligible IV observation lies within `1e-6` of the node in `k` (clean mode); `interpolated` iff inside the observed hull of that maturity and the bracketing gap ≤ `0.15`; otherwise `missing`; **extrapolation is disabled** |
| Forward & rate | forward inferred per expiry from put–call parity (median of the three strikes with the smallest `|C−P|`); rate known (constant) — Q-06 is tested on synthetic data only |
| Quote selection | OTM side only (put if `K < F̂`, else call), price = bid/ask midpoint |

### 9.2 Forecasters and evaluation (frozen)
- **Persistence:** forecast for day *t+1* = surface at day *t* (cells that are `missing` at *t* have no persistence forecast).
- **Factor-AR1 (honest, walk-forward):** at origin *t*, extract `(L,S,C)` by least squares from the `observed` cells of each past day ≤ *t* (the term shape `g(T)` is assumed known), fit AR(1) per factor on days ≤ *t* only (≥ 30 pairs), forecast the factors, rebuild the surface.
- **Oracle-AR (diagnostic upper bound; synthetic only):** uses the true `μ` and `φ` on the extracted factors; with `φ = 1` it is persistence.
- **Walk-forward:** minimum history 60 days; origins `t = 59 … N−2`; the target is the realized constructed surface at *t+1*.
- **Comparable cells:** cells `observed` at *t+1* **and** forecast by *every* compared forecaster. `n_missing` counts target-observed cells that are not comparable. **Group A** = comparable cells also `observed` at *t* (exact analytic checks); **Group B** = cells `interpolated` at *t*.
- **Metrics:** MAE and RMSE on decimal IV and in vol points; `n` cells, `n_origins`, `n_missing`; by maturity bucket (≤ 91d, 182d, ≥ 273d) and moneyness bucket (`k < −0.05`, `|k| ≤ 0.05`, `k > 0.05`).
- **Per-origin loss:** mean squared error over that day's comparable cells. **Inference:** `d_t = loss_persistence,t − loss_model,t`; moving-block bootstrap of `mean(d)`, block length 5, `B = 2000`, 95 % percentile interval, bootstrap seed = world seed + 1. **"Improvement detected" ⇔ interval lower bound > 0.**

### 9.3 Analytic expectations (for hand-checking)
For a Group A cell at moneyness `k`, persistence error `= ΔL + ΔS·k + ΔC·k²` (exact when IV is recovered exactly), so
`E[e²] = κ·(σ_L² + σ_S²·k² + σ_C²·k⁴)`, with `κ = 1` in World RW and `κ = 2/(1+φ)` in World AR (stationary). An oracle AR forecaster has error variance `σ_L² + σ_S²k² + σ_C²k⁴` in World AR, so
**oracle MSE / persistence MSE = (1+φ)/2 = 0.75** for `φ = 0.5` (RMSE ratio ≈ 0.866). A fitted AR forecaster should land slightly above these ratios because of estimation error.

### 9.4 Hypotheses, pass criteria and seeds (frozen)
| ID | Hypothesis | Pass criterion | Seed(s) |
|---|---|---|---|
| H-S1 | IV recovery: observed cells equal the generating IV | `max |IV_est − IV_true| ≤ 1e-8` over all `observed` cells (clean, full pipeline) | tests: RW 20261012, AR 20261013 |
| H-S2 | Validation conserves and detects injected defects | per day `ingested = retained + excluded`; detected counts per defect type **equal** injected counts exactly; solver `PRICE_ABOVE_UPPER_BOUND` count = injected above-bound defects that reached the solver | same |
| H-S3 | Status honesty | every `observed` cell has a node-aligned eligible observation; every `interpolated` cell is inside its slice hull with gap ≤ 0.15; no cell is extrapolated | same |
| H-S4 | **Persistence is appropriate in World RW** and is not artificially beaten | honest factor-AR1 is **not** detected better than persistence on the pre-registered seed; oracle with `φ=1` equals persistence on observed cells to `1e-9`; **study:** false-positive rate ≤ 2 of 10 seeds | tests: 20261012; study: 20261100…20261109 |
| H-S5 | **Known predictability is detected in World AR** | factor-AR1 detected better than persistence on the pre-registered seed; realized MSE ratio (AR1/persistence) in `[0.65, 0.90]`; oracle ratio in `[0.63, 0.87]`; **study:** detection in ≥ 9 of 10 seeds | tests: 20261013; study: 20261100…20261109 |
| H-S6 | Hand-checkable persistence error | Group A grid-weighted persistence MSE within ±15 % of the analytic expectation (§9.3) using the realized comparable-cell `k` values | tests: both seeds |
| H-S7 | Chronological evaluation | a forecaster that reads day > *t* raises `LookaheadError`; predictions at origin *t* are unchanged when all days > *t* are altered | unit tests |
| H-S8 | Reproducibility | same seed ⇒ identical data hash and identical metrics hash (12-dp rounding); different seed ⇒ different data hash | unit tests |
| H-S9 | (exploratory) Noise degrades gracefully | noise mode (tick 0.01, node tolerance `5e-4`): median `|IV_est − IV_true|` reported; loose bound `< 0.01` | 20261012, small config |

Unit tests use a **fast configuration** (150 days; strike grid step 0.05; 2 off-grid strikes) for speed; the main experiment and the study use the full configuration above with **N = 300 days**. The study (10 seeds × 2 worlds) is run by the CLI, not by the unit tests.

### 9.4a Outcome (added after execution — the text above is unchanged)
Executed 2026-10-12; results, failures and deviations are in [PHASE0_SYNTHETIC_RESULTS](PHASE0_SYNTHETIC_RESULTS.md). Headline: 57 unit tests passed (112 after the audit's regression and A2d tests); H-S1…H-S9 pass on the pre-registered main runs; the study found 0/9 false positives (RW) and 10/10 detections (AR); **but** H-S2 (strict) failed on the fast configuration, H-S1/H-S4/H-S6 each failed in 1–2 of 19 study runs, and one RW seed was an invalid world — all disclosed and diagnosed there. Protocol amendments needed **before freezing** thresholds (§7): make the cell-recovery tolerance consistent with the node-matching tolerance; widen the H-S6 tolerance (observed SD ≈ 10 % in AR); define a rule for invalid worlds.

**Audit addendum (2026-10-12, appended; the outcome text above is unchanged):** the post-hoc audit [PHASE0_AUDIT](PHASE0_AUDIT.md) analysed the three needed amendments with a 200-seed exploratory study and a bootstrap-coverage simulation. Proposals and their status (none signed): [decision.md](../../decision.md) PA-1 (bootstrap calibration, OPEN), PA-2 (H-S6 z-criterion, PROPOSED), PA-3 (recovery vs matching tolerance, PROPOSED for synthetic / OPEN for real data), PA-4 (invalid-world accounting, OPEN). The thresholds in §3 and §7 remain unfrozen.

### 9.5 How it is run (documented; the owner may re-run)
From `scripts/phase0_synthetic/` (nothing is installed): tests `python -m unittest discover -s tests -t .`; experiment `python -m phase0.run --help`. Run records (JSON) go to the git-ignored `experiments/phase0_synthetic/` and include Python version, platform, seeds, configuration, source-file hashes, validation and solver counts, metrics, intervals, and hypothesis outcomes.

### 9.6 Limitations declared in advance
Strikes are placed on a fixed moneyness grid so grid nodes can be matched exactly — real chains have fixed *price* strikes, so a proximity rule for `observed` will be needed (DEC-006); the factor structure is simple and known to the AR forecaster; there is no microstructure, no stale quotes, no per-contract timestamps, no AM/PM settlement mix; the constant rate is known; one underlying; one random-number generator. The synthetic worlds can validate the **pipeline's logic and detection ability** — they say nothing about real markets or real data quality.
