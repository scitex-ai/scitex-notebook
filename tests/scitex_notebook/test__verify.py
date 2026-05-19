#!/usr/bin/env python3
# Timestamp: "2026-05-19 (ywatanabe)"
# File: /home/ywatanabe/proj/scitex-notebook/tests/scitex_notebook/test__verify.py

"""Tests for scitex.notebook._verify module.

Covers:
  * ``check_notebook()`` — static analysis of notebook cells for untracked IO.
    Uses real notebook files written to ``tmp_path``.
  * ``verify_notebook()`` — clew-DB session verification. Tests inject
    hand-rolled fakes via the public ``db=`` and ``verify_run_fn=``
    parameters; no mock library is used.
  * ``_get_runs_for_notebook()`` — accepts a ``db`` arg directly, so tests
    pass a hand-rolled ``FakeClewDB`` with a canned ``list_runs`` payload.

Mock decisions:
  - Original tests used ``unittest.mock.MagicMock`` + ``patch`` on
    ``scitex_clew.get_db`` / ``scitex_clew.verify_run``. This was the
    classic patch-internals-on-import anti-pattern; the test was
    exercising the patch surface, not the production code.
  - Production code was refactored to accept the ``db`` handle and the
    ``verify_run`` callable as keyword arguments (dependency injection).
    Tests now pass concrete ``FakeClewDB`` / ``FakeVerification`` /
    ``FakeVerifyRun`` instances. These fakes record calls in
    ``calls.append(...)`` lists so we can assert *what* the code asked
    of its collaborators, not just the final return value.
  - No test was deleted — every behaviour the originals checked is
    still covered by an equivalent assertion against a real or
    hand-rolled fake collaborator.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

import pytest

from scitex_notebook._verify import (
    _get_runs_for_notebook,
    check_notebook,
    verify_notebook,
)

# ---------------------------------------------------------------------------
# Notebook builders
# ---------------------------------------------------------------------------


def _make_notebook(cells, tmp_path, name="nb.ipynb"):
    """Write a notebook JSON to tmp_path and return its Path."""
    nb = {
        "cells": cells,
        "metadata": {"kernelspec": {"name": "python3"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    nb_file = tmp_path / name
    nb_file.write_text(json.dumps(nb), encoding="utf-8")
    return nb_file


def _code_cell(source, cell_id):
    """Helper to build a code cell dict."""
    return {
        "cell_type": "code",
        "source": source,
        "metadata": {},
        "id": cell_id,
        "outputs": [],
    }


def _markdown_cell(source, cell_id):
    """Helper to build a markdown cell dict."""
    return {
        "cell_type": "markdown",
        "source": source,
        "metadata": {},
        "id": cell_id,
    }


# ---------------------------------------------------------------------------
# Hand-rolled fakes (replace MagicMock + patch)
# ---------------------------------------------------------------------------


@dataclass
class FakeClewDB:
    """Minimal stand-in for ``scitex_clew.VerificationDB``.

    Only the surface ``_get_runs_for_notebook`` and ``verify_notebook``
    actually exercise: a ``list_runs(limit=...)`` method that returns
    pre-seeded rows. Calls are recorded for assertion.
    """

    rows: List[Dict[str, Any]] = field(default_factory=list)
    calls: List[Dict[str, Any]] = field(default_factory=list)

    def list_runs(self, limit: int = 1_000) -> List[Dict[str, Any]]:
        self.calls.append({"method": "list_runs", "limit": limit})
        return list(self.rows)


@dataclass
class FakeStatus:
    """Stand-in for ``VerificationStatus`` enum value."""

    value: str


@dataclass
class FakeVerification:
    """Stand-in for ``RunVerification`` result object."""

    status: FakeStatus
    is_verified: bool


@dataclass
class FakeVerifyRun:
    """Callable stand-in for ``scitex_clew.verify_run``.

    Returns ``result`` on call; if ``exc`` is set, raises it instead.
    Records all call arguments for assertion.
    """

    result: Any = None
    exc: BaseException = None
    calls: List[str] = field(default_factory=list)

    def __call__(self, session_id: str):
        self.calls.append(session_id)
        if self.exc is not None:
            raise self.exc
        return self.result


# ---------------------------------------------------------------------------
# check_notebook() tests
# ---------------------------------------------------------------------------


def test_check_notebook_detects_untracked_load_call(tmp_path):
    """Cell with scitex.io.load() but no @stx.session should be flagged."""
    # Arrange
    nb_path = _make_notebook(
        [_code_cell("data = scitex.io.load('input.csv')", "c1")],
        tmp_path,
    )
    # Act
    issues = check_notebook(nb_path)
    # Assert
    assert (
        len(issues) == 1
        and issues[0]["has_load"] is True
        and issues[0]["has_session"] is False
    )


def test_check_notebook_detects_stx_alias_load_call(tmp_path):
    """Cell with stx.io.load() (alias) but no session decorator should be flagged."""
    # Arrange
    nb_path = _make_notebook(
        [_code_cell("result = stx.io.load('data.pkl')", "c1")],
        tmp_path,
    )
    # Act
    issues = check_notebook(nb_path)
    # Assert
    assert len(issues) == 1 and issues[0]["has_load"] is True


def test_check_notebook_detects_untracked_save_call(tmp_path):
    """Cell with scitex.io.save() but no @stx.session should be flagged."""
    # Arrange
    nb_path = _make_notebook(
        [_code_cell("scitex.io.save(result, 'output.pkl')", "c1")],
        tmp_path,
    )
    # Act
    issues = check_notebook(nb_path)
    # Assert
    assert (
        len(issues) == 1
        and issues[0]["has_save"] is True
        and issues[0]["has_session"] is False
    )


def test_check_notebook_detects_stx_alias_save_call(tmp_path):
    """Cell with stx.io.save() (alias) but no session decorator should be flagged."""
    # Arrange
    nb_path = _make_notebook(
        [_code_cell("stx.io.save(df, 'results.csv')", "c1")],
        tmp_path,
    )
    # Act
    issues = check_notebook(nb_path)
    # Assert
    assert len(issues) == 1 and issues[0]["has_save"] is True


def test_check_notebook_tracked_cell_not_flagged_as_issue(tmp_path):
    """Cell with IO and @stx.session should NOT appear in issues."""
    # Arrange
    source = (
        "@stx.session\n"
        "def run():\n"
        "    data = stx.io.load('input.csv')\n"
        "    stx.io.save(data, 'out.csv')\n"
    )
    nb_path = _make_notebook([_code_cell(source, "c1")], tmp_path)
    # Act
    issues = check_notebook(nb_path)
    # Assert
    assert issues == []


def test_check_notebook_scitex_session_decorator_accepted_as_tracking(tmp_path):
    """Cell with @scitex.session (long form) should NOT be flagged."""
    # Arrange
    source = "@scitex.session\ndef run():\n    data = scitex.io.load('f.pkl')\n"
    nb_path = _make_notebook([_code_cell(source, "c1")], tmp_path)
    # Act
    issues = check_notebook(nb_path)
    # Assert
    assert issues == []


def test_check_notebook_clean_notebook_returns_empty_issue_list(tmp_path):
    """Notebook with no IO calls should return an empty list."""
    # Arrange
    nb_path = _make_notebook(
        [
            _code_cell("x = 1 + 2", "c1"),
            _code_cell("print(x)", "c2"),
        ],
        tmp_path,
    )
    # Act
    issues = check_notebook(nb_path)
    # Assert
    assert issues == []


def test_check_notebook_markdown_cells_ignored_by_scan(tmp_path):
    """Markdown cells mentioning IO functions should not be flagged."""
    # Arrange
    nb_path = _make_notebook(
        [
            _markdown_cell("Use `stx.io.load('file')` to load data.", "md1"),
            _code_cell("x = 42", "c1"),
        ],
        tmp_path,
    )
    # Act
    issues = check_notebook(nb_path)
    # Assert
    assert issues == []


def test_check_notebook_cell_index_reported_in_issue(tmp_path):
    """Issues should report the correct cell index."""
    # Arrange
    nb_path = _make_notebook(
        [
            _code_cell("x = 1", "c0"),
            _code_cell("data = stx.io.load('f.csv')", "c1"),
        ],
        tmp_path,
    )
    # Act
    issues = check_notebook(nb_path)
    # Assert
    assert len(issues) == 1 and issues[0]["index"] == 1


def test_check_notebook_multiple_issues_all_reported(tmp_path):
    """Multiple cells with untracked IO should all appear in the result."""
    # Arrange
    nb_path = _make_notebook(
        [
            _code_cell("stx.io.load('a.csv')", "c0"),
            _code_cell("stx.io.save(x, 'b.csv')", "c1"),
            _code_cell("y = 99", "c2"),
        ],
        tmp_path,
    )
    # Act
    issues = check_notebook(nb_path)
    indices = sorted(iss["index"] for iss in issues)
    # Assert
    assert indices == [0, 1]


def test_check_notebook_issue_dict_has_required_keys(tmp_path):
    """Each issue dict must have index, has_load, has_save, has_session."""
    # Arrange
    nb_path = _make_notebook(
        [_code_cell("stx.io.load('f.pkl')", "c0")],
        tmp_path,
    )
    # Act
    issues = check_notebook(nb_path)
    # Assert
    assert len(issues) == 1 and set(issues[0]) >= {
        "index",
        "has_load",
        "has_save",
        "has_session",
    }


def test_check_notebook_cell_with_load_and_save_both_flagged_in_one_issue(tmp_path):
    """Cell with both load and save but no session should have both flags True."""
    # Arrange
    source = "data = stx.io.load('in.csv')\nstx.io.save(data, 'out.csv')"
    nb_path = _make_notebook([_code_cell(source, "c0")], tmp_path)
    # Act
    issues = check_notebook(nb_path)
    # Assert
    assert (
        len(issues) == 1
        and issues[0]["has_load"] is True
        and issues[0]["has_save"] is True
    )


# ---------------------------------------------------------------------------
# verify_notebook() with hand-rolled fake DB tests
# ---------------------------------------------------------------------------


def test_verify_notebook_no_sessions_returns_empty(tmp_path):
    """verify_notebook should return empty list when no matching sessions."""
    # Arrange
    nb_path = _make_notebook([_code_cell("x = 1", "c0")], tmp_path)
    db = FakeClewDB(rows=[])
    verify_fn = FakeVerifyRun()
    # Act
    results = verify_notebook(nb_path, db=db, verify_run_fn=verify_fn)
    # Assert
    assert results == []


def test_verify_notebook_no_sessions_skips_verify_call(tmp_path):
    """When the DB has no rows, verify_run must not be invoked at all."""
    # Arrange
    nb_path = _make_notebook([_code_cell("x = 1", "c0")], tmp_path)
    db = FakeClewDB(rows=[])
    verify_fn = FakeVerifyRun()
    # Act
    verify_notebook(nb_path, db=db, verify_run_fn=verify_fn)
    # Assert
    assert verify_fn.calls == []


def test_verify_notebook_with_verified_session_reports_one_result(tmp_path):
    """verify_notebook should report verified sessions."""
    # Arrange
    nb_path = _make_notebook([_code_cell("x = 1", "c0")], tmp_path)
    db = FakeClewDB(
        rows=[
            {
                "session_id": "s1",
                "started_at": "2026-01-01T00:00:00",
                "script_path": str(nb_path),
                "metadata": json.dumps({"notebook_path": str(nb_path.resolve())}),
            },
        ]
    )
    verify_fn = FakeVerifyRun(
        result=FakeVerification(status=FakeStatus("verified"), is_verified=True)
    )
    # Act
    results = verify_notebook(nb_path, db=db, verify_run_fn=verify_fn)
    # Assert
    assert len(results) == 1


def test_verify_notebook_with_verified_session_marks_is_verified_true(tmp_path):
    """verify_notebook should propagate is_verified=True from verifier."""
    # Arrange
    nb_path = _make_notebook([_code_cell("x = 1", "c0")], tmp_path)
    db = FakeClewDB(
        rows=[
            {
                "session_id": "s1",
                "started_at": "2026-01-01T00:00:00",
                "metadata": json.dumps({"notebook_path": str(nb_path.resolve())}),
            },
        ]
    )
    verify_fn = FakeVerifyRun(
        result=FakeVerification(status=FakeStatus("verified"), is_verified=True)
    )
    # Act
    results = verify_notebook(nb_path, db=db, verify_run_fn=verify_fn)
    # Assert
    assert results[0]["is_verified"] is True


def test_verify_notebook_passes_session_id_to_verify_run(tmp_path):
    """The session_id from the DB row must be forwarded to verify_run."""
    # Arrange
    nb_path = _make_notebook([_code_cell("x = 1", "c0")], tmp_path)
    db = FakeClewDB(
        rows=[
            {
                "session_id": "s1",
                "started_at": "2026-01-01T00:00:00",
                "metadata": json.dumps({"notebook_path": str(nb_path.resolve())}),
            },
        ]
    )
    verify_fn = FakeVerifyRun(
        result=FakeVerification(status=FakeStatus("verified"), is_verified=True)
    )
    # Act
    verify_notebook(nb_path, db=db, verify_run_fn=verify_fn)
    # Assert
    assert verify_fn.calls == ["s1"]


def test_verify_notebook_propagates_session_id_in_result(tmp_path):
    """Returned dict must echo the session_id from the run row."""
    # Arrange
    nb_path = _make_notebook([_code_cell("x = 1", "c0")], tmp_path)
    db = FakeClewDB(
        rows=[
            {
                "session_id": "s1",
                "started_at": "2026-01-01T00:00:00",
                "metadata": json.dumps({"notebook_path": str(nb_path.resolve())}),
            },
        ]
    )
    verify_fn = FakeVerifyRun(
        result=FakeVerification(status=FakeStatus("verified"), is_verified=True)
    )
    # Act
    results = verify_notebook(nb_path, db=db, verify_run_fn=verify_fn)
    # Assert
    assert results[0]["session_id"] == "s1"


def test_verify_notebook_with_failed_session_reports_one_result(tmp_path):
    """verify_notebook should report failed sessions as a single result row."""
    # Arrange
    nb_path = _make_notebook([_code_cell("x = 1", "c0")], tmp_path)
    db = FakeClewDB(
        rows=[
            {
                "session_id": "s1",
                "started_at": "2026-01-01T00:00:00",
                "metadata": json.dumps({"notebook_path": str(nb_path.resolve())}),
            },
        ]
    )
    verify_fn = FakeVerifyRun(
        result=FakeVerification(status=FakeStatus("mismatch"), is_verified=False)
    )
    # Act
    results = verify_notebook(nb_path, db=db, verify_run_fn=verify_fn)
    # Assert
    assert len(results) == 1


def test_verify_notebook_with_failed_session_marks_is_verified_false(tmp_path):
    """A mismatch verification should yield is_verified=False in the result."""
    # Arrange
    nb_path = _make_notebook([_code_cell("x = 1", "c0")], tmp_path)
    db = FakeClewDB(
        rows=[
            {
                "session_id": "s1",
                "started_at": "2026-01-01T00:00:00",
                "metadata": json.dumps({"notebook_path": str(nb_path.resolve())}),
            },
        ]
    )
    verify_fn = FakeVerifyRun(
        result=FakeVerification(status=FakeStatus("mismatch"), is_verified=False)
    )
    # Act
    results = verify_notebook(nb_path, db=db, verify_run_fn=verify_fn)
    # Assert
    assert results[0]["is_verified"] is False


def test_verify_notebook_handles_verifier_exception_with_error_status(tmp_path):
    """verify_notebook should catch verification errors with status=error."""
    # Arrange
    nb_path = _make_notebook([_code_cell("x = 1", "c0")], tmp_path)
    db = FakeClewDB(
        rows=[
            {
                "session_id": "s1",
                "started_at": "2026-01-01T00:00:00",
                "metadata": json.dumps({"notebook_path": str(nb_path.resolve())}),
            },
        ]
    )
    verify_fn = FakeVerifyRun(exc=RuntimeError("DB error"))
    # Act
    results = verify_notebook(nb_path, db=db, verify_run_fn=verify_fn)
    # Assert
    assert results[0]["status"] == "error"


def test_verify_notebook_handles_verifier_exception_with_is_verified_false(tmp_path):
    """Errors must mark the run as not verified."""
    # Arrange
    nb_path = _make_notebook([_code_cell("x = 1", "c0")], tmp_path)
    db = FakeClewDB(
        rows=[
            {
                "session_id": "s1",
                "started_at": "2026-01-01T00:00:00",
                "metadata": json.dumps({"notebook_path": str(nb_path.resolve())}),
            },
        ]
    )
    verify_fn = FakeVerifyRun(exc=RuntimeError("DB error"))
    # Act
    results = verify_notebook(nb_path, db=db, verify_run_fn=verify_fn)
    # Assert
    assert results[0]["is_verified"] is False


# ---------------------------------------------------------------------------
# _get_runs_for_notebook() tests
# ---------------------------------------------------------------------------


def test_get_runs_for_notebook_matches_run_via_metadata_notebook_path(tmp_path):
    """_get_runs_for_notebook should match runs via metadata.notebook_path."""
    # Arrange
    nb_path = tmp_path / "nb.ipynb"
    nb_path.write_text("{}", encoding="utf-8")
    runs = [
        {
            "session_id": "s1",
            "started_at": "2026-01-01T00:00:00",
            "metadata": json.dumps({"notebook_path": str(nb_path.resolve())}),
        },
        {
            "session_id": "s2",
            "started_at": "2026-01-02T00:00:00",
            "metadata": json.dumps({"notebook_path": "/other/nb.ipynb"}),
        },
    ]
    db = FakeClewDB(rows=runs)
    # Act
    result = _get_runs_for_notebook(db, str(nb_path.resolve()))
    # Assert
    assert [r["session_id"] for r in result] == ["s1"]


def test_get_runs_for_notebook_empty_metadata_with_non_ipynb_script_skipped():
    """Runs with no metadata and a non-ipynb script_path should be skipped."""
    # Arrange
    runs = [
        {
            "session_id": "s1",
            "started_at": "2026-01-01T00:00:00",
            "script_path": "/some/script.py",
        },
    ]
    db = FakeClewDB(rows=runs)
    # Act
    result = _get_runs_for_notebook(db, "/target/nb.ipynb")
    # Assert
    assert result == []


def test_get_runs_for_notebook_calls_list_runs_on_db():
    """The function must query the injected DB via list_runs."""
    # Arrange
    db = FakeClewDB(rows=[])
    # Act
    _get_runs_for_notebook(db, "/target/nb.ipynb")
    # Assert
    assert db.calls and db.calls[0]["method"] == "list_runs"


# EOF
