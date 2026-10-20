"""Expanding-window walk-forward folds with purging.

For each test year ``Y``: validation = year ``Y-1`` (early stopping / ridge penalty only), training = all
years before the validation year. Training origins whose *target day* falls on or after the first
validation origin are purged (their label would otherwise be a validation-period value); validation
origins are purged the same way against the test period. The test year is never used for selection.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np

from volatility_lab.config.settings import SplitConfig
from volatility_lab.features.panel import Prepared


@dataclass
class Fold:
    test_year: int
    val_year: int
    train: np.ndarray   # positions into p.origins
    val: np.ndarray
    test: np.ndarray
    train_rows_end: int  # last panel row any training label touches (for fitting fill values)


def make_folds(p: Prepared, cfg: SplitConfig, val_mode: str = "prev_year", val_frac: float = 0.2) -> List[Fold]:
    """``val_mode='prev_year'`` is E-1/E-2. ``'tail_frac'`` (experiment H2) validates on the chronologically last
    ``val_frac`` of the origins available before the test year (labels purged against the test period); training =
    the earlier origins whose labels end before the first validation origin. ``Fold.val_year`` is then only a label."""
    if val_mode not in ("prev_year", "tail_frac"):
        raise ValueError(f"unknown val_mode: {val_mode}")
    oyear = p.year[p.origins]
    odate = p.dates[p.origins]
    tdate = p.dates[p.targets]
    folds = []
    for Y in range(cfg.first_test_year, cfg.last_test_year + 1):
        test = np.flatnonzero(oyear == Y)
        if val_mode == "tail_frac":
            pool = np.flatnonzero((oyear < Y) & (tdate < odate[test].min())) if test.size else test
            if pool.size == 0:
                continue
            n_val = max(1, int(np.ceil(val_frac * pool.size)))
            val, train = pool[-n_val:], pool[:-n_val]
            train = train[tdate[train] < odate[val].min()]
            if len(np.unique(oyear[train])) < cfg.min_train_years or train.size == 0:
                continue
            folds.append(Fold(Y, Y - 1, train, val, test, int(p.targets[train].max())))
            continue
        val = np.flatnonzero(oyear == Y - 1)
        if test.size == 0 or val.size == 0:
            continue
        train = np.flatnonzero((oyear < Y - 1) & (tdate < odate[val].min()))
        val = val[tdate[val] < odate[test].min()]
        if len(np.unique(oyear[train])) < cfg.min_train_years or val.size == 0:
            continue
        folds.append(Fold(Y, Y - 1, train, val, test, int(p.targets[train].max())))
    if not folds:
        raise ValueError("no walk-forward fold satisfies the split configuration")
    return folds


class LeakageError(AssertionError):
    """A fold lets label or origin dates of one set reach into a later set. Subclasses ``AssertionError`` so existing
    callers keep working, but it is *raised*, not asserted: ``python -O`` strips ``assert`` and would silently disable
    the check."""


def assert_no_overlap(p: Prepared, f: Fold) -> None:
    """Hard leakage check: label days and origins are chronologically separated across the three sets."""
    odate, tdate = p.dates[p.origins], p.dates[p.targets]
    if min(f.train.size, f.val.size, f.test.size) == 0:
        raise LeakageError("a fold set is empty: the chronological check cannot be evaluated")
    if not tdate[f.train].max() < odate[f.val].min():
        raise LeakageError("train labels reach into validation")
    if not tdate[f.val].max() < odate[f.test].min():
        raise LeakageError("validation labels reach into test")
    if not odate[f.train].max() < odate[f.val].min() <= odate[f.val].max() < odate[f.test].min():
        raise LeakageError("origins not chronological")
