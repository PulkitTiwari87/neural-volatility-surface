# Agent D — Quantitative Research and Evaluation (stages S3–S5 design)

Read `_COMMON.md` first. **Owned file:** `orchestration/reports/RESEARCH_DESIGN.md` (only). No training, no real data, no code execution.

Read: `docs/research/` (esp. `EVALUATION_PROTOCOL.md`, `FORECASTING_STRATEGY.md`, `PHASE4_NEURAL_EVIDENCE_REVIEW.md`, `PHASE0_FEASIBILITY_PLAN.md` §7 thresholds, `KNOWN_LIMITATIONS.md`, `PHASE2_SURFACE_COMPARISON.md`), `guardrails.md` (GR-LEAK, GR-MOD, GR-QNT), `backend/src/volatility_lab/{evaluation,experiments,models,features}` and their tests.

Task:
1. Audit the methodology (static): targets (fixed-expiry vs nearest-expiry label — the H5/H6 result flips sign between them; explain what each measures and which is defensible), baselines (persistence, rolling mean, ridge, PCA-ridge), walk-forward/purge/embargo, metrics (per maturity × moneyness × period × regime with n), skill definition, the pre-registered decision rule and "holds_under_*_label_only" verdicts. Identify look-ahead bias, leakage paths, inappropriate splits, multiple-comparison/forking-paths problems across H1–H6, unsupported claims in docs, weak comparisons, seed/selection issues.
2. State clearly what H1–H6 evidence is and is not (hosted data of withdrawn/unverified licence → unpublishable history; the owner waived re-verification). Do not cite it as validated evidence.
3. Design (not run) the experiment sequence for a *future authorized* real dataset: baseline experiments first, then neural. For each: hypothesis, pre-registered metric/threshold, split/fold requirements (minimum independent surfaces — use the owner-adopted MVD thresholds in PHASE0_FEASIBILITY_PLAN §7 as given, flag they are owner-adopted not evidence-based), leakage tests required, seeds, reporting tables, and the stop/no-go rule. Include the minimum evidence required before any model can be called useful, and what wording is allowed in each outcome.
4. Specify what can be done on **synthetic data only** meanwhile and what it can/cannot show (synthetic ≠ market evidence).
5. Treat US and India as separate studies (different calendars/liquidity/lot sizes/expiry cycles) — list the market-specific methodological issues; do not decide the market.
Distinguish *research design* from *experiments that have run* in every section.
