"""Deterministic SYNTHETIC option-chain fixtures with a known generating volatility. NOT market data.
Black-76 prices from a smooth smile; spot/level paths from a seeded generator. Files are named *.synthetic.csv.
  python -m chainpipe.fixtures --out-dir <new dir>      (refuses to overwrite)"""
import argparse
import csv
import io
import math
import random
from datetime import date, datetime, timedelta
from pathlib import Path

from phase0.bsm import black76_price

from .schema import CANONICAL_COLUMNS

RATE, DIV = 0.02, 0.01
EXPIRIES = ("2026-04-17", "2026-05-15", "2026-06-18")
SOURCE = "synthetic-fixture-generator-v1"
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
FILES = {"normal": "chain_normal_snapshot.synthetic.csv", "malformed": "chain_malformed.synthetic.csv", "series": "chain_series12.synthetic.csv"}


def true_iv(k: float, T: float, level: float) -> float:
    """Known generating implied vol at forward log-moneyness k and maturity T (years)."""
    return level + 0.15 * k * k - 0.05 * k + 0.03 * (math.sqrt(T) - 0.3)


def _row(ts, spot, expiry, K, otype, bid, ask, **kw):
    f = lambda x: "" if x is None else ("%.8f" % x if isinstance(x, float) else str(x))
    r = {"quote_timestamp": ts, "underlying_id": "SYN", "underlying_price": "%.6f" % spot, "expiration": expiry, "strike": "%.4f" % K,
         "option_type": otype, "bid": f(bid), "ask": f(ask), "origin": "synthetic", "source": SOURCE}
    r.update(kw)
    return r


def chain_rows(ts, spot, level, expiries, strikes, fwd_spot=None):
    """Quotes for every (expiry, strike) as call and put. fwd_spot builds an expiry whose forward is inconsistent with the stated spot."""
    d0 = datetime.fromisoformat(ts).date()
    rows = []
    for e in expiries:
        T = (date.fromisoformat(e) - d0).days / 365.0
        F = (fwd_spot or spot) * math.exp((RATE - DIV) * T)
        for K in strikes:
            iv = true_iv(math.log(K / F), T, level)
            for otype in ("call", "put"):
                mid = black76_price(F, K, T, RATE, iv, otype == "call")
                h = min(0.5 * mid, 0.02 * mid + 0.005)
                rows.append(_row(ts, spot, e, K, otype, mid - h, mid + h))
    return rows


def normal_rows():
    return chain_rows("2026-03-02T21:00:00+00:00", 100.0, 0.20, EXPIRIES, [85 + 2.5 * i for i in range(13)])


def series_rows(n_days=12):
    rng = random.Random(20260302)
    spot, level, d, rows = 100.0, 0.20, date(2026, 3, 2), []
    for _ in range(n_days):
        while d.weekday() >= 5:
            d += timedelta(days=1)
        rows += chain_rows("%sT21:00:00+00:00" % d.isoformat(), spot, level, EXPIRIES, [90, 95, 100, 105, 110])
        spot *= math.exp(0.01 * rng.gauss(0, 1))
        level = 0.20 + 0.7 * (level - 0.20) + 0.005 * rng.gauss(0, 1)
        d += timedelta(days=1)
    return rows


def malformed_rows():
    """One snapshot with a tagged defect per row. 'fixture_expected' is the terminal disposition the pipeline must assign."""
    ts, spot, e = "2026-03-02T21:00:00+00:00", 100.0, "2026-04-17"
    good = chain_rows(ts, spot, 0.20, ("2026-04-17", "2026-06-18"), [90, 95, 100, 105, 110])
    rows = [dict(r, fixture_expected="OK") for r in good]
    rows += [dict(r, fixture_expected="UNALIGNABLE_EXPIRY") for r in chain_rows(ts, spot, 0.20, ("2026-05-15",), [95, 105])]  # 2 strikes: forward not inferable
    rows += [dict(r, fixture_expected="FORWARD_IMPLAUSIBLE") for r in chain_rows(ts, spot, 0.20, ("2026-07-17",), [140, 150, 160], fwd_spot=150.0)]  # forward ~150 vs spot 100
    dup = [r for r in good if r["expiration"] == e and r["strike"] == "100.0000" and r["option_type"] == "call"][0]
    tag = lambda t, r: dict(r, fixture_expected=t)
    rows += [
        tag("NEGATIVE_PRICE", _row(ts, spot, e, 92.5, "put", -0.10, 0.20)),
        tag("CROSSED_MARKET", _row(ts, spot, e, 107.5, "call", 1.50, 1.00)),
        tag("ZERO_BID", _row(ts, spot, e, 87.5, "put", 0.0, 0.05)),
        tag("MISSING_FIELD", _row(ts, spot, e, 112.5, "call", 0.10, None)),
        tag("DUPLICATE", dict(dup)),
        tag("BAD_OPTION_TYPE", _row(ts, spot, e, 100.0, "straddle", 1.0, 1.1)),
        tag("BAD_STRIKE", _row(ts, spot, e, 0.0, "call", 1.0, 1.1)),
        tag("BAD_STRIKE", dict(_row(ts, spot, e, 100.0, "call", 1.0, 1.1), strike="abc")),
        tag("BAD_EXPIRY", _row(ts, spot, "2026-03-01", 100.0, "call", 1.0, 1.1)),
        tag("BAD_EXPIRY", _row(ts, spot, "2026-13-45", 100.0, "call", 1.0, 1.1)),
        tag("BAD_TIMESTAMP", dict(_row(ts, spot, e, 100.0, "call", 1.0, 1.1), quote_timestamp="2026-03-02 21:00:00")),
        tag("BAD_UNDERLYING", dict(_row(ts, spot, e, 100.0, "call", 1.0, 1.1), underlying_price="0")),
        tag("BAD_PRICE_FIELD", dict(_row(ts, spot, e, 100.0, "call", 1.0, 1.1), bid="abc")),
        tag("INCONSISTENT_UNDERLYING", _row(ts, 103.0, e, 82.5, "put", 0.05, 0.10)),
        tag("BAD_ORIGIN", dict(_row(ts, spot, e, 100.0, "call", 1.0, 1.1), origin="unknown")),
        tag("SOLVER_PRICE_ABOVE_UPPER_BOUND", _row(ts, spot, e, 115.0, "call", 99.95, 100.05)),
        tag("SOLVER_NO_BRACKET", _row(ts, spot, e, 117.5, "call", 94.90, 95.10)),
    ]
    return rows


def to_csv(rows) -> str:
    cols = list(CANONICAL_COLUMNS) + (["fixture_expected"] if any("fixture_expected" in r for r in rows) else [])
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def generate() -> dict:
    return {FILES["normal"]: to_csv(normal_rows()), FILES["malformed"]: to_csv(malformed_rows()), FILES["series"]: to_csv(series_rows())}


def main(argv=None):
    ap = argparse.ArgumentParser(description="write the SYNTHETIC chain fixtures to a new directory")
    ap.add_argument("--out-dir", required=True)
    out = Path(ap.parse_args(argv).out_dir)
    if out.exists():
        raise SystemExit("refusing to overwrite existing path: %s" % out)
    out.mkdir(parents=True)
    for name, text in generate().items():
        (out / name).write_text(text, encoding="utf-8", newline="")
        print("wrote", out / name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
