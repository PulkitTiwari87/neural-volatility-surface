# Next Steps — Phase 0 to a go/no-go on the first real-data pipeline

**Status:** PROPOSED · **Date:** 2026-10-12 · Phase 0 is **incomplete**. Real-data feasibility is pending; no neural model has been trained or validated. Nothing below may be done without the owner's approval: **no contacting providers, creating accounts, accepting terms, buying data, or using real market data.** Git is the owner's alone. Related: [PHASE0_AUDIT](PHASE0_AUDIT.md), [PHASE0_FEASIBILITY_PLAN](PHASE0_FEASIBILITY_PLAN.md), [DATA_SOURCE_ASSESSMENT](../data/DATA_SOURCE_ASSESSMENT.md).

| # | Workstream | Concrete actions | Done when (evidence) | Owner approval needed |
|---|---|---|---|---|
| 1 | **Resolve scientific issues in the synthetic spike** | Finish audit A2/A3 (bootstrap coverage; 200-seed study) and record results in PHASE0_AUDIT §5; amend protocol tolerances (recovery tolerance vs matching tolerance; analytic-SD-based H-S6; invalid-world rule) **as dated amendments, keeping v1 outcomes**; refresh test counts in status docs (now 74) | Audit §5 complete; amended thresholds signed (Q-28) | Sign-off on amendments |
| 2 | **Finalize and review the Cboe questions** | Owner edits `docs/data/CBOE_LICENSING_QUESTIONS.md`, fills bracketed fields truthfully, decides addressee and individual-vs-firm status | Reviewed final text | Yes (before sending) |
| 3 | **Written clarification from Cboe** | Owner sends; log replies verbatim: derived IV surface fee liability (Q-16), display/publication/redistribution, applicable licences, price (Q-17), retention | Replies filed with the DEC-002 ADR | Yes |
| 4 | **Evaluate Databento as fallback** | Owner reads terms in a browser (Q-18); account-level cost estimate for one snapshot-minute per day; confirm CBBO-1m history under pay-as-you-go | Terms excerpt + cost estimate in the assessment | Yes (account, terms) |
| 5 | **Inspect a permitted real sample** | ≥ 20 dates chosen *before* looking (≥ 5 calm, ≥ 3 stressed, ≥ 2 consecutive pairs); only under terms that permit it | Dates + selection rule recorded; sample hashed, kept out of Git | Yes |
| 6 | **Measure real data** | Quote quality and exclusion rates, coverage, strike/expiry density, IV-solver failure rates, surface sparsity, per-contract timestamp gaps; test parity-forward (Q-06, Q-26) and the `observed` rule for fixed price strikes (Q-25) | Run record on real sample (labelled real, not committed) | Yes |
| 7 | **Revisit thresholds from observed variability** | Estimate *c* and ρ; set MVD density thresholds, minimum detectable improvement, power table | Thresholds frozen and dated before any model result | Sign-off |
| 8 | **Go/no-go on the first real-data pipeline** | Decide on DEC-001/002/003/015 ADRs, exposure level (Q-03) and spend | Phase 0 exit evidence in assessment §10.4 all present | Yes |

**Recommended next action:** workstream 1 (finish the audit) while the owner reviews and decides whether to send the Cboe email (workstreams 2–3).
