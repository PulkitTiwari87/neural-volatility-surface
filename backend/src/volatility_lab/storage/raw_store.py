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


def ingest(root, paths: Sequence, cfg: Config, *, max_rows=None) -> dict:
    """Raw files -> stored raw objects -> quotes -> surface panel -> versioned dataset. Returns the manifest.

    ``manifest["reused"]`` is True when the identical dataset version already existed (nothing rewritten).
    """
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
    text = json.dumps(manifest, indent=1, sort_keys=True, default=str)
    out = Path(root) / "datasets" / version
    mf = out / "manifest.json"
    if mf.exists():
        if mf.read_text() != text:
            raise OverwriteError(f"dataset {version[:12]} exists with different content; a correction needs a new version")
        return {**manifest, "reused": True}
    out.mkdir(parents=True)
    np.savez_compressed(out / "panel.npz", **panel)
    mf.write_text(text)
    return {**manifest, "reused": False}
