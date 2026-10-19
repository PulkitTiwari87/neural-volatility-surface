"""Static-arbitrage *diagnostics* on the constant-maturity grid. These are necessary-condition flags only:
a surface passing them is not thereby arbitrage-free, and nothing is repaired or dropped.
"""
from __future__ import annotations

import numpy as np

from volatility_lab.pricing.bs import black76_price


def calendar_violations(iv: np.ndarray, tenor_days: np.ndarray, tol: float = 1e-4):
    """Total variance w = iv^2 * T must not decrease with maturity at fixed k. Returns (violations, checks)."""
    T = np.asarray(tenor_days, dtype=float) / 365.0
    w = iv ** 2 * T[None, :, None]
    dw = np.diff(w, axis=1)
    both = np.isfinite(dw)
    return int((dw[both] < -tol).sum()), int(both.sum())


def butterfly_violations(iv: np.ndarray, tenor_days: np.ndarray, k_nodes: np.ndarray, tol: float = 1e-6):
    """Undiscounted call price (F = 1) must be convex in strike. Returns (violations, checks)."""
    T = np.asarray(tenor_days, dtype=float) / 365.0
    K = np.exp(np.asarray(k_nodes, dtype=float))
    viol = checks = 0
    n, nt, nk = iv.shape
    for j in range(nt):
        sig = iv[:, j, :]
        with np.errstate(invalid="ignore"):
            price = black76_price(1.0, K[None, :], T[j], np.where(np.isfinite(sig), sig, 1.0), True)
        price = np.where(np.isfinite(sig), price, np.nan)
        slope = np.diff(price, axis=1) / np.diff(K)[None, :]
        curv = np.diff(slope, axis=1)
        ok = np.isfinite(curv)
        viol += int((curv[ok] < -tol).sum())
        checks += int(ok.sum())
    return viol, checks


def diagnostics_report(panel: dict) -> dict:
    cv, cc = calendar_violations(panel["iv"], panel["tenor_days"])
    bv, bc = butterfly_violations(panel["iv"], panel["tenor_days"], panel["k_nodes"])
    return {"calendar_violations": cv, "calendar_checks": cc, "calendar_rate": cv / cc if cc else None,
            "butterfly_violations": bv, "butterfly_checks": bc, "butterfly_rate": bv / bc if bc else None,
            "note": "necessary-condition flags on a coarse grid; not a proof of arbitrage-freedom"}
