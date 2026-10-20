# Agent E — UI and End-to-End Integration (stage S6 design, S1 inspection)

Read `_COMMON.md` first. **Owned file:** `orchestration/reports/UI_INTEGRATION_REPORT.md` (only). **Do not edit `frontend/**` or `dashboard-design/**`** this wave (UI session owns them; report only). Do not start servers or open the viewer (that executes project code) — static inspection only.

Read: `frontend/` (all files), `backend/src/volatility_lab/api/{server,service}.py`, `docs/architecture/API_CONTRACTS.md` (esp. §8 gaps G1–G6), `dashboard-design/` (esp. `MODEL_HANDOFF.md`), `design.md` UA-01…UA-14, tests `backend/tests/unit/{test_api,test_api_contract,test_viewer_static}.py`, `scripts/make_synthetic_run.py`.

Task:
1. Map UI screens → API endpoints → backend modules → stored files. For each screen/feature decide: real functionality / placeholder / synthetic-only demo.
2. Contract mismatches between frontend field use and API payloads; loading, empty, error, invalid-input and missing-forecast states; origin/provenance/quality-status visibility (GR-DATA-04/05/07). Known finding to confirm or refute: viewer labels stored-run data "Live from run" (GR-DATA-07 reserves "live" for real-time licensed data).
3. Which UA-01…UA-14 journeys exist and what would be needed to execute each. Propose which can run in Colab (headless browser against the stdlib API on the Colab VM) vs need the owner's browser; give a concrete Colab E2E plan (steps, tool, expected assertions). Mark everything **Not run**.
4. Propose isolated fixes as diffs in the report (UI-owned files are routed to the UI session; API-semantics changes to core). No edits.
5. Confirm the scope decision (local research tool, no 3D, no framework, no auth/deployment) is respected by the code.
Never claim a journey passed.
