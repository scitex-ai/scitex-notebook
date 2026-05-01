#!/usr/bin/env python3
"""Tests for the scitex_notebook._cli._main module.

Covers the Click command tree added in commit 0d46a93 — root group, leaf
commands (verify-notebook / check-notebook / compile-notebook /
convert-notebook), introspection (list-python-apis), and the mcp group
(start / list-tools). All tests use Click's CliRunner so they exercise the
decorators + flag parsing without doing real I/O.
"""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from scitex_notebook._cli._main import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def empty_notebook(tmp_path):
    nb = tmp_path / "empty.ipynb"
    nb.write_text(
        json.dumps(
            {
                "cells": [],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
    )
    return nb


# --------------------------------------------------------------------------- #
# Root group
# --------------------------------------------------------------------------- #


class TestRootGroup:
    def test_no_args_shows_help(self, runner):
        result = runner.invoke(cli, [])
        assert result.exit_code == 0
        assert "verify-notebook" in result.output
        assert "compile-notebook" in result.output
        assert "convert-notebook" in result.output

    def test_help_flag(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "scitex-notebook" in result.output.lower() or "Usage:" in result.output

    def test_version_flag(self, runner):
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "scitex-notebook" in result.output

    def test_help_recursive(self, runner):
        result = runner.invoke(cli, ["--help-recursive"])
        assert result.exit_code == 0
        # Should descend into mcp subgroup commands
        assert "mcp" in result.output

    def test_json_flag_propagates(self, runner):
        # The flag should at least parse cleanly even when no subcommand is given
        result = runner.invoke(cli, ["--json"])
        assert result.exit_code == 0


# --------------------------------------------------------------------------- #
# verify-notebook
# --------------------------------------------------------------------------- #


class TestVerifyNotebook:
    def test_help_shows_example(self, runner):
        result = runner.invoke(cli, ["verify-notebook", "--help"])
        assert result.exit_code == 0
        assert "Example" in result.output

    def test_missing_argument(self, runner):
        result = runner.invoke(cli, ["verify-notebook"])
        assert result.exit_code != 0

    def test_missing_file(self, runner, tmp_path):
        result = runner.invoke(
            cli, ["verify-notebook", str(tmp_path / "does-not-exist.ipynb")]
        )
        assert result.exit_code != 0


# --------------------------------------------------------------------------- #
# check-notebook
# --------------------------------------------------------------------------- #


class TestCheckNotebook:
    def test_help_shows_example(self, runner):
        result = runner.invoke(cli, ["check-notebook", "--help"])
        assert result.exit_code == 0
        assert "Example" in result.output

    def test_empty_notebook_yields_no_issues(self, runner, empty_notebook):
        # check_notebook on an empty notebook should report zero issues -> rc 0.
        result = runner.invoke(cli, ["check-notebook", str(empty_notebook)])
        assert result.exit_code == 0
        assert (
            "No untracked" in result.output
            or "[]" in result.output
            or result.output.strip() == ""
        )

    def test_json_flag_emits_json(self, runner, empty_notebook):
        result = runner.invoke(cli, ["check-notebook", str(empty_notebook), "--json"])
        assert result.exit_code == 0
        # JSON list (possibly empty)
        assert result.output.lstrip().startswith("[")


# --------------------------------------------------------------------------- #
# compile-notebook (mutating verb)
# --------------------------------------------------------------------------- #


class TestCompileNotebook:
    def test_help_shows_example(self, runner):
        result = runner.invoke(cli, ["compile-notebook", "--help"])
        assert result.exit_code == 0
        assert "Example" in result.output

    def test_dry_run(self, runner, empty_notebook):
        result = runner.invoke(
            cli, ["compile-notebook", str(empty_notebook), "--dry-run"]
        )
        assert result.exit_code == 0
        assert "DRY RUN" in result.output


# --------------------------------------------------------------------------- #
# convert-notebook (mutating verb)
# --------------------------------------------------------------------------- #


class TestConvertNotebook:
    def test_help_shows_example(self, runner):
        result = runner.invoke(cli, ["convert-notebook", "--help"])
        assert result.exit_code == 0
        assert "Example" in result.output

    def test_dry_run(self, runner, empty_notebook):
        result = runner.invoke(
            cli, ["convert-notebook", str(empty_notebook), "--dry-run"]
        )
        assert result.exit_code == 0
        assert "DRY RUN" in result.output


# --------------------------------------------------------------------------- #
# list-python-apis (introspection)
# --------------------------------------------------------------------------- #


class TestListPythonApis:
    def test_default_run(self, runner):
        result = runner.invoke(cli, ["list-python-apis"])
        assert result.exit_code == 0
        # Must list at least one public API
        assert "scitex_notebook" in result.output

    def test_help_shows_example(self, runner):
        result = runner.invoke(cli, ["list-python-apis", "--help"])
        assert result.exit_code == 0
        assert "Example" in result.output

    def test_json_flag(self, runner):
        result = runner.invoke(cli, ["list-python-apis", "--json"])
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["module"] == "scitex_notebook"
        assert isinstance(payload["apis"], list)


# --------------------------------------------------------------------------- #
# mcp group
# --------------------------------------------------------------------------- #


class TestMcpGroup:
    def test_no_args_shows_help(self, runner):
        result = runner.invoke(cli, ["mcp"])
        assert result.exit_code == 0
        assert "start" in result.output
        assert "list-tools" in result.output

    def test_start_dry_run(self, runner):
        result = runner.invoke(cli, ["mcp", "start", "--dry-run"])
        assert result.exit_code == 0
        assert "DRY RUN" in result.output

    def test_start_help_shows_example(self, runner):
        result = runner.invoke(cli, ["mcp", "start", "--help"])
        assert result.exit_code == 0
        assert "Example" in result.output

    def test_list_tools_default(self, runner):
        result = runner.invoke(cli, ["mcp", "list-tools"])
        assert result.exit_code == 0
        # Should mention at least one of the registered tools
        assert "notebook" in result.output

    def test_list_tools_json(self, runner):
        result = runner.invoke(cli, ["mcp", "list-tools", "--json"])
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert isinstance(payload.get("tools"), list)
        assert payload.get("total") == len(payload["tools"])

    def test_list_tools_help_shows_example(self, runner):
        result = runner.invoke(cli, ["mcp", "list-tools", "--help"])
        assert result.exit_code == 0
        assert "Example" in result.output
