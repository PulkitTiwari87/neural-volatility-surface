"""Black-76 pricing helpers (European options on a forward). SYNTHETIC SPIKE."""
import math

_SQRT2 = math.sqrt(2.0)
_SQRT2PI = math.sqrt(2.0 * math.pi)


def norm_cdf(x: float) -> float:
    return 0.5 * math.erfc(-x / _SQRT2)


def norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / _SQRT2PI


def discount(r: float, T: float) -> float:
    return math.exp(-r * T)


def price_bounds(F: float, K: float, T: float, r: float, is_call: bool):
    """No-arbitrage bounds for a European option on forward F (discounted)."""
    df = discount(r, T)
    if is_call:
        return max(df * (F - K), 0.0), df * F
    return max(df * (K - F), 0.0), df * K


def black76_price(F: float, K: float, T: float, r: float, sigma: float, is_call: bool) -> float:
    if sigma < 0.0:
        raise ValueError("sigma must be >= 0")
    if sigma == 0.0 or T <= 0.0:
        return price_bounds(F, K, T, r, is_call)[0]
    df = discount(r, T)
    vol = sigma * math.sqrt(T)
    d1 = (math.log(F / K) + 0.5 * vol * vol) / vol
    d2 = d1 - vol
    if is_call:
        return df * (F * norm_cdf(d1) - K * norm_cdf(d2))
    return df * (K * norm_cdf(-d2) - F * norm_cdf(-d1))


def black76_vega(F: float, K: float, T: float, r: float, sigma: float) -> float:
    vol = sigma * math.sqrt(T)
    d1 = (math.log(F / K) + 0.5 * vol * vol) / vol
    return discount(r, T) * F * norm_pdf(d1) * math.sqrt(T)
