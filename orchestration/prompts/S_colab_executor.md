# Colab executor (separate chat, or orchestrator via colab-mcp)

Read `_COMMON.md` first, **but** this is the one role that executes project code — only inside Google Colab, never on the PC.
Owned file: `orchestration/reports/COLAB_VERIFICATION.md`.
1. Confirm a Colab runtime is connected (colab-mcp `open_colab_browser_connection`, or the owner's open notebook). If not: write `BLOCKED — COLAB UNAVAILABLE` and stop. Do not run anything locally.
2. Get the **exact working tree** to the runtime without commit/push and without credentials: zip `backend/`, `scripts/`, `configs/`, `docs/engineering` etc. (no `data/`, no `artifacts/`, no secrets, no `.env`) and upload through the Colab file API/UI, or have the owner upload the zip. Record a content manifest (file list + SHA-256 of each file, plus overall hash) and `git rev-parse HEAD` + `git status --short` of the PC tree at zip time.
3. In Colab: record `python --version`, `pip freeze` (or the packages actually installed), `nvidia-smi` if relevant. Install only the packages the code imports (numpy, pandas, scipy, pyarrow; torch only for GPU tasks) — state versions.
4. Run, one at a time, saving full output: `cd backend && PYTHONPATH=src python -W error::ResourceWarning -m unittest discover -s tests -t .`; `cd scripts/phase0_synthetic && python -W error::ResourceWarning -m unittest discover -s tests -t .`; `python scripts/foundation_audit.py`; `cd backend && PYTHONPATH=src python -O -m unittest tests.unit.test_leakage_and_folds`.
5. Report for each: environment, command, manifest hash, result (counts), failures verbatim. Do not compare to the PC numbers as if equivalent; list differences. Never print tokens.
Status: READY_FOR_REVIEW | BLOCKED | NEEDS_APPROVAL.
