# CLAUDE.md — Persistent instructions for Claude Code sessions

**Project:** Neural Volatility Surface Forecasting Lab (research-grade; **not** a trading product).
**Current state:** documentation scaffold plus **one disposable, synthetic-only Phase 0 spike** (`scripts/phase0_synthetic/`, standard library, not product code — [ADR-0003](docs/architecture/ADR/ADR-0003-phase0-spike-toolchain.md)). **`backend/src/volatility_lab` holds the research package (OptionsDX-format adapter, quote validation, Black-76 IV, constant-maturity surfaces, purged walk-forward, baselines, GPU-only MLP/GRU) that produced the owner-directed hosted-data experiments E-1/E-2 and H1-H6 ([docs/research/PHASE4_NEURAL_EVIDENCE_REVIEW.md](docs/research/PHASE4_NEURAL_EVIDENCE_REVIEW.md); the GRU ensemble beats persistence under the fixed-expiry label only, in H5/H6: formal verdict `holds_under_fixed_expiry_label_only`, not a general improvement, negative under the nearest-expiry label, no interpretable edge over the PCA-ridge baseline), plus a read-only stdlib research API (`api/`); `frontend/` holds the UI session's static viewer (no 3D, framework undecided).** Phase F (foundation) was accepted by the owner on 2026-10-19; Phases 0-5 are partial and no later gate is met ([IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)). Status in one line: synthetic feasibility spike = implemented and reproduced locally (synthetic data only); **real-data feasibility = pending** (provider terms, pricing and a permitted sample not obtained); **neural forecasting on real options data = implemented as GPU experiments on hosted SPY data of unverified licence; the only persistence-beating results (GRU, H5/H6) hold under the fixed-expiry label alone and are not a pre-registered general improvement; not validated**; synthetic inference audit = **CLOSED — NO-GO** (owner, 2026-10-13: statistical-method search stopped; no inferential or significance claims; not a Phase 0 pass); provider/market/audience/product-toolchain decisions = **open**; **Phase 0 = incomplete**. Never imply otherwise. Every component is `PLANNED` unless a status table says otherwise ([README.md](README.md#project-status)). Git operations (commit, push, branch, config) are the owner's alone — never perform them.
**Scope note:** a `CLAUDE.md` in a parent directory (`D:\Claude Code\`) belongs to an unrelated project ("Atlas": distributed compute, its own phase list). Its phases, DB rules and conventions **do not apply here**. Where the two conflict, this file wins for this repository. Generic habits that do carry over: smallest diff, inspect before editing, root-cause fixes, don't weaken tests.

---

## 1. Purpose and scope

Build an inspectable, reproducible workflow that constructs implied-volatility (IV) surfaces from options data, forecasts how they evolve, evaluates forecasts honestly against simple baselines, and visualizes everything in 2D/3D with data status visible. It is a research and education platform. **Out of scope:** automated trading, personalized advice, profitability claims, unlicensed data use ([PR.md §2](PR.md)).

Guiding principle (MP §26): *make every forecast inspectable, every experiment reproducible, and every limitation visible.*

## 2. Required reading order (read only what the task needs, but in this order)

1. This file.
2. [guardrails.md](guardrails.md) — the enforceable rules (always).
3. [NEURAL_VOLATILITY_SURFACE_FORECASTING_LAB_MASTER_PLAN.md](NEURAL_VOLATILITY_SURFACE_FORECASTING_LAB_MASTER_PLAN.md) — baseline spec, **read-only, never edit**.
4. [PR.md](PR.md) — requirement IDs (`FR/SCI/DATA/UI/NFR/SEC`).
5. [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) — find the current phase, its scope, exit gate, and **out-of-scope** list.
6. [decision.md](decision.md) — which choices are still open.
7. [architecture.md](architecture.md), then the topic doc from the canonical-location table in [docs/README.md](docs/README.md).

Do not read the whole docs tree by default. Follow links from the phase you are working on.

## 3. Source-of-truth order (when sources disagree)

1. Existing, tested code (once any exists) — then verify it against docs and fix the doc or the code deliberately.
2. [decision.md](decision.md) / ADRs for decided items.
3. [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md), [PR.md](PR.md), [guardrails.md](guardrails.md).
4. [architecture.md](architecture.md) and `docs/`.
5. Master plan (baseline intent).
6. Your assumptions — **last**; label them `ASSUMPTION` and surface them.

Guardrails and the master plan's "must not" statements are never overridden by convenience.

## 4. Architecture boundaries

Layers (detail in [architecture.md](architecture.md)): ingestion → raw store → validation → alignment → pricing/IV → surfaces → features/datasets → models → evaluation → experiments/forecast store → API → frontend.

- Dependencies point **downstream only** (e.g., `surfaces` may import `domain` and `pricing`; `pricing` must not import `surfaces`). `domain/` has no I/O. Only `storage/` touches persistence; only `ingestion/` touches providers; only `api/` handles HTTP.
- Business/scientific logic never lives in API handlers or UI components.
- The frontend never trains models, never holds provider credentials, and never computes IV or surfaces — it displays backend outputs ([guardrails.md](guardrails.md) PROD/SEC).
- Keep each module independently testable with explicit input/output contracts.
- Backend package: `backend/src/volatility_lab/<module>/`. Mirror modules in `backend/tests/{unit,integration,scientific}`.

## 5. Open decisions — do not pre-empt

The following are **not decided** ([decision.md](decision.md)): market/underlying, data provider, snapshot frequency, pricing model, moneyness/maturity convention, grid & interpolation, backend framework, frontend/3D stack, storage formats, experiment tracking, forecast representation, neural architecture, deployment, software licence, Python toolchain.

- Do **not** add a dependency, manifest, lockfile, framework scaffold or provider adapter that silently decides one of these.
- If a task needs a decision, run/propose the smallest feasibility experiment, record the result in `decision.md` (and an ADR when decided), then proceed.
- `PROPOSED` ≠ approved. Treat proposals as hypotheses.

## 6. Repository conventions

- Status labels everywhere: `PLANNED`, `PROPOSED`, `IN_PROGRESS`, `IMPLEMENTED`, `VALIDATED`, `BLOCKED`, `DEFERRED`. `IMPLEMENTED` requires code merged and tested; `VALIDATED` requires scientific/acceptance evidence recorded. Documentation existing is **not** implementation.
- Stable IDs: `FR-`, `SCI-`, `DATA-`, `UI-`, `NFR-`, `SEC-` ([PR.md](PR.md)); `DEC-` ([decision.md](decision.md)); `GR-` ([guardrails.md](guardrails.md)); `ADR-NNNN`. Reference IDs instead of copying text.
- **One canonical location per topic** ([docs/README.md](docs/README.md)). Link; don't duplicate.
- Config lives in `configs/` (versioned, no secrets). Real data never goes in Git. Synthetic fixtures are named `*.synthetic.*` and say so.
- Units: store IV as **decimal** (0.20 = 20%); label "vol points" only at display/reporting boundaries and state which. Times: UTC internally with explicit source timezone preserved; dates as ISO-8601.
- Keep diffs small and reviewable; no drive-by refactors or reformatting.

## 7. Quantitative research guardrails (summary — [guardrails.md](guardrails.md) is binding)

- A neural model is **never presumed better** than persistence/regression. No "improvement" claim without out-of-sample, chronologically-split evidence with sample counts.
- Never fabricate market data, IV, metrics, results, citations, provider access or test outcomes. If IV solving fails, store missing + reason.
- Observed, interpolated, extrapolated and missing surface values stay distinguishable end-to-end.
- Report metrics by maturity, moneyness, period, regime — never a single aggregate score alone.
- Label backtests as backtests; never imply live/real-time without provider latency known ([PR.md](PR.md) DATA-003).

## 8. Data provenance requirements

Every dataset, surface, feature table, model and forecast must be traceable to: source & snapshot, ingestion timestamp, processing version, quote-filter config, pricing/IV method & assumptions, coordinate/grid/interpolation version, feature version, split windows, model config & seed, evaluation code version (SCI-013). Raw data is immutable; corrections create a new version. Exclusions are recorded with reasons and counts — never silently dropped. Respect licence terms for storage, display, export.

## 9. Time-series leakage prevention (non-negotiable)

- Split chronologically; never random-shuffle dates for primary evaluation.
- Fit scalers/imputers/selectors **only** on training-eligible data; re-fit inside each walk-forward fold.
- Features may use only information available at the forecast origin; label construction must not leak into features.
- Hyper-parameter and model selection use validation periods only; the final test period is touched once, after selection is frozen.
- Any change to splitting, features, or preprocessing needs a leakage test (see `backend/tests/scientific/`).

## 10. Testing requirements

- Scientific/architectural changes require tests ([docs/engineering/TESTING_STRATEGY.md](docs/engineering/TESTING_STRATEGY.md)): unit, integration, scientific (synthetic known-answer), end-to-end.
- IV and surface code is verified against synthetic prices with known generating volatility.
- Test failure cases (solver non-convergence, crossed quotes, empty/partial data), not just happy paths.
- Fix root causes. Never weaken, skip, or delete a test to get green.
- **Never state that tests/checks passed unless you ran them and saw the output.** Report failures verbatim. If a check could not be run, say so and why.

## 11. Security and secrets

- Never commit secrets, API keys, tokens, `.env`, provider responses, or licensed data. Only `.env.example` (placeholders) is tracked.
- Credentials are server-side only; never in frontend code, logs, error messages, or fixtures.
- Validate all external input (API params, files, provider payloads). Authz/rate limits before exposing expensive operations.
- No destructive commands (`rm -rf`, force push, history rewrite, dropping data) without explicit user authorization. Don't run commands that call paid or external APIs unless the task authorizes it.

## 12. Documentation maintenance (required)

Update the relevant doc **in the same change** when you alter: architecture or module boundaries ([architecture.md](architecture.md), `docs/architecture/`), research methodology or scientific assumptions (`docs/research/`), data schemas ([docs/data/DATA_DICTIONARY.md](docs/data/DATA_DICTIONARY.md)), API contracts ([docs/architecture/API_CONTRACTS.md](docs/architecture/API_CONTRACTS.md)), guardrails, or decisions. Also: append to [CHANGELOG.md](CHANGELOG.md), update status labels in [README.md](README.md), and keep [docs/research/KNOWN_LIMITATIONS.md](docs/research/KNOWN_LIMITATIONS.md) honest. Always distinguish **implemented** behaviour from **planned** behaviour in prose.

## 13. Dependency minimization

Standard library / existing dependency first. A new dependency needs: the need, alternatives considered, licence, maintenance status, size/transitive cost, and a note in the PR (and `decision.md` if it settles an open decision). No microservices, queues, orchestration, registries, hosted ML platforms, or paid services without a documented need.

**Compute policy (owner, 2026-10-12; [decision.md](decision.md) DEC-015):** neural training, validation, evaluation and inference run only on a verified, explicitly selected GPU (Google Colab GPU, or the local NVIDIA RTX 4060 8 GB), log device/memory/framework/CUDA versions/seed/config, and raise an error instead of falling back to CPU. The standard-library Phase 0 tests and seeded Monte Carlo are unchanged and are **not** ported to CUDA without a separate documented, approved decision. The local PyTorch is currently a CPU-only build, so local neural runs are blocked until the owner approves a CUDA install.

## 14. Working method

1. Identify the current phase and its exit gate in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md). Implement only that phase; list out-of-scope items you notice rather than doing them.
2. **Inspect existing code and docs before editing**; reuse what exists; never overwrite a file you haven't read; merge, don't replace.
3. Smallest implementation that satisfies the requirement IDs; no speculative abstractions.
4. Add/adjust tests with the change; run the targeted tests, then the broader suite as warranted.
5. Update docs/status/changelog. Re-read your diff for leakage, fabricated numbers, and unlabeled assumptions.
6. Report: what changed, what was verified (with actual commands/results), what wasn't, open questions.

## 15. Definition of done (a change is done only when all hold)

- [ ] Satisfies stated requirement IDs and the phase's acceptance criteria.
- [ ] Tests added and **actually run**; results reported accurately.
- [ ] Relevant guardrails ([guardrails.md](guardrails.md)) are enforced by a test or check, or the gap is recorded.
- [ ] No leakage, fabricated data, secrets, or unapproved dependencies introduced.
- [ ] Docs, status labels, [CHANGELOG.md](CHANGELOG.md) updated; implemented vs planned clearly separated.
- [ ] Limitations and assumptions recorded.
- [ ] Phase exit gate not claimed unless its evidence exists.

## 16. Prohibited shortcuts

- Presenting synthetic or interpolated data as market data; "filling" IV when solving fails.
- Random train/test split of time series; fitting preprocessing on all data; peeking at the test period for selection.
- Reporting only a flattering aggregate metric, best seed, or best period.
- Claiming calibrated uncertainty without coverage evidence; claiming "live" for delayed data.
- Marking items implemented/validated because docs exist; editing the master plan to fit the work.
- Fabricating citations, benchmarks, provider capabilities, or licence terms — write `NEEDS RESEARCH` instead.
- Adding frameworks/libraries "just in case"; building the UI or API ahead of the data/science phases.
- Skipping or loosening a guardrail test to unblock progress.
