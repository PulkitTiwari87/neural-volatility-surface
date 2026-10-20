# Agent A — Repository Auditor (stage S1)

Read `_COMMON.md` first. **Owned file:** `orchestration/reports/REPO_AUDIT.md` (only).

Task: establish the baseline of the *actual* repository. Do not refactor, clean, or fix anything.
1. Map the pipeline end to end: ingestion → raw store → validation → pricing/IV → surfaces → features → models → evaluation → experiments → api → frontend. For each module under `backend/src/volatility_lab/`, state purpose, size (file count / approx lines), tests that exist for it (mirror in `backend/tests/{unit,integration,scientific}`), and status per the repo vocabulary.
2. Classify every claimed capability as **implemented / partially implemented / planned / unverified**. Cross-check `docs/engineering/CORE_STATUS.md`, `IMPLEMENTATION_PLAN.md`, `README.md` status table and `MODEL_STATUS.json` against the code and against each other; list every contradiction or stale number (e.g. test counts: CORE_STATUS cites 110, 158, 179 and 252 at different points; `MODEL_STATUS.json` completed_validation vs §9 of CORE_STATUS).
3. Inspect the uncommitted working tree (`git status`, `git diff --stat`, then diffs of the modified files and the untracked files) and summarise what each change does and whether docs/tests accompany it.
4. Identify duplication, dead code, inconsistent docs, and the **actual cause** of each listed blocker (`MODEL_STATUS.json` known_blockers, CORE_STATUS §8–9), distinguishing owner-decision blockers, external-access blockers (data licence), and engineering blockers.
5. Locate existing orchestration/subagent/CI infrastructure (`.github/workflows`, scripts, notebooks) and what has never been run (e.g. CI).
6. Note anything that could not be inspected.

Deliverable: `orchestration/reports/REPO_AUDIT.md`. Include a table of "claims that lack executable evidence in a clean environment".
