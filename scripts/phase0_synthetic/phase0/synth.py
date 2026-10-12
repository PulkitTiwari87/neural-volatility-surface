"""Deterministic SYNTHETIC option-chain generator. SYNTHETIC SPIKE - not market data.

World RW: volatility factors follow random walks (persistence is Bayes-optimal).
World AR: factors follow AR(1) around a mean (known predictable component).
All randomness comes from random.Random(seed).random() (ADR-0003).
"""
import hashlib
import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .bsm import black76_price, price_bounds

ORIGIN = "synthetic"
DEFECT_TYPES = (
    "NEGATIVE_PRICE",
    "CROSSED_MARKET",
    "ZERO_BID",
    "MISSING_FIELD",
    "DUPLICATE",
    "ABOVE_UPPER_BOUND",
)


@dataclass(frozen=True)
class WorldConfig:
    name: str  # "RW" or "AR"
    seed: int
    n_days: int = 300
    phi: float = 0.5  # AR coefficient (World AR only)
    mu: Tuple[float, float, float] = (0.22, -0.30, 0.40)
    sigma: Tuple[float, float, float] = (0.002, 0.010, 0.020)
    r: float = 0.02
    q: float = 0.01
    spot0: float = 100.0
    spot_vol: float = 0.01
    maturities: Tuple[float, ...] = tuple(d / 365.0 for d in (30, 60, 91, 182, 273, 365))
    strike_step: float = 0.025
    strike_max: float = 0.30
    keep_prob: float = 0.8
    n_offgrid: int = 3
    offgrid_max: float = 0.25
    min_price: float = 0.05
    halfspread_abs: float = 0.005
    halfspread_rel: float = 0.02
    tick: Optional[float] = None  # None = clean quotes (exact mids); 0.01 = noise mode
    defect_prob: float = 0.02

    def __post_init__(self):
        if self.name not in ("RW", "AR"):
            raise ValueError("name must be 'RW' or 'AR'")
        if self.name == "AR" and not (0.0 <= self.phi < 1.0):
            raise ValueError("AR world needs 0 <= phi < 1")


@dataclass(frozen=True)
class Quote:
    record_id: int
    day: int
    mat_idx: int
    T: float
    strike: float
    is_call: bool
    bid: Optional[float]
    ask: Optional[float]
    origin: str = ORIGIN


@dataclass
class DayData:
    day: int
    spot: float
    forwards: Tuple[float, ...]
    quotes: List[Quote]
    ledger: Dict[int, str]  # record_id -> injected defect type (ground truth; validator never sees it)
    injected: Dict[str, int]


@dataclass
class World:
    cfg: WorldConfig
    factors: List[Tuple[float, float, float]]
    spots: List[float]
    days: List[DayData]
    min_true_iv: float
    label: str = "SYNTHETIC - not market data"


def term(T: float) -> float:
    """Fixed term-structure shape g(T) (assumed known to the factor forecaster)."""
    return 0.03 * (math.sqrt(T) - 0.7)


def true_iv(x, k: float, T: float) -> float:
    """Generating IV(k, T) = L + S*k + C*k^2 + g(T)."""
    return x[0] + x[1] * k + x[2] * k * k + term(T)


def _normal(rng: random.Random) -> float:
    u1 = 1.0 - rng.random()  # in (0, 1]
    u2 = rng.random()
    return math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)


def _dynamics(cfg: WorldConfig):
    rng = random.Random(cfg.seed)
    if cfg.name == "AR":
        sd0 = [s / math.sqrt(1.0 - cfg.phi ** 2) for s in cfg.sigma]
        x = [m + s * _normal(rng) for m, s in zip(cfg.mu, sd0)]
    else:
        x = list(cfg.mu)
    spot = cfg.spot0
    factors, spots = [], []
    for _ in range(cfg.n_days):
        factors.append(tuple(x))
        spots.append(spot)
        if cfg.name == "AR":
            x = [m + cfg.phi * (xi - m) + s * _normal(rng) for m, xi, s in zip(cfg.mu, x, cfg.sigma)]
        else:
            x = [xi + s * _normal(rng) for xi, s in zip(x, cfg.sigma)]
        spot = spot * math.exp(-0.5 * cfg.spot_vol ** 2 + cfg.spot_vol * _normal(rng))
    return factors, spots


def _round_tick(value: float, tick: float, up: bool) -> float:
    n = math.ceil(value / tick - 1e-12) if up else math.floor(value / tick + 1e-12)
    return round(n * tick, 12)


def generate_world(cfg: WorldConfig) -> World:
    factors, spots = _dynamics(cfg)
    crng = random.Random(cfg.seed + 1_000_003)
    n_grid = int(round(cfg.strike_max / cfg.strike_step))
    days: List[DayData] = []
    next_id = 0
    min_iv = float("inf")
    for t in range(cfg.n_days):
        x, spot = factors[t], spots[t]
        forwards = tuple(spot * math.exp((cfg.r - cfg.q) * T) for T in cfg.maturities)
        quotes: List[Quote] = []
        for mi, T in enumerate(cfg.maturities):
            F = forwards[mi]
            ks = []
            for j in range(-n_grid, n_grid + 1):
                if crng.random() < cfg.keep_prob:
                    ks.append(round(j * cfg.strike_step, 12))
            for _ in range(cfg.n_offgrid):
                ks.append(cfg.offgrid_max * (2.0 * crng.random() - 1.0))
            for k in sorted(ks):
                iv = true_iv(x, k, T)
                if iv <= 0.02:
                    raise ValueError("generated implausible IV <= 0.02; adjust parameters")
                min_iv = min(min_iv, iv)
                K = F * math.exp(k)
                otm_call = k >= 0.0
                if black76_price(F, K, T, cfg.r, iv, otm_call) < cfg.min_price:
                    continue  # strike not listed
                for is_call in (True, False):
                    mid = black76_price(F, K, T, cfg.r, iv, is_call)
                    h = max(cfg.halfspread_abs, cfg.halfspread_rel * mid)
                    bid, ask = mid - h, mid + h
                    if cfg.tick is not None:
                        bid, ask = _round_tick(bid, cfg.tick, False), _round_tick(ask, cfg.tick, True)
                    quotes.append(Quote(next_id, t, mi, T, K, is_call, bid, ask))
                    next_id += 1
        # ---- defect injection (ground-truth ledger kept separately) ----
        ledger: Dict[int, str] = {}
        injected: Dict[str, int] = {d: 0 for d in DEFECT_TYPES}
        out: List[Quote] = []
        dups: List[Quote] = []
        for qt in quotes:
            if crng.random() >= cfg.defect_prob:
                out.append(qt)
                continue
            F = forwards[qt.mat_idx]
            otm_side = qt.is_call == (math.log(qt.strike / F) >= 0.0)
            kinds = ["NEGATIVE_PRICE", "CROSSED_MARKET", "ZERO_BID", "MISSING_FIELD", "DUPLICATE"]
            if otm_side:
                kinds.append("ABOVE_UPPER_BOUND")
            kind = kinds[min(int(crng.random() * len(kinds)), len(kinds) - 1)]
            injected[kind] += 1
            if kind == "DUPLICATE":
                out.append(qt)
                dup = Quote(next_id, qt.day, qt.mat_idx, qt.T, qt.strike, qt.is_call, qt.bid, qt.ask)
                next_id += 1
                ledger[dup.record_id] = kind
                dups.append(dup)
                continue
            bid, ask = qt.bid, qt.ask
            if kind == "NEGATIVE_PRICE":
                bid = -0.01
            elif kind == "CROSSED_MARKET":
                bid, ask = qt.ask, qt.bid
            elif kind == "ZERO_BID":
                bid = 0.0
            elif kind == "MISSING_FIELD":
                ask = None
            elif kind == "ABOVE_UPPER_BOUND":
                ub = price_bounds(F, qt.strike, qt.T, cfg.r, qt.is_call)[1]
                bid, ask = 1.10 * ub, 1.20 * ub
            ledger[qt.record_id] = kind
            out.append(Quote(qt.record_id, qt.day, qt.mat_idx, qt.T, qt.strike, qt.is_call, bid, ask))
        out.extend(dups)
        days.append(DayData(t, spot, forwards, out, ledger, injected))
    return World(cfg, factors, spots, days, min_iv)


def _f17(x: Optional[float]) -> str:
    return "None" if x is None else format(x, ".17g")


def data_hash(world: World) -> str:
    """SHA-256 over the full synthetic dataset (quotes, ledgers, hidden factors)."""
    h = hashlib.sha256()
    h.update(repr(sorted(world.cfg.__dict__.items())).encode())
    for t, d in enumerate(world.days):
        h.update(("F|%d|%s|%s\n" % (t, ",".join(_f17(v) for v in world.factors[t]), _f17(world.spots[t]))).encode())
        for q in d.quotes:
            h.update(
                ("Q|%d|%d|%d|%s|%d|%s|%s|%s\n" % (q.record_id, q.day, q.mat_idx, _f17(q.strike), q.is_call,
                                                  _f17(q.bid), _f17(q.ask), q.origin)).encode()
            )
        h.update(repr(sorted(d.ledger.items())).encode())
    return h.hexdigest()
