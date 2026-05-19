#!/usr/bin/env python3
# Timestamp: "2026-05-19 (ywatanabe)"
# File: /home/ywatanabe/proj/scitex-notebook/tests/scitex_notebook/test__convert.py

"""Tests for scitex.notebook._convert module.

Covers convert_notebook() in 'cell' and 'dag' order modes.
All file operations use tmp_path; clew DB interactions use a hand-rolled
``FakeClewDB`` injected via the public ``db=`` parameter.

Mock decisions:
  - Original DAG-order tests used ``MagicMock`` + ``patch("scitex_clew.get_db")``.
    The actual collaborator surface is tiny — ``list_runs(limit=...)`` and
    ``get_file_hashes(session_id, role=...)``. Replaced with a
    ``FakeClewDB`` dataclass that records calls in ``calls.append(...)``.
  - Production ``convert_notebook`` was extended with a keyword-only
    ``db=`` arg so callers and tests can inject without patching.
  - No behaviour test was deleted.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List

import pytest

from scitex_notebook._convert import convert_notebook

# ---------------------------------------------------------------------------
# Hand-rolled fake clew DB
# ---------------------------------------------------------------------------


@dataclass
class FakeClewDB:
    """Minimal stand-in for ``scitex_clew.VerificationDB`` used by DAG-mode."""

    rows: List[Dict[str, Any]] = field(default_factory=list)
    hashes: Dict[str, str] = field(default_factory=dict)
    calls: List[Dict[str, Any]] = field(default_factory=list)

    def list_runs(self, limit: int = 1_000) -> List[Dict[str, Any]]:
        self.calls.append({"method": "list_runs", "limit": limit})
        return list(self.rows)

    def get_file_hashes(self, session_id: str, role: str) -> Dict[str, str]:
        self.calls.append(
            {"method": "get_file_hashes", "session_id": session_id, "role": role}
        )
        return dict(self.hashes)


# ---------------------------------------------------------------------------
# Notebook fixtures
# ---------------------------------------------------------------------------

SAMPLE_NB = {
    "cells": [
        {
            "cell_type": "markdown",
            "source": ["# Analysis Notebook"],
            "metadata": {},
            "id": "md1",
        },
        {
            "cell_type": "code",
            "source": ["import numpy as np\n", "x = np.array([1, 2, 3])"],
            "metadata": {},
            "id": "code1",
            "outputs": [],
        },
        {
            "cell_type": "code",
            "source": [
                "%matplotlib inline\n",
                "import matplotlib.pyplot as plt\n",
                "plt.plot(x)",
            ],
            "metadata": {},
            "id": "code2",
            "outputs": [],
        },
        {
            "cell_type": "code",
            "source": ["!pip install scipy\n", "from scipy import stats"],
            "metadata": {},
            "id": "code3",
            "outputs": [],
        },
    ],
    "metadata": {"kernelspec": {"name": "python3"}},
    "nbformat": 4,
    "nbformat_minor": 5,
}


@pytest.fixture
def notebook_path(tmp_path):
    """Write the sample notebook to tmp_path and return its Path."""
    nb_file = tmp_path / "sample_analysis.ipynb"
    nb_file.write_text(json.dumps(SAMPLE_NB), encoding="utf-8")
    return nb_file


# ---------------------------------------------------------------------------
# convert_notebook() — cell order
# ---------------------------------------------------------------------------


def test_convert_notebook_cell_order_returns_str_type(notebook_path):
    # Arrange
    # Act
    result = convert_notebook(notebook_path, order="cell")
    # Assert
    assert isinstance(result, str)


def test_convert_notebook_cell_order_returns_nonempty_string(notebook_path):
    # Arrange
    # Act
    result = convert_notebook(notebook_path, order="cell")
    # Assert
    assert len(result) > 0


def test_convert_notebook_contains_python3_shebang(notebook_path):
    """Converted script must contain a Python shebang."""
    # Arrange
    # Act
    result = convert_notebook(notebook_path, order="cell")
    # Assert
    assert "#!/usr/bin/env python3" in result


def test_convert_notebook_contains_scitex_import_alias(notebook_path):
    """Converted script must import scitex as stx."""
    # Arrange
    # Act
    result = convert_notebook(notebook_path, order="cell")
    # Assert
    assert "import scitex as stx" in result


def test_convert_notebook_each_code_cell_becomes_function(notebook_path):
    """Each non-empty code cell should produce a function definition."""
    # Arrange
    result = convert_notebook(notebook_path, order="cell")
    # Act
    def_count = result.count("def cell_")
    # Assert
    assert def_count == 3


def test_convert_notebook_session_decorator_emitted_per_cell(notebook_path):
    """Every generated function should be decorated with @stx.session."""
    # Arrange
    result = convert_notebook(notebook_path, order="cell")
    # Act
    session_count = result.count("@stx.session")
    # Assert
    assert session_count == 3


def test_convert_notebook_magic_percent_stripped_from_output(notebook_path):
    """IPython % magic commands should be stripped from the output."""
    # Arrange
    # Act
    result = convert_notebook(notebook_path, order="cell")
    # Assert
    assert "%matplotlib" not in result


def test_convert_notebook_magic_bang_stripped_from_output(notebook_path):
    """IPython ! shell commands should be stripped from the output."""
    # Arrange
    # Act
    result = convert_notebook(notebook_path, order="cell")
    # Assert
    assert "!pip" not in result


def test_convert_notebook_markdown_cells_excluded_from_output(notebook_path):
    """Markdown cell content should not appear in the generated script."""
    # Arrange
    # Act
    result = convert_notebook(notebook_path, order="cell")
    # Assert
    assert "# Analysis Notebook" not in result


def test_convert_notebook_code_preserves_numpy_import(notebook_path):
    # Arrange
    # Act
    result = convert_notebook(notebook_path, order="cell")
    # Assert
    assert "import numpy as np" in result


def test_convert_notebook_code_preserves_assignment_statement(notebook_path):
    # Arrange
    # Act
    result = convert_notebook(notebook_path, order="cell")
    # Assert
    assert "x = np.array([1, 2, 3])" in result


def test_convert_notebook_output_file_created_on_disk(notebook_path, tmp_path):
    # Arrange
    out_file = tmp_path / "output_script.py"
    # Act
    convert_notebook(notebook_path, output=out_file, order="cell")
    # Assert
    assert out_file.exists()


def test_convert_notebook_output_file_content_equals_returned_string(
    notebook_path, tmp_path
):
    # Arrange
    out_file = tmp_path / "output_script.py"
    # Act
    result = convert_notebook(notebook_path, output=out_file, order="cell")
    content = out_file.read_text(encoding="utf-8")
    # Assert
    assert content == result


def test_convert_notebook_output_none_writes_no_file(notebook_path, tmp_path):
    """When output is None, no .py file should be created."""
    # Arrange
    before = set(tmp_path.iterdir())
    # Act
    convert_notebook(notebook_path, output=None, order="cell")
    after = set(tmp_path.iterdir())
    new_files = after - before
    py_files = [f for f in new_files if f.suffix == ".py"]
    # Assert
    assert py_files == []


def test_convert_notebook_creates_output_parent_dirs(tmp_path, notebook_path):
    """convert_notebook should create missing parent directories for output."""
    # Arrange
    out_file = tmp_path / "nested" / "deep" / "script.py"
    # Act
    convert_notebook(notebook_path, output=out_file, order="cell")
    # Assert
    assert out_file.exists()


def test_convert_notebook_each_function_is_called(notebook_path):
    """Each generated function should also be called (function_name() line)."""
    # Arrange
    import re

    result = convert_notebook(notebook_path, order="cell")
    defs = re.findall(r"def (cell_\d+)\(\):", result)
    # Act
    every_called = all(f"{name}()" in result for name in defs)
    # Assert
    assert every_called


def test_convert_notebook_empty_code_notebook_still_has_shebang(tmp_path):
    # Arrange
    nb = {
        "cells": [
            {
                "cell_type": "markdown",
                "source": ["# Only markdown"],
                "metadata": {},
                "id": "md1",
            }
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    nb_file = tmp_path / "empty_code.ipynb"
    nb_file.write_text(json.dumps(nb), encoding="utf-8")
    # Act
    result = convert_notebook(nb_file, order="cell")
    # Assert
    assert "#!/usr/bin/env python3" in result


def test_convert_notebook_empty_code_notebook_emits_no_cell_function(tmp_path):
    # Arrange
    nb = {
        "cells": [
            {
                "cell_type": "markdown",
                "source": ["# Only markdown"],
                "metadata": {},
                "id": "md1",
            }
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    nb_file = tmp_path / "empty_code.ipynb"
    nb_file.write_text(json.dumps(nb), encoding="utf-8")
    # Act
    result = convert_notebook(nb_file, order="cell")
    # Assert
    assert "def cell_" not in result


def test_convert_notebook_accepts_string_path_returns_string(notebook_path):
    # Arrange
    # Act
    result = convert_notebook(str(notebook_path), order="cell")
    # Assert
    assert isinstance(result, str)


def test_convert_notebook_accepts_string_path_contains_stx(notebook_path):
    # Arrange
    # Act
    result = convert_notebook(str(notebook_path), order="cell")
    # Assert
    assert "stx" in result


def test_convert_notebook_header_references_source_name(notebook_path):
    """Converted script docstring should reference the source notebook name."""
    # Arrange
    # Act
    result = convert_notebook(notebook_path, order="cell")
    # Assert
    assert "sample_analysis.ipynb" in result


# ---------------------------------------------------------------------------
# Invalid order
# ---------------------------------------------------------------------------


def test_convert_notebook_invalid_order_raises_valueerror(notebook_path):
    """convert_notebook with invalid order should raise ValueError."""
    # Arrange
    bad_order = "notebook"
    # Act
    # Assert
    with pytest.raises(ValueError, match="Invalid order"):
        convert_notebook(notebook_path, order=bad_order)


def test_convert_notebook_invalid_order_message_includes_bad_value(notebook_path):
    """Error message should mention the bad value."""
    # Arrange
    bad_order = "notebook"
    # Act
    # Assert
    with pytest.raises(ValueError, match="notebook"):
        convert_notebook(notebook_path, order=bad_order)


# ---------------------------------------------------------------------------
# DAG order using hand-rolled FakeClewDB
# ---------------------------------------------------------------------------


def _write_single_cell_nb(tmp_path, name="dag_test.ipynb"):
    nb_file = tmp_path / name
    nb_file.write_text(
        json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": ["x = 1"],
                        "metadata": {},
                        "id": "c1",
                        "outputs": [],
                    }
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        ),
        encoding="utf-8",
    )
    return nb_file


def test_convert_notebook_dag_no_history_falls_back_to_cell_functions(tmp_path):
    # Arrange
    nb_file = _write_single_cell_nb(tmp_path)
    db = FakeClewDB(rows=[])
    # Act
    result = convert_notebook(nb_file, order="dag", db=db)
    # Assert
    assert "def cell_" in result


def test_convert_notebook_dag_no_history_emits_session_decorator(tmp_path):
    # Arrange
    nb_file = _write_single_cell_nb(tmp_path)
    db = FakeClewDB(rows=[])
    # Act
    result = convert_notebook(nb_file, order="dag", db=db)
    # Assert
    assert "@stx.session" in result


def _make_db_with_one_run(nb_file):
    return FakeClewDB(
        rows=[
            {
                "session_id": "run-001",
                "started_at": "2026-01-01T00:00:00",
                "script_path": str(nb_file),
                "metadata": json.dumps({"notebook_path": str(nb_file.resolve())}),
            }
        ],
        hashes={},
    )


def test_convert_notebook_dag_with_history_emits_step_functions(tmp_path):
    # Arrange
    nb_file = _write_single_cell_nb(tmp_path, name="dag_hist.ipynb")
    db = _make_db_with_one_run(nb_file)
    # Act
    result = convert_notebook(nb_file, order="dag", db=db)
    # Assert
    assert "def step_" in result


def test_convert_notebook_dag_with_history_emits_session_decorator(tmp_path):
    # Arrange
    nb_file = _write_single_cell_nb(tmp_path, name="dag_hist.ipynb")
    db = _make_db_with_one_run(nb_file)
    # Act
    result = convert_notebook(nb_file, order="dag", db=db)
    # Assert
    assert "@stx.session" in result


def test_convert_notebook_dag_with_history_emits_auto_compiled_docstring(tmp_path):
    # Arrange
    nb_file = _write_single_cell_nb(tmp_path, name="dag_hist.ipynb")
    db = _make_db_with_one_run(nb_file)
    # Act
    result = convert_notebook(nb_file, order="dag", db=db)
    # Assert
    assert "Auto-compiled" in result


# EOF
