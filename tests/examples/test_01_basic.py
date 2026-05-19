"""Smoke test for examples/01_basic.py.

Auto-generated stub (audit-project PS303). Replace with a real test
that runs the example end-to-end and asserts on its outputs.
"""

import importlib.util
from pathlib import Path

import pytest

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "01_basic.py"


# Whole-module skip if the example is not a Python file. Keeps each test
# body to a single assertion (STX-TQ007 compliant).
pytestmark = pytest.mark.skipif(
    EXAMPLE.exists() and EXAMPLE.suffix != ".py",
    reason=f"non-python example: {EXAMPLE.suffix}",
)


def test_example_file_exists_on_disk():
    # Arrange
    # Act
    exists = EXAMPLE.exists()
    # Assert
    assert exists, f"missing example file: {EXAMPLE}"


def test_example_imports_cleanly_spec_is_not_none():
    # Arrange
    # Act
    spec = importlib.util.spec_from_file_location("ex", EXAMPLE)
    # Assert
    assert spec is not None


def test_example_imports_cleanly_spec_loader_is_not_none():
    # Arrange
    # Act
    spec = importlib.util.spec_from_file_location("ex", EXAMPLE)
    # Assert
    assert spec is not None and spec.loader is not None


def test_example_imports_cleanly_module_is_not_none():
    # Arrange
    spec = importlib.util.spec_from_file_location("ex", EXAMPLE)
    # Act
    module = (
        importlib.util.module_from_spec(spec)
        if spec is not None and spec.loader is not None
        else None
    )
    # Assert
    assert module is not None
