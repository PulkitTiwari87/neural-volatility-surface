# Quote Quality Policy

**Status:** PROPOSED (checks from MP §8; thresholds undefined) · **Canonical for:** quote validation checks, reason codes, quote-selection policy, sensitivity analysis · **Source:** MP §8 · **Related:** [DATA_DICTIONARY](DATA_DICTIONARY.md), [IV_METHODOLOGY](../research/IV_METHODOLOGY.md), guardrails GR-DATA-02/03

## 1. Principles
- **Never silently discard.** Every record gets a disposition (`retained`, `excluded`, `down_weighted`) and reason codes (GR-DATA-02).
- Policy is **configuration**, versioned and hashed; changing it changes the dataset version.
- Thresholds are **not set here**. They are chosen in Phase 1/2 from observed distributions on the assessed sample and recorded (`TBD(Phase 1)`), then tested for sensitivity (RQ-09).

## 2. Checks (MP §8 step 5) and reason codes
| Code | Check | Default disposition |
|---|---|---|
| `DUPLICATE` | Same contract + timestamp + source rule matched | exclude duplicates (keep one by documented rule) |
| `NEGATIVE_PRICE` | bid, ask, or last < 0 | exclude |
| `CROSSED_MARKET` | bid > ask | exclude |
| `LOCKED_MARKET` | bid = ask | flag; policy decides |
| `ZERO_BID` | bid = 0 | flag; policy decides (often exclude or down-weight for IV) |
| `ZERO_ASK_OR_IMPLAUSIBLE` | ask = 0, or bid/ask implausible vs intrinsic/underlying | exclude |
| `WIDE_SPREAD` | (ask − bid) above threshold (absolute or relative) | flag/down-weight/exclude per policy |
| `STALE_QUOTE` | quote timestamp too old relative to snapshot/underlying timestamp | exclude/flag |
| `STALE_UNDERLYING_ALIGNMENT` | underlying reference timestamp gap too large | flag/exclude |
| `INCONSISTENT_METADATA` | strike/expiry/type/multiplier mismatch across records | exclude |
| `EXPIRED_OR_INVALID_EXPIRY` | expiry not a valid session or already past | exclude |
| `UNALIGNABLE` | no underlying/rate/dividend available | exclude from IV |
| `BELOW_INTRINSIC` / `ABOVE_BOUND` | Price outside theoretical bounds (also detected in IV stage) | exclude from IV with status |
| `LOW_LIQUIDITY` | volume/open interest/size below policy | flag/down-weight |
| `MIN_MATURITY` | time to expiry below policy minimum | exclude/flag |

(Codes are a proposed initial enum; finalize in Phase 1.)

## 3. Quote-selection policy (MP §8)
Configurable, with defaults documented:
- **Price used:** bid/ask midpoint (starting point) — alternatives to compare: OTM-side only; spread-weighted; last-trade when no quote (generally discouraged).
- **Eligibility:** minimum quote quality, maximum spread, maximum staleness, zero-bid handling, minimum open interest/volume (all `TBD(Phase 1)`).
- **Weighting vs exclusion:** `down_weighted` records keep a weight used downstream (documented); excluded records are not used for IV but are reported.

## 4. Quality report (per snapshot; MP §8 step 8)
Counts ingested / retained / excluded / down-weighted; counts by reason code; timestamp-gap distribution; spread distribution; proportion zero-bid; coverage by maturity and moneyness after filtering. Invariant: `ingested = retained + excluded` (down-weighted ⊂ retained). Reports are stored and visible in the Data Quality view.

## 5. Sensitivity analysis (RQ-09)
Define ≥2 reasonable alternative policies (e.g., strict, baseline, lenient). For each, build surfaces and report: share of cells observed, IV differences between policies by region, effect on persistence-baseline error. Conclusions are labelled with the sample used. Policy choice for the primary experiments is fixed before test-period evaluation.

## 6. Tests
Defect-injection fixtures (one per code) with exact expected counts; conservation property; policy-change ⇒ new hash; boundary cases at thresholds; time-alignment edge cases (early close, holiday, DST).

## 7. Open items
Threshold values; treatment of locked markets; use of last-trade; use of put-call parity to cross-check quotes (NEEDS RESEARCH); exchange-specific quirks once the market is chosen.
