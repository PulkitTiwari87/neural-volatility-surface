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
| `tests/` | `unittest` suites (57 tests) |

## Run (from this directory; installs nothing)
```text
python -m unittest discover -s tests -t .
python -m phase0.run --help
python -m phase0.run single --world AR --seed 20261013 --days 300
python -m phase0.run study --first-seed 20261100 --n-seeds 10 --days 300
```
Run records are written to `experiments/phase0_synthetic/` (git-ignored). Each record contains seeds, configuration, Python version, source-file hashes, data/metrics hashes, validation and solver counts, metrics, intervals, hypothesis outcomes and limitations.

## Rules for this spike
Every generated record carries `origin = "synthetic"`. Do not point any code here at real market data. Thresholds in `run.TOL` and the solver settings are **spike values**, not adopted for the product. If this code is ever adopted it must be re-reviewed, moved under the product toolchain (DEC-015), and re-tested.
