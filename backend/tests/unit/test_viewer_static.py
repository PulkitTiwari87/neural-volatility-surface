"""Phase 5 A4 (static): the viewer ships no credentials, loads nothing from other origins and executes no data as code.

Static checks of ``frontend/index.html`` only (the file is owned by the UI workstream and is not edited here). They do
not replace the manual UA-01..UA-14 journeys or an accessibility audit, which are NOT done.
"""
import re
import unittest
from pathlib import Path

from volatility_lab.api.server import FRONTEND, HEADERS

HTML = Path(FRONTEND).read_text(encoding="utf-8")
SVG_NS = "http://www.w3.org/2000/svg"


class ViewerStaticTests(unittest.TestCase):
    def test_no_external_origin_is_referenced_except_the_svg_namespace(self):
        urls = set(re.findall(r"https?://[^\s\"'`)<>]+", HTML))
        self.assertEqual(urls - {SVG_NS}, set())

    def test_no_external_script_style_image_or_import_is_loaded(self):
        self.assertEqual(re.findall(r"<script[^>]+src=", HTML, re.I), [])
        self.assertEqual(re.findall(r"<link[^>]+href=", HTML, re.I), [])
        self.assertEqual(re.findall(r"<img[^>]+src=", HTML, re.I), [])
        self.assertEqual(re.findall(r"@import|url\(\s*['\"]?https?:", HTML, re.I), [])

    def test_all_network_access_is_a_same_origin_fetch(self):
        self.assertEqual(re.findall(r"XMLHttpRequest|WebSocket|EventSource|sendBeacon|importScripts", HTML), [])
        calls = re.findall(r"fetch\(([^,)]+)", HTML)
        self.assertTrue(calls)
        self.assertTrue(all(not c.strip().startswith(("'http", '"http', "`http")) for c in calls), calls)

    def test_no_dynamic_code_execution_and_no_credential_storage(self):
        self.assertEqual(re.findall(r"\beval\(|new Function\(|document\.write\(|setTimeout\(\s*['\"`]", HTML), [])
        self.assertEqual(re.findall(r"localStorage|sessionStorage|document\.cookie|indexedDB", HTML), [])

    def test_no_secret_like_literals(self):
        pat = re.compile(r"(AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{30,}|"
                         r"(?i:(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][A-Za-z0-9/+_\-]{12,}['\"]))")
        self.assertEqual(pat.findall(HTML), [])

    def test_innerhtml_is_only_used_for_built_in_constants_not_for_api_data(self):
        uses = re.findall(r"\.innerHTML\s*=\s*([^;]+);", HTML)
        self.assertTrue(all("ICONS" in u for u in uses), uses)

    def test_server_csp_allows_no_foreign_origin(self):
        csp = HEADERS["Content-Security-Policy"]
        self.assertIn("default-src 'none'", csp)
        self.assertIn("connect-src 'self'", csp)
        self.assertNotRegex(csp, r"https?:|\*")


if __name__ == "__main__":
    unittest.main()
