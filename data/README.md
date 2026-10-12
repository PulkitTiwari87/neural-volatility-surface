# data/

**Status:** PLANNED — placeholders only. **Contents of this directory are git-ignored** (see `.gitignore`). **Never commit market data, vendor exports, or credentials.**

| Directory | Purpose |
|---|---|
| `raw/` | Immutable, source-faithful snapshots (write-once; licence-dependent) |
| `interim/` | Scratch intermediate outputs; safe to delete |
| `processed/` | Versioned derived datasets (validated quotes, IV, surfaces, features) |
| `external/` | Reference data (calendars, rates) with licence tags |
| `samples/` | Tiny **synthetic** fixtures only, named `*.synthetic.*` and labelled as synthetic |

Rules and layout: [docs/data/DATA_GOVERNANCE.md](../docs/data/DATA_GOVERNANCE.md), [docs/architecture/STORAGE_DESIGN.md](../docs/architecture/STORAGE_DESIGN.md), [docs/data/DATA_VERSIONING.md](../docs/data/DATA_VERSIONING.md). The physical layout may change with DEC-009.
