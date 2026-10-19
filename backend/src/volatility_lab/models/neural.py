"""GPU-only neural forecasters (compact MLP and GRU) for the surface-change target.

Compute policy (decision.md DEC-015): every tensor lives on a verified CUDA device and
``require_cuda`` raises -- it never falls back to CPU. ``torch`` is imported lazily so this module can be
imported (and the failure path unit-tested with a stand-in object) on machines without PyTorch.

Target: ``Delta = y_{t+h} - s_t`` divided by one global scalar (train std), so the masked MSE is
proportional to the vol-point MSE used in evaluation. Missing target cells carry zero loss weight.
"""
from __future__ import annotations

import copy
import time
from typing import Dict, Optional

import numpy as np

from volatility_lab.config.settings import TrainConfig

GPU_HELP = (
    "No CUDA GPU is available, so neural training/validation/inference is refused (no CPU fallback).\n"
    "In Colab: Runtime -> Change runtime type -> Hardware accelerator: GPU (T4 or better) -> Save, "
    "then Runtime -> Restart session and re-run from the top."
)


class GpuUnavailableError(RuntimeError):
    pass


def require_cuda(torch_module=None) -> dict:
    """Return device metadata or raise ``GpuUnavailableError``. ``torch_module`` lets tests inject a stub."""
    if torch_module is None:
        try:
            import torch as torch_module  # noqa: PLC0415
        except (ImportError, OSError) as exc:  # missing, or installed but unusable (e.g. broken DLLs)
            raise GpuUnavailableError(f"PyTorch could not be imported ({exc.__class__.__name__}).\n" + GPU_HELP) from exc
    if not torch_module.cuda.is_available():
        raise GpuUnavailableError(GPU_HELP)
    props = torch_module.cuda.get_device_properties(0)
    return {
        "device": "cuda:0", "name": props.name, "total_memory_gb": round(props.total_memory / 2 ** 30, 2),
        "capability": f"{props.major}.{props.minor}", "torch": torch_module.__version__,
        "cuda": torch_module.version.cuda, "cudnn": torch_module.backends.cudnn.version(),
    }


def _modules(torch):
    nn = torch.nn

    class MLP(nn.Module):
        def __init__(self, d_in, n_out, hidden, dropout):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(d_in, hidden), nn.GELU(), nn.Dropout(dropout),
                nn.Linear(hidden, hidden), nn.GELU(), nn.Dropout(dropout), nn.Linear(hidden, n_out))

        def forward(self, x):
            return self.net(x)

    class GRUNet(nn.Module):
        def __init__(self, d_in, n_out, hidden, dropout):
            super().__init__()
            self.gru = nn.GRU(d_in, hidden, batch_first=True)
            self.drop = nn.Dropout(dropout)
            self.head = nn.Linear(hidden, n_out)

        def forward(self, x):
            out, _ = self.gru(x)
            return self.head(self.drop(out[:, -1]))

    return MLP, GRUNet


def _norm_fit(X: np.ndarray):
    axes = tuple(range(X.ndim - 1))
    mu = X.mean(axis=axes)
    sd = X.std(axis=axes)
    return mu, np.where(sd < 1e-8, 1.0, sd)


def train_and_predict(kind: str, data: Dict[str, np.ndarray], cfg: TrainConfig, seed: int, *,
                      torch_module=None, ckpt_path: Optional[str] = None, log=None) -> dict:
    """Train on ``data['Xtr']`` with early stopping on ``data['Xva']`` and predict ``data['Xte']``.

    ``data`` keys: Xtr, Dtr, Mtr, Xva, Dva, Mva, Xte (X: tabular (N,D) for ``mlp`` or sequences (N,L,D) for
    ``gru``; D*: change targets (NaN allowed); M*: boolean loss masks). Returns decimal-IV change
    predictions for the test rows plus history and metadata.
    """
    torch = torch_module
    if torch is None:
        import torch  # noqa: PLC0415
    info = require_cuda(torch)
    dev = torch.device("cuda:0")
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    MLP, GRUNet = _modules(torch)

    mu, sd = _norm_fit(data["Xtr"])
    ysd = float(np.sqrt(np.mean(data["Dtr"][data["Mtr"]] ** 2)))

    def X_(a):
        return torch.tensor(((a - mu) / sd), dtype=torch.float32, device=dev)

    def D_(a, m):
        return torch.tensor(np.where(m, a, 0.0) / ysd, dtype=torch.float32, device=dev), torch.tensor(m, dtype=torch.float32, device=dev)

    Xtr, Xva, Xte = X_(data["Xtr"]), X_(data["Xva"]), X_(data["Xte"])
    Dtr, Mtr = D_(data["Dtr"], data["Mtr"])
    Dva, Mva = D_(data["Dva"], data["Mva"])
    n_out = Dtr.shape[1]
    d_in = Xtr.shape[-1]
    net = (MLP if kind == "mlp" else GRUNet)(d_in, n_out, cfg.hidden if kind == "mlp" else cfg.gru_hidden, cfg.dropout).to(dev)
    opt = torch.optim.AdamW(net.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)

    def masked_mse(pred, y, m):
        return ((pred - y) ** 2 * m).sum() / m.sum().clamp(min=1.0)

    hist = {"train_loss": [], "val_loss": []}
    best, best_state, best_epoch, bad = np.inf, None, -1, 0
    t0 = time.time()
    n = Xtr.shape[0]
    g = torch.Generator(device=dev)
    g.manual_seed(seed)
    for epoch in range(cfg.max_epochs):
        net.train()
        perm = torch.randperm(n, device=dev, generator=g)
        tot, cnt = 0.0, 0
        for i in range(0, n, cfg.batch_size):
            idx = perm[i:i + cfg.batch_size]
            loss = masked_mse(net(Xtr[idx]), Dtr[idx], Mtr[idx])
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            tot += float(loss) * idx.numel()
            cnt += idx.numel()
        net.eval()
        with torch.no_grad():
            val = float(masked_mse(net(Xva), Dva, Mva))
        hist["train_loss"].append(tot / cnt)
        hist["val_loss"].append(val)
        if val < best - 1e-9:
            best, best_epoch, bad = val, epoch, 0
            best_state = copy.deepcopy({k: v.detach().clone() for k, v in net.state_dict().items()})
        else:
            bad += 1
            if bad >= cfg.patience:
                break
        if log and (epoch % 25 == 0):
            log(f"  [{kind} seed {seed}] epoch {epoch:3d} train {hist['train_loss'][-1]:.4f} val {val:.4f}")
    net.load_state_dict(best_state)
    net.eval()
    with torch.no_grad():
        pred = net(Xte).detach().cpu().numpy() * ysd
    out = {"pred_delta": pred, "history": hist, "best_epoch": int(best_epoch), "epochs_run": len(hist["val_loss"]),
           "best_val_loss_std_units": float(best), "target_scale": ysd, "seconds": round(time.time() - t0, 2),
           "peak_gpu_mem_mb": round(torch.cuda.max_memory_allocated() / 2 ** 20, 1), "device": info}
    if ckpt_path:
        torch.save({"state_dict": best_state, "kind": kind, "seed": seed, "d_in": d_in, "n_out": n_out,
                    "x_mu": mu, "x_sd": sd, "target_scale": ysd, "cfg": cfg.__dict__, "best_epoch": best_epoch},
                   ckpt_path)
    return out
