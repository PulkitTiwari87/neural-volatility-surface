"""Generate ``notebooks/Neural_Volatility_Surface_Colab.ipynb`` from the tested package source.

The notebook embeds every ``backend/src/volatility_lab`` module verbatim (``%%writefile`` cells), so a fresh Colab
runtime runs exactly the code the local unit tests exercised. Re-run this script after changing the package:

    python scripts/build_colab_notebook.py

Outputs are stripped (the generated file carries no results).
"""
from __future__ import annotations

import sys
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "backend" / "src"
OUT = ROOT / "notebooks" / "Neural_Volatility_Surface_Colab.ipynb"
sys.path.insert(0, str(Path(__file__).parent / "_notebook_cells"))
import cells  # noqa: E402  (cell text lives next to this script)
import cells_e2  # noqa: E402
import cells_h1  # noqa: E402
import cells_h1b  # noqa: E402
OUT_E2 = ROOT / "notebooks" / "Neural_Volatility_Surface_E2_FixedExpiry.ipynb"
OUT_H1 = ROOT / "notebooks" / "Neural_Volatility_Surface_H1_RidgeGrid.ipynb"
OUT_H1B = ROOT / "notebooks" / "Neural_Volatility_Surface_H1b_FixedExpiryGrid.ipynb"


def build() -> nbf.NotebookNode:
    nb = nbf.v4.new_notebook()
    c = []
    md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell

    c += [md(cells.OVERVIEW), md(cells.H_CONFIG), code(cells.CONFIG), md(cells.H_GPU), code(cells.GPU),
          md(cells.H_SETUP), code(cells.SETUP_PIP)]
    mods = sorted(p for p in (SRC / "volatility_lab").rglob("*.py") if "__pycache__" not in p.parts)
    dirs = sorted({str(m.parent.relative_to(SRC)).replace("\\", "/") for m in mods})
    c.append(code("import os\nfor d in " + repr(dirs) + ":\n    os.makedirs(f'/content/nvs/src/{d}', exist_ok=True)\nprint('package directories ready')"))
    for m in mods:
        rel = m.relative_to(SRC).as_posix()
        c.append(code(f"%%writefile /content/nvs/src/{rel}\n" + m.read_text(encoding="utf-8").rstrip("\n") + "\n"))
    c += [code(cells.IMPORTS), code(cells.GPU_SMOKE),
          md(cells.H_DATA), code(cells.DATA_CONNECT),
          md(cells.H_AUDIT), code(cells.AUDIT),
          md(cells.H_SURFACE), code(cells.SURFACE_PLOTS),
          md(cells.H_FEATURES), code(cells.FEATURES),
          md(cells.H_BASE), code(cells.BASELINES),
          md(cells.H_NEURAL), code(cells.NEURAL),
          md(cells.H_EVAL), code(cells.EVAL_TABLES), code(cells.EVAL_PLOTS),
          md(cells.H_EXTRA), code(cells.EXTRA_PLOTS),
          md(cells.H_INTERP), code(cells.INTERPRETATION),
          md(cells.H_SAVE), code(cells.SAVE),
          md(cells.H_REPRO)]
    nb.cells = c
    nb.metadata = {"colab": {"name": "Neural_Volatility_Surface_Colab.ipynb", "provenance": [], "gpuType": "T4"},
                   "accelerator": "GPU",
                   "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                   "language_info": {"name": "python"}}
    return nb


def build_e2() -> nbf.NotebookNode:
    """Experiment E-2: fixed-expiry vs nearest-expiry target. Shares setup, data and audit cells with E-1."""
    nb = nbf.v4.new_notebook()
    md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
    c = [md(cells_e2.OVERVIEW), md(cells.H_CONFIG), code(cells.CONFIG), md(cells.H_GPU), code(cells.GPU),
         md(cells.H_SETUP), code(cells.SETUP_PIP)]
    mods = sorted(p for p in (SRC / "volatility_lab").rglob("*.py") if "__pycache__" not in p.parts)
    dirs = sorted({str(m.parent.relative_to(SRC)).replace("\\", "/") for m in mods})
    c.append(code("import os\nfor d in " + repr(dirs) + ":\n    os.makedirs(f'/content/nvs/src/{d}', exist_ok=True)\nprint('package directories ready')"))
    for m in mods:
        rel = m.relative_to(SRC).as_posix()
        c.append(code(f"%%writefile /content/nvs/src/{rel}\n" + m.read_text(encoding="utf-8").rstrip("\n") + "\n"))
    c += [code(cells.IMPORTS), code(cells.GPU_SMOKE),
          md(cells.H_DATA), code(cells.DATA_CONNECT),
          md(cells.H_AUDIT), code(cells.AUDIT),
          md(cells_e2.H_FEATURES), code(cells_e2.FEATURES),
          md(cells_e2.H_BASE), code(cells_e2.BASELINES),
          md(cells_e2.H_NEURAL), code(cells_e2.NEURAL),
          md(cells_e2.H_EVAL), code(cells_e2.EVAL),
          md(cells_e2.H_EXTRA), code(cells_e2.EXTRA_HEAD + cells.EXTRA_PLOTS + cells_e2.EXTRA_TAIL + cells_e2.EXTRA_LOOP),
          md(cells_e2.H_INTERP), code(cells_e2.INTERP),
          md(cells_e2.H_SAVE), code(cells_e2.SAVE),
          md(cells.H_REPRO)]
    nb.cells = c
    nb.metadata = {"colab": {"name": "Neural_Volatility_Surface_E2_FixedExpiry.ipynb", "provenance": [], "gpuType": "T4"},
                   "accelerator": "GPU",
                   "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                   "language_info": {"name": "python"}}
    return nb


def build_h1() -> nbf.NotebookNode:
    """Experiment H1 (pre-registered 2026-10-16): wider ridge-penalty grid, baselines only, NO neural training, CPU is enough."""
    nb = nbf.v4.new_notebook()
    md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
    c = [md(cells_h1.OVERVIEW), md(cells.H_CONFIG), code(cells_h1.CONFIG), md(cells.H_SETUP), code(cells.SETUP_PIP)]
    mods = sorted(p for p in (SRC / "volatility_lab").rglob("*.py") if "__pycache__" not in p.parts)
    dirs = sorted({str(m.parent.relative_to(SRC)).replace("\\", "/") for m in mods})
    c.append(code("import os\nfor d in " + repr(dirs) + ":\n    os.makedirs(f'/content/nvs/src/{d}', exist_ok=True)\nprint('package directories ready')"))
    for m in mods:
        rel = m.relative_to(SRC).as_posix()
        c.append(code(f"%%writefile /content/nvs/src/{rel}\n" + m.read_text(encoding="utf-8").rstrip("\n") + "\n"))
    c += [code(cells_h1.IMPORTS),
          md(cells.H_DATA), code(cells.DATA_CONNECT),
          md(cells.H_AUDIT), code(cells.AUDIT),
          md(cells_e2.H_FEATURES), code(cells_e2.FEATURES),
          md(cells_h1.H_BASE), code(cells_h1.BASELINES),
          md(cells_h1.H_EVAL), code(cells_h1.EVAL),
          md(cells_h1.H_PLOTS), code(cells_h1.PLOTS),
          code(cells_e2.EXTRA_HEAD + cells.EXTRA_PLOTS + cells_e2.EXTRA_TAIL + cells_h1.EXTRA_LOOP),
          md(cells_h1.H_INTERP), code(cells_h1.INTERPRETATION),
          md(cells_h1.H_SAVE), code(cells_h1.SAVE)]
    nb.cells = c
    nb.metadata = {"colab": {"name": "Neural_Volatility_Surface_H1_RidgeGrid.ipynb", "provenance": []},
                   "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                   "language_info": {"name": "python"}}
    return nb


def build_h1b() -> nbf.NotebookNode:
    """Experiment H1b (pre-registered 2026-10-19): ridge grid to 1e9 for the fixed-expiry label only; baselines only, NO neural training."""
    nb = nbf.v4.new_notebook()
    md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
    c = [md(cells_h1b.OVERVIEW), md(cells.H_CONFIG), code(cells_h1b.CONFIG), md(cells.H_SETUP), code(cells.SETUP_PIP)]
    mods = sorted(p for p in (SRC / "volatility_lab").rglob("*.py") if "__pycache__" not in p.parts)
    dirs = sorted({str(m.parent.relative_to(SRC)).replace("\\", "/") for m in mods})
    c.append(code("import os\nfor d in " + repr(dirs) + ":\n    os.makedirs(f'/content/nvs/src/{d}', exist_ok=True)\nprint('package directories ready')"))
    for m in mods:
        rel = m.relative_to(SRC).as_posix()
        c.append(code(f"%%writefile /content/nvs/src/{rel}\n" + m.read_text(encoding="utf-8").rstrip("\n") + "\n"))
    c += [code(cells_h1b.IMPORTS),
          md(cells.H_DATA), code(cells.DATA_CONNECT),
          md(cells.H_AUDIT), code(cells.AUDIT),
          md(cells_e2.H_FEATURES), code(cells_e2.FEATURES),
          md(cells_h1b.H_BASE), code(cells_h1b.BASELINES),
          md(cells_h1b.H_EVAL), code(cells_h1b.EVAL),
          md(cells_h1b.H_PLOTS), code(cells_h1b.PLOTS),
          code(cells_e2.EXTRA_HEAD + cells.EXTRA_PLOTS + cells_e2.EXTRA_TAIL + cells_h1b.EXTRA_LOOP),
          md(cells_h1b.H_INTERP), code(cells_h1b.INTERPRETATION),
          md(cells_h1b.H_SAVE), code(cells_h1b.SAVE)]
    nb.cells = c
    nb.metadata = {"colab": {"name": "Neural_Volatility_Surface_H1b_FixedExpiryGrid.ipynb", "provenance": []},
                   "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                   "language_info": {"name": "python"}}
    return nb


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    for builder, target in ((build, OUT), (build_e2, OUT_E2), (build_h1, OUT_H1), (build_h1b, OUT_H1B)):
        nb = builder()
        nbf.validate(nb)
        nbf.write(nb, target)
        print(f"wrote {target.relative_to(ROOT)}  ({len(nb.cells)} cells)")