#!/usr/bin/env python3
"""Smoke tests for scitex_notebook._mcp.tool_schemas."""

from __future__ import annotations

import pytest


def test_get_tool_schemas_returns_nonempty():
    pytest.importorskip("mcp")
    from scitex_notebook._mcp.tool_schemas import get_tool_schemas

    schemas = get_tool_schemas()
    assert isinstance(schemas, list)
    assert len(schemas) > 0
    names = {getattr(t, "name", None) for t in schemas}
    # Each handler in __init__ should have a corresponding tool.
    assert any(n and n.startswith("notebook_") for n in names)


# EOF
