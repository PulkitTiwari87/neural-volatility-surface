import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from volatility_lab.models import neural
from volatility_lab.experiments import runner
from volatility_lab.evaluation.walkforward import make_folds
from ._fixtures import CFG, pipeline


def _stub(cuda: bool):
    props = SimpleNamespace(name="Stub GPU", total_memory=16 * 2 ** 30, major=7, minor=5)
    return SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: cuda, get_device_properties=lambda i: props),
                           __version__="stub", version=SimpleNamespace(cuda="12.x"),
                           backends=SimpleNamespace(cudnn=SimpleNamespace(version=lambda: 9000)))


class GpuGuardTests(unittest.TestCase):
    def test_no_cuda_raises_with_actionable_instructions_and_no_cpu_fallback(self):
        with self.assertRaises(neural.GpuUnavailableError) as cm:
            neural.require_cuda(_stub(False))
        msg = str(cm.exception)
        self.assertIn("Runtime", msg)
        self.assertIn("GPU", msg)
        self.assertIn("no CPU fallback", msg)

    def test_cuda_metadata_is_reported(self):
        info = neural.require_cuda(_stub(True))
        self.assertEqual(info["name"], "Stub GPU")
        self.assertEqual(info["device"], "cuda:0")
        self.assertEqual(info["total_memory_gb"], 16.0)

    def test_neural_run_refuses_before_creating_files_when_no_gpu(self):
        import tempfile
        p = pipeline()["prepared"]
        folds = make_folds(p, CFG.split)
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(neural.GpuUnavailableError):
                runner.run_neural(p, folds, CFG, Path(td) / "run", torch_module=_stub(False), log=lambda *_: None)
            self.assertFalse((Path(td) / "run").exists())

    def test_training_code_contains_no_cpu_device_path(self):
        src = Path(neural.__file__).read_text()
        for banned in ('device("cpu")', "device('cpu')", 'map_location="cpu"', "torch.set_default_device"):
            self.assertNotIn(banned, src)
        self.assertIn('torch.device("cuda:0")', src)


HAS_CUDA = False
try:  # torch may be absent or installed-but-broken (OSError on DLL load) on a CPU-only dev machine
    if importlib.util.find_spec("torch") is not None:
        import torch
        HAS_CUDA = torch.cuda.is_available()
except (ImportError, OSError):
    HAS_CUDA = False


@unittest.skipUnless(HAS_CUDA, "requires a real CUDA GPU (run in Colab); never runs on CPU")
class GpuTrainingTests(unittest.TestCase):
    def test_both_architectures_train_predict_and_checkpoint_on_gpu(self):
        import tempfile
        from volatility_lab.config.settings import TrainConfig
        rng = np.random.default_rng(0)
        n, C, D, L = 300, 12, 40, 6
        cfg = TrainConfig(max_epochs=8, patience=3, batch_size=64)
        for kind, shape in (("mlp", (n, D)), ("gru", (n, L, D))):
            X = rng.normal(size=shape)
            Y = rng.normal(size=(n, C)) * 0.01
            M = rng.random((n, C)) < 0.8
            data = {"Xtr": X[:200], "Dtr": Y[:200], "Mtr": M[:200], "Xva": X[200:250], "Dva": Y[200:250],
                    "Mva": M[200:250], "Xte": X[250:]}
            with tempfile.TemporaryDirectory() as td:
                out = neural.train_and_predict(kind, data, cfg, seed=1, ckpt_path=str(Path(td) / "m.pt"))
                self.assertEqual(out["pred_delta"].shape, (50, C))
                self.assertTrue(np.isfinite(out["pred_delta"]).all())
                self.assertTrue((Path(td) / "m.pt").exists())
                self.assertEqual(out["device"]["device"], "cuda:0")


if __name__ == "__main__":
    unittest.main()