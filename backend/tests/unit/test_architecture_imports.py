"""GR-ENG-03: dependencies point downstream only (architecture.md §4). AST scan, nothing is imported.

A package may import only packages ranked *before* it. Two existing edges break the documented order; they are
listed (with the reason) rather than hidden, and the test fails both on any NEW violation and if a listed one is
fixed without removing it from the list, so the list cannot rot.
"""
import ast
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "volatility_lab"

# architecture.md §4 order (config/domain importable by all); storage and api sit downstream of their producers
RANK = {"config": 0, "domain": 0, "ingestion": 1, "validation": 2, "pricing": 3, "surfaces": 4, "features": 5,
        "datasets": 6, "models": 7, "evaluation": 8, "experiments": 9, "storage": 10, "api": 11, "observability": 12}

KNOWN_VIOLATIONS = {
    ("models", "evaluation"): "models/baselines.py uses evaluation.metrics.eval_mask and evaluation.walkforward.Fold "
                              "(E-1 shortcut; fix = move Fold/eval_mask upstream, which changes the generated notebooks)",
    ("validation", "pricing"): "validation/quotes.py inverts IV with pricing.bs inside build_otm_quotes "
                               "(E-1 merges the validation and IV stages; fix = split the stage)",
}


def _edges():
    edges = {}
    for f in SRC.rglob("*.py"):
        parts = f.relative_to(SRC).parts
        if len(parts) < 2:
            continue
        pkg = parts[0]
        for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            mods = [n.module] if isinstance(n, ast.ImportFrom) and n.module else \
                   [a.name for a in n.names] if isinstance(n, ast.Import) else []
            for m in mods:
                p = m.split(".")
                if p[0] == "volatility_lab" and len(p) > 1 and p[1] != pkg:
                    edges.setdefault((pkg, p[1]), set()).add(str(f.relative_to(SRC)))
    return edges


class ImportDirectionTests(unittest.TestCase):
    def test_every_package_has_a_rank(self):
        pkgs = {p.name for p in SRC.iterdir() if (p / "__init__.py").is_file()}
        self.assertFalse(pkgs - set(RANK), f"rank the new package(s) in RANK: {pkgs - set(RANK)}")

    def test_no_new_upstream_violations(self):
        bad = {e: sorted(w) for e, w in _edges().items() if RANK[e[1]] >= RANK[e[0]] and e not in KNOWN_VIOLATIONS}
        self.assertEqual(bad, {}, "package imports a package that is not upstream of it (architecture.md §4)")

    def test_known_violations_still_exist(self):
        present = {e for e in _edges() if RANK[e[1]] >= RANK[e[0]]}
        self.assertEqual(present & set(KNOWN_VIOLATIONS), set(KNOWN_VIOLATIONS),
                         "a known violation was fixed: remove it from KNOWN_VIOLATIONS")

    def test_pricing_and_domain_have_no_internal_package_dependencies(self):
        edges = _edges()
        self.assertFalse([e for e in edges if e[0] in ("pricing", "domain", "config")], "pure modules import nothing")


if __name__ == "__main__":
    unittest.main()
