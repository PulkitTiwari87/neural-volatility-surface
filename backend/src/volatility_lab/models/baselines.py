"""Non-neural forecasters on the surface panel. All fitting uses the fold's TRAINING origins only;
the ridge penalty is chosen on the validation year; the test year is only predicted.

* ``persistence``   : tomorrow's surface = today's (causally forward-filled) surface.
* ``rolling_mean``  : mean of the last ``rolling_mean_window`` filled surfaces (a mean-reversion anchor).
* ``ridge``         : per-cell ridge on [surface, lagged surface changes, realised vol, availability]
                      predicting the change ``y_{t+h} - s_t`` (only cells observed in the label contribute).
* ``pca_ridge``     : ridge on the same features projected on the first PCA factors of the training
                      surfaces, predicting factor changes; reconstruction ``s_t + dz @ V``.
"""
from __future__ import annotations

from typing import Dict, Tuple

import numpy as np
import pandas as pd

from volatility_lab.config.settings import Config
from volatility_lab.evaluation.metrics import eval_mask
from volatility_lab.evaluation.walkforward import Fold
from volatility_lab.features.panel import Prepared, tabular_features, target_arrays, trailing_mean


def standardize_fit(X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    return mu, np.where(sd < 1e-8, 1.0, sd)


def ridge_fit(X: np.ndarray, Y: np.ndarray, M: np.ndarray, alpha: float):
    """Independent ridge per output column using only rows where ``M[:, c]``. Returns ``(W, b)``."""
    D, C = X.shape[1], Y.shape[1]
    W = np.zeros((D, C))
    b = np.zeros(C)
    eye = np.eye(D)
    for c in range(C):
        m = M[:, c]
        if m.sum() < D + 1:
            b[c] = float(np.nanmean(Y[m, c])) if m.any() else 0.0
            continue
        Xm, ym = X[m], Y[m, c]
        xbar, ybar = Xm.mean(axis=0), ym.mean()
        Xc = Xm - xbar
        W[:, c] = np.linalg.solve(Xc.T @ Xc + alpha * eye, Xc.T @ (ym - ybar))
        b[c] = ybar - xbar @ W[:, c]
    return W, b


def _masked_mse(pred, p, positions):
    m = eval_mask(p, positions, "all")
    y = target_arrays(p)[0][positions]
    return float(np.mean((pred - y)[m] ** 2)) if m.any() else np.inf


def predict_baselines(p: Prepared, fold: Fold, filled: np.ndarray, cfg: Config) -> Tuple[Dict[str, np.ndarray], dict]:
    """Return ``({name: prediction[n_test, C]}, chosen_hyperparameters)``."""
    fc, tc = cfg.features, cfg.train
    org = p.origins
    s_all = filled[org]
    y_all, ystat = target_arrays(p)
    out: Dict[str, np.ndarray] = {}
    chosen: dict = {}

    out["persistence"] = s_all[fold.test].copy()
    rm = pd.DataFrame(filled).rolling(fc.rolling_mean_window, min_periods=fc.rolling_mean_window).mean().to_numpy()
    out["rolling_mean"] = rm[org][fold.test]

    X = tabular_features(p, filled, fc)
    mu, sd = standardize_fit(X[fold.train])
    Xs = (X - mu) / sd
    D_all = y_all - s_all                      # NaN where the target cell is missing
    M_train = (ystat[fold.train] > 0) & np.isfinite(D_all[fold.train])

    best = (np.inf, None, None)
    curve = {}
    for a in tc.ridge_alphas:
        W, b = ridge_fit(Xs[fold.train], D_all[fold.train], M_train, a)
        v = _masked_mse(s_all[fold.val] + Xs[fold.val] @ W + b, p, fold.val)
        curve[a] = v
        if v < best[0]:
            best = (v, a, (W, b))
    a, (W, b) = best[1], best[2]
    out["ridge"] = s_all[fold.test] + Xs[fold.test] @ W + b
    chosen["ridge_alpha"] = a
    chosen["ridge_val_mse"] = curve        # validation-year masked MSE per penalty (the selection curve)

    # PCA factor model on training surfaces
    S_tr = s_all[fold.train]
    mean_s = S_tr.mean(axis=0)
    _, _, vt = np.linalg.svd(S_tr - mean_s, full_matrices=False)
    V = vt[: fc.pca_components]                                   # (K, C)
    Z = (filled - mean_s) @ V.T                                  # (n, K) scores of every row
    z_t = Z[org]
    parts = [z_t] + [z_t - Z[org - lag] for lag in fc.lags] + [p.rv[org], p.avail[org].mean(axis=1, keepdims=True)]
    if p.calendar is not None:
        parts.append(p.calendar[org])
    if p.mr_window is not None:
        parts.append(z_t - trailing_mean(Z, p.mr_window)[org])
    Xz = np.hstack(parts)
    muz, sdz = standardize_fit(Xz[fold.train])
    Xzs = (Xz - muz) / sdz
    if p.target_iv is None:                                      # E-1: the filled surface at the target row
        dZ = Z[p.targets] - z_t
    else:                                                        # E-2: the tracked-expiry target; no-label cells = no change
        tgt = np.where(np.isfinite(D_all) & (ystat > 0), y_all, s_all)
        dZ = (tgt - mean_s) @ V.T - z_t
    ones = np.ones_like(dZ, dtype=bool)
    best = (np.inf, None, None)
    curve = {}
    for a in tc.ridge_alphas:
        Wz, bz = ridge_fit(Xzs[fold.train], dZ[fold.train], ones[fold.train], a)
        v = _masked_mse(s_all[fold.val] + (Xzs[fold.val] @ Wz + bz) @ V, p, fold.val)
        curve[a] = v
        if v < best[0]:
            best = (v, a, (Wz, bz))
    a, (Wz, bz) = best[1], best[2]
    out["pca_ridge"] = s_all[fold.test] + (Xzs[fold.test] @ Wz + bz) @ V
    chosen["pca_ridge_alpha"] = a
    chosen["pca_ridge_val_mse"] = curve
    return out, chosen
