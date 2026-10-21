# Local Development

**Status:** PARTIAL (updated 2026-10-21). Research code exists (`backend/src/volatility_lab`, `scripts/phase0_synthetic`, `frontend/index.html`) but there is **no toolchain decision, dependency manifest or lockfile** (DEC-015 is OPEN), so a clean-machine setup procedure is still not written. **Do not invent or paste setup commands that do not exist.** · **Related:** [CONFIGURATION](CONFIGURATION.md), [CODING_STANDARDS](../engineering/CODING_STANDARDS.md), [TESTING_STRATEGY](../engineering/TESTING_STRATEGY.md)

## Phase 0 synthetic spike (the only runnable code today)
Verified on 2026-10-12 on Windows 11, CPython 3.12.6 (only configuration tested); needs nothing installed (standard library only, [ADR-0003](../architecture/ADR/ADR-0003-phase0-spike-toolchain.md)). From `scripts/phase0_synthetic/`:
```text
python -m unittest discover -s tests -t .
python -m phase0.run single --world AR --seed 20261013 --days 300
python -m phase0.run study --first-seed 20261100 --n-seeds 10 --days 300
```
All data are **synthetic**; run records go to the git-ignored `experiments/phase0_synthetic/`. This is not the product environment — that is still undecided (DEC-015).

## What is true today
- The repository contains documentation, the Phase 0 synthetic spike, the `volatility_lab` research package with its tests, a read-only standard-library research API and a static 2D viewer (no 3D, no framework: DEC-007/008).
- A Git repository exists with commits made by the owner. Git operations (commit, push, branch) are the owner's alone; agents do not perform them.
- **Execution policy (owner-stated, `orchestration/DECISIONS.md` OD-7; not yet recorded in `decision.md`, AP-006 pending):** project code is run in Google Colab, not on the owner's PC; local sessions read and edit only.
- Backend suite, as run in Colab on 2026-10-21 (Linux, Python 3.13.x, numpy 2.1.3; results and caveats in `orchestration/reports/COLAB_VERIFICATION.md` Addenda 7 and 11): `cd backend && PYTHONPATH=src python -W error::ResourceWarning -m unittest discover -s tests -t .` gave 278 tests OK (1 GPU test skipped on CPU, executed on a T4). The same command is the one in `.github/workflows/tests.yml`, which has never run on a GitHub runner.
- Research API (`backend/src/volatility_lab/api/server.py`): `--root` (directory with one sub-directory per run, required) and `--port` (default 8765), loopback only, read-only. The exact start command was not separately verified here; live-server probes were run in Colab (Addendum 11).

## To be completed when Phase 1 starts
| Section | Content to add | Blocked by |
|---|---|---|
| Prerequisites | OS support, language runtime versions, system packages | DEC-015 |
| Environment creation | Exact, tested commands to create the environment from the lockfile | DEC-015 |
| Configuration | Copy `.env.example` → `.env`, required variables (see [CONFIGURATION](CONFIGURATION.md)) | Phase 1 config module |
| Data | How to obtain **permitted** data; where it lives (`data/`, git-ignored); synthetic sample generation | DEC-002, Phase 0 |
| Running pipelines | Job entry points, order of stages | Phase 1–2 |
| Running tests | Commands per suite (unit / integration / scientific), expected duration | Phase 1 |
| Lint / type / format | Tool commands | DEC-015 |
| Backend API | Start command, port, docs URL | DEC-007, Phase 5 |
| Frontend | Install/build/dev commands | DEC-008, Phase 5 |
| Troubleshooting | Known issues and fixes | As discovered |

## Rules for this document
Every command listed must have been run successfully by the author on a clean checkout, with the date and OS recorded next to it. Remove instructions that stop working. Never include credentials.

## Acceptance
A new contributor can set up and run the test suite using only this document (verified by a clean-machine walkthrough at the Phase 1 gate).
