"""A2d diagnostic (SYNTHETIC; DIAGNOSTIC ONLY: no method selection, no formal verdicts, no thresholds).
Frozen design: docs/research/PHASE0_A2D_DIAGNOSTIC_DESIGN.md.   Run (from scripts/phase0_synthetic/):
    python -m diagnostics.a2d --out-prefix ../../scratch/phase0_audit/A2d_seed40001_reps2000
Writes <prefix>_raw.csv and <prefix>_summary.json; refuses existing paths and anything under experiments/.
Lives outside phase0/ on purpose: phase0/*.py are hashed into the frozen A2b records and must stay unchanged."""
import argparse
import csv
import hashlib
import json
import math
import random
import statistics
import sys
import time
from pathlib import Path

from phase0 import SYNTHETIC_BANNER
from phase0.audit import _fresh_path, _series, hac_ci, protocol_sha256, wilson
from phase0.run import code_hashes
from phase0.synth import _normal

SCHEMA = "A2d-v1"
N = 240
Z = 1.959963984540054
LAGS = (4, 9, 19)  # Bartlett lags of the HAC estimator (same implementation as A2b: phase0.audit.hac_ci)
FROZEN = {"seed0": 40001, "reps": 2000}
SERIES_SEEDS = (40001, 42000)  # series seed of replication i = seed0 + i; random.Random(seed)
BOOT_SEEDS_RESERVED = (140001, 142000)  # reserved and UNUSED: A2d makes no bootstrap draws
TARGET_EXCESS_KURTOSIS = 12.0  # that of z^2 - 1 with z standard normal
# (name, (first seed, last seed)) of every stream used or reserved so far; A2d must be disjoint from all of them
USED_RANGES = (("A2 series", (7001, 8000)), ("A2 bootstrap", (107001, 108000)),
               ("A2b screening series (also plumbing runs)", (7001, 9000)), ("A2b screening bootstrap", (107001, 109000)),
               ("A2b confirmation series (reserved, unclaimed)", (20001, 25000)), ("A2b confirmation bootstrap (reserved)", (120001, 125000)),
               ("A3 world and bootstrap seeds", (20262000, 20262200)), ("v1 single runs", (20261012, 20261014)),
               ("v1 study seeds", (20261100, 20261110)), ("unit-test series seeds", (50001, 50003)))
Q_LEVELS = (0.025, 0.05, 0.5, 0.95, 0.975)


# ---------------------------------------------------------------- cases and exact moments
def solve_sinh_a(excess=TARGET_EXCESS_KURTOSIS) -> float:
    """a with kurtosis(sinh(a z)) = 3 + excess for z ~ N(0,1). With u = exp(2 a^2): kurt = (u^4 - 4u + 3) / (2 (u - 1)^2)."""
    target = 3.0 + excess
    lo, hi = 1.0 + 1e-9, 100.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if (mid ** 4 - 4 * mid + 3) / (2 * (mid - 1) ** 2) < target:
            lo = mid
        else:
            hi = mid
    return math.sqrt(math.log((lo + hi) / 2.0) / 2.0)


def sinh_rho_z(target_lag1: float, a: float) -> float:
    """Gaussian AR(1) coefficient rho_z giving corr(Y_t, Y_t+1) = target for Y = sinh(a z): corr = sinh(a^2 rho)/sinh(a^2)."""
    return math.asinh(target_lag1 * math.sinh(a * a)) / (a * a)


def _series_sinh(a: float, rho: float, n: int, rng: random.Random):
    z = _normal(rng)
    out = []
    for _ in range(n):
        out.append(math.sinh(a * z))
        z = rho * z + math.sqrt(1.0 - rho * rho) * _normal(rng)
    return out


def build_cases() -> list:
    a = solve_sinh_a()
    cs = [{"id": "G1", "kind": "normal", "rho_z": 0.0}, {"id": "G2", "kind": "normal", "rho_z": 0.3},
          {"id": "G3", "kind": "normal", "rho_z": -0.2}, {"id": "S1", "kind": "normal", "rho_z": 0.6},
          {"id": "G4", "kind": "skewed", "rho_z": 0.3}, {"id": "G5", "kind": "skewed", "rho_z": math.sqrt(0.3)},
          {"id": "C4", "kind": "sinh", "rho_z": sinh_rho_z(0.09, a), "a": a, "matches": "G4", "target_lag1": 0.09},
          {"id": "C5", "kind": "sinh", "rho_z": sinh_rho_z(0.30, a), "a": a, "matches": "G5", "target_lag1": 0.30}]
    for c in cs:
        c["n"] = N
        c["lag1"] = c["rho_z"] ** 2 if c["kind"] == "skewed" else (c["rho_z"] if c["kind"] == "normal" else c["target_lag1"])
        g = gamma_fn(c)
        c["gamma0"] = g(0)
        c["V_n"] = exact_mean_variance(g, N)  # exact variance of the sample mean at n = 240
        c["lr_variance"] = g(0) + 2.0 * sum(g(k) for k in range(1, 20000))
        c["captured_fraction"] = {str(L): (g(0) + 2.0 * sum((1 - j / (L + 1.0)) * g(j) for j in range(1, L + 1))) / c["lr_variance"] for L in LAGS}
    return cs


def gamma_fn(c):
    """Exact autocovariance gamma(k), k >= 0, of the case's stationary series."""
    r = c["rho_z"]
    if c["kind"] == "normal":
        return lambda k: r ** k
    if c["kind"] == "skewed":  # z^2 - 1: Var = 2, gamma_k = 2 rho^(2k)
        return lambda k: 2.0 * r ** (2 * k)
    a2 = c["a"] ** 2  # sinh(a z): gamma_k = exp(a^2) sinh(a^2 rho^k)
    return lambda k: math.exp(a2) * math.sinh(a2 * r ** k)


def exact_mean_variance(g, n: int) -> float:
    return (g(0) + 2.0 * sum((1.0 - k / n) * g(k) for k in range(1, n))) / n


def generate(c, rng):
    if c["kind"] == "sinh":
        return _series_sinh(c["a"], c["rho_z"], c["n"], rng)
    return _series(c["kind"], c["rho_z"], c["n"], rng)


# ---------------------------------------------------------------- frozen design identity
def design_spec() -> dict:
    cs = build_cases()
    return {"schema": SCHEMA, "n": N, "z": Z, "lags": LAGS, "frozen": FROZEN, "series_seeds": SERIES_SEEDS, "boot_reserved": BOOT_SEEDS_RESERVED,
            "used_ranges": USED_RANGES, "q_levels": Q_LEVELS, "target_excess_kurtosis": TARGET_EXCESS_KURTOSIS,
            "cases": [{k: (round(v, 12) if isinstance(v, float) else v) for k, v in c.items() if k in ("id", "kind", "rho_z", "a", "matches", "target_lag1")} for c in cs],
            "rules": {"P1": "oracle in G1,G2,G3,S1: |coverage-0.95|<=3SE and each tail within 3SE of 0.025",
                      "P2": "G1,G3: miss(L4)<miss(L9)<miss(L19); G1: |CV2/((4/3)(L+1)/n)-1|<=0.25 and |mean r-1|<=0.03 for each L",
                      "P3": "G2,S1: captured_fraction-0.08 <= mean r_L <= captured_fraction+0.02 for each L",
                      "P4a": "oracle in G4,G5: lower-tail rate > upper-tail rate and z_asym<=-2",
                      "P4b": "HAC L4,L9 in G4,G5: upper > lower and z_asym>=3",
                      "P4c": "C4,C5: |z_asym|<3 for oracle, HAC L4, HAC L9",
                      "P4d": "corr(mean, r_4) > 0.10 in G4,G5 and |corr|<0.10 in C4,C5,G1",
                      "P5": "CV2(r_4)[C4] / CV2(r_4)[G1] > 1.5",
                      "P6": "mirror identity: lower-tail(mirror)=upper-tail(original) exactly"}}


def design_sha256() -> str:
    return hashlib.sha256(json.dumps(design_spec(), sort_keys=True, default=str).encode()).hexdigest()


def _overlaps(a, b) -> bool:
    return a[0] <= b[1] and b[0] <= a[1]


def check_seeds(series=SERIES_SEEDS, boot=BOOT_SEEDS_RESERVED) -> list:
    """Raises if the A2d streams overlap any used or reserved stream; returns the list of checks (for the record)."""
    out = []
    for mine_name, mine in (("A2d series", series), ("A2d bootstrap (reserved, unused)", boot)):
        for name, r in USED_RANGES:
            ok = not _overlaps(mine, r)
            out.append({"a2d": mine_name, "range": list(mine), "other": name, "other_range": list(r), "disjoint": ok})
            if not ok:
                raise SystemExit("%s %s overlaps %s %s" % (mine_name, mine, name, r))
    if _overlaps(series, boot):
        raise SystemExit("A2d series and bootstrap ranges overlap")
    return out


# ---------------------------------------------------------------- statistics helpers
def _skew(x):
    m, s = statistics.mean(x), statistics.pstdev(x)
    return sum(((v - m) / s) ** 3 for v in x) / len(x) if s > 0 else None


def _corr(x, y):
    mx, my = statistics.mean(x), statistics.mean(y)
    sx, sy = math.sqrt(sum((a - mx) ** 2 for a in x)), math.sqrt(sum((b - my) ** 2 for b in y))
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy) if sx > 0 and sy > 0 else None


def _quantile(sx, p):
    n = len(sx)
    idx = lambda r: max(0, min(n - 1, r))
    k, w = n * p, 1.959963984540054 * math.sqrt(n * p * (1 - p))
    return {"q": sx[idx(math.ceil(k) - 1)], "ci95": [sx[idx(math.floor(k - w) - 1)], sx[idx(math.ceil(k + w) - 1)]]}  # distribution-free order-statistic CI


def _rates(t, n):
    lo, hi = sum(1 for v in t if v > Z), sum(1 for v in t if v < -Z)
    cov = n - lo - hi
    asym = (hi - lo) / math.sqrt(hi + lo) if hi + lo else 0.0
    return {"lower_tail_count": lo, "upper_tail_count": hi, "coverage_count": cov, "lower_tail": lo / n, "upper_tail": hi / n, "coverage": cov / n,
            "lower_wilson95": wilson(lo, n), "upper_wilson95": wilson(hi, n), "coverage_wilson95": wilson(cov, n),
            "z_asym_(hi-lo)/sqrt(hi+lo)": asym}


def analyze_case(c, rows, attempted) -> dict:
    """rows: list of (mean, half_L4, half_L9, half_L19) for the replications. A replication is invalid when a value is
    non-finite or a half-width is <= 0; invalid replications are excluded from every statistic and counted."""
    ok = [r for r in rows if all(math.isfinite(v) for v in r) and all(h > 0 for h in r[1:])]
    n = len(ok)
    sd_n = math.sqrt(c["V_n"])
    means = [r[0] for r in ok]
    halves = {L: [r[1 + i] for r in ok] for i, L in enumerate(LAGS)}
    t = {"hac%d" % L: [Z * m / h for m, h in zip(means, halves[L])] for L in LAGS}
    t["oracle"] = [m / sd_n for m in means]
    res = {"id": c["id"], "kind": c["kind"], "rho_z": c["rho_z"], "lag1": c["lag1"], "V_n_exact": c["V_n"], "lr_variance": c["lr_variance"],
           "captured_fraction": c["captured_fraction"], "replications": {"attempted": attempted, "completed": n, "invalid": attempted - n},
           "mean_of_sample_means": statistics.mean(means), "sd_of_sample_means": statistics.pstdev(means), "sd_n_exact": sd_n,
           "intervals": {}, "variance_estimator": {}, "counterfactual_rescaled_variance": {}, "paired_vs_oracle": {}}
    for name, tv in t.items():
        s = sorted(tv)
        res["intervals"][name] = dict(_rates(tv, n), t_mean=statistics.mean(tv), t_sd=statistics.stdev(tv), t_skew=_skew(tv),
                                      t_quantiles={str(p): _quantile(s, p) for p in Q_LEVELS})
    for L in LAGS:
        # r = V_hat / (n V_n): V_hat = n (half/Z)^2 estimates the series-scale long-run variance, n V_n is its exact finite-n counterpart.
        # (The executed v1 code divided by V_n alone, a scale error of n; see the post-run amendment in the design document.)
        r = [(h / Z) ** 2 / c["V_n"] for h in halves[L]]
        mr, vr = statistics.mean(r), statistics.pvariance(r)
        res["variance_estimator"][str(L)] = {"mean_ratio_Vhat_over_Vn": mr, "cv2": vr / mr ** 2, "nu_eff_2_over_cv2": 2.0 * mr ** 2 / vr if vr > 0 else None,
                                             "asymptotic_cv2_iid_(4/3)(L+1)/n": (4.0 / 3.0) * (L + 1) / N, "corr_mean_vs_ratio": _corr(means, r)}
        c_ = 1.0 / mr  # rescale V_hat so that its mean ratio is 1: isolates variability from bias (uses the oracle V_n; NOT a usable procedure)
        hp = [h * math.sqrt(c_) for h in halves[L]]
        lo, hi = sum(1 for m, h in zip(means, hp) if m - h > 0), sum(1 for m, h in zip(means, hp) if m + h < 0)
        res["counterfactual_rescaled_variance"][str(L)] = {"coverage": (n - lo - hi) / n, "lower_tail": lo / n, "upper_tail": hi / n}
        for side, test in (("lower", lambda v: v > Z), ("upper", lambda v: v < -Z)):
            hflag, oflag = [test(v) for v in t["hac%d" % L]], [test(v) for v in t["oracle"]]
            b, d = sum(1 for h, o in zip(hflag, oflag) if h and not o), sum(1 for h, o in zip(hflag, oflag) if o and not h)
            res["paired_vs_oracle"]["hac%d_%s" % (L, side)] = {"hac_only": b, "oracle_only": d, "z": (b - d) / math.sqrt(b + d) if b + d else 0.0}
    if c["kind"] == "skewed":  # exact identity under Y -> -Y (both procedures are equivariant); derived, not measured
        res["mirror_by_negation"] = {name: {"lower_tail": v["upper_tail"], "upper_tail": v["lower_tail"], "coverage": v["coverage"], "t_skew": -v["t_skew"]}
                                     for name, v in res["intervals"].items()}
    return res


def evaluate_signatures(cases) -> dict:
    """Pre-registered expectations (frozen before the run). Descriptive support flags only; they are not gate verdicts."""
    by = {x["id"]: x for x in cases}
    n_ok = by["G1"]["replications"]["completed"]
    se_cov, se_tail = math.sqrt(.95 * .05 / n_ok), math.sqrt(.025 * .975 / n_ok)
    iv = lambda cid, k: by[cid]["intervals"][k]
    ve = lambda cid, L: by[cid]["variance_estimator"][str(L)]
    out = {}
    p1 = {cid: abs(iv(cid, "oracle")["coverage"] - .95) <= 3 * se_cov and abs(iv(cid, "oracle")["lower_tail"] - .025) <= 3 * se_tail
          and abs(iv(cid, "oracle")["upper_tail"] - .025) <= 3 * se_tail for cid in ("G1", "G2", "G3", "S1")}
    out["P1_oracle_exact_in_normal_cases"] = {"per_case": p1, "met": all(p1.values())}
    miss = lambda cid, L: 1 - iv(cid, "hac%d" % L)["coverage"]
    p2 = {"ordering_G1": miss("G1", 4) < miss("G1", 9) < miss("G1", 19), "ordering_G3": miss("G3", 4) < miss("G3", 9) < miss("G3", 19),
          "cv2_within_25pct_G1": {str(L): abs(ve("G1", L)["cv2"] / ve("G1", L)["asymptotic_cv2_iid_(4/3)(L+1)/n"] - 1) <= .25 for L in LAGS},
          "mean_ratio_within_0.03_of_1_G1": {str(L): abs(ve("G1", L)["mean_ratio_Vhat_over_Vn"] - 1) <= .03 for L in LAGS}}
    out["P2_H1_estimator_variability"] = dict(p2, met=p2["ordering_G1"] and p2["ordering_G3"] and all(p2["cv2_within_25pct_G1"].values()) and all(p2["mean_ratio_within_0.03_of_1_G1"].values()))
    p3 = {cid: {str(L): by[cid]["captured_fraction"][str(L)] - .08 <= ve(cid, L)["mean_ratio_Vhat_over_Vn"] <= by[cid]["captured_fraction"][str(L)] + .02 for L in LAGS} for cid in ("G2", "S1")}
    out["P3_H3_truncation_bias"] = {"per_case": p3, "met": all(all(v.values()) for v in p3.values())}
    za = lambda cid, k: iv(cid, k)["z_asym_(hi-lo)/sqrt(hi+lo)"]
    p4a = {cid: iv(cid, "oracle")["lower_tail"] > iv(cid, "oracle")["upper_tail"] and za(cid, "oracle") <= -2 for cid in ("G4", "G5")}
    p4b = {"%s_hac%d" % (cid, L): iv(cid, "hac%d" % L)["upper_tail"] > iv(cid, "hac%d" % L)["lower_tail"] and za(cid, "hac%d" % L) >= 3 for cid in ("G4", "G5") for L in (4, 9)}
    p4c = {"%s_%s" % (cid, k): abs(za(cid, k)) < 3 for cid in ("C4", "C5") for k in ("oracle", "hac4", "hac9")}
    p4d = {cid: (ve(cid, 4)["corr_mean_vs_ratio"] > .10) if cid in ("G4", "G5") else abs(ve(cid, 4)["corr_mean_vs_ratio"]) < .10 for cid in ("G4", "G5", "C4", "C5", "G1")}
    out["P4_H2_skew_vs_kurtosis"] = {"P4a_oracle_opposite_sign": p4a, "P4b_hac_replicates_screening_asymmetry": p4b, "P4c_controls_symmetric": p4c,
                                     "P4d_corr_mean_vs_variance_estimate": p4d,
                                     "asymmetry_attributable_to_skewness_(b_and_c)": all(p4b.values()) and all(p4c.values()),
                                     "studentization_mechanism_supported_(a_and_d)": all(p4a.values()) and all(p4d.values())}
    ratio = ve("C4", 4)["cv2"] / ve("G1", 4)["cv2"]
    out["P5_kurtosis_inflates_estimator_variability"] = {"cv2_ratio_C4_over_G1": ratio, "met": ratio > 1.5}
    mirror_ok = all(x["mirror_by_negation"]["hac4"]["lower_tail"] == x["intervals"]["hac4"]["upper_tail"] for x in cases if "mirror_by_negation" in x)
    out["P6_mirror_identity"] = {"met": mirror_ok, "note": "an exact identity, not independent evidence"}
    return out


def _read_raw(path):
    by = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            by.setdefault(row["case"], []).append((float(row["mean"]), float(row["half_L4"]), float(row["half_L9"]), float(row["half_L19"])))
    return by


def analyze_raw(path, reps, cases=None) -> list:
    """Independent re-analysis from the raw CSV alone (used to check the summary)."""
    cases = cases or build_cases()
    raw = _read_raw(path)
    return [analyze_case(c, raw[c["id"]], reps) for c in cases]


def run_a2d(prefix, reps=FROZEN["reps"], seed0=FROZEN["seed0"]) -> dict:
    prefix = str(prefix)
    raw_path, sum_path = _fresh_path(prefix + "_raw.csv"), _fresh_path(prefix + "_summary.json")
    frozen = (reps, seed0) == (FROZEN["reps"], FROZEN["seed0"])
    mine = (seed0, seed0 + reps - 1)
    if not frozen:  # plumbing runs may not touch the A2d, A2b or reserved streams
        for name, r in USED_RANGES + (("A2d series", SERIES_SEEDS), ("A2d bootstrap (reserved)", BOOT_SEEDS_RESERVED)):
            if _overlaps(mine, r) or _overlaps((seed0 + 100_000, seed0 + 100_000 + reps - 1), r):
                raise SystemExit("seeds %s overlap %s %s" % (mine, name, r))
    seed_check = check_seeds()
    t0 = time.time()
    cases = build_cases()
    raw_rows, per_case = [], {}
    for c in cases:
        rows = []
        for i in range(reps):
            seed = seed0 + i
            y = generate(c, random.Random(seed))
            m = sum(y) / len(y)
            h = []
            for L in LAGS:
                _, lo, hi = hac_ci(y, L)
                h.append((hi - lo) / 2.0)
            rows.append((m, h[0], h[1], h[2]))
            raw_rows.append((c["id"], i, seed, repr(m), repr(h[0]), repr(h[1]), repr(h[2])))
        per_case[c["id"]] = rows
    with open(raw_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["case", "rep", "series_seed", "mean", "half_L4", "half_L9", "half_L19"])
        w.writerows(raw_rows)
    results = [analyze_case(c, per_case[c["id"]], reps) for c in cases]
    rec = {"label": SYNTHETIC_BANNER, "schema": SCHEMA,
           "analysis": ("" if frozen else "PLUMBING CHECK ONLY - NOT EVIDENCE: ") + "A2d DIAGNOSTIC ONLY: no method selected, no formal verdicts, no thresholds applied",
           "stage": "diagnostic" if frozen else "plumbing", "selection_performed": False, "formal_verdicts_issued": False,
           "design_sha256": design_sha256(), "a2b_protocol_sha256_reference": protocol_sha256(), "code_sha256_phase0": code_hashes(),
           "a2d_module_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "python": sys.version.split()[0],
           "config": {"n": N, "reps": reps, "seed0": seed0, "series_seeds": list(mine), "bootstrap_seeds_reserved_unused": [seed0 + 100_000, seed0 + 100_000 + reps - 1],
                      "seed_mapping": "replication i of every case: series seed = seed0 + i, series = random.Random(seed); no bootstrap draws are made",
                      "z": Z, "hac_lags": LAGS, "target_excess_kurtosis": TARGET_EXCESS_KURTOSIS, "sinh_a": cases[-1].get("a"),
                      "t_definitions": "hac_L: t = z*mean/half_L (V_hat = n*(half_L/z)^2, hac_ci unchanged); oracle: t = mean/sqrt(V_n exact); lower tail = t > z; upper tail = t < -z",
                      "cases": [{k: v for k, v in c.items()} for c in cases]},
           "seed_check": seed_check, "raw_file": {"path": str(raw_path), "sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(), "rows": len(raw_rows)},
           "cases": results, "signatures": evaluate_signatures(results),
           "limitations": ["synthetic AR(1)-type series only; no volatility clustering, non-stationarity or long memory; n = 240 only",
                           "the oracle interval uses the true variance of the simulated process: it is a diagnostic, not a valid real-world procedure",
                           "the sinh control matches the 4th moment and the lag-1 autocorrelation of the skewed case, not its higher moments",
                           "cases share series seeds, so cases are not independent; lags and oracle are paired within a case",
                           "no bootstrap method is run in A2d"],
           "seconds": round(time.time() - t0, 1)}
    sum_path.write_text(json.dumps(rec, indent=1, default=str))
    return rec


FROZEN_DESIGN_SHA256 = "b23ba43cd68356e978831c0c112cc902e57b323710bdfe9a07003461e0bc9f55"  # design as frozen and executed (v1)


def reanalyze(raw_path, original_summary_path, out_path, reps=FROZEN["reps"]) -> dict:
    """POST-RUN ANALYSIS CORRECTION. Re-analyses the UNCHANGED raw file of an executed run with the corrected variance-ratio definition.
    No data is regenerated and the original summary is not modified; the raw file must hash to the value recorded in it."""
    out_path = _fresh_path(out_path)
    original_summary_path, raw_path = Path(original_summary_path), Path(raw_path)
    orig = json.loads(original_summary_path.read_text())
    raw_sha = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    if raw_sha != orig["raw_file"]["sha256"]:
        raise SystemExit("raw file hash differs from the one recorded in the original summary; refusing to re-analyse")
    cases = analyze_raw(raw_path, reps)
    rec = {"label": SYNTHETIC_BANNER, "schema": SCHEMA + "-analysis-correction", "stage": "diagnostic",
           "analysis": "A2d POST-RUN ANALYSIS CORRECTION (raw data unchanged, no rerun): DIAGNOSTIC ONLY, no method selected, no formal verdicts, no thresholds",
           "selection_performed": False, "formal_verdicts_issued": False,
           "defect": "v1 code defined r_L = V_hat_L / V_n, but V_n is the variance of the sample MEAN while V_hat_L estimates the series-scale long-run "
                     "variance; the correct ratio is V_hat_L / (n V_n). Mean ratios were therefore too large by exactly n = 240.",
           "invalid_in_original_summary": ["variance_estimator.*.mean_ratio_Vhat_over_Vn", "counterfactual_rescaled_variance (all)",
                                           "signature P2 mean-ratio clause and its met flag", "signature P3 and its met flag"],
           "unaffected_in_original_summary": ["all tail, coverage and t-statistic quantities", "CV2, nu_eff, corr_mean_vs_ratio (scale-free)",
                                              "paired contrasts", "mirror quantities", "signatures P1, P4, P5, P6"],
           "rules_and_thresholds_changed": False,
           "original_summary_sha256": hashlib.sha256(original_summary_path.read_bytes()).hexdigest(),
           "raw_sha256": raw_sha, "design_sha256_as_frozen": FROZEN_DESIGN_SHA256, "original_a2d_module_sha256": orig["a2d_module_sha256"],
           "corrected_a2d_module_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "code_sha256_phase0": code_hashes(),
           "python": sys.version.split()[0], "cases": cases, "signatures_corrected": evaluate_signatures(cases),
           "signatures_as_originally_reported": orig["signatures"]}
    out_path.write_text(json.dumps(rec, indent=1, default=str))
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description="A2d diagnostic (SYNTHETIC, diagnostic only)")
    ap.add_argument("--out-prefix", required=True)
    ap.add_argument("--reps", type=int, default=FROZEN["reps"])
    ap.add_argument("--seed0", type=int, default=FROZEN["seed0"])
    ap.add_argument("--reanalyze", action="store_true", help="post-run correction: re-analyse <out-prefix>_raw.csv; writes <out-prefix>_corrected_analysis.json")
    a = ap.parse_args(argv)
    if a.reanalyze:
        rec = reanalyze(a.out_prefix + "_raw.csv", a.out_prefix + "_summary.json", a.out_prefix + "_corrected_analysis.json", a.reps)
        print(json.dumps({"schema": rec["schema"], "signatures_corrected": {k: v.get("met", v) for k, v in rec["signatures_corrected"].items()}}, indent=1, default=str))
        return 0
    rec = run_a2d(a.out_prefix, a.reps, a.seed0)
    print(json.dumps({"stage": rec["stage"], "analysis": rec["analysis"], "design_sha256": rec["design_sha256"],
                      "replications": {c["id"]: c["replications"] for c in rec["cases"]},
                      "signatures": {k: v.get("met", v) for k, v in rec["signatures"].items()}, "seconds": rec["seconds"]}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
