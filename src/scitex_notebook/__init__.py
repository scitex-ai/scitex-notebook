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
from ._parse import get_code_cells, get_notebook_name, parse_notebook
from ._verify import check_notebook, verify_notebook

__version__ = "0.1.0"

__all__ = [
    "parse_notebook",
    "get_code_cells",
    "get_notebook_name",
    "verify_notebook",
    "check_notebook",
    "compile_notebook",
    "CompiledNotebook",
    "convert_notebook",
    "__version__",
]

# EOF
