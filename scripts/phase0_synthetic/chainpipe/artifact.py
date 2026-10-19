"""Surface artifact: canonical JSON, provenance, configuration, diagnostics and a content hash (version id).
Deterministic: no wall-clock time is stored, so the same input and configuration give byte-identical output."""
import hashlib
import json
import sys
from pathlib import Path

from phase0.audit import _fresh_path

from . import BANNER
from .pipeline import ChainResult, ChainRunConfig, config_dict
from .schema import ChainRead

SCHEMA_VERSION = "chainpipe-surface-1"
_PHASE0_USED = ("bsm.py", "iv.py", "quotes.py", "surface.py", "synth.py", "evaluate.py", "forecast.py")


def code_hashes() -> dict:
    here = Path(__file__).resolve().parent
    out = {"chainpipe/" + p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(here.glob("*.py"))}
    for n in _PHASE0_USED:
        out["phase0/" + n] = hashlib.sha256((here.parent / "phase0" / n).read_bytes()).hexdigest()
    return out


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False)


def content_sha256(art: dict) -> str:
    return hashlib.sha256(canonical_json({k: v for k, v in art.items() if k not in ("content_sha256", "version_id")}).encode()).hexdigest()


def build_artifact(read: ChainRead, result: ChainResult, cfg: ChainRunConfig) -> dict:
    origins = sorted({q.origin for s in read.snapshots for q in s.quotes})
    synthetic_only = origins == ["synthetic"]
    cfgd = config_dict(cfg)
    ledger = dict(result.file_ledger)
    ledger["parse_error_examples"] = [{"row": e.row, "code": e.code, "detail": e.detail} for e in read.row_errors[:100]]
    art = {"schema": SCHEMA_VERSION,
           "label": BANNER if synthetic_only else "CONTAINS NON-SYNTHETIC DATA: check the provider licence before storing, displaying or sharing",
           "origins": origins, "config": cfgd, "config_sha256": hashlib.sha256(canonical_json(cfgd).encode()).hexdigest(),
           "provenance": {"input_name": read.name, "input_sha256": read.sha256, "columns": list(read.columns), "extra_columns_ignored": list(read.extra_columns),
                          "code_sha256": code_hashes(), "python": sys.version.split()[0]},
           "file_ledger": ledger, "snapshots": result.snapshots}
    h = content_sha256(art)
    art["content_sha256"], art["version_id"] = h, "sfc-" + h[:16]
    return art


def write_artifact(path, art: dict) -> Path:
    p = _fresh_path(path)
    p.write_text(canonical_json(art) + "\n", encoding="utf-8")
    return p


def load_artifact(path) -> dict:
    art = json.loads(Path(path).read_text(encoding="utf-8"))
    if art.get("schema") != SCHEMA_VERSION:
        raise ValueError("unsupported schema %r" % art.get("schema"))
    if content_sha256(art) != art.get("content_sha256"):
        raise ValueError("content hash mismatch: the artifact was modified")
    return art
