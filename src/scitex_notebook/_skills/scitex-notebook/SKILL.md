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

### Mandatory

| File | Description |
|------|-------------|
| [01_installation.md](01_installation.md) | pip install + extras + verify |
| [02_quick-start.md](02_quick-start.md) | verify / check / compile / convert in one screen |
| [03_python-api.md](03_python-api.md) | Public callables + `CompiledNotebook` |
| [04_cli-reference.md](04_cli-reference.md) | `scitex-notebook` console commands |
| [05_mcp-tools.md](05_mcp-tools.md) | FastMCP server — six `notebook_*` tools |

### Deep-dive

| File | Description |
|------|-------------|
| [11_parse-and-convert.md](11_parse-and-convert.md) | parse_notebook, get_code_cells, get_notebook_name, convert |
| [12_dag-compile.md](12_dag-compile.md) | compile, CompiledNotebook.to_mermaid()/to_script(), DAG edge logic |
| [13_verify.md](13_verify.md) | verify (clew session results), check (untracked IO scan) |

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
