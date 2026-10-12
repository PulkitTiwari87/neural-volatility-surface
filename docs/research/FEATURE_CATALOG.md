# Feature Catalog

**Status:** PROPOSED catalog of candidates (nothing implemented; parameters undefined) · **Canonical for:** feature definitions, availability times, leakage notes · **Source:** MP §11 · **Related:** [DATA_FLOW](../architecture/DATA_FLOW.md) stage 7, [EVALUATION_PROTOCOL](EVALUATION_PROTOCOL.md), guardrails GR-LEAK-02/03/04

## 1. Rules
1. A feature may use only information with `available_at ≤ forecast origin`. Each feature declares its source and availability rule.
2. Every feature has an ID, version, definition (formula), required inputs, missing-value rule, and a **truncation-invariance test** (GR-LEAK-03).
3. Scalers/transformations are fit on the training view only, re-fit per fold (GR-LEAK-02).
4. Missingness is explicit: value + indicator, never silent imputation from future data.
5. Feature groups are validated by **ablation** (MP §11): keep only groups that help out of sample.
6. Revised data (e.g., adjusted prices) are used only if the revision was available at the origin.

Lags, window lengths, and similar parameters are **not specified here** (`TBD(Phase 3)`, chosen on validation data only and recorded).

## 2. Catalog

### Surface-derived (MP §11)
| ID | Feature | Definition (sketch) | Needs | Availability | Leakage note | Status |
|---|---|---|---|---|---|---|
| F-S01 | Grid IV at node (k,T) | IV in the standardized grid at origin | surface snapshot | origin close | Must include status/mask; do not treat interpolated as observed | PLANNED |
| F-S02 | Lagged grid IV | F-S01 at origins t−1…t−L | past snapshots | ≤ t | Past only | PLANNED |
| F-S03 | ATM IV by maturity | IV at k≈0 per T (interpolated flag) | surface | origin | Flag interpolation | PLANNED |
| F-S04 | Put-side / call-side skew | Slope of IV in k on each side at given T | surface | origin | — | PLANNED |
| F-S05 | Smile curvature | Second-difference/curvature of IV in k | surface | origin | Noise-sensitive | PLANNED |
| F-S06 | Term-structure slope | ΔIV/ΔT at fixed k | surface | origin | — | PLANNED |
| F-S07 | IV changes vs previous sessions | IV_t − IV_{t−j} per node/summary | past surfaces | ≤ t | Missing if either cell not observed | PLANNED |
| F-S08 | Surface summaries | Mean level, skew, curvature across the grid | surface | origin | Mask-aware | PLANNED |

### Market-context (where reliable data exists)
| ID | Feature | Needs | Leakage note | Status |
|---|---|---|---|---|
| F-M01 | Underlying returns | underlying prices | Use closes ≤ origin | PLANNED |
| F-M02 | Realized volatility (rolling) | underlying prices | Window ends at origin; no centered windows | PLANNED |
| F-M03 | Volume / open-interest summaries | quotes | Use values as of origin snapshot | PLANNED |
| F-M04 | Bid-ask spread & quote-quality measures | quotes | As of snapshot | PLANNED |
| F-M05 | Session / calendar features (day of week, pre-holiday, days to expiry cycle) | calendar | Known in advance ⇒ allowed for future date only if calendar is deterministic | PLANNED |
| F-M06 | Interest-rate & dividend inputs | reference data | Use as-of values; no later revisions | PLANNED |
| F-M07 | Broad market volatility indicator | external series | Requires licence + as-of availability | NEEDS RESEARCH |
| F-M08 | Event-calendar flags (earnings, macro) | timestamped event source | Only if the event schedule was known at origin | NEEDS RESEARCH |
| F-M09 | Liquidity / regime indicators | derived | Regime definition must use only past data | OPEN |

## 3. Entry template
```
ID / name / version:
Definition (formula):
Inputs and sources (with licence class):
Availability rule (available_at):
Parameters (values and how chosen — validation only):
Missing-value rule and indicator:
Leakage risks and the test that covers them:
Ablation group:
Status:
```

## 4. Validation
Truncation-invariance (features at *t* identical with data cut at *t*); sentinel tests on scalers; unit tests vs hand-computed examples; ablation reports in experiment records. Catalog changes bump the feature version and create a new dataset version.
