#!/usr/bin/env python3
"""MCP handlers for scitex-notebook server."""

from __future__ import annotations

__all__ = [
    "verify_handler",
    "check_handler",
    "compile_handler",
    "convert_handler",
]


async def verify_handler(path: str) -> dict:
    """Verify clew sessions associated with a notebook."""
    from scitex_notebook import verify_notebook

    results = verify_notebook(path)
    return {"success": True, "path": path, "results": results}


async def check_handler(path: str) -> dict:
    """Find cells with untracked scitex.io calls."""
    from scitex_notebook import check_notebook

    issues = check_notebook(path)
    return {"success": True, "path": path, "issues": issues}


async def compile_handler(path: str, format: str = "mermaid") -> dict:
    """Compile notebook execution history into a DAG."""
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
        return {"success": False, "error": f"Unknown format: {format}"}

    return {"success": True, "path": path, "format": format, "output": output}


async def convert_handler(
    path: str,
    mode: str = "per_cell",
    order: str = "cell",
    output: str | None = None,
) -> dict:
    """Convert notebook to SciTeX Python script."""
    from scitex_notebook import convert_notebook

    script = convert_notebook(path, output=output, order=order, mode=mode)
    return {
        "success": True,
        "path": path,
        "mode": mode,
        "order": order,
        "output_file": output,
        "script": script,
    }


# EOF
