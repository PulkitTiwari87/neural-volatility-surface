# phase0_synthetic — SYNTHETIC feasibility spike (disposable)

> **SYNTHETIC — not market data.** No real data, provider, account or network is used. This is **not product code**: nothing in `backend/` imports it. Findings, not code, feed later decisions.

**Status:** IMPLEMENTED as a spike; results recorded in [docs/research/PHASE0_SYNTHETIC_RESULTS.md](../../docs/research/PHASE0_SYNTHETIC_RESULTS.md). Protocol (pre-registered): [PHASE0_FEASIBILITY_PLAN §9](../../docs/research/PHASE0_FEASIBILITY_PLAN.md). Toolchain: [ADR-0003](../../docs/architecture/ADR/ADR-0003-phase0-spike-toolchain.md) — Python 3.12.6 (only version tested), **standard library only**, nothing installed.

## Layout
| Path | Role |
|---|---|
| `phase0/bsm.py` | Black-76 price, vega, no-arbitrage bounds |
| `phase0/iv.py` | Bounded Brent IV solver with explicit statuses (`CONVERGED`, `PRICE_BELOW_LOWER_BOUND`, `PRICE_ABOVE_UPPER_BOUND`, `NO_BRACKET`, `MAX_ITERATIONS`, `INVALID_INPUT`) |
| `phase0/synth.py` | Deterministic seeded generator: worlds **RW** (random-walk factors) and **AR** (AR(1) factors), irregular chains, injected defects with a ground-truth ledger |
| `phase0/quotes.py` | Validation with reason codes and exact conservation; parity-forward inference; OTM selection |
| `phase0/surface.py` | Grid construction; cell status `observed` / `interpolated` / `missing` (extrapolation disabled) |
| `phase0/forecast.py` | `HistoryView` look-ahead guard; persistence; walk-forward factor-AR(1); oracle-AR (diagnostic) |
| `phase0/evaluate.py` | Walk-forward evaluation, MAE/RMSE (decimal and vol points), block bootstrap |
| `phase0/pipeline.py`, `phase0/run.py` | End-to-end pipeline and CLI that writes run records |
| `phase0/audit.py` | POST HOC audit analyses: A2 (bootstrap coverage), A3 (200-seed study), A2b `sensitivity` (interval-method comparison; implemented, not run at protocol settings), A6 `stopped` (stopped invalid worlds; executed). `sensitivity` and `stopped` refuse existing paths and anything under `experiments/`; `sensitivity` (schema A2b-v1) also refuses reused or reserved seeds, requires `--screening` for the single-method confirmation stage and never selects there. `ledger` prints PA-4 R1–R5 from a stored study record (read-only). See [PHASE0_AUDIT](../../docs/research/PHASE0_AUDIT.md) |
| `chainpipe/` | Chain → surface → baseline-evaluation engineering path built **on** `phase0/` (which stays unchanged): `schema.py` (canonical columns, provider protocol), `pipeline.py` (row ledger, IV failures, surface), `diagnostics.py` (no-arbitrage flags), `artifact.py` (`chainpipe-surface-1`, content hash), `evaluation.py` (persistence/historical mean, leakage audit), `fixtures.py` + `fixtures/*.synthetic.csv`, `run.py` CLI. Status table: [IMPLEMENTATION_MATRIX](../../docs/engineering/IMPLEMENTATION_MATRIX.md) |
| `tests/` | `unittest` suites (145 tests: 57 original + 37 audit regression + 18 A2d in `test_a2d.py` + 33 in `test_chainpipe.py`; audit tests in `test_audit_regressions.py`) |

## Run (from this directory; installs nothing)
```text
python -m unittest discover -s tests -t .
python -m phase0.run --help
python -m phase0.run single --world AR --seed 20261013 --days 300
python -m phase0.run study --first-seed 20261100 --n-seeds 10 --days 300
python -m chainpipe.run build --input chainpipe/fixtures/chain_series12.synthetic.csv --out ../../scratch/chainpipe/series.json
python -m chainpipe.run evaluate --artifact ../../scratch/chainpipe/series.json --out ../../scratch/chainpipe/series_eval.json
```
Run records are written to `experiments/phase0_synthetic/` (git-ignored). Each record contains seeds, configuration, Python version, source-file hashes, data/metrics hashes, validation and solver counts, metrics, intervals, hypothesis outcomes and limitations.

## Rules for this spike
Every generated record carries `origin = "synthetic"`. Do not point any code here at real market data. Thresholds in `run.TOL` and the solver settings are **spike values**, not adopted for the product. If this code is ever adopted it must be re-reviewed, moved under the product toolchain (DEC-015), and re-tested.
