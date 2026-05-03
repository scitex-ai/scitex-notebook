---
name: scitex-notebook
description: |
  [WHAT] Jupyter notebook reproducibility.
  [WHEN] Use when the user asks to "verify my notebook", "check notebook reproducibility", "is this notebook reproducible?", "audit untracked I/O in this notebook".
  [HOW] `import scitex_notebook` for the Python API; see leaf skills for entry points.
tags: [scitex-notebook]
---


# stx.notebook — Skills Index

Verify, compile, and convert Jupyter notebooks. Reconstructs the actual execution dependency DAG from clew DB timestamps — "do what you want, organize later."

## Sub-skills

| File | Description |
|------|-------------|
| [01_parse-and-convert.md](01_parse-and-convert.md) | parse_notebook, get_code_cells, get_notebook_name, convert_notebook |
| [02_dag-compile.md](02_dag-compile.md) | compile_notebook, CompiledNotebook.to_mermaid(), to_script(), DAG edge logic |
| [03_verify.md](03_verify.md) | verify_notebook (clew session results), check_notebook (untracked IO scan) |

## Quick Reference

```python
from scitex.notebook import (
    parse_notebook, get_code_cells,
    compile_notebook, convert_notebook,
    verify_notebook, check_notebook,
)

cells = parse_notebook("experiment.ipynb")
compiled = compile_notebook("experiment.ipynb")
print(compiled.to_mermaid())   # Mermaid DAG
print(compiled.to_script())    # Topologically-ordered .py

results = verify_notebook("experiment.ipynb")
issues = check_notebook("experiment.ipynb")
```
