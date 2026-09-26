# SciTeX Notebook (`scitex-notebook`)

<p align="center">
  <a href="https://scitex.ai">
    <img src="docs/scitex-logo-blue-cropped.png" alt="SciTeX" width="400">
  </a>
</p>

<p align="center"><b>Jupyter notebook verification, compilation, and DAG-based conversion to topologically-ordered Python scripts.</b></p>

<p align="center">
  <a href="https://scitex-notebook.readthedocs.io/">Full Documentation</a> · <code>uv pip install scitex-notebook[all]</code>
</p>

<!-- scitex-badges:start -->
<p align="center">
  <a href="https://pypi.org/project/scitex-notebook/"><img src="https://img.shields.io/pypi/v/scitex-notebook?label=pypi" alt="pypi"></a>
  <a href="https://pypi.org/project/scitex-notebook/"><img src="https://img.shields.io/pypi/pyversions/scitex-notebook?label=python" alt="python"></a>
  <a href="https://scitex-notebook.readthedocs.io/en/latest/"><img src="https://img.shields.io/readthedocs/scitex-notebook?label=docs" alt="docs"></a>
</p>
<p align="center">
  <a href="https://github.com/ywatanabe1989/scitex-notebook/actions/workflows/pytest-matrix-on-ubuntu-py3-11-3-12-3-13.yml"><img src="https://img.shields.io/github/actions/workflow/status/ywatanabe1989/scitex-notebook/pytest-matrix-on-ubuntu-py3-11-3-12-3-13.yml?branch=develop&label=tests" alt="tests"></a>
  <a href="https://github.com/ywatanabe1989/scitex-notebook/actions/workflows/import-smoke-on-ubuntu-py3-12.yml"><img src="https://img.shields.io/github/actions/workflow/status/ywatanabe1989/scitex-notebook/import-smoke-on-ubuntu-py3-12.yml?branch=develop&label=install-check" alt="install-check"></a>
  <a href="https://codecov.io/gh/ywatanabe1989/scitex-notebook/branch/develop/graph/badge.svg"><img src="https://img.shields.io/codecov/c/github/ywatanabe1989/scitex-notebook/develop?label=cov" alt="cov"></a>
</p>
<!-- scitex-badges:end -->

---

## Problem and Solution

| # | Problem | Solution |
|---|---------|----------|
| 1 | **Cell order lies** — on-disk `.ipynb` cell sequence has no relationship to execution order, so naive `jupyter nbconvert` produces scripts that don't run | **DAG from timestamps** — reconstructs the true execution dependency graph from `scitex-clew` session timestamps, then emits a topologically-ordered `.py` or a Mermaid diagram |
| 2 | **Silent untracked I/O** — `scitex.io.save/load` calls outside `@stx.session` leave no reproducibility trail, but nothing warns you | **`check_notebook()`** — scans for untracked I/O and flags cells that bypass session tracking |
| 3 | **Exploration vs. production gap** — notebooks let you iterate freely, but shipping means rewriting by hand into a clean script | **"Do what you want, organize later"** — execute cells in any order while exploring; `compile_notebook(...).to_script()` emits the production-ready DAG-ordered script |

## Demo

```mermaid
%%{init: {'flowchart': {'nodeSpacing': 20, 'rankSpacing': 40, 'curve': 'linear'}, 'themeVariables': {'fontSize': '12px'}}}%%
flowchart LR
    A["experiment.ipynb"] --> B[parse_notebook]
    B --> C[scitex-clew DB timestamps]
    C --> D[compile_notebook DAG]
    D --> E["to_mermaid()"]
    D --> F["to_script() topologically ordered .py"]
```

<p align="center"><sub><b>Figure 1.</b> Notebook compilation from parse to DAG-ordered script.</sub></p>

Out-of-order cells in the notebook are re-ordered into a runnable script:

```bash
$ scitex-notebook compile-notebook experiment.ipynb --format script -o experiment.py
$ python experiment.py     # runs cleanly, every time
```

## Installation

```bash
uv pip install "scitex-notebook[all]"
```

Requires Python >= 3.10.

<details>
<summary><b>Per-module extras</b></summary>

<br>

| Extra | Pulls in |
|---|---|
| `mcp` | fastmcp server for AI agents |
| `linter` | IO-call conversion via scitex-dev |
| `all` | mcp plus linter (recommended) |
| `dev` | pytest, fastmcp, scitex-dev |
| `docs` | Sphinx plus theme and myst-parser |

```bash
uv pip install "scitex-notebook[mcp]"     # MCP server for AI agents
uv pip install "scitex-notebook[linter]"  # IO-call conversion
uv pip install -e ".[dev]"                 # editable install
```

</details>

## Architecture

### 1. Parse and verify

`parse` reads cells while `verify` and `check` scan clew sessions and untracked I/O.

### 2. Compile and convert

`compile` builds the timestamp DAG and `convert` emits topologically-ordered scripts.

### 3. Serve and extend

`mcp_server` exposes notebook tools and the IPython magic tracks live cells.

```mermaid
%%{init: {'flowchart': {'nodeSpacing': 20, 'rankSpacing': 40, 'curve': 'linear'}, 'themeVariables': {'fontSize': '12px'}}}%%
flowchart LR
    PARSE[parse module] --> VERIFY[verify and check]
    VERIFY --> COMPILE[compile DAG]
    COMPILE --> CONVERT[convert script]
    COMPILE --> MCP[mcp server]
    CONVERT --> OUT[runnable outputs]
    MCP --> OUT
```

<p align="center"><sub><b>Figure 2.</b> Module collaboration from parse to served outputs.</sub></p>

## Four Interfaces

<details>
<summary><strong>Python API</strong></summary>

```python
import scitex_notebook

cells    = scitex_notebook.parse_notebook("experiment.ipynb")
issues   = scitex_notebook.check("experiment.ipynb")         # untracked IO
results  = scitex_notebook.verify("experiment.ipynb")        # via clew DB
compiled = scitex_notebook.compile("experiment.ipynb")

print(compiled.to_mermaid())   # Mermaid DAG diagram
print(compiled.to_script())    # DAG-ordered Python script

scitex_notebook.convert(
    "experiment.ipynb",
    output="experiment.py",
    mode="unified",            # or "per_cell"
)
```

</details>

<details>
<summary><strong>CLI</strong></summary>

```bash
scitex-notebook verify-notebook experiment.ipynb
scitex-notebook check-notebook experiment.ipynb
scitex-notebook compile-notebook experiment.ipynb --format mermaid
scitex-notebook compile-notebook experiment.ipynb --format script -o experiment.py
scitex-notebook convert-notebook experiment.ipynb --mode unified -o experiment.py
scitex-notebook --help-recursive               # all commands + flags
scitex-notebook --json verify-notebook exp.ipynb  # structured output
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
| `notebook_parse_notebook` | Parse `.ipynb` and return all cells |
| `notebook_get_code_cells` | Return only code cells |
| `notebook_get_notebook_name` | Return notebook stem name |
| `notebook_skills_list` | List bundled skill pages |
| `notebook_skills_get` | Return a named skill page body |

```bash
scitex-notebook mcp start                      # start stdio server
scitex-notebook mcp list-tools                 # list available tools
scitex-notebook mcp doctor                     # verify MCP dependencies
```

</details>

## Python API

```python
from scitex_notebook import (
    parse_notebook, get_code_cells, get_notebook_name,
    compile, convert, verify, check,
)

cells = parse_notebook("experiment.ipynb")
compiled = compile("experiment.ipynb")
print(compiled.to_mermaid())   # Mermaid DAG
print(compiled.to_script())    # Topologically-ordered .py

results = verify("experiment.ipynb")
issues = check("experiment.ipynb")
```

## CLI

```bash
scitex-notebook compile-notebook experiment.ipynb   # DAG-ordered .py (--format script)
scitex-notebook convert-notebook experiment.ipynb   # .ipynb → @stx.session script
scitex-notebook verify-notebook experiment.ipynb    # clew session pass/fail
scitex-notebook check-notebook experiment.ipynb     # untracked-IO scan
scitex-notebook list-python-apis -vv                # public APIs with signatures
scitex-notebook skills list                         # bundled skill pages
scitex-notebook --help-recursive                    # full CLI reference
```

## IPython Magic Extension

```python
%load_ext scitex_notebook   # one line at the top of any notebook
```

Once loaded, every executed cell is analysed at runtime:
- **Hidden-state leak detection** — warns when a cell reads a name not defined by any earlier cell in this run
- **Out-of-order execution check** — flags non-monotonic `execution_count`
- **Untracked I/O** — every `stx.io.save/load` call is recorded per-cell

Cell metadata (dependencies, warnings, file hashes) is written to the same
Clew store used by `@scitex.session` and `stx.io`.

```bash
%load_ext scitex_notebook
%unload_ext scitex_notebook
```

## Dependencies

- **Required**: [`scitex-clew`](https://github.com/ywatanabe1989/scitex-clew) — execution-order reconstruction via timestamped sessions.
- **Optional**: [`scitex-linter`](https://github.com/ywatanabe1989/scitex-linter) — advanced IO-call rewriting during conversion.

## Part of SciTeX

`scitex-notebook` is part of [**SciTeX**](https://scitex.ai). Install via
the umbrella with `pip install scitex[notebook]` to use as
`scitex.notebook` (Python) or `scitex notebook ...` (CLI).

The SciTeX system follows the Four Freedoms for Research below, inspired by [the Free Software Definition](https://www.gnu.org/philosophy/free-sw.en.html):

>Four Freedoms for Research
>
>0. The freedom to **run** your research anywhere — your machine, your terms.
>1. The freedom to **study** how every step works — from raw data to final manuscript.
>2. The freedom to **redistribute** your workflows, not just your papers.
>3. The freedom to **modify** any module and share improvements with the community.
>
>AGPL-3.0 — because we believe research infrastructure deserves the same freedoms as the software it runs on.

---

<p align="center">
  <a href="https://scitex.ai" target="_blank"><img src="docs/scitex-icon-navy-inverted.png" alt="SciTeX" width="40"/></a>
</p>

<!-- EOF -->
