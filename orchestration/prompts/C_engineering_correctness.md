# Agent C — Engineering and Numerical Correctness (stages S1/S3)

Read `_COMMON.md` first. **Owned file this wave:** `orchestration/reports/ENGINEERING_REPORT.md` (only). **Wave 1 is report + proposed-patch only: do NOT edit anything under `backend/`, `scripts/`, `frontend/`, `docs/`** — no Colab runtime is verified yet, so no code change can be validated. Put each proposed fix as a unified diff inside a fenced block in your report (with file, line, evidence, and the test that would prove it), so the orchestrator can queue it in `INTEGRATION_QUEUE.md` and apply it after Colab verification.

Task: static, evidence-based defect hunt in `backend/src/volatility_lab/{ingestion,validation,storage,pricing,surfaces,features,evaluation,experiments,models,api}` and their tests. Focus (cite file:line for each finding):
- timestamps / timezones / calendar: day-count (calendar days / 365 is decided — check it is applied consistently, including expiry time-of-day and same-day expiry), date parsing, snapshot alignment;
- units: IV decimal vs vol points, moneyness/log-moneyness definitions, forward vs spot, rates/dividends handling in Black-76;
- missing/crossed/zero/locked quotes, bid/ask vs mid, stale quotes, duplicate handling, integer/float dtype traps;
- solver edge cases: bounds, deep ITM/OTM, tiny maturity, non-convergence, NaN propagation, `reprice_err`;
- surface construction: interpolation boundaries, cell-status semantics (observed/interpolated/extrapolated/missing), determinism and content hashing;
- leakage: any feature/scaler/selector that could see future data; walk-forward purge/embargo arithmetic; access-log reliability (GR-LEAK-05);
- reproducibility: seeds, ordering nondeterminism (dict/set/filesystem ordering, threading), hash stability across numpy/pandas versions (CORE_STATUS records tests passing on both numpy 1.26/pandas 2.1 and numpy 2.5/pandas 3.0 — check what could differ);
- API: error handling, input validation, contract vs `docs/architecture/API_CONTRACTS.md`;
- the two known import-direction violations (models→evaluation, validation→pricing) — assess, don't fix.
Also list the **exact Colab verification plan** (commands, working-dir, env, what each proves) for: backend suite, phase0 spike suite, foundation audit — the orchestrator will execute it.
Severity-rank findings (S1 critical … S4 nit). Mark each: Observed (static only) unless you can cite an existing executed result. Only propose fixes that are small, supported by evidence, and compatible with the existing architecture; anything larger goes under "Routed to others".
Deliverable also includes a **file-level change manifest** (proposed files, owner, conflict risk).
