#!/usr/bin/env python3
"""CLI entry point for scitex-notebook."""

from scitex_notebook._cli._main import cli as main

__all__ = ["main"]

# EOF


# audit §4 — inject version into root --help
try:
    from importlib.metadata import version as _v
    main.help = (
        f"scitex-notebook (v{_v('scitex-notebook')}) — "
        + (main.help or "").lstrip()
    )
except Exception:
    pass

# audit-cli §1a — packages with _skills/ MUST expose
# `<cli> skills {list,get,install}`.
from ._skills import skills_group as _skills_group

main.add_command(_skills_group, name="skills")
