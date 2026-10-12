# Contributing

**Status:** PROPOSED. Applies to humans and AI agents alike. Read [CLAUDE.md](CLAUDE.md) and [guardrails.md](guardrails.md) first.

## Before you start

- **Licence:** the software licence is undecided ([DEC-014](decision.md)). Until it is decided, external contributions are not accepted; internal work proceeds under the owner's direction.
- **Version control:** a Git repository exists in this folder but has **no commits**. It was not created by the foundation run (which made no Git changes), and files are currently staged by something outside it. The first commit is the owner's decision. Branching/commit conventions below apply from then on.
- Find the current phase and its scope in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md). Work outside the active phase needs an explicit decision.

## Ground rules

1. **Scientific integrity first:** no fabricated data/results; no leakage; baselines before neural claims; honest labels ([guardrails.md](guardrails.md)).
2. **Inspect before editing.** Read existing files; merge rather than overwrite.
3. **Smallest change** that satisfies the requirement IDs; no speculative abstractions; no unapproved dependencies.
4. **Tests accompany scientific/architectural changes** and must actually be run; paste the relevant output in the PR.
5. **Docs move with code:** update architecture, research methodology, data schemas, API contracts, status tables, and [CHANGELOG.md](CHANGELOG.md) in the same change.
6. **No secrets, no licensed data, no large artifacts** in commits. Use `.env.example` for placeholders. Synthetic fixtures are named `*.synthetic.*`.

## Workflow

1. Open an issue (bug or feature templates in `.github/ISSUE_TEMPLATE/`). For architectural or scientific choices, use [FEATURE_PROPOSAL_TEMPLATE](docs/templates/FEATURE_PROPOSAL_TEMPLATE.md) and, if a decision is involved, add/update an entry in [decision.md](decision.md) and an ADR ([template](docs/architecture/ADR/ADR-0001-template.md)).
2. Branch from the main line: `feat/<id>-short-name`, `fix/<id>-short-name`, `docs/<short-name>`, `exp/<experiment-id>` (names are a proposal).
3. Commit in small logical steps. Message format (proposal): `<area>: <imperative summary>` + body explaining *why*; reference requirement/decision IDs (e.g., `pricing: reject out-of-bound prices (FR-007, GR-QNT-01)`).
4. Open a PR using the template. Every checkbox must be answered honestly (N/A with reason is acceptable).
5. Review focuses on: guardrail compliance, leakage, provenance, status honesty, test evidence, doc updates.

## Experiments

Use [EXPERIMENT_TEMPLATE](docs/templates/EXPERIMENT_TEMPLATE.md). State the hypothesis and success criteria **before** running; record data/feature/model versions, seeds, windows, baselines, metrics with sample counts, results (including negative), and limitations. Never edit a published record to change its outcome; add a new version.

## Reporting problems

Use the bug template; include data/dataset/model versions and a minimal synthetic reproduction. **Do not attach licensed data or credentials.** Security issues: do not open a public issue; contact the owner privately (channel to be defined before any public release; see [SECURITY](docs/engineering/SECURITY.md)).

## Style

See [CODING_STANDARDS](docs/engineering/CODING_STANDARDS.md) (formatters/linters are selected with DEC-015) and [`.editorconfig`](.editorconfig).
