"""CLI for the synthetic end-to-end path (from scripts/phase0_synthetic/):
  python -m chainpipe.run build    --input chainpipe/fixtures/chain_normal_snapshot.synthetic.csv --out <new>.json [--rate 0.02]
  python -m chainpipe.run evaluate --artifact <artifact>.json --out <new>_eval.json [--train 0.6 --valid 0.2]
Outputs are new files only (existing paths and anything under experiments/ are refused)."""
import argparse
import json

from phase0.audit import _fresh_path

from .artifact import build_artifact, canonical_json, load_artifact, write_artifact
from .evaluation import evaluate_baselines
from .pipeline import ChainRunConfig, run_chain
from .schema import CsvChainProvider


def main(argv=None):
    ap = argparse.ArgumentParser(description="SYNTHETIC chain -> surface pipeline (spike-scope)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--input", required=True)
    b.add_argument("--out", required=True)
    b.add_argument("--rate", type=float, default=ChainRunConfig().rate)
    e = sub.add_parser("evaluate")
    e.add_argument("--artifact", required=True)
    e.add_argument("--out", required=True)
    e.add_argument("--train", type=float, default=0.6)
    e.add_argument("--valid", type=float, default=0.2)
    a = ap.parse_args(argv)
    if a.cmd == "build":
        cfg = ChainRunConfig(rate=a.rate)
        _fresh_path(a.out)  # fail before computing
        read = CsvChainProvider(a.input).read()
        art = build_artifact(read, run_chain(read, cfg), cfg)
        write_artifact(a.out, art)
        print(json.dumps({"version_id": art["version_id"], "label": art["label"], "snapshots": len(art["snapshots"]), "file_ledger": art["file_ledger"]["terminal_counts"]}, indent=1))
        return 0
    art = load_artifact(a.artifact)
    p = _fresh_path(a.out)
    rec = evaluate_baselines(art, a.train, a.valid)
    p.write_text(canonical_json(rec) + "\n", encoding="utf-8")
    print(json.dumps({"label": rec["label"], "leakage_audit": rec["leakage_audit"], "splits": rec["splits"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
