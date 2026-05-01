# SciTeX Notebook (`scitex-notebook`)

<!-- scitex-badges:start -->
[![PyPI](https://img.shields.io/pypi/v/scitex-notebook.svg)](https://pypi.org/project/scitex-notebook/)
[![Python](https://img.shields.io/pypi/pyversions/scitex-notebook.svg)](https://pypi.org/project/scitex-notebook/)
[![Tests](https://github.com/ywatanabe1989/scitex-notebook/actions/workflows/test.yml/badge.svg)](https://github.com/ywatanabe1989/scitex-notebook/actions/workflows/test.yml)
[![Install Test](https://github.com/ywatanabe1989/scitex-notebook/actions/workflows/install-test.yml/badge.svg)](https://github.com/ywatanabe1989/scitex-notebook/actions/workflows/install-test.yml)
[![Coverage](https://codecov.io/gh/ywatanabe1989/scitex-notebook/graph/badge.svg)](https://codecov.io/gh/ywatanabe1989/scitex-notebook)
[![Docs](https://readthedocs.org/projects/scitex-notebook/badge/?version=latest)](https://scitex-notebook.readthedocs.io/en/latest/)
[![License: AGPL v3](https://img.shields.io/badge/license-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
<!-- scitex-badges:end -->

<p align="center"><b>Jupyter notebook verification, compilation, and DAG-based conversion</b></p>

---

## Problem and Solution

| # | Problem | Solution |
|---|---------|----------|
| 1 | **Cell order lies** — on-disk `.ipynb` cell sequence has no relationship to execution order, so naive `jupyter nbconvert` produces scripts that don't run | **DAG from timestamps** — reconstructs the true execution dependency graph from `scitex-clew` session timestamps, then emits a topologically-ordered `.py` or a Mermaid diagram |
| 2 | **Silent untracked I/O** — `scitex.io.save/load` calls outside `@stx.session` leave no reproducibility trail, but nothing warns you | **`check_notebook()`** — scans for untracked I/O and flags cells that bypass session tracking |
| 3 | **Exploration vs. production gap** — notebooks let you iterate freely, but shipping means rewriting by hand into a clean script | **"Do what you want, organize later"** — execute cells in any order while exploring; `compile_notebook(...).to_script()` emits the production-ready DAG-ordered script |

## Installation

Requires Python >= 3.10.

```bash
pip install scitex-notebook
```

Optional extras:

```bash
pip install "scitex-notebook[mcp]"     # MCP server for AI agents
pip install "scitex-notebook[linter]"  # IO-call conversion via scitex-linter
pip install "scitex-notebook[all]"     # everything
```

## Quickstart

<details>
<summary><strong>Python API</strong></summary>

```python
import scitex_notebook as notebook

cells    = notebook.parse_notebook("experiment.ipynb")
issues   = notebook.check_notebook("experiment.ipynb")     # untracked IO
results  = notebook.verify_notebook("experiment.ipynb")    # via clew DB
compiled = notebook.compile_notebook("experiment.ipynb")

print(compiled.to_mermaid())   # Mermaid DAG diagram
print(compiled.to_script())    # DAG-ordered Python script

notebook.convert_notebook(
    "experiment.ipynb",
    output="experiment.py",
    mode="unified",            # or "per_cell"
)
```

</details>

<details>
<summary><strong>CLI</strong></summary>

```bash
scitex-notebook verify experiment.ipynb
scitex-notebook check experiment.ipynb
scitex-notebook compile experiment.ipynb --format mermaid
scitex-notebook compile experiment.ipynb --format script -o experiment.py
scitex-notebook convert experiment.ipynb --mode unified -o experiment.py
```

</details>

<details>
<summary><strong>MCP Server — for AI Agents</strong></summary>

| Tool | Description |
|------|-------------|
| `notebook_verify`  | Verify clew sessions for a notebook |
| `notebook_check`   | Flag untracked `scitex.io` calls |
| `notebook_compile` | Return Mermaid DAG / script / JSON |
| `notebook_convert` | Convert `.ipynb` to `.py` |

```bash
python -m scitex_notebook.mcp_server
```

</details>

## Dependencies

- **Required**: [`scitex-clew`](https://github.com/ywatanabe1989/scitex-clew) — execution-order reconstruction via timestamped sessions.
- **Optional**: [`scitex-linter`](https://github.com/ywatanabe1989/scitex-linter) — advanced IO-call rewriting during conversion.

## Part of SciTeX

SciTeX Notebook is part of [**SciTeX**](https://scitex.ai).

The SciTeX system follows the Four Freedoms for Research below, inspired by [the Free Software Definition](https://www.gnu.org/philosophy/free-sw.en.html):

>Four Freedoms for Research
>
>0. The freedom to **run** your research anywhere — your machine, your terms.
>1. The freedom to **study** how every step works — from raw data to final manuscript.
>2. The freedom to **redistribute** your workflows, not just your papers.
>3. The freedom to **modify** any module and share improvements with the community.
>
>AGPL-3.0 — because we believe research infrastructure deserves the same freedoms as the software it runs on.

<!-- EOF -->
