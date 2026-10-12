# Data Source Assessment

**Status:** PLANNED — **no source has been assessed.** All candidate entries below are `NOT ASSESSED`. This file is the Phase 0 work product for DEC-001/002/003 and must be filled with verified evidence. · **Source:** MP §2, §6, §25 · **Related:** [DATA_GOVERNANCE](DATA_GOVERNANCE.md), [decision.md](../../decision.md), [IMPLEMENTATION_PLAN](../../IMPLEMENTATION_PLAN.md) Phase 0

## 1. Purpose
Choose the initial market, underlying universe, provider and snapshot frequency on evidence — coverage, quality, and **licence** — before any ingestion code is written.

## 2. Ground rules
- Do not assume free access to complete historical option chains or real-time OPRA (MP §2).
- Every claim in an assessment cites its source (provider documentation, contract/ToS clause, or a measurement on a sample) and the date checked. Unverified items stay `UNVERIFIED`.
- No scraping of sites whose terms prohibit it; no use of credentials or paid APIs without the owner's explicit approval.
- Do not commit provider samples unless the licence expressly permits; default is not to.

## 3. Candidate categories (MP §6) and example names to evaluate
Example names are listed **only as candidates to investigate**, from general knowledge. **Coverage, history, pricing, and licence terms of each are UNVERIFIED and must not be assumed.**

| Category | Candidates to investigate (UNVERIFIED) | Typical questions |
|---|---|---|
| Licensed market-data vendors with historical option snapshots | Cboe DataShop; OptionMetrics (IvyDB); ORATS; Databento; Polygon.io | Depth of history, EOD vs intraday, field set, redistribution/display rights, price |
| Broker APIs | Interactive Brokers API; Tradier | Account requirements, history limits, ToS on storing/displaying |
| Academic / research datasets | Institutional subscriptions (e.g., via a university library) | Access terms, citation/publication rules, redistribution ban |
| Public datasets for prototyping | To be identified | Schema suitability, usage rights, coverage gaps |

## 4. Assessment table (MP §6) — one block per candidate (underlying, provider) pair
| Requirement | Questions | Evidence/answer | Source & date | Status |
|---|---|---|---|---|
| Coverage | Underlyings, contracts, exchanges, dates | | | NOT ASSESSED |
| Granularity | EOD, intraday snapshots, streaming | | | NOT ASSESSED |
| Quote fields | Bid, ask, sizes, last, volume, open interest, Greeks, IV | | | NOT ASSESSED |
| Timestamps | Exchange time, timezone, quote vs snapshot timestamp | | | NOT ASSESSED |
| Adjustments | Splits, dividends, symbol changes, adjusted contracts | | | NOT ASSESSED |
| Historical depth | How far back | | | NOT ASSESSED |
| Reliability | Known gaps, correction policy | | | NOT ASSESSED |
| Licensing | Store? Display? Redistribute? Publish results/derived data? | | | NOT ASSESSED |
| Cost & limits | Subscription, API, rate limits | | | NOT ASSESSED |
| Underlying price / rates / dividends | Source for each, timestamp alignment | | | NOT ASSESSED |
| Exercise style & settlement | European/American; cash/physical (affects DEC-004) | | | NOT ASSESSED |
| Raw reproducibility | Can raw responses be stored; are historical snapshots stable/versioned? | | | NOT ASSESSED |

## 5. Decision criteria (weights agreed before scoring)
1. **Licence permits the intended use** (hard gate; fail ⇒ reject or restrict scope).
2. Sufficient history and regime diversity for the minimum viable dataset (to be defined quantitatively in Phase 0).
3. Required fields present with timestamps allowing the alignment policy.
4. Strike/expiry density adequate for the target grid.
5. Cost within the owner's budget (no paid commitments without approval).
6. Reproducibility and stability of historical data.
7. Exercise-style simplicity (affects pricing model).

## 6. Minimum feasibility sample
A small, **permitted** extract (or a synthetic sample if none permitted) of a handful of dates containing calm and, if available, stressed conditions, sufficient to run: quotes → validation → IV → surface → persistence forecast. Measure: number of contracts per date, strikes/expiries per maturity bucket, share of zero/crossed/stale quotes, timestamp gaps. Results recorded here with dates and method.

## 7. Red flags
Terms prohibiting storage or derived-data display · no raw history, only vendor-computed IV · undocumented adjustments/corrections · timestamps without timezone · survivorship (expired/delisted contracts missing) · unstable historical values between pulls.

## 8. Output
A comparison table, the recommended (underlying, provider, frequency), the licence conclusions, and the measured feasibility sample statistics → ADRs for DEC-001/002/003. Until then, `decision.md` keeps them `NEEDS RESEARCH`.
