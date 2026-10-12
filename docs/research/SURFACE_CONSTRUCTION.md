# Surface Construction

**Status:** PROPOSED (conventions and grid pending DEC-005/DEC-006) · **Canonical for:** coordinates, grid, interpolation policy, masks, diagnostics · **Source:** MP §3, §10, §16 · **Related:** [IV_METHODOLOGY](IV_METHODOLOGY.md), [DATA_FLOW](../architecture/DATA_FLOW.md) stage 6, guardrails GR-DATA-05, GR-QNT-07

## 1. Purpose
Turn irregular, noisy IV observations on one snapshot into a standardized surface comparable across dates, without inventing market information.

## 2. Coordinates (conventions OPEN → versioned)
- **Moneyness:** proposed forward log-moneyness *k = ln(K/F)* (DEC-005). Alternatives: ln(K/S), K/S, delta. The chosen definition is stored with every snapshot (`convention.version`).
- **Maturity:** *T* in years by a documented day-count and calendar (DEC-005).
- Mapping back to strikes must be possible (invertibility) for lineage and display.
- Changing a convention creates a new surface version; old versions remain (DATA-004).

## 3. Grid
Fixed standardized grid in (*k*, *T*) so surfaces are comparable across dates. Resolution, range and spacing: `NEEDS RESEARCH` (DEC-006); chosen from observed density statistics, recorded as a versioned **grid ID**. Grid range must not extend far beyond typically observed coverage; otherwise most cells would be extrapolated.

## 4. Construction steps (MP §10)
1. Group eligible IV observations by snapshot.
2. Convert strikes/expirations to standardized coordinates.
3. Remove or flag unreliable observations (policy-driven; sensitivity-tested).
4. Aggregate multiple observations at the same coordinate (e.g., call and put at one strike) by a documented rule — OTM-preferred, averaging, or spread-weighted (`OPEN`; evaluate).
5. Assign each grid cell a status:
   - `observed` — derived directly from eligible observation(s) at (or within a stated tolerance of) the node;
   - `interpolated` — inside the observed hull, computed by the named method;
   - `extrapolated` — outside the hull, computed only if the policy allows; default **not computed** (`missing`);
   - `missing` — otherwise.
6. Save both the original IV observations and the standardized grid; each non-missing cell links to its source observations or interpolation parameters.
7. Compute quality summaries and diagnostics (§6).

## 5. Interpolation candidates (MP §10; no choice made)
| Method | Role | Notes |
|---|---|---|
| Nearest-neighbour / linear | Transparent baseline | Piecewise structure; easy to audit |
| Shape-preserving (monotone) | Avoids overshoot | Needs care across two dimensions |
| Smoothing spline | Noise reduction | Smoothness hyperparameter; can invent curvature |
| Parametric smile/surface fit | Comparison; low-dimensional | Fit error and parameter instability; arbitrage-aware forms deferred (Phase 7) |

**Policy:** interpolation only inside the observed hull; interpolation distance limits (`TBD(Phase 2)`) beyond which cells stay `missing`; no silent extrapolation; interpolation is *not* new market data.

**Selection experiment (DEC-006):** hold out a random subset of *observed* points within a snapshot, reconstruct them from the rest, and compare error by method, region and density; also compare downstream persistence-baseline metrics under each method (RQ-09). Report with sample counts.

## 6. Diagnostics (reported in snapshot metadata)
Coverage fractions by status; per-maturity strike count; largest gaps; roughness/jump measures between adjacent cells and consecutive dates; calendar-spread and butterfly-style sanity checks as **diagnostics only** (SCI-011); fit residuals for parametric methods. Implausible-jump thresholds `TBD(Phase 2)`.

## 7. Versioning and reproducibility
Snapshot ID depends on: IV-observation set ID, grid ID, convention version, aggregation rule version, interpolation method + parameters + version, code version. Identical inputs ⇒ identical hash (Phase 2 acceptance A3).

## 8. Tests (see GR-DATA-05, GR-QNT-07; MP §21)
Coordinate round-trip (strike ↔ *k*); mask preservation through storage; sparse and irregular chains; hull boundary behaviour (inside/outside/on boundary); interpolation reproduces observed nodes exactly when node-aligned; no-silent-extrapolation test; construction determinism; synthetic surface with known analytic form reconstructed within stated error.

## 9. Limitations
Observed hull varies by day (cell status changes over time, complicating time-series features — handled via masks/missingness indicators); aggregation across call/put and quote times introduces noise; grid resolution trades fidelity vs sparsity.
