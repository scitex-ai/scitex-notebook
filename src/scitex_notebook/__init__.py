#!/usr/bin/env python3
"""SciTeX Notebook — Jupyter notebook verification and compilation.

Provides tools to verify, compile, convert, and check Jupyter notebooks
for reproducibility using the Clew verification system.

Key Concept: Notebooks can be executed in any cell order. SciTeX records
actual execution order via timestamps, then reconstructs the dependency
DAG afterward ("do what you want, organize later").

Examples
--------
>>> from scitex_notebook import verify_notebook, compile_notebook
>>> results = verify_notebook("experiment.ipynb")
>>> compiled = compile_notebook("experiment.ipynb")
>>> print(compiled.to_mermaid())  # DAG visualization
>>> print(compiled.to_script())   # DAG-ordered .py
"""

from __future__ import annotations

from ._compile import CompiledNotebook, compile_notebook
from ._convert import convert_notebook
from ._magic import load_ipython_extension, unload_ipython_extension
from ._parse import get_code_cells, get_notebook_name, parse_notebook
from ._verify import check_notebook, verify_notebook

# Canonical bare-verb aliases (Python ↔ MCP parity per general/03_interface_03_mcp/07).
# MCP tool ``notebook_verify`` pairs with ``scitex_notebook.verify``; the
# legacy ``verify_notebook`` name is kept as a back-compat alias.
verify = verify_notebook
check = check_notebook
compile = compile_notebook  # noqa: A001 — shadowing the builtin is intentional here.
convert = convert_notebook

try:
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as _v

    try:
        __version__ = _v("scitex-notebook")
    except PackageNotFoundError:
        __version__ = "0.0.0+local"
    del _v, PackageNotFoundError
except ImportError:  # pragma: no cover — only on ancient Pythons
    __version__ = "0.0.0+local"
__all__ = [
    "parse_notebook",
    "get_code_cells",
    "get_notebook_name",
    # Canonical bare verbs (match MCP tool names per general/03_interface_03_mcp/07).
    "verify",
    "check",
    "compile",
    "convert",
    "CompiledNotebook",
    "__version__",
]
# Legacy verb_noun names (verify_notebook etc.) remain importable for prior
# callers but are intentionally absent from ``__all__`` so the canonical
# bare-verb names are what audit-mcp-tools sees.
#
# ``load_ipython_extension`` / ``unload_ipython_extension`` are IPython
# framework entry-point callbacks invoked by ``%load_ext scitex_notebook``
# (they take an ``ipython`` shell object, not data). They MUST stay
# importable from the package top — IPython resolves them via ``getattr``,
# which does not require ``__all__`` membership — but they are NOT part of
# the agent-facing Python-API surface, so they are intentionally absent
# from ``__all__`` (no MCP tool would make sense for a shell-hook callback).

# EOF
