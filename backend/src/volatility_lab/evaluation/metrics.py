"""Masked forecast-error metrics in implied-vol *points* (1 point = 0.01 of IV).

Evaluation mask (identical for every model): the target cell holds a real value of the requested status
(``primary``: OBSERVED only; ``all``: observed or interpolated) AND the cell had a real value at the
forecast origin, so persistence is defined everywhere the mask is true. Missing is never imputed here.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from volatility_lab.features.panel import Prepared, target_arrays
from volatility_lab.surfaces.grid import OBSERVED

PTS = 100.0


def eval_mask(p: Prepared, positions: np.ndarray, kind: str = "primary") -> np.ndarray:
    ty, tst = target_arrays(p)
    y, st = ty[positions], tst[positions]
    avail_t = p.avail[p.origins[positions]]
    tgt = (st == OBSERVED) if kind == "primary" else (st > 0)
    return np.isfinite(y) & tgt & avail_t


def _stats(err: np.ndarray) -> dict:
    n = int(err.size)
    if n == 0:
        return {"mae": np.nan, "rmse": np.nan, "n_cells": 0}
    return {"mae": float(np.mean(np.abs(err))), "rmse": float(np.sqrt(np.mean(err ** 2))), "n_cells": n}


def overall(p: Prepared, positions, pred, mask) -> dict:
    y = target_arrays(p)[0][positions]
    err = (pred - y)[mask] * PTS
    out = _stats(err)
    out["n_days"] = int(mask.any(axis=1).sum())
    return out


def daily_mae(p: Prepared, positions, pred, mask) -> np.ndarray:
    """Per-origin-day mean absolute error (NaN where the day has no evaluable cell)."""
    y = target_arrays(p)[0][positions]
    e = np.where(mask, np.abs(pred - y) * PTS, np.nan)
    with np.errstate(invalid="ignore"):
        return np.nanmean(e, axis=1)


MIN_CELLS = 100  # research setting, not a derived threshold: groups with fewer evaluated cells are flagged


def breakdowns(p: Prepared, positions, pred, mask, rv_cuts, min_cells: int = MIN_CELLS) -> pd.DataFrame:
    """Rows: (group_type, group, mae, rmse, n_cells, insufficient_n). Groups: tenor, k, calendar year, regime.

    ``insufficient_n`` is True when ``n_cells < min_cells``; such rows are still returned, never dropped."""
    y = target_arrays(p)[0][positions]
    err = (pred - y) * PTS
    rows = []

    def add(gt, g, m):
        s = _stats(err[m])
        rows.append({"group_type": gt, "group": g, **s})

    for tau in np.unique(p.cell_tenor):
        add("tenor_days", int(tau), mask & (p.cell_tenor == tau)[None, :])
    for k in np.unique(p.cell_k):
        add("log_moneyness", float(k), mask & (p.cell_k == k)[None, :])
    yr = p.year[p.origins[positions]]
    for Y in np.unique(yr):
        add("origin_year", int(Y), mask & (yr == Y)[:, None])
    rv20 = p.rv[p.origins[positions], -1]
    lo, hi = rv_cuts
    for name, sel in (("low", rv20 <= lo), ("mid", (rv20 > lo) & (rv20 <= hi)), ("high", rv20 > hi)):
        add("rv_regime", name, mask & sel[:, None])
    out = pd.DataFrame(rows)
    out["insufficient_n"] = out["n_cells"] < min_cells
    return out


def rv_terciles(p: Prepared, train_positions) -> tuple:
    """Regime cut-offs from TRAINING origins only (longest realised-vol window)."""
    r = p.rv[p.origins[train_positions], -1]
    r = r[np.isfinite(r)]
    return float(np.quantile(r, 1 / 3)), float(np.quantile(r, 2 / 3))
