"""Neural resume-cache identity (AP-004 Patch 4, finding C-01). SYNTHETIC data; NO model is trained.

``run_neural`` resumes from files already in ``out_dir``. Saved predictions may only be reused when a ``run_key.json``
written at the start of that run matches this run exactly; an absent, malformed or different key fails closed.
``neural.train_and_predict`` is replaced by a stub that writes a placeholder checkpoint and returns constant
predictions, and CUDA is stubbed (as in ``test_gpu_guard``), so nothing here touches PyTorch or a GPU.
"""
import dataclasses
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import numpy as np

from volatility_lab.evaluation.walkforward import make_folds
from volatility_lab.experiments import runner
from volatility_lab.features.panel import prepare
from volatility_lab.models import neural
from ._fixtures import CFG, pipeline


def _cuda_stub():
    props = SimpleNamespace(name="Stub GPU", total_memory=16 * 2 ** 30, major=7, minor=5)
    return SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: True, get_device_properties=lambda i: props),
                           __version__="stub", version=SimpleNamespace(cuda="12.x"),
                           backends=SimpleNamespace(cudnn=SimpleNamespace(version=lambda: 9000)))


class _FakeTrainer:
    def __init__(self):
        self.calls = 0

    def __call__(self, kind, data, cfg_train, seed, torch_module=None, ckpt_path=None, log=print):
        self.calls += 1
        Path(ckpt_path).write_bytes(b"placeholder checkpoint")
        n, c = data["Xte"].shape[0], data["Dtr"].shape[1]
        return {"pred_delta": np.full((n, c), 0.001 * (seed + 1)), "epochs_run": 1, "best_epoch": 1, "seconds": 0.0,
                "peak_gpu_mem_mb": 0}


def _tree_hashes(d: Path) -> dict:
    return {str(f.relative_to(d)): hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(d.rglob("*")) if f.is_file()}


class RunKeyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.panel = pipeline()["panel"]
        cls.p = prepare(cls.panel, CFG.features)
        cls.folds = make_folds(cls.p, CFG.split)
        cls.base = runner.run_key(cls.p, cls.folds, CFG)

    def test_key_is_deterministic_and_serialises_identically(self):
        again = runner.run_key(self.p, make_folds(self.p, CFG.split), CFG)
        self.assertEqual(self.base, again)
        self.assertEqual(runner._canonical(self.base), runner._canonical(again))
        self.assertEqual(self.base["schema"], runner.RUN_KEY_SCHEMA)

    def test_every_compatibility_field_changes_the_key(self):
        p = self.p
        iv = p.iv.copy()
        iv[tuple(np.argwhere(np.isfinite(iv))[0])] += 1e-3        # one finite surface value differs
        cfg_seed = dataclasses.replace(CFG, train=dataclasses.replace(CFG.train, seeds=CFG.train.seeds + (99,)))
        cfg_lr = dataclasses.replace(CFG, train=dataclasses.replace(CFG.train, lr=CFG.train.lr * 2))
        fixed = prepare(self.panel, CFG.features, "fixed_expiry")
        variants = {
            "target label": runner.run_key(fixed, make_folds(fixed, CFG.split), CFG),
            "calendar block": runner.run_key(prepare(self.panel, CFG.features, calendar=True), self.folds, CFG),
            "mr_window": runner.run_key(prepare(self.panel, CFG.features, mr_window=5), self.folds, CFG),
            "pca_factors": runner.run_key(p, self.folds, CFG, pca_factors=3),
            "seeds": runner.run_key(p, self.folds, cfg_seed),
            "learning rate": runner.run_key(p, self.folds, cfg_lr),
            "validation mode": runner.run_key(p, make_folds(p, CFG.split, "tail_frac", 0.2), CFG),
            "panel values": runner.run_key(dataclasses.replace(p, iv=iv), self.folds, CFG),
            "horizon": runner.run_key(dataclasses.replace(p, horizon=p.horizon + 1), self.folds, CFG),
        }
        for name, key in variants.items():
            with self.subTest(name):
                self.assertNotEqual(runner._canonical(key), runner._canonical(self.base))

    def test_pca_runs_are_bound_to_the_numpy_and_platform_identity(self):
        self.assertNotIn("pca_env", self.base)
        key = runner.run_key(self.p, self.folds, CFG, pca_factors=3)
        self.assertEqual(set(key["pca_env"]), {"numpy", "python", "machine", "system"})
        self.assertEqual(key["pca_env"]["numpy"], np.__version__)

    def test_unknown_field_types_fail_closed_instead_of_being_stringified(self):
        @dataclasses.dataclass
        class Odd:
            x: list
        with self.assertRaises(TypeError):
            runner._fingerprint(Odd([1, 2]))


class ClaimOutDirTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p = pipeline()["prepared"]
        cls.base = runner.run_key(p, make_folds(p, CFG.split), CFG)
        cls.other = dict(cls.base, config_sha256="0" * 64)

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.out = Path(self.td.name) / "run"
        (self.out / "predictions").mkdir(parents=True)

    def tearDown(self):
        self.td.cleanup()

    def test_fresh_dir_is_claimed_then_resumed_with_the_same_key(self):
        self.assertEqual(runner.claim_out_dir(self.out, self.base), "new")
        text = (self.out / runner.RUN_KEY_FILE).read_text()
        self.assertEqual(text, runner._canonical(self.base))
        self.assertEqual(runner.claim_out_dir(self.out, self.base), "resume")
        self.assertEqual((self.out / runner.RUN_KEY_FILE).read_text(), text)

    def test_different_key_is_refused_and_nothing_is_modified(self):
        runner.claim_out_dir(self.out, self.base)
        (self.out / "predictions" / "fold2020_mlp_seed0.npy").write_bytes(b"stale")
        before = _tree_hashes(self.out)
        with self.assertRaises(runner.RunKeyError):
            runner.claim_out_dir(self.out, self.other)
        self.assertEqual(_tree_hashes(self.out), before)

    def test_saved_files_without_a_key_are_refused_for_each_kind(self):
        for sub, name in (("predictions", "x.npy"), ("checkpoints", "x.pt"), ("histories", "x.json")):
            with self.subTest(sub):
                d = Path(self.td.name) / f"legacy_{sub}"
                (d / sub).mkdir(parents=True)
                (d / sub / name).write_bytes(b"old")
                with self.assertRaises(runner.RunKeyError):
                    runner.claim_out_dir(d, self.base)
                self.assertFalse((d / runner.RUN_KEY_FILE).exists(), "a refused claim writes no key")

    def test_malformed_keys_are_refused(self):
        for text in ("", "not json", "[]", "null", "{}", '{"schema": NaN}', json.dumps(dict(self.base, schema="run-key-0"))):
            with self.subTest(text[:20]):
                (self.out / runner.RUN_KEY_FILE).write_text(text)
                with self.assertRaises(runner.RunKeyError):
                    runner.claim_out_dir(self.out, self.base)
                self.assertEqual((self.out / runner.RUN_KEY_FILE).read_text(), text, "a bad key is left for inspection")


class RunNeuralResumeTests(unittest.TestCase):
    """End to end through ``run_neural`` with training stubbed out."""

    @classmethod
    def setUpClass(cls):
        cls.p = pipeline()["prepared"]
        cls.folds = make_folds(cls.p, CFG.split)
        cls.members = len(cls.folds) * len(CFG.train.models) * len(CFG.train.seeds)

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.out = Path(self.td.name) / "run"
        self.trainer = _FakeTrainer()

    def tearDown(self):
        self.td.cleanup()

    def run_it(self, cfg=CFG, p=None, **kw):
        with mock.patch.object(neural, "train_and_predict", self.trainer):
            return runner.run_neural(p or self.p, self.folds, cfg, self.out, torch_module=_cuda_stub(),
                                     log=lambda *_: None, **kw)

    def test_fresh_run_trains_every_member_and_writes_the_key(self):
        self.run_it()
        self.assertEqual(self.trainer.calls, self.members)
        self.assertTrue((self.out / runner.RUN_KEY_FILE).is_file())

    def test_identical_rerun_resumes_without_training_and_gives_the_same_forecasts(self):
        first, _ = self.run_it()
        self.trainer.calls = 0
        second, _ = self.run_it()
        self.assertEqual(self.trainer.calls, 0)
        for year in first:
            for name in first[year]:
                np.testing.assert_array_equal(first[year][name], second[year][name])

    def test_changed_hyperparameter_cannot_reuse_stale_predictions(self):
        self.run_it()
        before = _tree_hashes(self.out)
        self.trainer.calls = 0
        cfg2 = dataclasses.replace(CFG, train=dataclasses.replace(CFG.train, lr=CFG.train.lr * 2))
        with self.assertRaises(RuntimeError):                    # RunKeyError is a RuntimeError
            self.run_it(cfg2)
        self.assertEqual(self.trainer.calls, 0)
        self.assertEqual(_tree_hashes(self.out), before)

    def test_different_experiment_label_cannot_reuse_stale_predictions(self):
        self.run_it()
        self.trainer.calls = 0
        with self.assertRaises(RuntimeError):
            self.run_it(p=prepare(pipeline()["panel"], CFG.features, "fixed_expiry"))
        self.assertEqual(self.trainer.calls, 0)

    def test_pca_factor_run_cannot_reuse_a_cell_space_run(self):
        self.run_it()
        self.trainer.calls = 0
        with self.assertRaises(RuntimeError):
            self.run_it(pca_factors=3)
        self.assertEqual(self.trainer.calls, 0)

    def test_run_without_a_key_is_refused_even_though_predictions_exist(self):
        self.run_it()
        (self.out / runner.RUN_KEY_FILE).unlink()
        self.trainer.calls = 0
        with self.assertRaises(RuntimeError):
            self.run_it()
        self.assertEqual(self.trainer.calls, 0)

    def test_malformed_key_is_refused(self):
        self.run_it()
        (self.out / runner.RUN_KEY_FILE).write_text("{ truncated")
        self.trainer.calls = 0
        with self.assertRaises(RuntimeError):
            self.run_it()
        self.assertEqual(self.trainer.calls, 0)


if __name__ == "__main__":
    unittest.main()
