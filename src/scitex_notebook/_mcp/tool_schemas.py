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
                "Verify all clew sessions associated with a Jupyter notebook. "
                "Returns per-session verification status from the Clew DB."
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
                "Find cells with scitex.io calls that are not wrapped in "
                "@scitex.session (untracked IO)."
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
                "Compile a notebook's execution history into a DAG using "
                "timestamps from the Clew DB. Returns Mermaid, script, or JSON."
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
                "Convert a .ipynb notebook to a SciTeX Python script with "
                "@stx.session decorators."
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
