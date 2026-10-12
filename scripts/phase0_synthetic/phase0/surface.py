"""Surface construction with honest cell statuses. SYNTHETIC SPIKE.

observed     : an eligible IV observation lies within tol_k of the node. The cell value is that
               observation's IV, so its bias is bounded by |dIV/dk| * tol_k. CONSISTENCY RULE:
               a recovery tolerance must be >= max|dIV/dk| * tol_k. (Audit v2, POST HOC: the default
               tol_k was tightened from 1e-6 to 1e-9 so status and value agree; --tol-k 1e-6 reproduces v1.)
interpolated : node is inside the observed hull of that maturity slice and the
               bracketing gap <= max_gap; linear interpolation in k.
missing      : otherwise. Extrapolation is DISABLED (EXTRAPOLATED is never produced).
"""
import bisect
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Sequence, Tuple


class CellStatus(str, Enum):
    OBSERVED = "observed"
    INTERPOLATED = "interpolated"
    EXTRAPOLATED = "extrapolated"  # reserved; never produced in this spike
    MISSING = "missing"


@dataclass(frozen=True)
class SurfaceConfig:
    k_nodes: Tuple[float, ...] = tuple(round(-0.20 + 0.05 * i, 12) for i in range(9))
    tol_k: float = 1e-9  # v1 default was 1e-6 (see module docstring)
    max_gap: float = 0.15


@dataclass
class Surface:
    day: int
    iv: List[List[Optional[float]]]  # [maturity][k_node]
    status: List[List[CellStatus]]
    n_obs: List[int]
    max_snap_dk: float = 0.0  # max |k_obs - node| over OBSERVED cells (bias bound = slope * this)
    n_snapped: int = 0  # OBSERVED cells whose observation is not exactly at the node (> 1e-13)

    def n_status(self, s: CellStatus) -> int:
        return sum(1 for row in self.status for c in row if c is s)


def build_surface(day: int, obs_by_mat: Sequence[Sequence[Tuple[float, float]]], cfg: SurfaceConfig) -> Surface:
    iv_grid, st_grid, n_obs = [], [], []
    max_snap, n_snapped = 0.0, 0
    for obs in obs_by_mat:
        pts = sorted(obs)
        dedup: List[Tuple[float, float]] = []
        for k, v in pts:
            if dedup and abs(k - dedup[-1][0]) < 1e-12:
                continue
            dedup.append((k, v))
        ks = [p[0] for p in dedup]
        n_obs.append(len(dedup))
        iv_row: List[Optional[float]] = []
        st_row: List[CellStatus] = []
        for node in cfg.k_nodes:
            i = bisect.bisect_left(ks, node)
            cand = []
            if i < len(ks):
                cand.append(i)
            if i > 0:
                cand.append(i - 1)
            best = min(cand, key=lambda j: abs(ks[j] - node)) if cand else None
            if best is not None and abs(ks[best] - node) <= cfg.tol_k:
                dk = abs(ks[best] - node)
                max_snap = max(max_snap, dk)
                n_snapped += 1 if dk > 1e-13 else 0
                iv_row.append(dedup[best][1])
                st_row.append(CellStatus.OBSERVED)
                continue
            if 0 < i < len(ks):
                kl, vl = dedup[i - 1]
                kr, vr = dedup[i]
                if kr - kl <= cfg.max_gap:
                    iv_row.append(vl + (node - kl) / (kr - kl) * (vr - vl))
                    st_row.append(CellStatus.INTERPOLATED)
                    continue
            iv_row.append(None)
            st_row.append(CellStatus.MISSING)
        iv_grid.append(iv_row)
        st_grid.append(st_row)
    return Surface(day, iv_grid, st_grid, n_obs, max_snap, n_snapped)
