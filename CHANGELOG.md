# Changelog

All notable changes are recorded here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) loosely; versioning scheme is `OPEN` (no releases exist). Entries must describe **actual** changes, not plans.

## [Unreleased]

### Added
- 2026-10-12 — Repository foundation scaffold (Phase F): directory structure; `README.md`, `CLAUDE.md`, `PR.md`, `architecture.md`, `decision.md`, `guardrails.md`, `design.md`, `IMPLEMENTATION_PLAN.md`, `CONTRIBUTING.md`; documentation set under `docs/`; GitHub PR/issue templates; `.gitignore`, `.editorconfig`, `.env.example`.
- 2026-10-12 — Baseline specification copied unmodified into the repository root: `NEURAL_VOLATILITY_SURFACE_FORECASTING_LAB_MASTER_PLAN.md`.

- 2026-10-12 — Phase 0 desk research: `docs/data/DATA_SOURCE_ASSESSMENT.md` rewritten with candidate combinations, graded evidence, licence analysis, cost findings and blockers; new `docs/research/PHASE0_FEASIBILITY_PLAN.md` (proposed MVD, success criteria, synthetic-sample spec, minimal feasibility experiment); `decision.md` DEC-001/002/003 updated to `PROPOSED` with findings (none decided); `docs/planning/OPEN_QUESTIONS.md` extended (Q-16…Q-24); status updates in README, IMPLEMENTATION_PLAN, MILESTONES, RISKS, DATA_GOVERNANCE, EVALUATION_PROTOCOL, docs index. No data downloaded, no accounts created, nothing purchased.

- 2026-10-12 — Phase 0 synthetic feasibility spike (owner-approved): `docs/architecture/ADR/ADR-0003-phase0-spike-toolchain.md` (Python 3.12.6, standard library only, nothing installed; Proposed, spike scope); DEC-015 spike note in `decision.md`; pre-registered protocol (`PHASE0_FEASIBILITY_PLAN.md` §9) written **before** code; `scripts/phase0_synthetic/` (Black-76, Brent IV solver with explicit statuses, seeded RW/AR synthetic chains with injected defects, validation, parity forward, surface construction, persistence and walk-forward factor-AR forecasters, block bootstrap, run records; **57 `unittest` tests pass**); `docs/research/PHASE0_SYNTHETIC_RESULTS.md` (results incl. 4 disclosed failure types and 7 protocol deviations); `docs/data/CBOE_LICENSING_QUESTIONS.md` (**draft email, not sent**); new open questions Q-25…Q-28; status updates in README, CLAUDE.md, IMPLEMENTATION_PLAN, MILESTONES, KNOWN_LIMITATIONS (L-18), LOCAL_DEVELOPMENT, scripts/README. All data synthetic; no real data, accounts, purchases or network access; no Git operations.

### Not added (intentionally) — as of the foundation scaffold; later entries above add the disposable synthetic spike only
- No product code, dependency manifest, lockfile, CI workflow, real market data, model weights, or real-market results. No `LICENSE` file (DEC-014 open).
