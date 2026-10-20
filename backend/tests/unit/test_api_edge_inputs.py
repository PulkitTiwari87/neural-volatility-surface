"""API edge inputs (AP-004 Patch 3, findings C-05 and C-11). SYNTHETIC temp run directory, real loopback socket.

* HEAD and OPTIONS follow the contract (API_CONTRACTS section 8: every method but GET -> 405, ``Allow: GET``);
* Host-header guard for a local-only tool: only a loopback name may address the server (DNS-rebinding defence);
* a table cell that is not a finite number (nan, inf, overflow) becomes JSON ``null``; the table still answers 200
  with strictly valid JSON (no NaN / Infinity tokens) instead of the generic 500.
"""
import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path

import numpy as np

from volatility_lab.api.server import create_server
from volatility_lab.api.service import _num

CSV = """name,value
nan_lower,nan
nan_upper,NaN
pos_inf,inf
neg_inf,-inf
word_inf,Infinity
overflow,1e999
neg_overflow,-1e999
finite,7
text,hello
empty,
"""


def _reject_constant(token):
    raise ValueError(f"non-strict JSON constant in the response: {token}")


def _strict(body: bytes):
    return json.loads(body, parse_constant=_reject_constant)


class NumTests(unittest.TestCase):
    def test_non_finite_and_overflow_become_none_everything_else_unchanged(self):
        for s in ("nan", "NaN", "inf", "-inf", "Infinity", "-Infinity", "1e999", "-1e999"):
            self.assertIsNone(_num(s), s)
        self.assertEqual(_num("7"), 7.0)
        self.assertEqual(_num("-0.25"), -0.25)
        self.assertEqual(_num("1e-3"), 0.001)
        self.assertEqual(_num(""), "")
        self.assertEqual(_num("hello"), "hello")


class EdgeInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.td = tempfile.TemporaryDirectory()
        cls.root = Path(cls.td.name) / "runs"
        run = cls.root / "r1"
        (run / "tables").mkdir(parents=True)
        np.savez(run / "panel.npz", x=np.zeros(1))            # the table route only needs the run to exist
        (run / "tables" / "nonfinite.csv").write_text(CSV)
        cls.srv = create_server(cls.root, port=0)
        cls.port = cls.srv.server_address[1]
        cls.thread = threading.Thread(target=cls.srv.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()
        cls.td.cleanup()

    def request(self, method, path, host="default"):
        """-> (status, Allow header, body). ``host``: "default" = the port's own name, None = send no Host header."""
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            conn.putrequest(method, path, skip_host=True, skip_accept_encoding=True)
            if host == "default":
                host = f"127.0.0.1:{self.port}"
            if host is not None:
                conn.putheader("Host", host)
            conn.endheaders()
            r = conn.getresponse()
            return r.status, r.getheader("Allow"), r.read()
        finally:
            conn.close()

    # ---- C-05 -------------------------------------------------------------------------------------------------
    def test_table_with_non_finite_cells_answers_200_with_null_and_strict_json(self):
        status, _, body = self.request("GET", "/api/runs/r1/tables/nonfinite")
        self.assertEqual(status, 200, body[:200])
        doc = _strict(body)
        self.assertEqual(doc["columns"], ["name", "value"])
        self.assertFalse(doc["truncated"])
        self.assertEqual(doc["rows"], [
            ["nan_lower", None], ["nan_upper", None], ["pos_inf", None], ["neg_inf", None], ["word_inf", None],
            ["overflow", None], ["neg_overflow", None], ["finite", 7.0], ["text", "hello"], ["empty", ""]])
        for token in (b"NaN", b"Infinity"):
            self.assertNotIn(token, body)

    # ---- C-11: methods ----------------------------------------------------------------------------------------
    def test_head_and_options_follow_the_405_contract(self):
        for method in ("HEAD", "OPTIONS", "POST", "PUT", "DELETE", "PATCH"):
            status, allow, _ = self.request(method, "/api/runs")
            self.assertEqual(status, 405, method)
            self.assertEqual(allow, "GET", method)

    # ---- C-11: Host header ------------------------------------------------------------------------------------
    def test_loopback_host_names_are_served(self):
        p = self.port
        for host in (None, f"127.0.0.1:{p}", f"localhost:{p}", f"[::1]:{p}", "localhost", "127.0.0.1", "[::1]",
                     f"LocalHost:{p}"):
            status, _, body = self.request("GET", "/api/runs", host=host)
            self.assertEqual(status, 200, host)
            self.assertEqual([r["id"] for r in _strict(body)], ["r1"], host)

    def test_foreign_host_names_are_refused_with_400_json(self):
        p = self.port
        for host in ("evil.example", f"evil.example:{p}", "127.0.0.1.evil.example", f"127.0.0.1.evil.example:{p}",
                     "localhost.evil.example", "0.0.0.0", "evil@127.0.0.1", "[::1]evil", "127.0.0.1:80:80"):
            for path in ("/api/runs", "/"):
                status, _, body = self.request("GET", path, host=host)
                self.assertEqual(status, 400, (host, path))
                self.assertEqual(_strict(body), {"error": "unexpected Host header"}, host)

    def test_unknown_path_and_valid_routes_are_unaffected(self):
        self.assertEqual(self.request("GET", "/api/nope")[0], 404)
        self.assertEqual(self.request("GET", "/api/runs/r1")[0], 400)   # panel.npz lacks the required arrays: unchanged


if __name__ == "__main__":
    unittest.main()
