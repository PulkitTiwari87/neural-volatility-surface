# scripts/

**Status:** one disposable spike. Reserved for operational helpers (benchmarks, maintenance, one-off utilities) that are not part of the library. Scripts must default to dry-run for anything destructive, never embed secrets, and be documented in [docs/operations/LOCAL_DEVELOPMENT.md](../docs/operations/LOCAL_DEVELOPMENT.md). Benchmarks used for decisions (DEC-008/009) are recorded in the corresponding ADR with environment details.

| Path | What it is |
|---|---|
| [`phase0_synthetic/`](phase0_synthetic/README.md) | **SYNTHETIC** Phase 0 feasibility spike (Python standard library only; 57 `unittest` tests). Not product code; no real data. Protocol: [PHASE0_FEASIBILITY_PLAN §9](../docs/research/PHASE0_FEASIBILITY_PLAN.md); results: [PHASE0_SYNTHETIC_RESULTS](../docs/research/PHASE0_SYNTHETIC_RESULTS.md) |
