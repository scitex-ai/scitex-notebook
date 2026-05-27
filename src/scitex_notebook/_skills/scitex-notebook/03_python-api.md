---
description: |
  [TOPIC] Python API
  [DETAILS] Public callables — parse_notebook, get_code_cells, compile, convert, verify, check, CompiledNotebook.
tags: [scitex-notebook-python-api]
---

# Python API

```python
import scitex_notebook
```

## Top-level exports (`__all__`)

| Symbol | Purpose |
|---|---|
| `parse_notebook(path)` | Parse `.ipynb` JSON into structured form |
| `get_code_cells(path)` | Iterate code cells (skipping markdown/raw) |
| `get_notebook_name(path)` | Extract canonical notebook name |
| `compile(path, *, db=None)` | Build a `CompiledNotebook` (DAG from clew timestamps) |
| `convert(path, mode=..., output=...)` | Notebook → executable `.py` |
| `verify(path, *, db=None, verify_run_fn=None)` | Look up clew session results for the notebook |
| `check(path)` | Find cells with untracked `scitex.io` calls |
| `CompiledNotebook` | Class returned by `compile()` |
| `load_ipython_extension`, `unload_ipython_extension` | IPython auto-load hooks |
| `__version__` | Package version string |

## `CompiledNotebook`

```python
compiled = scitex_notebook.compile("experiment.ipynb")
compiled.to_mermaid()    # str — Mermaid DAG diagram
compiled.to_script()     # str — topologically-ordered .py source
```

## Modes for `convert()`

| Mode | Effect |
|---|---|
| `"unified"` | Single `.py` with all cells inline + `@stx.session` |
| `"per_cell"` | One `@stx.session` function per code cell |

## See also

- [12_dag-compile.md](12_dag-compile.md) — DAG edge logic
- [13_verify.md](13_verify.md) — clew session contract
- [11_parse-and-convert.md](11_parse-and-convert.md) — parse internals
