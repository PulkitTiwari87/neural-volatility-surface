"""Governance guards: properties the project promised in prose, now checked by code. SYNTHETIC / static checks only.

* GR-MOD-01 - a neural run is refused unless persistence and a regression baseline exist for every fold.
* No data-acquisition path exists in the package (project rule: nothing downloads data automatically; real data is
  user-provided or an explicitly user-triggered notebook step outside this package).
* The machine-readable model status can never say ``complete`` without an owner confirmation.
"""
import ast
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from volatility_lab.evaluation.walkforward import make_folds
from volatility_lab.experiments import runner
from ._fixtures import CFG, pipeline

SRC = Path(__file__).resolve().parents[2] / "src" / "volatility_lab"
STATUS_JSON = Path(__file__).resolve().parents[3] / "docs" / "engineering" / "MODEL_STATUS.json"

# Importing any of these inside the package would open a network or remote-storage path.
FORBIDDEN_MODULES = {"requests", "urllib3", "httpx", "aiohttp", "kaggle", "kagglehub", "gdown", "boto3", "botocore",
                     "ftplib", "smtplib", "paramiko", "socket", "ssl", "huggingface_hub", "google", "urllib.request",
                     "http.client", "xmlrpc", "telnetlib", "websocket", "websockets"}
FORBIDDEN_TEXT = ("from_pretrained", "torch.hub", "urlretrieve", "urlopen", "kaggle datasets download",
                  "drive.mount", "load_state_dict_from_url")


def _imports(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                yield a.name
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            yield node.module
            for a in node.names:                       # ``from urllib import request``
                yield f"{node.module}.{a.name}"


class BaselineGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = pipeline()["prepared"]
        cls.folds = make_folds(cls.p, CFG.split)

    def _preds(self, *names):
        return {f.test_year: {n: np.zeros(1) for n in names} for f in self.folds}

    def test_complete_baselines_pass(self):
        runner.require_baselines(self._preds("persistence", "ridge"), self.folds)
        runner.require_baselines(self._preds("persistence", "pca_ridge", "rolling_mean"), self.folds)

    def test_missing_persistence_or_regression_is_refused_per_fold(self):
        with self.assertRaisesRegex(runner.BaselineGateError, "no persistence"):
            runner.require_baselines(self._preds("ridge"), self.folds)
        with self.assertRaisesRegex(runner.BaselineGateError, "no regression baseline"):
            runner.require_baselines(self._preds("persistence", "rolling_mean"), self.folds)
        with self.assertRaises(runner.BaselineGateError):
            runner.require_baselines({}, self.folds)

    def test_run_neural_refuses_before_touching_a_gpu_or_writing_files(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "run"
            with self.assertRaises(runner.BaselineGateError):
                runner.run_neural(self.p, self.folds, CFG, out, baseline_preds=self._preds("persistence"),
                                  log=lambda *_: None)
            self.assertFalse(out.exists())


class NoAcquisitionPathTests(unittest.TestCase):
    def test_package_imports_no_network_or_remote_storage_client(self):
        offenders = []
        for py in sorted(SRC.rglob("*.py")):
            for mod in _imports(ast.parse(py.read_text(encoding="utf-8"))):
                if any(mod == bad or mod.startswith(bad + ".") for bad in FORBIDDEN_MODULES):
                    offenders.append(f"{py.relative_to(SRC)}: {mod}")
        self.assertEqual(offenders, [])

    def test_package_contains_no_download_call_patterns(self):
        offenders = []
        for py in sorted(SRC.rglob("*.py")):
            text = py.read_text(encoding="utf-8")
            offenders += [f"{py.relative_to(SRC)}: {t}" for t in FORBIDDEN_TEXT if t in text]
        self.assertEqual(offenders, [])

    def test_the_only_listening_socket_code_is_the_loopback_read_only_api(self):
        users = [p.relative_to(SRC).as_posix() for p in SRC.rglob("*.py")
                 if any(m.startswith(("http.server", "socketserver"))
                        for m in _imports(ast.parse(p.read_text(encoding="utf-8"))))]
        self.assertEqual(users, ["api/server.py"])

    def test_scanner_would_catch_a_forbidden_import(self):
        self.assertIn("urllib.request", list(_imports(ast.parse("import urllib.request"))))
        self.assertIn("urllib.request", list(_imports(ast.parse("from urllib import request"))))
        self.assertIn("requests", list(_imports(ast.parse("import requests as r"))))


class ModelStatusGovernanceTests(unittest.TestCase):
    def test_status_is_never_complete_without_an_owner_confirmation(self):
        status = json.loads(STATUS_JSON.read_text(encoding="utf-8"))
        if status["status"] == "complete":
            self.assertTrue(status.get("confirmed_by"), "MODEL_STATUS.json says complete without confirmed_by")
        self.assertIn(status["status"], {"in_progress", "blocked", "complete"})
        self.assertNotIn("validated", status["results_status"].lower().replace("not validated", ""))


if __name__ == "__main__":
    unittest.main()
