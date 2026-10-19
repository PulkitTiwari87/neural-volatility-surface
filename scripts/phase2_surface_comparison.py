"""Reproduce docs/research/PHASE2_SURFACE_COMPARISON.md. SYNTHETIC data only; deterministic (fixed seeds).

    python scripts/phase2_surface_comparison.py --out scratch/phase2_comparison.json

Refuses to overwrite ``--out``. Prints markdown tables to stdout.
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend" / "src"))

from volatility_lab.config.settings import Config, SplitConfig  # noqa: E402
from volatility_lab.datasets.synthetic import LABEL, make_chain, true_sigma  # noqa: E402
from volatility_lab.ingestion.optionsdx import RejectLedger, prefilter_batch  # noqa: E402
from volatility_lab.surfaces import compare_methods as cm  # noqa: E402
from volatility_lab.validation.quotes import build_otm_quotes  # noqa: E402

STUDY = {"seed": 3, "n_days": 120, "date_stride": 4, "noise_free": False,
         "chains": {"dense (strike step 1/5)": 1.0, "sparse (strike step 5/25)": 5.0}}
CFG = Config(split=SplitConfig(first_test_year=2020, last_test_year=2020, min_train_years=1))


def md(df: pd.DataFrame) -> str:
    return df.to_string(index=False, float_format=lambda v: f"{v:.3f}")


def main(out: Path) -> None:
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    report = {"label": LABEL, "study": STUDY, "k": {}, "t": {}, "filters": {}}
    for chain_name, step in STUDY["chains"].items():
        wide_raw, truth = make_chain(STUDY["n_days"], seed=STUDY["seed"], strike_step=step, noise_free=STUDY["noise_free"])
        wide = prefilter_batch(wide_raw, CFG.data, RejectLedger())
        quotes, ledger, _ = build_otm_quotes(wide, CFG.data)
        print(f"\n## {chain_name}: {len(quotes)} kept quotes from {ledger.rows_in} rows  [{LABEL}]")
        k = cm.summarize_by_region(cm.loo_k(quotes, date_stride=STUDY["date_stride"]))
        print("\n### leave-one-out in k (vol points)\n" + md(k))
        report["k"][chain_name] = k.to_dict("records")
        for thin in (1, 4):
            t = cm.summarize_by_region(cm.loo_expiry_t(quotes, thin=thin, date_stride=STUDY["date_stride"]))
            print(f"\n### leave-one-expiry-out in T, neighbours +-{thin} expiries (vol points)\n" + md(t[t.region == 'ALL']))
            report["t"].setdefault(chain_name, {})[f"thin{thin}"] = t.to_dict("records")
        f = cm.filter_policy_report(wide, truth, true_sigma, CFG)
        print("\n### quote-filter policies vs the generating surface\n" + md(f.T.reset_index().rename(columns={"index": "metric"})))
        report["filters"][chain_name] = f.to_dict("records")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1, default=float))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    main(ap.parse_args().out)
