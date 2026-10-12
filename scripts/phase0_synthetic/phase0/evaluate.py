"""Walk-forward evaluation, metrics and block bootstrap. SYNTHETIC SPIKE.

Comparable cells at origin t: cells OBSERVED at t+1 for which EVERY compared
forecaster produced a value. Target-observed cells that are not comparable are
counted in n_missing (never dropped silently).
"""
import math
import random
from typing import Dict, List, Optional, Sequence

from .forecast import HistoryView
from .surface import CellStatus, Surface


def walk_forward(surfaces: Sequence[Surface], forecasters: Dict[str, object], k_nodes: Sequence[float],
                 maturities: Sequence[float], min_history: int = 60) -> dict:
    records: List[dict] = []
    per_origin_missing: Dict[int, int] = {}
    skipped: List[int] = []
    for t in range(min_history - 1, len(surfaces) - 1):
        hist = HistoryView(surfaces, t)
        preds = {name: f.predict(hist) for name, f in forecasters.items()}  # fitted on days <= t only
        if any(p is None for p in preds.values()):
            skipped.append(t)
            continue
        target, origin = surfaces[t + 1], surfaces[t]  # target revealed only after forecasting
        n_missing = 0
        for mi, T in enumerate(maturities):
            for ki, k in enumerate(k_nodes):
                if target.status[mi][ki] is not CellStatus.OBSERVED:
                    continue
                vals = {name: preds[name][mi][ki] for name in preds}
                if any(v is None for v in vals.values()):
                    n_missing += 1
                    continue
                records.append({"t": t, "mi": mi, "ki": ki, "k": k, "T": T, "y": target.iv[mi][ki],
                                "origin_status": origin.status[mi][ki], "pred": vals})
        per_origin_missing[t] = n_missing
    return {"records": records, "n_missing_by_origin": per_origin_missing, "skipped_origins": skipped}


def metrics(records: Sequence[dict], name: str, cell_filter=None) -> dict:
    sel = [r for r in records if cell_filter is None or cell_filter(r)]
    n = len(sel)
    if n == 0:
        return {"n": 0, "n_origins": 0, "mae": None, "rmse": None, "mae_volpts": None, "rmse_volpts": None}
    errs = [r["pred"][name] - r["y"] for r in sel]
    mae = sum(abs(e) for e in errs) / n
    rmse = math.sqrt(sum(e * e for e in errs) / n)
    return {"n": n, "n_origins": len({r["t"] for r in sel}), "mae": mae, "rmse": rmse,
            "mae_volpts": 100.0 * mae, "rmse_volpts": 100.0 * rmse}


def per_origin_mse(records: Sequence[dict], name: str) -> Dict[int, float]:
    acc: Dict[int, List[float]] = {}
    for r in records:
        acc.setdefault(r["t"], []).append((r["pred"][name] - r["y"]) ** 2)
    return {t: sum(v) / len(v) for t, v in sorted(acc.items())}


def maturity_bucket(T: float) -> str:
    return "<=91d" if T <= 91 / 365 + 1e-9 else ("182d" if T <= 182 / 365 + 1e-9 else ">=273d")


def moneyness_bucket(k: float) -> str:
    return "k<-0.05" if k < -0.05 - 1e-9 else ("|k|<=0.05" if k <= 0.05 + 1e-9 else "k>0.05")


def bucket_metrics(records: Sequence[dict], name: str) -> dict:
    out = {}
    for mb in ("<=91d", "182d", ">=273d"):
        for kb in ("k<-0.05", "|k|<=0.05", "k>0.05"):
            out["%s|%s" % (mb, kb)] = metrics(
                records, name, lambda r, mb=mb, kb=kb: maturity_bucket(r["T"]) == mb and moneyness_bucket(r["k"]) == kb)
    return out


def block_bootstrap_ci(d: Sequence[float], block: int, B: int, seed: int, alpha: float = 0.05):
    """Moving-block bootstrap percentile interval for mean(d). Returns (mean, lo, hi)."""
    n = len(d)
    if n == 0:
        return None, None, None
    b = min(block, n)
    rng = random.Random(seed)
    n_blocks = -(-n // b)
    means = []
    for _ in range(B):
        total, count = 0.0, 0
        for _ in range(n_blocks):
            s = int(rng.random() * (n - b + 1))
            chunk = d[s:s + b]
            take = min(len(chunk), n - count)
            total += sum(chunk[:take])
            count += take
        means.append(total / n)
    means.sort()
    lo = means[int(alpha / 2.0 * B)]
    hi = means[int((1.0 - alpha / 2.0) * B) - 1]
    return sum(d) / n, lo, hi


def compare(records: Sequence[dict], base: str, model: str, block: int = 5, B: int = 2000, seed: int = 0) -> dict:
    lb, lm = per_origin_mse(records, base), per_origin_mse(records, model)
    origins = sorted(set(lb) & set(lm))
    d = [lb[t] - lm[t] for t in origins]
    mean_d, lo, hi = block_bootstrap_ci(d, block, B, seed)
    mb, mm = metrics(records, base), metrics(records, model)
    mean_base = sum(lb[t] for t in origins) / len(origins) if origins else None
    mean_model = sum(lm[t] for t in origins) / len(origins) if origins else None
    return {"base": base, "model": model, "n_origins": len(origins), "mean_d": mean_d, "ci_lo": lo, "ci_hi": hi,
            "improvement_detected": (lo is not None and lo > 0.0),
            "mse_ratio": (mm["rmse"] ** 2) / (mb["rmse"] ** 2) if mb["rmse"] else None,  # pooled over cells
            "rmse_ratio": mm["rmse"] / mb["rmse"] if mb["rmse"] else None,
            "rmse_rel_reduction": 1.0 - mm["rmse"] / mb["rmse"] if mb["rmse"] else None,
            # audit v2 (additive): the estimand the CI is actually about (equal weight per origin) and dependence of d_t
            "mse_ratio_origin_mean": (mean_model / mean_base) if mean_base else None,
            "lag1_autocorr_d": lag1_autocorr(d)}


def lag1_autocorr(d: Sequence[float]) -> Optional[float]:
    n = len(d)
    if n < 3:
        return None
    m = sum(d) / n
    den = sum((x - m) ** 2 for x in d)
    if den == 0.0:
        return None
    return sum((d[i] - m) * (d[i + 1] - m) for i in range(n - 1)) / den


def analytic_rel_sd(records: Sequence[dict], sigma: Sequence[float], phi: Optional[float], n_origins: int,
                    max_lag: int = 400) -> Optional[float]:
    """Relative SD of the realized persistence MSE around its analytic expectation (Group A cells).

    Per-origin MSE is a Gaussian quadratic form Q_t = sum_jl M_jl D_j D_l with D = factor changes (independent
    factors, autocovariance g_j(h)); Cov(Q_t, Q_{t+h}) = 2 sum_jl M_jl^2 g_j(h) g_l(h), so
    LRV = 2 sum_jl M_jl^2 [g_j(0) g_l(0) + 2 sum_{h>=1} g_j(h) g_l(h)] and rel_sd = sqrt(LRV / N) / E[Q].
    RW: g(0)=s^2, g(h)=0.   AR(1): g(0)=2 s^2/(1+phi), g(h)=-s^2 phi^(h-1) (1-phi)/(1+phi).
    M = mean of (1,k,k^2)(1,k,k^2)^T over the comparable cells (approximation: M varies slightly by origin).
    Derived POST HOC in the Phase 0 audit; the v1 +-15% tolerance had no such derivation."""
    if not records or n_origins <= 0:
        return None
    M = [[0.0] * 3 for _ in range(3)]
    for r in records:
        p = (1.0, r["k"], r["k"] ** 2)
        for i in range(3):
            for j in range(3):
                M[i][j] += p[i] * p[j]
    M = [[v / len(records) for v in row] for row in M]

    def g(j: int, h: int) -> float:
        s2 = sigma[j] ** 2
        if phi is None:
            return s2 if h == 0 else 0.0
        if h == 0:
            return 2.0 * s2 / (1.0 + phi)
        return -s2 * (phi ** (h - 1)) * (1.0 - phi) / (1.0 + phi)

    eq = sum(M[j][j] * g(j, 0) for j in range(3))
    lrv = 0.0
    for j in range(3):
        for l in range(3):
            c = g(j, 0) * g(l, 0) + 2.0 * sum(g(j, h) * g(l, h) for h in range(1, max_lag + 1))
            lrv += 2.0 * M[j][l] ** 2 * c
    return math.sqrt(lrv / n_origins) / eq


def analytic_persistence_mse(records: Sequence[dict], sigma: Sequence[float], kappa: float) -> Optional[float]:
    """Expected persistence MSE on Group A cells: kappa * mean(sig_L^2 + sig_S^2 k^2 + sig_C^2 k^4)."""
    if not records:
        return None
    return kappa * sum(sigma[0] ** 2 + sigma[1] ** 2 * r["k"] ** 2 + sigma[2] ** 2 * r["k"] ** 4 for r in records) / len(records)
