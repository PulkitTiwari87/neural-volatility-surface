"""Cell text for the E-2 notebook (fixed-expiry vs nearest-expiry target). Shared setup cells live in cells.py."""

OVERVIEW = r"""# Experiment E-2: fixed-expiry target versus the E-1 nearest-expiry target

Continues [E-1](docs/research/E1_RESULTS.md). Same hosted dataset (Kaggle `dudesurfin/spy-options-eod-volatility-surface-2010-2023`, upstream licence **unverified**), same surfaces, same walk-forward folds, same models and fixed hyper-parameters. Only the **label** changes.

**Why.** In E-1 the label of a cell (tenor, log-moneyness) at the target date is whichever real expiry is *nearest the tenor on that date*, chosen independently on each date. When the nearest expiry changes between the origin and the target, the "change" mixes the dynamics of the surface with a switch of contract, which inflates short-tenor error. E-2 removes that.

| | E-1 `nearest_expiry` | E-2 `fixed_expiry` |
|---|---|---|
| Label of cell *c* at origin *t* | IV of the expiry nearest the tenor **on t+h** | IV on t+h of the **same expiry that anchored c on t** (same log-moneyness node) |
| Expiry chosen from | target-date quotes | **origin-date quotes only** |
| Missing / expired expiry | n/a | label is **missing and counted** (censored, never imputed) |
| Eligible cells | observed on t+h and real value on t | anchored on one real expiry on t with tight quotes, same expiry tight on t+h |
| Maturity | re-anchored each day | shortens by *h* days (a genuine roll-down effect) |

Models: persistence, ridge, PCA-ridge, rolling mean, MLP, GRU (3 seeds + seed-average); GPU only for the neural models. **Descriptive results only**: no significance claim (inferential validity unsupported; Phase 0 closed NO-GO). Comparisons across the two targets are made on the **common (origin, cell) sample** where both labels exist, so coverage differences cannot masquerade as model differences.
"""

H_FEATURES = "## 8. Targets, folds and leakage audit\nBoth `Prepared` datasets are built from the same panel, so origins, target rows and folds are identical; only the label differs. The expiry anchoring each cell is read from origin-date quotes; the future is read only to form the label."

FEATURES = r"""display = lambda x: print(x.to_string() if hasattr(x, "to_string") else x)   # plain-text tables: they land in the run log
from volatility_lab.evaluation import compare, metrics as Mx
from volatility_lab.features.panel import target_arrays
p1 = prepare(panel, cfg.features, "nearest_expiry")      # E-1 label
p2 = prepare(panel, cfg.features, "fixed_expiry")        # E-2 label
folds = make_folds(p1, cfg.split)
assert np.array_equal(p1.origins, p2.origins) and np.array_equal(p1.targets, p2.targets)
rows = []
for f in folds:
    assert_no_overlap(p1, f)
    od = p1.dates[p1.origins].astype("datetime64[D]")
    rows.append({"test_year": f.test_year, "val_year": f.val_year, "train_from": str(od[f.train].min()), "train_to": str(od[f.train].max()),
                 "n_train": len(f.train), "n_val": len(f.val), "n_test": len(f.test)})
fold_table = pd.DataFrame(rows); display(fold_table)
LEAK = feature_invariance_check(p1, cfg)
print("leakage audit (features at origins <= t unchanged when every later row is scrambled):", LEAK); assert LEAK["passed"], "LEAKAGE DETECTED"
cov = compare.coverage_by_fold(p1, p2, folds)
print("eligible-sample coverage per test year (primary cells):"); display(cov)
tot = cov.sum(numeric_only=True)
print(f"TOTAL test cells: E-1 eligible {int(tot.e1_eligible):,} | E-2 eligible {int(tot.e2_eligible):,} | common {int(tot.common):,} | "
      f"E-2 anchored at origin {int(tot.e2_anchored_at_origin):,}, of which censored (expiry has no usable slice at the target) {int(tot.e2_censored_no_target):,} | "
      f"E-1 eligible cells whose nearest-expiry anchor SWITCHED: {int(tot.e1_eligible_anchor_switched):,} ({tot.e1_eligible_anchor_switched / tot.e1_eligible:.1%})")
FEATURE_DEFS = {"target_e1": "y(t+h,c) - s(t,c), y = value of the expiry nearest the tenor on t+h; eligible: observed on t+h and a real value on t",
                "target_e2": "y(t+h,c) - s(t,c), y = value on t+h of the SAME expiry that anchored c on t; eligible: tight on both dates; censored if that expiry has no usable slice on t+h",
                "features": "unchanged from E-1 (filled surface, lagged changes, realised vol, availability)",
                "fit_on_training_rows_only": ["per-cell fill means", "feature scalers", "PCA basis", "ridge penalty (validation year)", "early stopping (validation year)"]}
"""

H_BASE = "## 9. Baseline models on both targets\nIdentical code, folds and settings; each model is trained and scored under its own target, then compared on the common sample."

BASELINES = r"""t0 = time.time()
preds1, ch1 = runner.run_baselines(p1, folds, cfg, log=lambda *_: None)
preds2, ch2 = runner.run_baselines(p2, folds, cfg, log=print)
print(f"baselines (both targets) done in {time.time() - t0:.0f}s; ridge penalties E-1: {[v['ridge_alpha'] for v in ch1.values()]} | E-2: {[v['ridge_alpha'] for v in ch2.values()]}")
"""

H_NEURAL = "## 10. GPU neural training on both targets\nMLP and GRU, 3 seeds per (fold, model, target), early stopping on the validation year, the E-1 fixed hyper-parameters. Every tensor lives on the CUDA device; there is no CPU fallback."

NEURAL = r"""if not GPU_OK:
    raise neural.GpuUnavailableError(neural.GPU_HELP)
t0 = time.time()
n1, DEVICE = runner.run_neural(p1, folds, cfg, OUT_DIR / "e1_nearest", log=lambda *_: None)
n2, _ = runner.run_neural(p2, folds, cfg, OUT_DIR / "e2_fixed", log=lambda *_: None)
NEURAL_SECONDS = time.time() - t0
all1 = {fy: {**preds1[fy], **n1[fy]} for fy in preds1}
all2 = {fy: {**preds2[fy], **n2[fy]} for fy in preds2}
print(f"neural phase (2 targets x {len(folds)} folds x {len(cfg.train.models)} models x {len(cfg.train.seeds)} seeds) finished in {NEURAL_SECONDS:.0f}s on {DEVICE['name']}")
print(subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total", "--format=csv"], capture_output=True, text=True).stdout)
hist = []
for sub in ("e1_nearest", "e2_fixed"):
    for fp in sorted((OUT_DIR / sub / "histories").glob("*.json")):
        h = json.loads(fp.read_text()); hist.append({"target": sub, "run": fp.stem, "epochs_run": h["epochs_run"], "best_epoch": h["best_epoch"], "seconds": h["seconds"], "peak_gpu_mb": h["peak_gpu_mem_mb"]})
HIST = pd.DataFrame(hist)
display(HIST.assign(kind=HIST.run.str.extract(r"_(mlp|gru)_")[0]).groupby(["target", "kind"]).agg(runs=("run", "count"), epochs_mean=("epochs_run", "mean"), best_epoch_mean=("best_epoch", "mean"), best_epoch_max=("best_epoch", "max"), seconds_total=("seconds", "sum")).round(2))
"""

H_EVAL = "## 11. Out-of-sample evaluation\nPrimary cells only (tight quotes). Errors in implied-vol points (1 pt = 0.01). Sample counts are printed with every table."

EVAL = r"""per_fold1, pooled1, brk1, paired1 = runner.evaluate_all(p1, folds, all1)
per_fold2, pooled2, brk2, paired2 = runner.evaluate_all(p2, folds, all2)
def prim(pooled): return pooled[pooled.cells == "primary"].sort_values("rmse")
print("=== E-2 (fixed expiry) pooled out-of-sample, each model on its own eligible cells ==="); display(prim(pooled2).round(4))
print("=== E-1 (nearest expiry) re-run in this notebook, same models and settings ==="); display(prim(pooled1).round(4))

# reproduction check against the numbers published in docs/research/E1_RESULTS.md (Kaggle run kaggle_eaa46df0_76bf2f94)
E1_PUBLISHED_RMSE = {"pca_ridge": 2.5020, "persistence": 2.5686, "ridge": 2.5883, "gru_ens": 2.6659, "mlp_ens": 2.8219, "rolling_mean": 5.0162}
chk = prim(pooled1).set_index("model").rmse
repro = pd.DataFrame({"E1 published": pd.Series(E1_PUBLISHED_RMSE), "re-run here": chk.reindex(list(E1_PUBLISHED_RMSE)).round(4)}); repro["abs diff"] = (repro["re-run here"] - repro["E1 published"]).abs()
print("E-1 reproduction check (RMSE, vol pts):"); display(repro)
print("walk-forward RMSE by test year, E-2 fixed expiry (observed cells):"); display(per_fold2[per_fold2.cells == "primary"].pivot(index="fold", columns="model", values="rmse").round(3))
print("descriptive paired comparison vs persistence under E-2 (daily MAE; no p-values, no intervals):"); display(paired2.round(4))

# the head-to-head: identical (origin, cell) sample, each model under its own target
per_c, pooled_c = compare.paired_on_common(p1, p2, folds, all1, all2)
ens = [m for m in pooled_c.model.unique() if not m.endswith(("_s0", "_s1", "_s2"))]
tab = pooled_c[pooled_c.model.isin(ens)].pivot(index="model", columns="target", values=["rmse", "mse_skill_vs_persistence"]).round(4)
print(f"=== COMMON SAMPLE (cells eligible under both targets): n = {int(pooled_c.n_cells.iloc[0]):,} cells over {int(pooled_c.n_days.iloc[0]):,} origin days ==="); display(tab)
print("per-year RMSE on the common sample (persistence / pca_ridge / gru_ens / mlp_ens):")
display(per_c[per_c.model.isin(["persistence", "pca_ridge", "gru_ens", "mlp_ens"])].pivot_table(index="fold", columns=["model", "target"], values="rmse").round(3))
sb = compare.switch_breakdown(p1, folds, all1)
print("E-1 persistence error on its eligible cells, split by whether the nearest-expiry anchor switched between origin and target:"); display(sb.round(4))

rows = []
for f in folds:
    mask = compare.common_mask(p1, p2, f.test)
    for label, p, pr in (("nearest_expiry", p1, all1), ("fixed_expiry", p2, all2)):
        y = target_arrays(p)[0][f.test]
        for name in ("persistence", "pca_ridge", "gru_ens"):
            err = (pr[f.test_year][name] - y) * 100
            for tau in TENOR_DAYS:
                m = mask & (p.cell_tenor == tau)[None, :]
                rows.append({"target": label, "model": name, "tenor_days": tau, "se": float((err[m] ** 2).sum()), "n": int(m.sum())})
tenor_c = pd.DataFrame(rows).groupby(["model", "target", "tenor_days"]).sum().reset_index(); tenor_c["rmse"] = np.sqrt(tenor_c.se / tenor_c.n)
print("RMSE by tenor on the common sample:"); display(tenor_c.pivot_table(index="tenor_days", columns=["model", "target"], values="rmse").round(3))
print("n cells by tenor on the common sample:", tenor_c[(tenor_c.model == "persistence") & (tenor_c.target == "fixed_expiry")].set_index("tenor_days").n.to_dict())

fig, axs = plt.subplots(1, 2, figsize=(14, 4))
for name, ls in (("persistence", "-"), ("pca_ridge", "--"), ("gru_ens", ":")):
    for label, col in (("nearest_expiry", "C0"), ("fixed_expiry", "C1")):
        d = tenor_c[(tenor_c.model == name) & (tenor_c.target == label)]; axs[0].plot(d.tenor_days, d.rmse, ls, color=col, marker="o", label=f"{name} | {label}")
axs[0].set_xlabel("tenor (days)"); axs[0].set_ylabel("RMSE (vol pts)"); axs[0].set_title("common sample: error by tenor"); axs[0].legend(fontsize=6)
yr = per_c[per_c.model.isin(["persistence", "pca_ridge"])].pivot_table(index="fold", columns=["model", "target"], values="rmse"); yr.plot(ax=axs[1], marker="o"); axs[1].set_title("common sample: RMSE by test year"); axs[1].legend(fontsize=6)
savefig("e2_tenor_and_year"); plt.show()
"""

H_INTERP = "## 12. Results and interpretation\nGenerated from the tables above, so it cannot claim more than was computed."

INTERP = r"""import re
c1, c2 = prim(pooled1).set_index("model"), prim(pooled2).set_index("model")
cm = pooled_c.set_index(["model", "target"])
lines = [f"Data: {DATA_LABEL}; {audit['n_surface_dates']} surface dates {audit['first_date']} -> {audit['last_date']}; {len(folds)} walk-forward test years {[f.test_year for f in folds]}.",
         f"Neural models executed on {DEVICE['name']}: {len(cfg.train.seeds)} seeds x {len(cfg.train.models)} architectures x {len(folds)} folds x 2 targets.",
         f"Eligible test cells: E-1 {int(c1.loc['persistence','n_cells']):,}; E-2 {int(c2.loc['persistence','n_cells']):,}; common sample {int(cm.loc[('persistence','fixed_expiry'),'n_cells']):,}.",
         f"Persistence RMSE on the common sample: nearest-expiry label {cm.loc[('persistence','nearest_expiry'),'rmse']:.3f} pts vs fixed-expiry label {cm.loc[('persistence','fixed_expiry'),'rmse']:.3f} pts."]
for m in [x for x in c2.index if x != "persistence" and not re.search(r"_s\d+$", x)]:
    a = cm.loc[(m, "fixed_expiry"), "mse_skill_vs_persistence"]; b = cm.loc[(m, "nearest_expiry"), "mse_skill_vs_persistence"]
    row = paired2[paired2.model == m].iloc[0]
    lines.append(f"- {m}: MSE skill vs persistence on the common sample: fixed-expiry {a:+.3f} vs nearest-expiry {b:+.3f}; under E-2 better than persistence in {row.folds_better_than_persistence} test years, on {row.share_of_days_better:.1%} of days (n={int(row.n_days)}).")
beaten2 = [m for m in c2.index if m != "persistence" and not re.search(r"_s\d+$", m) and c2.loc[m, "mse_skill_vs_persistence"] > 0]
lines.append("Models with positive pooled MSE skill vs persistence under the fixed-expiry label (own eligible cells): " + (", ".join(beaten2) if beaten2 else "none") + ".")
lines += ["Not concluded: statistical significance (unsupported); that a model 'improves' on persistence unless the per-year table shows it consistently; generalisation beyond this dataset; any trading or hedging value.",
          "Caveats: the two labels have different eligible samples (use the common-sample rows to compare); E-2 censors cells whose expiry vanishes and excludes interpolated-in-maturity cells; closing-snapshot mids; American-vs-European mismatch."]
INTERPRETATION_TEXT = "\n".join(lines); print(INTERPRETATION_TEXT)
"""

H_SAVE = "## 13. Save outputs\nOne run folder with a SHA-256 manifest, re-opened and re-hashed. The raw dataset is never copied."

SAVE = r"""import platform
for name, df in (("coverage", cov), ("pooled_e1_nearest", pooled1), ("pooled_e2_fixed", pooled2), ("per_fold_e1", per_fold1), ("per_fold_e2", per_fold2),
                 ("paired_e2_vs_persistence", paired2), ("pooled_common", pooled_c), ("per_fold_common", per_c), ("switch_breakdown", sb), ("tenor_common", tenor_c),
                 ("e1_reproduction", repro.reset_index()), ("folds", fold_table), ("neural_runs", HIST)):
    df.to_csv(OUT_DIR / "tables" / f"{name}.csv", index=False)
runner.save_panel(panel, OUT_DIR / "surfaces" / "surface_panel.npz")
runner.export_forecasts(p1, folds, all1, OUT_DIR / "e1_nearest")   # forecasts/<model>.npz for the viewer API
runner.export_forecasts(p2, folds, all2, OUT_DIR / "e2_fixed")     # actual shown there is the surface at the target date, not the E-2 label
for tag, p, preds in (("e1", p1, all1), ("e2", p2, all2)):
    for f in folds:
        ty, tst = target_arrays(p)
        np.savez_compressed(OUT_DIR / "predictions" / f"{tag}_eval_fold{f.test_year}.npz", origin_dates=p.dates[p.origins[f.test]], target_dates=p.dates[p.targets[f.test]],
            actual=ty[f.test], target_status=tst[f.test], primary_mask=Mx.eval_mask(p, f.test, "primary"), common_mask=compare.common_mask(p1, p2, f.test), cell_tenor=p.cell_tenor, cell_k=p.cell_k,
            models=np.array(sorted(preds[f.test_year])), **{f"pred__{m}": v for m, v in preds[f.test_year].items()})
meta = {"run_id": RUN_ID, "experiment": "E-2 fixed-expiry vs nearest-expiry target", "data_label": DATA_LABEL, "kaggle_dataset": KAGGLE_DATASET, "dataset_fingerprint": FINGERPRINT,
        "config": cfg.to_dict(), "config_sha256": cfg.sha256(), "feature_definitions": FEATURE_DEFS, "split_boundaries": fold_table.to_dict("records"), "leakage_audit": LEAK,
        "ledger_prefilter": built["ledger_prefilter"], "ledger_quotes": built["ledger_quotes"], "audit": audit, "device": DEVICE, "neural_seconds": NEURAL_SECONDS, "extra_plot_errors": E2_PLOT_ERRORS,
        "environment": runner.environment_metadata(), "colab": {"platform": platform.platform()}}
(OUT_DIR / "metadata").mkdir(exist_ok=True)
(OUT_DIR / "metadata" / "run_metadata.json").write_text(json.dumps(meta, indent=1, default=str))
def md(df, **kw): return "```\n" + df.to_string(**kw) + "\n```"
report = ["# E-2 run report", f"**{DATA_LABEL}** | run `{RUN_ID}`", "", "## Interpretation (generated)", INTERPRETATION_TEXT, "", "## Eligible-sample coverage", md(cov, index=False), "",
          "## Pooled, E-2 fixed expiry (primary cells)", md(prim(pooled2).round(4), index=False), "", "## Pooled, E-1 nearest expiry re-run", md(prim(pooled1).round(4), index=False), "",
          "## Common sample", md(tab), "", "## Gates", "- inferential validity: UNSUPPORTED", "- trading / hedging validity: NOT EVALUATED"]
(OUT_DIR / "report.md").write_text("\n".join(report))
man = runner.write_manifest(OUT_DIR, {"run_id": RUN_ID, "config_sha256": cfg.sha256(), "dataset_combined_sha256": FINGERPRINT["combined_sha256"]})
problems = runner.verify_manifest(OUT_DIR); assert problems == [], problems
print(f"{len(man['files'])} files written, re-opened and re-hashed OK under {OUT_DIR}")
for rel in ("report.md", "manifest.json", "tables/pooled_common.csv", "tables/coverage.csv", "tables/pooled_e2_fixed.csv", "surfaces/surface_panel.npz", "metadata/run_metadata.json", "plots/e2_tenor_and_year.png"):
    fp = OUT_DIR / rel; print(("OK  " if fp.exists() else "MISSING "), fp, f"({fp.stat().st_size:,} bytes)" if fp.exists() else "")
print("checkpoints:", len(list(OUT_DIR.rglob("*.pt"))), "| prediction files:", len(list((OUT_DIR / "predictions").glob("*.npz"))), "| plots:", len(list((OUT_DIR / "plots").glob("*.png"))))
print("re-opened a predictions file:", np.load(OUT_DIR / "predictions" / f"e2_eval_fold{folds[0].test_year}.npz")["actual"].shape)
"""


H_EXTRA = "## 11b. Extra curves and heatmaps for both targets\nThe E-1 extra-plot code (training curves for every fold and seed, per-cell error / bias / skill heatmaps, daily-error and cumulative curves, skill by year and seed spread, actual-vs-forecast surfaces) is run once per target; files are prefixed `e1_nearest_` and `e2_fixed_`. Under E-2 every model is scored, and every heatmap drawn, on its own same-expiry label. Descriptive only; a figure that fails is reported loudly and recorded in the run metadata, never skipped silently."

# the notebook cell is  EXTRA_HEAD + <shared plotting source from cells.EXTRA_PLOTS> + EXTRA_TAIL + EXTRA_LOOP  (assembled in build_colab_notebook.py)
EXTRA_HEAD = "# shared plotting code (identical to the E-1 notebook section 11b), stored as text and run once per target below\nEXTRA_SRC = r'''"
EXTRA_TAIL = "'''\n"
EXTRA_LOOP = r"""def pool_brk(df):
    g = df.groupby(["group", "model"]); n = g.n_cells.sum()
    out = pd.DataFrame({"rmse": np.sqrt((df.assign(w=df.rmse ** 2 * df.n_cells).groupby(["group", "model"]).w.sum()) / n.replace(0, np.nan)), "n_cells": n})
    return out.reset_index()
E2_PLOT_ERRORS = {}
for PLOT_TAG, p, preds_all, per_fold, pooled, brk, HIST_DIR in (
        ("e1_nearest_", p1, all1, per_fold1, pooled1, brk1, OUT_DIR / "e1_nearest" / "histories"),
        ("e2_fixed_", p2, all2, per_fold2, pooled2, brk2, OUT_DIR / "e2_fixed" / "histories")):
    print(f"===== extra plots for target {PLOT_TAG.rstrip('_')} =====")
    _pr = pooled[pooled.cells == "primary"].sort_values("rmse")
    BEST_NEURAL = next((m for m in _pr.model if m.endswith("_ens")), None)
    BEST_BASE = next(m for m in _pr.model if m in ("rolling_mean", "ridge", "pca_ridge"))
    exec(EXTRA_SRC, globals())
    E2_PLOT_ERRORS[PLOT_TAG] = dict(EXTRA_PLOT_ERRORS)
print("extra-plot errors per target:", E2_PLOT_ERRORS or "none")
"""
