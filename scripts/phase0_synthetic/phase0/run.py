"""Run the SYNTHETIC feasibility experiment and write a run record. SYNTHETIC SPIKE.

  python -m phase0.run single --world AR --seed 20261013 --days 300
  python -m phase0.run study  --first-seed 20261100 --n-seeds 10 --days 300

All data are synthetic (origin = "synthetic"). Nothing here reads real market data.
"""
import argparse
import hashlib
import json
import platform
import sys
import time
from dataclasses import asdict, replace
from pathlib import Path

from . import SYNTHETIC_BANNER
from .evaluate import (analytic_persistence_mse, analytic_rel_sd, bucket_metrics, compare, metrics, walk_forward)
from .forecast import FactorAR1Forecaster, OracleARForecaster, PersistenceForecaster
from .pipeline import PipelineConfig, run_pipeline
from .surface import CellStatus, SurfaceConfig
from .synth import WorldConfig, data_hash, generate_world, term

REPO_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = REPO_ROOT / "experiments" / "phase0_synthetic"

# Frozen in docs/research/PHASE0_FEASIBILITY_PLAN.md section 9.4 (before any run)
TOL = {"recovery_abs": 1e-8, "analytic_rel": 0.15, "ar1_ratio": (0.65, 0.90), "oracle_ratio": (0.63, 0.87),
       "rw_false_positive_max": 2, "ar_detect_min": 9, "oracle_equal_abs": 1e-9,
       # audit v2 (POST HOC, not part of the v1 pre-registration):
       "bias_slack": 1e-11, "z_max": 3.0}


def _round(obj, nd=12):
    if isinstance(obj, float):
        return round(obj, nd)
    if isinstance(obj, dict):
        return {str(k): _round(v, nd) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_round(v, nd) for v in obj]
    return obj


def code_hashes():
    base = Path(__file__).resolve().parent
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(base.glob("*.py"))}


def fast_world_config(name: str, seed: int, n_days: int = 150) -> WorldConfig:
    """Cheaper configuration used by unit tests (coarser chain)."""
    return WorldConfig(name=name, seed=seed, n_days=n_days, strike_step=0.05, n_offgrid=2)


def run_single(wcfg: WorldConfig, pcfg: PipelineConfig = None, min_history: int = 60, block: int = 5,
               B: int = 2000, quiet: bool = True) -> dict:
    pcfg = pcfg or PipelineConfig()
    t0 = time.time()
    world = generate_world(wcfg)
    t1 = time.time()
    out = run_pipeline(world, pcfg)
    t2 = time.time()
    scfg: SurfaceConfig = pcfg.surface
    phi_true = wcfg.phi if wcfg.name == "AR" else 1.0
    fcs = {
        "persistence": PersistenceForecaster(),
        "factor_ar1": FactorAR1Forecaster(scfg.k_nodes, wcfg.maturities, term),
        "oracle_ar": OracleARForecaster(scfg.k_nodes, wcfg.maturities, term, wcfg.mu, phi_true),
    }
    wf = walk_forward(out["surfaces"], fcs, scfg.k_nodes, wcfg.maturities, min_history)
    t3 = time.time()
    rec = wf["records"]
    rec_a = [r for r in rec if r["origin_status"] is CellStatus.OBSERVED]
    rec_b = [r for r in rec if r["origin_status"] is CellStatus.INTERPOLATED]
    res = {"metrics_all": {n: metrics(rec, n) for n in fcs},
           "metrics_group_A_observed_at_t": {n: metrics(rec_a, n) for n in fcs},
           "metrics_group_B_interpolated_at_t": {n: metrics(rec_b, n) for n in fcs},
           "buckets_persistence": bucket_metrics(rec, "persistence"),
           "buckets_factor_ar1": bucket_metrics(rec, "factor_ar1"),
           "n_origins_evaluated": len({r["t"] for r in rec}), "n_origins_skipped": len(wf["skipped_origins"]),
           "n_target_observed_not_comparable": sum(wf["n_missing_by_origin"].values())}
    cmp_ar1 = compare(rec, "persistence", "factor_ar1", block, B, wcfg.seed + 1)
    cmp_orc = compare(rec, "persistence", "oracle_ar", block, B, wcfg.seed + 1)
    kappa = 1.0 if wcfg.name == "RW" else 2.0 / (1.0 + wcfg.phi)
    mse_a = metrics(rec_a, "persistence")["rmse"]
    mse_a = None if mse_a is None else mse_a ** 2
    expected = analytic_persistence_mse(rec_a, wcfg.sigma, kappa)
    rel_dev = None if not expected else mse_a / expected - 1.0
    oracle_gap = max((abs(r["pred"]["oracle_ar"] - r["pred"]["persistence"]) for r in rec_a), default=None)
    clean = wcfg.tick is None
    hyp = {}
    d = out["diag"]
    hyp["H-S1_recovery"] = {"max_abs_observed_cell_error": d["recovery"]["max_abs_observed_cell_error"],
                            "pass": (d["recovery"]["max_abs_observed_cell_error"] <= TOL["recovery_abs"]) if clean else None}
    nm = d["node_matching"]
    # POST HOC (audit v2): tolerance-consistent version of H-S1 - the cell error may not exceed the analytic bias bound
    # |dIV/dk| * max snap distance (+ numerical slack). The original H-S1 above is retained unchanged.
    hyp["H-S1b_POST_HOC_bias_bound"] = {
        "max_abs_observed_cell_error": d["recovery"]["max_abs_observed_cell_error"], "cell_bias_bound": nm["cell_bias_bound"],
        "max_snap_dk": nm["max_snap_dk"], "n_snapped_cells": nm["n_snapped_cells"], "tol_k": nm["tol_k"],
        "pass": (d["recovery"]["max_abs_observed_cell_error"] <= nm["cell_bias_bound"] + TOL["bias_slack"]) if clean else None}
    hyp["H-S2_conservation_and_defects"] = {
        "conserved_every_day": d["validation"]["conserved_every_day"],
        "defect_counts_match_exactly": d["defect_counts_match_exactly"],
        "above_bound_match": d["above_bound_injected"] == d["above_bound_detected_by_solver"],
        "unalignable_expiries": d["unalignable_expiries"],
        "pass": (d["validation"]["conserved_every_day"] and d["defect_counts_match_exactly"]
                 and d["above_bound_injected"] == d["above_bound_detected_by_solver"]
                 and d["unalignable_expiries"] == 0) if clean else None}
    # POST HOC (added after the pre-registered H-S2 failed on the fast config; see PHASE0_SYNTHETIC_RESULTS.md):
    # an exact accounting identity that holds regardless of chain density.
    hyp["H-S2a_accounting_identity_POST_HOC"] = {
        "above_bound_injected": d["above_bound_injected"],
        "above_bound_injected_in_unalignable_expiries": d["above_bound_injected_in_unalignable_expiries"],
        "above_bound_detected_by_solver": d["above_bound_detected_by_solver"],
        "pass": (d["validation"]["conserved_every_day"] and d["defect_counts_match_exactly"]
                 and d["above_bound_detected_by_solver"]
                 == d["above_bound_injected"] - d["above_bound_injected_in_unalignable_expiries"]) if clean else None}
    hyp["H-S3_no_extrapolation"] ={"n_extrapolated": d["cell_status_totals"].get("extrapolated", 0),
                                    "pass": d["cell_status_totals"].get("extrapolated", 0) == 0}
    hyp["H-S6_analytic_persistence_mse"] = {"realized_mse_groupA": mse_a, "analytic_expected": expected, "kappa": kappa,
                                            "relative_deviation": rel_dev,
                                            "pass": (rel_dev is not None and abs(rel_dev) <= TOL["analytic_rel"]) if clean else None}
    sd_rel = analytic_rel_sd(rec_a, wcfg.sigma, None if wcfg.name == "RW" else wcfg.phi,
                             len({r["t"] for r in rec_a}))
    z = None if (sd_rel is None or rel_dev is None) else rel_dev / sd_rel
    # POST HOC (audit v2): deviation measured in analytic standard deviations; the v1 +-15% criterion is retained above.
    hyp["H-S6z_POST_HOC_analytic_sd"] = {"relative_deviation": rel_dev, "analytic_rel_sd": sd_rel, "z": z,
                                         "pass": (z is not None and abs(z) <= TOL["z_max"]) if clean else None}
    if wcfg.name == "RW":
        hyp["H-S4_persistence_appropriate"] = {
            "factor_ar1_detected_better": cmp_ar1["improvement_detected"],
            "oracle_equals_persistence_on_observed_max_abs_gap": oracle_gap,
            # pre-registered criterion applies to CLEAN mode; noise mode is exploratory (pass = None, components reported)
            "pass": ((not cmp_ar1["improvement_detected"]) and oracle_gap is not None
                     and oracle_gap <= TOL["oracle_equal_abs"]) if clean else None}
    else:
        lo, hi = TOL["ar1_ratio"]
        olo, ohi = TOL["oracle_ratio"]
        hyp["H-S5_predictability_detected"] = {
            "factor_ar1_detected_better": cmp_ar1["improvement_detected"], "factor_ar1_mse_ratio": cmp_ar1["mse_ratio"],
            "oracle_mse_ratio": cmp_orc["mse_ratio"], "analytic_oracle_ratio": (1.0 + wcfg.phi) / 2.0,
            "pass": bool(cmp_ar1["improvement_detected"] and lo <= cmp_ar1["mse_ratio"] <= hi
                         and olo <= cmp_orc["mse_ratio"] <= ohi) if clean else None}
    record = {
        "label": SYNTHETIC_BANNER, "origin": "synthetic",
        "config": {"world": asdict(wcfg), "pipeline": {"forward_mode": pcfg.forward_mode, "tol_k": scfg.tol_k,
                                                        "max_gap": scfg.max_gap, "k_nodes": list(scfg.k_nodes)},
                   "min_history": min_history, "bootstrap": {"block": block, "B": B, "seed": wcfg.seed + 1}},
        "environment": {"python": sys.version.split()[0], "platform": platform.platform(),
                        "implementation": platform.python_implementation()},
        "code_sha256": code_hashes(),
        "data_sha256": data_hash(world), "min_true_iv": world.min_true_iv,
        "pipeline_diagnostics": d, "results": res, "comparison_factor_ar1_vs_persistence": cmp_ar1,
        "comparison_oracle_ar_vs_persistence": cmp_orc, "hypotheses": hyp,
        "timing_seconds": {"generate": round(t1 - t0, 2), "pipeline": round(t2 - t1, 2), "evaluate": round(t3 - t2, 2)},
        "limitations": ["SYNTHETIC data only; says nothing about real markets or real data quality",
                        "strikes on a fixed moneyness grid; real chains have fixed price strikes",
                        "factor structure is simple and known to the forecaster", "constant known rate",
                        "no stale quotes, microstructure, per-contract timestamps, or AM/PM settlement mix"],
    }
    record["metrics_sha256"] = hashlib.sha256(json.dumps(_round({"res": res, "cmp": cmp_ar1, "cmp2": cmp_orc, "diag": d}),
                                                         sort_keys=True, default=str).encode()).hexdigest()
    if not quiet:
        print("[%s seed=%d days=%d] data %s.. metrics %s.." % (wcfg.name, wcfg.seed, wcfg.n_days,
                                                              record["data_sha256"][:12], record["metrics_sha256"][:12]))
    return record


def _summary_line(rec: dict) -> str:
    w = rec["config"]["world"]
    c = rec["comparison_factor_ar1_vs_persistence"]
    return ("%s seed=%d  n_origins=%d  AR1 detected=%s  mse_ratio=%.4f  CI=[%.3e, %.3e]  hyp=%s" % (
        w["name"], w["seed"], c["n_origins"], c["improvement_detected"], c["mse_ratio"], c["ci_lo"], c["ci_hi"],
        {k: v.get("pass") for k, v in rec["hypotheses"].items()}))


def main(argv=None):
    ap = argparse.ArgumentParser(description="SYNTHETIC Phase 0 feasibility experiment (not market data)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("single")
    s.add_argument("--world", choices=["RW", "AR"], required=True)
    s.add_argument("--seed", type=int, required=True)
    s.add_argument("--days", type=int, default=300)
    s.add_argument("--noise", action="store_true", help="tick-rounded quotes, node tolerance 5e-4 (exploratory)")
    s.add_argument("--fast", action="store_true", help="coarser chain (as unit tests)")
    s.add_argument("--tol-k", type=float, default=None,
                   help="node-matching tolerance (default 1e-9 clean / 5e-4 noise; 1e-6 reproduces v1 behaviour)")
    s.add_argument("--out", type=str, default=None)
    m = sub.add_parser("study")
    m.add_argument("--first-seed", type=int, default=20261100)
    m.add_argument("--n-seeds", type=int, default=10)
    m.add_argument("--days", type=int, default=300)
    m.add_argument("--tol-k", type=float, default=None, help="node-matching tolerance (1e-6 reproduces v1 behaviour)")
    m.add_argument("--out", type=str, default=None)
    a = ap.parse_args(argv)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if a.cmd == "single":
        base = fast_world_config(a.world, a.seed, a.days) if a.fast else WorldConfig(name=a.world, seed=a.seed, n_days=a.days)
        if a.noise:
            base = replace(base, tick=0.01)
            pcfg = PipelineConfig(surface=SurfaceConfig(tol_k=5e-4 if a.tol_k is None else a.tol_k))
        else:
            pcfg = PipelineConfig() if a.tol_k is None else PipelineConfig(surface=SurfaceConfig(tol_k=a.tol_k))
        rec = run_single(base, pcfg, quiet=False)
        path = Path(a.out) if a.out else OUT_DIR / ("single_%s_%d%s.json" % (a.world, a.seed, "_noise" if a.noise else ""))
        path.write_text(json.dumps(rec, indent=1, default=str))
        print(_summary_line(rec))
        print("wrote", path)
        return 0
    recs = []
    invalid = []  # worlds rejected by the generator's plausibility guard (PROTOCOL DEVIATION, disclosed in results)
    for i in range(a.n_seeds):
        for world in ("RW", "AR"):
            seed = a.first_seed + i
            try:
                rec = run_single(WorldConfig(name=world, seed=seed, n_days=a.days),
                                 None if a.tol_k is None else PipelineConfig(surface=SurfaceConfig(tol_k=a.tol_k)),
                                 quiet=True)
            except ValueError as exc:
                if "implausible IV" not in str(exc):
                    raise
                invalid.append({"world": world, "seed": seed, "status": "INVALID_WORLD", "error": str(exc)})
                print("%s seed=%d  INVALID_WORLD (generator guard: %s)" % (world, seed, exc), flush=True)
                continue
            recs.append(rec)
            print(_summary_line(rec), flush=True)
    rw = [r for r in recs if r["config"]["world"]["name"] == "RW"]
    ar = [r for r in recs if r["config"]["world"]["name"] == "AR"]
    fp = sum(1 for r in rw if r["comparison_factor_ar1_vs_persistence"]["improvement_detected"])
    det = sum(1 for r in ar if r["comparison_factor_ar1_vs_persistence"]["improvement_detected"])
    summary = {"label": SYNTHETIC_BANNER, "n_seeds": a.n_seeds, "first_seed": a.first_seed,
               "invalid_worlds": invalid, "n_valid_rw": len(rw), "n_valid_ar": len(ar),
               "rw_false_positives": fp, "rw_false_positive_rate": (fp / len(rw)) if rw else None,
               "ar_detections": det, "ar_detection_rate": (det / len(ar)) if ar else None,
               "pass_rw": fp <= TOL["rw_false_positive_max"], "pass_ar": det >= TOL["ar_detect_min"],
               "ar_mse_ratios": [r["comparison_factor_ar1_vs_persistence"]["mse_ratio"] for r in ar],
               "rw_mse_ratios": [r["comparison_factor_ar1_vs_persistence"]["mse_ratio"] for r in rw],
               "all_hypothesis_passes": {r["config"]["world"]["name"] + str(r["config"]["world"]["seed"]):
                                         {k: v.get("pass") for k, v in r["hypotheses"].items()} for r in recs}}
    path = Path(a.out) if a.out else OUT_DIR / ("study_%d_%d.json" % (a.first_seed, a.n_seeds))
    path.write_text(json.dumps({"summary": summary, "runs": recs}, indent=1, default=str))
    print("STUDY", json.dumps({k: v for k, v in summary.items() if k not in ("all_hypothesis_passes",)}, default=str))
    print("wrote", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
