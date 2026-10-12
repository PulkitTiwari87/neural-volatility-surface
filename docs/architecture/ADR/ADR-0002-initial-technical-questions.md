# ADR-0002: Initial technical questions are open and resolved by feasibility evidence

- **Status:** Proposed (a *process* decision only — it decides **how** to decide, not **what** to choose; becomes Accepted when the project owner confirms)
- **Date:** 2026-10-12
- **Decision register entry:** DEC-001 … DEC-015 ([decision.md](../../../decision.md))
- **Deciders / responsible role:** Project owner (to confirm on review)
- **Affected:** all phases; [IMPLEMENTATION_PLAN](../../../IMPLEMENTATION_PLAN.md)

## Context
The master plan deliberately leaves the market, provider, pricing model, grid, interpolation, frameworks, storage, tracking, architecture and deployment undecided (MP §2, §6, §10, §16, §18, §19). The foundation brief forbids silently selecting any of them. Early commitment risks building around a data source that cannot be licensed, or around infrastructure the data volume does not justify.

## Options considered
1. **Decide all technical choices now** from familiarity. Fast, but unsupported by evidence; high rework risk.
2. **Decide lazily as code demands.** Cheap short-term; produces implicit, undocumented decisions and inconsistent conventions.
3. **Keep a decision register; resolve each by the smallest feasibility experiment at the phase that needs it; record outcomes as ADRs.** (chosen)

## Evaluation criteria
Evidence quality, reversibility, effort, consistency with MP, protection against hidden assumptions.

## Evidence
Dependencies between decisions are acyclic (see below). Data-related decisions gate everything and are resolved first (Phase 0). Stack decisions are independent of the science and are resolved by throwaway spikes.

## Decision
1. All 15 items in decision.md remain `OPEN`/`NEEDS RESEARCH`/`PROPOSED` until an ADR with evidence sets them `DECIDED`.
2. Resolution order and mechanism:

| Decision | Resolved in | Mechanism |
|---|---|---|
| DEC-001, 002, 003 | Phase 0 | Data-source assessment + licence review + sample extract |
| DEC-015 | Phase 0 | Clean-machine install test of candidate toolchains |
| DEC-004, 005 | Phase 0 (draft) → Phase 2 (final) | Sensitivity study on sample/synthetic data |
| DEC-009 | Phase 1 start | Storage benchmark on synthetic data (spike) |
| DEC-006 | Phase 2 | Interpolation/grid comparison on real sample |
| DEC-010, 011 | Phase 3 | Baseline results; reproduce-from-record test |
| DEC-012 | Phase 4 | Baselines + multi-seed MLP |
| DEC-007, 008 | Phase 5 start (spikes may run earlier) | API spike; 3D/2D rendering + accessibility prototype |
| DEC-013 | Phase 5 exit | Licence outcome + job profile + audience |
| DEC-014 | Before public release | Owner decision + dependency licence audit |

3. `PROPOSED` recommendations are hypotheses for those experiments.
4. Spikes are throwaway; only findings are recorded.

## Consequences
Positive: decisions are evidence-backed and auditable; no hidden lock-in. Negative: some early work (e.g., storage) needs a minimal provisional choice with a documented migration path; Phase 0 carries more research than a typical project start.

## Guardrail and compliance check
Supports GR-ENG-01/02 (no speculative abstractions / unapproved dependencies) and CLAUDE.md §5.

## Review trigger
A decision proves unresolvable by its planned mechanism; the owner changes the resolution order.

## Follow-up actions
- [x] decision.md created
- [ ] Phase 0 begins with DEC-001/002/003
