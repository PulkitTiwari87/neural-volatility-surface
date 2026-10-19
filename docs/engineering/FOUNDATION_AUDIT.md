# Phase F foundation audit (2026-10-16)

**Status:** mechanical audit executed and passed; **owner review not yet given — Phase F stays `IN_PROGRESS`.** The assistant cannot accept its own audit (IMPLEMENTATION_PLAN Phase F exit gate: "audit report accepted by the project owner"). Run by `scripts/foundation_audit.py` (standard library, read-only; negative-controlled against a deliberately broken tree: it catches a broken link, undefined IDs, a planted secret-like string and missing files).

## 1. Result of the mechanical checks

Command, from the repository root: `python scripts/foundation_audit.py` (exit code 0, `hard_failures: false`).

| Check | Result |
|---|---|
| Required files (12 root/docs files) and directories (19) exist | none missing; none trivial (< 200 bytes) |
| Relative Markdown links (code spans/fences excluded) | 664 checked on the first run; 712 after this session's documents were added; 0 broken both times (anchors not checked) |
| Requirement IDs `FR/SCI/DATA/UI/NFR/SEC` referenced vs defined in PR.md | 72 defined, 0 undefined references |
| `DEC-` IDs referenced vs defined in decision.md | 15 defined, 0 undefined |
| `GR-` IDs referenced vs defined in guardrails.md | 45 defined, 0 undefined |
| `ADR-` IDs referenced vs files in `docs/architecture/ADR/` | 3 defined, 0 undefined |
| Secret-like strings in repository text files (keys, tokens, private-key headers) | 0 hits |
| Files tracked by Git under `data/` or `artifacts/` besides README/.gitkeep | 0 |
| `.env` ignored / `.env*` files tracked | ignored: yes; tracked: 0 |
| Decision register | 15 decisions, **0 `DECIDED`** (matches Phase F acceptance "all undecided") |
| Dependency manifest or lockfile tracked or present (separate check) | none (`requirements*`, `pyproject.toml`, `package*.json` not found) |

The required-file list is the assistant's reading of the foundation structure (the original foundation brief is not in the repository); it is a list of what the audit checks, not an independent definition of Phase F.

## 2. Phase F acceptance criteria, one by one

| Criterion (IMPLEMENTATION_PLAN Phase F) | Status | Note |
|---|---|---|
| All required files exist and are non-trivial | PASS (mechanical) | §1 |
| PR.md maps to the master plan | NOT AUDITED | No mechanical check exists; a content review is needed |
| Decision register shows all 15 decisions undecided | PASS | §1; statuses are `PROPOSED`, `NEEDS RESEARCH` or `OPEN` |
| No code, dependency manifest, data or results | **SUPERSEDED, not met literally** | By owner direction the repository now holds the Phase 0 spike (`scripts/phase0_synthetic`), the E-1/E-2 research package (`backend/src/volatility_lab`), a read-only API, a static viewer, generated notebooks and results documents. No dependency manifest/lockfile and no tracked data exist. This criterion belonged to the scaffold-only moment and should be recorded as superseded by the owner rather than silently ignored |
| Exit gate: audit accepted by the owner; Phase 0 may start | **NOT MET** | Phase 0 already started on the owner's instruction (2026-10-12) without a recorded acceptance of this audit |

## 3. Findings that need the owner

1. **No recorded owner acceptance of Phase F.** Either accept this audit (and record it in [MILESTONES](../planning/MILESTONES.md)) or state that Phase F is superseded by the owner-directed Phase 0/E-1 work.
2. **`CLAUDE.md` line 4 is stale**: it says "there is no API and no frontend code", but a read-only stdlib API (`api/`), a 2D static viewer (`frontend/index.html`) and their tests exist ([IMPLEMENTATION_MATRIX](IMPLEMENTATION_MATRIX.md) §8). `CLAUDE.md` is the owner's instruction file, so the assistant did not edit it. [MODEL_HANDOFF](../../dashboard-design/MODEL_HANDOFF.md) §3.1 raised the same point.
3. **No CI exists.** `.github/workflows/` is empty. A workflow that installs the packages would choose a Python version and install route, which touches the open toolchain decision DEC-015; see the proposal in [CORE_STATUS](CORE_STATUS.md) §5.
4. **Guardrail enforcement is partial**: guardrails whose check now exists are listed in [CORE_STATUS](CORE_STATUS.md) §4; GR-DATA-05 holds for the surface layer but not for a UI test (none exists); GR-SEC-01 secret scanning exists only as this script's local check, not in CI.

## 4. What this audit cannot show

It checks presence and consistency, not truth: it cannot tell whether a document's claim is correct, whether PR.md faithfully covers the master plan, or whether the status tables are honest. Those remain review items. It does not look inside the dashboard session's `dashboard-design/` or `frontend/` files beyond link, ID and secret checks.
