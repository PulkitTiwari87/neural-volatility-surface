# frontend/

**Status:** IMPLEMENTED (local, research use). `index.html` is the whole interface: a landing page and a research workbench (overview, surface explorer with heatmap and table views, evaluation, data and provenance, experiments and pipeline, artifacts, methodology; a 3D surface tab was re-added on 2026-10-21 at the owner's request, see DEC-008 amendment). It is one self-contained file with no dependencies because the research server serves exactly this file under a strict CSP. It reads only the read-only API in `backend/src/volatility_lab/api/`.

The framework, charting and 3D decision (DEC-008) was **DECIDED 2026-10-20 (owner, local research tool): keep this static viewer, no frontend framework; 3D tab added 2026-10-21 as a dependency-free canvas renderer** (decision.md). What was built, what differs from the plan and what was verified: [../dashboard-design/IMPLEMENTATION_STATUS.md](../dashboard-design/IMPLEMENTATION_STATUS.md). Design: [../dashboard-design/](../dashboard-design/). The frontend must never hold provider credentials, train models or compute IV.

Run: see the status file §8.
