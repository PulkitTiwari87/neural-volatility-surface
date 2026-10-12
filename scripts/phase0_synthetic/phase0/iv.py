"""Implied-volatility solver: bounded Brent with explicit statuses. SYNTHETIC SPIKE.

Invariants (GR-QNT-02/03):
  * iv is not None  <=>  status == CONVERGED
  * iv is None      =>  reason is not None
No IV is ever fabricated when the solver fails.
"""
import math
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from .bsm import black76_price, price_bounds

_EPS = 2.220446049250313e-16


class IVStatus(str, Enum):
    CONVERGED = "CONVERGED"
    PRICE_BELOW_LOWER_BOUND = "PRICE_BELOW_LOWER_BOUND"  # price <= lower bound: no positive IV
    PRICE_ABOVE_UPPER_BOUND = "PRICE_ABOVE_UPPER_BOUND"  # price >= upper bound: no finite IV
    NO_BRACKET = "NO_BRACKET"  # root not inside [sigma_lo, sigma_hi]
    MAX_ITERATIONS = "MAX_ITERATIONS"
    INVALID_INPUT = "INVALID_INPUT"


@dataclass(frozen=True)
class SolverConfig:
    """Spike values; NOT adopted for the product (tolerances TBD in Phase 2)."""

    sigma_lo: float = 1e-6
    sigma_hi: float = 5.0
    xtol: float = 1e-12
    max_iter: int = 200


@dataclass(frozen=True)
class IVResult:
    iv: Optional[float]
    status: IVStatus
    iterations: int
    residual: Optional[float]
    reason: Optional[str]


def _fail(status: IVStatus, reason: str, iterations: int = 0) -> IVResult:
    return IVResult(None, status, iterations, None, reason)


def _brent(f: Callable[[float], float], a: float, b: float, fa: float, fb: float, xtol: float, max_iter: int):
    """Brent's method (after Numerical Recipes 'zbrent'). Returns (root, f(root), iterations, converged)."""
    c, fc = b, fb
    d = e = b - a
    for it in range(1, max_iter + 1):
        if (fb > 0.0 and fc > 0.0) or (fb < 0.0 and fc < 0.0):
            c, fc = a, fa
            d = e = b - a
        if abs(fc) < abs(fb):
            a = b
            b = c
            c = a
            fa = fb
            fb = fc
            fc = fa
        tol1 = 2.0 * _EPS * abs(b) + 0.5 * xtol
        xm = 0.5 * (c - b)
        if abs(xm) <= tol1 or fb == 0.0:
            return b, fb, it, True
        if abs(e) >= tol1 and abs(fa) > abs(fb):
            s = fb / fa
            if a == c:
                p = 2.0 * xm * s
                q = 1.0 - s
            else:
                q = fa / fc
                rr = fb / fc
                p = s * (2.0 * xm * q * (q - rr) - (b - a) * (rr - 1.0))
                q = (q - 1.0) * (rr - 1.0) * (s - 1.0)
            if p > 0.0:
                q = -q
            p = abs(p)
            min1 = 3.0 * xm * q - abs(tol1 * q)
            min2 = abs(e * q)
            if 2.0 * p < min(min1, min2):
                e = d
                d = p / q
            else:
                d = xm
                e = d
        else:
            d = xm
            e = d
        a, fa = b, fb
        if abs(d) > tol1:
            b += d
        else:
            b += math.copysign(tol1, xm)
        fb = f(b)
    return b, fb, max_iter, False


def implied_vol(price, F, K, T, r, is_call, cfg: SolverConfig = SolverConfig()) -> IVResult:
    values = (price, F, K, T, r)
    if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in values):
        return _fail(IVStatus.INVALID_INPUT, "non-finite or non-numeric input")
    if F <= 0.0 or K <= 0.0 or T <= 0.0:
        return _fail(IVStatus.INVALID_INPUT, "F, K and T must be positive")
    if price < 0.0:
        return _fail(IVStatus.INVALID_INPUT, "negative price")

    lb, ub = price_bounds(F, K, T, r, is_call)
    if price <= lb:
        return _fail(IVStatus.PRICE_BELOW_LOWER_BOUND, "price <= lower bound; no positive IV exists")
    if price >= ub:
        return _fail(IVStatus.PRICE_ABOVE_UPPER_BOUND, "price >= upper bound; no finite IV exists")

    def f(s: float) -> float:
        return black76_price(F, K, T, r, s, is_call) - price

    flo, fhi = f(cfg.sigma_lo), f(cfg.sigma_hi)
    if flo > 0.0 or fhi < 0.0:
        return _fail(IVStatus.NO_BRACKET, "root not bracketed by [sigma_lo, sigma_hi]")

    root, froot, iterations, converged = _brent(f, cfg.sigma_lo, cfg.sigma_hi, flo, fhi, cfg.xtol, cfg.max_iter)
    if not converged:
        return _fail(IVStatus.MAX_ITERATIONS, "max iterations reached", iterations)
    return IVResult(root, IVStatus.CONVERGED, iterations, froot, None)
