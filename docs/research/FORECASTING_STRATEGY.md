# Forecasting Strategy

**Status:** PROPOSED (DEC-011/DEC-012 not decided) · **Canonical for:** forecasting targets, representations, model ladder, experiment order · **Source:** MP §12–§13 · **Related:** [EVALUATION_PROTOCOL](EVALUATION_PROTOCOL.md), [FEATURE_CATALOG](FEATURE_CATALOG.md), [decision.md](../../decision.md)

## 1. Target (MP §12)
Initial: the **next valid trading session's** standardized IV surface at forecast origin *t* (target time determined by the market calendar). Later horizons (several sessions; joint/separate multi-horizon) are Phase 7.

The target is the future **surface**, not the underlying price. Evaluation is restricted to grid cells with `observed` status in the realized surface (and, separately, reports behaviour on interpolated cells if ever used), so models are not rewarded for reproducing the interpolator.

## 2. Output representations (MP §12) — compare at least grid vs low-dimensional
| Representation | Predicts | Pros | Cons |
|---|---|---|---|
| Grid | IV per node | Direct, simple | High-dimensional; masks; instability with short history |
| Change | Δ from latest surface | Persistence is the natural zero; reduces level non-stationarity | Needs latest surface defined at each node |
| Latent factors | Factors of PCA/autoencoder; decode to surface | Parsimonious, smooth | Reconstruction error; factor interpretability |
| Parametric | Parameters of a conventional fit | Smooth, interpretable | Fit error propagates; arbitrage-aware forms later |

PROPOSED (DEC-011): primary = change forecasting on the grid; comparator = low-dimensional factors. Hypothesis H-1 tested, not assumed.

## 3. Model ladder (ordered; each step must justify the next)
1. **Persistence** — tomorrow = today.
2. **Training-only historical average / mean change.**
3. **Linear / regularized regression** on lagged surface + context features (grid changes or factors).
4. **Statistical time-series** where the representation supports it (e.g., autoregressive models on factors/summary series).
5. **Parametric-surface baseline** — forecast parameters of a conventional fit.
6. **MLP** on lagged surface and context features (neural starting point; MP §13).
7. **TCN or GRU/LSTM** — only if the dataset supports sequence learning (sample size, diversity) and the MLP shows promise.
8. **Autoencoder + temporal model** — if grid dimensionality is high relative to history.
9. **Transformer-style** — only if data volume, diversity and compute justify it (MP §13); expected to be unjustified at modest history.

Advance only when the previous rung is evaluated under the frozen protocol and the go/no-go note (Phase 3 A5) supports it.

## 4. Experiment order (MP §13) and gates
Validate target & persistence → regression → MLP → sequence (if justified) → latent-factor (if high-dimensional) → compare complexity vs out-of-sample improvement, stability, runtime. Gate: GR-MOD-01 (baselines exist before neural).

## 5. Training protocol rules
- Training/validation/test windows chronological; walk-forward for primary claims (EVALUATION_PROTOCOL).
- Normalization stats from training view only.
- Early stopping and hyperparameter selection use validation windows; test window untouched until the configuration is frozen.
- Multiple seeds; report spread. Record seeds, library versions, hardware, training dates, hyperparameters (SCI-013).
- Loss functions evaluate on observed cells only (mask-aware).
- Frontend never trains models; training runs as jobs.

## 6. Framework
PyTorch is mentioned in MP §13 as an example "or another selected framework"; **not decided** (DEC-012/DEC-015). Choose once, use consistently.

## 7. Success criteria
Defined and dated in Phase 0 ([EVALUATION_PROTOCOL](EVALUATION_PROTOCOL.md) §8). "No improvement" is an acceptable, publishable outcome.

## 8. Open items
Number of lags and context set (`TBD(Phase 3)`); minimum training history; treatment of cells that change status through time (mask inputs).
