"""Read-only research-API logic (Phase 5). No HTTP here; ``server.py`` is the transport.

A *runs root* holds one directory per run::

    <run_id>/panel.npz        surface panel arrays (``build_surface_panel`` keys)      required
    <run_id>/meta.json        {"origin": "synthetic"|"real", "description": "..."}      optional
    <run_id>/manifest.json    ``dataset-1`` manifest from ``storage.raw_store.ingest``  optional
    <run_id>/tables/*.csv     descriptive result tables                                 optional
    <run_id>/forecasts/*.npz  stored forecasts: target_index, origin_index, pred (n,T,K)  optional

This layer never computes IV, never trains, never forecasts and never holds provider credentials: it only
reads files that already exist and says what they are. A run without ``meta.json`` is reported as
``unlabelled`` so the viewer cannot mistake it for labelled real or synthetic data.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import numpy as np

from volatility_lab.storage.raw_store import panel_sha256
from volatility_lab.surfaces.grid import OBSERVED, STATUS_LABELS

NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")
MAX_TABLE_ROWS = 5000
ORIGINS = ("synthetic", "real")


class NotFound(LookupError):
    pass


class BadRequest(ValueError):
    pass


def _clean(a) -> list:
    """ndarray -> nested lists with NaN -> None (JSON has no NaN)."""
    return np.where(np.isfinite(a), a, None).tolist() if a.dtype.kind == "f" else a.tolist()


def _num(s: str):
    try:
        return float(s)
    except ValueError:
        return s


class RunStore:
    def __init__(self, root) -> None:
        self.root = Path(root).resolve()

    # -- path safety: names are validated by regex AND must resolve to a direct child of the root
    def _run_dir(self, run_id: str) -> Path:
        if not isinstance(run_id, str) or not NAME.match(run_id):
            raise BadRequest("invalid run id")
        d = (self.root / run_id).resolve()
        if d.parent != self.root or not (d / "panel.npz").is_file():
            raise NotFound(f"no such run: {run_id}")
        return d

    def _panel(self, d: Path) -> dict:
        with np.load(d / "panel.npz") as z:
            return {k: z[k] for k in z.files}

    @staticmethod
    def _json(path: Path) -> dict:
        return json.loads(path.read_text()) if path.is_file() else {}

    def _label(self, d: Path) -> dict:
        meta = self._json(d / "meta.json")
        origin = meta.get("origin") if meta.get("origin") in ORIGINS else "unlabelled"
        return {"origin": origin, "description": str(meta.get("description", ""))}

    def list_runs(self) -> list:
        out = []
        for d in sorted(p for p in self.root.iterdir() if p.is_dir() and NAME.match(p.name)) if self.root.is_dir() else []:
            if (d / "panel.npz").is_file():
                out.append({"id": d.name, **self._label(d)})
        return out

    def run_info(self, run_id: str) -> dict:
        d = self._run_dir(run_id)
        panel = self._panel(d)
        manifest = self._json(d / "manifest.json")
        st = panel["status"]
        info = {
            "id": run_id, **self._label(d),
            "dates": [str(x) for x in panel["dates"].astype("datetime64[D]")],
            "tenor_days": panel["tenor_days"].tolist(), "k_nodes": panel["k_nodes"].tolist(),
            "status_labels": {str(k): v for k, v in STATUS_LABELS.items()},
            "status_counts": {v: int((st == k).sum()) for k, v in STATUS_LABELS.items()},
            "tables": sorted(p.stem for p in (d / "tables").glob("*.csv")) if (d / "tables").is_dir() else [],
            "forecasts": sorted(p.stem for p in (d / "forecasts").glob("*.npz")) if (d / "forecasts").is_dir() else [],
            "lineage": None,
        }
        if manifest:
            actual = panel_sha256(panel)
            info["lineage"] = {
                "version_id": manifest.get("version_id"), "config_sha256": manifest.get("config_sha256"),
                "inputs": manifest.get("inputs"), "ledgers_conserved": manifest.get("ledgers_conserved"),
                "ledger_prefilter": manifest.get("ledger_prefilter"), "ledger_quotes": manifest.get("ledger_quotes"),
                "panel_sha256_recorded": manifest.get("panel_sha256"), "panel_sha256_actual": actual,
                "panel_hash_matches": manifest.get("panel_sha256") == actual,
            }
        return info

    def surface(self, run_id: str, index: int) -> dict:
        d = self._run_dir(run_id)
        panel = self._panel(d)
        n = panel["iv"].shape[0]
        if not 0 <= index < n:
            raise NotFound(f"surface index out of range 0..{n - 1}")
        return {
            "run": run_id, **self._label(d), "index": index,
            "date": str(panel["dates"][index].astype("datetime64[D]")),
            "spot": float(panel["spot"][index]), "n_quotes": int(panel["n_quotes"][index]),
            "tenor_days": panel["tenor_days"].tolist(), "k_nodes": panel["k_nodes"].tolist(),
            "iv": _clean(panel["iv"][index]), "status": panel["status"][index].tolist(),
            "iv_units": "decimal (0.20 = 20%)",
        }

    def _forecast_file(self, d: Path, model: str) -> Path:
        if not isinstance(model, str) or not NAME.match(model):
            raise BadRequest("invalid forecast name")
        fp = d / "forecasts" / f"{model}.npz"
        if not fp.is_file():
            raise NotFound(f"no such forecast: {model}")
        return fp

    def forecast(self, run_id: str, model: str, index: int) -> dict:
        """Stored forecast of the surface at panel ``index`` next to the actual surface and their difference.

        ``forecasts/<model>.npz`` holds ``target_index`` (n,), ``origin_index`` (n,) and ``pred`` (n, T, K). The file is
        rejected if any origin is not strictly before its target (a forecast cannot use the future). The difference
        (forecast - actual) exists only where the actual cell is not missing and the forecast is finite; MAE is
        reported on cells whose actual status is OBSERVED, with the count.
        """
        d = self._run_dir(run_id)
        panel = self._panel(d)
        with np.load(self._forecast_file(d, model)) as z:
            tgt, org, pred = z["target_index"], z["origin_index"], z["pred"]
        n, T, K = panel["iv"].shape
        if pred.shape != (len(tgt), T, K) or org.shape != tgt.shape:
            raise BadRequest("forecast file shape does not match the run's panel")
        if (org >= tgt).any() or tgt.min(initial=0) < 0 or tgt.max(initial=0) >= n:
            raise BadRequest("forecast file has an origin at or after its target, or an index outside the panel")
        hit = np.flatnonzero(tgt == index)
        if hit.size != 1:
            raise NotFound(f"no forecast of this model for surface index {index}")
        f, o = pred[hit[0]], int(org[hit[0]])
        actual, st = panel["iv"][index], panel["status"][index]
        both = np.isfinite(f) & np.isfinite(actual) & (st != 0)
        diff = np.where(both, f - actual, np.nan)
        obs = both & (st == OBSERVED)
        return {
            "run": run_id, **self._label(d), "model": model, "index": index,
            "target_date": str(panel["dates"][index].astype("datetime64[D]")),
            "origin_date": str(panel["dates"][o].astype("datetime64[D]")), "horizon_panel_steps": index - o,
            "tenor_days": panel["tenor_days"].tolist(), "k_nodes": panel["k_nodes"].tolist(),
            "actual": _clean(np.where(st != 0, actual, np.nan)), "status": st.tolist(),
            "forecast": _clean(f), "difference": _clean(diff),
            "n_difference_cells": int(both.sum()), "n_observed_cells": int(obs.sum()),
            "mae_observed_vol_points": float(np.abs(diff[obs]).mean() * 100.0) if obs.any() else None,
            "iv_units": "decimal (0.20 = 20%); difference = forecast - actual",
        }

    def table(self, run_id: str, name: str) -> dict:
        d = self._run_dir(run_id)
        if not isinstance(name, str) or not NAME.match(name):
            raise BadRequest("invalid table name")
        fp = d / "tables" / f"{name}.csv"
        if not fp.is_file():
            raise NotFound(f"no such table: {name}")
        with open(fp, newline="") as fh:
            rows = list(csv.reader(fh))
        header, body = rows[0], rows[1:]
        return {"run": run_id, "table": name, "columns": header, "truncated": len(body) > MAX_TABLE_ROWS,
                "rows": [[_num(c) for c in r] for r in body[:MAX_TABLE_ROWS]]}
