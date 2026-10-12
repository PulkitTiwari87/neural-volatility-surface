"""Quote validation, parity-forward inference and OTM selection. SYNTHETIC SPIKE.

Every input record receives exactly one disposition with a reason code; nothing
is dropped silently (GR-DATA-02/03). `ingested == retained + excluded` always.
"""
import math
import statistics
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from .synth import Quote


class Reason(str, Enum):
    RETAINED = "RETAINED"
    MISSING_FIELD = "MISSING_FIELD"
    NEGATIVE_PRICE = "NEGATIVE_PRICE"
    CROSSED_MARKET = "CROSSED_MARKET"
    ZERO_BID = "ZERO_BID"
    DUPLICATE = "DUPLICATE"


@dataclass(frozen=True)
class QualityPolicy:
    """Spike policy; thresholds for real data are TBD(Phase 1)."""

    exclude_zero_bid: bool = True


@dataclass
class ValidationReport:
    ingested: int
    retained: int
    excluded: int
    counts: Dict[str, int]
    dispositions: Dict[int, Reason] = field(repr=False, default_factory=dict)

    @property
    def conserved(self) -> bool:
        return self.ingested == self.retained + self.excluded == sum(self.counts.values())


def _finite(x) -> bool:
    return isinstance(x, (int, float)) and math.isfinite(x)


def validate_day(quotes: List[Quote], policy: QualityPolicy = QualityPolicy()):
    """Return (retained_quotes, ValidationReport). Precedence: missing > negative > crossed > zero-bid > duplicate."""
    seen = set()
    retained: List[Quote] = []
    counts = {r.value: 0 for r in Reason}
    disp: Dict[int, Reason] = {}
    for q in quotes:
        if not (_finite(q.bid) and _finite(q.ask)):
            reason = Reason.MISSING_FIELD
        elif q.bid < 0.0 or q.ask < 0.0:
            reason = Reason.NEGATIVE_PRICE
        elif q.bid > q.ask:
            reason = Reason.CROSSED_MARKET
        elif policy.exclude_zero_bid and q.bid == 0.0:
            reason = Reason.ZERO_BID
        elif (q.mat_idx, q.strike, q.is_call) in seen:
            reason = Reason.DUPLICATE
        else:
            reason = Reason.RETAINED
        if reason is Reason.RETAINED:
            seen.add((q.mat_idx, q.strike, q.is_call))
            retained.append(q)
        counts[reason.value] += 1
        disp[q.record_id] = reason
    n = len(quotes)
    return retained, ValidationReport(n, len(retained), n - len(retained), counts, disp)


def mid(q: Quote) -> float:
    return 0.5 * (q.bid + q.ask)


def infer_forward(quotes_one_expiry: List[Quote], T: float, r: float) -> Optional[float]:
    """Forward from put-call parity C - P = exp(-rT)(F - K): median over the 3 strikes with smallest |C-P|.

    Returns None (expiry 'unalignable') if fewer than 3 strikes have both a call and a put.
    """
    by_strike: Dict[float, Dict[bool, float]] = {}
    for q in quotes_one_expiry:
        by_strike.setdefault(q.strike, {})[q.is_call] = mid(q)
    pairs = [(K, sides[True] - sides[False]) for K, sides in by_strike.items() if True in sides and False in sides]
    if len(pairs) < 3:
        return None
    pairs.sort(key=lambda p: (abs(p[1]), p[0]))
    est = [K + math.exp(r * T) * diff for K, diff in pairs[:3]]
    return statistics.median(est)


def select_otm(quotes_one_expiry: List[Quote], F_hat: float) -> List[Quote]:
    """OTM side only: call if ln(K/F_hat) >= -1e-9, else put (price = bid/ask midpoint)."""
    out = []
    for q in quotes_one_expiry:
        call_side = math.log(q.strike / F_hat) >= -1e-9
        if q.is_call == call_side:
            out.append(q)
    return out
