# S2 — Authorized data ingestion (separate chat; start ONLY after APPROVALS AP-002 is GRANTED)

Read `_COMMON.md`, `contracts/S2.md`, `reports/DATA_SOURCE_RESEARCH.md`, `docs/data/DATA_ACQUISITION_AUTHORIZATION.md`, and the signed authorization record in `orchestration/APPROVALS.md`. If no signed record exists, stop and report `BLOCKED`.
Owned: ingestion adapter files named in the approved scope; `reports/S2_INGESTION_REPORT.md`. Reuse the OptionsDX-format adapter conventions, `storage/raw_store.py` (write-once), the conserved ledger. Never exceed the approved source/fields/size. Execute only in Colab (see `S_colab_executor.md`). Report ledger conservation per snapshot, rejected-record counts with reasons, hashes.
