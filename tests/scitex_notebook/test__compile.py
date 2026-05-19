#!/usr/bin/env python3
# Timestamp: "2026-05-19 (ywatanabe)"
# File: /home/ywatanabe/proj/scitex-notebook/tests/scitex_notebook/test__compile.py

"""Tests for scitex.notebook._compile module.

Covers _topological_sort, _build_dag, CompiledNotebook, and compile_notebook.

Mock decisions:
  - Original tests used ``MagicMock`` + ``patch("scitex_clew.get_db", ...)``.
    The DB interface that _build_dag and compile_notebook actually call is
    a tiny surface (``list_runs(limit=...)`` and
    ``get_file_hashes(session_id, role=...)``), so a hand-rolled fake is
    trivial and exercises the real production code path.
  - Production ``compile_notebook`` was extended with a keyword-only
    ``db=`` arg (dependency injection) so callers — including tests —
    can pass a real or fake DB without monkey-patching imports.
  - No behaviour test was deleted; every original assertion has an
    equivalent here against a real or hand-rolled-fake collaborator.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pytest

from scitex_notebook._compile import (
    CompiledNotebook,
    _build_dag,
    _topological_sort,
    compile_notebook,
)

# ---------------------------------------------------------------------------
# Hand-rolled fake clew DB
# ---------------------------------------------------------------------------


@dataclass
class FakeClewDB:
    """Minimal stand-in for ``scitex_clew.VerificationDB``.

    Surface exercised by ``_build_dag`` and ``compile_notebook``:
      * ``list_runs(limit=...)`` returns the ``rows`` list.
      * ``get_file_hashes(session_id, role=...)`` is looked up via
        ``hashes_fn`` (a callable so tests can express A→B IO chains)
        or falls back to ``hashes`` (a flat dict if no callable given).
    """

    rows: List[Dict[str, Any]] = field(default_factory=list)
    hashes: Dict[str, str] = field(default_factory=dict)
    hashes_fn: Optional[Callable[..., Dict[str, str]]] = None
    calls: List[Dict[str, Any]] = field(default_factory=list)

    def list_runs(self, limit: int = 1_000) -> List[Dict[str, Any]]:
        self.calls.append({"method": "list_runs", "limit": limit})
        return list(self.rows)

    def get_file_hashes(self, session_id: str, role: str) -> Dict[str, str]:
        self.calls.append(
            {"method": "get_file_hashes", "session_id": session_id, "role": role}
        )
        if self.hashes_fn is not None:
            return self.hashes_fn(session_id, role)
        return dict(self.hashes)


# ---------------------------------------------------------------------------
# _topological_sort() tests
# ---------------------------------------------------------------------------


def test_topological_sort_linear_chain_orders_a_before_b():
    # Arrange
    dag = {"A": ["B"], "B": ["C"], "C": []}
    fallback = ["A", "B", "C"]
    # Act
    result = _topological_sort(dag, fallback)
    # Assert
    assert result.index("A") < result.index("B")


def test_topological_sort_linear_chain_orders_b_before_c():
    # Arrange
    dag = {"A": ["B"], "B": ["C"], "C": []}
    fallback = ["A", "B", "C"]
    # Act
    result = _topological_sort(dag, fallback)
    # Assert
    assert result.index("B") < result.index("C")


def test_topological_sort_diamond_root_first():
    # Arrange
    dag = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
    fallback = ["A", "B", "C", "D"]
    # Act
    result = _topological_sort(dag, fallback)
    # Assert
    assert result[0] == "A"


def test_topological_sort_diamond_sink_last():
    # Arrange
    dag = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
    fallback = ["A", "B", "C", "D"]
    # Act
    result = _topological_sort(dag, fallback)
    # Assert
    assert result[-1] == "D"


def test_topological_sort_diamond_b_before_d():
    # Arrange
    dag = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
    fallback = ["A", "B", "C", "D"]
    # Act
    result = _topological_sort(dag, fallback)
    # Assert
    assert result.index("B") < result.index("D")


def test_topological_sort_diamond_c_before_d():
    # Arrange
    dag = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
    fallback = ["A", "B", "C", "D"]
    # Act
    result = _topological_sort(dag, fallback)
    # Assert
    assert result.index("C") < result.index("D")


def test_topological_sort_empty_dag_returns_fallback():
    """Empty DAG must return the fallback order unchanged."""
    # Arrange
    dag = {}
    fallback = ["X", "Y", "Z"]
    # Act
    result = _topological_sort(dag, fallback)
    # Assert
    assert result == fallback


def test_topological_sort_single_node_returned_as_only_element():
    """DAG with a single node and no edges should return that node."""
    # Arrange
    dag = {"solo": []}
    fallback = ["solo"]
    # Act
    result = _topological_sort(dag, fallback)
    # Assert
    assert result == ["solo"]


def test_topological_sort_disconnected_nodes_all_present():
    """Nodes not connected by edges should all appear in result."""
    # Arrange
    dag = {"A": [], "B": [], "C": []}
    fallback = ["A", "B", "C"]
    # Act
    result = _topological_sort(dag, fallback)
    # Assert
    assert set(result) == {"A", "B", "C"}


def test_topological_sort_respects_fallback_tiebreaker():
    """When two nodes have same in-degree, fallback_order is used as tiebreaker."""
    # Arrange
    dag = {"root": ["A", "B"], "A": [], "B": []}
    fallback = ["root", "A", "B"]
    # Act
    result = _topological_sort(dag, fallback)
    # Assert
    assert result.index("A") < result.index("B")


def test_topological_sort_nodes_not_in_dag_appended_to_result():
    """Nodes in fallback_order but absent from DAG should be appended at end."""
    # Arrange
    dag = {"A": ["B"], "B": []}
    fallback = ["A", "B", "C"]  # C is not in dag
    # Act
    result = _topological_sort(dag, fallback)
    # Assert
    assert "C" in result


# ---------------------------------------------------------------------------
# _build_dag() tests
# ---------------------------------------------------------------------------


def _make_run(session_id):
    """Helper to make a minimal run dict."""
    return {"session_id": session_id}


def test_build_dag_no_shared_files_produces_empty_adjacency():
    """Sessions with no shared IO files should produce an empty DAG (no edges)."""
    # Arrange
    runs = [_make_run("s1"), _make_run("s2")]
    db = FakeClewDB(hashes={})
    # Act
    dag = _build_dag(runs, db)
    # Assert
    assert dag == {"s1": [], "s2": []}


def test_build_dag_producer_consumer_edge_b_listed_under_a():
    # Arrange
    runs = [_make_run("A"), _make_run("B")]

    def _hashes(session_id, role):
        if session_id == "A" and role == "output":
            return {"shared.csv": "hash1"}
        if session_id == "B" and role == "input":
            return {"shared.csv": "hash1"}
        return {}

    db = FakeClewDB(hashes_fn=_hashes)
    # Act
    dag = _build_dag(runs, db)
    # Assert
    assert "B" in dag["A"]


def test_build_dag_producer_consumer_edge_a_not_listed_under_b():
    # Arrange
    runs = [_make_run("A"), _make_run("B")]

    def _hashes(session_id, role):
        if session_id == "A" and role == "output":
            return {"shared.csv": "hash1"}
        if session_id == "B" and role == "input":
            return {"shared.csv": "hash1"}
        return {}

    db = FakeClewDB(hashes_fn=_hashes)
    # Act
    dag = _build_dag(runs, db)
    # Assert
    assert "A" not in dag.get("B", [])


def test_build_dag_no_self_edge_for_single_session():
    """A session should not be its own producer/consumer."""
    # Arrange
    runs = [_make_run("A")]
    db = FakeClewDB(hashes={"file.csv": "hash1"})
    # Act
    dag = _build_dag(runs, db)
    # Assert
    assert "A" not in dag.get("A", [])


def test_build_dag_all_sessions_present_as_keys():
    """Every session ID must appear as a key in the returned DAG."""
    # Arrange
    runs = [_make_run("s1"), _make_run("s2"), _make_run("s3")]
    db = FakeClewDB(hashes={})
    # Act
    dag = _build_dag(runs, db)
    # Assert
    assert set(dag.keys()) == {"s1", "s2", "s3"}


# ---------------------------------------------------------------------------
# CompiledNotebook tests
# ---------------------------------------------------------------------------


def test_compiled_notebook_to_mermaid_contains_graph_td_header():
    """to_mermaid() output must start with 'graph TD'."""
    # Arrange
    cn = CompiledNotebook(notebook_path="/nb.ipynb")
    # Act
    mermaid = cn.to_mermaid()
    # Assert
    assert "graph TD" in mermaid


def test_compiled_notebook_to_mermaid_includes_graph_td_with_sessions():
    # Arrange
    runs = [
        {"session_id": "session-abc123", "started_at": "2026-01-01T00:00:00"},
        {"session_id": "session-def456", "started_at": "2026-01-02T00:00:00"},
    ]
    cn = CompiledNotebook(
        notebook_path="/nb.ipynb",
        execution_order=["session-abc123", "session-def456"],
        dag={"session-abc123": ["session-def456"], "session-def456": []},
        runs=runs,
    )
    # Act
    mermaid = cn.to_mermaid()
    # Assert
    assert "graph TD" in mermaid


def test_compiled_notebook_to_mermaid_includes_session_id_token():
    # Arrange
    runs = [
        {"session_id": "session-abc123", "started_at": "2026-01-01T00:00:00"},
        {"session_id": "session-def456", "started_at": "2026-01-02T00:00:00"},
    ]
    cn = CompiledNotebook(
        notebook_path="/nb.ipynb",
        execution_order=["session-abc123", "session-def456"],
        dag={"session-abc123": ["session-def456"], "session-def456": []},
        runs=runs,
    )
    # Act
    mermaid = cn.to_mermaid()
    # Assert
    assert "session-abc123"[:20].replace("-", "_") in mermaid.replace("-", "_")


def test_compiled_notebook_to_mermaid_includes_edge_arrows():
    """to_mermaid() should include '-->' arrows for DAG edges."""
    # Arrange
    runs = [
        {"session_id": "A", "started_at": ""},
        {"session_id": "B", "started_at": ""},
    ]
    cn = CompiledNotebook(
        notebook_path="/nb.ipynb",
        execution_order=["A", "B"],
        dag={"A": ["B"], "B": []},
        runs=runs,
    )
    # Act
    mermaid = cn.to_mermaid()
    # Assert
    assert "-->" in mermaid


def test_compiled_notebook_to_script_contains_shebang():
    """to_script() output must contain a Python shebang line."""
    # Arrange
    cn = CompiledNotebook(notebook_path="/nb.ipynb")
    # Act
    script = cn.to_script()
    # Assert
    assert "#!/usr/bin/env python3" in script


def test_compiled_notebook_to_script_contains_scitex_import():
    """to_script() must import scitex as stx."""
    # Arrange
    cn = CompiledNotebook(notebook_path="/nb.ipynb")
    # Act
    script = cn.to_script()
    # Assert
    assert "import scitex as stx" in script


def test_compiled_notebook_to_script_emits_session_decorator():
    """to_script() must include @stx.session decorator for each session."""
    # Arrange
    runs = [{"session_id": "run-001", "script_path": "/script.py"}]
    cn = CompiledNotebook(
        notebook_path="/nb.ipynb",
        execution_order=["run-001"],
        dag={"run-001": []},
        runs=runs,
    )
    # Act
    script = cn.to_script()
    # Assert
    assert "@stx.session" in script


def test_compiled_notebook_to_script_empty_still_emits_header():
    """to_script() with no runs should still produce a valid (minimal) header."""
    # Arrange
    cn = CompiledNotebook(notebook_path="/nb.ipynb")
    # Act
    script = cn.to_script()
    # Assert
    assert "python3" in script and "stx" in script


def test_compiled_notebook_to_script_function_per_session_one_per_run():
    """to_script() should produce one function definition per session."""
    # Arrange
    runs = [
        {"session_id": "r1", "script_path": ""},
        {"session_id": "r2", "script_path": ""},
    ]
    cn = CompiledNotebook(
        notebook_path="/nb.ipynb",
        execution_order=["r1", "r2"],
        dag={"r1": [], "r2": []},
        runs=runs,
    )
    script = cn.to_script()
    # Act
    def_count = script.count("def step_")
    # Assert
    assert def_count == 2


def test_compiled_notebook_default_execution_order_is_empty():
    # Arrange
    # Act
    cn = CompiledNotebook(notebook_path="/nb.ipynb")
    # Assert
    assert cn.execution_order == []


def test_compiled_notebook_default_dag_is_empty():
    # Arrange
    # Act
    cn = CompiledNotebook(notebook_path="/nb.ipynb")
    # Assert
    assert cn.dag == {}


def test_compiled_notebook_default_runs_is_empty():
    # Arrange
    # Act
    cn = CompiledNotebook(notebook_path="/nb.ipynb")
    # Assert
    assert cn.runs == []


# ---------------------------------------------------------------------------
# Cycle detection tests
# ---------------------------------------------------------------------------


def test_topological_sort_cycle_warns_with_cyclic_message():
    """Cyclic DAG should emit a warning whose text mentions cyclic deps."""
    # Arrange
    import warnings

    dag = {"A": ["B"], "B": ["A"]}
    fallback = ["A", "B"]
    # Act
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        _topological_sort(dag, fallback)
        # Assert
        assert len(w) == 1 and "Cyclic" in str(w[0].message)


def test_topological_sort_two_node_cycle_returns_all_nodes():
    """Cyclic DAG should still return every node in the result."""
    # Arrange
    import warnings

    dag = {"A": ["B"], "B": ["A"]}
    fallback = ["A", "B"]
    # Act
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        result = _topological_sort(dag, fallback)
    # Assert
    assert set(result) == {"A", "B"}


def test_topological_sort_cycle_preserves_non_cyclic_nodes():
    """Nodes not in cycle should still appear correctly in the result."""
    # Arrange
    import warnings

    # C depends on A; A and B form a cycle
    dag = {"A": ["B"], "B": ["A"], "C": []}
    fallback = ["C", "A", "B"]
    # Act
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        result = _topological_sort(dag, fallback)
    # Assert
    assert set(result) == {"A", "B", "C"}


def test_topological_sort_three_node_cycle_emits_single_warning():
    """Three-node cycle A→B→C→A should emit exactly one warning."""
    # Arrange
    import warnings

    dag = {"A": ["B"], "B": ["C"], "C": ["A"]}
    fallback = ["A", "B", "C"]
    # Act
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        _topological_sort(dag, fallback)
        # Assert
        assert len(w) == 1


def test_topological_sort_three_node_cycle_returns_all_nodes():
    """Three-node cycle A→B→C→A should include all nodes in the result."""
    # Arrange
    import warnings

    dag = {"A": ["B"], "B": ["C"], "C": ["A"]}
    fallback = ["A", "B", "C"]
    # Act
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        result = _topological_sort(dag, fallback)
    # Assert
    assert set(result) == {"A", "B", "C"}


# ---------------------------------------------------------------------------
# compile_notebook() tests using injected FakeClewDB
# ---------------------------------------------------------------------------


def _write_empty_notebook(tmp_path, name="test.ipynb"):
    nb = {
        "cells": [],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    nb_file = tmp_path / name
    nb_file.write_text(json.dumps(nb), encoding="utf-8")
    return nb_file


def test_compile_notebook_empty_runs_returns_empty_execution_order(tmp_path):
    # Arrange
    nb_file = _write_empty_notebook(tmp_path)
    db = FakeClewDB(rows=[])
    # Act
    result = compile_notebook(nb_file, db=db)
    # Assert
    assert result.execution_order == []


def test_compile_notebook_empty_runs_returns_empty_dag(tmp_path):
    # Arrange
    nb_file = _write_empty_notebook(tmp_path)
    db = FakeClewDB(rows=[])
    # Act
    result = compile_notebook(nb_file, db=db)
    # Assert
    assert result.dag == {}


def _two_run_db(nb_file):
    return FakeClewDB(
        rows=[
            {
                "session_id": "s1",
                "started_at": "2026-01-01T00:00:00",
                "script_path": str(nb_file),
                "metadata": json.dumps({"notebook_path": str(nb_file.resolve())}),
            },
            {
                "session_id": "s2",
                "started_at": "2026-01-01T00:01:00",
                "script_path": str(nb_file),
                "metadata": json.dumps({"notebook_path": str(nb_file.resolve())}),
            },
        ],
        hashes={},
    )


def test_compile_notebook_two_runs_execution_order_is_s1_s2(tmp_path):
    # Arrange
    nb_file = _write_empty_notebook(tmp_path, name="experiment.ipynb")
    db = _two_run_db(nb_file)
    # Act
    result = compile_notebook(nb_file, db=db)
    # Assert
    assert result.execution_order == ["s1", "s2"]


def test_compile_notebook_two_runs_dag_contains_s1_key(tmp_path):
    # Arrange
    nb_file = _write_empty_notebook(tmp_path, name="experiment.ipynb")
    db = _two_run_db(nb_file)
    # Act
    result = compile_notebook(nb_file, db=db)
    # Assert
    assert "s1" in result.dag


def test_compile_notebook_two_runs_dag_contains_s2_key(tmp_path):
    # Arrange
    nb_file = _write_empty_notebook(tmp_path, name="experiment.ipynb")
    db = _two_run_db(nb_file)
    # Act
    result = compile_notebook(nb_file, db=db)
    # Assert
    assert "s2" in result.dag


# EOF
