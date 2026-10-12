# Configuration

**Status:** PROPOSED (design only; nothing reads configuration yet) · **Source:** MP §20, §22 · **Canonical for:** configuration principles, layers, and the planned variable catalogue · **Related:** NFR-007, SEC-001, [`.env.example`](../../.env.example), [configs/README](../../configs/README.md), [SECURITY](../engineering/SECURITY.md)

## 1. Principles
1. **Separate secrets from configuration.** Secrets come from environment/secret store only; configuration files are versioned and contain no secrets.
2. **Typed and validated** at startup; fail fast with clear, secret-free messages.
3. **Everything that affects results is versioned config** (quote policy, pricing/solver settings, grid & interpolation, features, models, evaluation) and its hash is stored in run records (SCI-013).
4. **Separate frontend and backend configuration**; the frontend receives only non-secret public settings (NFR-007).
5. **Defaults are safe** (local-only, no external calls, debug off).

## 2. Layers (precedence low → high)
1. Code defaults (safe, minimal) → 2. `configs/**` versioned files (experiment and pipeline settings) → 3. Environment variables (deployment/secrets/paths) → 4. Explicit CLI/job parameters (recorded).

## 3. Planned directories (`configs/`)
| Directory | Holds |
|---|---|
| `configs/data/` | Provider-independent ingestion options, quote policy variants, assumption sets, calendar refs |
| `configs/features/` | Grid definitions, coordinate convention, feature catalog selections and parameters |
| `configs/models/` | Model hyperparameters, seeds policy |
| `configs/evaluation/` | Splits, gaps, folds, regimes, metric settings, success criteria |

No config files exist yet.

## 4. Environment variables (planned; see `.env.example`)
| Variable | Purpose | Secret? |
|---|---|---|
| `VOLLAB_ENV` | development / test / production | no |
| `VOLLAB_DATA_DIR`, `VOLLAB_ARTIFACTS_DIR`, `VOLLAB_EXPERIMENTS_DIR` | Paths | no |
| `VOLLAB_PROVIDER_NAME`, `VOLLAB_PROVIDER_BASE_URL` | Provider selection (DEC-002) | no |
| `VOLLAB_PROVIDER_API_KEY` | Provider credential | **yes** |
| `VOLLAB_API_HOST`, `VOLLAB_API_PORT` | API binding | no |
| `VOLLAB_API_AUTH_SECRET` | API auth secret (when needed) | **yes** |
| `VOLLAB_LOG_LEVEL` | Logging | no |

Names are provisional and will be reconciled with the implemented config module; `.env.example` must stay in sync (check at review).

## 5. Rules
- Only `config` reads the environment; other modules receive config objects.
- Config objects are immutable; a stable hash is derived from canonical serialization.
- Unknown keys are rejected; missing required keys fail startup.
- Changing a result-affecting setting yields a new artifact version, never an in-place change.
- Production secrets are injected by the deployment platform (DEC-013), never baked into images or repository.

## 6. Validation
Schema tests for each config type; test that secrets are absent from serialized/logged config; hash determinism; `.env.example` ↔ config schema consistency check.
