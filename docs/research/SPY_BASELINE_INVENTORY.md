# SPY baseline inventory (metadata only)

**Status:** IMPLEMENTED as a documentation inventory, 2026-10-21. Built **only** from repository files; no model, test, inference, download or hash of external data was run. Values not found in the repository are written `not recorded`. Nothing here is independently reproduced ([KNOWN_LIMITATIONS](KNOWN_LIMITATIONS.md) L-29).

**Policy it supports:** OR-D2 in [orchestration/DECISIONS.md](../../orchestration/DECISIONS.md) — preserve, never retrain automatically. **Usage status:** withdrawn by the owner on 2026-10-20 ([decision.md](../../decision.md) DEC-002), then narrowly amended on 2026-10-21 (DEC-002-A, awaiting owner confirmation): private local Colab use of these held artifacts is permitted in principle, each run separately authorized; no export, public display, hosting or new data. Preserving an artifact is not authorization to run it. Artifacts are frozen: no retraining, regeneration or overwrite.

## 1. Dataset
| Item | Value | Source |
|---|---|---|
| Identifier | Kaggle `dudesurfin/spy-options-eod-volatility-surface-2010-2023` (v2, updated 2026-04-28); upstream OptionsDX | [E1_RESULTS](E1_RESULTS.md) §1; [HOSTED_DATASET_ASSESSMENT](../data/HOSTED_DATASET_ASSESSMENT.md) |
| Local path | **none** — never downloaded locally; `data/` holds only `.gitkeep` | E1_RESULTS §1; `data/` listing 2026-10-21 |
| Format / coverage | 14 parquet files; daily 4 pm snapshot; target 2010-01-04 to 2023-12-29 (3,500 surface dates) | E1_RESULTS §1; DEC-003 |
| Dataset-bytes hash | only the prefix `76bf2f94…` (run id `kaggle_eaa46df0_76bf2f94`); **full SHA-256 not recorded in the repository** | E1_RESULTS §1 |
| Provenance | uploader MIT label; **upstream OptionsDX terms unverified** → licence **UNRESOLVED**, treat as not cleared | HOSTED_DATASET_ASSESSMENT §3 |
| Usage restriction | not authorized for further runs, display or export (DEC-002, 2026-10-20) | decision.md |
| Instrument/expiry/schema | wide format: `UNDERLYING_LAST`, `EXPIRE_DATE`, `STRIKE`, `C_*`/`P_*` bid, ask, IV, Greeks, volume; American-style SPY options priced with European Black-76 on OTM mids (L-23); maturity = calendar days/365 (DEC-005) | HOSTED_DATASET_ASSESSMENT §3; KNOWN_LIMITATIONS L-23 |
| Real date coverage, gaps, row count | `not recorded` here (printed in the run's Section 6 audit, which lives on Kaggle) | HOSTED_DATASET_ASSESSMENT §3 |

## 2. Models, checkpoints, outputs
| Item | Value | Source |
|---|---|---|
| Checkpoint files | **not present in the repository or on this computer.** `artifacts/` holds only a README. Reported to exist in the owner's Kaggle account: 48 checkpoints, 56 prediction files, 171–194 output files for E-1 | E1_RESULTS §1, §7; `artifacts/README.md` |
| Checkpoint hashes | `not recorded` locally. The Kaggle run manifest holds a SHA-256 per file; its contents were not transcribed here | E1_RESULTS §1 |
| Stored forecast / run directory | none (MODEL_STATUS `available_artifacts: []`) | MODEL_STATUS.json |
| Architectures | MLP (hidden 128) and GRU (hidden 64, seq_len 20), dropout 0.1; ridge, PCA-ridge (3 components), rolling-mean, persistence baselines | `config/settings.py`, TrainConfig/FeatureConfig |
| Training config | seeds (0,1,2), max_epochs 150, patience 15, batch 128, lr 1e-3, weight_decay 1e-4; ridge alphas (0.1…1000) in E-1 | `config/settings.py` |
| Feature/preprocessing | horizon 1, lags (1,5), ffill 5 days, rv windows (5,20), rolling-mean 20; grid 6 tenors (7,14,30,60,91,182) × 9 log-moneyness nodes; scalers/PCA/fill fit on training rows only | `config/settings.py`; PHASE4 review |
| Target/label | 1-trading-day change of each cell; **nearest-expiry** (E-1) vs **fixed-expiry** (E-2, H-series) — different quantities (L-26) | E1_RESULTS; E2_FIXED_EXPIRY_RESULTS |
| Split | expanding window; validation = preceding year (H2: last 20 % of training origins); labels purged; test years 2016–2023 (8 folds); `min_train_years` 3 | `config/settings.py` SplitConfig; PHASE4 review |
| Python / library versions | E-1 run: PyTorch 2.11.0+cu128, CUDA 12.8, Tesla T4; other pip versions `not recorded` in docs | E1_RESULTS §1 |

## 3. Run records (all transcribed from notebook outputs, not from files; L-29)
| Run | Config hash (prefix) | Where recorded | Notes |
|---|---|---|---|
| E-1 | `eaa46df0…`; `kaggle_eaa46df0_76bf2f94`; scriptVersionId 357929900 and 358774908 (regenerated) | E1_RESULTS §1, §7 | pooled n = 36,793 cells / 1,954 origin days; neither neural model beat persistence |
| E-2 | `not recorded` here | E2_FIXED_EXPIRY_RESULTS | fixed-expiry label comparison |
| H1 / H1b | `eaa46df0…` (H1); H1b `not recorded` | PHASE4 review §H1, §H1b | baselines only; no model improves on persistence |
| H2 | `28b90c2a…`; `kaggle_28b90c2a_76bf2f94` | PHASE4 review | 56/96 neural runs near-untrained |
| H3 | `28b90c2a…` (config sha as printed) | PHASE4 review | 30/96 near-untrained |
| H4–H6 | `not recorded` (Colab outputs, runtime only) | PHASE4 review | H5/H6 `gru_ens`: `holds_under_fixed_expiry_label_only` (fixed-expiry skill +0.0351 in H5; negative under nearest-expiry) |

## 4. Reproducibility gaps
1. No dataset file, checkpoint, prediction file or run directory is stored locally; everything rests on the owner's Kaggle/Colab outputs and doc transcriptions.
2. Full SHA-256 values for the dataset and checkpoints are not recorded here; only prefixes.
3. The H-series notebooks in the repository carry no cell outputs; they still point at the withdrawn dataset (`config/settings.py` `kaggle_dataset`).
4. Test years 2016–2023 were reused across experiments, so H1–H6 verdicts are exploratory ([RESEARCH_DESIGN](../../orchestration/reports/RESEARCH_DESIGN.md); INDEPENDENT_REVIEW correction 5).
5. Cross-platform panel hash/manifest sensitivity (L-34) means a re-ingest on another OS may differ in `panel_sha256`.
6. The upstream licence is unverified; the 600-origin floor (below) is an owner-adopted value, not an evidence-derived one.

## 5. Scoring facts and unresolved questions
- **Verified in the repository:** maturity = calendar days/365 (DEC-005); chronological expanding-window evaluation; persistence retained as the comparator; pass rule in `evaluation/decision_rule.py` (a–e criteria).
- **Reported historical results:** the E-1/E-2/H1–H6 numbers above (descriptive, one run each).
- **600-origin minimum:** [PHASE0_FEASIBILITY_PLAN](PHASE0_FEASIBILITY_PLAN.md) M3/M4 derive it as "roughly 600 test origins from ≥ 2,000 snapshots" and state it is *a floor, not a guarantee of power*. A statistical justification for 600 specifically is **unresolved** (D's review: "underpowered in advance"; AP-008).
- **Unresolved:** any fixed-expiry vs nearest-expiry primary-scoring choice (AP-008); effect-size and multiplicity treatment of the pass rule.
