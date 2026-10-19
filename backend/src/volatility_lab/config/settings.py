"""All tunable settings in one place (the notebook builds a ``Config`` and nothing else).

Every value is a *research setting for this experiment*, not an adopted product decision
(see decision.md DEC-012..DEC-015 and the experiment record in the run manifest).
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class DataConfig:
    kaggle_dataset: str = "dudesurfin/spy-options-eod-volatility-surface-2010-2023"
    # pre-filters applied while streaming batches (counted in the reject ledger)
    min_dte: int = 2
    max_dte: int = 400
    max_abs_log_strike: float = 0.45       # |ln(K/S)| pre-filter
    batch_rows: int = 500_000
    # per-quote filters (applied after the forward is known)
    min_mid: float = 0.05                  # USD; SPY tick is 0.01
    max_rel_spread: float = 0.35           # (ask-bid)/mid
    min_iv: float = 0.02
    max_iv: float = 3.0
    max_abs_k: float = 0.30                # |ln(K/F)| kept for the surface
    # forward / discount-factor estimation from put-call parity
    parity_window_k: float = 0.06          # near-ATM pairs used
    min_parity_pairs: int = 3
    regression_min_pairs: int = 5
    regression_min_T: float = 30 / 365
    df_bounds: Tuple[float, float] = (0.90, 1.01)
    forward_ratio_bounds: Tuple[float, float] = (0.85, 1.15)  # F/S plausibility


@dataclass(frozen=True)
class SurfaceConfig:
    tenor_days: Tuple[int, ...] = (7, 14, 30, 60, 91, 182)
    k_nodes: Tuple[float, ...] = (-0.20, -0.12, -0.08, -0.04, -0.02, 0.0, 0.02, 0.04, 0.08)
    min_quotes_per_slice: int = 5
    gap_tight: float = 0.02                # adjacent-quote gap in k treated as "observed"
    tol_obs_days: float = 1.0              # expiry within this many days of the tenor ...
    tol_obs_frac: float = 0.015            # ... or this fraction of the tenor (larger wins)


@dataclass(frozen=True)
class FeatureConfig:
    horizon: int = 1                       # forecast horizon in trading days (rows of the panel)
    lags: Tuple[int, ...] = (1, 5)
    ffill_days: int = 5
    seq_len: int = 20
    rv_windows: Tuple[int, ...] = (5, 20)
    rolling_mean_window: int = 20
    pca_components: int = 3


@dataclass(frozen=True)
class SplitConfig:
    first_test_year: int = 2016
    last_test_year: int = 2023
    min_train_years: int = 3               # years strictly before the validation year


@dataclass(frozen=True)
class TrainConfig:
    seeds: Tuple[int, ...] = (0, 1, 2)
    max_epochs: int = 150
    patience: int = 15
    batch_size: int = 128
    lr: float = 1e-3
    weight_decay: float = 1e-4
    hidden: int = 128
    gru_hidden: int = 64
    dropout: float = 0.1
    ridge_alphas: Tuple[float, ...] = (0.1, 1.0, 10.0, 100.0, 1000.0)
    models: Tuple[str, ...] = ("mlp", "gru")


@dataclass(frozen=True)
class Config:
    data: DataConfig = field(default_factory=DataConfig)
    surface: SurfaceConfig = field(default_factory=SurfaceConfig)
    features: FeatureConfig = field(default_factory=FeatureConfig)
    split: SplitConfig = field(default_factory=SplitConfig)
    train: TrainConfig = field(default_factory=TrainConfig)

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    def sha256(self) -> str:
        blob = json.dumps(self.to_dict(), sort_keys=True, default=list).encode()
        return hashlib.sha256(blob).hexdigest()
