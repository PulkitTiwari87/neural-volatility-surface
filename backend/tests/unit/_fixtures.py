"""Shared, cached SYNTHETIC fixtures (generated once per test process)."""
import functools

from volatility_lab.config.settings import Config, SplitConfig
from volatility_lab.datasets.synthetic import make_chain
from volatility_lab.features.panel import prepare
from volatility_lab.ingestion.optionsdx import RejectLedger, prefilter_batch
from volatility_lab.surfaces.grid import build_surface_panel
from volatility_lab.validation.quotes import build_otm_quotes

CFG = Config(split=SplitConfig(first_test_year=2020, last_test_year=2020, min_train_years=1))


@functools.lru_cache(maxsize=None)
def chain(n_days=560, seed=3, noise_free=True):
    return make_chain(n_days, seed=seed, noise_free=noise_free)


@functools.lru_cache(maxsize=None)
def pipeline(n_days=560, seed=3):
    wide_raw, truth = chain(n_days, seed)
    led = RejectLedger()
    wide = prefilter_batch(wide_raw, CFG.data, led)
    quotes, qled, diag = build_otm_quotes(wide, CFG.data)
    panel = build_surface_panel(quotes, CFG.surface)
    return {"raw": wide_raw, "truth": truth, "wide": wide, "quotes": quotes, "panel": panel, "ledger1": led,
            "ledger2": qled, "diag": diag, "prepared": prepare(panel, CFG.features)}