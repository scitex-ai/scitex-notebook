"""Smoke: notebook CLI happy paths (fast, subprocess, every PR)."""

import subprocess
import sys

import pytest

pytestmark = pytest.mark.smoke


def test_notebook_help_exits_zero():
    # Arrange
    cmd = [sys.executable, "-m", "scitex_notebook", "--help"]
    # Act
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    # Assert
    assert proc.returncode == 0
