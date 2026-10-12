# Vision

**Status:** PROPOSED · **Source:** MP §1, §26 · **Related:** [SCOPE](SCOPE.md), [PR.md](../../PR.md)

## Purpose
State what the project is for and what "good" looks like, so scope and trade-off decisions have an anchor.

## Vision
A **quantitative research terminal** that lets a researcher study how option-implied volatility varies across strike/moneyness and maturity, whether a neural time-series model can forecast how that surface evolves, and — crucially — *how much to trust the answer*. The workflow is fully inspectable: source data, cleaning, price validation, IV calculation, surface construction, features, training, evaluation, uncertainty, limitations.

## Core question
Given the option market observed at time *t*, how accurately can a model forecast the implied-volatility surface at a future horizon (first: the next trading day), compared with simple baselines? (MP §1)

## What success looks like
- A researcher can go from an attractive 3D surface to the underlying quote, inspect the IV calculation and construction method, see the forecast, compare it with a baseline, and understand the evidence for and against it (MP §26).
- A published experiment can be **reproduced** from saved configuration and data versions.
- Results are **honest**: negative or null findings are reported as readily as positive ones; limitations are visible in the product.

## Guiding principles
1. Every forecast inspectable; every experiment reproducible; every limitation visible (MP §26).
2. A neural model is a hypothesis to test, not an assumed improvement.
3. Observed ≠ interpolated; absence is information.
4. Research and education only: no trading signals, advice, or profitability claims.
5. Simplicity: the smallest architecture that supports the science.

## What it is not
Not a trading system, not an investment-advice product, not a real-time market-data terminal, not a generic ML dashboard.

## Status
Vision `PROPOSED` pending owner review. Success is *not* defined as "the neural model wins".
