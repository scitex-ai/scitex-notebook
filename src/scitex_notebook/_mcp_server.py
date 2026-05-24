#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canonical FastMCP server for scitex-notebook.

Single ``mcp`` instance is the single source of truth — every tool is
registered here with ``@mcp.tool()``. The umbrella ``scitex._mcp_tools``
imports this module and mounts ``mcp`` via ``safe_mount(namespace=...)``;
no per-tool re-wrapping is needed (see general/03_interface_03_mcp/02).

Tool naming follows ``<pkg>_<verb>_<noun>``: bare ``verify`` etc. inside
this module's mounted namespace become ``notebook_verify`` at the
umbrella level, matching the existing user-facing names. To preserve
that contract while keeping internal names short, we register the tools
with the prefix already attached so direct fastmcp clients (and the
legacy ``scitex-notebook mcp start``) see the same names the umbrella
publishes.

Run directly with::

    fastmcp run scitex_notebook._mcp_server:mcp

Or via the package CLI::

    scitex-notebook mcp start
"""

from __future__ import annotations

import json
from typing import Optional

from fastmcp import FastMCP

mcp = FastMCP(
    name="scitex-notebook",
    instructions=(
        "Verify, audit, compile, and convert Jupyter notebooks with "
        "Clew-aware reproducibility tooling. Pair with the IPython "
        "extension (%load_ext scitex_notebook) for live cell-level "
        "tracking."
    ),
)


def _json(data) -> str:
    return json.dumps(data, indent=2, default=str)


# ---------------------------------------------------------------------------
# Notebook tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def notebook_verify(path: str) -> str:
    """Verify Clew sessions associated with a notebook.

    Run every recorded ``@scitex.session`` block in the given ``.ipynb``
    against the Clew database and report pass/fail per session.

    Use whenever the user asks "is my notebook reproducible?", "verify
    this .ipynb", "did the analysis actually run cleanly?", "re-run
    verification on this notebook", or before sharing/submitting a
    notebook as supplementary material. Returns per-session verification
    status from the Clew DB.

    Parameters
    ----------
    path
        Filesystem path to a ``.ipynb`` file.
    """
    from scitex_notebook import verify_notebook

    results = verify_notebook(path)
    return _json({"success": True, "path": path, "results": results})


@mcp.tool()
async def notebook_check(path: str) -> str:
    """Audit a notebook for untracked I/O outside ``@scitex.session``.

    Find every ``scitex.io`` save/load call that lives outside a
    ``@scitex.session`` block (i.e. invisible to the reproducibility
    DAG).

    Use whenever the user asks to "find untracked I/O", "audit my
    notebook for session coverage", "what's outside @scitex.session?",
    "lint this notebook for reproducibility gaps", or before calling
    ``notebook_verify`` / ``notebook_compile`` on an unfamiliar
    notebook. Returns a list of offending cells with line numbers.

    Parameters
    ----------
    path
        Filesystem path to a ``.ipynb`` file.
    """
    from scitex_notebook import check_notebook

    issues = check_notebook(path)
    return _json({"success": True, "path": path, "issues": issues})


@mcp.tool()
async def notebook_compile(path: str, format: str = "mermaid") -> str:
    """Compile a notebook's cell-dependency DAG from Clew records.

    Reconstruct a notebook's true cell-dependency DAG from
    Clew-recorded execution timestamps and emit it as a Mermaid diagram,
    a topologically-ordered standalone ``.py`` script, or raw JSON.

    Embodies "do what you want, organize later" — cells can be
    executed in any order during exploration and still produce a clean
    linear script. Use whenever the user asks to "compile this
    notebook", "show the execution DAG", "visualize cell dependencies",
    "linearize my notebook", "export a script in dependency order",
    "turn this Jupyter mess into a .py", or needs a reproducible script
    built from out-of-order cell runs.

    Parameters
    ----------
    path
        Filesystem path to a ``.ipynb`` file.
    format
        Output format. One of ``"mermaid"`` (default), ``"script"``,
        ``"json"``.
    """
    from scitex_notebook import compile_notebook

    compiled = compile_notebook(path)

    if format == "mermaid":
        output = compiled.to_mermaid()
    elif format == "script":
        output = compiled.to_script()
    elif format == "json":
        output = {
            "notebook_path": compiled.notebook_path,
            "execution_order": compiled.execution_order,
            "dag": compiled.dag,
        }
    else:
        return _json({"success": False, "error": f"Unknown format: {format}"})

    return _json({"success": True, "path": path, "format": format, "output": output})


@mcp.tool()
async def notebook_convert(
    path: str,
    mode: str = "per_cell",
    order: str = "cell",
    output: Optional[str] = None,
) -> str:
    """Convert a notebook to a SciTeX Python script with session decorators.

    Drop-in replacement for ``jupyter nbconvert --to script`` plus the
    manual step of adding ``@stx.session`` decorators around each cell.

    Use whenever the user asks to "convert this notebook to .py",
    "export as Python script", "make this reproducible as a script", or
    "strip the notebook into scitex sessions".

    Parameters
    ----------
    path
        Filesystem path to a ``.ipynb`` file.
    mode
        ``"per_cell"`` keeps each cell as its own session (default);
        ``"unified"`` wraps everything in one session.
    order
        ``"cell"`` keeps original notebook order (default);
        ``"dag"`` topologically sorts by dependency.
    output
        Optional output ``.py`` path. If omitted, the script is
        returned in the response payload only.
    """
    from scitex_notebook import convert_notebook

    script = convert_notebook(path, output=output, order=order, mode=mode)
    return _json(
        {
            "success": True,
            "path": path,
            "mode": mode,
            "order": order,
            "output_file": output,
            "script": script,
        }
    )


# ---------------------------------------------------------------------------
# Notebook parsing tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def notebook_parse_notebook(path: str) -> str:
    """Parse a ``.ipynb`` file and return every cell.

    Read the notebook with stdlib JSON (no ``nbformat`` dependency) and
    return each cell's ``index``, ``source``, ``cell_id``, and
    ``cell_type`` — both code and markdown cells.

    Use whenever the user asks to "parse this notebook", "list the cells",
    "show me what's in this .ipynb", or needs the raw cell structure before
    a deeper compile/verify step. Returns the full cell list.

    Parameters
    ----------
    path
        Filesystem path to a ``.ipynb`` file.
    """
    from scitex_notebook import parse_notebook

    cells = parse_notebook(path)
    return _json({"success": True, "path": path, "n_cells": len(cells), "cells": cells})


@mcp.tool()
async def notebook_get_code_cells(path: str) -> str:
    """Return only the code cells of a ``.ipynb`` file.

    Parse the notebook and filter to ``cell_type == "code"``, dropping
    markdown/raw cells.

    Use whenever the user asks for "just the code cells", "extract the code
    from this notebook", or needs the executable cells without prose.
    Returns the filtered cell list.

    Parameters
    ----------
    path
        Filesystem path to a ``.ipynb`` file.
    """
    from scitex_notebook import get_code_cells

    cells = get_code_cells(path)
    return _json({"success": True, "path": path, "n_cells": len(cells), "cells": cells})


@mcp.tool()
async def notebook_get_notebook_name(path: str) -> str:
    """Return the notebook's stem name (filename without extension).

    Use whenever the user asks for "the notebook name", or a downstream
    tool needs a stable, extension-free identifier for the notebook.

    Parameters
    ----------
    path
        Filesystem path to a ``.ipynb`` file.
    """
    from scitex_notebook import get_notebook_name

    name = get_notebook_name(path)
    return _json({"success": True, "path": path, "name": name})


# ---------------------------------------------------------------------------
# Skills tools (canonical pair — see 03_interface_03_mcp/06_skills-integration.md)
# ---------------------------------------------------------------------------


def _skills_root():
    """Locate the package's ``_skills/scitex-notebook/`` directory."""
    from pathlib import Path

    here = Path(__file__).resolve().parent
    cand = here / "_skills" / "scitex-notebook"
    if cand.is_dir():
        return cand
    # Fallback: bare _skills/ if the per-pip-name subfolder is absent.
    return here / "_skills"


@mcp.tool()
async def notebook_skills_list() -> str:
    """List the scitex-notebook skill pages bundled with this package."""
    root = _skills_root()
    if not root.is_dir():
        return _json({"success": True, "count": 0, "skills": []})
    skills = []
    for p in sorted(root.rglob("*.md")):
        rel = p.relative_to(root)
        skills.append({"name": str(rel.with_suffix("")), "path": str(rel)})
    return _json({"success": True, "count": len(skills), "skills": skills})


@mcp.tool()
async def notebook_skills_get(name: str) -> str:
    """Return the body of a named skill page (e.g. ``"SKILL"``)."""
    root = _skills_root()
    candidates = [root / f"{name}.md", root / name]
    for p in candidates:
        if p.is_file():
            return _json(
                {
                    "success": True,
                    "name": name,
                    "content": p.read_text(encoding="utf-8"),
                }
            )
    return _json({"success": False, "error": f"skill {name!r} not found under {root}"})


# ---------------------------------------------------------------------------
# Server entry point — used by `scitex-notebook mcp start`
# ---------------------------------------------------------------------------


def run_server() -> None:
    """Start the FastMCP server over stdio."""
    mcp.run()


__all__ = ["mcp", "run_server"]

# EOF
