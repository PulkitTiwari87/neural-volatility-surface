"""Canonical option-chain schema, provider interface and CSV provider.

Every data row of an input ends with exactly one disposition: parsed into a ChainQuote or reported as a RowError.
Precedence of schema checks (first failure wins): timestamp, underlying, strike, expiry, option type, origin, price fields.
Bid/ask that are empty or 'nan' become None here and are rejected later by phase0 validation as MISSING_FIELD."""
import csv
import hashlib
import io
import json
import math
from dataclasses import dataclass
from datetime import date, datetime, timezone
from enum import Enum
from pathlib import Path
from typing import List, Optional, Protocol, Tuple

CANONICAL_COLUMNS = ("quote_timestamp", "underlying_id", "underlying_price", "expiration", "strike", "option_type",
                     "bid", "ask", "origin", "source")
ORIGINS = ("synthetic", "provider")


class SchemaReason(str, Enum):
    BAD_TIMESTAMP = "BAD_TIMESTAMP"
    BAD_UNDERLYING = "BAD_UNDERLYING"
    BAD_STRIKE = "BAD_STRIKE"
    BAD_EXPIRY = "BAD_EXPIRY"
    BAD_OPTION_TYPE = "BAD_OPTION_TYPE"
    BAD_ORIGIN = "BAD_ORIGIN"
    BAD_PRICE_FIELD = "BAD_PRICE_FIELD"


class ChainSchemaError(Exception):
    """File-level problem (missing required column, undecodable file): fail fast, nothing is parsed."""


@dataclass(frozen=True)
class ChainQuote:
    row: int  # 1-based data-row number in the source (record identity)
    quote_ts: datetime  # timezone-aware, UTC
    underlying_id: str
    underlying_price: float
    expiration: date
    strike: float
    option_type: str  # "call" | "put"
    bid: Optional[float]
    ask: Optional[float]
    origin: str
    source: str


@dataclass(frozen=True)
class RowError:
    row: int
    code: str
    detail: str


@dataclass(frozen=True)
class ChainSnapshot:
    underlying_id: str
    quote_ts: datetime
    quotes: Tuple[ChainQuote, ...]


@dataclass
class ChainRead:
    snapshots: List[ChainSnapshot]
    row_errors: List[RowError]
    n_rows: int
    columns: Tuple[str, ...]
    extra_columns: Tuple[str, ...]
    sha256: str
    name: str
    chronological_in_input: bool


class ChainProvider(Protocol):
    """The only contract a data source must meet. Real provider adapters (not written: provider undecided) implement read()."""

    def read(self) -> ChainRead: ...


def _num(s) -> Optional[float]:
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _price(raw):
    """(ok, value): empty / nan / none / null -> (True, None); unparseable -> (False, None)."""
    s = ("" if raw is None else str(raw)).strip()
    if s.lower() in ("", "nan", "none", "null"):
        return True, None
    v = _num(s)
    return (v is not None), v


def parse_row(row_no: int, rec: dict):
    def err(code: SchemaReason, detail: str) -> RowError:
        return RowError(row_no, code.value, detail)

    try:
        ts = datetime.fromisoformat(str(rec.get("quote_timestamp") or "").strip().replace("Z", "+00:00"))
    except ValueError:
        return err(SchemaReason.BAD_TIMESTAMP, "not ISO-8601")
    if ts.tzinfo is None:
        return err(SchemaReason.BAD_TIMESTAMP, "timezone required")
    ts = ts.astimezone(timezone.utc)
    uid, up = str(rec.get("underlying_id") or "").strip(), _num(rec.get("underlying_price"))
    if not uid or up is None or up <= 0.0:
        return err(SchemaReason.BAD_UNDERLYING, "underlying_id empty or underlying_price not a positive finite number")
    strike = _num(rec.get("strike"))
    if strike is None or strike <= 0.0:
        return err(SchemaReason.BAD_STRIKE, "strike not a positive finite number")
    try:
        exp = date.fromisoformat(str(rec.get("expiration") or "").strip())
    except ValueError:
        return err(SchemaReason.BAD_EXPIRY, "not a YYYY-MM-DD date")
    if exp <= ts.date():
        return err(SchemaReason.BAD_EXPIRY, "expired or expires on the quote date (T <= 0)")
    ot = str(rec.get("option_type") or "").strip().lower()
    ot = {"call": "call", "c": "call", "put": "put", "p": "put"}.get(ot)
    if ot is None:
        return err(SchemaReason.BAD_OPTION_TYPE, "option_type must be call/put (or c/p)")
    origin = str(rec.get("origin") or "").strip().lower()
    if origin not in ORIGINS:
        return err(SchemaReason.BAD_ORIGIN, "origin must be one of %s" % (ORIGINS,))
    ok_b, bid = _price(rec.get("bid"))
    ok_a, ask = _price(rec.get("ask"))
    if not (ok_b and ok_a):
        return err(SchemaReason.BAD_PRICE_FIELD, "bid/ask present but not numeric")
    return ChainQuote(row_no, ts, uid, up, exp, strike, ot, bid, ask, origin, str(rec.get("source") or "").strip() or "unknown")


def read_rows(rows, name: str, sha256: str, columns) -> ChainRead:
    """Parse an iterable of dict records (the CSV path and in-memory providers share this)."""
    columns = tuple(columns)
    missing = [c for c in CANONICAL_COLUMNS if c not in columns]
    if missing:
        raise ChainSchemaError("missing required column(s): %s" % missing)
    quotes, errors, n = [], [], 0
    for n, rec in enumerate(rows, start=1):
        r = parse_row(n, rec)
        (errors if isinstance(r, RowError) else quotes).append(r)
    groups = {}
    for q in quotes:
        groups.setdefault((q.quote_ts, q.underlying_id), []).append(q)
    snaps = [ChainSnapshot(uid, ts, tuple(g)) for (ts, uid), g in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1]))]
    order = [(q.underlying_id, q.quote_ts) for q in quotes]
    chrono = all(b[1] >= a[1] for a, b in zip(order, order[1:]) if a[0] == b[0])
    extra = tuple(c for c in columns if c not in CANONICAL_COLUMNS)
    return ChainRead(snaps, errors, n, columns, extra, sha256, name, chrono)


class CsvChainProvider:
    """Canonical CSV (header required; extra columns ignored and recorded). Reads a local file only."""

    def __init__(self, path):
        self.path = Path(path)

    def read(self) -> ChainRead:
        raw = self.path.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as e:
            raise ChainSchemaError("input is not valid UTF-8: %s" % e)
        rd = csv.DictReader(io.StringIO(text, newline=""))
        return read_rows(list(rd), self.path.name, hashlib.sha256(raw).hexdigest(), rd.fieldnames or ())


class ListChainProvider:
    """In-memory provider (tests, notebooks); proves the interface is not tied to files."""

    def __init__(self, rows, name="in-memory"):
        self.rows, self.name = list(rows), name

    def read(self) -> ChainRead:
        blob = json.dumps(self.rows, sort_keys=True, default=str).encode()
        return read_rows(self.rows, self.name, hashlib.sha256(blob).hexdigest(), tuple(self.rows[0].keys()) if self.rows else CANONICAL_COLUMNS)
