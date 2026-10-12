# Data Versioning

**Status:** PROPOSED · **Canonical for:** versioning scheme, identity, supersession, reproducibility of data artifacts · **Source:** MP §8.9, §19 · **Related:** [STORAGE_DESIGN](../architecture/STORAGE_DESIGN.md), [DATA_FLOW](../architecture/DATA_FLOW.md), DATA-004/007, SCI-013

## 1. Goals
Any result can be traced to the exact data, configuration and code that produced it; corrections never silently change history (MP §19).

## 2. What is versioned
| Artifact | Identity depends on |
|---|---|
| Raw snapshot | Source, query parameters, retrieval time, content hash |
| Normalized/validated quotes | Raw snapshot ID, normalizer version, quote-policy hash |
| Assumption set | Rate/dividend/day-count/calendar content |
| IV observation set | Aligned quotes ID, assumption-set ID, pricing/solver version & tolerances |
| Surface snapshot / set | IV set ID, grid ID, convention version, interpolation method+parameters+version |
| Feature table / dataset | Surface-set ID(s), feature-catalog version, split definition |
| Forecast set | Dataset ID, model version, config hash, seed, `forecast_kind` |
| Evaluation report | Forecast set ID, realized surface set ID, metric config, evaluation code version |
| Experiment record | All of the above + environment |

## 3. Identity scheme (proposed)
- **Content-derived ID**: hash over canonical serialization of (content or input IDs + parameters + code version). Deterministic stages must reproduce the same ID from the same inputs; non-deterministic ones (e.g., stochastic training) record seed and a separate artifact hash.
- **Human labels** (e.g., `surfaces/2026Q4-draft`) are aliases to IDs, never identities.
- **Code version:** commit hash once under version control; before that, a recorded manual version string.

## 4. Rules
1. **Immutable:** published versions are never edited. Fixing a bug or correcting a source creates a new version with a `supersedes` link and a reason.
2. **Pinned:** every downstream artifact records exact upstream IDs; "latest" aliases exist for convenience only and are never stored in results.
3. **Reproducible:** `rebuild(version_id)` from upstream IDs + config reproduces the same ID (deterministic stages) or a documented tolerance (stochastic stages).
4. **Visible:** the UI shows versions in the context bar and provenance card.
5. **Provider restatements:** if a provider changes historical values, ingest as a new raw version and mark which experiments used the old one.
6. **Deprecation:** superseded versions remain readable until the retention policy allows deletion; experiments referencing them stay reproducible or are flagged `source_unavailable`.

## 5. Dataset versioning specifics
A dataset version fixes: included origins, features and their versions, masks, split windows/gaps, fold definitions, scaler-fit policy (not fitted values — those are per fold artifacts). Changing any of these ⇒ new dataset ID.

## 6. Tests
Determinism (same inputs ⇒ same ID); change-sensitivity (any input/config change ⇒ different ID); supersession preserves old content hash; lineage walk completes on synthetic dataset; rebuild reproduces stored artifact.

## 7. Open items
Hash algorithm and serialization format; storage of IDs in the metadata store (DEC-009); tool for experiment/artifact versioning (DEC-010).
