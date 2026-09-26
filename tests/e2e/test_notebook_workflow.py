"""E2E: parse a minimal notebook (real subsystem, no network)."""

import json

import pytest

pytestmark = pytest.mark.e2e


def test_parse_minimal_notebook(tmp_path):
    # Arrange
    from scitex_notebook import parse_notebook

    nb = tmp_path / "mini.ipynb"
    nb.write_text(json.dumps({"cells": [{"cell_type": "code", "source": ["x = 1"]}], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}))
    # Act
    cells = parse_notebook(str(nb))
    # Assert
    assert len(cells) == 1
