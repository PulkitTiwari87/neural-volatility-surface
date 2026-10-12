# Implied-Volatility Methodology

**Status:** PROPOSED (model and conventions pending DEC-004/DEC-005/DEC-001) · **Canonical for:** IV computation process, bounds, solver policy, statuses, limitations · **Source:** MP §3, §8–§9, §21 · **Related:** [QUOTE_QUALITY_POLICY](../data/QUOTE_QUALITY_POLICY.md), [SURFACE_CONSTRUCTION](SURFACE_CONSTRUCTION.md), [guardrails.md](../../guardrails.md) GR-QNT, [decision.md](../../decision.md) DEC-004/005

## 1. Purpose
Specify how IV is derived from option prices reproducibly, with explicit failure modes, so that IV is never fabricated and every value is auditable.

## 2. Process (MP §9)
1. Select an eligible quote under the quote policy (eligibility rules in QUOTE_QUALITY_POLICY).
2. Compute the market price used (default **midpoint**; alternative policies are sensitivity-tested, MP §8).
3. Determine time to expiration *T* by the documented calendar and day-count (DEC-005).
4. Assemble inputs: underlying price *S* (aligned in time), strike *K*, rate *r*, dividend/carry *q* (or forward *F*), option type, exercise style.
5. Choose the pricing model appropriate to the instrument (DEC-004).
6. Solve for σ numerically within bounds.
7. Check convergence and that the price lies within theoretical bounds.
8. Store IV, solver diagnostics, inputs, flags.

## 3. Pricing model (PROPOSED, conditional)
For **European-style** options, the proposed starting model is Black–Scholes–Merton expressed via the forward *F = S·e^{(r−q)T}* (Black-76 form):

- d₁ = [ ln(F/K) + ½σ²T ] / (σ√T), d₂ = d₁ − σ√T
- Call = e^{−rT} [ F·N(d₁) − K·N(d₂) ]; Put = e^{−rT} [ K·N(−d₂) − F·N(−d₁) ]

If the chosen instruments are **American-style** (e.g., many single-stock/ETF options), this model is **not** appropriate without handling early exercise (MP §9). Options: restrict to regions where the early-exercise premium is shown negligible, or use an American-option method. This is `NEEDS RESEARCH` and must be settled in DEC-004 before Phase 2. A model that does not support the instrument must reject it with status `UNSUPPORTED_INSTRUMENT` (GR-QNT-04).

Dividend treatment (continuous yield, discrete dividends, implied forward), rate curve choice, and index/ETF specifics: `OPEN`; recorded as a versioned **assumption set** attached to each IV observation.

## 4. Theoretical bounds (European, forward form)
- Call: max(e^{−rT}(F − K), 0) ≤ C ≤ e^{−rT} F
- Put: max(e^{−rT}(K − F), 0) ≤ P ≤ e^{−rT} K

A price at or below the lower bound (no time value) or above the upper bound has no finite positive IV under the model → explicit status, no value. Prices extremely close to bounds are numerically ill-conditioned; tolerance handling is part of the solver spec (`TBD(Phase 2)`).

## 5. Solver policy
- **Bracketed root-finding** (e.g., Brent) is the default (MP §9): requires `f(σ_low) < 0 < f(σ_high)`; bounds `[σ_low, σ_high]` are configured and documented (values `TBD(Phase 2)` from synthetic study; not set here).
- **Newton-type** acceleration allowed only with a safeguard falling back to bracketing (vega near zero in deep wings/short maturities).
- Convergence criteria: price tolerance and/or σ tolerance and max iterations — configured, recorded with each result.
- **Result record:** `iv` (nullable), `solver_status`, `iterations`, `residual`, `model`, `assumption_set_id`, `inputs`, `quality_flags`, `failure_reason`.

### Status enum (initial proposal; finalize in Phase 2)
`CONVERGED`, `PRICE_BELOW_LOWER_BOUND`, `PRICE_ABOVE_UPPER_BOUND`, `NO_BRACKET`, `MAX_ITERATIONS`, `NON_FINITE_INPUT`, `INVALID_INPUT`, `UNSUPPORTED_INSTRUMENT`, `EXCLUDED_BY_QUOTE_POLICY`.

### Invariants
`iv ≠ null ⇒ status = CONVERGED ∧ |price(iv) − market| ≤ tolerance`; `iv = null ⇒ failure_reason ≠ null`. Failures are counted and reported (Data Quality view), never imputed in the IV table. Surface construction may later *interpolate*, but those cells are labelled as such (GR-DATA-05).

## 6. Edge cases (MP §9) and handling
| Case | Handling |
|---|---|
| Very short *T* | Vega and price collapse; require minimum *T* by policy (`TBD(Phase 2)`) or flag low-reliability; test explicitly |
| Deep ITM | Little time value; IV ill-determined; prefer OTM-side quotes (put-call parity based selection is a policy option to evaluate) |
| Deep OTM / tiny or zero bid | Midpoint unreliable; policy for zero bids (exclude/down-weight) |
| Wide spreads | Spread threshold in policy; IV bounds from bid and ask can be recorded as diagnostics |
| Stale/invalid price | Excluded upstream with reason |
| Price out of bounds | Status above; counted |
| Rate/dividend inconsistent with model | Assumption-set validation; flag |
| American exercise | See §3 |

## 7. Limitations (to carry into KNOWN_LIMITATIONS)
IV depends on model, assumptions (rates, dividends, calendar) and price choice; midpoint is not a transaction price; illiquid quotes are noisy; European model misprices early-exercise value; end-of-day snapshots may mix quote times across contracts.

## 8. Validation (scientific tests; guardrails GR-QNT-01…06)
1. **Synthetic recovery:** price(σ*) → solve → σ̂; compare across a grid of σ*, *T* (including very short), moneyness (including deep ITM/OTM), call/put. Tolerances recorded before running on real data.
2. **Bounds:** below/above-bound prices → expected statuses.
3. **Convergence/failure:** forced non-bracket, NaN/inf inputs, max-iteration cases.
4. **Reference cases:** compare with independently documented reference values (source cited in the test).
5. **Instrument appropriateness:** unsupported styles rejected.
6. **Determinism:** same inputs ⇒ identical outputs.

## 9. Open items
DEC-004 (model, dividends), DEC-005 (conventions), solver bounds/tolerances (`TBD(Phase 2)`), put-call parity usage (NEEDS RESEARCH).
