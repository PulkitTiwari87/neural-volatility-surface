"""Orchestration: hosted files -> surfaces -> baselines -> GPU neural models -> descriptive evaluation.

Everything here is deterministic given (data bytes, Config, seeds). Outputs go to a caller-chosen
``out_dir`` (a Colab runtime path, optionally mirrored to Drive by the notebook); nothing is written to the
repository. No inferential statistic is computed: comparisons are descriptive with explicit counts.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from volatility_lab.config.settings import Config
from volatility_lab.evaluation import evidence
from volatility_lab.evaluation import metrics as M
from volatility_lab.evaluation.walkforward import Fold, assert_no_overlap
from volatility_lab.features.panel import (Prepared, causal_fill, cell_means, sequence_features,
                                           tabular_features, target_arrays)
from volatility_lab.ingestion.optionsdx import discover_files, fingerprint_files, load_wide
from volatility_lab.models import baselines
from volatility_lab.surfaces.diagnostics import diagnostics_report
from volatility_lab.surfaces.grid import STATUS_LABELS, build_surface_panel, status_counts
from volatility_lab.validation.quotes import build_otm_quotes


# ----------------------------------------------------------------------------- data -> surfaces
def build_surfaces(root, cfg: Config, *, max_rows=None, fingerprint=True, log=print) -> dict:
    files = discover_files(root)
    log(f"files: {[f.name for f in files]}")
    fp = fingerprint_files(files) if fingerprint else None
    wide, ledger1 = load_wide(files, cfg.data, max_rows=max_rows)
    log(f"prefilter ledger: {ledger1.to_dict()}")
    quotes, ledger2, diag = build_otm_quotes(wide, cfg.data)
    log(f"quote ledger: {ledger2.to_dict()}")
    panel = build_surface_panel(quotes, cfg.surface)
    return {"panel": panel, "fingerprint": fp, "ledger_prefilter": ledger1.to_dict(), "ledger_quotes": ledger2.to_dict(),
            "quote_diagnostics": diag, "surface_status_counts": status_counts(panel),
            "arbitrage_diagnostics": diagnostics_report(panel), "n_wide_rows_after_prefilter": int(len(wide)),
            "quotes": quotes}


def save_panel(panel: dict, path) -> None:
    np.savez_compressed(path, **panel)


def load_panel(path) -> dict:
    with np.load(path) as z:
        return {k: z[k] for k in z.files}


def data_audit(built: dict) -> dict:
    q, panel = built["quotes"], built["panel"]
    d = panel["dates"].astype("datetime64[D]")
    years = d.astype("datetime64[Y]").astype(int) + 1970
    per_year = pd.Series(years).value_counts().sort_index().to_dict()
    st = panel["status"]
    return {
        "first_date": str(d[0]), "last_date": str(d[-1]), "n_surface_dates": int(len(d)),
        "surface_dates_per_year": {int(k): int(v) for k, v in per_year.items()},
        "max_calendar_gap_days": int(np.diff(panel["dates"]).max()),
        "n_quotes": int(len(q)), "quotes_per_date_median": float(np.median(panel["n_quotes"])),
        "cells_total": int(st.size),
        "cell_share": {STATUS_LABELS[c]: float((st == c).mean()) for c in (0, 1, 2, 3)},
        "cell_share_by_tenor_observed": {int(t): float((st[:, j, :] == 3).mean()) for j, t in enumerate(panel["tenor_days"])},
        "median_rel_spread": float(q.rel_spread.median()),
        "iv_percentiles_pts": {str(p): float(np.percentile(q.iv, p) * 100) for p in (1, 5, 50, 95, 99)},
    }


# ----------------------------------------------------------------------------- model runs
def _fold_inputs(p: Prepared, f: Fold, cfg: Config):
    fill = cell_means(p, np.arange(0, f.train_rows_end + 1))
    return causal_fill(p, cfg.features.ffill_days, fill)


def _log_fold_access(access_log, f: Fold) -> None:
    """GR-LEAK-05: train rows fit, validation rows select, test rows are only predicted/scored."""
    if access_log is not None:
        access_log.record("fit", "train", len(f.train))
        access_log.record("select", "val", len(f.val))
        access_log.record("predict", "test", len(f.test))


def run_baselines(p: Prepared, folds: List[Fold], cfg: Config, log=print, access_log=None):
    """``access_log`` (optional ``evaluation.access_log.AccessLog``): records window use per fold; no numerical effect."""
    preds, chosen = {}, {}
    for f in folds:
        assert_no_overlap(p, f)
        _log_fold_access(access_log, f)
        filled = _fold_inputs(p, f, cfg)
        preds[f.test_year], chosen[f.test_year] = baselines.predict_baselines(p, f, filled, cfg)
        log(f"baselines fold {f.test_year}: train={len(f.train)} val={len(f.val)} test={len(f.test)} { {k: v for k, v in chosen[f.test_year].items() if k.endswith('_alpha')} }")
    return preds, chosen


def pca_factor_targets(s_all, D, M_, train, k):
    """Factor-space targets for experiment H5: basis ``V`` (k, C) from the TRAINING surfaces only; ``D`` -> its projection
    (missing-label cells = no change), loss mask all True."""
    mean_s = s_all[train].mean(axis=0)
    V = np.linalg.svd(s_all[train] - mean_s, full_matrices=False)[2][:k]
    return np.where(M_, D, 0.0) @ V.T, np.ones((D.shape[0], k), dtype=bool), V


class BaselineGateError(RuntimeError):
    """GR-MOD-01: a neural run was requested without persistence and a regression baseline for every fold."""


def require_baselines(baseline_preds: Dict[int, Dict[str, np.ndarray]], folds: List[Fold]) -> None:
    """Raise unless every fold has persistence and at least one regression baseline (``ridge`` or ``pca_ridge``)."""
    problems = []
    for f in folds:
        have = baseline_preds.get(f.test_year, {})
        if "persistence" not in have:
            problems.append(f"fold {f.test_year}: no persistence")
        if not ({"ridge", "pca_ridge"} & set(have)):
            problems.append(f"fold {f.test_year}: no regression baseline")
    if problems:
        raise BaselineGateError("; ".join(problems))


# ----------------------------------------------------------------------------- resume-cache identity (AP-004, C-01)
RUN_KEY_FILE = "run_key.json"
RUN_KEY_SCHEMA = "run-key-1"


class RunKeyError(RuntimeError):
    """Saved predictions in ``out_dir`` cannot be proven to belong to this run: refused (fail closed)."""


def _array_sha256(a: np.ndarray) -> str:
    a = np.ascontiguousarray(a)
    h = hashlib.sha256(f"{a.dtype.str}|{a.shape}|".encode())
    h.update(a.tobytes())
    return h.hexdigest()


def _fingerprint(obj) -> dict:
    """Every field of a dataclass (``Prepared``, ``Fold``) as JSON, arrays by content hash. A field of any other type
    raises: it is never silently stringified into the key."""
    out = {}
    for f in dataclasses.fields(obj):
        v = getattr(obj, f.name)
        if isinstance(v, np.ndarray):
            out[f.name] = {"array_sha256": _array_sha256(v)}
        elif v is None or isinstance(v, (bool, str)):
            out[f.name] = v
        elif isinstance(v, (int, np.integer)):
            out[f.name] = int(v)
        elif isinstance(v, (float, np.floating)):
            out[f.name] = float(v)
        else:
            raise TypeError(f"cannot fingerprint {type(obj).__name__}.{f.name} of type {type(v).__name__}")
    return out


def run_key(p: Prepared, folds: List[Fold], cfg: Config, pca_factors=None) -> dict:
    """Everything that decides whether saved ``(fold, model, seed)`` predictions may be reused. ``cfg.sha256()`` alone is not
    enough: the experiment flags (label, calendar block, ``mr_window``, ...) live on ``Prepared`` and ``pca_factors`` is an
    argument, so H2/H3/H4 shared one config hash. Arrays are hashed by content (dtype and shape included), so a different
    panel, label, fold boundary or feature block gives a different key. With ``pca_factors`` the basis is recomputed on
    resume and its sign depends on the LAPACK build, so the numpy/platform identity is part of the key."""
    key = {"schema": RUN_KEY_SCHEMA, "config_sha256": cfg.sha256(), "pca_factors": pca_factors,
           "prepared": _fingerprint(p), "folds": [_fingerprint(f) for f in folds]}
    if pca_factors:
        key["pca_env"] = {"numpy": np.__version__, "python": platform.python_version(),
                          "machine": platform.machine(), "system": platform.system()}
    return key


def _canonical(key) -> str:
    return json.dumps(key, sort_keys=True, indent=1, allow_nan=False)


def claim_out_dir(out_dir, key: dict) -> str:
    """Bind ``out_dir`` to ``key``. Returns ``"new"`` (key written) or ``"resume"`` (identical key already there).

    Raises ``RunKeyError`` when saved files exist without a key (older version), when the key is unreadable or
    malformed, or when it differs in any way. Nothing is deleted or rewritten on a refusal."""
    out_dir = Path(out_dir)
    kf = out_dir / RUN_KEY_FILE
    mine = _canonical(key)
    if kf.exists():
        try:
            stored = _canonical(json.loads(kf.read_text(encoding="utf-8")))
        except (OSError, ValueError) as e:
            raise RunKeyError(f"{kf} is unreadable or malformed ({e.__class__.__name__}); use a new out_dir") from e
        if stored != mine:
            raise RunKeyError(f"{out_dir} holds predictions of a different run (config, label, features, folds, data or "
                              f"environment differ); use a new out_dir")
        return "resume"
    saved = [f for sub, pat in (("predictions", "*.npy"), ("checkpoints", "*.pt"), ("histories", "*.json"))
             for f in (out_dir / sub).glob(pat)]
    if saved:
        raise RunKeyError(f"{out_dir} has {len(saved)} saved file(s) but no {RUN_KEY_FILE} (written by an older version): "
                          f"they cannot be proven to belong to this run; use a new out_dir")
    tmp = kf.with_name(kf.name + ".tmp")
    tmp.write_text(mine, encoding="utf-8")
    tmp.replace(kf)
    return "new"


def run_neural(p: Prepared, folds: List[Fold], cfg: Config, out_dir, *, torch_module=None, log=print, pca_factors=None,
               baseline_preds=None, access_log=None):
    """Train/predict every (fold, model, seed); resumes from files already present in ``out_dir`` only if its
    ``run_key.json`` matches this run exactly (``RunKeyError`` otherwise, including for older directories without one).

    ``pca_factors=K`` (experiment H5): the network predicts the K PCA-factor changes (basis fitted on the training
    surfaces of the fold only, as in the PCA-ridge baseline) instead of every cell; the cell forecast is
    ``s_t + delta_z @ V``. Cells without a label count as "no change". Loss weights are all ones.

    ``baseline_preds`` (the ``run_baselines`` output for the same panel and folds): when given, the run is refused
    unless persistence and a regression baseline exist for every fold (GR-MOD-01). It is optional only because the
    already-executed H1-H6 notebooks call this function without it; new callers should pass it.

    ``access_log`` (optional ``AccessLog``): records train-fit / val-select / test-predict use per fold (GR-LEAK-05)."""
    if baseline_preds is not None:
        require_baselines(baseline_preds, folds)
    from volatility_lab.models import neural  # lazy: needs PyTorch + CUDA
    device = neural.require_cuda(torch_module)  # raises before any work (or any file) when no GPU
    log(f"GPU: {device}")
    out_dir = Path(out_dir)
    for sub in ("checkpoints", "predictions", "histories"):
        (out_dir / sub).mkdir(parents=True, exist_ok=True)
    claim_out_dir(out_dir, run_key(p, folds, cfg, pca_factors))   # refuses to resume another run's predictions
    preds: Dict[int, Dict[str, np.ndarray]] = {}
    for f in folds:
        assert_no_overlap(p, f)
        _log_fold_access(access_log, f)
        filled = _fold_inputs(p, f, cfg)
        s_all = filled[p.origins]
        y_all, ystat = target_arrays(p)
        D = y_all - s_all
        M_ = (ystat > 0) & np.isfinite(D)
        if pca_factors:
            D, M_, V = pca_factor_targets(s_all, D, M_, f.train, pca_factors)
        feats = {}
        if "mlp" in cfg.train.models:
            feats["mlp"] = tabular_features(p, filled, cfg.features)
        if "gru" in cfg.train.models:
            feats["gru"] = sequence_features(p, filled, cfg.features)
        preds[f.test_year] = {}
        for kind in cfg.train.models:
            X = feats[kind]
            data = {"Xtr": X[f.train], "Dtr": D[f.train], "Mtr": M_[f.train], "Xva": X[f.val], "Dva": D[f.val],
                    "Mva": M_[f.val], "Xte": X[f.test]}
            for seed in cfg.train.seeds:
                tag = f"fold{f.test_year}_{kind}_seed{seed}"
                pf = out_dir / "predictions" / f"{tag}.npy"
                ck = out_dir / "checkpoints" / f"{tag}.pt"
                hf = out_dir / "histories" / f"{tag}.json"
                if pf.exists() and ck.exists() and hf.exists():
                    delta = np.load(pf)
                    log(f"resume: {tag}")
                else:
                    r = neural.train_and_predict(kind, data, cfg.train, seed, torch_module=torch_module,
                                                 ckpt_path=str(ck), log=log)
                    delta = r.pop("pred_delta")
                    np.save(pf, delta)
                    hf.write_text(json.dumps(r, indent=1))
                    log(f"{tag}: epochs={r['epochs_run']} best_epoch={r['best_epoch']} {r['seconds']}s peak_mem={r['peak_gpu_mem_mb']}MB")
                preds[f.test_year][f"{kind}_s{seed}"] = s_all[f.test] + (delta @ V if pca_factors else delta)
            stack = np.stack([preds[f.test_year][f"{kind}_s{s}"] for s in cfg.train.seeds])
            preds[f.test_year][f"{kind}_ens"] = stack.mean(axis=0)
    return preds, device


# ----------------------------------------------------------------------------- evaluation
def export_forecasts(p: Prepared, folds: List[Fold], preds: Dict[int, Dict[str, np.ndarray]], out_dir) -> List[str]:
    """Write ``out_dir/forecasts/<model>.npz`` (``target_index``, ``origin_index``, ``pred`` (n, T, K)) for the viewer API.

    Indices are panel rows. Forecasts are the out-of-sample test-fold predictions exactly as evaluated; nothing is
    re-fitted or re-computed here. ``origin_index < target_index`` always holds (horizon >= 1). Under the E-2 label the
    viewer's "actual" is still the surface at the target date, not the same-expiry label the model was scored on.
    """
    sub = Path(out_dir) / "forecasts"
    sub.mkdir(parents=True, exist_ok=True)
    names = sorted({n for f in folds for n in preds[f.test_year]})
    for name in names:
        fs = [f for f in folds if name in preds[f.test_year]]
        pos = np.concatenate([f.test for f in fs])
        pred = np.concatenate([preds[f.test_year][name] for f in fs]).reshape(len(pos), p.n_tenor, p.n_k)
        np.savez_compressed(sub / f"{name}.npz", target_index=p.targets[pos], origin_index=p.origins[pos], pred=pred)
    return names


def evaluate_all(p: Prepared, folds: List[Fold], preds: Dict[int, Dict[str, np.ndarray]]):
    """Return ``(per_fold, pooled, breakdown, paired)`` DataFrames. Descriptive only (no p-values/CIs)."""
    per_fold, brk, daily = [], [], {}
    for f in folds:
        cuts = M.rv_terciles(p, f.train)
        for kind in ("primary", "all"):
            mask = M.eval_mask(p, f.test, kind)
            for name, pred in preds[f.test_year].items():
                per_fold.append({"fold": f.test_year, "model": name, "cells": kind, **M.overall(p, f.test, pred, mask)})
                if kind == "primary":
                    b = M.breakdowns(p, f.test, pred, mask, cuts)
                    b["fold"], b["model"] = f.test_year, name
                    brk.append(b)
                    daily.setdefault(name, []).append((f.test_year, M.daily_mae(p, f.test, pred, mask)))
    per_fold = pd.DataFrame(per_fold)
    brk = pd.concat(brk, ignore_index=True)

    rows = []
    for (cells, model), g in per_fold.groupby(["cells", "model"]):
        n = g.n_cells.sum()
        rows.append({"cells": cells, "model": model, "mae": (g.mae * g.n_cells).sum() / n,
                     "rmse": float(np.sqrt((g.rmse ** 2 * g.n_cells).sum() / n)), "n_cells": int(n),
                     "n_days": int(g.n_days.sum()), "n_folds": int(g.fold.nunique())})
    pooled = pd.DataFrame(rows)
    ref = pooled[pooled.model == "persistence"].set_index("cells").rmse
    pooled["mse_skill_vs_persistence"] = 1.0 - (pooled.rmse ** 2) / (pooled.cells.map(ref) ** 2)

    base = dict(daily["persistence"])
    prow = []
    for name, lst in daily.items():
        if name == "persistence":
            continue
        diffs, better_folds, tot_folds = [], 0, 0
        for fy, d in lst:
            ok = np.isfinite(d) & np.isfinite(base[fy])
            if ok.any():
                diffs.append(d[ok] - base[fy][ok])
                tot_folds += 1
                better_folds += int(np.mean(d[ok]) < np.mean(base[fy][ok]))
        dd = np.concatenate(diffs) if diffs else np.array([])
        prow.append({"model": name, "n_days": int(dd.size),
                     "mean_daily_mae_diff_vs_persistence_pts": float(dd.mean()) if dd.size else np.nan,
                     "share_of_days_better": float((dd < 0).mean()) if dd.size else np.nan,
                     "folds_better_than_persistence": f"{better_folds}/{tot_folds}"})
    return per_fold, pooled, brk, pd.DataFrame(prow)


# ----------------------------------------------------------------------------- provenance
def environment_metadata() -> dict:
    meta = {"python": sys.version.split()[0], "platform": platform.platform(), "numpy": np.__version__,
            "pandas": pd.__version__}
    try:
        import torch  # noqa: PLC0415
        meta["torch"] = torch.__version__
        meta["cuda_available"] = bool(torch.cuda.is_available())
    except (ImportError, OSError):
        meta["torch"] = None
    try:
        meta["nvidia_smi"] = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version,utilization.gpu", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=20).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        meta["nvidia_smi"] = None
    return meta


def write_manifest(out_dir, extra: dict) -> dict:
    """Hash every file under ``out_dir`` and write ``manifest.json`` (excluded from its own listing)."""
    out_dir = Path(out_dir)
    if "claim_level" in extra:              # opt-in: a record that states a claim level must meet the evidence rules
        evidence.require_valid(extra)
    files = {}
    for fp in sorted(out_dir.rglob("*")):
        if fp.is_file() and fp.name != "manifest.json":
            files[str(fp.relative_to(out_dir))] = {"bytes": fp.stat().st_size,
                                                    "sha256": hashlib.sha256(fp.read_bytes()).hexdigest()}
    manifest = {**extra, "files": files}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=1, default=str))
    return manifest


def verify_manifest(out_dir) -> list:
    """Re-open and re-hash every file listed in the manifest; returns the list of problems (empty = OK)."""
    out_dir = Path(out_dir)
    m = json.loads((out_dir / "manifest.json").read_text())
    bad = []
    for rel, info in m["files"].items():
        fp = out_dir / rel
        if not fp.exists():
            bad.append(f"missing {rel}")
        elif hashlib.sha256(fp.read_bytes()).hexdigest() != info["sha256"]:
            bad.append(f"hash mismatch {rel}")
    return bad