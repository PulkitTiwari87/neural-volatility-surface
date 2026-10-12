# configs/

**Status:** PLANNED — no configuration files exist yet. Versioned, **secret-free** configuration for pipelines and experiments: `data/` (ingestion, quote policy, assumption sets), `features/` (grid, conventions, feature selections), `models/` (hyperparameters), `evaluation/` (splits, folds, regimes, metrics, success criteria). Everything that affects results lives here and is hashed into run records. See [docs/operations/CONFIGURATION.md](../docs/operations/CONFIGURATION.md). Secrets belong in the environment, never here.
