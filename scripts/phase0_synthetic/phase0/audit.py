"""Phase 0 audit analyses (POST HOC / EXPLORATORY; declared in docs/research/PHASE0_AUDIT.md section 4).

SYNTHETIC SPIKE - not market data.
  python -m phase0.audit coverage          # A2: bootstrap CI coverage on series with known mean 0
  python -m phase0.audit study --first-seed 20262000 --n-seeds 200 --days 300   # A3: extended study
"""
import argparse
import datetime
import hashlib
import json
import math
import random
import statistics
import sys
import time
from pathlib import Path

from . import SYNTHETIC_BANNER
from .evaluate import block_bootstrap_ci
from .run import OUT_DIR, code_hashes, run_single
from .synth import WorldConfig, _normal, generate_world


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


# ---------------------------------------------------------------------------------------------------------------
# A2b (decision.md PA-1) and A6 (decision.md PA-4). Both write ONLY to a fresh path outside experiments/.
# A2b measures interval-method behaviour for the MEAN of a stationary series whose true mean is exactly 0
# (the boundary null of the one-sided rule "lo > 0"). It is NOT a pipeline-level size: the pipeline's loss differences
# have no known exact-zero-mean world (see decision.md PA-1). The thresholds below are PROPOSED, not signed.
# ---------------------------------------------------------------------------------------------------------------
A2B_BLOCKS = {"M0_block5": 5, "M1_block10": 10, "M2_block20": 20}
A2B_HAC_LAGS = {"M3_hac_L4": 4, "M4_hac_L9": 9, "M5_hac_L19": 19}  # Bartlett lag L has the same truncation as block b = L + 1
A2B_METHODS = tuple(A2B_BLOCKS) + tuple(A2B_HAC_LAGS)
# (id, series case, rho of the underlying AR(1) z, n, gating). 'skewed' is z^2 - 1, whose own lag-1 autocorrelation is rho^2.
A2B_CASES = (("G1", "normal", 0.0, 240, True), ("G2", "normal", 0.3, 240, True), ("G3", "normal", -0.2, 240, True),
             ("G4", "skewed", 0.3, 240, True), ("G5", "skewed", math.sqrt(0.3), 240, True),
             ("S1", "normal", 0.6, 240, False), ("S2", "normal", 0.3, 120, False))
A2_STORED_COVERAGE = {("normal", 0.0, 240): 0.933, ("normal", 0.3, 240): 0.908, ("normal", 0.6, 240): 0.858,
                      ("skewed", 0.3, 240): 0.913}  # experiments/phase0_synthetic/audit_A2_bootstrap_coverage.json
# PROPOSED, unsigned (decision.md PA-1; frozen text for approval: docs/research/PHASE0_OWNER_DECISION_PACKAGE.md section 9).
# SCREENING TOLERANCES = Monte-Carlo bands (2 SE at 1000 replications): they keep simulation noise from rejecting a good method.
# They are NOT a certification. FORMAL CONFIRMATION criteria = one-sided 95% confidence bounds on the true rates (stage 2 only).
SCREEN_COVERAGE_MIN, SCREEN_SIZE_MAX = 0.936, 0.035
FORMAL_COVERAGE_LCB, FORMAL_SIZE_UCB = 0.935, 0.035
WIDTH_CAP, TIE, TIE_EPS = 1.5, 0.0035, 1e-12  # tie band = 1 SE of a 2.5% rate at 2000 replications (7 counts); EPS makes the comparison exact
MIN_REPS_SCREEN, MIN_REPS_FORMAL = 2000, 5000
PROTOCOL = {"screening": {"seed0": 7001, "reps": 2000, "B": 1000}, "confirmation": {"seed0": 20001, "reps": 5000, "B": 1000}}
BOOT_OFFSET = 100_000  # bootstrap seed of replication i = seed0 + BOOT_OFFSET + i; series seed = seed0 + i
RESERVED_SEEDS = (7001, 9000)  # series seeds of A2 (7001-8000) and of the screening run (7001-9000)
RESERVED_SEED_RANGES = (RESERVED_SEEDS, (RESERVED_SEEDS[0] + BOOT_OFFSET, RESERVED_SEEDS[1] + BOOT_OFFSET))  # series and bootstrap seeds
Z_ONE_SIDED_95 = 1.6448536269514722
SCHEMA = "A2b-v1"


def protocol_spec() -> dict:
    """Everything that defines the frozen A2b protocol; its SHA-256 is written into every record and quoted in the owner package."""
    return {"schema": SCHEMA, "methods": A2B_METHODS, "blocks": A2B_BLOCKS, "hac_lags": A2B_HAC_LAGS, "cases": A2B_CASES,
            "stored_a2_coverage": sorted(A2_STORED_COVERAGE.items()), "screen": [SCREEN_COVERAGE_MIN, SCREEN_SIZE_MAX],
            "formal": [FORMAL_COVERAGE_LCB, FORMAL_SIZE_UCB, Z_ONE_SIDED_95], "width_cap": WIDTH_CAP, "tie": TIE, "tie_eps": TIE_EPS,
            "protocol": PROTOCOL, "boot_offset": BOOT_OFFSET, "reserved": RESERVED_SEED_RANGES}


def protocol_sha256() -> str:
    return hashlib.sha256(json.dumps(protocol_spec(), sort_keys=True, default=str).encode()).hexdigest()


def _fresh_path(p) -> Path:
    p = Path(p).resolve()
    if p.exists():
        raise SystemExit("refusing to overwrite existing path: %s" % p)
    if OUT_DIR.parent.resolve() in p.parents:
        raise SystemExit("refusing to write under experiments/: %s" % p)
    return p


def hac_ci(d, L=None, z: float = 1.959963984540054):
    """Mean with a normal-theory Newey-West interval: Bartlett weights, lag L (default floor(4 (n/100)^(2/9))), divisor n.
    No small-sample correction (a sqrt((n-1)/n) factor would change the half-width by 0.2%, the t(n-1) quantile by 0.5%).
    Bartlett lag L truncates dependence exactly like a moving block of length L + 1. Returns (mean, lo, hi)."""
    n = len(d)
    m = sum(d) / n
    L = int(4.0 * (n / 100.0) ** (2.0 / 9.0)) if L is None else L
    c = [x - m for x in d]
    v = sum(x * x for x in c) / n
    for j in range(1, L + 1):
        v += 2.0 * (1.0 - j / (L + 1.0)) * sum(c[i] * c[i + j] for i in range(n - j)) / n
    half = z * math.sqrt(max(v, 0.0) / n)
    return m, m - half, m + half


def select_trace(stats) -> dict:
    """PROPOSED selection rule, fully specified (calibration first; no pipeline detection count enters). stats: {method:
    {"admissible": bool, "geo": geometric-mean half-width ratio over gating cases, "max_lo": worst gating-case lower-tail rate}}.
    1) admissible = screening-admissible methods; none -> selected None (keep M0 as a screening rule, no confirmation).
    2) candidates = admissible with geo <= WIDTH_CAP x the smallest admissible geo.
    3) best = smallest max_lo among candidates; tied = candidates with max_lo <= best + TIE (+TIE_EPS).
    4) selected = the tied method that comes first in A2B_METHODS order (lowest identifier).
    Narrowest-wins is deliberately NOT used: width correlates with liberal size, so it would pick the method closest to the gate."""
    adm = [m for m in A2B_METHODS if m in stats and stats[m]["admissible"]]
    if not adm:
        return {"admissible": [], "narrowest_geo": None, "width_cap_candidates": [], "best_max_lo": None, "tied": [], "selected": None}
    narrow = min(stats[m]["geo"] for m in adm)
    cand = [m for m in adm if stats[m]["geo"] <= WIDTH_CAP * narrow]
    best = min(stats[m]["max_lo"] for m in cand)
    tied = [m for m in cand if stats[m]["max_lo"] <= best + TIE + TIE_EPS]
    return {"admissible": adm, "narrowest_geo": narrow, "width_cap_candidates": cand, "best_max_lo": best, "tied": tied, "selected": tied[0]}


def select_method(stats):
    return select_trace(stats)["selected"]


def _overlaps(a, b) -> bool:
    return a[0] <= b[1] and b[0] <= a[1]


def _stage(reps, B, seed0, methods) -> str:
    s, c = PROTOCOL["screening"], PROTOCOL["confirmation"]
    if (seed0, reps, B) == (s["seed0"], s["reps"], s["B"]) and tuple(methods) == A2B_METHODS:
        return "screening"
    if (seed0, reps, B) == (c["seed0"], c["reps"], c["B"]) and len(methods) == 1:
        return "confirmation"
    return "plumbing" if reps < MIN_REPS_SCREEN else "exploratory"


def _claim_confirmation(screening_path, method, out) -> dict:
    """Stage 2 is tied to ONE screening record: it must be a protocol-conformant, non-void screening run of the same code that
    selected exactly this method, and its seeds are single-use (a lock file beside the screening record; honour-system guard)."""
    if not screening_path:
        raise SystemExit("confirmation needs --screening <the screening record that selected %s>" % method)
    sp = Path(screening_path).resolve()
    if not sp.is_file():
        raise SystemExit("confirmation needs --screening <screening record>: %s not found" % sp)
    if OUT_DIR.parent.resolve() in sp.parents:
        raise SystemExit("screening record must not be under experiments/")
    raw = sp.read_bytes()
    s = json.loads(raw.decode("utf-8"))
    problems = [name for name, ok in (
        ("schema", s.get("schema") == SCHEMA), ("stage == screening", s.get("stage") == "screening"),
        ("protocol_conformant", s.get("protocol_conformant") is True), ("not void", s.get("void_reason") is None),
        ("protocol_sha256 equal to this code's", s.get("protocol_sha256") == protocol_sha256()),
        ("code_sha256 equal to this code's", s.get("code_sha256") == code_hashes()),
        ("selected method equals --methods", s.get("selected_by_proposed_rule") == method)) if not ok]
    if problems:
        raise SystemExit("screening record rejected (%s); a replacement method cannot be chosen at confirmation" % ", ".join(problems))
    lock = sp.with_name(sp.name + ".confirmation_used")
    try:
        with open(lock, "x") as f:  # exclusive create: the confirmation seeds are used once
            json.dump({"claimed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "method": method, "out": str(out)}, f)
    except FileExistsError:
        raise SystemExit("confirmation seeds already claimed for this screening record (%s); remove the lock only with owner approval" % lock)
    return {"screening_file": str(sp), "screening_sha256": hashlib.sha256(raw).hexdigest(), "screening_selected": method, "lock_file": str(lock)}


def run_sensitivity(out, reps: int = 2000, B: int = 1000, seed0: int = 7001, methods=None, screening=None) -> dict:
    out = _fresh_path(out)
    methods = tuple(methods) if methods else A2B_METHODS
    unknown = [m for m in methods if m not in A2B_METHODS]
    if unknown:
        raise SystemExit("unknown method(s): %s" % unknown)
    if seed0 != PROTOCOL["screening"]["seed0"]:
        mine = [(seed0, seed0 + reps - 1), (seed0 + BOOT_OFFSET, seed0 + BOOT_OFFSET + reps - 1)]
        if any(_overlaps(a, r) for a in mine for r in RESERVED_SEED_RANGES):
            raise SystemExit("seeds %s overlap the A2/screening seeds %s; use a fresh seed0 (proposed: %d)"
                             % (mine, list(RESERVED_SEED_RANGES), PROTOCOL["confirmation"]["seed0"]))
    stage = _stage(reps, B, seed0, methods)
    if stage != "confirmation":  # the confirmation seeds are single-use and must not be peeked at by any other run
        c = PROTOCOL["confirmation"]
        conf = [(c["seed0"], c["seed0"] + c["reps"] - 1), (c["seed0"] + BOOT_OFFSET, c["seed0"] + BOOT_OFFSET + c["reps"] - 1)]
        mine = [(seed0, seed0 + reps - 1), (seed0 + BOOT_OFFSET, seed0 + BOOT_OFFSET + reps - 1)]
        if any(_overlaps(a, b) for a in mine for b in conf):
            raise SystemExit("seeds %s overlap the reserved single-use confirmation seeds %s" % (mine, conf))
    link = {}
    if stage == "confirmation":
        link = _claim_confirmation(screening, methods[0], out)
    elif screening:
        raise SystemExit("--screening is only valid for the confirmation stage")
    t0 = time.time()
    cases = []
    for cid, case, rho, n, gating in A2B_CASES:
        acc = {m: {"cov": 0, "lo": 0, "hi": 0, "half": 0.0, "sec": 0.0, "cov1000": 0} for m in methods}
        means = []
        done = 0
        for i in range(reps):
            d = _series(case, rho, n, random.Random(seed0 + i))  # same series and bootstrap seeds as A2
            means.append(sum(d) / n)
            for m in methods:
                t = time.time()
                if m in A2B_HAC_LAGS:
                    _, lo, hi = hac_ci(d, A2B_HAC_LAGS[m])
                else:
                    _, lo, hi = block_bootstrap_ci(d, A2B_BLOCKS[m], B, seed0 + BOOT_OFFSET + i)
                a = acc[m]
                a["sec"] += time.time() - t
                hit = 1 if lo <= 0.0 <= hi else 0
                a["cov"] += hit
                a["lo"] += 1 if lo > 0.0 else 0
                a["hi"] += 1 if hi < 0.0 else 0
                a["half"] += (hi - lo) / 2.0
                if i < 1000:
                    a["cov1000"] += hit
            done += 1
        sd_mean = statistics.pstdev(means)  # empirical SD of the sample mean: the target the interval half-width estimates
        ref = methods[0]
        res = {}
        for m in methods:
            a = acc[m]
            res[m] = {"coverage": a["cov"] / reps, "coverage_count": a["cov"], "lo_gt_0_rate": a["lo"] / reps,
                      "lo_gt_0_count": a["lo"], "hi_lt_0_rate": a["hi"] / reps, "mean_half_width": a["half"] / reps,
                      "half_width_over_sd_of_mean": a["half"] / reps / sd_mean,
                      "half_width_ratio_vs_first_method": a["half"] / acc[ref]["half"], "seconds": round(a["sec"], 2)}
        ref_cov = A2_STORED_COVERAGE.get((case, rho, n))
        check = (seed0 == 7001 and B == 1000 and reps >= 1000 and "M0_block5" in methods and ref_cov is not None)
        cases.append({"id": cid, "case": case, "rho_z": rho, "effective_lag1": (rho ** 2 if case == "skewed" else rho),
                      "n": n, "gating": gating, "reps": reps, "B": B,
                      "replications": {"attempted": reps, "completed": done, "invalid": reps - done},  # a failure aborts the run
                      "sd_of_sample_mean": sd_mean, "methods": res,
                      "m0_first1000_matches_stored_A2":
                          (round(acc["M0_block5"]["cov1000"] / 1000.0, 3) == ref_cov) if check else None})
    g = [c for c in cases if c["gating"]]
    stats, verdict, formal_detail = {}, {}, {}
    for m in methods:
        screen = all(c["methods"][m]["coverage"] >= SCREEN_COVERAGE_MIN and c["methods"][m]["lo_gt_0_rate"] <= SCREEN_SIZE_MAX
                     for c in g)
        detail = [{"id": c["id"], "size_ucb95_one_sided": wilson(c["methods"][m]["lo_gt_0_count"], reps, Z_ONE_SIDED_95)[1],
                   "coverage_lcb95_one_sided": wilson(c["methods"][m]["coverage_count"], reps, Z_ONE_SIDED_95)[0]} for c in g]
        for x in detail:
            x["size_ok"] = x["size_ucb95_one_sided"] <= FORMAL_SIZE_UCB
            x["coverage_ok"] = x["coverage_lcb95_one_sided"] >= FORMAL_COVERAGE_LCB
        formal_detail[m] = detail
        geo = math.exp(statistics.mean(math.log(c["methods"][m]["half_width_ratio_vs_first_method"]) for c in g))
        max_lo = max(c["methods"][m]["lo_gt_0_rate"] for c in g)
        # screening verdicts only in screening, formal verdicts only in confirmation: they must not be read across stages
        verdict[m] = {"screening_admissible": screen if stage != "confirmation" else None,
                      "formal_pass": all(x["size_ok"] and x["coverage_ok"] for x in detail) if stage == "confirmation" else None,
                      "geo_mean_half_width_ratio_gating": geo, "max_gating_lo_gt_0_rate": max_lo}
        stats[m] = {"admissible": screen, "geo": geo, "max_lo": max_lo}
    reg = [c["m0_first1000_matches_stored_A2"] for c in cases if c["m0_first1000_matches_stored_A2"] is not None]
    void = ("M0 first 1000 replications do not reproduce the stored A2 coverages"
            if stage == "screening" and not (reg and all(reg)) else None)
    trace = select_trace(stats) if (stage == "screening" and void is None) else None
    selected = trace["selected"] if trace else None
    outcome = None
    if stage == "screening":
        outcome = ("VOID" if void else ("SELECTED " + selected if selected else "NO_METHOD_ADMISSIBLE: keep M0 as a screening rule; no confirmation"))
    if stage == "confirmation":
        ok = verdict[methods[0]]["formal_pass"]
        outcome = {"method": methods[0], "formal_pass": ok, "per_case": formal_detail[methods[0]],
                   "replacement_selection": "not performed: choosing another method on confirmation seeds is forbidden"}
    label = {"plumbing": "PLUMBING CHECK ONLY - NOT EVIDENCE (reps < %d): " % MIN_REPS_SCREEN,
             "exploratory": "EXPLORATORY - NOT THE FROZEN PROTOCOL, NO SELECTION OR FORMAL VERDICT: ",
             "screening": "STAGE 1 SCREENING (tolerance bands, not certification): ",
             "confirmation": "STAGE 2 CONFIRMATION (formal one-sided 95% bounds, single method, fresh seeds): "}[stage]
    rec = {"label": SYNTHETIC_BANNER, "schema": SCHEMA, "protocol_sha256": protocol_sha256(), "stage": stage,
           "protocol_conformant": stage in ("screening", "confirmation"),
           "analysis": label + "A2b interval-method sensitivity (POST HOC; protocol PROPOSED in decision.md PA-1, NOT signed)",
           "plumbing_check_only": stage == "plumbing", "screening_valid": stage == "screening" and void is None,
           "formal_valid": stage == "confirmation", "void_reason": void,
           "config": {"reps": reps, "B": B, "seed0": seed0, "methods": methods, "cases": A2B_CASES,
                      "series_seeds": [seed0, seed0 + reps - 1], "bootstrap_seeds": [seed0 + BOOT_OFFSET, seed0 + BOOT_OFFSET + reps - 1],
                      "screen": [SCREEN_COVERAGE_MIN, SCREEN_SIZE_MAX], "formal_one_sided_95": [FORMAL_COVERAGE_LCB, FORMAL_SIZE_UCB],
                      "threshold_semantics": {"screen": "Monte-Carlo tolerance bands for screening; NOT a certification",
                                              "formal": "one-sided 95% confidence bounds; the only certification criterion; stage 2 only"},
                      "width_cap": WIDTH_CAP, "tie": TIE, "tie_eps": TIE_EPS},
           "null": "series with exactly zero true mean (stationary start); NOT a pipeline-level size",
           "m0_first1000_regression_vs_stored_A2": (all(reg) if reg else None), "verdict": verdict,
           "selected_by_proposed_rule": selected, "selection_trace": trace, "outcome": outcome, "confirmation_link": link or None,
           "cases": cases, "code_sha256": code_hashes(), "python": sys.version.split()[0], "seconds": round(time.time() - t0, 1)}
    out.write_text(json.dumps(rec, indent=1, default=str))
    return rec


def stopped_world_days(name: str, seed: int, n_max: int = 300) -> int:
    """STOPPING RULE (A6): the largest n_days for which generate_world succeeds. Because day t of a world depends only on
    days <= t (prefix property, checked by check_prefix), validity is monotone in n and equals the index of the first day
    on which the plausibility guard fires. Returns n_max if the full world is valid."""
    def valid(n):
        try:
            generate_world(WorldConfig(name=name, seed=seed, n_days=n))
            return True
        except ValueError as exc:
            if "implausible IV" not in str(exc):
                raise
            return False
    if valid(n_max):
        return n_max
    lo, hi = 0, n_max  # lo: valid (vacuous at 0), hi: invalid
    while hi - lo > 1:
        mid = (lo + hi) // 2
        lo, hi = (mid, hi) if valid(mid) else (lo, mid)
    return lo


def check_prefix(name: str, seed: int, n_stop: int, n_max: int = 300) -> dict:
    """The truncated world must equal the first n_stop days of the full-length world. The full world cannot be generated
    (guard), so the guard is bypassed by clamping true IV to 0.02 + 1e-9 (affects only nodes that breach, i.e. day >= n_stop;
    any earlier effect would show up as a mismatch below)."""
    from unittest import mock
    from . import synth
    real = synth.true_iv
    with mock.patch.object(synth, "true_iv", lambda x, k, T: max(real(x, k, T), 0.02 + 1e-9)):
        full = generate_world(WorldConfig(name=name, seed=seed, n_days=n_max))
    part = generate_world(WorldConfig(name=name, seed=seed, n_days=n_stop))
    return {"factors_equal": full.factors[:n_stop] == part.factors, "spots_equal": full.spots[:n_stop] == part.spots,
            "days_equal": full.days[:n_stop] == part.days,
            "n_quotes": sum(len(dd.quotes) for dd in part.days)}


def run_stopped(seeds, out_dir, world: str = "RW") -> dict:
    """A6: run the unchanged pipeline on each world stopped at its first implausible-IV day. Results are NOT combined
    with the full-world false-positive rate."""
    out_dir = _fresh_path(out_dir)
    out_dir.mkdir(parents=True)
    t0 = time.time()
    rows = []
    for s in seeds:
        row = {"world": world, "seed": s, "attempted": True}
        try:
            n_stop = stopped_world_days(world, s)
            row["n_days_stopped"] = n_stop
            row["full_world_was_invalid"] = n_stop < 300
            row["prefix_check"] = check_prefix(world, s, n_stop)
            rec = run_single(WorldConfig(name=world, seed=s, n_days=n_stop), quiet=True)
            (out_dir / ("%s_%d_d%d.json" % (world, s, n_stop))).write_text(json.dumps(rec, indent=1, default=str))
            c = rec["comparison_factor_ar1_vs_persistence"]
            row.update(completed=True, detected=c["improvement_detected"], ci_lo=c["ci_lo"], ci_hi=c["ci_hi"], mean_d=c["mean_d"],
                       n_origins=c["n_origins"], mse_ratio=c["mse_ratio"], persistence_significantly_better=c["ci_hi"] < 0.0)
        except Exception as exc:  # recorded in the ledger, never hidden
            row.update(completed=False, error="%s: %s" % (type(exc).__name__, exc))
        rows.append(row)
        print(json.dumps(row, default=str), flush=True)
    done = [r for r in rows if r["completed"]]
    x = sum(1 for r in done if r["detected"])
    summary = {"label": SYNTHETIC_BANNER, "analysis": "A6 stopped-world analysis (EXPLORATORY, POST HOC; protocol PROPOSED in decision.md PA-4)",
               "stopping_rule": "n_days = first day on which the plausibility guard (true IV <= 0.02 at a sampled node) fires; days 0..n_days-1 are the unchanged world",
               "attempted": len(rows), "completed": len(done), "failed": len(rows) - len(done),
               "detections": x, "detection_wilson95": wilson(x, len(done)),
               "prefix_checks_all_equal": all(all(v for k, v in r["prefix_check"].items() if k.endswith("_equal")) for r in done),
               "note": "different estimand from the full-world rate; do not pool with it", "runs": rows,
               "code_sha256": code_hashes(), "python": sys.version.split()[0], "seconds": round(time.time() - t0, 1)}
    (out_dir / "A6_ledger.json").write_text(json.dumps(summary, indent=1, default=str))
    return summary


LEDGER_F_GRID = (0.0, 0.05, 0.10, 0.20, 0.50, 1.0)


def invalid_world_ledger(n_attempted: int, n_valid: int, detections: int, invalid_worlds=()) -> dict:
    """PA-4 reporting rules R1-R5 for ONE world type (PROPOSED, unsigned). Pure arithmetic on recorded counts; it never
    pools stopped-world (A6) results (R6) and it is a reporting format, not evidence that any interval method is valid."""
    n_inv = n_attempted - n_valid
    if n_inv < 0 or n_valid < 0 or detections < 0 or detections > n_valid:
        raise ValueError("inconsistent counts")
    invalid_worlds = list(invalid_worlds)
    if invalid_worlds and len(invalid_worlds) != n_inv:
        raise ValueError("invalid_worlds list does not match n_attempted - n_valid")
    x, n = detections, n_attempted
    lo_b, hi_b = x / n, (x + n_inv) / n  # R4: unknown invalid-world outcomes -> bounds, not an estimate
    w_lo, w_hi = wilson(x, n), wilson(x + n_inv, n)

    def f_star(alpha):  # invalid-world detection rate at which the unconditional rate equals alpha (None if no invalid worlds)
        return None if n_inv == 0 else (alpha * n - x) / n_inv

    return {
        "R1": {"attempted": n, "valid": n_valid, "invalid": n_inv, "invalid_rate": n_inv / n, "invalid_wilson95": wilson(n_inv, n)},
        "R2": {"reason_counts": {"IMPLAUSIBLE_IV": n_inv},  # the only exception the study loop catches; others are re-raised
               "invalid_worlds": invalid_worlds,
               "note": "per-world breach day/node are not stored in the study record; see decision.md PA-4 (D1) and A6 stop days"},
        "R3": {"label": "conditional on world validity", "detections": x, "n_valid": n_valid,
               "rate": (x / n_valid) if n_valid else None, "wilson95": wilson(x, n_valid)},
        "R4": {"unconditional_rate_bounds": [lo_b, hi_b], "wilson95_union": [min(w_lo[0], w_hi[0]), max(w_lo[1], w_hi[1])],
               "note": "identification bounds when invalid-world outcomes are unknown; the upper end is a bound, not an estimate"},
        "R5": {"break_even_invalid_world_detection_rate": {"for_2.5pct": f_star(0.025), "for_5pct": f_star(0.05)},
               "unconditional_rate_by_invalid_world_detection_rate": {str(f): (x + f * n_inv) / n for f in LEDGER_F_GRID}},
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="SYNTHETIC Phase 0 audit analyses (post hoc / exploratory)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("coverage")
    s = sub.add_parser("study")
    s.add_argument("--first-seed", type=int, default=20262000)
    s.add_argument("--n-seeds", type=int, default=200)
    s.add_argument("--days", type=int, default=300)
    q = sub.add_parser("sensitivity", help="A2b (PROPOSED): needs --out, a path that does not exist, outside experiments/")
    q.add_argument("--out", required=True)
    q.add_argument("--reps", type=int, default=MIN_REPS_SCREEN)
    q.add_argument("--B", type=int, default=1000)
    q.add_argument("--seed0", type=int, default=7001, help="7001 = screening seeds (paired with A2); a fresh value for confirmation")
    q.add_argument("--methods", default="", help="comma-separated subset of: " + ",".join(A2B_METHODS))
    q.add_argument("--screening", default="", help="confirmation only: the screening record that selected --methods (single use)")
    g = sub.add_parser("ledger", help="PA-4 R1-R5 from a stored study record; read-only, writes nothing")
    g.add_argument("--a3", default=str(OUT_DIR / "audit_A3_study_20262000_200.json"))
    g.add_argument("--a6", default="", help="optional A6 ledger; shown on a separate line, never pooled")
    t = sub.add_parser("stopped", help="A6: needs --out, a directory that does not exist, outside experiments/")
    t.add_argument("--out", required=True)
    t.add_argument("--a3", default=str(OUT_DIR / "audit_A3_study_20262000_200.json"), help="read-only; lists the invalid worlds")
    a = ap.parse_args(argv)
    if a.cmd == "sensitivity":
        rec = run_sensitivity(a.out, a.reps, a.B, a.seed0, [m for m in a.methods.split(",") if m], a.screening or None)
        print(json.dumps({"analysis": rec["analysis"], "stage": rec["stage"], "protocol_sha256": rec["protocol_sha256"],
                          "outcome": rec["outcome"], "void_reason": rec["void_reason"],
                          "selected_by_proposed_rule": rec["selected_by_proposed_rule"],
                          "m0_first1000_regression_vs_stored_A2": rec["m0_first1000_regression_vs_stored_A2"]}, indent=1, default=str))
        return 0
    if a.cmd == "ledger":
        s = json.loads(Path(a.a3).read_text())["summary"]
        out = {"source": a.a3, "estimands": "R3 is conditional on validity; R4 bounds the unconditional rate; R6 is a different estimand",
               "RW": invalid_world_ledger(s["n_seeds"], s["RW"]["n_valid"], s["RW"]["detections"], [x for x in s["invalid_worlds"] if x["world"] == "RW"]),
               "AR": invalid_world_ledger(s["n_seeds"], s["AR"]["n_valid"], s["AR"]["detections"], [x for x in s["invalid_worlds"] if x["world"] == "AR"])}
        if a.a6:
            l6 = json.loads(Path(a.a6).read_text())
            out["R6_stopped_worlds_A6"] = {k: l6[k] for k in ("attempted", "completed", "failed", "detections", "detection_wilson95", "stopping_rule", "note")}
        print(json.dumps(out, indent=1))
        return 0
    if a.cmd == "stopped":
        inv = json.loads(Path(a.a3).read_text())["summary"]["invalid_worlds"]
        summ = run_stopped([x["seed"] for x in inv if x["world"] == "RW"], a.out)
        print(json.dumps({k: v for k, v in summ.items() if k != "runs"}, indent=1, default=str))
        return 0
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
