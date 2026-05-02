#!/usr/bin/env python3
# Timestamp: "2026-05-02 (ywatanabe)"
# File: tests/scitex_notebook/test__magic.py

"""Tests for scitex_notebook._magic — IPython extension for notebook tracking.

Covers the three reproducibility-risk detectors plus the IPython extension
entry points. Uses a hand-rolled fake IPython shell — we don't import the
real IPython at test time so the tests run on every CI matrix without
adding a heavy dependency. The fake shell exposes only the surface
``ScitexNotebookMagics`` actually touches: ``events`` (with register /
unregister), ``user_ns``, and ``history_manager.session_number``.
"""

from __future__ import annotations

import importlib

import pytest

from scitex_notebook._magic import (
    _AMBIENT_NAMES,
    ScitexNotebookMagics,
    _ast_loads_and_stores,
    load_ipython_extension,
    unload_ipython_extension,
)

# ---------------------------------------------------------------------------
# Fake IPython shell
# ---------------------------------------------------------------------------


class _FakeEvents:
    def __init__(self):
        self.handlers: dict[str, list] = {}

    def register(self, name, fn):
        self.handlers.setdefault(name, []).append(fn)

    def unregister(self, name, fn):
        if name in self.handlers and fn in self.handlers[name]:
            self.handlers[name].remove(fn)


class _FakeHistoryManager:
    def __init__(self, session_number=42):
        self.session_number = session_number


class _FakeShell:
    """Minimum IPython surface ``ScitexNotebookMagics`` consumes."""

    def __init__(self):
        self.events = _FakeEvents()
        self.user_ns: dict = {}
        self.history_manager = _FakeHistoryManager()


class _FakePreInfo:
    def __init__(self, src):
        self.raw_cell = src


class _FakePostResult:
    def __init__(self, error=None, execution_count=None):
        self.error_in_exec = error
        self.execution_count = execution_count


@pytest.fixture(autouse=True)
def _reset_module_global():
    """``_INSTALLED`` is module-global; reset between tests."""
    import scitex_notebook._magic as m

    m._INSTALLED = None
    yield
    m._INSTALLED = None


@pytest.fixture
def shell():
    return _FakeShell()


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------


class TestAstLoadsAndStores:
    def test_simple_assignment(self):
        loads, stores = _ast_loads_and_stores("x = 1")
        assert stores == {"x"}
        assert loads == set()

    def test_load_then_store(self):
        loads, stores = _ast_loads_and_stores("y = x + 1")
        assert stores == {"y"}
        assert loads == {"x"}

    def test_function_def_creates_store(self):
        loads, stores = _ast_loads_and_stores("def foo():\n    return 1")
        assert "foo" in stores

    def test_class_def_creates_store(self):
        _, stores = _ast_loads_and_stores("class Foo:\n    pass")
        assert "Foo" in stores

    def test_import_creates_store(self):
        _, stores = _ast_loads_and_stores("import numpy")
        assert "numpy" in stores

    def test_import_as_uses_alias(self):
        _, stores = _ast_loads_and_stores("import numpy as np")
        assert "np" in stores
        assert "numpy" not in stores

    def test_from_import(self):
        _, stores = _ast_loads_and_stores("from scitex import io")
        assert "io" in stores

    def test_builtins_filtered_out(self):
        loads, _ = _ast_loads_and_stores("print(len([1, 2]))")
        # ``print`` and ``len`` are builtins and must not show up as loads.
        assert "print" not in loads
        assert "len" not in loads

    def test_syntax_error_returns_empty(self):
        # IPython line-magics like ``%timeit`` would trip ast.parse;
        # we want a graceful empty return, not an exception.
        loads, stores = _ast_loads_and_stores("%timeit 1+1")
        assert loads == set()
        assert stores == set()

    def test_ambient_names_include_print(self):
        assert "print" in _AMBIENT_NAMES


# ---------------------------------------------------------------------------
# Hidden-state-leak detection
# ---------------------------------------------------------------------------


class TestHiddenStateLeak:
    def test_clean_run_no_warnings(self, shell):
        m = ScitexNotebookMagics(shell)
        m._pre_run_cell(_FakePreInfo("x = 1"))
        m._post_run_cell(_FakePostResult())
        m._pre_run_cell(_FakePreInfo("y = x + 1"))
        m._post_run_cell(_FakePostResult())
        kinds = {w["kind"] for w in m.warnings}
        assert "hidden_state_leak" not in kinds

    def test_leak_when_name_undefined(self, shell):
        m = ScitexNotebookMagics(shell)
        m._pre_run_cell(_FakePreInfo("y = x + 1"))  # x never defined
        m._post_run_cell(_FakePostResult())
        leaks = [w for w in m.warnings if w["kind"] == "hidden_state_leak"]
        assert len(leaks) == 1
        assert leaks[0]["name"] == "x"

    def test_failed_cell_does_not_register_stores(self, shell):
        """A cell that raises should not declare its stores satisfied."""
        m = ScitexNotebookMagics(shell)
        # Cell 1 attempts to define ``x`` but fails.
        m._pre_run_cell(_FakePreInfo("x = 1/0"))
        m._post_run_cell(_FakePostResult(error=ZeroDivisionError("nope")))
        # Cell 2 reads ``x`` — should be flagged as a leak because cell 1
        # never actually completed the assignment.
        m._pre_run_cell(_FakePreInfo("print(x)"))
        m._post_run_cell(_FakePostResult())
        leaks = [w for w in m.warnings if w["kind"] == "hidden_state_leak"]
        names = [w["name"] for w in leaks]
        assert "x" in names


# ---------------------------------------------------------------------------
# Out-of-order execution detection
# ---------------------------------------------------------------------------


class TestOutOfOrder:
    def test_linear_run_no_warning(self, shell):
        m = ScitexNotebookMagics(shell)
        m._pre_run_cell(_FakePreInfo("x = 1"))
        m._post_run_cell(_FakePostResult(execution_count=1))
        m._pre_run_cell(_FakePreInfo("y = 2"))
        m._post_run_cell(_FakePostResult(execution_count=2))
        kinds = {w["kind"] for w in m.warnings}
        assert "out_of_order_execution" not in kinds

    def test_skipped_count_warns(self, shell):
        m = ScitexNotebookMagics(shell)
        m._pre_run_cell(_FakePreInfo("x = 1"))
        # User re-ran an earlier cell so global counter is 7, but our local
        # is 1 — that mismatch is precisely what we want to catch.
        m._post_run_cell(_FakePostResult(execution_count=7))
        ooo = [w for w in m.warnings if w["kind"] == "out_of_order_execution"]
        assert len(ooo) == 1
        assert ooo[0]["execution_count"] == 7

    def test_execution_count_none_does_not_warn(self, shell):
        """Some IPython versions/results don't expose execution_count;
        absence must not create a false-positive warning."""
        m = ScitexNotebookMagics(shell)
        m._pre_run_cell(_FakePreInfo("x = 1"))
        m._post_run_cell(_FakePostResult(execution_count=None))
        ooo = [w for w in m.warnings if w["kind"] == "out_of_order_execution"]
        assert ooo == []


# ---------------------------------------------------------------------------
# Data-dependency parent edge
# ---------------------------------------------------------------------------


class TestDependencyEdge:
    def test_no_dep_means_independent_cell(self, shell):
        m = ScitexNotebookMagics(shell)
        m._pre_run_cell(_FakePreInfo("x = 1"))
        m._post_run_cell(_FakePostResult())
        # First cell has no parent — the metadata must record an empty list.
        # The tracker is tracker_module-level state; we inspect via the
        # internal `_cell_dep_parents` snapshot kept on the magic.
        # Reset for a second, dependent cell.
        m._pre_run_cell(_FakePreInfo("y = x + 1"))
        # Before _post fires the parent edges are already computed in pre.
        assert len(m._cell_dep_parents) == 1
        m._post_run_cell(_FakePostResult())

    def test_redefining_name_shifts_parent(self, shell):
        m = ScitexNotebookMagics(shell)
        m._pre_run_cell(_FakePreInfo("x = 1"))
        m._post_run_cell(_FakePostResult())
        m._pre_run_cell(_FakePreInfo("x = 2"))  # redefine x
        m._post_run_cell(_FakePostResult())
        m._pre_run_cell(_FakePreInfo("y = x"))
        # Parent should be the most-recent definer (cell 2), not cell 1.
        assert len(m._cell_dep_parents) == 1
        # The session-id encodes the cell number in its suffix.
        assert m._cell_dep_parents[0].endswith("cell-0002")
        m._post_run_cell(_FakePostResult())


# ---------------------------------------------------------------------------
# warnings_summary()
# ---------------------------------------------------------------------------


def test_warnings_summary_aggregates_kinds(shell):
    m = ScitexNotebookMagics(shell)
    m._pre_run_cell(_FakePreInfo("y = x + 1"))  # leak
    m._post_run_cell(_FakePostResult(execution_count=99))  # OOE
    summary = m.warnings_summary()
    assert summary["n_cells_executed"] == 1
    assert summary["n_warnings"] == 2
    assert summary["by_kind"]["hidden_state_leak"] == 1
    assert summary["by_kind"]["out_of_order_execution"] == 1


# ---------------------------------------------------------------------------
# IPython extension entry points
# ---------------------------------------------------------------------------


class TestExtensionEntryPoints:
    def test_load_registers_handlers(self, shell):
        load_ipython_extension(shell)
        assert "pre_run_cell" in shell.events.handlers
        assert "post_run_cell" in shell.events.handlers
        assert len(shell.events.handlers["pre_run_cell"]) == 1
        assert "_scitex_nb_magic" in shell.user_ns

    def test_load_is_idempotent(self, shell):
        load_ipython_extension(shell)
        load_ipython_extension(shell)
        # No double-registration.
        assert len(shell.events.handlers["pre_run_cell"]) == 1

    def test_unload_unregisters_and_clears(self, shell):
        load_ipython_extension(shell)
        unload_ipython_extension(shell)
        assert shell.events.handlers["pre_run_cell"] == []
        assert "_scitex_nb_magic" not in shell.user_ns

    def test_unload_without_prior_load_is_noop(self, shell):
        # Must not raise.
        unload_ipython_extension(shell)


# ---------------------------------------------------------------------------
# Importable in a clean process
# ---------------------------------------------------------------------------


def test_module_imports_cleanly():
    """A bare ``import scitex_notebook._magic`` must not error.

    Catches accidentally-required heavy deps at import time.
    """
    importlib.import_module("scitex_notebook._magic")


def test_load_ipython_extension_exported_at_package_root():
    import scitex_notebook

    assert hasattr(scitex_notebook, "load_ipython_extension")
    assert hasattr(scitex_notebook, "unload_ipython_extension")


# EOF
