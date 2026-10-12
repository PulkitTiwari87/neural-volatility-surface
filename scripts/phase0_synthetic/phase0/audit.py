"""Phase 0 audit analyses (POST HOC / EXPLORATORY; declared in docs/research/PHASE0_AUDIT.md section 4).

SYNTHETIC SPIKE - not market data.
  python -m phase0.audit coverage          # A2: bootstrap CI coverage on series with known mean 0
  python -m phase0.audit study --first-seed 20262000 --n-seeds 200 --days 300   # A3: extended study
"""
import argparse
import json
import math
import random
import statistics
import sys
import time
from pathlib import Path

from . import SYNTHETIC_BANNER
from .evaluate import block_bootstrap_ci
from .run import OUT_DIR, run_single
from .synth import WorldConfig, _normal


def wilson(k: int, n: int, z: float = 1.959963984540054):
    """Wilson 95% interval for a binomial proportion."""
    if n == 0:
        return None, None
    p = k / n
    den = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, centre - half), min(1.0, centre + half)


def _series(case: str, rho: float, n: int, rng: random.Random):
    """Series with TRUE MEAN 0. 'normal': AR(1) unit-variance. 'skewed': z^2 - 1 with z unit-variance AR(1)."""
    z = _normal(rng)
    out = []
    for _ in range(n):
        out.append(z if case == "normal" else z * z - 1.0)
        z = rho * z + math.sqrt(1.0 - rho * rho) * _normal(rng)
    return out


def bootstrap_coverage(case: str, rho: float, n: int = 240, reps: int = 1000, B: int = 1000, block: int = 5,
                       seed0: int = 7001) -> dict:
    covered = rejects = 0
    for i in range(reps):
        d = _series(case, rho, n, random.Random(seed0 + i))
        _, lo, hi = block_bootstrap_ci(d, block, B, seed0 + 100_000 + i)
        covered += 1 if lo <= 0.0 <= hi else 0
        rejects += 1 if lo > 0.0 else 0
    se = math.sqrt(0.95 * 0.05 / reps)
    return {"case": case, "rho": rho, "n": n, "reps": reps, "B": B, "block": block, "coverage": covered / reps,
            "coverage_se": se, "lo_gt_0_rate": rejects / reps, "lo_gt_0_nominal": 0.025}


def run_coverage(out: Path) -> dict:
    t0 = time.time()
    res = [bootstrap_coverage("normal", 0.0), bootstrap_coverage("normal", 0.3), bootstrap_coverage("normal", 0.6),
           bootstrap_coverage("skewed", 0.3)]
    rec = {"label": SYNTHETIC_BANNER, "analysis": "A2 bootstrap coverage (POST HOC)", "results": res,
           "seconds": round(time.time() - t0, 1)}
    out.write_text(json.dumps(rec, indent=1))
    return rec


def _compact(rec: dict) -> dict:
    c = rec["comparison_factor_ar1_vs_persistence"]
    h = rec["hypotheses"]
    return {"world": rec["config"]["world"]["name"], "seed": rec["config"]["world"]["seed"],
            "detected": c["improvement_detected"], "ci_lo": c["ci_lo"], "ci_hi": c["ci_hi"], "mse_ratio": c["mse_ratio"],
            "mse_ratio_origin_mean": c["mse_ratio_origin_mean"], "lag1_autocorr_d": c["lag1_autocorr_d"],
            "H-S1": h["H-S1_recovery"]["pass"], "H-S1b": h["H-S1b_POST_HOC_bias_bound"]["pass"],
            "H-S1_max_err": h["H-S1_recovery"]["max_abs_observed_cell_error"],
            "H-S2": h["H-S2_conservation_and_defects"]["pass"], "H-S2a": h["H-S2a_accounting_identity_POST_HOC"]["pass"],
            "H-S6": h["H-S6_analytic_persistence_mse"]["pass"], "rel_dev": h["H-S6z_POST_HOC_analytic_sd"]["relative_deviation"],
            "analytic_rel_sd": h["H-S6z_POST_HOC_analytic_sd"]["analytic_rel_sd"], "z": h["H-S6z_POST_HOC_analytic_sd"]["z"],
            "H-S6z": h["H-S6z_POST_HOC_analytic_sd"]["pass"],
            "n_snapped_cells": h["H-S1b_POST_HOC_bias_bound"]["n_snapped_cells"]}


def run_study(first_seed: int, n_seeds: int, days: int, out: Path) -> dict:
    t0 = time.time()
    runs, invalid = [], []
    for i in range(n_seeds):
        for world in ("RW", "AR"):
            seed = first_seed + i
            try:
                runs.append(_compact(run_single(WorldConfig(name=world, seed=seed, n_days=days), quiet=True)))
            except ValueError as exc:
                if "implausible IV" not in str(exc):
                    raise
                invalid.append({"world": world, "seed": seed})
        if (i + 1) % 10 == 0:
            print("seeds done:", i + 1, "elapsed %.0fs" % (time.time() - t0), flush=True)
    summary = {"label": SYNTHETIC_BANNER, "analysis": "A3 extended study (EXPLORATORY, POST HOC)", "first_seed": first_seed,
               "n_seeds": n_seeds, "days": days, "invalid_worlds": invalid, "seconds": round(time.time() - t0, 1)}
    for world in ("RW", "AR"):
        rs = [r for r in runs if r["world"] == world]
        n_inv = sum(1 for x in invalid if x["world"] == world)
        det = sum(1 for r in rs if r["detected"])
        devs = [r["rel_dev"] for r in rs if r["rel_dev"] is not None]
        sds = [r["analytic_rel_sd"] for r in rs if r["analytic_rel_sd"] is not None]
        zs = [r["z"] for r in rs if r["z"] is not None]
        ac = [r["lag1_autocorr_d"] for r in rs if r["lag1_autocorr_d"] is not None]
        persist_sig_better = sum(1 for r in rs if r["ci_hi"] < 0.0)
        summary[world] = {
            "n_valid": len(rs), "n_invalid": n_inv, "n_invalid_wilson95": wilson(n_inv, n_seeds),
            "detections": det, "detection_rate": det / len(rs) if rs else None, "detection_wilson95": wilson(det, len(rs)),
            "worst_case_detections_invalid_as_detected": det + n_inv, "worst_case_rate": (det + n_inv) / (len(rs) + n_inv),
            "worst_case_wilson95": wilson(det + n_inv, len(rs) + n_inv),
            "persistence_significantly_better": persist_sig_better,
            "mse_ratio_mean": statistics.mean(r["mse_ratio"] for r in rs) if rs else None,
            "mse_ratio_sd": statistics.stdev(r["mse_ratio"] for r in rs) if len(rs) > 1 else None,
            "mse_ratio_min": min((r["mse_ratio"] for r in rs), default=None),
            "mse_ratio_max": max((r["mse_ratio"] for r in rs), default=None),
            "lag1_autocorr_d_mean": statistics.mean(ac) if ac else None,
            "H-S6_rel_dev_mean": statistics.mean(devs) if devs else None,
            "H-S6_rel_dev_sd_empirical": statistics.stdev(devs) if len(devs) > 1 else None,
            "analytic_rel_sd_mean": statistics.mean(sds) if sds else None,
            "frac_within_15pct": sum(1 for v in devs if abs(v) <= 0.15) / len(devs) if devs else None,
            "frac_z_within_2": sum(1 for v in zs if abs(v) <= 2.0) / len(zs) if zs else None,
            "frac_z_within_3": sum(1 for v in zs if abs(v) <= 3.0) / len(zs) if zs else None,
            "z_mean": statistics.mean(zs) if zs else None, "z_sd": statistics.stdev(zs) if len(zs) > 1 else None,
            "H-S1_pass": sum(1 for r in rs if r["H-S1"]), "H-S1b_pass": sum(1 for r in rs if r["H-S1b"]),
            "H-S2_pass": sum(1 for r in rs if r["H-S2"]), "H-S2a_pass": sum(1 for r in rs if r["H-S2a"]),
            "H-S6_pass": sum(1 for r in rs if r["H-S6"]), "H-S6z_pass": sum(1 for r in rs if r["H-S6z"]),
            "runs_with_snapped_cells": sum(1 for r in rs if r["n_snapped_cells"] > 0),
            "ratio_range_ok_ar_0.65_0.90": sum(1 for r in rs if 0.65 <= r["mse_ratio"] <= 0.90) if world == "AR" else None}
    out.write_text(json.dumps({"summary": summary, "runs": runs}, indent=1, default=str))
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser(description="SYNTHETIC Phase 0 audit analyses (post hoc / exploratory)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("coverage")
    s = sub.add_parser("study")
    s.add_argument("--first-seed", type=int, default=20262000)
    s.add_argument("--n-seeds", type=int, default=200)
    s.add_argument("--days", type=int, default=300)
    a = ap.parse_args(argv)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if a.cmd == "coverage":
        rec = run_coverage(OUT_DIR / "audit_A2_bootstrap_coverage.json")
        print(json.dumps(rec, indent=1))
    else:
        summ = run_study(a.first_seed, a.n_seeds, a.days, OUT_DIR / ("audit_A3_study_%d_%d.json" % (a.first_seed, a.n_seeds)))
        print(json.dumps(summ, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
