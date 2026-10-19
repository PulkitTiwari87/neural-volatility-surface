"""Pre-registered DESCRIPTIVE decision rule for "improves on persistence" wording (owner-approved 2026-10-16).

Source of truth: docs/research/PHASE4_NEURAL_EVIDENCE_REVIEW.md section 3. This is a checklist over numbers that
``runner.evaluate_all`` already produced; it is **not** a statistical test and produces no p-value or interval (L-22).

A model "improves on persistence under one label" only if ALL applicable criteria hold on the primary cells:
  a. pooled MSE skill vs persistence > 0 AND pooled MAE below persistence's;
  b. better than persistence by daily MAE in at least ``min_years_better`` test years;
  c. every seed's pooled MSE skill > 0 (``None`` = not applicable, e.g. deterministic baselines);
  d. skill > 0 in at least ``min_regimes`` realised-volatility regimes that each have n >= ``min_cells`` cells.
Criterion e is ``combine_labels``: it must hold under BOTH the nearest-expiry and the fixed-expiry label, otherwise
the result is reported as holding under one label only (never as a general improvement).
A criterion that cannot be evaluated is ``None`` (never silently passed).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _regime_mse(brk: pd.DataFrame, model: str) -> pd.DataFrame:
    r = brk[(brk.group_type == "rv_regime") & (brk.model == model)]
    out = {}
    for g, d in r.groupby("group"):
        n = int(d.n_cells.sum())
        sse = float((d.rmse.fillna(0.0) ** 2 * d.n_cells).sum())
        out[str(g)] = (n, sse / n if n else np.nan)
    return pd.DataFrame(out, index=["n", "mse"]).T


def improvement_rule(pooled: pd.DataFrame, brk: pd.DataFrame, paired: pd.DataFrame, model: str, *,
                     min_years_better: int = 6, min_regimes: int = 2, min_cells: int = 100,
                     seed_skills=None) -> dict:
    """Evaluate criteria a-d for ``model`` under one label. Returns ``{"a": {...}, ..., "label_pass": bool | None}``."""
    pr = pooled[pooled.cells == "primary"].set_index("model")
    skill, mae_m, mae_p = float(pr.loc[model, "mse_skill_vs_persistence"]), float(pr.loc[model, "mae"]), float(pr.loc["persistence", "mae"])
    a = {"pass": bool(skill > 0 and mae_m < mae_p), "detail": f"MSE skill {skill:+.4f}, MAE {mae_m:.4f} vs persistence {mae_p:.4f}"}

    row = paired[paired.model == model]
    if row.empty:
        b = {"pass": None, "detail": "no paired daily comparison for this model"}
    else:
        better, total = (int(x) for x in str(row.iloc[0].folds_better_than_persistence).split("/"))
        b = ({"pass": None, "detail": f"{better}/{total} years better; fewer than {min_years_better} years evaluated"} if total < min_years_better
             else {"pass": better >= min_years_better, "detail": f"{better}/{total} test years better by daily MAE (need >= {min_years_better})"})

    if seed_skills is None:
        c = {"pass": None, "detail": "not applicable (deterministic model, no seeds)"}
    else:
        c = {"pass": bool(len(seed_skills) > 0 and all(s > 0 for s in seed_skills)),
             "detail": "per-seed pooled MSE skill: " + ", ".join(f"{s:+.4f}" for s in seed_skills)}

    rm, rp = _regime_mse(brk, model), _regime_mse(brk, "persistence")
    elig = [g for g in rm.index if g in rp.index and rm.loc[g, "n"] >= min_cells and rp.loc[g, "n"] >= min_cells
            and np.isfinite(rm.loc[g, "mse"]) and rp.loc[g, "mse"] > 0]
    sk = {g: 1.0 - rm.loc[g, "mse"] / rp.loc[g, "mse"] for g in elig}
    if len(elig) < min_regimes:
        d = {"pass": None, "detail": f"only {len(elig)} regime(s) with n >= {min_cells}; need {min_regimes}"}
    else:
        d = {"pass": sum(v > 0 for v in sk.values()) >= min_regimes,
             "detail": "regime MSE skill: " + ", ".join(f"{g} {v:+.4f}" for g, v in sorted(sk.items()))}

    crit = {"a": a, "b": b, "c": c, "d": d}
    if any(crit[k]["pass"] is False for k in "abcd"):
        label_pass = False
    elif any(crit[k]["pass"] is None for k in "abd"):
        label_pass = None
    else:
        label_pass = True
    return {**crit, "label_pass": label_pass}


def combine_labels(nearest: dict, fixed: dict) -> str:
    """Criterion e. ``nearest``/``fixed`` are ``improvement_rule`` results under the two target definitions."""
    n, f = nearest["label_pass"], fixed["label_pass"]
    if n is True and f is True:
        return "improves_on_persistence_under_both_labels"
    if n is True:
        return "holds_under_nearest_expiry_label_only"
    if f is True:
        return "holds_under_fixed_expiry_label_only"
    if n is None and f is None:
        return "not_evaluable"
    return "no_improvement_shown"
