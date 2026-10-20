"""Write-once raw store and content-versioned datasets (Phase 1; local filesystem only).

* Raw files are stored content-addressed (``raw/<sha[:2]>/<sha256><suffix>``): the same bytes always map to
  the same path, a path can never hold different bytes, and a corrected file is a *new* object.
* A dataset version is ``sha256(input hashes + config hash)``. Ingesting the same inputs with the same config
  yields the same version id and an identical manifest; any change yields a different id. Nothing is
  overwritten: an id that already exists must reproduce byte-identical manifest content or ingestion refuses.
* The manifest carries both reject ledgers (``rows_in == kept + rejects``, checked) and the panel hash.

Storage format is not a decision (DEC-009): this is a minimal local layout, not an adopted standard.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Sequence

import numpy as np

from volatility_lab.config.settings import Config
from volatility_lab.ingestion.optionsdx import load_wide
from volatility_lab.surfaces.grid import build_surface_panel, status_counts
from volatility_lab.validation.quotes import build_otm_quotes

SCHEMA = "dataset-1"
ORIGINS = ("synthetic", "real")


class OverwriteError(RuntimeError):
    """An existing object would be changed (raw bytes or a dataset manifest)."""


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def panel_sha256(panel: dict) -> str:
    """Hash of a surface panel's content (keys, dtypes, shapes, bytes); NaN-safe and file-format independent."""
    h = hashlib.sha256()
    for key in sorted(panel):
        a = np.ascontiguousarray(panel[key])
        h.update(f"{key}|{a.dtype.str}|{a.shape}|".encode())
        h.update(a.tobytes())
    return h.hexdigest()


class RawStore:
    def __init__(self, root) -> None:
        self.root = Path(root)

    def put(self, path) -> dict:
        """Store a file by content. Idempotent for identical bytes; refuses to alter an existing object."""
        path = Path(path)
        digest = sha256_file(path)
        dest = self.root / "raw" / digest[:2] / f"{digest}{path.suffix}"
        if dest.exists():
            if sha256_file(dest) != digest:
                raise OverwriteError(f"stored object {dest.name} no longer matches its hash")
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dest)
        return {"name": path.name, "sha256": digest, "bytes": dest.stat().st_size, "stored": str(dest)}

    def verify(self) -> list:
        """Re-hash every stored object; returns problems (empty = intact)."""
        raw = self.root / "raw"
        bad = []
        for fp in sorted(raw.rglob("*")) if raw.exists() else []:
            if fp.is_file() and sha256_file(fp) != fp.stem:
                bad.append(f"hash mismatch {fp.name}")
        return bad


def dataset_version_id(input_hashes: Sequence[str], config_sha256: str) -> str:
    blob = json.dumps({"inputs": sorted(input_hashes), "config_sha256": config_sha256}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


def ingest(root, paths: Sequence, cfg: Config, *, max_rows=None, origin: str | None = None) -> dict:
    """Raw files -> stored raw objects -> quotes -> surface panel -> versioned dataset. Returns the manifest.

    ``manifest["reused"]`` is True when the identical dataset version already existed (nothing rewritten).

    ``origin`` ("synthetic" | "real", GR-DATA-04) is optional. When given it is recorded in the manifest and in a
    ``meta.json`` (written only if absent) next to ``panel.npz``; it is *not* part of ``version_id``. When ``None``
    the manifest is exactly what it was before this option existed. Input files named ``*.synthetic.*`` are refused
    as ``"real"``. Re-ingesting the same inputs with a different origin (or with/without one) is refused by the
    manifest overwrite check: a label is never silently changed.
    """
    if origin is not None and origin not in ORIGINS:
        raise ValueError(f"origin must be one of {ORIGINS} or None, got {origin!r}")
    if origin == "real":
        bad = [Path(p).name for p in paths if ".synthetic." in Path(p).name]
        if bad:
            raise ValueError(f"synthetic file(s) can never be stored as real data: {bad}")
    store = RawStore(root)
    inputs = [store.put(p) for p in sorted(map(Path, paths), key=lambda p: p.name)]
    version = dataset_version_id([i["sha256"] for i in inputs], cfg.sha256())
    wide, ledger1 = load_wide([Path(i["stored"]) for i in inputs], cfg.data, max_rows=max_rows)
    quotes, ledger2, diag = build_otm_quotes(wide, cfg.data)
    panel = build_surface_panel(quotes, cfg.surface)
    manifest = {
        "schema": SCHEMA, "version_id": version, "config_sha256": cfg.sha256(), "config": cfg.to_dict(),
        "max_rows": max_rows,
        "inputs": [{k: i[k] for k in ("name", "sha256", "bytes")} for i in inputs],
        "ledger_prefilter": ledger1.to_dict(), "ledger_quotes": ledger2.to_dict(), "ledgers_conserved": True,
        "quote_diagnostics": diag, "surface_status_counts": status_counts(panel), "panel_sha256": panel_sha256(panel),
    }
    if origin is not None:
        manifest["origin"] = origin
    # Phase 1 A2: per-snapshot reconciliation (rows_in = kept + rejected on every quote date), kept next to the manifest
    report_text = json.dumps({"schema": "quality-report-1", "prefilter_by_snapshot": ledger1.by_date_report(),
                              "quotes_by_snapshot": ledger2.by_date_report()}, indent=1, sort_keys=True)
    manifest["quality_report_sha256"] = hashlib.sha256(report_text.encode()).hexdigest()
    text = json.dumps(manifest, indent=1, sort_keys=True, default=str)
    out = Path(root) / "datasets" / version
    mf = out / "manifest.json"
    if mf.exists():
        if mf.read_text() != text:
            raise OverwriteError(f"dataset {version[:12]} exists with different content; a correction needs a new version")
        qr = out / "quality_report.json"
        if not qr.is_file() or qr.read_text() != report_text:
            raise OverwriteError(f"dataset {version[:12]} has a missing or altered quality report")
        _write_meta(out, origin)
        return {**manifest, "reused": True}
    out.mkdir(parents=True)
    np.savez_compressed(out / "panel.npz", **panel)
    (out / "quality_report.json").write_text(report_text)
    mf.write_text(text)
    _write_meta(out, origin)
    return {**manifest, "reused": False}


def verify_dataset(root, version_id: str) -> list:
    """Re-check a stored dataset against its manifest (panel hash, quality-report hash, per-snapshot conservation).

    Returns the problems found (empty = intact). Read-only."""
    out = Path(root) / "datasets" / version_id
    problems = []
    try:
        manifest = json.loads((out / "manifest.json").read_text())
        with np.load(out / "panel.npz") as z:
            panel = {k: z[k] for k in z.files}
        report_text = (out / "quality_report.json").read_text()
    except (OSError, ValueError) as e:
        return [f"unreadable dataset file: {e}"]
    if panel_sha256(panel) != manifest.get("panel_sha256"):
        problems.append("panel hash mismatch")
    if hashlib.sha256(report_text.encode()).hexdigest() != manifest.get("quality_report_sha256"):
        problems.append("quality report hash mismatch")
    try:
        report = json.loads(report_text)
        for stage in ("prefilter_by_snapshot", "quotes_by_snapshot"):
            for day, c in report[stage].items():
                if c["rows_in"] != c["kept"] + sum(c["rejects"].values()):
                    problems.append(f"{stage} {day}: rows_in != kept + rejected")
    except (ValueError, KeyError, TypeError, AttributeError):
        problems.append("quality report is malformed")
    return problems


def _write_meta(out: Path, origin: str | None) -> None:
    """``meta.json`` is the run label read by the API; an existing one is never overwritten."""
    meta = out / "meta.json"
    if origin is not None and not meta.exists():
        meta.write_text(json.dumps({"origin": origin, "description": f"ingested with origin={origin}"}, indent=1))
