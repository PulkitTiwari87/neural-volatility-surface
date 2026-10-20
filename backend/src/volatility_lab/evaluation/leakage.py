"""Executable leakage audit: features at an origin must not change when anything AFTER it changes."""
from __future__ import annotations

import dataclasses

import numpy as np

from volatility_lab.config.settings import Config
from volatility_lab.features.panel import (Prepared, causal_fill, cell_means, realized_vol, sequence_features,
                                           tabular_features)


def perturb_after(p: Prepared, row: int, cfg: Config, seed: int = 0) -> Prepared:
    """Copy of ``p`` whose surfaces, status and spot AFTER ``row`` are replaced by random values."""
    rng = np.random.default_rng(seed)
    iv, spot, st = p.iv.copy(), p.spot.copy(), p.status.copy()
    iv[row + 1:] = rng.uniform(0.05, 0.9, iv[row + 1:].shape)
    spot[row + 1:] = rng.uniform(100, 900, spot[row + 1:].shape)
    st[row + 1:] = 3
    changes = {}
    if p.calendar is not None:
        # the calendar block (days-to-expiry per tenor, weekday) is also an input: a feature that read a LATER row of it
        # must be caught, so the rows after the origin are scrambled too
        cal = p.calendar.copy()
        cal[row + 1:] = rng.uniform(0.0, 400.0, cal[row + 1:].shape)
        changes["calendar"] = cal
    return dataclasses.replace(p, iv=iv, spot=spot, status=st, avail=st > 0,
                               rv=realized_vol(spot, cfg.features.rv_windows), **changes)


def feature_invariance_check(p: Prepared, cfg: Config, row: int | None = None) -> dict:
    """Return a report; ``passed`` is True iff every tabular and sequence feature at origins <= ``row`` is identical."""
    row = int(row if row is not None else p.origins[len(p.origins) // 2])
    q = perturb_after(p, row, cfg)
    rows = np.arange(0, row + 1)
    fv = cell_means(p, rows)
    same_fill = np.array_equal(fv, cell_means(q, rows))
    f1, f2 = causal_fill(p, cfg.features.ffill_days, fv), causal_fill(q, cfg.features.ffill_days, fv)
    sel = p.origins <= row
    tab = np.array_equal(tabular_features(p, f1, cfg.features)[sel], tabular_features(q, f2, cfg.features)[sel])
    seq = np.array_equal(sequence_features(p, f1, cfg.features)[sel], sequence_features(q, f2, cfg.features)[sel])
    return {"perturbed_after_row": row, "origins_checked": int(sel.sum()), "fill_values_identical": same_fill,
            "tabular_identical": tab, "sequence_identical": seq, "passed": bool(same_fill and tab and seq)}