"""Build a viewer run from the held SPY end-of-day options dataset. PRIVATE, LOCAL USE ONLY (decision.md DEC-002-A).

Run it where the dataset already is (the owner's Kaggle notebook or Colab runtime; this repository never holds the data):

    python scripts/make_spy_run.py --src /kaggle/input/spy-options-eod-volatility-surface-2010-2023 --out /kaggle/working/spy_store

Then download ONLY ``<out>/datasets/<version_id>/`` (panel.npz, meta.json, manifest.json, tables/, forecasts/) to
``scratch/spy_local/datasets/`` on the owner's own machine (``scratch/`` is Git-ignored) and view it with

    python -m volatility_lab.api.server --root scratch/spy_local/datasets

Do NOT download ``<out>/raw`` (it holds copies of the vendor's rows), do not commit, host or publish any of it: the upstream OptionsDX
licence is unverified. The run is labelled ``origin=real`` with the label DEC-002-A requires. The only forecast stored is persistence
(the surface at t is the forecast for t+1; no model is trained here). Needs an explicit per-run authorization (AP-003/AP-009).
"""
import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from make_synthetic_run import persistence_table  # noqa: E402
from volatility_lab.config.settings import Config  # noqa: E402
from volatility_lab.ingestion.optionsdx import discover_files  # noqa: E402
from volatility_lab.storage.raw_store import ingest  # noqa: E402

LABEL = "SPY end-of-day options, upstream licence unverified, backtest only"


def write_run(out: Path, files: list) -> Path:
    m = ingest(out, files, Config(), origin="real")
    run = out / "datasets" / m["version_id"]
    with np.load(run / "panel.npz") as z:
        panel = {k: z[k] for k in z.files}
    (run / "meta.json").write_text(json.dumps({"origin": "real", "description": LABEL}))
    (run / "tables").mkdir(exist_ok=True)
    with open(run / "tables" / "persistence_by_tenor.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["tenor_days", "mae_vol_points", "n_cells", "insufficient_n"])
        w.writerows(persistence_table(panel))
    (run / "forecasts").mkdir(exist_ok=True)
    n = panel["iv"].shape[0]
    np.savez_compressed(run / "forecasts" / "persistence.npz", target_index=np.arange(1, n),
                        origin_index=np.arange(0, n - 1), pred=panel["iv"][:-1])
    return run


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="directory holding the dataset files (parquet/csv)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    run = write_run(Path(a.out), discover_files(a.src))
    print(f"run: {run}\ndownload only this directory, never <out>/raw")


if __name__ == "__main__":
    main()
