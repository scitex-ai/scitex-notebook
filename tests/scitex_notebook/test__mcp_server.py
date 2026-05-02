#!/usr/bin/env python3
# Timestamp: "2026-05-02 (ywatanabe)"
# File: tests/scitex_notebook/test__mcp_server.py

"""Tests for scitex_notebook._mcp_server — canonical FastMCP server.

Covers:
  - the FastMCP instance is built and named correctly,
  - all four notebook tools plus the skills pair are registered,
  - tool names follow the ``<pkg>_<verb>_<noun>`` convention,
  - each tool's docstring/description is non-trivial,
  - the skills tools resolve against the bundled ``_skills/`` tree.

The audit-mcp-tools auditor checks for ``_mcp_server.mcp`` at module
top, which is exactly what these tests also assume.
"""

from __future__ import annotations

import asyncio
import json

import pytest


@pytest.fixture(scope="module")
def server():
    from scitex_notebook._mcp_server import mcp

    return mcp


@pytest.fixture(scope="module")
def tools(server):
    return asyncio.run(server.list_tools())


# ---------------------------------------------------------------------------
# Server identity
# ---------------------------------------------------------------------------


class TestServerIdentity:
    def test_module_exposes_mcp_at_top_level(self):
        """``audit-mcp-tools`` looks for ``_mcp_server.mcp`` exactly."""
        from scitex_notebook import _mcp_server

        assert hasattr(_mcp_server, "mcp")

    def test_run_server_is_exported(self):
        from scitex_notebook._mcp_server import run_server

        assert callable(run_server)

    def test_server_name(self, server):
        assert server.name == "scitex-notebook"

    def test_server_instructions_non_trivial(self, server):
        # Required by the canonical convention so MCP clients have a
        # one-paragraph description of what the tools do.
        assert server.instructions
        assert len(server.instructions) > 40


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------


EXPECTED_TOOLS = {
    "notebook_verify",
    "notebook_check",
    "notebook_compile",
    "notebook_convert",
    "notebook_skills_list",
    "notebook_skills_get",
}


class TestToolRegistration:
    def test_expected_tools_registered(self, tools):
        names = {t.name for t in tools}
        assert EXPECTED_TOOLS.issubset(names), (
            f"missing tools: {EXPECTED_TOOLS - names}"
        )

    def test_no_unexpected_tools(self, tools):
        names = {t.name for t in tools}
        extras = names - EXPECTED_TOOLS
        assert extras == set(), f"unexpected tools: {extras}"

    def test_tool_count(self, tools):
        assert len(tools) == len(EXPECTED_TOOLS)

    @pytest.mark.parametrize("name", sorted(EXPECTED_TOOLS))
    def test_tool_naming_convention(self, name):
        # <pkg>_<verb>_<noun?> — first segment must be ``notebook``.
        head, _, _ = name.partition("_")
        assert head == "notebook"

    @pytest.mark.parametrize("name", sorted(EXPECTED_TOOLS))
    def test_tool_has_substantial_description(self, tools, name):
        t = next(t for t in tools if t.name == name)
        desc = (t.description or "").strip()
        # Meaningful descriptions, not a stub.
        assert len(desc) > 40, f"{name} description too short: {desc!r}"


# ---------------------------------------------------------------------------
# Skills tools — call them and inspect the JSON body
# ---------------------------------------------------------------------------


def _call_tool(server, tool_name, **kwargs):
    """Synchronously invoke an MCP tool and parse its JSON return body."""
    result = asyncio.run(server.call_tool(tool_name, kwargs))
    # FastMCP 3.x returns ToolResult; extract the structured payload.
    payload = getattr(result, "structured_content", None)
    if payload is None:
        # Fallback: TextContent body parsed as JSON.
        content = getattr(result, "content", None) or []
        text = "".join(getattr(c, "text", "") for c in content)
        payload = json.loads(text) if text else None
    if isinstance(payload, dict) and "result" in payload and len(payload) == 1:
        # Some FastMCP versions wrap the body under {"result": "<json>"}.
        inner = payload["result"]
        if isinstance(inner, str):
            try:
                payload = json.loads(inner)
            except json.JSONDecodeError:
                pass
    return payload


class TestSkillsTools:
    def test_skills_list_returns_dict(self, server):
        body = _call_tool(server, "notebook_skills_list")
        assert isinstance(body, dict)
        assert body.get("success") is True
        assert isinstance(body.get("count"), int)
        assert isinstance(body.get("skills"), list)

    def test_skills_list_finds_at_least_one_skill(self, server):
        body = _call_tool(server, "notebook_skills_list")
        # The package ships a non-empty _skills/ tree.
        assert body["count"] > 0

    def test_skills_get_unknown_returns_error_payload(self, server):
        body = _call_tool(server, "notebook_skills_get", name="does-not-exist")
        assert isinstance(body, dict)
        assert body.get("success") is False
        assert "not found" in body.get("error", "")


# EOF
