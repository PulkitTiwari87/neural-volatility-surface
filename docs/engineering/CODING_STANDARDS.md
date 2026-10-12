# Coding Standards

**Status:** PROPOSED (language-specific tooling selected with DEC-015/DEC-008; nothing enforced yet) · **Canonical for:** engineering conventions · **Related:** [CLAUDE.md](../../CLAUDE.md), [guardrails.md](../../guardrails.md) GR-ENG, [TESTING_STRATEGY](TESTING_STRATEGY.md)

## 1. Principles
1. **Simple and explicit over clever.** No speculative abstractions or frameworks; add a layer when ≥2 concrete callers or a test need exists (GR-ENG-01).
2. **Pure core, impure edges.** Science code (`pricing`, `surfaces`, `features`, `evaluation`) is deterministic and I/O-free; I/O lives in `ingestion`, `storage`, `api`.
3. **Make invalid states unrepresentable:** enums for statuses/flags, typed records with validation at boundaries, nullable only where meaning is "missing with reason".
4. **Failure is data in scientific paths** (status + reason), exceptions for programmer/IO errors.
5. **Dependencies are liabilities** — justify each (GR-ENG-02, CLAUDE.md §13).

## 2. Structure and boundaries
- Package `volatility_lab` under `backend/src/`; modules per [architecture.md](../../architecture.md) §3–§4; imports flow downstream only (architecture test).
- No module reads environment variables or files outside `config` / `storage` / `ingestion`.
- One time/maturity convention module; no ad hoc date arithmetic elsewhere (GR-QNT-05).
- No global mutable state; randomness via explicit seeded generators passed in.

## 3. Language-level conventions (apply once languages are fixed)
- **Python (assumed backend, DEC-015):** static type annotations on public functions; formatter + linter + type checker chosen and pinned with the toolchain; docstrings state units, conventions, and failure modes; vectorized numerics where it does not harm clarity.
- **Frontend (DEC-008):** typed language preferred; formatting/lint tooling pinned; accessibility lint rules on.
- Naming: domain terms from the [GLOSSARY](../project/GLOSSARY.md); units in names where ambiguity exists (`iv_decimal`, `iv_volpts`); status enums UPPER_SNAKE for solver, lower_snake for cell status per DATA_DICTIONARY.

## 4. Numerical code
- State units and conventions in docstrings; assert shapes/finite inputs at boundaries.
- Tolerances are named constants/config, never inline magic numbers.
- Compare floats with explicit tolerances in tests.
- No silent NaN propagation: NaN/inf inputs map to explicit statuses.
- Deterministic: set seeds; avoid nondeterministic ops without recording (and documenting tolerance).

## 5. Data handling
Timestamps timezone-aware, UTC internally; IV decimal; money with currency; IDs opaque. Never mutate input records; return new objects. No sentinel values for missing.

## 6. Errors and logging
Typed exceptions for unexpected failures; scientific failures as statuses; log with run/job IDs; redact secrets; do not log licensed payloads (see [OBSERVABILITY](OBSERVABILITY.md), [SECURITY](SECURITY.md)).

## 7. Configuration
Typed, validated config objects with hash; defaults documented; no secrets in config files; experiment configs live in `configs/` and are referenced by hash in run records.

## 8. Commits and reviews
Small, single-purpose changes; message format per [CONTRIBUTING](../../CONTRIBUTING.md); reviews check guardrails, leakage, provenance, tests, docs, status honesty.

## 9. Documentation in code
Comments explain *why*, assumptions and references (e.g., formula source); do not narrate the obvious. Public functions document inputs/outputs/failure statuses. Scientific choices link to the doc section or decision ID.

## 10. Validation
Formatter/linter/type-check/test commands to be listed in [LOCAL_DEVELOPMENT](../operations/LOCAL_DEVELOPMENT.md) once selected, and run in CI. Until tools exist, reviews enforce this document.
