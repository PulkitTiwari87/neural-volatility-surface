# Model handoff: what must be true before frontend implementation starts

**Status:** `PROPOSED` coordination contract. **No completion marker exists and none was created.** This session did not touch the model, training, data or backend code, and does not assume the model is finished from the absence of file changes.

## 1. What the frontend consumes (verified by reading the code and docs)

The frontend never trains, infers or computes IV. It reads files that already exist through the read-only API (`backend/src/volatility_lab/api/`). A **runs root** holds one directory per run (contract in the `api/service.py` docstring):

| File | Required | Content |
|---|---|---|
| `<run>/panel.npz` | yes | Surface panel arrays used by the API: `iv` (dates x tenors x k, decimal), `status` (0 missing, 1 interpolated in tenor, 2 interpolated in strike, 3 observed), `dates`, `tenor_days`, `k_nodes`, `spot`, `n_quotes` |
| `<run>/meta.json` | optional, strongly wanted | `{"origin": "synthetic" or "real", "description": "..."}`; without it the run shows as *unlabelled* |
| `<run>/manifest.json` | optional | `dataset-1` manifest: `version_id`, `config_sha256`, `inputs`, ledgers, `panel_sha256` (used for the panel-hash check) |
| `<run>/tables/*.csv` | optional | Descriptive result tables (the notebook writes `pooled.csv`, `per_fold.csv`, `training_summary.csv` and region breakdowns) |
| `<run>/forecasts/<model>.npz` | optional | `target_index`, `origin_index` (strictly before the target), `pred` of shape (n, tenors, k) |

What exists today (from [../docs/engineering/IMPLEMENTATION_MATRIX.md](../docs/engineering/IMPLEMENTATION_MATRIX.md) §6 to §8 and [../docs/research/E1_RESULTS.md](../docs/research/E1_RESULTS.md)): the E-1 package (`backend/src/volatility_lab`: ingestion, validation, pricing, surfaces, features, evaluation, baselines, GPU-only neural models, runner, raw store, API), unit tests (`backend/tests/unit`), generated notebooks, an executed real-data E-1 run on a Kaggle T4 (2026-10-13, reproduced 2026-10-16) and E-2 (2026-10-13). Results are descriptive and unvalidated.

## 2. Artifacts the dashboard will need, and where they are

| Artifact | Needed by | Actual location | Status |
|---|---|---|---|
| A synthetic demo run | All development and tests | `scripts/make_synthetic_run.py` generates it; the output is not in Git | `AVAILABLE` (generate locally) |
| A real E-1 run (panel, manifest, tables, forecasts) | Real-data views | On the owner's Kaggle account (private notebook version output, about 40 MB and 194 files per E1_RESULTS §7); **not in Git, not on this computer** | `UNKNOWN` locally; copy and layout step required (§3.3); licence gate (§5) |
| Forecast files (`forecasts/*.npz`) | Forecast comparison | Exported by `experiments/runner.py` `export_forecasts`; per E1_RESULTS §7 the 2026-10-16 Kaggle re-run exported them | `UNKNOWN` locally |
| Result tables | Evaluation | `tables/` of a run; documented values in E1_RESULTS §3 | Documented `VERIFIED`; runtime per run |
| Model checkpoints (48) | none (the UI never loads models) | Kaggle output | not needed |

## 3. Discrepancies the model session (or owner) should resolve

1. **Stale status text.** `CLAUDE.md` says there is "no API and no frontend code" and that neural forecasting on real data is "not implemented, not validated"; IMPLEMENTATION_MATRIX §6 to §8 and E1_RESULTS record an API, a 2D viewer and an executed neural run. The UI states what the matrix and results document; the owner should reconcile CLAUDE.md.
2. **Forecast export evidence conflicts.** IMPLEMENTATION_MATRIX P5d says the notebooks' `export_forecasts` call was "not executed since the change"; E1_RESULTS §7 says the 2026-10-16 Kaggle run exported forecasts. Verify which holds before building the comparison view.
3. **Run layout mismatch.** The notebook output uses `surfaces/surface_panel.npz` and, for E-2, nested `e1_nearest/forecasts` and `e2_fixed/forecasts`; the API needs `panel.npz` with `forecasts/` beside it ([IMPLEMENTATION_MATRIX P5d](../docs/engineering/IMPLEMENTATION_MATRIX.md) describes the manual copy). Decide whether the runner writes the API layout or a copy tool exists.
4. **`frontend/README.md`** still says the directory is intentionally empty.

## 4. Completion signal and gate (exact)

**Existing mechanism:** none found. A search of the repository's Markdown files for a model-completion, status or handoff mechanism found none outside this directory; progress is recorded only in prose (IMPLEMENTATION_MATRIX, CHANGELOG, results documents). The presence of a README, a finished plan or an unchanged `git status` is not a signal.

**Proposed minimal contract** (to be created by the model session or the owner, never by the dashboard session): a machine-readable file, suggested path `docs/engineering/MODEL_STATUS.json`:

```json
{
  "schema_version": 1,
  "status": "in_progress | complete | blocked",
  "updated_at": "2026-10-16T00:00:00Z",
  "confirmed_by": "owner",
  "model_interface": {
    "run_directory_contract": "see api/service.py docstring",
    "forecast_file": "forecasts/<model>.npz {target_index, origin_index, pred}",
    "inference_entry_point": "none; the UI consumes stored files only"
  },
  "available_artifacts": [{ "path": "<run>/panel.npz", "sha256": "<hex>", "kind": "surface_panel", "origin": "synthetic | real" }],
  "completed_validation": [{ "name": "unit tests", "command": "<documented test command>", "result": "<observed output summary>", "date": "2026-10-16" }],
  "known_blockers": []
}
```

(Example values only; this file does not exist.)

**Authorisation to begin implementation requires ALL of the following, in this order:**

1. `MODEL_STATUS.json` exists with `"status": "complete"` and `confirmed_by` set by the owner, **and** the owner tells the dashboard session in chat, in words, to begin implementation. A file alone is not authorisation.
2. Every path in `available_artifacts` exists and its SHA-256 matches.
3. The model and API tests were run by the dashboard session and their output seen. The exact command is not stated in `backend/README.md` (checked); take it from [../docs/engineering/TESTING_STRATEGY.md](../docs/engineering/TESTING_STRATEGY.md) or the model session. Do not guess it. E1_RESULTS records "49 CPU tests OK, 1 GPU test skipped locally" as the last known result, which is evidence to re-check, not a pass.
4. `git status --short` (read-only) shows no uncommitted change under `backend/src/volatility_lab`, `backend/tests`, `scripts/_notebook_cells` and `notebooks` since the model session reported completion. Today these paths are untracked, so this check is only meaningful after the owner commits; until then rely on item 2.
5. The model session states it is no longer editing files the integration consumes; ask, do not infer from silence.
6. The owner decisions in [IMPLEMENTATION_PLAN §7](IMPLEMENTATION_PLAN.md) items 1, 2 and 7 are made.

If any item fails, record why in the status file's `known_blockers` (by its owner) and stop.

## 5. Known unknowns and blockers

- **Licence.** The hosted dataset's upstream terms are unverified. Whether derived surfaces, forecasts or tables may be stored locally or displayed is undecided (DEC-002, SEC-006). Development and automated tests use synthetic runs only; no real data is committed or downloaded by the dashboard work.
- **Per-cell quote lineage** (UI-010) and **stored arbitrage flags** are not in any artifact; the widgets are `UNAVAILABLE` or `UNKNOWN` ([DATA_WIDGET_MATRIX](DATA_WIDGET_MATRIX.md) X6, X15).
- **Result-table column names** are unknown until a real run is read.
- **Whether the model session will change E-1 results or add runs** is unknown; the landing page and Overview contain a documented-finding statement that must be revisited if results change (LANDING_PAGE §3 C).
- **GPU policy:** training and inference run only on a verified GPU ([../CLAUDE.md](../CLAUDE.md) §13); irrelevant to the frontend, which loads no models.
- **Statistical inference** is closed (NO-GO); the UI must never imply significance.

## 6. Checklist for the future session

- [ ] Gate §4 items 1 to 6 satisfied and recorded.
- [ ] A fresh synthetic run generated and loads in the existing viewer.
- [ ] Real-run copy and layout step agreed (§3.3) and the licence decision recorded (§5).
- [ ] Table names and columns for Evaluation read from an actual run, not assumed.
- [ ] Forecast files confirmed present for the run (or the comparison view is hidden with an explicit Unavailable state).
- [ ] Stale statements in §3 reconciled or acknowledged.
- [ ] Stack decision (DEC-008) and static-serving change approved.
