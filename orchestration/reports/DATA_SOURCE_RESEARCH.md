# DATA_SOURCE_RESEARCH — Agent B (stage S1, task T-B1)

**Status:** NEEDS_APPROVAL (research complete as far as public documentation allows; §7 is an approval request the owner has not seen; nothing was acted on)
**Revision/manifest:** git HEAD `306c01b` ("finishing all the training of models H1-H6"); working tree has uncommitted owner work (`git status --short` listed 45 entries at read time; SHARED_STATUS says 44 — likely `orchestration/` itself). No Git write, no project code run, no data downloaded, no account created, no API called, no email sent. `orchestration/reports/` did not exist; creating this file created it.
**Access date for every web fact below:** 2026-10-20. **Owner direction applied:** local research tool; assess US and India separately; free first; raw bid/ask + underlying preferred; T = calendar days / 365; withdrawn hosted Kaggle/OptionsDX dataset not recommended anywhere.
**Method limits (read first):** web pages were read through a summarizing fetch tool or a search tool. Several pages could not be read: `nseindia.com` pages timed out 6 times (NSE terms were therefore **not read directly**), Databento terms render as an empty shell (still unread, same as DATA_SOURCE_ASSESSMENT §1.2), Cboe's SPY/SPX delayed-quote pages exceeded the fetch size limit, `docs.marketdata.app` did not resolve. Everything is research input, **not legal advice**, and nothing here is verified by a data sample.

### Evidence grades (same scheme as [DATA_SOURCE_ASSESSMENT](../../docs/data/DATA_SOURCE_ASSESSMENT.md) §1.1, plus one)
| Grade | Meaning |
|---|---|
| **G1** | Document text read directly (PDF/page rendered verbatim) |
| **G2** | Provider's own page via summarizing fetch (stated on the page; re-read before relying) |
| **G3** | Search-result summary or third party / forum. A lead, never a fact |
| **NR** | NEEDS RESEARCH: not found, not retrievable, or conflicting |

In the tables, "Verified" in the task prompt's sense = G1/G2 (provider's own statement); "Uncertain" = G3 or conflicting; "NEEDS RESEARCH" = NR. **No cell is verified by inspecting data** (that word stays reserved for samples, as in the existing docs).

---

## 1. Headline

| Market | Best option found | Honest bottom line |
|---|---|---|
| **US** | **Marketdata.app "Free Forever"** is the only *free* candidate found that documents historical per-contract **bid/ask + underlying price** (1-year depth, 100 credits/day). Licence is "personal non-professional / internal use" with a "creating derivative works" clause that **must be clarified in writing** before use. For long history the leads are paid: Cboe DataShop (SPX, licence text G1-clear for internal research, price unknown, SPX index level needs the >= $1,000/month indices licence) and ThetaData / Databento / Massive Advanced. | **No free source with multi-year raw historical bid/ask was found.** A free 1-year window (about 250 daily surfaces at most) can test the pipeline and data structure but **cannot** meet the MVD (>= 2,000 daily surfaces, DATA_SOURCE_ASSESSMENT §5.5) or support regime claims. |
| **India** | **No compliant free raw-quote source found.** Free official files (NSE bhavcopy / UDiFF) are end-of-day close/settlement prices with no bid/ask; free broker APIs give live chains (bid/ask) but not historical expired-contract quotes. NSE Data & Analytics sells historical F&O order-book snapshots and trades (bid/ask derivable) but price, availability and terms are **NR**. | Recommend **no India real-data acquisition now**; send two written questions (NSE Data & Analytics, plus one broker) first. NSE's website terms prohibit automated collection (G3, not read directly). |

---

## 2. What was already known (not redone) and what changes

Read: DATA_SOURCE_ASSESSMENT, HOSTED_DATASET_ASSESSMENT, CBOE_LICENSING_QUESTIONS, DATA_ACQUISITION_AUTHORIZATION, DEC-001/002/003 summary rows, SHARED_STATUS (current, dated 2026-10-20; consistent with decision.md).

Not re-verified (carried forward unchanged): Cboe DataShop product/agreement findings (§5.1 there, G1), Databento OPRA (§5.2, terms still unread), ORATS (§5.3, price conflicts), OptionMetrics/WRDS (§5.4).

**New evidence that extends or contradicts existing docs**
1. **Contradiction/clarification, DATA_SOURCE_ASSESSMENT §5.5:** Massive options plan table reconfirmed (G2): Basic $0 (2 y, end-of-day, 5 calls/min), Starter $29 (2 y, 15-min delayed), Developer $79 (4 y, trades), Advanced $199 (5+ y, trades and **quotes**, real-time). The page lists **no quotes on Basic**, so Massive free cannot supply bid/ask. Consistent with the existing screen-out; no change to ranking.
2. **New candidate not in the existing docs: Marketdata.app** (free tier with historical option bid/ask). See §3.
3. **New restriction on Cboe's free web pages:** Cboe's delayed-quote pages state that downloading quote-table data with "auto-extraction programs/queries and/or software" is prohibited, with IP blocking (G3, search excerpt of the pages [S9]). `cboe.com/terms` (last updated 2022-11-16, read G2) permits viewing/printing/downloading "one copy of the Materials" for personal non-commercial use and requires prior written consent for further copying/distribution; and `cboe.com/use-of-content` says data counts as Cboe Content needing a signed licence before reuse. So **"free to view" is not "free to automate/store"** for Cboe web pages (the explicit project trap).
4. **Cboe academic pricing lead (G3):** SEC fee filings for Cboe BZX/C2 options list an academic rate for **Open-Close historical data** (about $500-750 per year) and a free trial of up to 6 months [S10]. That product is open-close summary data, not NBBO quotes; it does not replace DataShop quotes. NR whether DataShop quote products have any academic rate (existing question Q2 in CBOE_LICENSING_QUESTIONS already asks).
5. **DATA_SOURCE_ASSESSMENT §5.5 "Interactive Brokers / Tradier: not assessed"** is now assessed: IBKR does not serve historical data for expired options and has no end-of-day option data (G3 from IBKR docs excerpt [S14]); Tradier documents only a current chain (G2 [S15]). Both screened out for this purpose.
6. **ThetaData** (not previously assessed): paid only; options history 6/10/14 years at $40/$80/$160 per month; NBBO quotes only on the two upper tiers; individual tier "personal use only, no redistribution or business use" (G2 [S16]).
7. **Alpha Vantage** HISTORICAL_OPTIONS (full chain per date, 15+ years, from 2008-01-01) is **premium-only**; bid/ask fields not stated on the page; terms of service read directly (G1) allow "personal, non-commercial" use including "research" (see §3.3).
8. India findings are entirely new to the repo (the HOSTED assessment only rejected hosted Indian sets as out of scope under DEC-001; DEC-001 itself is SPY-interim and is the owner's call whether India enters scope).

---

## 3. United States

Instruments sought: index (SPX/SPXW), ETF (SPY), stock options; quotes at a fixed daily snapshot; underlying price; expiry and strike coverage. All rows access date 2026-10-20.

### 3.1 Comparison table (grade in brackets)

| Candidate | Licence / automation | Cost | History | Instruments | Bid/ask vs last vs settle | Underlying price | Granularity | Access / limits | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| **Marketdata.app Free Forever** [S1-S4] | Terms: "own personal non-professional use" (G2). Pricing page: "Internal Use" on free/paid, redistribution only on Commercial (G2). Must **delete data downloaded** if subscription ends (G2). **No** selling/redistribution/export-file distribution (G2). **"creating derivative works"** of the Data prohibited (G2): meaning for IV/surfaces **NR**. API is the sanctioned automated channel (G2). Model training and publishing results not addressed (G2). | $0 (G2) | **1 year** on free; 5 y on Starter ($12-30/mo); unlimited on Trader ($30-75/mo) (G2) | OPRA-listed options; SPY/SPX not named on pages read (NR); index options and OPRA licensing not addressed (NR) | **bid, ask**, mid, last, volume, OI on all plans (G2). Historical chain: values "as of 16:00 ET" on the requested date; greeks **not** returned historically (G2) | `underlyingPrice` in the chain response, as of the same time (G2) | One end-of-day snapshot per requested date, 16:00 ET (G2) | API; historical chain via `date` param; 1 credit per 1,000 symbols returned; free plan 100 credits/day, resets 09:30 ET (G2). Free data described as 24 h delayed on pricing page; historical for "professional or unknown user type" is one day old (G2) | **Only free candidate with documented historical bid/ask.** Gate: written licence reply and a sample |
| **Cboe DataShop EOD Option Quotes** (existing C1) | Internal research clearly permitted (G1 agreement). Display/publication unresolved. Web-page scraping prohibited (see §2.3) | Price **NR** (cart-calculated); third-party figures $50/day full market, caps $300/month for EOD summary (G3), SPX 1-min quotes about $550/yr per window (2023, G3) | Jan 2012 to present (G2) | All OPRA-listed incl. SPX/SPXW | bid, ask, sizes, OHLC, volume, OI; vendor IV/Greeks only with Calcs (G2) | Stocks/ETFs yes; **SPX/^OEX underlying bid/ask only with CGIF licence, fees from $1,000/month** (G2) | 15:45 ET and end-of-day snapshots (G2); "Download sample" link exists (G2), cost/terms NR | Files; manual download | Best licence evidence, but **not free** and SPX index level costs extra |
| **Databento OPRA CBBO-1m** (existing C2) | **Terms unread (NR)** — page is an empty shell via fetch | Per GB; **$125 new-user credit** (existing G2); Standard $199/mo | 2013 to present (existing G3) | Incl. index options | NBBO at interval end (existing G2) | Not in options feed (existing) | 1-minute | Batch download | Unchanged from existing ranking; still blocked by B3 |
| **ThetaData Options Standard/Pro** [S16] | "Personal use only, no redistribution or business use" (G2); full terms NR | $80 / $160 per month (G2); no free tier listed | 10 / 14 y (G2) | All US stock and index options claimed (G3 via blog) | Quote tier mentions every OPRA NBBO quote (G2); EOD not mentioned | NR | Tick-level | API | Paid; plausible long-history alternative; terms NR |
| **Massive (ex-Polygon) Options** [S5] | Individual plans non-professional only (existing G2); terms NR | Basic $0; Advanced $199/mo (G2) | Basic 2 y EOD; Advanced 5+ y (G2) | All US option tickers | **Quotes only on Advanced** (G2); Basic lists none | NR | EOD (Basic) / real-time (Advanced) | API, 5 calls/min on Basic | Free tier has no bid/ask; Advanced fails "prefer free" |
| **Alpha Vantage HISTORICAL_OPTIONS** [S6, S7] | **ToS read directly (G1):** licence "for personal, non-commercial use"; commercial = purpose beyond "investment analysis, research, testing, monitoring" or any third-party access or firm affiliation; EULA lists no storage/redistribution/derivative clause; automated access via API is the product | Premium plan required; price NR; free key = 25 calls/day (G3) | 15+ y, dates after 2008-01-01 (G2) | Full chain per symbol/date (G2) | **Bid/ask not mentioned**; IV and Greeks are vendor-computed (G2) | NR | End of day | API | Not free; fields NR; low priority |
| **Alpaca options data** [S11, S12] | Terms NR | Free "Indicative" feed; OPRA feed requires paid plan (G2) | **From Feb 2024 only** (G2) | Listed options | Indicative quotes are "derivatives, not actual OPRA quotes" (G2); historical bid/ask endpoint **NR** (docs show bars) | NR | Bars | API | Too short, derived quotes: **reject** for this purpose |
| **Tradier** [S15] | Brokerage account required; terms NR | Free sandbox/brokerage data (delay NR) | Chain endpoint documents **no historical date parameter** (G2) | Listed options | bid, ask, sizes, OI in current chain (G2); IV "courtesy of ORATS" | NR | Current only | API | Current-only: usable only for **forward collection**, not history |
| **Interactive Brokers API** [S14] | Brokerage account; market-data terms NR | Account + subscriptions | **"Expired options" and EOD data for options listed as unavailable** (G3 excerpt of IBKR docs) | Listed options | n/a | n/a | n/a | Pacing limits | **Reject** (no history of expired contracts) |
| **Nasdaq.com option chain pages** | Terms **NR** (nasdaq.com terms not retrieved) | Free to view | Current only (G3) | Listed options | Current | Current | Current | Web | Treat as "free to view only" until terms read. **Not usable** |
| **Yahoo-derived tools (yfinance)** [S8, S13] | Yahoo Developer API terms (read G2) bar deriving income, require deleting Yahoo **user** data within 24 h unless stated storable, revocable; those terms do **not** mention Yahoo Finance quotes (NR which terms govern). yfinance's own notice calls Yahoo's API "personal use only" (G3) | Free | Current chain only (G3) | Listed options | Current | Current | Current | Unofficial endpoints; breakage common | **Reject:** unofficial, ToS-uncertain, no history |
| **OptionsDX / Kaggle copies** | OptionsDX terms **not found** (site links Terms page; content not retrieved; one URL 404) | n/a | n/a | n/a | n/a | n/a | n/a | n/a | **Withdrawn by owner 2026-10-20; do not use.** Record only: upstream licence still unverified |
| **FRED / U.S. Treasury (rates only)** [S17, S18] | FRED API terms (G2): own personal use fine for third-party series; permission needed from series owner for anything beyond personal; app notice required; destroy copies on termination. Treasury page shows **no reuse terms** (NR); XML feeds exist | Free | Long | Rates | n/a | n/a | Daily | API key / XML | Rates: low-risk, but record the terms (existing B6) |

### 3.2 Ranked recommendation (US), free first, raw quotes preferred (PROPOSED; none authorized)

1. **Marketdata.app Free Forever, SPY (and only after a licence reply)** — documented raw bid/ask + underlying at a 16:00 ET snapshot, $0. **Limits:** 1-year history; 24 h-delayed/"historical" framing; SPY options are American (DEC-004 conditional); quote at 16:00 ET is a snapshot whose staleness cannot be tested per contract unless an `updated` timestamp per contract exists (the field is per snapshot, G2); derivative-works wording unresolved.
2. **Cboe DataShop SPX/SPXW EOD quotes** — clearest licence text for internal research (G1), 2012+ history; blocked by price (NR) and by the CGIF requirement for the SPX level (the project could infer the forward from parity, existing Q-06, and use no Cboe index level; needs Cboe's written confirmation — already Q4 in the drafted email). **Prepared email stays unsent.**
3. **Databento OPRA CBBO-1m, 1 minute/day** — $125 credit, best timestamps, **terms unread** (B3).
4. **ThetaData Standard ($80/mo, 10 y)** — paid, individual personal-use licence; terms beyond the price page NR.
5. Everything else screened out above.

"**No compliant free multi-year raw-quote source found**" is the accurate statement for the US; item 1 is free but one year deep.

### 3.3 Licence reading notes (US)

- **Marketdata.app terms (G2, summarized):** personal non-professional; must delete downloaded data at subscription end; no sale/retransmission/redistribution or export file; no "derivative works"; API-only automation; professional status decided by exchange rules, "unknown" status restricts to delayed/historical. Open: do "derivative works" cover implied volatilities and surfaces; does the delete-on-end clause bind free-tier users; may research results/figures be published.
- **Alpha Vantage ToS (G1)** is the only terms document read verbatim for a candidate (besides the Cboe agreement already in the repo). It permits personal non-commercial research; it is silent on storage/derived data; its "commercial" test includes any third-party access, so a public viewer would flip it to commercial.
- **Exchange pass-through:** third-party summaries state that delayed/historical (older than 15 min) OPRA-derived data does not carry per-user display fees and that redistribution needs OPRA agreements (G3, [S19]); not verified against OPRA's own policy (consistent with existing "OPRA policy not consulted").

---

## 4. India

Instruments in scope if the owner adds India (DEC-001 is currently SPY-interim; this is a proposal input only): NIFTY/BANKNIFTY index options, large single-stock options. Indian index options are cash-settled and described in NSE's own 2019 data note with "CE/PE" labelled European and "CA/PA" American types (G1 [S21]); current exercise style and settlement per contract are **NR** and would need NSE contract specifications.

### 4.1 Comparison table

| Candidate | Licence / automation | Cost | History | Bid/ask vs last vs settle | Underlying | Granularity | Format / access | Verdict |
|---|---|---|---|---|---|---|---|---|
| **NSE bhavcopy (F&O UDiFF Common Bhavcopy; legacy discontinued 2024-07-08)** [S20] | NSE website terms of use: bars "systematic or automated data collection (including scraping, data mining, data extraction and data harvesting)" and copying/storing/redistribution without written permission (**G3**, from search excerpt of `nseindia.com/static/nse-terms-of-use`; page **not read directly**: timeouts). A third-party excerpt suggests an exception for content "offered for download" (G3). Whether scripted download of archive files is allowed: **NR** | Free | Long (community archive reports about 2020 to 2026 coverage, G3) | **EOD open/high/low/close, settlement price, volume, OI only; no bid/ask** (G3; legacy field list also G1 in [S21]: close, last traded price, OI, traded qty/value, trades) | Not in the file (index level via separate file, NR) | One row per contract per day | Zip/CSV, per-day files; UDiFF column names NR (must read header) | **Not a quote source.** Only usable for a clearly-labelled price-based exercise |
| **NSE Data & Analytics historical F&O** [S21, S22] | Terms and price **NR**. NSE describes a "formal framework" for historical F&O dissemination "for use in research and analysis" (G1, 2019 note) | **NR** (not in the 2019 note); NSE sells 15-min delayed/real-time feeds per display medium and requires written consent to pass delayed feeds to vendor clients (G3, [S22]) | 2003-style monthly archive is the example; actual coverage dates **NR** | **Limit-order-book snapshots (bid/ask derivable at hourly points: 11:00, 12:00, 13:00, 14:00, 15:00 in the example) and every trade** (G1 2019 note); bhavcopy | Index values: NR (CM data includes index value per G3 [S22]) | Snapshot-level, hourly; order-level fields (18 per record) | gz files | **Best structural fit for raw quotes but likely not free**; price/terms/availability require NSE reply |
| **NSE option chain web page / `/api/` endpoints** | Same website terms (automation barred, G3). Forum reports `robots.txt` disallows `/api/` and blocks cloud IPs (G3, unverified) | Free to view | Current only | Current bid/ask | Current | Snapshot | JSON behind cookies | **Do not use** (automation prohibited; no history) |
| **Zerodha Kite Connect** [S23, S24] | Forum/staff: API "intended for personal use", data distribution prohibited (G3). Official terms **NR** | Personal plan free but **no market data**; historical data needs Connect: **conflicting prices (about Rs 500 vs Rs 2,000 per month)** across sources (G3) | Candles only | OHLC candles; no historical bid/ask (NR on option-expired coverage) | NR | Minute-level candles | API, needs Zerodha account + TOTP | Not free; no historical quotes: **reject** for surfaces |
| **Dhan Data API** [S25, S26] | Terms NR (docs silent). Trading APIs free; Data API **Rs 499/month** (G3) | Paid | **Rolling expired-options OHLC + IV + OI + strike + spot, up to 5 years, 1-60 min bars, but only ATM +/- 3 (stocks) or +/- 10 (near-expiry index) strikes** (G2) | **No bid/ask** (G2); live option chain/depth endpoints exist (details NR) | Spot yes | Minute bars | API | Not free, not quotes, narrow strikes: **reject** |
| **Upstox API** [S27] | Terms NR | Free tier; **expired-instrument endpoints need Upstox Plus** (G3 from official backtesting guide) | Expired contracts: 6 months to 2 y retention, reliability issues reported (G3) | OHLC candles (no historical bid/ask) | NR | 1-30 min, day | API | Reject (not free for expired, no quotes) |
| **Angel One SmartAPI** [S28] | Terms NR | Free historical for active tokens (G3) | Staff say **no historical data for expired F&O contracts** (G3) | Candles | NR | Candles | API | Reject |
| **Fyers API v3** [S29] | Terms NR | Free (G3, community post) | History API for symbols; expired option symbols reportedly stop resolving (G3 anecdote) | Option chain returns OI, LTP, **bid & ask**, and depth (G3) | Index quote | Live snapshot | API, 100k requests/day (G3) | **Only free route to live bid/ask; no history**; usable only for owner's own forward collection after reading terms |
| **BSE bhavcopy / website** | BSE terms **not found** (search returned none) | NR | NR | NR | NR | NR | NR | **NR**, not assessed |
| **Hosted/academic Indian datasets (Kaggle, Hugging Face)** | Repackagers' labels (CC-BY-NC, ODC-By etc.) do not replace NSE's terms (DATA_ACQUISITION_AUTHORIZATION step 2) | Free | 2021-2026 per earlier listing | Unverified | NR | NR | n/a | **Not recommended**: same upstream-licence problem that caused the 2026-10-20 withdrawal |

### 4.2 Ranked recommendation (India)

1. **No compliant free raw-quote source found.** State this plainly in any decision record.
2. **Best next step is a question, not a download:** ask **NSE Data & Analytics** (a) price/terms for historical F&O order-book snapshots and trades for a small research sample, (b) whether personal non-commercial research is covered, (c) whether scripted download of the public bhavcopy archive for personal research is permitted. NSE's own 2019 note is the lead [S21]. Contact route and price list are NR; the NSE price file PDF (April 2026) was not readable here [S22].
3. **Forward collection via the owner's own broker API (Fyers is the only documented free source of live bid/ask)** is the only route to free raw Indian quotes, but yields about one surface per trading day and needs the broker's data terms read first (NR). It cannot produce a training history for years.
4. Bhavcopy-derived close/settlement surfaces would break the owner's "raw quotes" preference and the project's staleness/crossed-quote checks; allowed only as a clearly labelled mechanics exercise (§6).

---

## 5. Traps checked explicitly

| Trap | Finding |
|---|---|
| "Free to view" is not "free to automate/store" | Cboe delayed-quote pages prohibit auto-extraction (G3); NSE website terms prohibit scraping (G3); Yahoo API terms limit storage and commercial use (G2); Marketdata.app requires deleting data at subscription end (G2) |
| End-of-day close/settlement is not bid/ask | NSE bhavcopy has no bid/ask (G1 legacy fields + G3); Dhan rolling data is OHLC/IV/OI only (G2); Massive Basic lists no quotes (G2) |
| Delayed vs historical | Marketdata.app: free data "24 hours delayed"; historical chains as of 16:00 ET; label freshness per GR-DATA-07 (`historical` or `delayed`, never `live`) |
| Index options need extra licences | Cboe: SPX underlying needs CGIF from $1,000/month (G2) |
| Repackager licence labels | Kaggle/HF Indian sets and the withdrawn OptionsDX copy: upstream terms govern |
| Indian exchange redistribution | NSE requires consent to pass delayed feeds to vendor clients and prices per display medium (G3 [S22]); Zerodha says personal-use only (G3): **no public display of Indian exchange data without a licence** |

---

## 6. Smallest compliant real-data experiment per market

**Gate for both:** the DATA_ACQUISITION_AUTHORIZATION process (record, owner decision) **before** any call. Nothing below is authorized.

### US — Experiment US-1 (Marketdata.app Free, SPY, 20 dates)
- **Licence questions to answer in writing first (send to Marketdata.app support, owner's act):** (1) does "personal non-professional use" cover non-commercial research including computing implied volatilities and surfaces, given the "derivative works" clause; (2) does the delete-on-termination clause apply to free-plan data, and may derived surfaces be kept; (3) may figures/aggregate metrics be published; (4) are historical `bid`/`ask` NBBO quotes at 16:00 ET or last-known quotes; is there a per-contract timestamp; (5) which historical date range and which underlyings (SPY? SPX/index options excluded?) the free tier allows; (6) owner's professional/non-professional status determination.
- **Scope:** SPY only; 20 trading dates inside the free 1-year window chosen by a mechanical rule written before any data is seen (e.g. every 12th trading day counting back from the most recent complete day; dates therefore fall after 2025-10-20; note this cannot include a stress episode, so no regime claims).
- **Exact fields:** option symbol (or strike, expiration, side), `bid`, `ask`, `bidSize`/`askSize` if present, `underlyingPrice`, `updated`, `volume`, `openInterest`. **Exclude** vendor Greeks/IV (not returned historically per docs; IV computed here).
- **Size estimate (ASSUMPTION, not measured):** the credit rule is 1 credit per 1,000 symbols; a full SPY chain for one date may be several thousand to over ten thousand symbols, so roughly 5-15 credits per date, 100-300 credits for 20 dates, about 1-3 free days at 100 credits/day; restrict with `expiration`/`strikeLimit` to fewer. Download size of order MB. **NR until one measured request.**
- **What it can show:** field presence, bid/ask validity rates, strike/expiry density, snapshot timestamp, crossed/zero-bid shares, SPY-forward-from-parity workability. **Cannot show:** MVD (>= 2,000 surfaces), regime diversity, anything about SPX.
- **Storage:** raw files via write-once store only, never committed; key in Colab Secrets only; run only in Colab and only on the owner's explicit trigger.

### US — Experiment US-2 (alternative; paid/unknown cost)
Cboe DataShop SPX/SPXW sample or Databento $125 credit, exactly as in DATA_SOURCE_ASSESSMENT §14.4 and the drafted Cboe email (20 pre-registered dates). Still blocked by B1-B4. Not free.

### India — Experiment IN-1 (written questions only; nothing downloaded)
- Send questions to NSE Data & Analytics (§4.2 item 2) and, if forward collection is wanted, read the chosen broker's API data terms (Fyers first).
- **If and only if** NSE confirms personal research use of the public archive: 20 pre-registered dates of the UDiFF F&O bhavcopy (one zip each), fields read from the file header (strike, expiry, option type, settle/close price, OI, underlying). **Labelled mechanics exercise only**: prices are closes/settlements, not quotes; no quote-quality claims; no IV "from bid/ask".
- **If forward collection is chosen (not a download of history):** one Nifty chain snapshot per trading day at a fixed time via the owner's broker API (bid, ask, strike, expiry, side, index level); size estimate roughly 10^3 rows/day (ASSUMPTION); needs months to accumulate; broker terms **NR**.

---

## 7. Approval request (ready to submit; DO NOT ACT ON IT)

**Request ID (suggested):** AP-DATA-01 (orchestrator to renumber against APPROVALS.md).
**Decision requested (owner):** Approve, for **private, local, non-commercial research only**: (a) the owner sending the written questions listed in §6 (US-1 items 1-6; IN-1 NSE questions) and (b) **conditional on written replies that permit it**, a one-time sample of at most 20 trading dates of SPY option chains from the Marketdata.app Free Forever plan, run in Colab by the owner, authorized under the DATA_ACQUISITION_AUTHORIZATION record template.
**Evidence:** §3.1 row 1 (free tier, 1-year history, documented bid/ask, `underlyingPrice`, 16:00 ET snapshot, 1 credit/1,000 symbols, 100 credits/day, personal/internal-use terms, derivative-works and delete-on-end clauses); §4 (no compliant free Indian raw quotes found). All grades G2/G3; **no sample inspected**.
**Alternatives considered:** Cboe DataShop (best licence, price unknown, SPX needs >= $1,000/month index licence, email drafted and unsent); Databento ($125 credit, terms unread); ThetaData ($80/month, personal use); Massive Advanced ($199/month); stay on synthetic only; add India (blocked on NSE reply).
**Exact scope:** SPY; <= 20 pre-registered dates in the free window; fields in §6; no vendor Greeks; no SPX; no public display, export or redistribution of raw or chain-level derived data; raw files never in Git; API key in Colab Secrets (owner's account; owner creates it); delete obligations followed per the written reply; results labelled "backtest/historical, delayed" (GR-DATA-07) and "American-style option, European model approximation" (DEC-004).
**Cost/risk:** $0 and an owner-created free account. Risks: terms ambiguity (derivative works, deletion, publication), 1-year depth too short for any model claim, American-option approximation, vendor reliability unknown, account/API-key exposure (handled via Colab Secrets). Risk of reusing a withdrawn pattern (repackaged data) is avoided because this is the vendor's own API.
**If declined:** the project stays on synthetic data; real-data track remains BLOCKED (DEC-002); no further data research is done beyond keeping the Cboe questions drafted.
**Not requested:** any purchase, any subscription, any India download, any change to DEC-001/002/003.

---

## 8. Facts only the owner or a provider reply can resolve

1. **Marketdata.app (written reply):** derivative-works scope; free-tier deletion duty; publication of metrics/figures; real quote vs last-known at 16:00 ET and per-contract timestamp; which underlyings and date range the free plan returns; owner's professional status; exact free-plan history start date (page says "1 year"; docs on coverage and earliest date not retrieved).
2. **Cboe (existing questions Q1-Q7, unsent):** price, SPX forward-without-index-level licence, derived-data fee liability, sample, publication.
3. **Databento terms (B3):** owner reads `databento.com/legal` in a normal browser (still unreadable via tools).
4. **NSE Data & Analytics:** whether historical F&O order-book snapshots/trades are sold to individuals, price, licence, coverage dates, whether scripted archive download is allowed, and whether the website terms' "offered for download" exception exists (I could not read NSE's terms directly).
5. **Indian broker data terms** (Fyers/Upstox/Kite/Dhan/Angel): official storage/redistribution/derived-data text NR for all; Kite price conflict (Rs 500 vs Rs 2,000).
6. **BSE terms and data availability:** not assessed.
7. **Owner decisions:** market scope (SPY-interim vs adding India); whether a 1-year free sample is worth the clean-up cost; owner's professional/non-professional status; whether the project will ever display data publicly (Alpha Vantage and Marketdata.app both treat third-party access as commercial); who creates accounts and holds keys.
8. **OPRA's own vendor/derived-data policy** (unconsulted in the repo): needed if any non-owner ever sees data.
9. **Cboe web terms** `cboe.com/terms` has no explicit scraping clause (read G2); the "auto-extraction prohibited" wording is from the delayed-quote page banner (G3 excerpt): re-read in a browser if ever relevant.

---

## 9. Source index (all accessed 2026-10-20)

- S1 Marketdata.app pricing — https://www.marketdata.app/pricing/ (G2)
- S2 Marketdata.app terms — https://www.marketdata.app/terms/ (G2)
- S3 Marketdata.app options chain docs — https://www.marketdata.app/docs/api/options/chain (G2)
- S4 Marketdata.app credits/rate limit — https://www.marketdata.app/docs/api/rate-limiting (G2)
- S5 Massive options pricing — https://massive.com/pricing?product=options (G2); terms hub https://massive.com/legal/terms (points to separate individual/business terms; those pages 404'd via fetch, NR)
- S6 Alpha Vantage ToS PDF — https://www.alphavantage.co/terms_of_service/ (G1; PDF read; saved by the fetch tool under the session tool-results folder, outside the repo)
- S7 Alpha Vantage documentation — https://www.alphavantage.co/documentation/ (G2; HISTORICAL_OPTIONS section)
- S8 Yahoo Developer API terms — https://legal.yahoo.com/us/en/yahoo/terms/product-atos/apiforydn/index.html (G2)
- S9 Cboe delayed quotes pages (auto-extraction notice) — https://www.cboe.com/delayed_quotes/cboe and sibling quote-table pages (G3, search excerpt); Cboe terms https://www.cboe.com/terms (G2); use of content https://www.cboe.com/use-of-content (G2)
- S10 Cboe fee filings (academic rate, free trial) — https://www.sec.gov/files/rules/sro/cboebzx/2025/34-104367-ex5.pdf and https://www.sec.gov/files/rules/sro/c2/2025/34-104366-ex5.pdf (G3, search summary; not read)
- S11 Alpaca market data — https://docs.alpaca.markets/docs/market-data (G3)
- S12 Alpaca historical option data — https://docs.alpaca.markets/docs/historical-option-data (G2)
- S13 yfinance PyPI disclaimer — https://pypi.org/project/yfinance/ (G3)
- S14 IBKR TWS API unavailable historical data — https://www.interactivebrokers.com/docs/tws-api/doc/market-data-historical/historical-data-limitations/unavailable-historical-data (G3, search excerpt)
- S15 Tradier options chain reference — https://docs.tradier.com/reference/brokerage-api-markets-get-options-chains (G2)
- S16 ThetaData pricing — https://thetadata.net/pricing (G2)
- S17 FRED API terms — https://fred.stlouisfed.org/docs/api/terms_of_use.html (G2)
- S18 U.S. Treasury interest-rate statistics — https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics (G2)
- S19 OPRA/market-data redistribution commentary — https://www.marketdata.app/?p=10374 (G3)
- S20 NSE F&O reports page (UDiFF note) — https://www.nseindia.com/all-reports-derivatives (G3 via search excerpt; page timed out); NSE terms of use — https://www.nseindia.com/static/nse-terms-of-use (G3 via search excerpt; **not read directly**)
- S21 NSE Data & Analytics, "Historical Data Dissemination of Future and Options Segment" (2019) — https://archives.nseindia.com/content/press/Data_Details_F_n_O.pdf (G1; PDF read; saved by the fetch tool outside the repo)
- S22 NSE data products / tariffs — https://www.nseindia.com/nsedataandanalytics ; https://nsearchives.nseindia.com//web/mediaattachment/2026-03/NSE_Pricing_file_-_Domestic_clients_20260309171343.pdf ; https://nsearchives.nseindia.com//web/mediaattachment/2026-04/Download_1_min_Snapshot_15_minute_delayed_Tariff.pdf (G3 via search summary; tariff PDFs timed out, NR)
- S23 Kite Connect docs — https://kite.trade/docs/connect/v3/ (G2, intro only); Zerodha pricing/personal-plan coverage https://www.marketcalls.in/algo-trading/zerodha-makes-trading-api-free-for-personal-use-bundles-historical-data-with-connect-api.html (G3)
- S24 Kite forum posts on personal-use/data distribution — https://kite.trade/forum/discussion/comment/51277/ and related (G3)
- S25 Dhan expired options (rolling) — https://dhanhq.co/docs/v2/expired-options-data/ (G2); Dhan data API overview https://dhanhq.co/docs/v2/ (G2)
- S26 Dhan Data API subscription FAQ — https://dhan.co/support/platforms/dhanhq-api/is-the-dhanhq-data-api-subscription-free-if-i-execute-a-minimum-number-of-trades-every-month/ (G3)
- S27 Upstox backtesting/expired instruments — https://upstox.com/developer/api-documentation/backtesting (G3 via search summary)
- S28 Angel One SmartAPI forum — https://smartapi.angelone.in/smartapi/forum/post/14341 and related (G3)
- S29 Fyers API v3 — https://fyers.in/api-docs/v3/changelog/ and https://fyers.in/community/t/introducing-fyers-api-version-3-v3-0-0-a-major-update-for-improved-algo-trading/12193 (G3)
- Carried from existing docs: Cboe DataShop EOD quotes https://datashop.cboe.com/option-quotes-end-of-day-with-calcs ; Cboe quote intervals https://datashop.cboe.com/option-quote-intervals (re-read G2 this session: sample link exists, fields list confirmed, SPX underlying needs CGIF from $1,000/month, price not shown) ; quantvps comparison https://www.quantvps.com/blog/download-historical-options-data (G3)

---

## Report sections required by `_COMMON.md`

**Verified** (evidence actually in hand; no sample data exists)
- Alpha Vantage ToS text read verbatim (personal non-commercial; "research" inside the non-commercial definition; third-party access = commercial).
- NSE 2019 historical F&O note read verbatim (bhavcopy, masters, order-book snapshots, trades; 16/12/18/10-field layouts).
- Provider-page statements (G2) on Marketdata.app, Massive, Cboe DataShop, ThetaData, Tradier, Alpaca, Dhan, FRED, Yahoo Developer API terms, cboe.com/terms.

**Observed** (read, not verified by data): everything else, including all G3 items.

**Proposed:** rankings in §3.2 and §4.2; experiments US-1, US-2, IN-1; approval request §7. None authorized.

**Blocked:** NSE terms not directly read (site timeouts); Databento terms (empty shell); Marketdata.app earliest-history date and underlying coverage; NSE price file; BSE; every Indian broker's official data terms.

**Not run:** no API call, no download, no account, no email, no project code, no tests. Fetch tool saved two documentation PDFs (Alpha Vantage ToS, NSE 2019 note) under the session's tool-results folder outside the repository; they are documentation, not market data.

**Failed:** `nseindia.com` fetches (6 timeouts), `docs.marketdata.app` (DNS), Massive individual/business terms (404), OptionsDX terms URL (404), Cboe SPX/SPY delayed-quote page (10 MB limit), Databento terms (empty).

**Routed to others**
- Agent D / orchestrator: SPY is American-style; if SPY free-tier data is ever used, DEC-004 and the European Black-76 approximation caveat apply; a free-tier sample of about 12 months cannot serve walk-forward or regime evidence (MVD >= 2,000 surfaces).
- Agent C / engineering: Marketdata.app returns per-contract `bid`/`ask`/`underlyingPrice` at one snapshot and no per-contract quote timestamp is documented (staleness check cannot run on it, same as Cboe EOD); India bhavcopy would need a price-based schema variant if ever used; adapter, if ever authorized, must stay a separate, owner-triggered path (existing test forbids acquisition code in the package).
- Orchestrator: renumber AP-DATA-01 in `orchestration/APPROVALS.md`; SHARED_STATUS line count (44 vs 45) is a minor mismatch; T-B1 status to NEEDS_APPROVAL.
- Owner/docs (not edited by me): DATA_SOURCE_ASSESSMENT §5.5 "IBKR/Tradier not assessed" and §3 candidate table can be updated with §2 above; no doc was modified.

**Files changed:** `orchestration/reports/DATA_SOURCE_RESEARCH.md` (new; created `orchestration/reports/`). Nothing else.

**Handoff**
- Safe to rely on: the statement that no free multi-year raw historical bid/ask source was found in either market; the existence and terms summary of Marketdata.app Free (G2) as a candidate to verify; Cboe web pages are not an automation route; NSE bhavcopy has no bid/ask; IBKR/Tradier/Alpaca/Massive-Basic/Yahoo cannot supply multi-year historical quotes.
- Not safe to rely on: any price, history start date, or licence reading marked G3/NR; Marketdata.app credit-cost estimates; Indian exercise-style/settlement details; any claim that data is available, usable for IV/surfaces, or publishable. No data should be acquired until the owner signs a DATA_ACQUISITION_AUTHORIZATION record.
