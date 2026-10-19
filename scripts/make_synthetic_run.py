"""Build a labelled SYNTHETIC demo run for the research viewer. No model is trained; nothing is downloaded.

    python scripts/make_synthetic_run.py --out scratch/demo_store

Creates ``<out>/datasets/<version_id>/`` (raw store + versioned dataset via ``storage.raw_store.ingest``), then adds
``meta.json`` (origin = synthetic) and ``tables/persistence_by_tenor.csv`` (a descriptive no-change error table:
mean |IV(t+1) - IV(t)| over cells OBSERVED on both days, with counts). View it with:

    python -m volatility_lab.api.server --root <out>/datasets
"""
import argparse
import csv
import json
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend" / "src"))

from volatility_lab.config.settings import Config  # noqa: E402
from volatility_lab.datasets.synthetic import LABEL, make_chain  # noqa: E402
from volatility_lab.evaluation.metrics import MIN_CELLS  # noqa: E402
from volatility_lab.storage.raw_store import ingest  # noqa: E402
from volatility_lab.surfaces.grid import OBSERVED  # noqa: E402


def persistence_table(panel: dict) -> list:
    iv, st = panel["iv"], panel["status"]
    both = (st[1:] == OBSERVED) & (st[:-1] == OBSERVED)
    err = np.abs(iv[1:] - iv[:-1]) * 100.0
    rows = []
    for j, tau in enumerate(panel["tenor_days"]):
        e = err[:, j, :][both[:, j, :]]
        n = int(e.size)
        rows.append([int(tau), round(float(e.mean()), 6) if n else "", n, n < MIN_CELLS])
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--days", type=int, default=60)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    out = Path(a.out)
    wide, _ = make_chain(a.days, seed=a.seed)
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / f"synthetic_chain_seed{a.seed}_{a.days}d.csv"
        wide.to_csv(src, index=False)
        m = ingest(out, [src], Config())
    run = out / "datasets" / m["version_id"]
    with np.load(run / "panel.npz") as z:
        panel = {k: z[k] for k in z.files}
    (run / "meta.json").write_text(json.dumps({"origin": "synthetic", "description": LABEL}))
    (run / "tables").mkdir(exist_ok=True)
    with open(run / "tables" / "persistence_by_tenor.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["tenor_days", "mae_vol_points", "n_cells", "insufficient_n"])
        w.writerows(persistence_table(panel))
    # persistence forecast (no model): the surface at t is the forecast of the surface at t+1
    (run / "forecasts").mkdir(exist_ok=True)
    n = panel["iv"].shape[0]
    np.savez_compressed(run / "forecasts" / "persistence.npz", target_index=np.arange(1, n),
                        origin_index=np.arange(0, n - 1), pred=panel["iv"][:-1])
    print(f"run: {run}\nversion_id: {m['version_id']}\nreused: {m['reused']}")


if __name__ == "__main__":
    main()
