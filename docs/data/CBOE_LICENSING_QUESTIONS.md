# Cboe Licensing and Pricing Questions — DRAFT EMAIL (NOT SENT)

**Status:** DRAFT. **This email has not been sent.** The owner reviews, completes the bracketed fields, and decides whether and how to send it. Nothing in this repository sends email, accepts terms, or contacts a provider. · **Drafted:** 2026-10-12 · **Resolves (when answered in writing):** blockers B1, B2 and part of B4 in [DATA_SOURCE_ASSESSMENT](DATA_SOURCE_ASSESSMENT.md) §10.3; open questions Q-16, Q-17, Q-19, Q-23 in [OPEN_QUESTIONS](../planning/OPEN_QUESTIONS.md); evidence for DEC-002 in [decision.md](../../decision.md).

## 1. Before sending (owner checklist)
- [ ] Fill every `[BRACKETED]` field truthfully. **Do not overstate** your status or purpose; the answers depend on it.
- [ ] Decide whether you write as an **individual** or on behalf of a **firm/institution**; this changes the applicable agreement and possibly fees.
- [ ] Confirm the addressee. The Cboe Data Policies (effective 2026-09-01) direct fee-exception questions about derived data to **marketdata@cboe.com**; the Subscriber Agreement lists **legalnotices@cboe.com** for contract notices only. DataShop's own support address was not verified when this was drafted — check the DataShop site and use it if one is listed. *(Addresses above come from Cboe documents read on 2026-10-12; confirm they are still current.)*
- [ ] Do not attach data, credentials, or code. Do not create a DataShop account or accept terms merely to send this email.
- [ ] Consider asking your institution's counsel or library to review if the use may become commercial or public.
- [ ] Keep Cboe's replies verbatim (with headers/dates) and file them with the DEC-002 ADR. Verbal answers do not count as evidence.

## 2. Draft email

**To:** marketdata@cboe.com *(and/or DataShop support — see checklist)*
**Cc:** [OPTIONAL: your institutional contact]
**Subject:** Written clarification requested — DataShop historical SPX/SPXW option data: derived-data fees, IV surfaces, display, and pricing

Dear Cboe Market Data team,

I am [OWNER NAME], a [individual researcher / student / researcher at INSTITUTION — choose one and be exact]. I am evaluating whether Cboe DataShop historical option data can support a **non-commercial research project** and would be grateful for written answers to the questions below *before* I place any order or accept any agreement.

**Intended use (summary).** I plan to license historical end-of-day option quotes for S&P 500 index options (SPX and SPXW), January 2012 onward, such as *End-of-Day Option Quotes* (with or without Calcs), and use them **internally** to: (1) validate quotes; (2) compute implied volatilities **myself** from bid/ask midpoints; (3) build standardized implied-volatility surfaces on a fixed grid of moneyness and maturity; (4) forecast next-day surfaces with statistical and machine-learning models and evaluate them out of sample; and (5) show the results in a research application and possibly in research write-ups. The work is research and education only; it involves **no trading, no investment advice, no real-time or delayed redistribution, and no sale of data**. The software would not republish raw quotes. [OWNER: add or correct anything — e.g., whether the project will ever be commercial, public, or part of a thesis/paper.]

I have read the *Historical Market Data Subscriber Agreement* (version dated 2022-05-27) and the *Cboe Global Markets North American Data Policies* (effective September 1, 2026), and I would like to confirm how they apply. Where I quote them below I refer to section numbers or headings only.

### A. Product scope
1. Do the *End-of-Day Option Quotes* products include **all SPX and SPXW series** (all listed expirations and strikes, including AM-settled SPX and PM-settled SPXW expirations) for every trading day from January 2012 to the present? Are there known gaps, missing dates, or changes in coverage over time (e.g., when daily SPXW expirations were introduced)?
2. How are **AM- and PM-settled expirations** identified in the files (root symbol, flag, or other field)?
3. Which snapshot times apply — the 15:45 U.S. Eastern snapshot and an end-of-day snapshot — and what is the exact time of the end-of-day snapshot for SPX/SPXW? Do the files contain a **per-contract quote timestamp**, or only snapshot-level timing?
4. Do the files include **underlying index values** for SPX without a Cboe Global Indices Feed licence? The product page indicates that underlying bid/ask for ^SPX requires a licence. If I do not use SPX index levels from Cboe at all (and infer forwards from the option quotes themselves), is any additional licence required?
5. Does Cboe correct or restate historical files after delivery? (The Subscriber Agreement says no corrections or updates are provided for data previously delivered; please confirm whether a restatement notice process exists.)

### B. Pricing
6. What is the **price for the full history** (January 2012 – present) of SPX and SPXW end-of-day option quotes (a) without Calcs and (b) with Calcs? Please state whether the price is per symbol/root, per file, per month of data, or full-market, whether one-time or subscription, and the date the price list took effect (a price update effective December 5, 2024 was mentioned in a secondary source I could not verify).
7. Are there **academic, student, or individual discounts**, or other pricing for non-commercial research?
8. Are there any **additional fees** (indices licence, exchange/OPRA pass-through, professional-status fees) that would apply to my use?

### C. Registration and applicable agreements
9. For my situation, should I register as an **Individual** or a **Firm**? Does my status [OWNER: individual/academic/other] affect which agreement, fees, or rights apply (including any OPRA-related professional/non-professional classification)?
10. Is the **Historical Market Data Subscriber Agreement (2022-05-27)** the current agreement for these products, or has it been superseded? Which version of the Market Data Policies applies to purchases today?
11. Are any **additional documents** required for my intended use (for example a Data Agreement, Data Order Form, or System Description)?

### D. Derived data and implied-volatility surfaces
12. I intend to compute implied volatilities, Greeks, and **standardized implied-volatility surfaces** (values on a fixed grid of moneyness and maturity, partly interpolated) from the quotes. The Subscriber Agreement (Derived Data section) permits Derived Data that is not an index or financial product and cannot readily be reverse-engineered to recreate or substitute for the Data. **Please confirm that such surfaces qualify as Derived Data for internal use**, and whether any provider-level agreement under that section's last condition is required.
13. The Data Policies describe Derived Data as generally not fee-liable, **except** where it contains or resembles price data or is based upon a single security, futures contract, currency pair or index. A volatility surface for SPX options is derived from options on a single index. **Is a standardized implied-volatility surface — and a forecast of such a surface — considered fee-liable Derived Data**, and if so under which fee schedule and at what rates? Does the answer differ for (a) purely internal use and (b) any external display?
14. Does the answer change if the surface is **coarse** (for example, a small number of grid points per day) or **aggregated** (error metrics, summary statistics, time series of at-the-money volatility)?

### E. Display, publication, and redistribution
15. I would like to display charts, 3D surfaces and heatmaps built from the derived surfaces in a research application. Please confirm which of the following require a Data Agreement, Order Form/System Description, approval, or fees:
    a. display only to me (single user, local);
    b. display to a small group of invited collaborators;
    c. display on a publicly accessible website;
    d. static figures or tables in a paper, thesis, presentation, or blog post.
16. The Data Policies state that redistributing Historical Data to non-affiliates, **including in charts, graphs and other presentations**, requires approval. Does this apply to charts of **derived** surfaces and to published research figures? Is there a level of derivation (e.g., aggregate error metrics only) at which no approval is needed?
17. May I publish **derived daily series** (for example daily at-the-money implied volatility) or **grid-point values** to collaborators or as a research dataset for reproducibility? If not, is there a licence route?
18. I understand raw quotes may not be disseminated. Does displaying an **individual underlying quote value** inside a lineage view (for the owner only) count as display of the Data?
19. May I publish **source code** and **synthetic** test data that mimic the file format (but contain no Cboe data) in a public repository?

### F. Retention and termination
20. What are my obligations on **cancellation or termination** — must stored files be deleted, and may derived results (surfaces, trained models, published figures) be retained? The Data Policies suggest internal use may continue; please confirm for both purchased history and subscriptions.
21. May I keep **backups** of purchased files for the duration of the research project?

### G. Samples
22. The product pages offer a **"Download sample"** option. What do the samples contain (dates, symbols), what terms govern them, and may I use them to test a feasibility pipeline? May I retain them after evaluation?

I would appreciate **written** replies to these questions (a reply to this email is sufficient), and I am happy to clarify the project further or to complete any forms you require. If another team (legal, licensing, or DataShop support) is better placed to answer, please forward this message or tell me whom to contact.

Thank you for your help.

Kind regards,
[OWNER NAME]
[Affiliation, if any / status]
[Email] · [Phone, optional]

## 3. Reply log (fill in when answers arrive)

| Date sent | Sent to | Date reply | Question # | Cboe's written answer (verbatim, with sender) | Evidence file | Effect on decisions |
|---|---|---|---|---|---|---|
| — | — | — | — | *No email has been sent; nothing recorded yet.* | — | — |

## 4. How replies feed the project

| Replies on | Resolves | Update |
|---|---|---|
| Q1–Q5 | Q-23, MVD M7–M8, DEC-003 | DATA_SOURCE_ASSESSMENT §5.1; DEC-003/005 notes |
| Q6–Q8 | Q-17, blocker B2; cost gate | Cost table §8; owner's spend approval |
| Q9–Q11 | Q-19, blocker B4 | DATA_GOVERNANCE |
| Q12–Q14 | Q-16, blocker B1 | DEC-002 ADR; risk RISK-10 |
| Q15–Q19 | Q-03, DEC-013 (exposure level) | SECURITY §5 exposure choice; whether any display beyond L0 is feasible |
| Q20–Q21 | Retention clause | DATA_GOVERNANCE §6 |
| Q22 | Sample route (assessment §9) | Owner decision on sample download |

**Interpretation rule:** until a written answer exists, the project assumes the narrowest reading — internal, local, single-user use; no public display; no sharing of data or derived datasets ([DATA_GOVERNANCE](DATA_GOVERNANCE.md)). This draft is not legal advice.
