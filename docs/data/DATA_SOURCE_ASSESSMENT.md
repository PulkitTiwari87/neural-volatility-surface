# Data Source Assessment

**Status:** IN_PROGRESS — **Phase 0 desk research completed 2026-10-12. No sample data has been obtained, no account created, nothing purchased, and no source is verified by measurement.** All conclusions are `PROPOSED`. · **Source:** MP §2, §6, §25 · **Work product for:** DEC-001, DEC-002, DEC-003 · **Related:** [PHASE0_FEASIBILITY_PLAN](../research/PHASE0_FEASIBILITY_PLAN.md) · [DATA_GOVERNANCE](DATA_GOVERNANCE.md) · [decision.md](../../decision.md) · [IMPLEMENTATION_PLAN](../../IMPLEMENTATION_PLAN.md) Phase 0

## 1. Purpose and method

Choose the initial market, underlying, provider and snapshot frequency on evidence — coverage, quality and **licence** — before ingestion code exists.

**What was done:** read provider pages and legal documents on 2026-10-12 using web search, a page-fetch tool, and (for one PDF) a plain-text extraction of a public document. **What was not done:** no account creation, no sign-in, no downloads of market data, no purchases, no API calls, no restricted data accessed.

### 1.1 Evidence grades (used in every table)
| Grade | Meaning | Reliability |
|---|---|---|
| **G1** | Document text read directly by the assessor | Highest. Still not legal advice; versions change |
| **G2** | Provider's own page, but delivered through a summarizing fetch tool (not read verbatim); may omit or garble details | Medium. Treat as "stated on the provider page, to be re-read" |
| **G3** | Search-result summaries or third-party sites | Low. A lead, never a fact |
| **U** | Not found / not stated / could not be retrieved | Unknown — **not** "no" |

"**Verified**" is reserved for facts confirmed by inspecting an actual sample. **Nothing is verified in that sense yet.**

### 1.2 Known limits of this research
- Databento's terms page rendered empty in both the fetch tool and the built-in browser → **terms unread**.
- Several price tables were garbled or inconsistent between pages (called out below).
- Cboe's current price list is not on the product pages I could read.
- Provider pages change; every row carries the access date 2026-10-12.
- Two public legal PDFs were saved locally by the fetch tool as a side effect (outside the repository); they are not copied into the project.

## 2. Ground rules (unchanged)
- Do not assume free access to complete historical option chains or real-time OPRA (MP §2).
- Cite source and date for every claim; unverified items stay `U`/G3.
- No scraping against terms; no credentials or paid APIs without the owner's explicit approval.
- Do not commit provider samples unless the licence expressly permits.

## 3. Candidate combinations

| ID | (Underlying, source) | Why credible | Status |
|---|---|---|---|
| **C1** | S&P 500 index options (SPX / SPXW) × **Cboe DataShop** "End-of-Day Option Quotes (with or without Calcs)" | Exchange-operated vendor of the listing venue's own product; fixed-time 15:45 ET snapshot; history from 2012-01; licence text read (G1) | Best-supported so far; **price and public-display terms unresolved** |
| **C2** | SPX/SPXW × **Databento OPRA.PILLAR** (CBBO-1m, definitions, statistics), one snapshot minute per day | Per-minute NBBO from 2013-04; nanosecond UTC timestamps; pay-as-you-go historical | Plausible alternative; **terms unread, cost not estimable without account** |
| **C3** | SPY (ETF options) × **ORATS** end-of-day files | History from 2007; includes rates/dividend fields and vendor Greeks | Lower fit: American-style options; vendor-computed IV; **price/terms conflicting** |
| **C4** | SPX × **OptionMetrics IvyDB US** via **WRDS** | Longest history (1996→), EOD quotes, IV/surface | **Conditional on institutional WRDS access (unknown)**; terms not public |
| — | Massive (formerly Polygon.io) | Options plans exist | Screened out for history depth on the plans documented (§6.5) |
| — | Broker APIs (Interactive Brokers, Tradier) | Named in MP §6 as a category | **Not assessed** — no evidence gathered |

## 4. Why the underlying matters (DEC-001 / DEC-004 input)

| Question | SPX / SPXW | SPY | Evidence |
|---|---|---|---|
| Exercise style | European (exercise at expiration only) | American — *general knowledge, U* | SPX: Cboe materials via search summary (G3) |
| Settlement | Cash. **SPX** monthly standard: AM-settled (opening prices, 3rd Friday). **SPXW** weeklies/end-of-month: PM-settled (closing price) | Physical/ETF shares — *U* | G3 |
| Pricing-model consequence | European forward-based model is appropriate (IV_METHODOLOGY §3) | Early-exercise handling needed (DEC-004) | MP §9 |
| Dividends / carry | Index: effectively a continuous yield; **forward can be inferred from put–call parity per expiry** | Discrete dividends; borrow | Parity-implied index forwards are used by ORATS for index options (G2) |
| Maturity definition | **AM vs PM settlement mixes two time-to-expiry conventions on one chain** — must be modelled in DEC-005 | One convention | G3 |
| Structural changes | A Cboe rule filing (SR-CBOE-2026-044) proposes AM-settled daily SPX expirations; **status must be checked** — the expiry cycle has changed over time and may change again | — | G3 |
| Underlying price in vendor files | SPX index bid/ask **requires an active Cboe Global Indices licence** (≥ $1,000/month) in the Cboe products | Included for stocks/ETFs in Cboe products | G2 (Cboe pages) |

**Implication (PROPOSED):** SPX is the simpler instrument for the pricing model and avoids discrete-dividend modelling, provided the forward is inferred from parity (to be tested, Q-06) and AM/PM maturities are handled explicitly. SPY remains a backup if licensing or cost makes SPX impractical, at the price of an American-option model.

## 5. Assessment tables (MP §6 nine criteria + three added)

### 5.1 C1 — SPX × Cboe DataShop End-of-Day Option Quotes

| Requirement | Finding | Source / date / grade |
|---|---|---|
| Coverage | Listed options on U.S. stocks, ETFs and indices disseminated over OPRA; options on futures and non-U.S. not supported. SPX options are implied by the index-licence notes but **not explicitly confirmed on the page** | Cboe DataShop product page, 2026-10-12, G2 |
| Granularity | Two snapshots per day: **15:45 ET** and end-of-day (exact close time "product dependent"). Separate intraday product: 1–390/405-minute intervals, subscription files delayed 15 min | Product + intervals pages, 2026-10-12, G2 |
| Quote fields | Per snapshot: bid, ask, bid size, ask size; EOD adds open/high/low/close, volume, VWAP, open interest; stock/ETF underlying bid/ask; with *Calcs* add-on: IV, Greeks, "active underlying price" (15:45) | Same, G2 |
| Timestamps | Snapshot-level only (`Quote Date` + 15:45/EOD fields); **no per-contract quote timestamp field listed** → quote staleness cannot be tested per contract; timezone ET | Same, G2 (inference from field list) |
| Adjustments | Not stated | U |
| Historical depth | January 2012 → present. Legacy end-of-day summary (volume/OI/OHLC, not quotes) 2005 → 2019-09-30 | Product pages, G2; legacy range G3 |
| Reliability / corrections | Subscriber Agreement §9: Cboe LiveVol has **no obligation to provide corrections or updates to data previously provided**; §8: content/format may change or be discontinued without notice (refund of prepayments) | Subscriber Agreement v2022-05-27, **G1** |
| Licensing — store / use | Licence is limited, non-exclusive, non-transferable, **solely for the subscriber's own personal or internal business purposes**; may not sell, distribute, transfer or otherwise disseminate Data to any other person (§1) | **G1** |
| Licensing — display / redistribution | Redistribution exists only if selected in the order: **display only**; display of Derived Data also permitted; no transfer to third parties; no sub-licensing (§2). The intervals-product order form offered only "No" for External Distribution | Agreement **G1**; order form G2 |
| Licensing — derived data | Derived Data allowed if created in whole/part from Data, is not an index or financial product, **cannot readily be reverse-engineered to recreate or substitute for Data**, and (where a provider requires) an agreement exists (§3). Internal calculation of Greeks, theoretical values and implied volatility is expressly **not** prohibited | **G1** |
| Licensing — current policies | North American Data Policies (effective 2026-09-01): *Historical Data* = data after the next trading day's open; recipients may use it **internally** (including affiliates); **redistribution to non-affiliates — explicitly including charts, graphs and other presentations — requires a signed Data Agreement, Order Form/System Description and approval, with possible extra fees**. After termination, redistribution of historical data must stop unless it is Cboe-approved Derived Data; internal use may continue. *Derived Data* is generally not fee-liable **except** where it contains or resembles price data (returns, % change) **or is based upon a single security, index, etc.**, which is generally fee-liable at the underlying product's rates. Derived-data distribution is described via the Order Form/System Description | Policies PDF, sections read directly, **G1** (partial read) |
| Licensing — **interpretive gaps** | (i) Whether a standardized implied-volatility surface for one index counts as "based upon a single … index" (fee-liable) is **not answered by the text**; (ii) whether publishing figures in a paper/blog counts as redistribution is **not addressed**; (iii) no retention/deletion clause found in the Subscriber Agreement text (policies state internal use may continue after termination) | Assessor's reading of G1 text — **needs written confirmation from Cboe** |
| Cost & limits | Product pages show subscription periods (monthly/annual) but **no prices**; the only dollar figure found is **≥ $1,000/month for the Cboe Global Indices licence** needed for SPX underlying bid/ask. A secondary page mentions a price update effective 2024-12-05 | G2; price-change note G3. **Price: U** |
| Underlying / rates / dividends | SPX underlying bid/ask only with the indices licence; rates and dividends are **not** in the listed field set | G2 |
| Exercise style & settlement | SPX European cash-settled; AM (SPX) vs PM (SPXW) | G3 |
| Raw reproducibility | Delivered as files per day or month; "Download sample" button on product pages (**not used; terms/cost unknown**) | G2 / G3 |

### 5.2 C2 — SPX × Databento OPRA.PILLAR

| Requirement | Finding | Source / date / grade |
|---|---|---|
| Coverage | Consolidated last sale and national BBO across US equity-options venues; includes stock, ETF and **index options** — SPX appears in the dataset's symbol table | Databento OPRA dataset page, G2; launch post G2 |
| Granularity | Schemas include CMBP-1, CBBO-1s, **CBBO-1m**, TCBBO, Trades, OHLCV (1s/1m/1h/1d), Statistics, Status, **Definition**. CMBP-1 is very large ("several terabytes" per day) — avoid | G2 |
| History | Dataset from **2013-04-01**; per-schema starts "could vary". CBBO-1m reported from 2013-04 after a 2025 extension (G3); CBBO-1s from 2023-03-28 (G3). **Whether pay-as-you-go includes full Level-1 history is unclear**: the tier table was garbled and appears to cap Level-1 history by plan (12 months / 3 years / 13+ years) | Dataset page G2; extension/start dates G3 |
| Quote fields | CBBO schemas carry NBBO and last sale at fixed intervals; exact field list, **open interest** (via Statistics?) and **exercise-style/instrument-class fields in Definition** not retrieved | G2/U |
| Timestamps | `ts_event` and `ts_recv` as nanoseconds since UNIX epoch, UTC via PTP; hardware-timestamped capture | G2 — **best timestamp quality of the candidates** |
| Historical delay | Historical data delayed 1 hour or next day at 09:30 ET | G2 |
| Underlying / rates / dividends | **No index level in the options feed**; the forward would be inferred from parity or a separate source | Assessor inference from schema list, U |
| Licensing | Blog: no exchange licence is needed to receive historical (≥ 24 h old) data; **redistributing historical data can require a licence**; non-professional vs professional status concerns real-time/delayed. **Databento's own Terms were not readable** — rights to store, display, publish derived surfaces are **unknown** | Licensing blog G2; Terms **U** |
| Cost & limits | Usage-based pay-as-you-go for historical (billed **per GB** of uncompressed binary; CSV/JSON no extra charge; batch re-download 30 days); new-user **$125 free historical credits expiring after 6 months, one set per team**; Standard **$199/month** includes live data and no license fees. Plus/Unlimited plan license fees differ **between the OPRA page ($1,500 / $4,000) and the general pricing page ($1,750 / $4,500)**; per-GB rate for CBBO-1m not retrieved; a cost estimator exists in the account/API | G2 (pages inconsistent) |
| Adjustments / corrections | Definition schema exists; policy not retrieved | U |
| Raw reproducibility | Batch downloads can be stored locally; historical stability/restatement policy not retrieved | U |

### 5.3 C3 — SPY (and indices) × ORATS end-of-day

| Requirement | Finding | Source / date / grade |
|---|---|---|
| Coverage | > 5,000 symbols, end-of-day history **from 2007**; index options covered (ORATS solves an implied futures price per expiry); SPX itself **not named** on the pages read | ORATS pages, G2 |
| Granularity | EOD snapshot taken ~14 min before the close (≈ 15:46 ET); 1-minute intraday from 2020 (pages conflict on Aug/Oct 2020); tick prints from 2022-09 | G2 |
| Quote fields | NBBO bid/ask for calls and puts, call/put volume and open interest, underlying price (+ cash index price), **vendor** bid/mid/ask IV, Greeks, theoretical values, **`iRate`, `divRate`**, contract identifiers; bid/ask **sizes not stated** | near-EOD page, G2 |
| Timestamps | Snapshot-level; OPI updated by OCC the prior night | G2 |
| Corrections | Not stated | U |
| Licensing | **Not stated** on the pages read; a third-party summary mentions "individual (non-pro) use only" for one plan; purchase of the hard-drive product says the licence is "included in the purchase" (terms not read) | G2 / G3 / U |
| Cost & limits | Recurring EOD **$99/month (individual tier)**; one-time historical (2007→, ~500 GB) shown as **$599** on one page and **$399** in a search summary of another; delayed API shown as **$199** on one page and **$99** in a search summary → **inconsistent, unverified**; institutional pricing by quote; historical S3 access lasts 14 days after purchase | G2 / G3 |
| Fit concerns | IV and Greeks are **ORATS-computed**; this project computes IV itself (MP §9), so only bid/ask and identifiers would be used | — |

### 5.4 C4 — SPX × OptionMetrics IvyDB US (via WRDS)

| Requirement | Finding | Source / date / grade |
|---|---|---|
| Coverage / depth | U.S. exchange-traded equity and index options, **end-of-day, January 1996 → present**; includes ETF options | OptionMetrics + WRDS pages, G2 |
| Content | Bid/ask, volume, open interest, IV and Greeks computed with American and European models, interest-rate/dividend/corporate-action information; standardized constant-maturity surface on a delta grid | G2; surface grid details G3 |
| Access | Distributed through **WRDS**; an institutional subscription is the described route. Whether the owner's institution subscribes is **unknown** | G2 |
| Licensing | Marked a "custom licence"; terms **not public** in the pages read | G3 / U |
| Cost | **Not public** | U |
| Fit | Longest history and 2008/2020 regimes; EOD-only closing quotes; vendor surface is delta-based (this project builds its own from quotes) | — |

### 5.5 Screened out / not assessed
- **Massive (formerly Polygon.io):** options plans listed as Basic $0 (2 years, EOD), Starter $29 (2 years), Developer $79 (4 years, trades only), **Advanced $199 ("5+ years", trades and quotes)**; individual plans tagged non-professional only; business plans not priced on the page. Historical **quotes** are listed only on Advanced and, per one secondary source, a Business tier lists quotes only since 2022 (G3). On the documented depth it **cannot meet the proposed MVD (≥ 2,000 daily surfaces)** → screened out unless the pricing page is shown to say otherwise. (G2/G3)
- **Interactive Brokers / Tradier:** MP §6 names brokers as a category. **No evidence gathered; not assessed.** Whether they provide historical option chains at all is unknown.
- **Historicaloptiondata.com** (third-party SPX history "from 1990"): surfaced in a search; **not evaluated** (licence and provenance unknown, G3).

## 6. Reference data (rates, forwards)
- **Risk-free rate:** U.S. Treasury publishes daily par-yield-curve and bill rates, based on indicative quotations obtained ~15:30 ET each business day (page read 2026-10-12, G2). That timing sits just before a 15:45 snapshot — acceptable in principle; alignment to be tested. **The page does not state reuse/copyright terms (U).**
- **Forward / dividends for SPX:** infer per expiry from put–call parity on the snapshot (a method ORATS describes using for indices, G2). **Unvalidated for this project** → Q-06 and the feasibility experiment.
- **SPY dividends:** would require a dividend source (ORATS publishes dividend files, G2) — only needed if C3/SPY is chosen.

## 7. Licence conclusions by candidate (PROPOSED; not legal advice)

| Use | C1 Cboe | C2 Databento | C3 ORATS | C4 OptionMetrics |
|---|---|---|---|---|
| Store raw files locally for own research | **Permitted for personal/internal use** (G1) | Likely (historical needs no exchange licence, G2) — **terms unread (U)** | U | Per institutional agreement (U) |
| Compute IV/Greeks/surfaces internally | **Expressly allowed** (G1 §3) | U | U | U |
| Show derived surfaces to others / public app | **Requires approved redistribution and possibly fees** (G1 policies); order form offered "No" externally (G2) | U | U | U |
| Publish figures in a paper / blog | **Unclear — ask Cboe** | U | U | U |
| Commit data to a public repository | **No** (dissemination prohibited, G1) | Assume no (U) | Assume no (U) | Assume no (U) |
| Survives subscription end | Internal use may continue; redistribution must stop (G1 policies) | U | U | U |

**Consequence for architecture (PROPOSED):** treat the initial deployment exposure as **L0 local single user** ([SECURITY](../engineering/SECURITY.md) §5) and do not build any public display of provider-derived values until a written licence conclusion exists (DEC-013 stays open).

## 8. Costs — what is and is not verifiable

| Item | Amount | Basis | Grade |
|---|---|---|---|
| Cboe EOD Option Quotes (SPX/SPXW), history 2012→ | **Not published on pages read** | Subscription periods shown, no prices | U |
| Cboe Global Indices licence (only for SPX underlying bid/ask) | **≥ $1,000 / month** | Stated on two Cboe product pages | G2 |
| Databento historical OPRA | **Per GB; rate not retrieved**; $125 new-user credit (expires 6 months); Standard plan $199/month (includes live data, probably unnecessary for historical research) | Pricing + OPRA pages (inconsistent plan figures) | G2 |
| ORATS | $99/month recurring individual; one-time historical $599 or $399 (conflict) | Provider pages | G2 / G3 |
| Massive options Advanced | $199/month ("5+ years") | Pricing page | G2 |
| OptionMetrics / WRDS | Not public | — | U |
| **Estimated cost of the Phase 0 pilot sample** | **$0 only if** Cboe's "Download sample" or Databento's free credit works as advertised — **neither has been tested**. Otherwise unknown | — | U |

No spending is authorized or recommended by this document.

## 9. Is a permitted historical sample available?

**Determination: no permitted real sample is in hand.** Leads, each needing an owner action and acceptance of terms (none taken):

| Lead | What would be needed | Status |
|---|---|---|
| Cboe DataShop "Download sample" on option-quote product pages | Owner account/terms; read what the sample covers and its terms | G3 (button reported), untested |
| Databento free credit ($125) | Owner account; use the cost estimator first | G2, untested |
| ORATS University historical samples | Terms unknown | G2 (mentioned), untested |
| WRDS `optionmsamp_us` sample library | Institutional WRDS access | G3, untested |
| Massive Basic (free, 2 years EOD) | Account; likely too short for MVD but adequate as a *format* sample | G2, untested |

**Default for Phase 0:** a clearly labelled **synthetic sample** ([PHASE0_FEASIBILITY_PLAN](../research/PHASE0_FEASIBILITY_PLAN.md) §4). It can exercise every pipeline stage but **cannot** satisfy the real-data availability evidence required by the Phase 0 exit gate (see §10).

## 10. Comparison, provisional ranking, blockers, and exit evidence

### 10.1 Against the decision criteria (§11 below, weights agreed before scoring)
| Criterion | C1 Cboe SPX | C2 Databento SPX | C3 ORATS SPY | C4 OptionMetrics SPX |
|---|---|---|---|---|
| 1 Licence permits intended use (hard gate) | **Internal research: yes (G1).** Public display/publication: **unresolved** | **Unknown (terms unread)** | Unknown | Unknown / access-dependent |
| 2 History & regime diversity | 2012→ (≈ 14 y: includes 2015–16, 2018, 2020, 2022) *(regimes by assessor knowledge, U)* | 2013→ (CBBO-1m, tier-dependent) | 2007→ (includes 2008) | 1996→ |
| 3 Required fields & timestamps | Bid/ask/size/OI at fixed snapshots; no per-quote timestamp | Bid/ask/size; best timestamps; fields to confirm | Bid/ask (no sizes stated), vendor IV | Bid/ask, EOD |
| 4 Strike/expiry density | Expected high for SPX (**unmeasured**) | Same (unmeasured) | Unmeasured | Unmeasured |
| 5 Cost | **Unknown** | Pay-per-GB; likely modest for one minute/day (**unestimated**) | $99–$599 range (**conflicting**) | Unknown |
| 6 Reproducibility/stability | Files; no corrections provided (G1) | Unknown | Vendor-modified fields | Annual updates |
| 7 Exercise-style simplicity | European (SPX) | European (SPX) | American (SPY) | Either |

### 10.2 Provisional ranking (PROPOSED)
1. **C1 — SPX × Cboe DataShop EOD quotes (15:45 ET snapshot):** best-supported, mainly because the **licence text was actually read** and is clear for internal research; the fixed snapshot and field set match the MVD. *Not verified by any sample; price unknown; display/publication rights unresolved.*
2. **C2 — SPX × Databento OPRA (single-minute CBBO per day):** strongest timestamps and likely flexible cost, but **terms unread and cost unestimated**; the best fallback and a useful cross-check source.
3. **C4 — SPX × OptionMetrics via WRDS:** the best history, **only if** the owner already has institutional access; otherwise out.
4. **C3 — SPY × ORATS:** lowest fit (American options, vendor IV, conflicting pricing, terms unstated).

### 10.3 Outstanding licensing blockers
| # | Blocker | Needed to clear |
|---|---|---|
| B1 | Whether a standardized SPX IV surface is "Derived Data … based upon a single … index" (fee-liable) and whether public display/publication needs an approved Order Form | Written reply from Cboe market-data/legal (contacts named in their documents). **Draft questions prepared, not sent:** [CBOE_LICENSING_QUESTIONS](CBOE_LICENSING_QUESTIONS.md) |
| B2 | Cboe price for SPX/SPXW EOD option quotes, 2012→ | Price list or written quote |
| B3 | Databento terms (store/display/derived/publish) | Owner reads `databento.com/legal` in a browser; paste relevant clauses into the ADR |
| B4 | Professional vs. non-professional status of the owner for OPRA-sourced data | Owner declaration + provider/exchange definitions |
| B5 | Intended audience/exposure (Q-03) | Owner decision |
| B6 | Treasury/FRED reuse terms for rates | Read terms; likely permissive but **unverified** |
| B7 | Owner's WRDS/OptionMetrics access (C4) | Owner check with library |

### 10.4 Exact evidence required to exit Phase 0
Phase 0 exits only when **all** of the following exist as linked artifacts (see [IMPLEMENTATION_PLAN](../../IMPLEMENTATION_PLAN.md) and [PHASE0_FEASIBILITY_PLAN](../research/PHASE0_FEASIBILITY_PLAN.md)):

1. **Licence evidence:** B1–B4 closed with written provider replies (or product-page text plus accepted terms) attached to the ADR for DEC-002; checklist in [DATA_GOVERNANCE](DATA_GOVERNANCE.md) §3 fully answered.
2. **Real sample evidence:** a permitted sample (or, for a full-history purchase, a provider-supplied listing) from the chosen source, with the measured statistics in [PHASE0_FEASIBILITY_PLAN](../research/PHASE0_FEASIBILITY_PLAN.md) §5 for ≥ 20 pre-selected dates, confirming SPX/SPXW presence, fields, snapshot timestamps and density.
3. **Availability evidence against the MVD:** counts of available trading days, gaps, and regime coverage (M3–M5) from provider metadata or purchase listing.
4. **Cost evidence:** a written price or estimator output for the full MVD history; the owner's approval of the spend (none is made here).
5. **Frozen criteria:** owner-signed MVD thresholds and success criteria (PHASE0_FEASIBILITY_PLAN §7), including pilot-derived *c* and ρ.
6. **Synthetic feasibility run recorded:** the F0–F8 experiment run on the synthetic sample with S3, S4, S6–S8 results in a run record. **Done 2026-10-12** (owner-approved spike, ADR-0003): see [PHASE0_SYNTHETIC_RESULTS](../research/PHASE0_SYNTHETIC_RESULTS.md) — 57 tests passed at first run, 112 after the audit's regression and A2d tests ([PHASE0_AUDIT](../research/PHASE0_AUDIT.md)); failures and protocol deviations disclosed there. This item covers **synthetic** evidence only and does not satisfy items 2–3.
7. **ADRs:** DEC-001, DEC-002, DEC-003 set to `DECIDED` with the evidence above; DEC-004/005 drafts reflecting AM/PM settlement and the forward-from-parity approach.
8. **Decision on exposure** (L0 local vs wider) recorded (Q-03).

If item 2 or 3 fails, **re-scope** (different source/underlying/frequency) rather than proceed.

## 11. Decision criteria (weights agreed before scoring; unchanged)
1. **Licence permits the intended use** (hard gate; fail ⇒ reject or restrict scope).
2. Sufficient history and regime diversity for the MVD.
3. Required fields present with timestamps allowing the alignment policy.
4. Strike/expiry density adequate for the target grid.
5. Cost within the owner's budget (no commitments without approval).
6. Reproducibility and stability of historical data.
7. Exercise-style simplicity (affects pricing model).

## 12. Red flags (updated with findings)
Terms prohibiting storage or derived-data display · vendor-computed IV only · undocumented adjustments/corrections (Cboe: **no corrections provided** → store what you got, version it) · timestamps without per-quote values (Cboe EOD: snapshot-level only) · survivorship (expired contracts) · unstable history between pulls · **AM/PM mixed settlement** on one SPX chain · price pages that contradict each other (Databento plan fees; ORATS prices).

## 13. Sources (accessed 2026-10-12)
**Primary / G1:**
- Cboe LiveVol, *Historical Market Data Subscriber Agreement*, v. 2022-05-27 — https://datashop.cboe.com/documents/Historical_Market_Data_Subscriber_Agreement.pdf
- Cboe Global Markets, *North American Data Policies*, effective 2026-09-01 (Historical Data, Derived Data, Record Retention sections read) — https://cdn.cboe.com/resources/membership/Market_Data_Policies.pdf

**Provider pages / G2:**
- Cboe DataShop, End-of-Day Option Quotes with Calcs — https://datashop.cboe.com/option-quotes-end-of-day-with-calcs
- Cboe DataShop, Option Quote Intervals — https://datashop.cboe.com/options-intervals
- Databento OPRA.PILLAR dataset — https://databento.com/catalog/opra/OPRA.PILLAR
- Databento pricing — https://databento.com/pricing
- Databento, OPRA launch post — https://databento.com/blog/opra-data
- Databento, market-data licensing primer — https://databento.com/blog/introduction-market-data-licensing
- ORATS data API — https://orats.com/data-api ; historical files — https://orats.com/university/historical-data ; near end-of-day — https://orats.com/near-eod-data
- OptionMetrics historical options data — https://lp.optionmetrics.com/historical-options-price-data
- Massive options pricing/overview — https://massive.com/options
- U.S. Treasury interest-rate statistics — https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics

**Search summaries / G3 (leads only):** Cboe SPX fact sheets and settlement descriptions (https://cdn.cboe.com/resources/spx/spx-fact-sheet.pdf; rule filing https://cdn.cboe.com/resources/regulation/rule_filings/approved/2026/SR-CBOE-2026-044.pdf); WRDS vendor page (https://wrds-www.wharton.upenn.edu/pages/about/data-vendors/optionmetrics/); Databento CBBO start dates (databento.com/blog/opra-improvements-coming-soon); third-party price comparisons for ORATS and Massive.

**Not retrievable:** Databento Terms (https://databento.com/legal renders empty); Cboe price list; OptionMetrics/WRDS licence text; OPRA's own vendor/derived-data policy (not consulted).

## 14. Engineering-feasibility addendum (2026-10-13; public documentation only)

**Scope and method.** Re-checked only what the engineering work needs: can each candidate's *documented* fields populate the spike's canonical chain schema (`chainpipe/schema.py`: `quote_timestamp, underlying_id, underlying_price, expiration, strike, option_type, bid, ask, origin, source`)? Public pages and public crate documentation only; no account, sign-in, download, purchase, contact or credential. Grades as in §1.1. **Nothing here is verified by a sample.** This addendum changes none of §10's rankings or blockers; it adds the mapping and one recommended next decision. Implementation status: [IMPLEMENTATION_MATRIX](../engineering/IMPLEMENTATION_MATRIX.md) (no provider adapter is built).

### 14.1 Newly read this session
| Fact | Source | Grade |
|---|---|---|
| Databento definition record has `strike_price` (i64, **1e-9 fixed-point**), `expiration` (u64, ns since UNIX epoch, null sentinel allowed), `instrument_class` (single char), `underlying` (symbol), `underlying_id`, `security_type`, `exchange`, `currency`, `strike_price_currency`, `settl_currency` | docs.rs `dbn` crate, `InstrumentDefMsg` (page read via fetch tool, paraphrased table) | G2 |
| That page lists **no exercise-style field**; European vs American and AM vs PM settlement would have to come from elsewhere (symbol root / underlying choice) | same | G2 (absence on one page ≠ absence in the schema → **U**) |
| Databento consolidated-BBO record carries `levels[1]` with `bid_px`, `ask_px` (i64, 1e-9 fixed-point), `bid_sz`, `ask_sz` (u32), `bid_pb`, `ask_pb` (publisher IDs), plus last-trade `price`/`size`/`side`, `flags`, and `ts_recv` = interval end time | docs.rs `dbn`, `CbboMsg` and `ConsolidatedBidAskPair` | G2 |
| `databento.com` documentation and terms pages render as an empty shell or truncated text through the fetch tool; **Databento's Terms remain unread** (B3 unchanged) | fetch of `/terms`, `/docs/schemas-and-data-formats/*` | U |

### 14.2 Field mapping to the canonical schema (documented fields only)
| Canonical field | C1 Cboe EOD quotes | C2 Databento OPRA (CBBO-1m + definition) |
|---|---|---|
| `quote_timestamp` | Snapshot-level only (`Quote Date` + 15:45 ET / EOD); **no per-contract timestamp** → staleness untestable (G2) | `ts_recv` interval end, ns UTC (G2); per-contract last-update time not shown on the pages read (U) |
| `underlying_id` / `underlying_price` | Underlying price for stocks/ETFs included; **SPX index level needs the Cboe Global Indices licence** (G2); "active underlying price" with *Calcs* (G2) | **Not in the options feed** → separate source or parity-inferred only (U); `underlying` symbol in definitions (G2) |
| `expiration` | Contract field (format U) | `expiration` ns timestamp in the definition record; it is "last eligible trade time", not a settlement-convention label (G2) → AM/PM must be derived, not read |
| `strike`, `option_type` | Contract fields (G2) | `strike_price` ÷ 1e9; `instrument_class` char decoded to call/put (code table not read, U) |
| `bid`, `ask` (+ sizes) | bid, ask, bid size, ask size (G2) | `bid_px/ask_px` ÷ 1e9; `bid_sz/ask_sz` (G2) |
| Open interest (not in canonical schema) | Present in EOD (G2) | Via Statistics schema (U) |
| Provider IV/Greeks | Only with *Calcs* add-on; **must not be used** (the project computes IV itself) | Not provided in CBBO (G2) |
| `origin` / `source` | Set to `provider` and a provider/version string by the adapter; raw files kept immutable | same |

**Consequences for the engineering design (PROPOSED):** (1) the canonical schema already fits both candidates' bid/ask fields; (2) both need a **separate underlying/rate source** or a parity-inferred forward, which the pipeline already supports (forward is inferred per expiry; rate is a config constant); (3) neither documents an exercise-style field, so SPX European treatment must remain an explicit configuration assumption; (4) fixed-point price decoding (÷ 1e9) is an adapter concern, not a schema one; (5) Cboe's lack of a per-contract timestamp means the staleness check cannot be exercised on that source.

### 14.3 Unresolved access decisions (all owner-side; none taken)
B1–B4 and B6–B7 in §10.3 are unchanged. Nothing was purchased, requested or downloaded. No sample exists, so the Phase 0 real-data exit items (§10.4 items 2–4) are **still open**.

### 14.4 Recommended next decision (PROPOSED, owner's)
Decide **whether the owner will take the one low-cost, reversible access step**: read Databento's Terms in a normal browser session (B3, free) **and** use the Databento cost estimator for a single CBBO-1m snapshot-minute per day for 20 pre-selected dates, *or* send the prepared Cboe questions ([CBOE_LICENSING_QUESTIONS](CBOE_LICENSING_QUESTIONS.md)). Either unblocks a permitted ~20-date sample, which is the evidence the adapter, Q-25 (`observed` definition) and the pricing assumptions all wait on. This is a recommendation, not an authorization; no spend is implied.

**Sources added (2026-10-13):** `https://docs.rs/dbn/latest/dbn/record/struct.InstrumentDefMsg.html` · `…/struct.CbboMsg.html` · `…/struct.ConsolidatedBidAskPair.html` (public crate documentation, G2).
