# scripts/

**Status:** one disposable spike. Reserved for operational helpers (benchmarks, maintenance, one-off utilities) that are not part of the library. Scripts must default to dry-run for anything destructive, never embed secrets, and be documented in [docs/operations/LOCAL_DEVELOPMENT.md](../docs/operations/LOCAL_DEVELOPMENT.md). Benchmarks used for decisions (DEC-008/009) are recorded in the corresponding ADR with environment details.

| Path | What it is |
|---|---|
| [`foundation_audit.py`](foundation_audit.py) | Read-only mechanical Phase F audit (required files, relative links, requirement/decision/guardrail/ADR IDs, secret-like strings, tracked data); result in [FOUNDATION_AUDIT](../docs/engineering/FOUNDATION_AUDIT.md) |
| [`phase2_surface_comparison.py`](phase2_surface_comparison.py) | Reproduces [PHASE2_SURFACE_COMPARISON](../docs/research/PHASE2_SURFACE_COMPARISON.md) on SYNTHETIC data (`--out` must be a new file) |
| [`phase0_synthetic/`](phase0_synthetic/README.md) | **SYNTHETIC** Phase 0 feasibility spike (Python standard library only; 145 `unittest` tests: 57 original + 37 audit regression + 18 A2d + 33 `chainpipe`). Not product code; no real data. Protocol: [PHASE0_FEASIBILITY_PLAN §9](../docs/research/PHASE0_FEASIBILITY_PLAN.md); results: [PHASE0_SYNTHETIC_RESULTS](../docs/research/PHASE0_SYNTHETIC_RESULTS.md) |
