"""Deterministic chain -> validated quotes -> forward -> implied vols -> surface. REUSES phase0; adds only what was missing:
schema-level handling, expiry/strike normalisation (T = calendar days / 365, k = ln(K / F_hat)), explicit per-row terminal
dispositions, snapshot consistency, forward-vs-spot sanity and diagnostics. No IV is ever fabricated."""
import math
from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Dict, List

from phase0.iv import SolverConfig, implied_vol
from phase0.quotes import QualityPolicy, Reason, infer_forward, mid, select_otm, validate_day
from phase0.surface import SurfaceConfig, build_surface
from phase0.synth import Quote

from .diagnostics import check_surface
from .schema import ChainRead, ChainSnapshot

DAY_COUNT = "ACT/365 on calendar dates (no intraday or settlement-time adjustment)"


@dataclass(frozen=True)
class ChainRunConfig:
    rate: float = 0.02  # constant continuously compounded rate; the forward comes from put-call parity, not from this and a dividend
    policy: QualityPolicy = field(default_factory=QualityPolicy)
    solver: SolverConfig = field(default_factory=SolverConfig)
    surface: SurfaceConfig = field(default_factory=SurfaceConfig)
    max_forward_deviation: float = 0.25  # |F_hat / spot - 1| above this marks the expiry FORWARD_IMPLAUSIBLE


def config_dict(cfg: ChainRunConfig) -> dict:
    d = asdict(cfg)
    d["day_count"] = DAY_COUNT
    return d


@dataclass
class ChainResult:
    snapshots: List[dict]
    dispositions: Dict[int, str]  # input row number -> terminal code (every row has exactly one)
    file_ledger: dict


def build_snapshot(snap: ChainSnapshot, cfg: ChainRunConfig, disp: Dict[int, str]) -> dict:
    ts = snap.quote_ts
    quotes = list(snap.quotes)
    modal = sorted(Counter(q.underlying_price for q in quotes).items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    usable = []
    for q in quotes:
        if q.underlying_price != modal:
            disp[q.row] = "INCONSISTENT_UNDERLYING"
        else:
            usable.append(q)
    expiries = sorted({q.expiration for q in usable})
    mat = {e: i for i, e in enumerate(expiries)}
    T_of = {e: (e - ts.date()).days / 365.0 for e in expiries}
    pq = [Quote(q.row, 0, mat[q.expiration], T_of[q.expiration], q.strike, q.option_type == "call", q.bid, q.ask, q.origin) for q in usable]
    retained, rep = validate_day(pq, cfg.policy)
    for rid, reason in rep.dispositions.items():
        if reason is not Reason.RETAINED:
            disp[rid] = reason.value
    solver_counts: Counter = Counter()
    obs_by_mat, rows_info, observations, failures, exp_out = [], [], [], [], []
    for e in expiries:
        T, qs = T_of[e], [q for q in retained if q.mat_idx == mat[e]]
        F = infer_forward(qs, T, cfg.rate)
        info = {"expiration": e.isoformat(), "T": T, "n_retained": len(qs), "forward": F,
                "forward_over_spot": (F / modal) if F is not None else None, "status": "ALIGNED", "n_otm": 0, "n_forward_only": 0, "n_iv_converged": 0}
        obs = []
        if F is None or abs(F / modal - 1.0) > cfg.max_forward_deviation:
            info["status"] = "UNALIGNABLE_EXPIRY" if F is None else "FORWARD_IMPLAUSIBLE"
            for q in qs:
                disp[q.record_id] = info["status"]
            rows_info.append(None)
        else:
            otm = select_otm(qs, F)
            otm_ids = {q.record_id for q in otm}
            for q in qs:
                if q.record_id not in otm_ids:
                    disp[q.record_id] = "FORWARD_ONLY"
                    info["n_forward_only"] += 1
            info["n_otm"] = len(otm)
            for q in otm:
                res = implied_vol(mid(q), F, q.strike, T, cfg.rate, q.is_call, cfg.solver)
                solver_counts[res.status.value] += 1
                if res.iv is None:
                    disp[q.record_id] = "SOLVER_" + res.status.value
                    failures.append({"row": q.record_id, "expiration": e.isoformat(), "strike": q.strike, "option_type": "call" if q.is_call else "put",
                                     "status": res.status.value, "reason": res.reason})
                else:
                    disp[q.record_id] = "USED"
                    k = math.log(q.strike / F)
                    obs.append((k, res.iv))
                    observations.append({"row": q.record_id, "expiration": e.isoformat(), "strike": q.strike, "option_type": "call" if q.is_call else "put", "k": k, "iv": res.iv})
                    info["n_iv_converged"] += 1
            rows_info.append({"T": T, "F": F})
        obs_by_mat.append(obs)
        exp_out.append(info)
    surf = build_surface(0, obs_by_mat, cfg.surface)
    status = [[c.value for c in r] for r in surf.status]
    diag = check_surface(rows_info, surf.iv, status, cfg.surface.k_nodes, cfg.rate)
    term = Counter(disp[q.row] for q in quotes)
    return {"quote_timestamp": ts.isoformat(), "underlying_id": snap.underlying_id, "underlying_price": modal, "n_rows": len(quotes),
            "ledger": {"validation": {"ingested": rep.ingested, "retained": rep.retained, "excluded": rep.excluded, "by_reason": rep.counts,
                                      "conserved": rep.conserved},
                       "terminal_counts": dict(sorted(term.items()))},
            "expiries": exp_out, "observations": observations, "solver_status_counts": dict(sorted(solver_counts.items())),
            "solver_failures": failures,
            "surface": {"k_nodes": list(cfg.surface.k_nodes), "iv": surf.iv, "status": status, "n_obs": surf.n_obs,
                        "max_snap_dk": surf.max_snap_dk, "n_snapped": surf.n_snapped},
            "diagnostics": diag}


def run_chain(read: ChainRead, cfg: ChainRunConfig = ChainRunConfig()) -> ChainResult:
    disp: Dict[int, str] = {e.row: e.code for e in read.row_errors}
    snaps = [build_snapshot(s, cfg, disp) for s in read.snapshots]
    term = Counter(disp.values())
    ledger = {"rows": read.n_rows, "parse_errors": len(read.row_errors), "snapshots": len(snaps),
              "terminal_counts": dict(sorted(term.items())), "conserved": len(disp) == read.n_rows,
              "chronological_in_input": read.chronological_in_input}
    return ChainResult(snaps, disp, ledger)
