"""Chronological split, leakage audit and baseline forecasts on surface artifacts. NO neural model (GPU-only policy).

Task: from the snapshot at origin t, predict the implied vol of the same (expiry date, k node) cell at the next snapshot t+1,
for cells OBSERVED at t+1. Baselines: persistence (origin cell value) and expanding historical mean (observed cells up to t).
Targets, not origins, define the split. Cells skipped for any reason are counted by reason (the selection effect is visible)."""
import math
from typing import Dict, List, Sequence

from phase0.evaluate import maturity_bucket, moneyness_bucket
from phase0.forecast import HistoryView

from .artifact import code_hashes, content_sha256

EVAL_SCHEMA = "chainpipe-eval-1"


class ChronologyError(Exception):
    pass


def assert_chronology(snaps: Sequence[dict]) -> None:
    last: Dict[str, str] = {}
    for i, s in enumerate(snaps):
        u, ts = s["underlying_id"], s["quote_timestamp"]
        if u in last and ts <= last[u]:
            raise ChronologyError("snapshot %d (%s %s) is not strictly later than the previous snapshot of the same underlying" % (i, u, ts))
        last[u] = ts
    if len({s["underlying_id"] for s in snaps}) > 1:
        raise ChronologyError("evaluation expects one underlying per artifact")


def chronological_split(n_targets: int, train: float = 0.6, valid: float = 0.2) -> Dict[str, List[int]]:
    """Contiguous, ordered target-index blocks; every block must be non-empty. Never shuffles."""
    a, b = int(n_targets * train), int(n_targets * (train + valid))
    out = {"train": list(range(0, a)), "valid": list(range(a, b)), "test": list(range(b, n_targets))}
    if not all(out.values()):
        raise ValueError("%d targets are too few for the requested fractions (every split needs at least one)" % n_targets)
    return out


class AuditedHistory(HistoryView):
    """HistoryView that records the largest snapshot index actually read (leakage audit)."""

    def __init__(self, snaps, upto):
        super().__init__(snaps, upto)
        self.max_index = -1

    def __getitem__(self, i):
        v = super().__getitem__(i)
        self.max_index = max(self.max_index, i if i >= 0 else self.upto + 1 + i)
        return v


def _surface_cells(snap: dict) -> dict:
    out = {}
    for ri, e in enumerate(snap["expiries"]):
        for j, k in enumerate(snap["surface"]["k_nodes"]):
            out[(e["expiration"], j)] = (snap["surface"]["iv"][ri][j], snap["surface"]["status"][ri][j], e["T"], k)
    return out


def _contract_cells(snap: dict) -> dict:
    """Actual quote IVs keyed by contract (expiry date, strike, option type); always 'observed'."""
    T = {e["expiration"]: e["T"] for e in snap["expiries"]}
    return {(o["expiration"], o["strike"], o["option_type"]): (o["iv"], "observed", T[o["expiration"]], o["k"]) for o in snap["observations"]}


def _stats(errs: List[float]) -> dict:
    n = len(errs)
    if n == 0:
        return {"n": 0, "mae": None, "rmse": None, "bias_pred_minus_actual": None, "mae_volpts": None, "rmse_volpts": None}
    mae, rmse, bias = sum(abs(e) for e in errs) / n, math.sqrt(sum(e * e for e in errs) / n), sum(errs) / n
    return {"n": n, "mae": mae, "rmse": rmse, "bias_pred_minus_actual": bias, "mae_volpts": 100 * mae, "rmse_volpts": 100 * rmse}


BASELINES = ("persistence", "historical_mean")


def _task(snaps, split, which, cells_fn, target_ok, origin_ok) -> dict:
    """One forecasting task on one cell definition. Leakage is audited per origin (AuditedHistory)."""
    n_t = len(snaps) - 1
    errs = {b: {s: [] for s in split} for b in BASELINES}
    by_status = {b: {s: {} for s in split} for b in BASELINES}
    buckets = {b: {s: {} for s in split} for b in BASELINES}
    skipped = {b: {} for b in BASELINES}
    leak = {"origin_before_target": True, "max_history_index_le_origin": True, "pairs": 0}
    skip = lambda b, r: skipped[b].__setitem__(r, skipped[b].get(r, 0) + 1)

    def add(b, s, err, status, bk):
        errs[b][s].append(err)
        by_status[b][s].setdefault(status, []).append(err)
        buckets[b][s].setdefault(bk, []).append(err)

    for t in range(n_t):
        origin, target = t, t + 1
        hist = AuditedHistory(snaps, origin)
        o_cells, t_cells = cells_fn(hist[origin]), cells_fn(snaps[target])
        leak["pairs"] += 1
        leak["origin_before_target"] &= origin < target
        past_cells = [cells_fn(hist[j]) for j in range(origin + 1)]
        for key, (tv, tst, tT, k) in t_cells.items():
            if tv is None or tst not in target_ok:
                for b in BASELINES:
                    skip(b, "target_cell_missing_or_status_excluded")
                continue
            bk = (moneyness_bucket(k), maturity_bucket(tT))
            ov = o_cells.get(key)
            if ov is None:
                skip("persistence", "cell_not_in_origin")
            elif ov[0] is None or ov[1] not in origin_ok:
                skip("persistence", "origin_cell_missing_or_status_excluded")
            else:
                add("persistence", which[t], ov[0] - tv, tst, bk)
            past = [c[key][0] for c in past_cells if key in c and c[key][1] == "observed" and c[key][0] is not None]
            if not past:
                skip("historical_mean", "no_observed_history_for_cell")
            else:
                add("historical_mean", which[t], sum(past) / len(past) - tv, tst, bk)
        leak["max_history_index_le_origin"] &= hist.max_index <= origin
    return {"leakage": leak,
            "baselines": {b: {"metrics": {s: _stats(errs[b][s]) for s in split},
                              "by_target_status": {s: {st: _stats(v) for st, v in sorted(by_status[b][s].items())} for s in split},
                              "by_moneyness_x_maturity": {s: {"%s|%s" % bk: _stats(v) for bk, v in sorted(buckets[b][s].items())} for s in split},
                              "skipped_cells": dict(sorted(skipped[b].items()))} for b in BASELINES}}


def evaluate_baselines(art: dict, train: float = 0.6, valid: float = 0.2, surface_target_ok=("observed", "interpolated"),
                       origin_ok=("observed", "interpolated")) -> dict:
    snaps = art["snapshots"]
    assert_chronology(snaps)
    n_t = len(snaps) - 1
    if n_t < 3:
        raise ValueError("need at least 4 snapshots (3 targets)")
    split = chronological_split(n_t, train, valid)
    which = {t: s for s, idx in split.items() for t in idx}
    tasks = {"contract_level": _task(snaps, split, which, _contract_cells, ("observed",), ("observed",)),
             "surface_cell_level": _task(snaps, split, which, _surface_cells, tuple(surface_target_ok), tuple(origin_ok))}
    tsl = lambda idx: [snaps[i + 1]["quote_timestamp"] for i in idx]
    ordered = max(tsl(split["train"])) < min(tsl(split["valid"])) and max(tsl(split["valid"])) < min(tsl(split["test"]))
    leak = {"splits_ordered": ordered, "per_task": {k: v["leakage"] for k, v in tasks.items()}}
    leak["all_passed"] = ordered and all(v["leakage"]["origin_before_target"] and v["leakage"]["max_history_index_le_origin"] for v in tasks.values())
    rec = {"schema": EVAL_SCHEMA, "label": art["label"], "artifact_version_id": art["version_id"], "artifact_content_sha256": art["content_sha256"],
           "config": {"train": train, "valid": valid, "surface_target_status_ok": list(surface_target_ok), "origin_status_ok": list(origin_ok),
                      "task": "IV at the next snapshot of the same contract (contract_level) or the same (expiry, k node) cell (surface_cell_level)",
                      "note": "interpolated surface targets include interpolation error (see by_target_status); skipped cells are counted by reason"},
           "splits": {s: {"n_targets": len(i), "first_target": tsl(i)[0], "last_target": tsl(i)[-1]} for s, i in split.items()},
           "leakage_audit": leak, "tasks": {k: v["baselines"] for k, v in tasks.items()}, "code_sha256": code_hashes()}
    rec["content_sha256"] = content_sha256(rec)
    return rec
