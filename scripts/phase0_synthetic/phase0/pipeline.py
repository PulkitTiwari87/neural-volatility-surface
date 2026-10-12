"""End-to-end SYNTHETIC pipeline: validate -> forward -> IV -> surface. SYNTHETIC SPIKE."""
import math
import statistics
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List

from .iv import IVStatus, SolverConfig, implied_vol
from .quotes import QualityPolicy, infer_forward, mid, select_otm, validate_day
from .surface import CellStatus, SurfaceConfig, build_surface
from .synth import World, true_iv

CLEAN_DEFECTS = ("NEGATIVE_PRICE", "CROSSED_MARKET", "ZERO_BID", "MISSING_FIELD", "DUPLICATE")


@dataclass(frozen=True)
class PipelineConfig:
    forward_mode: str = "parity"  # "parity" (inferred) or "true" (oracle forward, diagnostic only)
    policy: QualityPolicy = field(default_factory=QualityPolicy)
    solver: SolverConfig = field(default_factory=SolverConfig)
    surface: SurfaceConfig = field(default_factory=SurfaceConfig)


def run_pipeline(world: World, pcfg: PipelineConfig = PipelineConfig()) -> dict:
    cfg = world.cfg
    surfaces = []
    totals = Counter()
    reasons = Counter()
    solver_counts = Counter()
    injected = Counter()
    per_day_reconciled = True
    unalignable = 0
    above_in_unalignable = 0
    max_snap, n_snapped, max_slope_bound = 0.0, 0, 0.0
    max_obs_err = 0.0
    errs: List[float] = []
    max_cell_err = 0.0
    n_obs = 0
    n_cells_checked = 0
    for t, day in enumerate(world.days):
        retained, rep = validate_day(day.quotes, pcfg.policy)
        totals["ingested"] += rep.ingested
        totals["retained"] += rep.retained
        totals["excluded"] += rep.excluded
        if not rep.conserved:
            per_day_reconciled = False
        for name, c in rep.counts.items():
            reasons[name] += c
        for name, c in day.injected.items():
            injected[name] += c
        for name in CLEAN_DEFECTS:
            if rep.counts[name] != day.injected[name]:
                per_day_reconciled = False
        obs_by_mat: List[list] = []
        x = world.factors[t]
        for mi, T in enumerate(cfg.maturities):
            qs = [q for q in retained if q.mat_idx == mi]
            F_hat = day.forwards[mi] if pcfg.forward_mode == "true" else infer_forward(qs, T, cfg.r)
            if F_hat is None:
                unalignable += 1
                above_in_unalignable += sum(1 for q in day.quotes if q.mat_idx == mi
                                            and day.ledger.get(q.record_id) == "ABOVE_UPPER_BOUND")
                obs_by_mat.append([])
                continue
            obs = []
            for q in select_otm(qs, F_hat):
                res = implied_vol(mid(q), F_hat, q.strike, T, cfg.r, q.is_call, pcfg.solver)
                solver_counts[res.status.value] += 1
                if res.iv is None:
                    continue
                k_hat = math.log(q.strike / F_hat)
                obs.append((k_hat, res.iv))
                k_true = math.log(q.strike / day.forwards[mi])
                err = abs(res.iv - true_iv(x, k_true, T))
                max_obs_err = max(max_obs_err, err)
                errs.append(err)
                n_obs += 1
            obs_by_mat.append(obs)
        surf = build_surface(t, obs_by_mat, pcfg.surface)
        max_snap = max(max_snap, surf.max_snap_dk)
        n_snapped += surf.n_snapped
        # |dIV/dk| <= |S| + 2|C| * max|node| over the grid (used only for the tolerance-consistency bound)
        node_max = max(abs(k) for k in pcfg.surface.k_nodes)
        max_slope_bound = max(max_slope_bound, abs(x[1]) + 2.0 * abs(x[2]) * node_max)
        for mi, T in enumerate(cfg.maturities):
            for ki, node in enumerate(pcfg.surface.k_nodes):
                if surf.status[mi][ki] is CellStatus.OBSERVED:
                    max_cell_err = max(max_cell_err, abs(surf.iv[mi][ki] - true_iv(x, node, T)))
                    n_cells_checked += 1
        surfaces.append(surf)
    status_totals = Counter()
    for s in surfaces:
        for row in s.status:
            for c in row:
                status_totals[c.value] += 1
    diag: Dict[str, object] = {
        "n_days": len(world.days),
        "validation": {"ingested": totals["ingested"], "retained": totals["retained"], "excluded": totals["excluded"],
                       "by_reason": dict(reasons), "conserved_every_day": per_day_reconciled and
                       totals["ingested"] == totals["retained"] + totals["excluded"]},
        "injected_defects": dict(injected),
        "defect_counts_match_exactly": all(reasons[n] == injected[n] for n in CLEAN_DEFECTS) and per_day_reconciled,
        "solver_status_counts": dict(solver_counts),
        "above_bound_injected": injected["ABOVE_UPPER_BOUND"],
        "above_bound_detected_by_solver": solver_counts[IVStatus.PRICE_ABOVE_UPPER_BOUND.value],
        "unalignable_expiries": unalignable,
        "above_bound_injected_in_unalignable_expiries": above_in_unalignable,
        "node_matching": {"tol_k": pcfg.surface.tol_k, "max_snap_dk": max_snap, "n_snapped_cells": n_snapped,
                          "max_slope_bound": max_slope_bound,
                          "cell_bias_bound": max_slope_bound * max_snap},  # audit v2 (additive diagnostics)
        "cell_status_totals": dict(status_totals),
        "recovery": {"n_iv_observations": n_obs, "max_abs_obs_error": max_obs_err,
                     "median_abs_obs_error": statistics.median(errs) if errs else None,
                     "n_observed_cells_checked": n_cells_checked, "max_abs_observed_cell_error": max_cell_err},
        "forward_mode": pcfg.forward_mode,
    }
    return {"surfaces": surfaces, "diag": diag}
