"""Window-access log (GR-LEAK-04 / GR-LEAK-05, GR-MOD-05).

Records how many rows of each walk-forward window (train / val / test) are touched, and for what purpose, so a run
record can state ``test_accessed_count``: the number of test-window accesses made for *fitting or selection*
(purpose ``fit`` / ``select``). Test rows used only to ``predict`` / ``evaluate`` do not count. The log is an audit
trail, not a security boundary: callers record honestly, ``guard`` makes a violation raise.
"""
from __future__ import annotations

from typing import List

KINDS = ("train", "val", "test")
SELECTION_PURPOSES = frozenset({"fit", "select"})


class TestWindowAccessError(RuntimeError):
    """Selection code (purpose fit/select) tried to read the test window without explicit authorization."""

    __test__ = False  # not a pytest/unittest test class despite the name


class AccessLog:
    def __init__(self, authorized: bool = False):
        self.authorized = bool(authorized)
        self.events: List[dict] = []

    def guard(self, kind: str, purpose: str) -> None:
        """Raise when selection code touches the test window, unless the log was created ``authorized=True``."""
        if kind == "test" and purpose in SELECTION_PURPOSES and not self.authorized:
            raise TestWindowAccessError(f"test window accessed for '{purpose}' without authorization (GR-LEAK-04)")

    def record(self, purpose: str, kind: str, n: int) -> None:
        if kind not in KINDS:
            raise ValueError(f"unknown window kind: {kind!r}")
        self.guard(kind, purpose)
        self.events.append({"purpose": purpose, "kind": kind, "n": int(n),
                            "authorized": bool(self.authorized and kind == "test" and purpose in SELECTION_PURPOSES)})

    @property
    def test_accessed_for_selection(self) -> int:
        return sum(1 for e in self.events if e["kind"] == "test" and e["purpose"] in SELECTION_PURPOSES)

    def to_dict(self) -> dict:
        return {"test_accessed_count": self.test_accessed_for_selection, "events": [dict(e) for e in self.events]}
