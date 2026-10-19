"""Constant-maturity implied-volatility surfaces on a fixed (tenor, log-moneyness) grid.

Cell status (the Q-25 fix: *observed* is defined by where real quotes are, not by grid coincidence):

* ``OBSERVED`` (3): an expiry lies within ``tol`` of the tenor AND the two real quotes bracketing the node
  in log-moneyness are closer than ``gap_tight``. The value is a linear interpolation *between those two
  adjacent real quotes of that one expiry* (second-order exact for strikes this dense).
* ``INTERP_K`` (2): same expiry anchor, but the bracketing quotes are far apart (sparse wing).
* ``INTERP_T`` (1): no expiry near the tenor; linear interpolation of total variance ``iv^2 * T`` between
  the two bracketing expiries.
* ``MISSING`` (0): outside the range of real quotes in k, or the tenor is not bracketed by expiries.
  **Nothing is ever extrapolated.**
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from volatility_lab.config.settings import SurfaceConfig

MISSING, INTERP_T, INTERP_K, OBSERVED = 0, 1, 2, 3
STATUS_LABELS = {MISSING: "missing", INTERP_T: "interpolated_T", INTERP_K: "interpolated_k", OBSERVED: "observed"}


def _slice_nodes(k: np.ndarray, iv: np.ndarray, nodes: np.ndarray):
    """Linear-in-k node values for one expiry slice; NaN outside [k.min, k.max]. Also the bracketing gap."""
    val = np.full(nodes.size, np.nan)
    gap = np.full(nodes.size, np.nan)
    inside = (nodes >= k[0]) & (nodes <= k[-1])
    if inside.any():
        val[inside] = np.interp(nodes[inside], k, iv)
        hi = np.clip(np.searchsorted(k, nodes[inside], side="left"), 1, k.size - 1)
        gap[inside] = k[hi] - k[hi - 1]
    return val, gap


def build_day_surface(day_q: pd.DataFrame, cfg: SurfaceConfig):
    """One date -> ``(iv[nt,nk], status[nt,nk])``."""
    iv, status, _ = build_day_surface_ex(day_q, cfg)
    return iv, status


def build_day_surface_ex(day_q: pd.DataFrame, cfg: SurfaceConfig):
    """One date -> ``(iv, status, extra)``.

    ``extra`` carries what a *tracked-expiry* target needs, all computed from this date's quotes only:
    ``anchor[nt]`` (expiry id of the real expiry anchoring each tenor, -1 if none) and the per-expiry slice
    arrays ``slice_expiry[M]``, ``slice_iv[M,nk]``, ``slice_gap[M,nk]``.
    """
    nodes = np.asarray(cfg.k_nodes, dtype=float)
    nt, nk = len(cfg.tenor_days), nodes.size
    exp_T, exp_id, vals, gaps = [], [], [], []
    for eid, s in day_q.groupby("expiry", sort=True):
        if len(s) < cfg.min_quotes_per_slice:
            continue
        k = s.k.to_numpy()
        order = np.argsort(k)
        v, g = _slice_nodes(k[order], s.iv.to_numpy()[order], nodes)
        exp_T.append(float(s["T"].iloc[0]))
        exp_id.append(int(eid))
        vals.append(v)
        gaps.append(g)
    iv = np.full((nt, nk), np.nan)
    status = np.zeros((nt, nk), dtype=np.int8)
    anchor = np.full(nt, -1, dtype=np.int64)
    if not exp_T:
        return iv, status, {"anchor": anchor, "slice_expiry": np.zeros(0, np.int64),
                            "slice_iv": np.zeros((0, nk)), "slice_gap": np.zeros((0, nk))}
    exp_T = np.asarray(exp_T)
    V = np.vstack(vals)
    G = np.vstack(gaps)
    valid = np.isfinite(V)
    for j, tau in enumerate(cfg.tenor_days):
        Tt = tau / 365.0
        tol = max(cfg.tol_obs_days / 365.0, cfg.tol_obs_frac * Tt)
        near = int(np.argmin(np.abs(exp_T - Tt)))
        anchored = abs(exp_T[near] - Tt) <= tol
        if anchored:
            anchor[j] = exp_id[near]
        for i in range(nk):
            if anchored and valid[near, i]:
                iv[j, i] = V[near, i]
                status[j, i] = OBSERVED if G[near, i] <= cfg.gap_tight else INTERP_K
                continue
            lo_idx = np.flatnonzero(valid[:, i] & (exp_T <= Tt))
            hi_idx = np.flatnonzero(valid[:, i] & (exp_T >= Tt))
            if lo_idx.size == 0 or hi_idx.size == 0:
                continue  # not bracketed: never extrapolate
            lo, hi = lo_idx[-1], hi_idx[0]
            if lo == hi:
                continue
            w = (Tt - exp_T[lo]) / (exp_T[hi] - exp_T[lo])
            var = (1 - w) * V[lo, i] ** 2 * exp_T[lo] + w * V[hi, i] ** 2 * exp_T[hi]
            iv[j, i] = np.sqrt(var / Tt)
            status[j, i] = INTERP_T
    return iv, status, {"anchor": anchor, "slice_expiry": np.asarray(exp_id, dtype=np.int64),
                        "slice_iv": V, "slice_gap": G}


def build_surface_panel(quotes: pd.DataFrame, cfg: SurfaceConfig) -> dict:
    """All dates -> arrays ``iv[n,nt,nk]`` (NaN where missing), ``status[n,nt,nk]``, ``dates`` (epoch days)."""
    dates, spots, ivs, sts, nq = [], [], [], [], []
    anchors, s_row, s_exp, s_iv, s_gap = [], [], [], [], []
    bounds = np.flatnonzero(np.diff(quotes.date.to_numpy()) != 0) + 1
    starts = np.r_[0, bounds]
    ends = np.r_[bounds, len(quotes)]
    for a, b in zip(starts, ends):
        day = quotes.iloc[a:b]
        iv, st, ex = build_day_surface_ex(day, cfg)
        if not (st > 0).any():
            continue
        row = len(dates)
        anchors.append(ex["anchor"])
        s_row.append(np.full(len(ex["slice_expiry"]), row, dtype=np.int64))
        s_exp.append(ex["slice_expiry"]); s_iv.append(ex["slice_iv"]); s_gap.append(ex["slice_gap"])
        dates.append(int(day.date.iloc[0]))
        spots.append(float(day.spot.iloc[0]))
        nq.append(len(day))
        ivs.append(iv)
        sts.append(st)
    if not dates:
        raise ValueError("no date produced a surface")
    return {"dates": np.asarray(dates, dtype=np.int64), "spot": np.asarray(spots), "n_quotes": np.asarray(nq),
            "iv": np.stack(ivs), "status": np.stack(sts),
            "gap_tight": np.asarray(cfg.gap_tight), "anchor_expiry": np.stack(anchors), "slice_row": np.concatenate(s_row), "slice_expiry": np.concatenate(s_exp),
            "slice_iv": np.vstack(s_iv), "slice_gap": np.vstack(s_gap),
            "tenor_days": np.asarray(cfg.tenor_days), "k_nodes": np.asarray(cfg.k_nodes)}


def status_counts(panel: dict) -> dict:
    st = panel["status"]
    return {STATUS_LABELS[c]: int((st == c).sum()) for c in (OBSERVED, INTERP_K, INTERP_T, MISSING)}
