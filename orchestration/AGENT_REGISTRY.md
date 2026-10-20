# AGENT_REGISTRY

**Updated:** 2026-10-20. Launch prompts: [prompts/](prompts/) (all start with `_COMMON.md`). "Subagent" = real Claude Code Agent-tool subagent launched by the orchestrator; "Chat" = must be launched by the human in a separate conversation (no automatic cross-chat channel exists or is claimed — coordination is through these files only).

| Role | ID | Writable files | May do | Must not | Mode (this run) | Assignment |
|---|---|---|---|---|---|---|
| Master Orchestrator | ORCH | `orchestration/**` (except others' reports), shared status docs | integrate, assign, run Colab, request approvals | commit/push, acquire data, train without approval | this session | integration, Colab, approvals |
| Repository Auditor | A | `reports/REPO_AUDIT.md` | read-only audit | edit/refactor | **Subagent (launched)** | T-A1 |
| Data Source & Governance | B | `reports/DATA_SOURCE_RESEARCH.md` | read public docs/terms | download/scrape/API calls/accounts/email | **Subagent (launched)** | T-B1 |
| Engineering & Numerical | C | `reports/ENGINEERING_REPORT.md` (wave 1); later: `backend/src/**`, `backend/tests/**` by explicit grant | static review, proposed diffs; after Colab+grant: small fixes | run code locally; edit outside granted files | **Subagent (launched, report-only)** | T-C1 |
| Quant Research & Evaluation | D | `reports/RESEARCH_DESIGN.md` | methodology audit, experiment design | train; real data; run code | **Subagent (launched)** | T-D1 |
| UI & E2E Integration | E | `reports/UI_INTEGRATION_REPORT.md` (wave 1) | inspect, propose diffs | edit `frontend/**` (UI session's) | **Subagent (launched, report-only)** | T-E1 |
| Independent Reviewer | F | `reports/INDEPENDENT_REVIEW.md` | challenge claims, spot-check | rubber-stamp; edit others' work | Subagent (Wave 2) | T-F1 (not started) |
| UI session | UI | `frontend/**`, `dashboard-design/**` | per CORE_STATUS §1 | change models/payload semantics | **Chat (human-launched)** — prompt `prompts/S6_ui_e2e.md` | awaiting launch |
| Colab executor | COLAB | `reports/COLAB_VERIFICATION.md` | run approved commands in Colab | run on PC; expose tokens | Orchestrator via `colab-mcp`, else **Chat** — `prompts/S_colab_executor.md` | not connected |

## Installed capabilities discovered (2026-10-20)
- **Skills listed in the session:** `anthropic-skills:ponytail`, `anthropic-skills:caveman*`, `agent-reach`, many `ecc:*` (incl. `ecc:team-agent-orchestration`, `ecc:plan-orchestrate`, `ecc:orch-*`, `ecc:python-review`, `ecc:mle-workflow`, `ecc:security-review`). **Ponytail/Caveman principles applied manually** (minimal files, reuse existing status docs, terse reports); the skills were not invoked as tools. **ECC orchestration skills were not used**: the project-local file protocol below is sufficient (CLAUDE.md §13: no extra frameworks).
- **AgentReach (`agent-reach`)**: per its listed description it is an **internet research/content-fetching skill** (16 platforms, search, social, web), **not** an agent-coordination or cross-chat messaging tool. It is not used for coordination. Its CLI (`agent-reach doctor`) was not run or installed. Agent B uses WebSearch/WebFetch on docs pages instead.
- **Agent types available:** `general-purpose`, `Explore`, `Plan`, `ecc:code-reviewer`, `ecc:python-reviewer`, `ecc:mle-reviewer`, `ecc:security-reviewer`, etc. Wave 1 uses `general-purpose` (needs Write for reports).
- **Colab:** MCP server `colab-mcp`, one tool `open_colab_browser_connection` (not yet called).
