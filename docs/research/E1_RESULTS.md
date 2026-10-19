# Experiment E-1 results: hosted-data surface forecasting (executed 2026-10-13)

> **REAL market data (SPY end-of-day options, via a Kaggle-hosted dataset whose upstream licence is unverified) with DESCRIPTIVE results only.** No statistical significance, interval, calibration or trading claim is made or supported (Phase 0 inference audit closed NO-GO: [PHASE0_CLOSURE_RECORD](PHASE0_CLOSURE_RECORD.md) §7, [KNOWN_LIMITATIONS](KNOWN_LIMITATIONS.md) L-22). Backtest only. Numbers below were read from the executed Kaggle notebook (interactive session and an independent committed rerun that printed identical headline results); the saved artifacts live on the owner's Kaggle account, not in Git.

## 1. What was run

| Item | Value |
|---|---|
| Notebook | [`notebooks/Neural_Volatility_Surface_Colab.ipynb`](../../notebooks/Neural_Volatility_Surface_Colab.ipynb), generated from `backend/src/volatility_lab` (49 CPU tests OK, 1 GPU test skipped locally) |
| Data | Kaggle `dudesurfin/spy-options-eod-volatility-surface-2010-2023`, attached to a Kaggle Notebook as an input (nothing downloaded locally, to Drive or to Git). 14 parquet files; upstream OptionsDX; licence label MIT (uploader); **upstream terms unverified** ([HOSTED_DATASET_ASSESSMENT](../data/HOSTED_DATASET_ASSESSMENT.md)) |
| Compute | Kaggle Notebook, GPU **T4 x2** (code uses `cuda:0` = Tesla T4, 14.56 GiB, PyTorch 2.11.0+cu128, CUDA 12.8, cuDNN 9.19.0). Neural phase: 48 trainings in **43 s**. Whole notebook: 150 s |
| Run id / artifacts | `kaggle_eaa46df0_76bf2f94` (config SHA-256 `eaa46df0…`, dataset-bytes SHA-256 `76bf2f94…`); committed private version `scriptVersionId=357929900`: 171 output files (report, tables, plots, surface panel, 48 checkpoints, 56 prediction files, manifest with SHA-256 of every file; re-opened and re-hashed in the run) |
| Earlier GPU check | The same notebook in a **labelled SYNTHETIC** mode ran end to end on a Colab Tesla T4 (12 checkpoints, 56 files verified). That run says nothing about markets |
| Not used | Colab + Kaggle API credentials route (needs the owner's token in Colab Secrets; never entered by the assistant); Google Drive persistence (`USE_DRIVE=False`) |

## 2. Data audit (real)

- Coverage 2010-01-04 to 2023-12-29; **3,500 surface dates** (242-256 per year); largest calendar gap 13 days.
- Stage 1 (streaming pre-filter): 9,468,584 rows in, 7,037,351 kept; dropped: DTE outside 2-400 days 1,602,997, strike far from spot 819,068, no usable side 9,168.
- Stage 2 (one OTM quote per row): 7,037,351 in, **4,819,053 usable IV quotes**; dropped: no parity forward 628, |k| > 0.30 751,586, missing/zero bid 589,464, crossed or locked 253,849, mid below $0.05 494,696, relative spread above 35 % 128,075. Ledgers are conserved (every row has one reason). Zero duplicate (date, expiry, strike).
- Forward/discount from put-call parity: 72,072 slices (21,156 by regression, 25 without pairs, 0 implausible). **Vendor IV vs ours: median ratio 0.990 over 4,818,927 quotes, median absolute difference 0.31 vol points** (sanity check only).
- Quote mix: 37.3 % calls (OTM side), median 21 expiries per date, DTE percentiles 5/50/95 = 8/79/337; IV percentiles 1/5/50/95/99 = 8.2/10.3/20.0/37.7/52.2 vol pts; median relative spread 2.3 %.
- Grid (6 tenors x 9 log-moneyness nodes): observed 26.2 %, interpolated-T 54.2 %, interpolated-k 1.6 %, missing 18.0 %. Static-arbitrage flags (necessary conditions only): calendar 0 of 123,461 checks; butterfly 194 of 113,504 (0.17 %).
- Leakage audit on the real panel: features at 1,730 origins were identical when every later row was scrambled (tabular, sequence and fill values); chronology asserts passed in all 8 folds.

## 3. Out-of-sample results (8 expanding-window test years, 2016-2023)

Primary metric: cells **observed** at the target date with a real value at the origin: n = 36,793 cells over 1,954 origin days, identical for every model. Errors in vol points (1 pt = 0.01 IV). Target: 1-trading-day change of each cell. Validation year = the year before each test year; hyper-parameters fixed a priori.

| Model | MAE | RMSE | MSE skill vs persistence | Better than persistence (daily-MAE, years) |
|---|---|---|---|---|
| **pca_ridge** | 1.330 | **2.502** | **+0.051** | 3 / 8 years; 47.7 % of days |
| persistence | 1.351 | 2.569 | 0 | n/a |
| ridge | 1.411 | 2.588 | -0.015 | 0 / 8; 39.9 % |
| gru_ens (3 seeds) | 1.380 | 2.666 | -0.077 | 2 / 8; 42.5 % |
| gru seeds s0 / s1 / s2 | 1.397 / 1.396 / 1.430 | 2.679 / 2.666 / 2.722 | -0.088 / -0.077 / -0.123 | 2 / 1 / 0 of 8 |
| mlp_ens (3 seeds) | 1.406 | 2.822 | -0.207 | 3 / 8; 44.8 % |
| mlp seeds s0 / s1 / s2 | 1.420 / 1.437 / 1.415 | 2.861 / 2.845 / 2.848 | -0.241 / -0.227 / -0.229 | 3 / 3 / 2 of 8 |
| rolling_mean | 2.776 | 5.016 | -2.814 | 0 / 8; 21.8 % |

All non-missing target cells (observed + interpolated, n = 92,427): pca_ridge RMSE 1.940 (+0.037), persistence 1.977, ridge 2.005, gru_ens 2.057, mlp_ens 2.180, rolling_mean 3.915.

**RMSE by test year (observed cells)**

| Year | persistence | pca_ridge | gru_ens | mlp_ens | ridge | rolling_mean |
|---|---|---|---|---|---|---|
| 2016 | 1.581 | 1.586 | 1.605 | 1.593 | 1.842 | 3.019 |
| 2017 | 0.920 | 0.928 | 0.943 | 0.950 | 0.980 | 1.353 |
| 2018 | 2.249 | 2.167 | 2.216 | 2.323 | 2.180 | 3.548 |
| 2019 | 1.426 | 1.408 | 1.429 | 1.412 | 1.453 | 2.791 |
| 2020 | 4.864 | 4.715 | 5.167 | 5.651 | 4.871 | 10.202 |
| 2021 | 2.090 | 2.013 | 2.072 | 2.037 | 2.067 | 2.997 |
| 2022 | 2.039 | 2.050 | 2.083 | 2.032 | 2.126 | 4.003 |
| 2023 | 1.227 | 1.190 | 1.220 | 1.218 | 1.218 | 2.185 |

**By region (persistence / pca_ridge / gru_ens RMSE, n cells)**: tenor 7d 3.734 / 3.648 / 3.865 (9,009); 14d 2.597 / 2.509 / 2.682 (11,115); 30d 1.765 / 1.727 / 1.847 (10,268); 60d 1.916 / 1.902 / 2.102 (1,900); 91d 0.902 / 0.831 / 0.919 (2,287); 182d 0.790 / 0.780 / 0.855 (2,214). Moneyness k = -0.20 to +0.08: persistence 2.642, 2.557, 2.490, 2.426, 2.478, 2.514, 2.535, 2.725, 3.353 (the call wing at +0.08 has only 1,560 cells and the highest error). Realised-vol regime (train terciles): high 3.306 / 3.211 / 3.448 (18,094); mid 1.669 / 1.637 / 1.687 (8,937); low 1.437 / 1.425 / 1.463 (9,762).

**Residuals** (prediction - actual, n = 36,793): persistence std 2.569, skew -1.82, excess kurtosis 56.3; pca_ridge std 2.502, skew -3.85, kurtosis 65.7; gru_ens mean -0.19, std 2.659, skew -3.74, kurtosis 63.7. Errors are extremely heavy-tailed.

Coverage per test year (target cells / observed / interpolated / missing / evaluated): 2016 13,554/2,907/7,807/2,840/2,698; 2017 13,500/3,028/6,955/3,517/2,840; 2018 13,608/4,717/7,099/1,792/4,574; 2019 13,392/4,547/6,527/2,318/4,415; 2020 13,500/6,169/6,560/771/6,064; 2021 13,608/6,064/6,348/1,196/5,929; 2022 13,824/6,404/6,826/594/6,277; 2023 13,446/4,107/7,821/1,518/3,996.

## 4. What the evidence supports, and what it does not

**Supported (descriptive, this dataset, these 8 test years):**
- Neither neural architecture beat persistence on pooled error: the GRU seed-average is about 7.7 % worse in MSE and the MLP about 20.7 % worse. By yearly RMSE the GRU is below persistence in 3 of 8 years (2018, 2021, 2023) and the MLP in 4 of 8 (2019, 2021, 2022, 2023), but both are far worse in 2020 (GRU 5.167, MLP 5.651 vs 4.864), which drives the pooled gap.
- The only candidate that beat persistence pooled is the low-capacity PCA-ridge factor model (MSE skill +0.051). Its margin is small and uneven: it is lower than persistence in 5 of 8 test years by RMSE (2018, 2019, 2020, 2021, 2023) and higher in 3 (2016, 2017, 2022); by daily MAE it is better on only 47.7 % of days and better in 3 of 8 years; the pooled gain is concentrated in the high-volatility regime and in 2020 (4.715 vs 4.864). **Without an inferential method (unsupported), this cannot be called a real improvement.**
- Seed variation of the neural models (e.g. GRU RMSE 2.666 to 2.722; MLP 2.845 to 2.861) is smaller than the gap to persistence, so the neural shortfall is not a single-seed accident.
- The headline results reproduced in an independent fresh-session rerun (the committed version printed the same ranking, RMSEs and skills for pca_ridge, ridge and gru_ens; I did not diff every table).

**Not concluded:** that neural networks cannot forecast IV surfaces; that PCA-ridge is better than persistence in any statistical sense; that any result generalises to other underlyings, vendors, intraday data or the future; any trading, hedging or P&L value.

**Likely contributors that were NOT tested (hypotheses, not findings):**
1. *Target noise from the cell definition.* An OBSERVED cell takes the real expiry nearest the tenor (within about a day) with no time adjustment, so the anchoring expiry changes between days. The error is largest at the shortest tenors (persistence RMSE 3.7 at 7 days vs 0.8 at 182 days) and residuals are extremely heavy-tailed. A fixed-contract or fixed-expiry-tracking target would remove this composition effect and is the most valuable next experiment.
2. *Little learnable one-day signal beyond persistence at closing-snapshot quotes*, and 1,000-3,000 training samples per fold for networks with tens of thousands of weights: early stopping selected early epochs (best epoch between 0 and 38; epoch 0-2 in every 2021-fold seed), consistent with models that barely leave their initialisation.
3. *Distribution shift in the validation year.* For the 2021 test fold the validation year is 2020 and its standardised validation loss (about 6.5-6.9) is several times the training loss, so early stopping is driven by the crash year.
4. *The ridge penalty sat at the top of its grid (1000)* in 8 of 8 folds (PCA-ridge in 7 of 8): stronger penalties were not tried.

## 5. Provenance and limits

- Everything is a backtest on end-of-day snapshots. SPY options are American-style; IV is a European Black-76 inversion of OTM mids with parity-implied forward and discount factor (L-23). One underlying, one vendor, one snapshot per day (L-24). Fixed a-priori hyper-parameters, 3 seeds, 1-day horizon (L-25).
- No data and no model weights are in this repository (they are on the owner's Kaggle account); regenerate by running the notebook.
- The Phase 0 closure is unchanged: real-data feasibility of the *licensed* sources, scope approval and inferential validation remain open.

## 6. Follow-up (2026-10-13): E-2 tested hypothesis 1 of section 4

The untested hypothesis that label switching between expiries inflates the short-tenor error was tested in [E2_FIXED_EXPIRY_RESULTS](E2_FIXED_EXPIRY_RESULTS.md): **not supported**. On the identical sample, persistence is *harder* under a same-expiry label (RMSE 3.128 vs 2.700); the E-1 headline numbers reproduced exactly. Sections 1 to 5 above are unchanged.

## 7. Re-run with full plot set and forecast export (2026-10-16)

The regenerated E-1 notebook (same package, same config hash `eaa46df0...`, plus an extra-plots section 11b and `export_forecasts`) was executed on the owner's Kaggle account: private notebook `notebook320a199847`, version 1 (`scriptVersionId` 358774908), accelerator GPU T4 x2 (one device used, Tesla T4, PyTorch 2.11.0+cu128), "Save & Run All" completed in 176.8 s, 48 neural trainings in 42 s, 194 files written and re-hashed OK, output 40.59 MB, run id `kaggle_eaa46df0_76bf2f94`. The dataset was attached as an input; nothing was downloaded to this computer.

**Numbers reproduce section 3 exactly** (observed cells, 36,793 evaluated cells, 8 test years 2016-2023): pca_ridge RMSE 2.502 vs persistence 2.569 pts (MSE skill +0.051; better in 3/8 years); ridge -0.015 (0/8); gru_ens -0.077 (2/8); mlp_ens -0.207 (3/8); rolling_mean -2.814 (0/8). Only pca_ridge has positive pooled skill. Descriptive only (L-22): no significance, generalisation or trading claim.

**New records (all in the Kaggle version's output, `plots/` and `tables/plot_data.npz`; 18 figures in total, 0 plotting errors):** training curves for every fold and seed (`training_curves_all_mlp`, `training_curves_all_gru`, `training_summary`; `tables/training_summary.csv`), per-cell MAE / bias / RMSE heatmaps on the tenor x moneyness grid (`error_heatmaps`), per-cell MSE-skill heatmaps (`skill_heatmaps`), level / std / count heatmaps, daily-error and cumulative-difference curves, RMSE breakdown curves, skill by year and seed spread, and actual-vs-forecast surface heatmaps for the worst (2020-03-16), a typical and the calmest day, plus the original E-1 figures. Baseline and neural forecasts were also exported to `forecasts/<model>.npz` for the viewer API.

**Observed in the training curves and run log (descriptive):** training loss falls steadily while validation loss rises within a few epochs in most folds (best epoch 0-3 in several folds; fold 2021 has validation loss 6.5-6.9 in standardised units against about 1.0 at the start of training, best epoch 0-2), so early stopping selects an almost untrained network. This matches the neural models not beating persistence; it does not by itself explain why. Cosmetic: row titles overlap the x labels of the row above in `surface_actual_vs_forecast_heatmaps`.

