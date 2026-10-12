# ADR-0003: Toolchain, dependencies and scope for the Phase 0 synthetic feasibility spike

- **Status:** Proposed — **scoped to the Phase 0 spike only.** The owner approved doing this work on 2026-10-12 and asked that these choices be documented first; formal acceptance of the ADR remains the owner's call. This ADR does **not** decide the product toolchain.
- **Date:** 2026-10-12
- **Decision register entry:** DEC-015 (product toolchain stays `OPEN`; this is a spike-scope sub-decision) — see [decision.md](../../../decision.md)
- **Deciders / responsible role:** Project owner; implemented by the assistant under the owner's instruction
- **Phase / requirement IDs affected:** Phase 0 (A5, S3–S9 in [PHASE0_FEASIBILITY_PLAN](../../research/PHASE0_FEASIBILITY_PLAN.md)); SCI-007/008/009, GR-QNT-01/02/06, GR-LEAK-01, GR-DATA-04/05, GR-ENG-02

## Context
Phase 0 requires running the whole analytical path once on **clearly labelled synthetic data** ([PHASE0_FEASIBILITY_PLAN](../../research/PHASE0_FEASIBILITY_PLAN.md) §4–§5) before any real data, provider, or product toolchain is chosen. No manifest, lockfile or dependency decision exists (DEC-015). The brief forbids installing dependencies until the toolchain and requirements are documented. Observed on the development machine (read-only check, 2026-10-12): **Python 3.12.6, Windows 11 (AMD64)**; numpy, scipy, pandas and pytest happen to be installed globally, which is **not** a project decision and is not relied on.

## Options considered
1. **Standard library only + `unittest`.** No installs; every numerical step (Black-76 price, Brent solver, interpolation, OLS, bootstrap) is explicit and hand-checkable; nothing hidden in library defaults; trivially reproducible on any Python. Slower than vectorized code.
2. **numpy/scipy (+ pytest).** Faster; `scipy.optimize.brentq` and `scipy.stats.norm` are well-tested. But introduces dependencies that DEC-015 has not approved, depends on the machine's global packages (not a controlled environment), and hides solver behaviour that the spike exists to specify.
3. **pandas-based pipeline.** Convenient for tabular work; adds a heavy dependency and implicit behaviours (indexing, NaN semantics) that conflict with the "no silent missing values" guardrails.

## Evaluation criteria (fixed before implementation)
No new dependencies (GR-ENG-02); determinism and hand-checkability; independence from the machine's global packages; sufficient speed for the spike's size (~10⁵ quotes per run); disposability.

## Evidence
Run size estimate: ~300 days × ~6 maturities × ~25 strikes ≈ 4.5×10⁴ implied-volatility solves per full run; a pure-Python bracketed solver evaluating `erfc` is expected to handle this in seconds to tens of seconds. Speed will be **measured and reported** in the results document; if it proves inadequate for the spike, that is a finding for DEC-015, not a reason to add dependencies mid-spike.

## Decision (spike scope only)
1. **Python:** 3.12.6 as observed; code is written to avoid version-specific features and **tested only on 3.12.6** — no compatibility claim for other versions.
2. **Dependencies:** **standard library only** (as implemented: `math`, `random`, `statistics`, `bisect`, `collections`, `dataclasses`, `enum`, `typing`, `hashlib`, `json`, `argparse`, `platform`, `sys`, `time`, `pathlib`, `unittest`; verified by search — no network, subprocess, `os`, or third-party imports). **Nothing is installed.** No manifest or lockfile is created (there is nothing to lock). Source-file hashes and the interpreter version are recorded in every run record instead.
3. **Test runner:** `unittest` (`python -m unittest discover`). pytest-compatible but not required.
4. **Random numbers:** `random.Random(seed)` using only `.random()`; normal variates by an explicit Box–Muller transform (no reliance on `gauss`/library normal samplers). Same-platform bit-reproducibility is tested; cross-platform last-bit differences are possible (libm) and are mitigated by hashing metrics after rounding.
5. **Location:** `scripts/phase0_synthetic/` — **outside** `backend/src/volatility_lab/`; no product module imports it. It is a disposable spike; only its **findings** inform later decisions. If the spike's code is later adopted, it must be re-reviewed, moved, and re-tested under the product toolchain.
6. **Synthetic labelling:** every generated record carries `origin = "synthetic"`; run records and result documents state **SYNTHETIC — not market data**; no real market data is read, downloaded, or fetched; no provider account is touched.
7. **Scope of the experiment (in):** deterministic synthetic European option quotes with injected defects of known counts; quote validation with reason codes and exact conservation; parity-based forward inference; bounded Brent implied-volatility solver with explicit failure statuses; surface construction with `observed`/`interpolated`/`missing` statuses (no extrapolation); persistence forecast and a walk-forward factor-AR(1) forecaster; chronological evaluation with hand-checkable metrics and block-bootstrap intervals; two worlds (random-walk factors: persistence is appropriate; AR(1) factors: known predictable component); automated tests; run records.
8. **Out of scope:** real data, provider access, neural networks, frontend, API, storage layer, any product module, performance optimization, GPU/numeric libraries.

## Consequences
- **Positive:** no installs or approvals needed; fully inspectable numerics; the spike cannot silently depend on the machine's global packages.
- **Negative:** pure-Python speed limits experiment size; some functions (e.g., OLS, interpolation) are re-implemented at small scale — acceptable for a throwaway spike, and a reason **not** to treat this code as product code.
- **Neutral:** DEC-015 remains open; real-data pipelines will probably want vectorized numerics, which the spike's measured runtime will help justify (or not).

## Guardrail and compliance check
GR-ENG-02 (no unapproved dependencies): satisfied. GR-DATA-04 (no fabricated market data; synthetic labelled): satisfied by `origin` field and file/run-record labels. GR-ENG-06 (tests executed, not assumed): results recorded from actual runs. GR-LEAK-01: chronological evaluation is tested. Security: no network access, no secrets, no real data.

## Review trigger
The spike's measured runtime or numerical findings contradict this ADR; the owner selects the product toolchain (DEC-015); the spike code is proposed for adoption.

## Follow-up actions
- [x] Record this decision before writing code
- [x] Update [decision.md](../../../decision.md) DEC-015 with the spike-scope note
- [x] Record test and experiment results in [PHASE0_SYNTHETIC_RESULTS](../../research/PHASE0_SYNTHETIC_RESULTS.md) — measured runtime ≈ 0.8 s for a 300-day, ≈ 63k-quote run in pure Python on the development machine (one machine, one run), so the "pure-Python speed" risk in this ADR did not materialize at this size
- [ ] Revisit when DEC-015 is decided
