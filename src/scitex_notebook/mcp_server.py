#!/usr/bin/env python3
"""MCP Server for SciTeX Notebook.

Usage:
    python -m scitex_notebook.mcp_server
"""

from __future__ import annotations

import asyncio
import sys

from . import __version__

try:
    from mcp.server import NotificationOptions, Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

__all__ = ["NotebookServer", "main", "MCP_AVAILABLE"]


class NotebookServer:
    """MCP Server for notebook verification, compilation, conversion."""

    def __init__(self):
        self.server = Server("scitex-notebook")
        self.setup_handlers()

    def setup_handlers(self):
        from ._mcp.handlers import (
            check_handler,
            compile_handler,
            convert_handler,
            verify_handler,
        )
        from ._mcp.tool_schemas import get_tool_schemas

        @self.server.list_tools()
        async def handle_list_tools():
            return get_tool_schemas()

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict):
            if name == "notebook_verify":
                return await verify_handler(**arguments)
            if name == "notebook_check":
                return await check_handler(**arguments)
            if name == "notebook_compile":
                return await compile_handler(**arguments)
            if name == "notebook_convert":
                return await convert_handler(**arguments)
            raise ValueError(f"Unknown tool: {name}")


async def _run_server():
    server = NotebookServer()
    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="scitex-notebook",
                server_version=__version__,
                capabilities=server.server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


def main():
    if not MCP_AVAILABLE:
        print(
            "MCP server for scitex-notebook requires the 'mcp' package.\n"
            "Install with: pip install scitex-notebook[mcp]",
            file=sys.stderr,
        )
        sys.exit(1)
    asyncio.run(_run_server())


if __name__ == "__main__":
    main()

# EOF
