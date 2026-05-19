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
    def test_no_args_shows_help_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, [])
        # Act
        # Assert
        # Assert
        assert result.exit_code == 0

    def test_no_args_shows_help_verify_notebook_in_result_output(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, [])
        # Act
        # Assert
        # Assert
        assert "verify-notebook" in result.output

    def test_no_args_shows_help_compile_notebook_in_result_output(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, [])
        # Act
        # Assert
        # Assert
        assert "compile-notebook" in result.output

    def test_no_args_shows_help_convert_notebook_in_result_output(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, [])
        # Act
        # Assert
        # Assert
        assert "convert-notebook" in result.output

    def test_help_flag_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["--help"])
        # Act
        # Assert
        # Assert
        assert result.exit_code == 0

    def test_help_flag_scitex_notebook_in_result_output_lower_or_usage_in_result_ou(
        self, runner
    ):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["--help"])
        # Act
        # Assert
        # Assert
        assert "scitex-notebook" in result.output.lower() or "Usage:" in result.output

    def test_version_flag_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["--version"])
        # Act
        # Assert
        # Assert
        assert result.exit_code == 0

    def test_version_flag_scitex_notebook_in_result_output(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["--version"])
        # Act
        # Assert
        # Assert
        assert "scitex-notebook" in result.output

    def test_help_recursive_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["--help-recursive"])
        # Act
        # Assert
        # Assert
        assert result.exit_code == 0

    def test_help_recursive_mcp_in_result_output(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["--help-recursive"])
        # Act
        # Assert
        # Assert
        assert "mcp" in result.output

    def test_json_flag_propagates(self, runner):
        # The flag should at least parse cleanly even when no subcommand is given
        # Arrange
        # Act
        result = runner.invoke(cli, ["--json"])
        # Assert
        assert result.exit_code == 0


# --------------------------------------------------------------------------- #
# verify-notebook
# --------------------------------------------------------------------------- #


class TestVerifyNotebook:
    def test_help_shows_example_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["verify-notebook", "--help"])
        # Act
        # Assert
        # Assert
        assert result.exit_code == 0

    def test_help_shows_example_example_in_result_output(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["verify-notebook", "--help"])
        # Act
        # Assert
        # Assert
        assert "Example" in result.output

    def test_missing_argument_result_exit_code_0(self, runner):
        # Arrange
        # Act
        result = runner.invoke(cli, ["verify-notebook"])
        # Assert
        assert result.exit_code != 0

    def test_missing_file_result_exit_code_0(self, runner, tmp_path):
        # Arrange
        # Act
        result = runner.invoke(
            cli, ["verify-notebook", str(tmp_path / "does-not-exist.ipynb")]
        )
        # Assert
        assert result.exit_code != 0


# --------------------------------------------------------------------------- #
# check-notebook
# --------------------------------------------------------------------------- #


class TestCheckNotebook:
    def test_help_shows_example_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["check-notebook", "--help"])
        # Act
        # Assert
        # Assert
        assert result.exit_code == 0

    def test_help_shows_example_example_in_result_output(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["check-notebook", "--help"])
        # Act
        # Assert
        # Assert
        assert "Example" in result.output

    def test_empty_notebook_yields_no_issues_result_exit_code_equals_n_0(
        self, runner, empty_notebook
    ):
        # check_notebook on an empty notebook should report zero issues -> rc 0.
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["check-notebook", str(empty_notebook)])
        # Act
        # Assert
        # Assert
        assert result.exit_code == 0

    def test_empty_notebook_yields_no_issues_no_untracked_in_result_output_or_in_result_output_or_result_(
        self, runner, empty_notebook
    ):
        # check_notebook on an empty notebook should report zero issues -> rc 0.
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["check-notebook", str(empty_notebook)])
        # Act
        # Assert
        # Assert
        assert (
            "No untracked" in result.output
            or "[]" in result.output
            or result.output.strip() == ""
        )

    def test_json_flag_emits_json_result_exit_code_equals_n_0(
        self, runner, empty_notebook
    ):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["check-notebook", str(empty_notebook), "--json"])
        # Act
        # Assert
        # Assert
        assert result.exit_code == 0

    def test_json_flag_emits_json_result_output_lstrip_startswith(
        self, runner, empty_notebook
    ):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["check-notebook", str(empty_notebook), "--json"])
        # Act
        # Assert
        # Assert
        assert result.output.lstrip().startswith("[")


# --------------------------------------------------------------------------- #
# compile-notebook (mutating verb)
# --------------------------------------------------------------------------- #


class TestCompileNotebook:
    def test_help_shows_example_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["compile-notebook", "--help"])
        # Act
        # Assert
        # Assert
        assert result.exit_code == 0

    def test_help_shows_example_example_in_result_output(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["compile-notebook", "--help"])
        # Act
        # Assert
        # Assert
        assert "Example" in result.output

    def test_dry_run_result_exit_code_equals_n_0(self, runner, empty_notebook):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(
            cli, ["compile-notebook", str(empty_notebook), "--dry-run"]
        )
        # Act
        # Assert
        # Assert
        assert result.exit_code == 0

    def test_dry_run_dry_run_in_result_output(self, runner, empty_notebook):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(
            cli, ["compile-notebook", str(empty_notebook), "--dry-run"]
        )
        # Act
        # Assert
        # Assert
        assert "DRY RUN" in result.output


# --------------------------------------------------------------------------- #
# convert-notebook (mutating verb)
# --------------------------------------------------------------------------- #


class TestConvertNotebook:
    def test_help_shows_example_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["convert-notebook", "--help"])
        # Act
        # Assert
        # Assert
        assert result.exit_code == 0

    def test_help_shows_example_example_in_result_output(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["convert-notebook", "--help"])
        # Act
        # Assert
        # Assert
        assert "Example" in result.output

    def test_dry_run_result_exit_code_equals_n_0(self, runner, empty_notebook):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(
            cli, ["convert-notebook", str(empty_notebook), "--dry-run"]
        )
        # Act
        # Assert
        # Assert
        assert result.exit_code == 0

    def test_dry_run_dry_run_in_result_output(self, runner, empty_notebook):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(
            cli, ["convert-notebook", str(empty_notebook), "--dry-run"]
        )
        # Act
        # Assert
        # Assert
        assert "DRY RUN" in result.output


# --------------------------------------------------------------------------- #
# list-python-apis (introspection)
# --------------------------------------------------------------------------- #


class TestListPythonApis:
    def test_default_run_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["list-python-apis"])
        # Act
        # Assert
        # Assert
        assert result.exit_code == 0

    def test_default_run_scitex_notebook_in_result_output(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["list-python-apis"])
        # Act
        # Assert
        # Assert
        assert "scitex_notebook" in result.output

    def test_help_shows_example_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["list-python-apis", "--help"])
        # Act
        # Assert
        # Assert
        assert result.exit_code == 0

    def test_help_shows_example_example_in_result_output(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["list-python-apis", "--help"])
        # Act
        # Assert
        # Assert
        assert "Example" in result.output

    def test_json_flag_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["list-python-apis", "--json"])
        # Act
        # Assert
        # Assert
        assert result.exit_code == 0

    def test_json_flag_payload_module_scitex_notebook(self, runner):
        # Arrange
        result = runner.invoke(cli, ["list-python-apis", "--json"])
        # Act
        payload = json.loads(result.output) if result.exit_code == 0 else {}
        # Assert
        assert payload.get("module") == "scitex_notebook"

    def test_json_flag_isinstance_payload_apis_list(self, runner):
        # Arrange
        result = runner.invoke(cli, ["list-python-apis", "--json"])
        # Act
        payload = json.loads(result.output) if result.exit_code == 0 else {}
        # Assert
        assert isinstance(payload.get("apis"), list)


# --------------------------------------------------------------------------- #
# mcp group
# --------------------------------------------------------------------------- #


class TestMcpGroup:
    def test_no_args_shows_help_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["mcp"])
        # Act
        # Assert
        # Assert
        assert result.exit_code == 0

    def test_no_args_shows_help_start_in_result_output(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["mcp"])
        # Act
        # Assert
        # Assert
        assert "start" in result.output

    def test_no_args_shows_help_list_tools_in_result_output(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["mcp"])
        # Act
        # Assert
        # Assert
        assert "list-tools" in result.output

    def test_start_dry_run_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["mcp", "start", "--dry-run"])
        # Act
        # Assert
        # Assert
        assert result.exit_code == 0

    def test_start_dry_run_dry_run_in_result_output(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["mcp", "start", "--dry-run"])
        # Act
        # Assert
        # Assert
        assert "DRY RUN" in result.output

    def test_start_help_shows_example_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["mcp", "start", "--help"])
        # Act
        # Assert
        # Assert
        assert result.exit_code == 0

    def test_start_help_shows_example_example_in_result_output(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["mcp", "start", "--help"])
        # Act
        # Assert
        # Assert
        assert "Example" in result.output

    def test_list_tools_default_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["mcp", "list-tools"])
        # Act
        # Assert
        # Assert
        assert result.exit_code == 0

    def test_list_tools_default_notebook_in_result_output(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["mcp", "list-tools"])
        # Act
        # Assert
        # Assert
        assert "notebook" in result.output

    def test_list_tools_json_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["mcp", "list-tools", "--json"])
        # Act
        # Assert
        # Assert
        assert result.exit_code == 0

    def test_list_tools_json_isinstance_payload_get_tools_list(self, runner):
        # Arrange
        result = runner.invoke(cli, ["mcp", "list-tools", "--json"])
        # Act
        payload = json.loads(result.output) if result.exit_code == 0 else {}
        # Assert
        assert isinstance(payload.get("tools"), list)

    def test_list_tools_json_payload_get_total_len_payload_tools(self, runner):
        # Arrange
        result = runner.invoke(cli, ["mcp", "list-tools", "--json"])
        # Act
        payload = json.loads(result.output) if result.exit_code == 0 else {"tools": []}
        # Assert
        assert payload.get("total") == len(payload["tools"])

    def test_list_tools_help_shows_example_result_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["mcp", "list-tools", "--help"])
        # Act
        # Assert
        # Assert
        assert result.exit_code == 0

    def test_list_tools_help_shows_example_example_in_result_output(self, runner):
        # Arrange
        # Arrange
        # Act
        result = runner.invoke(cli, ["mcp", "list-tools", "--help"])
        # Act
        # Assert
        # Assert
        assert "Example" in result.output
