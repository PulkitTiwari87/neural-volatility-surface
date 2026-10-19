"""No-arbitrage and quality diagnostics on a built surface (FLAGS ONLY: the surface is never modified or repaired).

Checked on cells that are observed or interpolated; every example says whether an interpolated cell was involved.
  calendar : total variance w = iv^2 * T must not decrease with T at a fixed forward log-moneyness node.
  butterfly: discounted call price must be convex in strike within each expiry (consecutive available nodes).
  slope    : discounted call price slope in strike must lie in [-discount, 0].
Necessary conditions only: passing them does not prove the surface is arbitrage-free."""
import math
from typing import Dict, List, Optional, Sequence

from phase0.bsm import black76_price

AVAILABLE = ("observed", "interpolated")


def check_surface(rows: Sequence[Optional[dict]], iv, status, k_nodes: Sequence[float], rate: float, tol: float = 1e-10, cap: int = 50) -> dict:
    """rows[i] = {"T": float, "F": float} for expiry i, or None when the expiry has no forward (all cells missing)."""
    avail = lambda i, j: rows[i] is not None and iv[i][j] is not None and status[i][j] in AVAILABLE
    interp = lambda i, j: status[i][j] == "interpolated"
    cal: List[dict] = []
    n_cal = 0
    for j, k in enumerate(k_nodes):
        pts = sorted((rows[i]["T"], i) for i in range(len(rows)) if avail(i, j))
        for (t1, i1), (t2, i2) in zip(pts, pts[1:]):
            n_cal += 1
            w1, w2 = iv[i1][j] ** 2 * t1, iv[i2][j] ** 2 * t2
            if w2 < w1 - tol:
                cal.append({"k": k, "T1": t1, "T2": t2, "w1": w1, "w2": w2, "shortfall": w1 - w2, "uses_interpolated": interp(i1, j) or interp(i2, j)})
    bfly: List[dict] = []
    slope: List[dict] = []
    n_b = n_s = 0
    for i, row in enumerate(rows):
        if row is None:
            continue
        T, F, df = row["T"], row["F"], math.exp(-rate * row["T"])
        pts = []
        for j, k in enumerate(k_nodes):
            if avail(i, j):
                K = F * math.exp(k)
                pts.append((K, black76_price(F, K, T, rate, iv[i][j], True), j))
        slopes = [((b[1] - a[1]) / (b[0] - a[0]), a[2], b[2]) for a, b in zip(pts, pts[1:])]
        for s, ja, jb in slopes:
            n_s += 1
            if s > tol or s < -df - tol:
                slope.append({"T": T, "k_pair": [k_nodes[ja], k_nodes[jb]], "slope": s, "bounds": [-df, 0.0], "uses_interpolated": interp(i, ja) or interp(i, jb)})
        for (s1, ja, jb), (s2, _, jc) in zip(slopes, slopes[1:]):
            n_b += 1
            if s2 < s1 - tol:
                bfly.append({"T": T, "k_triple": [k_nodes[ja], k_nodes[jb], k_nodes[jc]], "convexity_shortfall": s1 - s2,
                             "uses_interpolated": interp(i, ja) or interp(i, jb) or interp(i, jc)})
    st: Dict[str, int] = {}
    for r in status:
        for c in r:
            st[c] = st.get(c, 0) + 1
    n_cells = sum(st.values())
    return {"flags_only": True, "tolerance": tol,
            "checked": {"calendar_pairs": n_cal, "butterfly_triples": n_b, "slope_pairs": n_s},
            "calendar_violations": len(cal), "butterfly_violations": len(bfly), "slope_bound_violations": len(slope),
            "examples": {"calendar": cal[:cap], "butterfly": bfly[:cap], "slope": slope[:cap]},
            "cell_status_counts": st, "cells": n_cells, "available_fraction": (sum(st.get(a, 0) for a in AVAILABLE) / n_cells) if n_cells else 0.0,
            "note": "necessary conditions on available cells only; no repair is applied"}
