"""Regression test: importing tests/conftest.py must not touch site-packages."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

CONFTEST_PATH = Path(__file__).resolve().parents[1] / "conftest.py"


def test_conftest_leaves_site_packages_untouched():
    # Arrange
    child_code = (
        "import os\n"
        "import runpy\n"
        "import site\n"
        "from pathlib import Path\n"
        f"conftest = {str(CONFTEST_PATH)!r}\n"
        "os.environ['COVERAGE_PROCESS_START'] = 'sentinel-process-start'\n"
        "os.environ['COVERAGE_FILE'] = 'sentinel-coverage-file'\n"
        "dirs = list(site.getsitepackages())\n"
        "dirs.append(site.getusersitepackages())\n"
        "before = {}\n"
        "for d in dirs:\n"
        "    p = Path(d)\n"
        "    try:\n"
        "        before[d] = sorted(x.name for x in p.iterdir()) if p.is_dir() else []\n"
        "    except OSError:\n"
        "        before[d] = []\n"
        "runpy.run_path(conftest)\n"
        "for d in dirs:\n"
        "    p = Path(d)\n"
        "    try:\n"
        "        after = sorted(x.name for x in p.iterdir()) if p.is_dir() else []\n"
        "    except OSError:\n"
        "        after = []\n"
        "    assert before[d] == after, d\n"
        "assert os.environ['COVERAGE_PROCESS_START'] == 'sentinel-process-start'\n"
        "assert os.environ['COVERAGE_FILE'] == 'sentinel-coverage-file'\n"
    )
    # Act
    proc = subprocess.run(
        [sys.executable, "-c", child_code],
        capture_output=True,
        text=True,
    )
    # Assert
    assert proc.returncode == 0, proc.stderr
