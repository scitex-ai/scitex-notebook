---
description: |
  [TOPIC] Quick start
  [DETAILS] Smallest example — verify, check, compile, convert a Jupyter notebook.
tags: [scitex-notebook-quick-start]
---

# Quick Start

## CLI — one-shot

```bash
scitex-notebook verify-notebook  experiment.ipynb     # check clew session results
scitex-notebook check-notebook   experiment.ipynb     # find untracked scitex.io calls
scitex-notebook compile-notebook experiment.ipynb --format mermaid
scitex-notebook convert-notebook experiment.ipynb --mode unified -o exp.py
scitex-notebook --help-recursive                      # full reference
```

## IPython magic

```python
%load_ext scitex_notebook          # one line at notebook top
```

After loading, every executed cell is analysed at runtime for hidden-state
leaks, out-of-order execution, and untracked I/O — all recorded in the
same Clew DB.

## Python — same surface

```python
from scitex_notebook import (
    parse_notebook, get_code_cells,
    compile, convert, verify, check,
)

cells = get_code_cells("experiment.ipynb")
compiled = compile("experiment.ipynb")
print(compiled.to_mermaid())   # DAG of cell dependencies
print(compiled.to_script())    # topologically-ordered .py

results = verify("experiment.ipynb")     # clew session results
issues  = check("experiment.ipynb")      # untracked-IO scan
```

## Why this exists

`scitex-notebook` reconstructs the *actual* execution dependency DAG from
clew DB timestamps — "do what you want, organize later." It treats the
notebook as a record of *what ran* and produces the corresponding
reproducible script.

## Next

- [03_python-api.md](03_python-api.md) — full surface
- [04_cli-reference.md](04_cli-reference.md) — CLI commands + flags
- [12_dag-compile.md](12_dag-compile.md) — DAG construction details
- [13_verify.md](13_verify.md) — verify/check semantics
