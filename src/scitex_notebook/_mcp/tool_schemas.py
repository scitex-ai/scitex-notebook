#!/usr/bin/env python3
"""Tool schemas for the scitex-notebook MCP server."""

from __future__ import annotations

__all__ = ["get_tool_schemas"]


def get_tool_schemas():
    """Return all tool schemas for the notebook MCP server."""
    import mcp.types as types

    return [
        types.Tool(
            name="notebook_verify",
            description=(
                "Check whether every `@scitex.session` block in a `.ipynb` actually "
                "reproduces — runs each recorded Clew session and reports pass/fail per "
                "session. Use whenever the user asks 'is my notebook reproducible?', "
                "'verify this .ipynb', 'did the analysis actually run cleanly?', 're-run "
                "verification on this notebook', or before sharing/submitting a notebook "
                "as supplementary material. Returns per-session verification status from "
                "the Clew DB."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the .ipynb file",
                    },
                },
                "required": ["path"],
            },
        ),
        types.Tool(
            name="notebook_check",
            description=(
                "Audit a `.ipynb` for untracked I/O — any `scitex.io` save/load call "
                "outside a `@scitex.session` block (i.e. invisible to the reproducibility "
                "DAG). Use whenever the user asks to 'find untracked I/O', 'audit my "
                "notebook for session coverage', 'what's outside @scitex.session?', 'lint "
                "this notebook for reproducibility gaps', or before calling "
                "`notebook_verify` / `notebook_compile` on an unfamiliar notebook. Returns "
                "a list of offending cells with line numbers."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the .ipynb file",
                    },
                },
                "required": ["path"],
            },
        ),
        types.Tool(
            name="notebook_compile",
            description=(
                "Reconstruct a notebook's true cell-dependency DAG from Clew-recorded "
                "execution timestamps and emit it as a Mermaid diagram, a topologically-"
                "ordered standalone `.py` script, or raw JSON. Embodies 'do what you want, "
                "organize later' — cells can be executed in any order during exploration "
                "and still produce a clean linear script. Use whenever the user asks to "
                "'compile this notebook', 'show the execution DAG', 'visualize cell "
                "dependencies', 'linearize my notebook', 'export a script in dependency "
                "order', 'turn this Jupyter mess into a .py', or needs a reproducible "
                "script built from out-of-order cell runs."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the .ipynb file",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["mermaid", "script", "json"],
                        "default": "mermaid",
                    },
                },
                "required": ["path"],
            },
        ),
        types.Tool(
            name="notebook_convert",
            description=(
                "Convert a `.ipynb` to a SciTeX Python script with `@stx.session` "
                "decorators wrapping each (or merged) cell — gives you a production-ready "
                "`.py` that re-runs cleanly and records provenance. Drop-in replacement "
                "for `jupyter nbconvert --to script` plus the manual step of adding "
                "session decorators. Use whenever the user asks to 'convert this notebook "
                "to .py', 'export as Python script', 'make this reproducible as a script', "
                "or 'strip the notebook into scitex sessions'. Choose `mode='per_cell'` to "
                "keep each cell as its own session, or `mode='unified'` for one session "
                "around everything; `order='dag'` topologically sorts by dependency, "
                "`order='cell'` keeps notebook order."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "mode": {
                        "type": "string",
                        "enum": ["per_cell", "unified"],
                        "default": "per_cell",
                    },
                    "order": {
                        "type": "string",
                        "enum": ["cell", "dag"],
                        "default": "cell",
                    },
                    "output": {
                        "type": "string",
                        "description": "Optional output .py path",
                    },
                },
                "required": ["path"],
            },
        ),
    ]


# EOF
