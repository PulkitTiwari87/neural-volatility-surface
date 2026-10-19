"""Surface panel -> leakage-safe forecasting dataset.

Every feature at origin ``t`` uses only rows ``<= t``. Targets are the surface ``h`` panel rows ahead.
Anything *fitted* (cell means used to fill never-seen cells, scalers, PCA) is fitted by the caller on
training rows only and passed in.

Cell index ``c = tenor_index * n_k + k_index`` (tenor-major).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np
import pandas as pd

from volatility_lab.config.settings import FeatureConfig


@dataclass
class Prepared:
    dates: np.ndarray        # (n,) epoch days
    year: np.ndarray         # (n,)
    spot: np.ndarray         # (n,)
    iv: np.ndarray           # (n, C) NaN where status == 0
    status: np.ndarray       # (n, C) int8
    avail: np.ndarray        # (n, C) bool: a real surface value exists on that day
    rv: np.ndarray           # (n, len(rv_windows)) annualised realised vol of the underlying, NaN early
    cell_tenor: np.ndarray   # (C,)
    cell_k: np.ndarray       # (C,)
    origins: np.ndarray      # (N,) row indices usable as forecast origins
    targets: np.ndarray      # (N,) row index of the target day
    horizon: int
    n_tenor: int
    n_k: int
    # Optional explicit target aligned with ``origins`` (N, C). ``None`` = the E-1 definition:
    # whatever the surface holds at ``targets``. Experiment E-2 fills them with the SAME-expiry value.
    target_iv: Optional[np.ndarray] = None
    target_status: Optional[np.ndarray] = None
    anchor_changed: Optional[np.ndarray] = None  # (N, C) bool: the nearest-expiry anchor differs at origin vs target
    target_name: str = "nearest_expiry"
    # Optional (n, n_tenor + 5) calendar block (experiment H3): days-to-expiry of the expiry anchoring each tenor on
    # that row (nominal tenor when none) and a Monday-Friday one-hot weekday. Row-local: uses only that row's date/quotes.
    calendar: Optional[np.ndarray] = None
    # Optional mean-reversion window (experiment H4): adds "surface minus its trailing ``mr_window``-row mean" to the
    # tabular / PCA features. Causal (rows <= t only). ``None`` = off.
    mr_window: Optional[int] = None

    @property
    def n_cells(self) -> int:
        return self.iv.shape[1]


def flatten_panel(panel: dict):
    n, nt, nk = panel["iv"].shape
    iv = panel["iv"].reshape(n, nt * nk)
    st = panel["status"].reshape(n, nt * nk)
    tenor = np.repeat(panel["tenor_days"], nk)
    k = np.tile(panel["k_nodes"], nt)
    return iv, st, tenor, k


def realized_vol(spot: np.ndarray, windows: Tuple[int, ...]) -> np.ndarray:
    """Annualised std of daily log returns over the last ``w`` rows (inclusive of today)."""
    r = pd.Series(np.log(spot)).diff()
    return np.column_stack([r.rolling(w).std().to_numpy() * np.sqrt(252.0) for w in windows])


def _flat_anchor(panel: dict) -> np.ndarray:
    """(n, C) expiry id anchoring each cell's tenor on that date (-1 = none); tenor-major like the cells."""
    return np.repeat(panel["anchor_expiry"], panel["k_nodes"].size, axis=1)


def anchor_switches(panel: dict, h: int) -> np.ndarray:
    """(n, C) bool, row t: the nearest-expiry anchor of the cell at t+h is a DIFFERENT expiry than at t."""
    a = _flat_anchor(panel)
    n = a.shape[0]
    sw = np.zeros(a.shape, dtype=bool)
    sw[: n - h] = (a[h:] != a[: n - h]) & (a[h:] >= 0) & (a[: n - h] >= 0)
    return sw


def fixed_expiry_targets(panel: dict, h: int):
    """Same-expiry target (experiment E-2). Returns ``(ty, tst)`` of shape (n, C), indexed by the ORIGIN row.

    For origin row ``t`` and a cell whose tenor is anchored on a real expiry ``E`` at ``t`` (status OBSERVED or
    INTERP_K), the target is the IV of THAT SAME expiry ``E`` at the same log-moneyness node on row ``t+h``.
    * The expiry is chosen from origin-date quotes only; the future is read only for the label itself.
    * If ``E`` has no usable slice on ``t+h`` (expired, too few quotes, node outside its quotes) the target is
      MISSING (status 0): censored, never imputed. Callers report the censoring counts.
    * status 3 = tight bracketing quotes on both dates, 2 = anchored but sparse on either date, 0 = missing.
    The cell's maturity shortens by ``h`` days between the two dates (a genuine roll-down effect).
    """
    n, nt, nk = panel["iv"].shape
    C = nt * nk
    anchor = _flat_anchor(panel)
    status = panel["status"].reshape(n, C)
    gap_tight = float(panel["gap_tight"]) if "gap_tight" in panel else 0.02
    lookup = {(int(r), int(e)): m for m, (r, e) in enumerate(zip(panel["slice_row"], panel["slice_expiry"]))}
    sv, sg = panel["slice_iv"], panel["slice_gap"]
    ty = np.full((n, C), np.nan)
    tst = np.zeros((n, C), dtype=np.int8)
    for t in range(n - h):
        for j in range(nt):
            e = anchor[t, j * nk]
            if e < 0:
                continue
            m = lookup.get((t + h, int(e)))
            if m is None:
                continue
            cols = slice(j * nk, (j + 1) * nk)
            v, g, o = sv[m], sg[m], status[t, cols]
            ok = np.isfinite(v) & (o >= 2)
            tight = ok & (o == 3) & (g <= gap_tight)
            ty[t, cols] = np.where(ok, v, np.nan)
            tst[t, cols] = np.where(tight, 3, np.where(ok, 2, 0))
    return ty, tst


def calendar_block(panel: dict) -> np.ndarray:
    """(n, n_tenor + 5): anchoring-expiry days-to-expiry per tenor, then weekday one-hot (Mon..Fri). Known at row t."""
    d = panel["dates"]
    dte = panel["anchor_expiry"].astype(float) - d[:, None]
    dte = np.where(panel["anchor_expiry"] >= 0, dte, panel["tenor_days"][None, :].astype(float))
    wd = (d + 3) % 7                       # epoch day 0 (1970-01-01) was a Thursday -> Monday = 0
    return np.hstack([dte, (wd[:, None] == np.arange(5)[None, :]).astype(float)])


def prepare(panel: dict, cfg: FeatureConfig, target: str = "nearest_expiry", calendar: bool = False,
            mr_window: Optional[int] = None) -> Prepared:
    if target not in ("nearest_expiry", "fixed_expiry"):
        raise ValueError(f"unknown target definition: {target}")
    iv, st, tenor, k = flatten_panel(panel)
    n = iv.shape[0]
    dates = panel["dates"]
    cal = dates.astype("datetime64[D]")
    year = cal.astype("datetime64[Y]").astype(int) + 1970
    rv = realized_vol(panel["spot"], cfg.rv_windows)
    min_hist = max(max(cfg.lags), cfg.seq_len - 1 + max(cfg.rv_windows))
    h = cfg.horizon
    t = np.arange(min_hist, n - h)
    gap_ok = (dates[t + h] - dates[t]) <= (h + 4)  # a missing stretch of days must not masquerade as "h days ahead"
    t = t[gap_ok]
    extra = {}
    if "anchor_expiry" in panel:
        extra["anchor_changed"] = anchor_switches(panel, h)[t]
    if target == "fixed_expiry":
        ty, tst = fixed_expiry_targets(panel, h)
        extra.update(target_iv=ty[t], target_status=tst[t])
    if calendar:
        extra["calendar"] = calendar_block(panel)
    if mr_window is not None:
        extra["mr_window"] = int(mr_window)
    return Prepared(dates=dates, year=year, spot=panel["spot"], iv=iv, status=st, avail=st > 0, rv=rv,
                    cell_tenor=tenor, cell_k=k, origins=t, targets=t + h, horizon=h,
                    n_tenor=len(panel["tenor_days"]), n_k=len(panel["k_nodes"]), target_name=target, **extra)


def cell_means(p: Prepared, rows: np.ndarray) -> np.ndarray:
    """Per-cell mean IV over ``rows`` (training rows only); cells never seen fall back to the global mean."""
    vals = np.where(p.avail[rows], p.iv[rows], np.nan)
    n = np.isfinite(vals).sum(axis=0)
    m = np.where(n > 0, np.nansum(vals, axis=0) / np.maximum(n, 1), np.nan)
    return np.where(np.isfinite(m), m, np.nanmean(m))


def causal_fill(p: Prepared, ffill_days: int, fill_values: np.ndarray) -> np.ndarray:
    """Forward-fill each cell for at most ``ffill_days`` rows (past only), then ``fill_values`` for the rest."""
    n, C = p.iv.shape
    cur = np.where(p.avail, p.iv, np.nan)
    out = np.empty((n, C))
    last = np.full(C, np.nan)
    age = np.full(C, np.inf)
    for t in range(n):
        has = np.isfinite(cur[t])
        last = np.where(has, cur[t], last)
        age = np.where(has, 0.0, age + 1.0)
        out[t] = np.where(age <= ffill_days, last, np.nan)
    return np.where(np.isfinite(out), out, fill_values[None, :])


def trailing_mean(a: np.ndarray, w: int) -> np.ndarray:
    """Mean of rows ``t-w+1..t`` (inclusive of t; shorter windows early on). Causal."""
    return pd.DataFrame(a).rolling(w, min_periods=1).mean().to_numpy()


def tabular_features(p: Prepared, filled: np.ndarray, cfg: FeatureConfig) -> np.ndarray:
    """(N, D): [s_t, s_t - s_{t-lag} for lag in lags, rv_t, availability fraction]. Rows = ``p.origins``."""
    t = p.origins
    parts = [filled[t]]
    for lag in cfg.lags:
        parts.append(filled[t] - filled[t - lag])
    parts.append(p.rv[t])
    parts.append(p.avail[t].mean(axis=1, keepdims=True))
    if p.calendar is not None:
        parts.append(p.calendar[t])
    if p.mr_window is not None:
        parts.append(filled[t] - trailing_mean(filled, p.mr_window)[t])
    return np.hstack(parts)


def sequence_features(p: Prepared, filled: np.ndarray, cfg: FeatureConfig) -> np.ndarray:
    """(N, L, 2C + n_rv): per day [filled surface, availability mask, realised vols] for rows t-L+1..t."""
    L = cfg.seq_len
    day = np.hstack([filled, p.avail.astype(float), np.nan_to_num(p.rv)] + ([p.calendar] if p.calendar is not None else []))
    idx = p.origins[:, None] + np.arange(-L + 1, 1)[None, :]
    return day[idx]


def target_arrays(p: Prepared):
    """``(y, y_status)`` aligned with ``p.origins``: target-day IV (NaN where missing) and its status."""
    if p.target_iv is not None:
        return p.target_iv, p.target_status
    return p.iv[p.targets], p.status[p.targets]
