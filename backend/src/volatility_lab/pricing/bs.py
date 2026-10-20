"""Vectorised Black-76 pricing and implied-volatility inversion.

Conventions (mirror ``scripts/phase0_synthetic/phase0``, which is the scalar reference
implementation this module is cross-checked against in the tests):

* European option on a forward ``F``; ``T`` in years; prices are *undiscounted*
  (the caller divides market prices by the discount factor).
* A failed inversion is an explicit status, never a fabricated IV.
"""
from __future__ import annotations

import numpy as np
from scipy.special import ndtr

# int8 status codes (kept numeric so they live in arrays)
OK = 0
BELOW_LOWER_BOUND = 1  # price <= intrinsic: no positive IV
ABOVE_UPPER_BOUND = 2  # price >= call: F / put: K, no finite IV
INVALID_INPUT = 3
# The price is inside the no-arbitrage bounds but the root lies outside [SIGMA_LO, SIGMA_HI]. These are solver-range
# failures, not arbitrage violations, and must not be reported as BELOW_LOWER_BOUND / ABOVE_UPPER_BOUND.
BELOW_SOLVER_FLOOR = 4  # price < price(SIGMA_LO): implied sigma < SIGMA_LO
ABOVE_SOLVER_CEILING = 5  # price > price(SIGMA_HI): implied sigma > SIGMA_HI
STATUS_NAMES = {OK: "OK", BELOW_LOWER_BOUND: "BELOW_LOWER_BOUND",
                ABOVE_UPPER_BOUND: "ABOVE_UPPER_BOUND", INVALID_INPUT: "INVALID_INPUT",
                BELOW_SOLVER_FLOOR: "BELOW_SOLVER_FLOOR", ABOVE_SOLVER_CEILING: "ABOVE_SOLVER_CEILING"}

SIGMA_LO = 1e-4
SIGMA_HI = 5.0


def _d1_d2(F, K, T, sigma):
    vol = sigma * np.sqrt(T)
    d1 = (np.log(F / K) + 0.5 * vol * vol) / vol
    return d1, d1 - vol


def black76_price(F, K, T, sigma, is_call):
    """Undiscounted Black-76 price; broadcasts over arrays. ``sigma`` must be > 0."""
    F, K, T, sigma = (np.asarray(x, dtype=float) for x in (F, K, T, sigma))
    is_call = np.asarray(is_call, dtype=bool)
    d1, d2 = _d1_d2(F, K, T, sigma)
    call = F * ndtr(d1) - K * ndtr(d2)
    put = K * ndtr(-d2) - F * ndtr(-d1)
    return np.where(is_call, call, put)


def black76_vega(F, K, T, sigma):
    """Undiscounted vega dP/dsigma (per 1.00 of vol, not per vol point)."""
    F, K, T, sigma = (np.asarray(x, dtype=float) for x in (F, K, T, sigma))
    d1, _ = _d1_d2(F, K, T, sigma)
    return F * np.exp(-0.5 * d1 * d1) / np.sqrt(2.0 * np.pi) * np.sqrt(T)


def black76_greeks(F, K, T, sigma, is_call):
    """Forward-measure sensitivities: ``(delta, gamma, vega)`` of the undiscounted price.

    ``delta`` is dP/dF, ``gamma`` d2P/dF2, ``vega`` dP/dsigma (per 1.00 of vol).
    Theta and rho are intentionally omitted: they need a rate/dividend model this
    pipeline does not claim to have.
    """
    F, K, T, sigma = (np.asarray(x, dtype=float) for x in (F, K, T, sigma))
    is_call = np.asarray(is_call, dtype=bool)
    d1, _ = _d1_d2(F, K, T, sigma)
    delta = np.where(is_call, ndtr(d1), ndtr(d1) - 1.0)
    gamma = np.exp(-0.5 * d1 * d1) / np.sqrt(2.0 * np.pi) / (F * sigma * np.sqrt(T))
    return delta, gamma, black76_vega(F, K, T, sigma)


def implied_vol(price, F, K, T, is_call, *, n_iter: int = 48, chunk: int = 1_000_000):
    """Vectorised IV by bisection on [SIGMA_LO, SIGMA_HI].

    Returns ``(iv, status)``; ``iv`` is NaN wherever ``status != OK``.
    48 halvings shrink the bracket to ~1e-13, below any market-data resolution.
    """
    price, F, K, T = (np.asarray(x, dtype=float) for x in (price, F, K, T))
    shape = np.broadcast_shapes(price.shape, F.shape, K.shape, T.shape, np.shape(is_call))
    p, f, k, t = (np.ravel(np.broadcast_to(x, shape)) for x in (price, F, K, T))
    c = np.ravel(np.broadcast_to(np.asarray(is_call, dtype=bool), shape))
    iv = np.full(p.size, np.nan)
    status = np.full(p.size, INVALID_INPUT, dtype=np.int8)

    with np.errstate(invalid="ignore"):
        ok_in = np.isfinite(p) & np.isfinite(f) & np.isfinite(k) & np.isfinite(t) & (f > 0) & (k > 0) & (t > 0) & (p >= 0)
        lower = np.where(c, np.maximum(f - k, 0.0), np.maximum(k - f, 0.0))
        upper = np.where(c, f, k)
        status[ok_in & (p <= lower)] = BELOW_LOWER_BOUND
        status[ok_in & (p >= upper)] = ABOVE_UPPER_BOUND
        solve = ok_in & (p > lower) & (p < upper)

    idx_all = np.flatnonzero(solve)
    for s in range(0, idx_all.size, chunk):
        idx = idx_all[s:s + chunk]
        ps, fs, ks, ts, cs = p[idx], f[idx], k[idx], t[idx], c[idx]
        lo = np.full(idx.size, SIGMA_LO)
        hi = np.full(idx.size, SIGMA_HI)
        for _ in range(n_iter):
            mid = 0.5 * (lo + hi)
            too_high = black76_price(fs, ks, ts, mid, cs) > ps
            hi = np.where(too_high, mid, hi)
            lo = np.where(too_high, lo, mid)
        sol = 0.5 * (lo + hi)
        # the root must lie inside the search bracket
        pl = black76_price(fs, ks, ts, np.full(idx.size, SIGMA_LO), cs)
        ph = black76_price(fs, ks, ts, np.full(idx.size, SIGMA_HI), cs)
        bracketed = (pl <= ps) & (ps <= ph)
        iv[idx] = np.where(bracketed, sol, np.nan)
        status[idx] = np.where(bracketed, OK, np.where(ps < pl, BELOW_SOLVER_FLOOR, ABOVE_SOLVER_CEILING)).astype(np.int8)
    return iv.reshape(shape), status.reshape(shape)
