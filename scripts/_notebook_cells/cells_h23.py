"""Cell text for notebooks H2 (tail-fraction validation) and H3 (calendar features). Both reuse the E-2 pipeline
cells (``cells``, ``cells_e2``): same data, test years, models, seeds, both labels, GPU-only neural training.
Everything specific to H2/H3 is generated here from the VARIANTS table."""
import cells
import cells_e2

COMMON = r'''
**Setting (identical to E-2 except the one change above).** Hosted SPY surfaces (Kaggle `dudesurfin/spy-options-eod-volatility-surface-2010-2023`, upstream licence **unverified**); walk-forward test years 2016-2023; models persistence, rolling mean, ridge, PCA-ridge, MLP, GRU (3 seeds + seed-average, fixed hyper-parameters, no search); both labels (E-1 nearest-expiry, E-2 fixed-expiry). Ridge/PCA-ridge use the **H1 penalty grid** (up to 1e6; H1b showed a wider grid changes nothing), so the baselines are the ones that stand after H1/H1b. **Neural training is GPU-only** (no CPU fallback): choose *Accelerator: GPU* in Kaggle.

**Pre-registered decision rule (descriptive; owner-approved 2026-10-16).** A model "improves on persistence" only if (a) pooled MSE skill > 0 **and** pooled MAE below persistence, (b) better by daily MAE in >= 6 of 8 test years, (c) every seed's pooled skill > 0, (d) skill > 0 in >= 2 of 3 realised-vol regimes with n >= 100 cells, (e) under **both** labels; otherwise "holds under one label only" or "no improvement shown". No p-values, no intervals. **A neural result worse than persistence is reported as such and retains the NO-GO.** Test years are evaluated once per frozen configuration (GR-LEAK-05): nothing is selected on them; the configuration hash is printed and saved. No test-window access log exists (known gap).

**How to run on Kaggle.** New notebook -> File -> Import notebook (upload this `.ipynb`) -> *+ Add Input* -> dataset `dudesurfin/spy-options-eod-volatility-surface-2010-2023` -> Accelerator **GPU (T4 or P100)** -> *Save & Run All (Commit)*. Then copy the final "RESULT SUMMARY" line and `report.md` back. Runtime is of the order of E-2 (the GPU phase dominates).
'''

VARIANTS = {
    "h2": dict(
        key="H2", file="Neural_Volatility_Surface_H2_TailValidation", calendar=False, val_mode="tail_frac", mr=None, pca=None, gpu=True,
        title="Experiment H2: does early stopping fail because the validation year is a different regime? (Phase 4)",
        change=("**Hypothesis (from the E-1/E-2 untested list).** Early stopping on the *preceding calendar year* selects an almost untrained network when the "
                "validation year is in a different regime from the test year (notably the 2020 -> 2021 fold), so the neural models are handicapped by the selection protocol rather than by the architecture.\n\n"
                "**What changes (one thing only).** The validation set: instead of the previous calendar year, the **chronologically last 20 % of the training-eligible origins** "
                "(`make_folds(..., val_mode='tail_frac', val_frac=0.2)`), purged on both sides like before (validation labels end before the first test origin; training labels end before the first validation origin). "
                "Test sets are identical to E-2. Same models, seeds, features and fixed hyper-parameters. The ridge and PCA-ridge penalties are also chosen on this validation set (one protocol for every model).\n\n"
                "**Success / null.** Success only per the pre-registered rule below. **Null** if the best epoch stays at 0-3 and skill stays negative. A worse-than-persistence result keeps the NO-GO.")),
    "h4": dict(
        key="H4", file="Neural_Volatility_Surface_H4_StrongBaseline", calendar=True, val_mode="prev_year", mr=20, pca=None, gpu=True, neural=False,
        title="Experiment H4: a stronger non-neural baseline (H3 calendar features + mean reversion) (Phase 4)",
        change=("**Question.** The only thing that has cleared the pre-registered rule so far is a *baseline* (PCA-ridge with the H3 calendar block). Before any neural model is judged, the bar it must beat should be the strongest honest baseline.\n\n"
                "**What changes (one thing only vs H3).** Ridge, PCA-ridge, rolling-mean and persistence get the H3 calendar block **plus a mean-reversion block**: for every cell, the filled surface at the origin minus its trailing 20-row mean (for the PCA input: the same on the 3 factor scores). Causal (rows <= t), unit-tested. Ridge penalty grid = H1 grid, validation = previous year (as E-2/H3). **No neural model is trained.** Per the owner's 2026-10-19 instruction the notebook still runs on a **GPU runtime** with CUDA verified and logged; the ridge/PCA/persistence arithmetic stays NumPy float64 (porting it to CUDA would change the numbers and is not done).\n\n"
                "**Success / null.** Descriptive only. The result sets the baseline that H5/H6 neural models must beat; if the mean-reversion block changes PCA-ridge skill by less than 0.01 (absolute) under both labels versus H3, the H3 baseline stands.")),
    "h5": dict(
        key="H5", file="Neural_Volatility_Surface_H5_PCAFactorNeural", calendar=True, val_mode="prev_year", mr=20, pca=3, gpu=True,
        title="Experiment H5: PCA-factor neural models (MLP/GRU predict 3 factor changes) (Phase 4)",
        change=("**Hypothesis.** The cell-level networks (54 outputs, noisy sparse cells) are too flexible for ~2,000 daily samples. A network that predicts only the **3 PCA-factor changes** (basis fitted on each fold's training surfaces, exactly as in the PCA-ridge baseline) and rebuilds the surface as `s_t + dz @ V` is a much smaller problem, and is judged against the H4 baseline.\n\n"
                "**What changes (one thing only vs H4).** MLP and GRU output 3 values instead of every cell (`run_neural(..., pca_factors=3)`); loss weights are all ones in factor space (cells without a label count as no change). Same features as H4 (calendar + mean-reversion), validation = previous year, 3 seeds, fixed hyper-parameters. Baselines are re-run with the same features, so the comparison is like for like.\n\n"
                "**Success / null.** Success only per the pre-registered rule below, against persistence; additionally compare to the H4 PCA-ridge in the printed tables. A worse-than-persistence result keeps the NO-GO.")),
    "h6": dict(
        key="H6", file="Neural_Volatility_Surface_H6_CombinedH2H3", calendar=True, val_mode="tail_frac", mr=None, pca=None, gpu=True,
        title="Experiment H6: cell-level neural models with H3 features and H2 validation combined (Phase 4)",
        change=("**Question.** H2 (tail-fraction validation) and H3 (calendar features) were each tested alone. Do they interact for the cell-level MLP/GRU?\n\n"
                "**What changes.** Calendar block (H3) **and** `tail_frac` validation (H2) together; cell-level networks as in E-2; baselines on the H1 grid. Everything else as E-2/H3.\n\n"
                "**Success / null.** Success only per the pre-registered rule below. H2 showed no benefit alone, so a null is the expected outcome; this run closes the question.")),
    "h3": dict(
        key="H3", file="Neural_Volatility_Surface_H3_CalendarFeatures", calendar=True, val_mode="prev_year", mr=None, pca=None, gpu=True,
        title="Experiment H3: do the models lack the deterministic roll-down / weekday signal under the fixed-expiry label? (Phase 4)",
        change=("**Hypothesis (E-2 section 8 item 2).** Under the fixed-expiry label the tracked contract's maturity shortens by one day, so part of the change is deterministic roll-down; a weekday cycle may also exist. "
                "The models never see days-to-expiry or the weekday.\n\n"
                "**What changes (one thing only).** Features gain a calendar block known at the origin: for each of the 6 tenors, the **days-to-expiry of the expiry anchoring that tenor at the origin date** (the nominal tenor when no expiry anchors it), and a **Monday-Friday one-hot weekday**. "
                "Added to the tabular features (MLP, ridge), to every day of the GRU sequence, and to the PCA-ridge input. Validation protocol (previous year), folds, models, seeds and hyper-parameters are exactly as in E-2. Row-local, so it cannot look ahead (unit-tested).\n\n"
                "**Success / null.** Success only per the pre-registered rule below, under the fixed-expiry label (and then both). A worse-than-persistence result keeps the NO-GO.")),
}


def overview(v):
    return (f"# {v['title']}\n\n**Pre-registered 2026-10-19** in [`PHASE4_NEURAL_EVIDENCE_REVIEW`](../docs/research/PHASE4_NEURAL_EVIDENCE_REVIEW.md) "
            f"section 3 (table row {v['key']}). Generated by `scripts/build_colab_notebook.py` from the unit-tested package; **not yet executed**: run it once on Kaggle (GPU).\n\n{v['change']}\n{COMMON}")


CONFIG_EXTRA = r'''

# ---- PRE-REGISTERED @KEY@ SETTINGS (2026-10-19): DO NOT EDIT ----
VARIANT = "@KEY@"
VAL_MODE = "@VAL_MODE@"        # "prev_year" (E-1/E-2) | "tail_frac" (H2)
VAL_FRAC = 0.2                 # only used by "tail_frac"
CALENDAR = @CALENDAR@          # True = H3 calendar block (days-to-expiry per tenor + weekday one-hot)
MR_WINDOW = @MR@               # None = off; else trailing-mean window for the mean-reversion block (H4/H5)
PCA_FACTORS = @PCA@            # None = cell-level networks; else networks predict this many PCA-factor changes (H5)
ALPHAS_H1 = (0.1, 1.0, 10.0, 100.0, 1000.0, 3000.0, 1.0e4, 3.0e4, 1.0e5, 3.0e5, 1.0e6)   # baselines that stand after H1/H1b
MIN_YEARS_BETTER, MIN_REGIMES, MIN_CELLS_REGIME = 6, 2, 100
'''


def config(v):
    extra = (CONFIG_EXTRA.replace("@KEY@", v["key"]).replace("@VAL_MODE@", v["val_mode"]).replace("@CALENDAR@", str(v["calendar"]))
             .replace("@MR@", str(v["mr"])).replace("@PCA@", str(v["pca"])))
    if not v["gpu"]:
        extra = "\nMODELS = ()                   # baselines only: no neural model is trained (the session still runs on the GPU runtime; the baseline maths is NumPy float64)\n" + extra
    return cells.CONFIG.rstrip("\n") + extra


IMPORTS = cells.IMPORTS.replace("models=MODELS))", "models=MODELS, ridge_alphas=ALPHAS_H1))")
assert "ridge_alphas=ALPHAS_H1" in IMPORTS

FEATURES = (cells_e2.FEATURES
            .replace('prepare(panel, cfg.features, "nearest_expiry")', 'prepare(panel, cfg.features, "nearest_expiry", calendar=CALENDAR, mr_window=MR_WINDOW)')
            .replace('prepare(panel, cfg.features, "fixed_expiry")', 'prepare(panel, cfg.features, "fixed_expiry", calendar=CALENDAR, mr_window=MR_WINDOW)')
            .replace("folds = make_folds(p1, cfg.split)", "folds = make_folds(p1, cfg.split, VAL_MODE, VAL_FRAC)"))
assert FEATURES.count("mr_window=MR_WINDOW") == 2 and "VAL_MODE" in FEATURES
FEATURES += '''FEATURE_DEFS["variant"] = {"name": VARIANT, "val_mode": VAL_MODE, "val_frac": VAL_FRAC, "calendar_block": CALENDAR, "mr_window": MR_WINDOW, "pca_factors": PCA_FACTORS, "ridge_alphas": ALPHAS_H1}
print("variant:", FEATURE_DEFS["variant"], "| config sha256:", cfg.sha256())
'''

H_RULE = ("## 11a. Pre-registered decision rule\nApplied to every non-persistence model under both labels. A criterion that cannot be evaluated is "
          "reported as such, never passed. Per-seed skills feed criterion (c).")

RULE = r'''import re
from volatility_lab.evaluation.decision_rule import improvement_rule, combine_labels
def seed_skills(pooled, kind):
    pr = pooled[pooled.cells == "primary"].set_index("model")
    return [float(pr.loc[f"{kind}_s{s}", "mse_skill_vs_persistence"]) for s in cfg.train.seeds if f"{kind}_s{s}" in pr.index]
RULE = {}
for m in [x for x in prim(pooled2).model if x != "persistence" and not re.search(r"_s\d+$", x)]:
    kind = m[:-4] if m.endswith("_ens") else None
    r1 = improvement_rule(pooled1, brk1, paired1, m, min_years_better=MIN_YEARS_BETTER, min_regimes=MIN_REGIMES, min_cells=MIN_CELLS_REGIME, seed_skills=seed_skills(pooled1, kind) if kind else None)
    r2 = improvement_rule(pooled2, brk2, paired2, m, min_years_better=MIN_YEARS_BETTER, min_regimes=MIN_REGIMES, min_cells=MIN_CELLS_REGIME, seed_skills=seed_skills(pooled2, kind) if kind else None)
    RULE[m] = {"nearest_expiry": r1, "fixed_expiry": r2, "verdict": combine_labels(r1, r2)}
rule_rows = []
for m, v in RULE.items():
    for label in ("nearest_expiry", "fixed_expiry"):
        r = v[label]
        rule_rows.append({"model": m, "label": label, **{f"{k}_pass": r[k]["pass"] for k in "abcd"}, "label_pass": r["label_pass"], "verdict_both_labels": v["verdict"], **{f"{k}_detail": r[k]["detail"] for k in "abcd"}})
RULE_TABLE = pd.DataFrame(rule_rows)
print("=== decision rule (a pooled skill+MAE, b years better, c every seed, d regimes; None = not evaluable) ==="); display(RULE_TABLE[["model", "label", "a_pass", "b_pass", "c_pass", "d_pass", "label_pass", "verdict_both_labels"]])
for _, r in RULE_TABLE.iterrows():
    print(f"  {r.model:14s} {r.label:15s} a: {r.a_detail} | b: {r.b_detail} | d: {r.d_detail}")
print("VERDICTS:", {m: v["verdict"] for m, v in RULE.items()})
# the diagnostic H2 is about: the epoch early stopping selected (0-3 = effectively untrained)
BEST_EPOCH = HIST.assign(kind=HIST.run.str.extract(r"_(mlp|gru)_")[0], fold=HIST.run.str.extract(r"fold(\d+)_")[0].astype(int)).groupby(["target", "kind", "fold"]).best_epoch.agg(["min", "mean", "max"]).round(1)
print("best epoch per (target, model, fold):"); display(BEST_EPOCH)
NEAR_UNTRAINED = int((HIST.best_epoch <= 3).sum()); print(f"runs whose early stopping picked epoch <= 3 (effectively untrained): {NEAR_UNTRAINED} of {len(HIST)}")
'''


def save(v):
    s = cells_e2.SAVE
    old = '"experiment": "E-2 fixed-expiry vs nearest-expiry target"'
    assert old in s and '"# E-2 run report"' in s and '"## Common sample", md(tab),' in s
    s = s.replace(old, f'"experiment": "{v["key"]} (variant of E-2)", "variant": FEATURE_DEFS["variant"], "near_untrained_runs": NEAR_UNTRAINED, '
                       '"decision_rule": {m: {"verdict": r["verdict"], **{l: {k: r[l][k] for k in ("a", "b", "c", "d", "label_pass")} for l in ("nearest_expiry", "fixed_expiry")}} for m, r in RULE.items()}')
    s = s.replace('"# E-2 run report"', f'"# {v["key"]} run report"')
    s = s.replace('"## Common sample", md(tab),', '"## Decision rule", md(RULE_TABLE[["model", "label", "a_pass", "b_pass", "c_pass", "d_pass", "label_pass", "verdict_both_labels"]], index=False), "", "## Common sample", md(tab),')
    s += (f'print("RESULT SUMMARY -> {v["key"]} | config", cfg.sha256()[:8], "| near-untrained runs:", NEAR_UNTRAINED, "of", len(HIST), '
          '"| verdicts:", {m: r["verdict"] for m, r in RULE.items()})\n')
    return s


def neural_cell(v):
    n = cells_e2.NEURAL
    if not v.get("neural", True):
        return ("# H4: baselines only; the shared evaluation / plotting cells below expect these names\n"
                "all1, all2 = preds1, preds2\nDEVICE = {'name': 'none (baselines only, CPU)'}; NEURAL_SECONDS = 0.0\n"
                "HIST = pd.DataFrame(columns=['target', 'run', 'epochs_run', 'best_epoch', 'seconds', 'peak_gpu_mb'])\n")
    if v["pca"]:
        a = 'runner.run_neural(p1, folds, cfg, OUT_DIR / "e1_nearest", log=lambda *_: None)'
        b = 'runner.run_neural(p2, folds, cfg, OUT_DIR / "e2_fixed", log=lambda *_: None)'
        assert a in n and b in n
        n = n.replace(a, a[:-1] + ", pca_factors=PCA_FACTORS)").replace(b, b[:-1] + ", pca_factors=PCA_FACTORS)")
    return n


def eval_cell(v):
    e = cells_e2.EVAL
    if not v.get("neural", True):
        e = e.replace('("persistence", "pca_ridge", "gru_ens")', '("persistence", "pca_ridge")')
        e = e.replace('(("persistence", "-"), ("pca_ridge", "--"), ("gru_ens", ":"))', '(("persistence", "-"), ("pca_ridge", "--"))')
    return e
