# Hosted dataset assessment (experiment E-1, 2026-10-13)

**Status:** PROPOSED for a single owner-directed experiment; **not** a product data-source decision (DEC-001/002/003 stay as they are in [decision.md](../../decision.md)). Evidence is graded as in [DATA_SOURCE_ASSESSMENT](DATA_SOURCE_ASSESSMENT.md): **G1** = read directly from the provider's machine-readable API, **U** = unknown / not verified. Nothing here was downloaded: only public listing/metadata endpoints were queried (Kaggle `datasets/list` and `datasets/view`, Hugging Face `api/datasets` and `datasets-server`), on 2026-10-13.

## 1. Constraint that drove the choice
The owner's rules for this experiment: use an existing hosted dataset, never download it to the local machine, repository or Drive as a separate step, access it directly from Colab through its official mechanism, and never commit data or credentials. A Kaggle dataset cannot be streamed; the official client places it in the Colab runtime's **temporary** cache (`~/.cache/kagglehub`), which is the only copy and disappears with the runtime.

## 2. Candidates examined

| Candidate | What it is (G1) | Licence label (G1) | Coverage (as stated) | Fit | Decision |
|---|---|---|---|---|---|
| **Kaggle `dudesurfin/spy-options-eod-volatility-surface-2010-2023`** (v2, updated 2026-04-28, ~0.6 GB) | SPY end-of-day chains, parquet, "unfiltered"; wide format with `UNDERLYING_LAST`, `EXPIRE_DATE`, `STRIKE`, `C_/P_` bid, ask, IV, Greeks, volume; 4 pm snapshot | MIT (uploader label) | 2010-2023 (stated) | Has everything needed for IV surfaces: bid/ask, spot, expiry, strike, both sides, vendor IV for a cross-check. 14 years incl. 2011, 2015, 2018, 2020 stress | **PRIMARY** |
| Kaggle `kylegraupe/spy-daily-eod-options-quotes-2020-2022` | SPY EOD quotes, three years | CC0 | 2020-2022 | Same family; too short for walk-forward training | Fallback (needs the same adapter; schema U) |
| Kaggle `shankerabhigyan/s-and-p500-options-spy-implied-volatility-2019-24` | SPY contracts: bid/ask/size/last/IV/Greeks (`contractID`, `type`, `date`) | CC0 | 2014-2025 | No underlying-price column is documented (spot would have to be inferred); 8.7 GB; different schema | Not used (adapter work and size) |
| Hugging Face `siddharthmb/stocks-options` | Equity options (date, symbol, expiration, strike, bid, ask, vol, Greeks), 43.6 M rows | none stated | 2019-02 to 2023-01 | No underlying price; SPY presence could not be verified (dataset-server filter timed out); no licence, provenance unclear | Rejected |
| Hugging Face `fabhaus/equities_5m_options` | 5-minute OHLCV bars of option contracts | "other" | 2024-2025 | No bid/ask: cannot build IV from quotes | Rejected |
| Hugging Face `papylove/alpaca-options-data` | Minute bars with technical features | none | 2025 | Not an option chain | Rejected |
| Hugging Face / Kaggle Indian-index and crypto option sets | NSE/BSE index options; Aevo crypto options | CC-BY-NC / ODC-By / CC0 | 2021-2026 | Different market; some non-commercial or short history | Rejected (market not in scope: DEC-001) |
| Cboe DataShop, OptionMetrics IvyDB, FirstRate, HistoricalOptionData | Commercial | paid | 1990/2010+ | Authoritative but paid and unobtained; the real-data track in [CBOE_LICENSING_QUESTIONS](CBOE_LICENSING_QUESTIONS.md) stays open | Out of this experiment |

No Hugging Face dataset with SPY or index end-of-day option quotes was found.

## 3. Verified vs unverified for the primary dataset
- **G1 (API metadata):** owner `dudesurfin`, MIT, version 2, parquet, size reported 509-596 MB (the listing and view endpoints disagree), data dictionary lists `[QUOTE_UNIXTIME] [QUOTE_READTIME] [QUOTE_DATE] [QUOTE_TIME_HOURS] [UNDERLYING_LAST] [EXPIRE_DATE] [EXPIRE_UNIX] [DTE] [STRIKE] [C_*] [P_*] [STRIKE_DISTANCE] [STRIKE_DISTANCE_PCT]`, stated source OptionsDX.
- **U (must be checked by the run):** actual column types (vendor exports often carry padded strings; the adapter coerces and counts failures), real date coverage and gaps, row count, share of unusable quotes. The notebook's data audit (Section 6) reports all of these and the run manifest stores the file SHA-256.
- **Licence caveat (U):** the MIT label is the uploader's. The rows originate from OptionsDX, a commercial vendor whose own terms govern redistribution and are **not verified**. Consequences: private research use only; do not redistribute the data or chain-level derived files; do not publish the results as endorsed by the vendor; treat any publication of derived surfaces as an open licensing question (compare Q-16 for Cboe).

## 4. Known suitability limits (also in [KNOWN_LIMITATIONS](../research/KNOWN_LIMITATIONS.md))
- **American-style options:** SPY options can be exercised early; the pipeline uses European Black-76 on OTM quotes only. Early-exercise premium and dividend effects are not modelled; the forward and discount factor are implied from put-call parity per expiry, which is itself approximate for American options.
- **Closing snapshot, mid quotes:** not executable prices; 4 pm quotes in thin wings are noisy; no per-contract timestamps.
- **One underlying, one vendor, one snapshot per day:** conclusions cannot be generalised.
- **Backtest only.** Nothing here implies live availability (DATA-003).
- **No risk-free-rate or dividend series** is used; the vendor Greeks are not used for modelling (vendor IV is used only as a unit-agnostic sanity ratio).

## 5. Access method (reproducible)
`kagglehub.dataset_download("dudesurfin/spy-options-eod-volatility-surface-2010-2023")` with credentials taken from **Colab Secrets** (`KAGGLE_USERNAME` + `KAGGLE_KEY`, or `KAGGLE_API_TOKEN`). The Kaggle API rejects unauthenticated downloads (HTTP 404 on `datasets/download`), so credentials are a user action. Free access; no payment. The notebook prints the dataset version (taken from the cache path) and the SHA-256 of every file it reads.