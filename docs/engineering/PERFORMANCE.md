# Performance

**Status:** PROPOSED — **no performance targets are asserted**; targets are set from measurements after feasibility spikes. · **Source:** MP §16, §19, §20, §22 · **Related:** NFR-004/005/010, DEC-008/009, [STORAGE_DESIGN](../architecture/STORAGE_DESIGN.md)

## 1. Principle
Measure first, optimize second. Correctness, reproducibility and clarity outrank speed. Avoid premature optimization and infrastructure (YAGNI).

## 2. Expected hot spots (hypotheses to measure)
| Area | Why it may matter | First measurement |
|---|---|---|
| Ingestion volume | Historical chains can be large | Rows/day, raw size, fetch duration (sample) |
| IV solving | Many contracts × many dates | Contracts/second for the solver on synthetic grid; scaling with vectorization |
| Surface construction | Interpolation over many snapshots | Time per snapshot |
| Dataset assembly & walk-forward | Many folds × refits | End-to-end time for baselines |
| Neural training | Model/GPU needs depend on sample count | Time per epoch on Phase 3 dataset; hardware recorded |
| Storage queries | Date-range scans; lineage lookups | Benchmarks in DEC-009 spike |
| Frontend 3D rendering | Large grids, interactivity | Frame time/load time on target grid in DEC-008 spike |
| API | Repeated surface queries | Latency with/without cache |

## 3. Strategies (apply only when measurement justifies)
- Vectorize numerics; avoid per-contract Python loops in hot paths if profiling shows need.
- Incremental/partitioned processing keyed by version IDs; skip rebuild if output ID exists.
- Cache immutable results by version ID (NFR-010); never cache "latest" aliases.
- Downsample 3D geometry with visible factor and a full-resolution table (NFR-005).
- Asynchronous jobs with resource limits (NFR-004).
- Lazy loading/pagination of large lists; avoid blocking the UI.

## 4. Benchmarks and budgets
Spikes (throwaway): storage benchmark (DEC-009); rendering benchmark (DEC-008). Budgets (`TBD`) are recorded here as: metric, dataset size, hardware, method, target, date. Regressions beyond a budget block the relevant gate once a budget exists.

## 5. Reproducibility vs speed
Performance optimizations must not change numerical results beyond documented tolerances; deterministic stages stay bit-reproducible unless an ADR relaxes it; non-deterministic accelerations (e.g., GPU kernels) are recorded in run metadata.

## 6. Resource limits
Jobs declare and enforce memory/time limits; public deployments cap request sizes and concurrent jobs (SECURITY).

## 7. Validation
Benchmarks are reproducible scripts (stored under `scripts/` when created) with recorded environment; before/after measurements accompany performance PRs.
