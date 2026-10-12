# backend/

**Status:** PLANNED — directory placeholders only; **no code, manifest, or lockfile** (toolchain undecided: DEC-015).

Layout: `src/volatility_lab/{config,domain,ingestion,validation,pricing,surfaces,features,datasets,models,evaluation,experiments,storage,api,observability}` and `tests/{unit,integration,scientific,fixtures}`.

Module responsibilities, dependency direction, and what each module must not do: [architecture.md](../architecture.md) §3–§4. Testing approach: [docs/engineering/TESTING_STRATEGY.md](../docs/engineering/TESTING_STRATEGY.md). Phase in which each module is introduced: [docs/architecture/SYSTEM_OVERVIEW.md](../docs/architecture/SYSTEM_OVERVIEW.md) §3. Empty `.gitkeep` files keep directories in version control; do not add code until the phase that introduces it begins.
