# Data acquisition authorization

**Status:** `PROPOSED` process (written 2026-10-20). It implements GR-DATA-06 and the Phase 0 requirement to review provider terms before any real-data use. It does not decide DEC-001/002/003 and grants no permission by itself.

## Rule

No new real market dataset is downloaded, scraped, purchased, copied or bulk-ingested — by a person, a script, a notebook or an AI agent — until an **authorization record** (below) exists, is signed by the project owner in chat or in a committed file, and links the evidence it relies on. A dataset being publicly reachable is not evidence of permission. The package `backend/src/volatility_lab` contains no download code and a test enforces it (`tests/unit/test_governance_guards.py::NoAcquisitionPathTests`); notebooks that read hosted data do so only on the owner's explicit, user-triggered run.

## Process

1. **Name the need** — which Phase 0 / MVD criterion ([PHASE0_FEASIBILITY_PLAN](../research/PHASE0_FEASIBILITY_PLAN.md)) cannot be met with synthetic data, and the smallest sample that would meet it.
2. **Obtain the terms in writing** — provider licence / order form / reply to the questions in [CBOE_LICENSING_QUESTIONS](CBOE_LICENSING_QUESTIONS.md) (draft, **not sent**), or for a hosted copy the *upstream* provider's terms ([HOSTED_DATASET_ASSESSMENT](HOSTED_DATASET_ASSESSMENT.md)). A repackager's licence label does not replace the upstream terms. Anything not found is written `NEEDS RESEARCH`, never assumed.
3. **Check the use against the terms** — storage, display, derived works, redistribution, model training, publication of metrics, retention and deletion; private research versus public display are separate rows.
4. **Cost and credentials** — price, who pays, where credentials live (server-side, never in Git; [SECURITY](../engineering/SECURITY.md)).
5. **Owner decision** — record `AUTHORIZED` / `AUTHORIZED FOR PRIVATE RESEARCH ONLY` / `REFUSED` with date and scope. Sending any email or placing any order is the owner's act.
6. **Ingest only through the write-once store** — `storage/raw_store.py` (content-addressed, manifest with input hashes and ledgers). Raw data never enters Git (`data/` placeholders only; checked by `scripts/foundation_audit.py`).
7. **Close the loop** — update [decision.md](../../decision.md), the register below and [KNOWN_LIMITATIONS](../research/KNOWN_LIMITATIONS.md).

## Record template

```
Dataset / provider:
Need (criterion, minimum sample):
Evidence reviewed (links, dates):  terms / licence / correspondence
Permitted: storage [ ] private display [ ] public display [ ] export [ ] model training [ ] metric publication [ ]
Unknown / NEEDS RESEARCH:
Cost and payer:
Decision: AUTHORIZED | AUTHORIZED FOR PRIVATE RESEARCH ONLY | REFUSED    Owner / date:
Scope limits and expiry:
```

## Register (what is actually authorized today)

| Dataset | Scope | Evidence | Status |
|---|---|---|---|
| Hosted Kaggle SPY end-of-day options (OptionsDX origin, 2010–2023) | **None.** The 2026-10-19 interim (private research only) was **withdrawn by the owner on 2026-10-20** (DEC-002) | Platform label only; **upstream OptionsDX licence unverified** | **REFUSED / not authorized**: no further runs, display, export or redistribution. E-1/E-2/H1–H6 remain as unpublishable history; the notebooks still reference it by name and must not be run |
| Cboe DataShop or any other paid / licensed sample | none | Questions drafted, **not sent** | **Not authorized**; no sample obtained |
| Synthetic data (`*.synthetic.*`, generated fixtures) | Any | Generated here | No licence issue; never presented as market evidence |
