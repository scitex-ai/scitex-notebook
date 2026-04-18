"""Sphinx configuration for scitex-notebook."""

import os
import sys

sys.path.insert(0, os.path.abspath("../../src"))

project = "scitex-notebook"
copyright = "2026, Yusuke Watanabe"
author = "Yusuke Watanabe"

try:
    from scitex_notebook import __version__

    release = __version__
    version = ".".join(release.split(".")[:2])
except ImportError:
    release = "0.1.0"
    version = "0.1"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

autodoc_mock_imports = ["scitex_clew", "mcp"]
autosummary_generate = True

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

html_theme_options = {
    "navigation_depth": 4,
    "titles_only": False,
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

napoleon_google_docstring = True
napoleon_numpy_docstring = True
