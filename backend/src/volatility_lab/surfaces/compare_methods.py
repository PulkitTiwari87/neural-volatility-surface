"""Phase 2 comparison of candidate interpolation methods and quote-filter policies (evidence for DEC-006).

This module is **research evidence code, not an adopted method**: ``surfaces.grid`` keeps its production
behaviour (linear in k, linear total variance in T). Nothing here decides DEC-006.

Criteria (fixed before looking at results; see docs/research/PHASE2_SURFACE_COMPARISON.md):

* **Leave-one-out in k**: for each interior quote of an expiry slice, hide it, predict its IV from the
  remaining quotes of the same slice, compare. Interior only, so no method ever extrapolates.
* **Leave-one-expiry-out in T**: hide a whole expiry, predict each of its quotes from the two neighbouring
  expiries (``thin`` steps either side), compare. Neighbour IV at the quote's k comes from the same linear-in-k
  rule for every T-method, so only the T-rule differs.
* Errors are reported in **vol points** (decimal IV x 100) by moneyness region with ``n``; a region below
  ``MIN_N`` is flagged ``insufficient_n`` instead of being ranked.
* Quote filters: kept-quote counts, surface cell-status shares, and reconstruction error of kept quotes and of
  non-missing cells against the *known* generating surface (synthetic data only).
"""
from __future__ import annotations

import dataclasses
from typing import Callable, Dict, List

import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline, PchipInterpolator

from volatility_lab.config.settings import Config, DataConfig
from volatility_lab.surfaces import grid

MIN_N = 100                      # per-region sample floor for ranking (research setting, not a Phase 0 threshold)
REGIONS = (("put_wing k<-0.10", -np.inf, -0.10), ("put_body -0.10<=k<-0.02", -0.10, -0.02),
           ("atm -0.02<=k<0.02", -0.02, 0.02), ("call_body 0.02<=k<0.10", 0.02, 0.10),
           ("call_wing k>=0.10", 0.10, np.inf))


# ---------------------------------------------------------------- candidate methods (k direction)
def k_linear_iv(k, iv, T, kq):
    return np.interp(kq, k, iv)


def k_linear_total_variance(k, iv, T, kq):
    return np.sqrt(np.interp(kq, k, iv * iv * T) / T)


def k_pchip_iv(k, iv, T, kq):
    return PchipInterpolator(k, iv, extrapolate=False)(kq)


def k_cubic_spline_iv(k, iv, T, kq):
    if k.size < 4:
        return np.full_like(np.asarray(kq, dtype=float), np.nan)
    return CubicSpline(k, iv, extrapolate=False)(kq)


K_METHODS: Dict[str, Callable] = {"linear_iv (production)": k_linear_iv, "linear_total_variance": k_linear_total_variance,
                                  "pchip_iv": k_pchip_iv, "cubic_spline_iv": k_cubic_spline_iv}


# ---------------------------------------------------------------- candidate methods (T direction)
def t_linear_total_variance(T, Tlo, Thi, ivlo, ivhi):
    w = (T - Tlo) / (Thi - Tlo)
    return np.sqrt(((1 - w) * ivlo ** 2 * Tlo + w * ivhi ** 2 * Thi) / T)


def t_linear_iv(T, Tlo, Thi, ivlo, ivhi):
    w = (T - Tlo) / (Thi - Tlo)
    return (1 - w) * ivlo + w * ivhi


def t_nearest_expiry(T, Tlo, Thi, ivlo, ivhi):
    return np.where(abs(T - Tlo) <= abs(Thi - T), ivlo, ivhi)


T_METHODS: Dict[str, Callable] = {"linear_total_variance (production)": t_linear_total_variance,
                                  "linear_iv": t_linear_iv, "nearest_expiry": t_nearest_expiry}


# ---------------------------------------------------------------- evaluation
def _slices(quotes: pd.DataFrame):
    for (d, e), s in quotes.groupby(["date", "expiry"], sort=True):
        s = s.sort_values("k")
        yield d, e, float(s["T"].iloc[0]), s.k.to_numpy(), s.iv.to_numpy()


def loo_k(quotes: pd.DataFrame, methods: Dict[str, Callable] = K_METHODS, *, min_pts: int = 8,
          stride: int = 3, date_stride: int = 1) -> pd.DataFrame:
    """One row per (method, held-out quote): ``k, gap, err`` (prediction - quote, decimal IV; NaN if undefined)."""
    dates = np.unique(quotes.date.to_numpy())[::date_stride]
    rows: List[tuple] = []
    for d, e, T, k, iv in _slices(quotes[quotes.date.isin(dates)]):
        if k.size < min_pts:
            continue
        for i in range(1, k.size - 1, stride):
            keep = np.arange(k.size) != i
            gap = k[i + 1] - k[i - 1]
            for name, f in methods.items():
                pred = float(f(k[keep], iv[keep], T, np.array([k[i]]))[0])
                rows.append((name, int(d), int(e), T, k[i], gap, pred - iv[i]))
    return pd.DataFrame(rows, columns=["method", "date", "expiry", "T", "k", "gap", "err"])


def loo_expiry_t(quotes: pd.DataFrame, methods: Dict[str, Callable] = T_METHODS, *, thin: int = 1,
                 min_pts: int = 8, stride: int = 4, date_stride: int = 1) -> pd.DataFrame:
    """Hide expiry j, predict its quotes from expiries j-thin and j+thin. ``thin`` widens the maturity gap."""
    dates = np.unique(quotes.date.to_numpy())[::date_stride]
    rows: List[tuple] = []
    for d, sub in quotes[quotes.date.isin(dates)].groupby("date", sort=True):
        sl = [(T, k, iv) for _, _, T, k, iv in _slices(sub) if k.size >= min_pts]
        for j in range(thin, len(sl) - thin):
            (Tl, kl, vl), (T, k, iv), (Th, kh, vh) = sl[j - thin], sl[j], sl[j + thin]
            inside = (k >= max(kl[0], kh[0])) & (k <= min(kl[-1], kh[-1]))
            idx = np.flatnonzero(inside)[::stride]
            if idx.size == 0:
                continue
            ivlo, ivhi = np.interp(k[idx], kl, vl), np.interp(k[idx], kh, vh)
            for name, f in methods.items():
                pred = np.asarray(f(T, Tl, Th, ivlo, ivhi), dtype=float)
                for q, p in zip(idx, pred):
                    rows.append((name, int(d), T, Th - Tl, k[q], float(p - iv[q])))
    return pd.DataFrame(rows, columns=["method", "date", "T", "t_gap", "k", "err"])


def summarize_by_region(df: pd.DataFrame, min_n: int = MIN_N) -> pd.DataFrame:
    """Per (method, region): n, n_missing, MAE/RMSE/p95 in vol points; ``insufficient_n`` below ``min_n``."""
    out = []
    for name, g in df.groupby("method", sort=False):
        for label, lo, hi in REGIONS + (("ALL", -np.inf, np.inf),):
            r = g[(g.k >= lo) & (g.k < hi)]
            e = r.err.to_numpy()
            ok = np.isfinite(e)
            a = np.abs(e[ok]) * 100.0
            out.append({"method": name, "region": label, "n": int(ok.sum()), "n_missing": int((~ok).sum()),
                        "mae_vp": float(a.mean()) if a.size else np.nan,
                        "rmse_vp": float(np.sqrt((a ** 2).mean())) if a.size else np.nan,
                        "p95_vp": float(np.quantile(a, 0.95)) if a.size else np.nan,
                        "insufficient_n": bool(ok.sum() < min_n)})
    return pd.DataFrame(out)


# ---------------------------------------------------------------- quote-filter policies (synthetic truth)
FILTER_POLICIES: Dict[str, dict] = {
    "default (min_mid 0.05, spread 0.35)": {},
    "strict (min_mid 0.25, spread 0.10)": {"min_mid": 0.25, "max_rel_spread": 0.10},
    "loose (min_mid 0.01, spread 0.80)": {"min_mid": 0.01, "max_rel_spread": 0.80},
}


def filter_policy_report(wide: pd.DataFrame, truth: pd.DataFrame, true_sigma: Callable, base: Config,
                         policies: Dict[str, dict] = FILTER_POLICIES) -> pd.DataFrame:
    """Run ``build_otm_quotes`` + the production surface builder under each policy and score against the truth.

    ``truth`` has per-date ``level``/``skew``; ``true_sigma(k, T, level, skew)`` is the generating surface.
    Errors are vs the *generating* surface, so this is only meaningful on synthetic data.
    """
    from volatility_lab.validation.quotes import build_otm_quotes
    lv = {int(np.datetime64(d, "D").astype("int64")): (L, S) for d, L, S in zip(truth["date"], truth["level"], truth["skew"])}
    rows = []
    for name, over in policies.items():
        dcfg: DataConfig = dataclasses.replace(base.data, **over)
        quotes, ledger, _ = build_otm_quotes(wide, dcfg)
        LS = np.array([lv[int(d)] for d in quotes.date.to_numpy()])
        qerr = np.abs(quotes.iv.to_numpy() - true_sigma(quotes.k.to_numpy(), quotes["T"].to_numpy(), LS[:, 0], LS[:, 1])) * 100
        panel = grid.build_surface_panel(quotes, base.surface)
        cell_err = []
        for i, d in enumerate(panel["dates"]):
            L, S = lv[int(d)]
            for j, tau in enumerate(panel["tenor_days"]):
                ok = panel["status"][i, j] > 0
                if ok.any():
                    t = true_sigma(panel["k_nodes"][ok], tau / 365.0, L, S)
                    cell_err.append(np.abs(panel["iv"][i, j][ok] - t) * 100)
        cell_err = np.concatenate(cell_err)
        st = grid.status_counts(panel)
        n_cells = int(panel["status"].size)
        rows.append({"policy": name, "rows_in": ledger.rows_in, "quotes_kept": ledger.kept,
                     "kept_share": ledger.kept / ledger.rows_in, "quote_mae_vp": float(qerr.mean()),
                     "quote_p95_vp": float(np.quantile(qerr, 0.95)), "quote_max_vp": float(qerr.max()),
                     **{f"cells_{k}": v / n_cells for k, v in st.items()},
                     "cell_mae_vp": float(cell_err.mean()), "cell_p95_vp": float(np.quantile(cell_err, 0.95)),
                     "cell_max_vp": float(cell_err.max()), "n_cells_scored": int(cell_err.size)})
    return pd.DataFrame(rows)
