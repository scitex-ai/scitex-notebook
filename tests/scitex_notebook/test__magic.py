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
    def test_simple_assignment_stores_equals_x(self):
        # Arrange
        # Arrange
        # Act
        loads, stores = _ast_loads_and_stores("x = 1")
        # Act
        # Assert
        # Assert
        assert stores == {"x"}

    def test_simple_assignment_loads_equals_set(self):
        # Arrange
        # Arrange
        # Act
        loads, stores = _ast_loads_and_stores("x = 1")
        # Act
        # Assert
        # Assert
        assert loads == set()

    def test_load_then_store_stores_equals_y(self):
        # Arrange
        # Arrange
        # Act
        loads, stores = _ast_loads_and_stores("y = x + 1")
        # Act
        # Assert
        # Assert
        assert stores == {"y"}

    def test_load_then_store_loads_equals_x(self):
        # Arrange
        # Arrange
        # Act
        loads, stores = _ast_loads_and_stores("y = x + 1")
        # Act
        # Assert
        # Assert
        assert loads == {"x"}

    def test_function_def_creates_store(self):
        # Arrange
        # Act
        loads, stores = _ast_loads_and_stores("def foo():\n    return 1")
        # Assert
        assert "foo" in stores

    def test_class_def_creates_store(self):
        # Arrange
        # Act
        _, stores = _ast_loads_and_stores("class Foo:\n    pass")
        # Assert
        assert "Foo" in stores

    def test_import_creates_store(self):
        # Arrange
        # Act
        _, stores = _ast_loads_and_stores("import numpy")
        # Assert
        assert "numpy" in stores

    def test_import_as_uses_alias_np_in_stores(self):
        # Arrange
        # Arrange
        # Act
        _, stores = _ast_loads_and_stores("import numpy as np")
        # Act
        # Assert
        # Assert
        assert "np" in stores

    def test_import_as_uses_alias_numpy_not_in_stores(self):
        # Arrange
        # Arrange
        # Act
        _, stores = _ast_loads_and_stores("import numpy as np")
        # Act
        # Assert
        # Assert
        assert "numpy" not in stores

    def test_from_import_io_in_stores(self):
        # Arrange
        # Act
        _, stores = _ast_loads_and_stores("from scitex import io")
        # Assert
        assert "io" in stores

    def test_builtins_filtered_out_print_not_in_loads(self):
        # Arrange
        # Arrange
        # Act
        loads, _ = _ast_loads_and_stores("print(len([1, 2]))")
        # Act
        # Assert
        # Assert
        assert "print" not in loads

    def test_builtins_filtered_out_len_not_in_loads(self):
        # Arrange
        # Arrange
        # Act
        loads, _ = _ast_loads_and_stores("print(len([1, 2]))")
        # Act
        # Assert
        # Assert
        assert "len" not in loads

    def test_syntax_error_returns_empty_loads_equals_set(self):
        # IPython line-magics like ``%timeit`` would trip ast.parse;
        # we want a graceful empty return, not an exception.
        # Arrange
        # Arrange
        # Act
        loads, stores = _ast_loads_and_stores("%timeit 1+1")
        # Act
        # Assert
        # Assert
        assert loads == set()

    def test_syntax_error_returns_empty_stores_equals_set(self):
        # IPython line-magics like ``%timeit`` would trip ast.parse;
        # we want a graceful empty return, not an exception.
        # Arrange
        # Arrange
        # Act
        loads, stores = _ast_loads_and_stores("%timeit 1+1")
        # Act
        # Assert
        # Assert
        assert stores == set()

    def test_ambient_names_include_print(self):
        # Arrange
        # Act
        # Assert
        assert "print" in _AMBIENT_NAMES


# ---------------------------------------------------------------------------
# Hidden-state-leak detection
# ---------------------------------------------------------------------------


class TestHiddenStateLeak:
    def test_clean_run_no_warnings(self, shell):
        # Arrange
        m = ScitexNotebookMagics(shell)
        m._pre_run_cell(_FakePreInfo("x = 1"))
        m._post_run_cell(_FakePostResult())
        m._pre_run_cell(_FakePreInfo("y = x + 1"))
        m._post_run_cell(_FakePostResult())
        # Act
        kinds = {w["kind"] for w in m.warnings}
        # Assert
        assert "hidden_state_leak" not in kinds

    def test_leak_when_name_undefined_len_leaks_is_1(self, shell):
        # Arrange
        # Arrange
        m = ScitexNotebookMagics(shell)
        m._pre_run_cell(_FakePreInfo("y = x + 1"))  # x never defined
        m._post_run_cell(_FakePostResult())
        # Act
        leaks = [w for w in m.warnings if w["kind"] == "hidden_state_leak"]
        # Act
        # Assert
        # Assert
        assert len(leaks) == 1

    def test_leak_when_name_undefined_leaks_0_name_x(self, shell):
        # Arrange
        # Arrange
        m = ScitexNotebookMagics(shell)
        m._pre_run_cell(_FakePreInfo("y = x + 1"))  # x never defined
        m._post_run_cell(_FakePostResult())
        # Act
        leaks = [w for w in m.warnings if w["kind"] == "hidden_state_leak"]
        # Act
        # Assert
        # Assert
        assert leaks[0]["name"] == "x"

    def test_failed_cell_does_not_register_stores(self, shell):
        """A cell that raises should not declare its stores satisfied."""
        # Arrange
        m = ScitexNotebookMagics(shell)
        # Cell 1 attempts to define ``x`` but fails.
        m._pre_run_cell(_FakePreInfo("x = 1/0"))
        m._post_run_cell(_FakePostResult(error=ZeroDivisionError("nope")))
        # Cell 2 reads ``x`` — should be flagged as a leak because cell 1
        # never actually completed the assignment.
        m._pre_run_cell(_FakePreInfo("print(x)"))
        m._post_run_cell(_FakePostResult())
        leaks = [w for w in m.warnings if w["kind"] == "hidden_state_leak"]
        # Act
        names = [w["name"] for w in leaks]
        # Assert
        assert "x" in names


# ---------------------------------------------------------------------------
# Out-of-order execution detection
# ---------------------------------------------------------------------------


class TestOutOfOrder:
    def test_linear_run_no_warning(self, shell):
        # Arrange
        m = ScitexNotebookMagics(shell)
        m._pre_run_cell(_FakePreInfo("x = 1"))
        m._post_run_cell(_FakePostResult(execution_count=1))
        m._pre_run_cell(_FakePreInfo("y = 2"))
        m._post_run_cell(_FakePostResult(execution_count=2))
        # Act
        kinds = {w["kind"] for w in m.warnings}
        # Assert
        assert "out_of_order_execution" not in kinds

    def test_skipped_count_warns_len_ooo_is_1(self, shell):
        # Arrange
        # Arrange
        m = ScitexNotebookMagics(shell)
        m._pre_run_cell(_FakePreInfo("x = 1"))
        # User re-ran an earlier cell so global counter is 7, but our local
        # is 1 — that mismatch is precisely what we want to catch.
        m._post_run_cell(_FakePostResult(execution_count=7))
        # Act
        ooo = [w for w in m.warnings if w["kind"] == "out_of_order_execution"]
        # Act
        # Assert
        # Assert
        assert len(ooo) == 1

    def test_skipped_count_warns_ooo_0_execution_count_7(self, shell):
        # Arrange
        # Arrange
        m = ScitexNotebookMagics(shell)
        m._pre_run_cell(_FakePreInfo("x = 1"))
        # User re-ran an earlier cell so global counter is 7, but our local
        # is 1 — that mismatch is precisely what we want to catch.
        m._post_run_cell(_FakePostResult(execution_count=7))
        # Act
        ooo = [w for w in m.warnings if w["kind"] == "out_of_order_execution"]
        # Act
        # Assert
        # Assert
        assert ooo[0]["execution_count"] == 7

    def test_execution_count_none_does_not_warn(self, shell):
        """Some IPython versions/results don't expose execution_count;
        absence must not create a false-positive warning."""
        # Arrange
        m = ScitexNotebookMagics(shell)
        m._pre_run_cell(_FakePreInfo("x = 1"))
        m._post_run_cell(_FakePostResult(execution_count=None))
        # Act
        ooo = [w for w in m.warnings if w["kind"] == "out_of_order_execution"]
        # Assert
        assert ooo == []


# ---------------------------------------------------------------------------
# Data-dependency parent edge
# ---------------------------------------------------------------------------


class TestDependencyEdge:
    def test_no_dep_means_independent_cell(self, shell):
        # Arrange
        m = ScitexNotebookMagics(shell)
        m._pre_run_cell(_FakePreInfo("x = 1"))
        m._post_run_cell(_FakePostResult())
        # First cell has no parent — the metadata must record an empty list.
        # The tracker is tracker_module-level state; we inspect via the
        # internal `_cell_dep_parents` snapshot kept on the magic.
        # Reset for a second, dependent cell.
        # Act
        m._pre_run_cell(_FakePreInfo("y = x + 1"))
        # Before _post fires the parent edges are already computed in pre.
        # Assert
        assert len(m._cell_dep_parents) == 1
        m._post_run_cell(_FakePostResult())

    def test_redefining_name_shifts_parent_len_m_cell_dep_parents_is_1(self, shell):
        # Arrange
        # Arrange
        m = ScitexNotebookMagics(shell)
        m._pre_run_cell(_FakePreInfo("x = 1"))
        m._post_run_cell(_FakePostResult())
        m._pre_run_cell(_FakePreInfo("x = 2"))  # redefine x
        m._post_run_cell(_FakePostResult())
        # Act
        m._pre_run_cell(_FakePreInfo("y = x"))
        # Act
        # Assert
        # Assert
        assert len(m._cell_dep_parents) == 1

    def test_redefining_name_shifts_parent_m_cell_dep_parents_0_endswith_cell_0002(
        self, shell
    ):
        # Arrange
        # Arrange
        m = ScitexNotebookMagics(shell)
        m._pre_run_cell(_FakePreInfo("x = 1"))
        m._post_run_cell(_FakePostResult())
        m._pre_run_cell(_FakePreInfo("x = 2"))  # redefine x
        m._post_run_cell(_FakePostResult())
        # Act
        m._pre_run_cell(_FakePreInfo("y = x"))
        # Act
        # Assert
        # Assert
        assert m._cell_dep_parents[0].endswith("cell-0002")


# ---------------------------------------------------------------------------
# warnings_summary()
# ---------------------------------------------------------------------------


def test_warnings_summary_aggregates_kinds_summary_n_cells_executed_1(shell):
    # Arrange
    # Arrange
    m = ScitexNotebookMagics(shell)
    m._pre_run_cell(_FakePreInfo("y = x + 1"))  # leak
    m._post_run_cell(_FakePostResult(execution_count=99))  # OOE
    # Act
    summary = m.warnings_summary()
    # Act
    # Assert
    # Assert
    assert summary["n_cells_executed"] == 1


def test_warnings_summary_aggregates_kinds_summary_n_warnings_2(shell):
    # Arrange
    # Arrange
    m = ScitexNotebookMagics(shell)
    m._pre_run_cell(_FakePreInfo("y = x + 1"))  # leak
    m._post_run_cell(_FakePostResult(execution_count=99))  # OOE
    # Act
    summary = m.warnings_summary()
    # Act
    # Assert
    # Assert
    assert summary["n_warnings"] == 2


def test_warnings_summary_aggregates_kinds_summary_by_kind_hidden_state_leak_1(shell):
    # Arrange
    # Arrange
    m = ScitexNotebookMagics(shell)
    m._pre_run_cell(_FakePreInfo("y = x + 1"))  # leak
    m._post_run_cell(_FakePostResult(execution_count=99))  # OOE
    # Act
    summary = m.warnings_summary()
    # Act
    # Assert
    # Assert
    assert summary["by_kind"]["hidden_state_leak"] == 1


def test_warnings_summary_aggregates_kinds_summary_by_kind_out_of_order_execution_1(
    shell,
):
    # Arrange
    # Arrange
    m = ScitexNotebookMagics(shell)
    m._pre_run_cell(_FakePreInfo("y = x + 1"))  # leak
    m._post_run_cell(_FakePostResult(execution_count=99))  # OOE
    # Act
    summary = m.warnings_summary()
    # Act
    # Assert
    # Assert
    assert summary["by_kind"]["out_of_order_execution"] == 1


# ---------------------------------------------------------------------------
# IPython extension entry points
# ---------------------------------------------------------------------------


class TestExtensionEntryPoints:
    def test_load_registers_handlers_pre_run_cell_in_shell_events_handlers(self, shell):
        # Arrange
        # Arrange
        # Act
        load_ipython_extension(shell)
        # Act
        # Assert
        # Assert
        assert "pre_run_cell" in shell.events.handlers

    def test_load_registers_handlers_post_run_cell_in_shell_events_handlers(
        self, shell
    ):
        # Arrange
        # Arrange
        # Act
        load_ipython_extension(shell)
        # Act
        # Assert
        # Assert
        assert "post_run_cell" in shell.events.handlers

    def test_load_registers_handlers_len_shell_events_handler_is_1(self, shell):
        # Arrange
        # Arrange
        # Act
        load_ipython_extension(shell)
        # Act
        # Assert
        # Assert
        assert len(shell.events.handlers["pre_run_cell"]) == 1

    def test_load_registers_handlers_scitex_nb_magic_in_shell_user_ns(self, shell):
        # Arrange
        # Arrange
        # Act
        load_ipython_extension(shell)
        # Act
        # Assert
        # Assert
        assert "_scitex_nb_magic" in shell.user_ns

    def test_load_is_idempotent(self, shell):
        # Arrange
        load_ipython_extension(shell)
        # Act
        load_ipython_extension(shell)
        # No double-registration.
        # Assert
        assert len(shell.events.handlers["pre_run_cell"]) == 1

    def test_unload_unregisters_and_clears_shell_events_handlers_pre_run_cell(
        self, shell
    ):
        # Arrange
        # Arrange
        load_ipython_extension(shell)
        # Act
        unload_ipython_extension(shell)
        # Act
        # Assert
        # Assert
        assert shell.events.handlers["pre_run_cell"] == []

    def test_unload_unregisters_and_clears_scitex_nb_magic_not_in_shell_user_ns(
        self, shell
    ):
        # Arrange
        # Arrange
        load_ipython_extension(shell)
        # Act
        unload_ipython_extension(shell)
        # Act
        # Assert
        # Assert
        assert "_scitex_nb_magic" not in shell.user_ns

    def test_unload_without_prior_load_is_noop(self, shell):
        """Calling unload before load must succeed and leave the shell pristine."""
        # Arrange
        before_handlers = list(shell.events.handlers.get("pre_run_cell", []))
        # Act
        unload_ipython_extension(shell)
        # Assert
        assert shell.events.handlers.get("pre_run_cell", []) == before_handlers


# ---------------------------------------------------------------------------
# Importable in a clean process
# ---------------------------------------------------------------------------


def test_module_imports_cleanly():
    """A bare ``import scitex_notebook._magic`` must not error.

    Catches accidentally-required heavy deps at import time.
    """
    # Arrange
    # Act
    mod = importlib.import_module("scitex_notebook._magic")
    # Assert
    assert mod is not None


def test_load_ipython_extension_exported_at_package_root_hasattr_scitex_notebook_load_ipython_extension():
    # Arrange
    # Arrange
    # Act
    import scitex_notebook

    # Act
    # Assert
    # Assert
    assert hasattr(scitex_notebook, "load_ipython_extension")


def test_load_ipython_extension_exported_at_package_root_hasattr_scitex_notebook_unload_ipython_extension():
    # Arrange
    # Arrange
    # Act
    import scitex_notebook

    # Act
    # Assert
    # Assert
    assert hasattr(scitex_notebook, "unload_ipython_extension")


# EOF
