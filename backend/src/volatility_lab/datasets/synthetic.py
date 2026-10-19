"""SYNTHETIC option chains in the OptionsDX wide format, generated from a *known* volatility surface.

Used for CPU unit tests (known-answer IV / forward / surface recovery) and for a labelled plumbing run.
Never evidence about real markets. The latent surface is a smooth parametric function whose level, skew
and term slope follow independent AR(1) processes; the underlying is an independent GBM.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from volatility_lab.pricing.bs import black76_price

LABEL = "SYNTHETIC - not market data"


def true_sigma(k, T, level, skew, term=0.02, curv=1.5):
    return np.maximum(0.05, level + skew * k + curv * k * k + term * (T - 0.25))


def make_chain(n_days: int = 60, seed: int = 0, start: str = "2018-01-02", r: float = 0.02, q: float = 0.015,
               strike_step: float = 1.0, noise_free: bool = True, messy_format: bool = True,
               expiry_freq: str = "W-FRI", max_dte: int = 230):
    """Return ``(wide_frame, truth)``; ``truth`` holds per-date latent parameters, spot, F-factor and DF.

    ``expiry_freq`` is a pandas offset alias for the listed expiries ("W-FRI" weekly; "B" daily, as SPY now has).
    """
    rng = np.random.default_rng(seed)
    days = pd.bdate_range(start, periods=n_days)
    level, skew = 0.20, -0.8
    spot = 300.0
    fridays = pd.date_range(days[0], days[-1] + pd.Timedelta(days=max_dte), freq=expiry_freq)
    rows, truth = [], []
    for d in days:
        level = 0.20 + 0.97 * (level - 0.20) + 0.008 * rng.standard_normal()
        level = float(np.clip(level, 0.08, 0.6))
        skew = -0.8 + 0.98 * (skew + 0.8) + 0.03 * rng.standard_normal()
        spot *= float(np.exp(0.0003 + 0.01 * rng.standard_normal()))
        truth.append({"date": d, "level": level, "skew": skew, "spot": spot})
        for e in fridays:
            dte = (e - d).days
            if dte < 2 or dte > max_dte:
                continue
            T = dte / 365.0
            F = spot * np.exp((r - q) * T)
            df = np.exp(-r * T)
            K = np.arange(np.floor(0.72 * spot), np.ceil(1.28 * spot), strike_step * (1 if T < 0.3 else 5))
            sig = true_sigma(np.log(K / F), T, level, skew)
            call = df * black76_price(F, K, T, sig, True)
            put = df * black76_price(F, K, T, sig, False)
            half_c = np.maximum(0.005, 0.01 * call)
            half_p = np.maximum(0.005, 0.01 * put)
            if not noise_free:
                call, put = np.round(call, 2), np.round(put, 2)
            rows.append(pd.DataFrame({
                "[QUOTE_DATE]": d.strftime("%Y-%m-%d"), "[EXPIRE_DATE]": e.strftime("%Y-%m-%d"), "[STRIKE]": K,
                "[UNDERLYING_LAST]": spot, "[DTE]": float(dte),
                "[C_BID]": call - half_c, "[C_ASK]": call + half_c, "[P_BID]": put - half_p, "[P_ASK]": put + half_p,
                "[C_IV]": sig, "[P_IV]": sig}))
    wide = pd.concat(rows, ignore_index=True)
    # deep-OTM quotes with no bid, as in real chains
    wide.loc[wide["[C_BID]"] < 0.01, "[C_BID]"] = 0.0
    wide.loc[wide["[P_BID]"] < 0.01, "[P_BID]"] = 0.0
    if messy_format:  # padded strings like the raw vendor export
        for c in ("[STRIKE]", "[C_BID]", "[C_ASK]", "[P_BID]", "[P_ASK]", "[C_IV]", "[P_IV]", "[UNDERLYING_LAST]"):
            wide[c] = wide[c].map(lambda v: f" {v:.6f} ")
        wide["[QUOTE_DATE]"] = " " + wide["[QUOTE_DATE]"] + " "
        wide["[EXPIRE_DATE]"] = " " + wide["[EXPIRE_DATE]"] + " "
    return wide, pd.DataFrame(truth)
