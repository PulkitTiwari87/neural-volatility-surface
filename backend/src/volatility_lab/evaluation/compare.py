"""E-1 (nearest-expiry) versus E-2 (same-expiry) target comparison on identical (origin, cell) samples.

Both ``Prepared`` objects are built from the SAME surface panel, so they share origins, targets rows and the
walk-forward folds. Only the label of a cell differs:

* E-1: the value of whichever real expiry is nearest the tenor on the target date.
* E-2: the value of the expiry that anchored the cell on the ORIGIN date, tracked to the target date.

Everything here is descriptive: counts, errors, and shares. No test statistic is computed.
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

from volatility_lab.evaluation import metrics as M
from volatility_lab.evaluation.walkforward import Fold
from volatility_lab.features.panel import Prepared, target_arrays


def common_mask(p1: Prepared, p2: Prepared, positions) -> np.ndarray:
    """Cells that are evaluable under BOTH targets (primary = tight / observed on both)."""
    return M.eval_mask(p1, positions, "primary") & M.eval_mask(p2, positions, "primary")


def coverage_by_fold(p1: Prepared, p2: Prepared, folds: List[Fold]) -> pd.DataFrame:
    """Eligible-sample counts per test year under each target, their overlap, and E-2 censoring."""
    ty2, tst2 = target_arrays(p2)
    rows = []
    for f in folds:
        pos = f.test
        m1, m2 = M.eval_mask(p1, pos, "primary"), M.eval_mask(p2, pos, "primary")
        both = m1 & m2
        anchored = p2.status[p2.origins[pos]] >= 2          # origin cell anchored on one real expiry
        censored = anchored & (tst2[pos] == 0)               # ... but its expiry has no usable slice at the target
        sw = p1.anchor_changed[pos] if p1.anchor_changed is not None else np.zeros_like(m1)
        rows.append({"fold": f.test_year, "origin_cells": int(m1.size),
                     "e1_eligible": int(m1.sum()), "e2_eligible": int(m2.sum()), "common": int(both.sum()),
                     "e1_only": int((m1 & ~m2).sum()), "e2_only": int((m2 & ~m1).sum()),
                     "e2_anchored_at_origin": int(anchored.sum()), "e2_censored_no_target": int(censored.sum()),
                     "e1_eligible_anchor_switched": int((m1 & sw).sum()),
                     "e1_switch_share": float((m1 & sw).sum() / m1.sum()) if m1.sum() else np.nan})
    return pd.DataFrame(rows)


def _pool(g: pd.DataFrame) -> dict:
    n = g.n_cells.sum()
    return {"mae": float((g.mae * g.n_cells).sum() / n), "rmse": float(np.sqrt((g.rmse ** 2 * g.n_cells).sum() / n)),
            "n_cells": int(n), "n_days": int(g.n_days.sum())}


def paired_on_common(p1: Prepared, p2: Prepared, folds: List[Fold], preds1: Dict[int, Dict[str, np.ndarray]],
                     preds2: Dict[int, Dict[str, np.ndarray]]):
    """Per (fold, model, target) and pooled errors on the common sample. Models are those present in both."""
    per = []
    for f in folds:
        mask = common_mask(p1, p2, f.test)
        for name in preds1[f.test_year]:
            if name not in preds2[f.test_year]:
                continue
            for label, p, preds in (("nearest_expiry", p1, preds1), ("fixed_expiry", p2, preds2)):
                per.append({"fold": f.test_year, "model": name, "target": label,
                            **M.overall(p, f.test, preds[f.test_year][name], mask)})
    per = pd.DataFrame(per)
    pooled = pd.DataFrame([{"model": m, "target": t, **_pool(g)} for (m, t), g in per.groupby(["model", "target"])])
    ref = pooled[pooled.model == "persistence"].set_index("target").rmse
    pooled["mse_skill_vs_persistence"] = 1.0 - pooled.rmse ** 2 / pooled.target.map(ref) ** 2
    return per, pooled


def switch_breakdown(p1: Prepared, folds: List[Fold], preds1: Dict[int, Dict[str, np.ndarray]],
                     model: str = "persistence") -> pd.DataFrame:
    """E-1 error of ``model`` on its primary cells, split by whether the nearest-expiry anchor changed at the target."""
    if p1.anchor_changed is None:
        raise ValueError("panel was built without anchor expiries")
    ty, _ = target_arrays(p1)
    rows = []
    for f in folds:
        mask = M.eval_mask(p1, f.test, "primary")
        err = (preds1[f.test_year][model] - ty[f.test]) * M.PTS
        for name, sel in (("anchor_switched", p1.anchor_changed[f.test]), ("same_expiry", ~p1.anchor_changed[f.test])):
            s = M._stats(err[mask & sel])
            rows.append({"fold": f.test_year, "group": name, **s})
    df = pd.DataFrame(rows)
    out = []
    for name, g in df.groupby("group"):
        n = g.n_cells.sum()
        out.append({"group": name, "n_cells": int(n), "share": np.nan,
                    "mae": float((g.mae.fillna(0) * g.n_cells).sum() / n) if n else np.nan,
                    "rmse": float(np.sqrt((g.rmse.fillna(0) ** 2 * g.n_cells).sum() / n)) if n else np.nan})
    out = pd.DataFrame(out)
    out["share"] = out.n_cells / out.n_cells.sum()
    return out
