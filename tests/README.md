# tests/ (repository-level)

**Status:** PLANNED — no repository-level or product tests exist (the only tests are the spike's `unittest` suites in `scripts/phase0_synthetic/tests/`). `end_to_end/` (user journeys through API + UI), `regression/` (frozen synthetic scenarios for fixed defects, golden outputs), `fixtures/` (synthetic, labelled `*.synthetic.*`). Backend unit/integration/scientific tests live in `backend/tests/`. Strategy and the minimum scientific test set: [docs/engineering/TESTING_STRATEGY.md](../docs/engineering/TESTING_STRATEGY.md). Never include licensed data in fixtures.
