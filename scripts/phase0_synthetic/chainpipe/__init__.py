"""Spike-scope engineering for the deterministic chain-to-surface path (SYNTHETIC fixtures only; stdlib only).

Maps to the planned modules in architecture.md: schema -> domain/ingestion, pipeline -> validation/pricing/surfaces,
diagnostics -> surfaces, artifact -> storage/experiments, evaluation -> datasets/evaluation. It REUSES phase0 (validation,
parity forward, OTM selection, Brent IV solver, surface construction, HistoryView, buckets) and does not modify it.
Not product code: it migrates to backend/src/volatility_lab/ once DEC-015 (toolchain) is decided."""
BANNER = "SYNTHETIC - not market data"
