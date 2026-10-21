"""Contract-level quote persistence (Q-D5; design and owner answers D1-D11 in STORAGE_DESIGN 8.8). SYNTHETIC ONLY.

The owner's go-ahead (2026-10-21) covers synthetic data verified in Colab; ``build_quote_set`` therefore refuses any
origin other than ``"synthetic"`` and any input file not named ``*.synthetic.*``. Real data needs a new decision.

Layout (sidecar beside ``datasets/``, never under the API runs root, D2)::

    <root>/quotes/<quote_set_id>/rows/<YYYY-MM-DD>.parquet   one partition per quote date (D1, provisional: DEC-009)
    <root>/quotes/<quote_set_id>/slice_forward.parquet       F, DF, n_pairs, regression, fstat, T per (date, expiry)
    <root>/quotes/<quote_set_id>/manifest.json               written last
    <root>/quotes/<quote_set_id>/purge.json                  only after ``purge_quote_set`` (D3)

* Additive: the dataset ``<root>/datasets/<version_id>`` must already exist (``raw_store.ingest``) and is only read;
  its panel is rebuilt here and must reproduce the stored ``panel_sha256``. ``Config``, ``Prepared``, ``run_key``
  and archived runs are untouched.
* ``quote_set_id`` = sha256(dataset version id, ``QuotePolicy`` hash, schema, code version) (D4). An existing set is
  re-checked, never rewritten: source columns must match exactly, derived floats within ``rebuild_rel_tol``.
* One row per (quote date, expiry, strike, option type) for every contract that reaches the quote stage, both sides
  (D6), plus ``no_usable_side`` pre-filter rejects (D5); every excluded row carries its reason.
* Columns F, DF, T, k, iv, otm_selected and disposition of a *target-day* row are scoring-side quantities and must
  never feed origin-day features (STORAGE_DESIGN 8.7; LT-4/LT-5). Nothing in the package reads this store yet (Q-D2).
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

from volatility_lab.config.settings import Config, QuotePolicy
from volatility_lab.ingestion.optionsdx import load_wide
from volatility_lab.pricing import bs
from volatility_lab.storage.raw_store import OverwriteError, RawStore, dataset_version_id, panel_sha256
from volatility_lab.surfaces.grid import build_surface_panel
from volatility_lab.validation.quotes import QUOTE_REASONS, build_otm_quotes, estimate_forwards

EXERCISE_STYLES = ("american", "european")
DATA_MODE = "end-of-day snapshot; backtest only, not live (DATA-003)"
SOURCE_COLUMNS = ("contract_id", "quote_date", "expiry", "strike", "option_type", "bid", "ask", "spot")
DERIVED_FLOATS = ("mid", "F", "DF", "T", "k", "iv", "reprice_err", "vendor_iv", "rel_spread")
EXACT_COLUMNS = ("underlying", "settlement", "snapshot_kind", "quote_time_local", "tz", "solver_status",
                 "otm_selected", "disposition", "reason")
DATE_COLUMNS = ("quote_date", "expiry")
STRING_COLUMNS = ("contract_id", "underlying", "option_type", "settlement", "snapshot_kind", "quote_time_local", "tz",
                  "solver_status", "disposition", "reason")
COLUMNS = ("contract_id", "underlying", "expiry", "strike", "option_type", "settlement", "quote_date", "snapshot_kind",
           "quote_time_local", "tz", "bid", "ask", "mid", "spot", "F", "DF", "T", "k", "iv", "solver_status",
           "reprice_err", "vendor_iv", "otm_selected", "rel_spread", "disposition", "reason")
_CODE_FILES = ("ingestion/optionsdx.py", "validation/quotes.py", "pricing/bs.py", "storage/quote_store.py")


def code_version() -> str:
    """sha256 of the source files that produce quote rows, line endings normalised (Windows and Linux agree)."""
    pkg = Path(__file__).resolve().parents[1]
    h = hashlib.sha256()
    for rel in _CODE_FILES:
        h.update(rel.encode() + b"\0" + (pkg / rel).read_bytes().replace(b"\r\n", b"\n") + b"\0")
    return h.hexdigest()


def quote_set_id(dataset_version: str, policy: QuotePolicy) -> str:
    blob = {"dataset_version_id": dataset_version, "policy_sha256": policy.sha256(), "schema": policy.schema,
            "code_version": code_version()}
    return hashlib.sha256(json.dumps(blob, sort_keys=True).encode()).hexdigest()


def contract_ids(underlying: str, expiry_days, strike, option_type) -> np.ndarray:
    """sha256 of ``underlying|expiry_iso|strike_decimal|C/P``; the strike is the shortest round-trip decimal string,
    so the same contract has the same id on every day and on every platform."""
    keys = pd.DataFrame({"e": np.asarray(expiry_days, dtype=np.int64), "s": np.asarray(strike, dtype=float),
                         "t": np.asarray(option_type)})
    uniq = keys.drop_duplicates()
    text = [f"{underlying}|{np.datetime64(int(e), 'D')}|{np.format_float_positional(s, trim='-')}|{t}"
            for e, s, t in uniq.itertuples(index=False)]
    ids = uniq.assign(id=[hashlib.sha256(x.encode()).hexdigest() for x in text])
    return keys.merge(ids, on=["e", "s", "t"], how="left")["id"].to_numpy(dtype=object)


def _status_names(codes: np.ndarray) -> np.ndarray:
    names = {**bs.STATUS_NAMES, -1: "not_attempted"}
    return np.array([names[int(c)] for c in codes], dtype=object)


def _nullable(a) -> np.ndarray:
    """Non-finite floats are stored as null (``None``), never as NaN or inf."""
    a = np.asarray(a, dtype=float)
    out = a.astype(object)
    out[~np.isfinite(a)] = None
    return out


def quote_rows(rows: pd.DataFrame, unusable: pd.DataFrame, underlying: str) -> pd.DataFrame:
    """Long-format ``quote_row`` table (STORAGE_DESIGN 8.2): both sides of every quote-stage row plus the
    ``no_usable_side`` rows, sorted by (quote_date, expiry, strike, option_type)."""
    parts = []
    for side, is_call in (("C", True), ("P", False)):
        x = side.lower()
        selected = rows["otm_is_call"].to_numpy() == is_call
        bid, ask = rows[f"{x}_bid"].to_numpy(dtype=float), rows[f"{x}_ask"].to_numpy(dtype=float)
        reason = rows["reason"].to_numpy(dtype=object)
        with np.errstate(invalid="ignore", divide="ignore"):
            own_mid = 0.5 * (bid + ask)
        parts.append(pd.DataFrame({
            "quote_date": rows["date"].to_numpy(dtype=np.int32), "expiry": rows["expiry"].to_numpy(dtype=np.int32),
            "strike": rows["strike"].to_numpy(dtype=float), "option_type": side, "bid": bid, "ask": ask,
            "mid": np.where(selected, rows["mid"].to_numpy(dtype=float), own_mid),
            "spot": rows["spot"].to_numpy(dtype=float), "F": rows["F"].to_numpy(dtype=float),
            "DF": rows["DF"].to_numpy(dtype=float), "T": rows["T"].to_numpy(dtype=float),
            "k": rows["k"].to_numpy(dtype=float),
            "iv": np.where(selected, rows["iv"].to_numpy(dtype=float), np.nan),
            "solver_status": np.where(selected, _status_names(rows["solver_status"].to_numpy()), "not_attempted"),
            "reprice_err": np.where(selected, rows["reprice_err"].to_numpy(dtype=float), np.nan),
            "vendor_iv": rows[f"{x}_iv"].to_numpy(dtype=float),
            "otm_selected": selected,
            "rel_spread": np.where(selected, rows["rel_spread"].to_numpy(dtype=float), np.nan),
            "disposition": np.where(selected, np.where(pd.isna(reason), "retained", "excluded"), "not_selected"),
            "reason": np.where(selected, reason, None),
        }))
        u = unusable
        with np.errstate(invalid="ignore", divide="ignore"):
            u_mid = 0.5 * (u[f"{x}_bid"].to_numpy(dtype=float) + u[f"{x}_ask"].to_numpy(dtype=float))
        nan = np.full(len(u), np.nan)
        parts.append(pd.DataFrame({
            "quote_date": u["date"].to_numpy(dtype=np.int32), "expiry": u["expiry"].to_numpy(dtype=np.int32),
            "strike": u["strike"].to_numpy(dtype=float), "option_type": side,
            "bid": u[f"{x}_bid"].to_numpy(dtype=float), "ask": u[f"{x}_ask"].to_numpy(dtype=float), "mid": u_mid,
            "spot": u["spot"].to_numpy(dtype=float), "F": nan, "DF": nan,
            "T": (u["expiry"].to_numpy(dtype=float) - u["date"].to_numpy(dtype=float)) / 365.0, "k": nan, "iv": nan,
            "solver_status": "not_attempted", "reprice_err": nan, "vendor_iv": nan, "otm_selected": False,
            "rel_spread": nan, "disposition": "excluded", "reason": "no_usable_side",
        }))
    t = pd.concat(parts, ignore_index=True)
    t["contract_id"] = contract_ids(underlying, t["expiry"], t["strike"], t["option_type"])
    t["underlying"] = underlying
    t["settlement"] = None          # AM/PM unknown for this source (D8); never assumed
    t["snapshot_kind"] = "eod_close"
    t["quote_time_local"] = None    # end-of-day source gives no time (D7); never filled by assumption
    t["tz"] = None
    t = t.sort_values(["quote_date", "expiry", "strike", "option_type"], kind="mergesort").reset_index(drop=True)
    for c in DERIVED_FLOATS:
        t[c] = _nullable(t[c])
    t["reason"] = t["reason"].where(pd.notna(t["reason"]), None)
    return t[list(COLUMNS)]


def source_content_sha256(t: pd.DataFrame) -> str:
    """Logical hash of the source columns only (fixed little-endian dtypes; derived floats excluded, D4)."""
    h = hashlib.sha256()
    for c in SOURCE_COLUMNS:
        col = t[c]
        if c in DATE_COLUMNS:
            b = col.to_numpy(dtype="<i4").tobytes()
        elif c in ("strike", "bid", "ask", "spot"):
            a = col.to_numpy(dtype="<f8")
            b = np.where(np.isfinite(a), a, np.nan).astype("<f8").tobytes()
        else:
            b = "\n".join("" if v is None else str(v) for v in col).encode()
        h.update(c.encode() + b"\0" + b + b"\0")
    return h.hexdigest()


def _dedupe_unusable(unusable: pd.DataFrame, wide: pd.DataFrame):
    """Unusable rows keyed like the wide frame: exact copies collapse, conflicting keys and keys that also have a
    usable row are dropped (counted, so the ``no_usable_side`` ledger still reconciles)."""
    key = ["date", "expiry", "strike"]
    exact = unusable.duplicated(keep="first").to_numpy()
    u = unusable[~exact]
    conflict = u.duplicated(key, keep=False).to_numpy()
    u = u[~conflict]
    in_wide = u.set_index(key).index.isin(wide.set_index(key).index)
    return u[~in_wide].reset_index(drop=True), int(exact.sum()), int(conflict.sum() + in_wide.sum())


def _to_arrow(t: pd.DataFrame):
    import pyarrow as pa  # noqa: PLC0415  (pyarrow is already imported by ingestion for Parquet input)
    arrays, fields = [], []
    for c in COLUMNS:
        if c in DATE_COLUMNS:
            arr = pa.array(t[c].to_numpy(dtype=np.int32), type=pa.int32()).cast(pa.date32())
        elif c in STRING_COLUMNS:
            arr = pa.array(list(t[c]), type=pa.string())
        elif c == "otm_selected":
            arr = pa.array(t[c].to_numpy(dtype=bool), type=pa.bool_())
        else:
            arr = pa.array(list(t[c]) if t[c].dtype == object else t[c].to_numpy(dtype=float), type=pa.float64())
        arrays.append(arr)
        fields.append(pa.field(c, arr.type))
    return pa.Table.from_arrays(arrays, schema=pa.schema(fields))


def _read_parquet(path: Path) -> pd.DataFrame:
    import pyarrow as pa  # noqa: PLC0415
    import pyarrow.parquet as pq  # noqa: PLC0415
    tab = pq.read_table(path)
    for c in DATE_COLUMNS:
        if c in tab.column_names:
            tab = tab.set_column(tab.column_names.index(c), c, tab.column(c).cast(pa.int32()))
    df = tab.to_pandas()
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].where(pd.notna(df[c]), None)
    return df


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _counts(t: pd.DataFrame) -> dict:
    return {"rows": int(len(t)), "by_disposition": {k: int(v) for k, v in t["disposition"].value_counts().items()},
            "by_reason": {k: int(v) for k, v in t["reason"].dropna().value_counts().items()}}


def build_quote_set(root, paths: Sequence, cfg: Config, *, underlying: str, exercise_style: str,
                    origin: str = "synthetic", policy: QuotePolicy = QuotePolicy()) -> dict:
    """Persist the contract-level quotes of an already-ingested SYNTHETIC dataset. Returns the manifest
    (``reused`` True when the identical set already existed and re-checked clean)."""
    if origin != "synthetic":
        raise ValueError("quote persistence is approved for synthetic data only (Q-D5, 2026-10-21); "
                         f"origin={origin!r} needs a new owner decision")
    names = [Path(p).name for p in paths]
    if not names or any(".synthetic." not in n for n in names):
        raise ValueError(f"every input must be named *.synthetic.* (synthetic only, Q-D5): {names}")
    if exercise_style not in EXERCISE_STYLES:
        raise ValueError(f"exercise_style must be one of {EXERCISE_STYLES}")
    if not underlying or "|" in underlying:
        raise ValueError("underlying must be a non-empty name without '|'")
    root = Path(root)
    inputs = [RawStore(root).put(p) for p in sorted(map(Path, paths), key=lambda p: p.name)]
    version = dataset_version_id([i["sha256"] for i in inputs], cfg.sha256())
    ds_mf = root / "datasets" / version / "manifest.json"
    if not ds_mf.is_file():
        raise FileNotFoundError(f"dataset {version[:12]} not found: run raw_store.ingest first (quotes are additive)")
    ds = json.loads(ds_mf.read_text())
    if ds.get("origin") != "synthetic":
        raise ValueError(f"dataset {version[:12]} is not labelled origin='synthetic' (got {ds.get('origin')!r})")

    wide, ledger1, unusable = load_wide([Path(i["stored"]) for i in inputs], cfg.data, max_rows=ds.get("max_rows"),
                                        return_unusable=True)
    quotes, ledger2, _diag, rows = build_otm_quotes(wide, cfg.data, return_rows=True)
    if panel_sha256(build_surface_panel(quotes, cfg.surface)) != ds["panel_sha256"]:
        raise OverwriteError(f"rebuilt panel does not reproduce dataset {version[:12]}'s panel_sha256; not persisting")
    unusable, n_exact, n_collide = _dedupe_unusable(unusable, wide)
    table = quote_rows(rows, unusable, underlying)

    # conservation: every quote-stage row and every no_usable_side reject is accounted for
    sel = table[table["otm_selected"]]
    problems = []
    if int((sel["disposition"] == "retained").sum()) != ledger2.kept or ledger2.kept != len(quotes):
        problems.append("retained rows != quote ledger kept")
    for r in QUOTE_REASONS:
        if int((sel["reason"] == r).sum()) != ledger2.rejects.get(r, 0):
            problems.append(f"reason {r}: rows != ledger")
    if len(unusable) + n_exact + n_collide != ledger1.rejects.get("no_usable_side", 0):
        problems.append("no_usable_side rows + dropped != prefilter ledger")
    if table.duplicated(["contract_id", "quote_date"]).any():
        problems.append("duplicate (contract_id, quote_date)")
    if problems:
        raise AssertionError(f"quote set not conserved: {problems}")

    qid = quote_set_id(version, policy)
    out = root / "quotes" / qid
    if (out / "purge.json").exists():
        raise OverwriteError(f"quote set {qid[:12]} was purged; re-creating it needs an explicit owner decision")
    if (out / "manifest.json").is_file():
        bad = verify_quote_set(root, qid, rebuilt=table)
        if bad:
            raise OverwriteError(f"quote set {qid[:12]} exists and does not match a rebuild: {bad}")
        return {**json.loads((out / "manifest.json").read_text()), "reused": True}
    if out.exists():
        raise OverwriteError(f"quote set {qid[:12]} directory exists without a manifest; inspect it by hand")

    import pyarrow as pa  # noqa: PLC0415
    import pyarrow.parquet as pq  # noqa: PLC0415
    stage = root / "quotes" / f".staging-{qid[:12]}-{uuid.uuid4().hex[:8]}"
    (stage / "rows").mkdir(parents=True)
    try:
        files = {}
        for day, part in table.groupby("quote_date", sort=True):
            rel = f"rows/{np.datetime64(int(day), 'D')}.parquet"
            pq.write_table(_to_arrow(part.reset_index(drop=True)), stage / rel)
            files[rel] = None
        fw = estimate_forwards(wide, cfg.data).reset_index()
        sf = pa.table({"quote_date": pa.array(fw["date"].to_numpy(dtype=np.int32)).cast(pa.date32()),
                       "expiry": pa.array(fw["expiry"].to_numpy(dtype=np.int32)).cast(pa.date32()),
                       "F": fw["F"].to_numpy(dtype=float), "DF": fw["DF"].to_numpy(dtype=float),
                       "n_pairs": fw["n_pairs"].to_numpy(dtype=np.int32), "regression": fw["regression"].to_numpy(),
                       "fstat": fw["fstat"].to_numpy(dtype=np.int8),
                       "T": (fw["expiry"].to_numpy(dtype=float) - fw["date"].to_numpy(dtype=float)) / 365.0})
        pq.write_table(sf, stage / "slice_forward.parquet")
        files["slice_forward.parquet"] = None
        files = {rel: {"bytes": (stage / rel).stat().st_size, "sha256": _sha256(stage / rel)} for rel in files}
        manifest = {
            "schema": policy.schema, "quote_set_id": qid, "dataset_version_id": version,
            "panel_sha256": ds["panel_sha256"], "config_sha256": cfg.sha256(), "policy": {
                "schema": policy.schema, "rebuild_rel_tol": policy.rebuild_rel_tol}, "policy_sha256": policy.sha256(),
            "code_version": code_version(), "origin": origin, "licence_class": "synthetic", "underlying": underlying,
            "exercise_style": exercise_style, "settlement": None, "snapshot_kind": "eod_close", "data_mode": DATA_MODE,
            "timestamp_convention": "quote_date = venue calendar date (not UTC); no intraday time in this source",
            "pricing_method": "Black-76 on the put-call-parity forward, OTM side only (validation/quotes.py)",
            "inputs": [{k: i[k] for k in ("name", "sha256", "bytes")} for i in inputs],
            "counts": {**_counts(table), "unusable_exact_duplicates": n_exact, "unusable_key_collisions": n_collide},
            "ledgers_conserved": True, "source_content_sha256": source_content_sha256(table),
            "files": files, "file_format": "parquet (provisional; DEC-009 benchmark not run)",
            "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "environment": {"python": platform.python_version(), "platform": platform.platform(),
                            "numpy": np.__version__, "pandas": pd.__version__, "pyarrow": pa.__version__},
        }
        (stage / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True))  # last
        os.replace(stage, out)   # atomic promote: readers never see a half-written set
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return {**manifest, "reused": False}


def load_quote_rows(root, qid: str) -> pd.DataFrame:
    out = Path(root) / "quotes" / qid
    if (out / "purge.json").exists():
        raise FileNotFoundError(f"quote set {qid[:12]} was purged (manifest kept, rows removed)")
    manifest = json.loads((out / "manifest.json").read_text())
    parts = [_read_parquet(out / rel) for rel in sorted(manifest["files"]) if rel.startswith("rows/")]
    return pd.concat(parts, ignore_index=True)[list(COLUMNS)]


def verify_quote_set(root, qid: str, *, rebuilt: pd.DataFrame | None = None) -> list:
    """Problems with a stored set (empty = intact). With ``rebuilt``, also compare to a fresh rebuild: source columns
    and exact columns must be identical, derived floats within the policy tolerance (scaled by the column maximum)."""
    out = Path(root) / "quotes" / qid
    try:
        manifest = json.loads((out / "manifest.json").read_text())
    except (OSError, ValueError) as e:
        return [f"unreadable manifest: {e}"]
    if (out / "purge.json").exists():
        left = [rel for rel in manifest["files"] if (out / rel).exists()]
        return [f"purged set still has files: {left}"] if left else []
    problems = [f"file {rel}: missing or hash mismatch" for rel, f in manifest["files"].items()
                if not (out / rel).is_file() or _sha256(out / rel) != f["sha256"]]
    if problems:
        return problems
    stored = load_quote_rows(root, qid)
    if source_content_sha256(stored) != manifest["source_content_sha256"]:
        problems.append("source content hash mismatch")
    if _counts(stored) != {k: manifest["counts"][k] for k in ("rows", "by_disposition", "by_reason")}:
        problems.append("row counts differ from manifest")
    if rebuilt is not None:
        if len(rebuilt) != len(stored) or source_content_sha256(rebuilt) != source_content_sha256(stored):
            return problems + ["rebuild: source columns differ"]
        for c in EXACT_COLUMNS:
            if [None if pd.isna(v) else v for v in rebuilt[c]] != [None if pd.isna(v) else v for v in stored[c]]:
                problems.append(f"rebuild: column {c} differs")
        tol = manifest["policy"]["rebuild_rel_tol"]
        for c in DERIVED_FLOATS:
            a = pd.to_numeric(rebuilt[c], errors="coerce").to_numpy(dtype=float)
            b = pd.to_numeric(stored[c], errors="coerce").to_numpy(dtype=float)
            scale = float(np.nanmax(np.abs(b))) if np.isfinite(b).any() else 1.0
            if not np.array_equal(np.isnan(a), np.isnan(b)) or not np.allclose(
                    a, b, rtol=tol, atol=tol * scale, equal_nan=True):
                problems.append(f"rebuild: derived column {c} outside tolerance {tol}")
    return problems


def purge_quote_set(root, qid: str, reason: str) -> dict:
    """Remove a set's data files (D3). The manifest stays, so a recorded ``quote_set_id`` still resolves; a
    ``purge.json`` records why and when. Refuses an empty reason and a second purge."""
    if not reason.strip():
        raise ValueError("a purge needs a reason")
    out = Path(root) / "quotes" / qid
    manifest = json.loads((out / "manifest.json").read_text())
    if (out / "purge.json").exists():
        raise OverwriteError(f"quote set {qid[:12]} is already purged")
    record = {"quote_set_id": qid, "reason": reason, "removed": sorted(manifest["files"]),
              "purged_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    (out / "purge.json").write_text(json.dumps(record, indent=1, sort_keys=True))  # first: a crash leaves it marked
    for rel in manifest["files"]:
        (out / rel).unlink(missing_ok=True)
    shutil.rmtree(out / "rows", ignore_errors=True)
    return record
