#!/usr/bin/env python3
"""Smoke tests for scitex_notebook._mcp.handlers."""

from __future__ import annotations


def test_handlers_callable():
    from scitex_notebook._mcp import (
        check_handler,
        compile_handler,
        convert_handler,
        verify_handler,
    )

    for fn in (check_handler, compile_handler, convert_handler, verify_handler):
        assert callable(fn)


# EOF
