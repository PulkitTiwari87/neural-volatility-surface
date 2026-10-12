"""Forecasters and the chronological history guard. SYNTHETIC SPIKE.

A forecaster only ever sees a HistoryView(upto=t): reading any day > t raises
LookaheadError (GR-LEAK-01). Fitting uses days <= t only.
"""
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .surface import CellStatus, Surface

Grid = List[List[Optional[float]]]


class LookaheadError(Exception):
    """Raised when a forecaster tries to read a day after the forecast origin."""


class HistoryView:
    def __init__(self, surfaces: Sequence[Surface], upto: int):
        self._s = surfaces
        self.upto = upto

    def __len__(self) -> int:
        return self.upto + 1

    def __getitem__(self, i: int) -> Surface:
        if i < 0:
            i = self.upto + 1 + i
        if i < 0 or i > self.upto:
            raise LookaheadError("day %d is outside history 0..%d" % (i, self.upto))
        return self._s[i]


class PersistenceForecaster:
    name = "persistence"

    def predict(self, history: HistoryView) -> Optional[Grid]:
        s = history[-1]
        return [list(row) for row in s.iv]


def solve3(a: List[List[float]], b: List[float]) -> Optional[List[float]]:
    """Solve a 3x3 linear system by Gaussian elimination with partial pivoting."""
    n = 3
    m = [row[:] + [bi] for row, bi in zip(a, b)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-14:
            return None
        m[col], m[piv] = m[piv], m[col]
        for r in range(col + 1, n):
            f = m[r][col] / m[col][col]
            for c in range(col, n + 1):
                m[r][c] -= f * m[col][c]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        x[r] = (m[r][n] - sum(m[r][c] * x[c] for c in range(r + 1, n))) / m[r][r]
    return x


def extract_factors(surface: Surface, k_nodes: Sequence[float], maturities: Sequence[float],
                    term: Callable[[float], float]) -> Optional[Tuple[float, float, float]]:
    """Least-squares (L, S, C) from OBSERVED cells only: iv - g(T) = L + S k + C k^2."""
    pts = []
    for mi, T in enumerate(maturities):
        for ki, k in enumerate(k_nodes):
            if surface.status[mi][ki] is CellStatus.OBSERVED:
                pts.append((k, surface.iv[mi][ki] - term(T)))
    if len({round(k, 9) for k, _ in pts}) < 3:
        return None
    a = [[0.0] * 3 for _ in range(3)]
    b = [0.0] * 3
    for k, y in pts:
        phi = (1.0, k, k * k)
        for i in range(3):
            b[i] += phi[i] * y
            for j in range(3):
                a[i][j] += phi[i] * phi[j]
    sol = solve3(a, b)
    return None if sol is None else (sol[0], sol[1], sol[2])


def _grid_from_factors(x, k_nodes, maturities, term) -> Grid:
    return [[x[0] + x[1] * k + x[2] * k * k + term(T) for k in k_nodes] for T in maturities]


class _FactorBase:
    def __init__(self, k_nodes, maturities, term):
        self.k_nodes, self.maturities, self.term = tuple(k_nodes), tuple(maturities), term
        self._cache: Dict[int, Tuple[Surface, Optional[Tuple[float, float, float]]]] = {}

    def _factors(self, history: HistoryView, day: int):
        s = history[day]  # guarded read
        hit = self._cache.get(day)
        if hit is not None and hit[0] is s:
            return hit[1]
        x = extract_factors(s, self.k_nodes, self.maturities, self.term)
        self._cache[day] = (s, x)
        return x


class FactorAR1Forecaster(_FactorBase):
    """Honest walk-forward: AR(1) per factor fitted by OLS on days <= origin only."""

    name = "factor_ar1"

    def __init__(self, k_nodes, maturities, term, min_pairs: int = 30):
        super().__init__(k_nodes, maturities, term)
        self.min_pairs = min_pairs

    def predict(self, history: HistoryView) -> Optional[Grid]:
        t = history.upto
        xs = [self._factors(history, d) for d in range(t + 1)]
        if xs[t] is None:
            return None
        pred = []
        for f in range(3):
            pairs = [(xs[d][f], xs[d + 1][f]) for d in range(t) if xs[d] is not None and xs[d + 1] is not None]
            if len(pairs) < self.min_pairs:
                return None
            n = len(pairs)
            mx = sum(p[0] for p in pairs) / n
            my = sum(p[1] for p in pairs) / n
            var = sum((p[0] - mx) ** 2 for p in pairs)
            if var <= 0.0:
                return None
            cov = sum((p[0] - mx) * (p[1] - my) for p in pairs)
            phi_hat = cov / var
            a = my - phi_hat * mx
            pred.append(a + phi_hat * xs[t][f])
        return _grid_from_factors(pred, self.k_nodes, self.maturities, self.term)


class OracleARForecaster(_FactorBase):
    """Diagnostic UPPER BOUND using the TRUE generating mu and phi (synthetic only; impossible on real data).

    With phi = 1 it equals persistence on observed cells."""

    name = "oracle_ar"

    def __init__(self, k_nodes, maturities, term, mu, phi: float):
        super().__init__(k_nodes, maturities, term)
        self.mu, self.phi = tuple(mu), phi

    def predict(self, history: HistoryView) -> Optional[Grid]:
        x = self._factors(history, history.upto)
        if x is None:
            return None
        pred = [m + self.phi * (xi - m) for m, xi in zip(self.mu, x)]
        return _grid_from_factors(pred, self.k_nodes, self.maturities, self.term)
