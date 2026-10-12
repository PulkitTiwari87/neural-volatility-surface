## Summary
<!-- What changed and why. Reference requirement/decision IDs (FR-, SCI-, DATA-, UI-, NFR-, SEC-, DEC-, GR-). -->

**Phase:** <!-- F / 0 / 1 / 2 / 3 / 4 / 5 / 6 / 7 -->
**Related issue / decision / ADR:**

## Type
- [ ] Documentation only
- [ ] Code (module: …)
- [ ] Configuration
- [ ] Experiment / research result
- [ ] Decision (updates decision.md / ADR)

## Verification (paste real output; "not run" is acceptable if stated with reason)
- Commands run and results:
- Tests added/changed:
- Checks not run and why:

## Scientific integrity
- [ ] No fabricated data/results; synthetic data labelled `*.synthetic.*`
- [ ] No look-ahead leakage (chronological splits; preprocessing fit on training only; features available at origin) — or N/A
- [ ] Baselines included for any model claim; metrics report sample counts and missingness — or N/A
- [ ] Observed / interpolated / extrapolated / missing statuses preserved — or N/A
- [ ] IV failures stored as missing with reason (never fabricated) — or N/A
- [ ] Data mode labelled correctly (historical / delayed / latest available / real-time licensed)

## Guardrails
- [ ] Relevant `GR-*` rules are enforced by a test/check, or the gap is noted: …
- [ ] No automated trading, personalized advice, or profitability claims introduced

## Security & data governance
- [ ] No secrets, credentials, `.env`, or provider payloads committed
- [ ] No licensed/market data committed; licence implications considered
- [ ] External inputs validated; logs contain no secrets — or N/A

## Dependencies & scope
- [ ] No new dependency — or justification, alternatives, licence, size noted: …
- [ ] No open decision (see decision.md) silently resolved
- [ ] Change is within the active phase's scope and not in its out-of-scope list

## Documentation
- [ ] Affected docs updated (architecture / methodology / data dictionary / API contracts / guardrails)
- [ ] Status labels honest (nothing marked IMPLEMENTED/VALIDATED without code + evidence)
- [ ] CHANGELOG.md updated
- [ ] KNOWN_LIMITATIONS.md updated if limitations changed
