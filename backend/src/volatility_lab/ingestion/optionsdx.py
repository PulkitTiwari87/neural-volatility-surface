"""Adapter for OptionsDX-style wide option-chain files (one row = one strike/expiry, call and put side by side).

Reads parquet or CSV in column-pruned batches (the full file is never held in memory) and returns a
compact numeric frame plus a *conserved* reject ledger: ``rows_in == rows_kept + sum(rejects)``.

Nothing here downloads data. ``discover_files`` only lists files that a hosted-data client (Kaggle in
the notebook) has already placed in runtime-local storage.
"""
from __future__ import annotations

import hashlib
import re
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

import numpy as np
import pandas as pd

from volatility_lab.config.settings import DataConfig

REQUIRED = ("quote_date", "expire_date", "strike", "underlying_last", "c_bid", "c_ask", "p_bid", "p_ask")
OPTIONAL = ("c_iv", "p_iv")
NUMERIC = ("strike", "underlying_last", "c_bid", "c_ask", "p_bid", "p_ask", "c_iv", "p_iv")

# Order matters: a row gets the *first* reason that applies (this is what makes the ledger conserve).
PREFILTER_REASONS = ("bad_quote_date", "bad_expiry", "bad_strike_or_spot", "dte_out_of_range",
                     "strike_far_from_spot", "no_usable_side")


# Applied after all batches are concatenated (a contract is identified by date, expiry, strike).
DUPLICATE_REASONS = ("duplicate_row_exact", "conflicting_duplicate_key")
CONTRACT_KEY = ["date", "expiry", "strike"]


class SchemaError(ValueError):
    """The file does not contain the columns the adapter needs."""


def normalize_name(name: str) -> str:
    return str(name).strip().strip("[]").strip().lower()


class RejectLedger:
    """Counts rows by terminal disposition; ``check()`` asserts conservation."""

    def __init__(self) -> None:
        self.rows_in = 0
        self.kept = 0
        self.rejects: Counter = Counter()
        # per snapshot (quote date, int days since epoch; the NaT sentinel is the "unknown date" bucket):
        # {"rows_in", "kept", <reason>: n}. Phase 1 A2: conservation must hold for every snapshot, not only globally.
        self.by_date: Dict[int, Counter] = {}

    def reject(self, reason: str, n: int) -> None:
        if n:
            self.rejects[reason] += int(n)

    def note_dates(self, dates, terminal, reasons: Sequence[str]) -> None:
        """Record each row's terminal disposition per snapshot: ``terminal`` is 0 (kept) or a 1-based index into ``reasons``."""
        counts = pd.DataFrame({"d": np.asarray(dates), "t": np.asarray(terminal)}).groupby(["d", "t"]).size()
        for (d, t), n in counts.items():
            c = self.by_date.setdefault(int(d), Counter())
            c["rows_in"] += int(n)
            c["kept" if t == 0 else reasons[int(t) - 1]] += int(n)

    def move_kept_to_reject(self, dates, reason: str) -> None:
        """Rows already counted as kept on these snapshots are rejected for ``reason`` (the global counters are the caller's)."""
        for d, n in pd.Series(np.asarray(dates)).value_counts().items():
            c = self.by_date[int(d)]
            c["kept"] -= int(n)
            c[reason] += int(n)

    def check_by_date(self) -> None:
        for d, c in self.by_date.items():
            rest = sum(v for k, v in c.items() if k not in ("rows_in", "kept"))
            if c["rows_in"] != c["kept"] + rest or c["kept"] < 0:
                raise AssertionError(f"ledger not conserved on snapshot {self._label(d)}: {dict(c)}")
        if (sum(c["rows_in"] for c in self.by_date.values()) != self.rows_in
                or sum(c["kept"] for c in self.by_date.values()) != self.kept):
            raise AssertionError("per-snapshot ledger does not add up to the global ledger")

    @staticmethod
    def _label(d: int) -> str:
        return "unknown_date" if d == np.iinfo("int64").min else str(np.datetime64(int(d), "D"))

    def by_date_report(self) -> dict:
        """JSON-safe per-snapshot ledger: ``{date: {"rows_in", "kept", "rejects": {reason: n}}}`` (sorted)."""
        self.check_by_date()
        return {self._label(d): {"rows_in": c["rows_in"], "kept": c["kept"],
                                 "rejects": {k: v for k, v in sorted(c.items()) if k not in ("rows_in", "kept") and v}}
                for d, c in sorted(self.by_date.items())}

    def check(self) -> None:
        total = self.kept + sum(self.rejects.values())
        if total != self.rows_in:
            raise AssertionError(f"ledger not conserved: in={self.rows_in} kept+rejected={total}")
        if self.by_date:
            self.check_by_date()

    def to_dict(self) -> dict:
        self.check()
        return {"rows_in": self.rows_in, "kept": self.kept, "rejects": dict(self.rejects)}


def discover_files(root) -> List[Path]:
    root = Path(root)
    files = sorted(root.rglob("*.parquet")) or sorted(root.rglob("*.csv"))
    if not files:
        raise FileNotFoundError(f"no .parquet or .csv files under {root}")
    return files


def fingerprint_files(paths: Sequence[Path]) -> dict:
    """Name, size and SHA-256 of every file (streamed). Identifies *which bytes* an experiment used."""
    out = []
    for p in paths:
        h = hashlib.sha256()
        with open(p, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 22), b""):
                h.update(chunk)
        out.append({"file": p.name, "bytes": p.stat().st_size, "sha256": h.hexdigest()})
    return {"files": out, "combined_sha256": hashlib.sha256("".join(f["sha256"] for f in out).encode()).hexdigest()}


_ISO_DATE = re.compile(r"^(\d{4}-\d{2}-\d{2})(?:[T ].*)?$")


def _to_date_days(col: pd.Series) -> np.ndarray:
    """Parse a date column (datetime or padded strings) to int days since epoch; NaT -> min int64.

    A quote/expiry date is a *calendar date of the trading venue*, so the date as written is kept: a time or UTC
    offset is ignored, never converted (an evening quote at -05:00 must not become the next UTC day). Strings must
    start with an ISO ``YYYY-MM-DD``; anything else (``01/02/2020`` is month-first or day-first?) is NaT and is
    rejected as a bad date instead of being guessed by ``dateutil``.
    """
    if pd.api.types.is_datetime64_any_dtype(col):
        parsed = pd.to_datetime(col, errors="coerce")
        if parsed.dt.tz is not None:
            parsed = parsed.dt.tz_localize(None)  # wall-clock date as written; ``.values`` would convert to UTC
    else:
        text = col.astype(str).str.strip()
        uniq = pd.Series(text.unique())
        iso = uniq.str.extract(_ISO_DATE)[0]
        mapping = dict(zip(uniq, pd.to_datetime(iso, format="%Y-%m-%d", errors="coerce")))
        parsed = text.map(mapping)
    return parsed.values.astype("datetime64[D]").astype("int64")  # NaT -> iinfo.min


def prefilter_batch(df: pd.DataFrame, cfg: DataConfig, ledger: RejectLedger) -> pd.DataFrame:
    """Normalise one raw batch and drop rows that cannot be used, recording why."""
    df = df.rename(columns={c: normalize_name(c) for c in df.columns})
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise SchemaError(f"missing required columns: {missing}; have: {sorted(df.columns)}")
    n = len(df)
    ledger.rows_in += n
    num = {c: pd.to_numeric(df[c], errors="coerce").to_numpy(dtype=float) if c in df.columns
           else np.full(n, np.nan) for c in NUMERIC}
    d = _to_date_days(df["quote_date"])
    e = _to_date_days(df["expire_date"])
    nat = np.iinfo("int64").min
    dte = e - d
    strike, spot = num["strike"], num["underlying_last"]
    with np.errstate(invalid="ignore", divide="ignore"):
        pos = np.isfinite(strike) & np.isfinite(spot) & (strike > 0) & (spot > 0)
        far = np.abs(np.log(strike / spot)) > cfg.max_abs_log_strike
        c_ok = (num["c_bid"] > 0) & (num["c_ask"] > 0)
        p_ok = (num["p_bid"] > 0) & (num["p_ask"] > 0)
    conditions = [d == nat, e == nat, ~pos, (dte < cfg.min_dte) | (dte > cfg.max_dte), far, ~(c_ok | p_ok)]
    first = np.select(conditions, np.arange(1, len(conditions) + 1), default=0)
    for i, reason in enumerate(PREFILTER_REASONS, start=1):
        ledger.reject(reason, int((first == i).sum()))
    ledger.note_dates(d, first, PREFILTER_REASONS)
    keep = first == 0
    ledger.kept += int(keep.sum())
    out = pd.DataFrame({"date": d[keep].astype(np.int32), "expiry": e[keep].astype(np.int32)})
    for c in ("strike", "underlying_last", "c_bid", "c_ask", "p_bid", "p_ask"):
        out[c] = num[c][keep]
    for c in OPTIONAL:
        out[c] = num[c][keep].astype(np.float32)
    return out.rename(columns={"underlying_last": "spot"})


def _iter_raw_batches(path: Path, batch_rows: int) -> Iterable[pd.DataFrame]:
    want = set(REQUIRED) | set(OPTIONAL)
    if path.suffix == ".parquet":
        import pyarrow.parquet as pq
        pf = pq.ParquetFile(path)
        cols = [n for n in pf.schema_arrow.names if normalize_name(n) in want]
        for batch in pf.iter_batches(batch_size=batch_rows, columns=cols):
            yield batch.to_pandas()
    else:
        for chunk in pd.read_csv(path, chunksize=batch_rows, usecols=lambda c: normalize_name(c) in want,
                                 dtype=str, skipinitialspace=True):
            yield chunk


def load_wide(paths: Sequence[Path], cfg: DataConfig, *, max_rows: Optional[int] = None):
    """Stream all files, returning ``(wide_frame, ledger)``. ``max_rows`` is for smoke tests only."""
    ledger = RejectLedger()
    parts = []
    seen = 0
    for p in paths:
        for raw in _iter_raw_batches(Path(p), cfg.batch_rows):
            if max_rows is not None and seen >= max_rows:
                break
            if max_rows is not None:
                raw = raw.iloc[: max_rows - seen]
            seen += len(raw)
            parts.append(prefilter_batch(raw, cfg, ledger))
    if not parts:
        raise SchemaError("no rows were read")
    wide = drop_duplicates_with_ledger(pd.concat(parts, ignore_index=True), ledger)
    ledger.check()
    return wide, ledger


def drop_duplicates_with_ledger(wide: pd.DataFrame, ledger: RejectLedger) -> pd.DataFrame:
    """Remove repeated contract rows, recording why (rows previously counted as kept move to rejects).

    * a row identical in every field to an earlier row is dropped (``duplicate_row_exact``; the first is kept);
    * rows sharing (date, expiry, strike) but differing in any quote are *all* dropped
      (``conflicting_duplicate_key``): which of them is right cannot be known, and keeping one would be arbitrary.
    """
    exact = wide.duplicated(keep="first").to_numpy()
    ledger.move_kept_to_reject(wide["date"].to_numpy()[exact], "duplicate_row_exact")
    wide = wide[~exact]
    conflict = wide.duplicated(CONTRACT_KEY, keep=False).to_numpy()
    ledger.move_kept_to_reject(wide["date"].to_numpy()[conflict], "conflicting_duplicate_key")
    wide = wide[~conflict]
    n_exact, n_conflict = int(exact.sum()), int(conflict.sum())
    ledger.kept -= n_exact + n_conflict
    ledger.reject("duplicate_row_exact", n_exact)
    ledger.reject("conflicting_duplicate_key", n_conflict)
    return wide.reset_index(drop=True)
