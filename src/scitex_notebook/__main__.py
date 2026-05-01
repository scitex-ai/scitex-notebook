#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File: /home/ywatanabe/proj/scitex-notebook/src/scitex_notebook/__main__.py

"""Entry point for `python -m scitex_notebook`.

Per scitex-dev audit-project PS105: every distribution must be runnable
via `python -m <package>`. Delegates to the Click CLI defined in
`scitex_notebook._cli`.
"""

from scitex_notebook._cli import main

if __name__ == "__main__":
    main()
