---
description: |
  [TOPIC] Installation
  [DETAILS] pip install scitex-notebook. Pulls click + scitex-clew. Optional [linter] and [mcp] extras.
tags: [scitex-notebook-installation]
---

# Installation

## Standard

```bash
pip install scitex-notebook
```

Pulls `click>=8.0` and `scitex-clew` (for session-result lookup).

## Optional extras

| Extra | Purpose |
|---|---|
| `linter` | Plugin for `scitex-linter` (notebook-aware checks) |
| `mcp` | MCP server (`scitex-notebook mcp serve`) |
| `dev` | Test + lint tooling |
| `docs` | Sphinx + RTD theme |
| `all` | Everything above |

```bash
pip install 'scitex-notebook[mcp]'
```

## Verify

```bash
python -c "import scitex_notebook; print(scitex_notebook.__version__)"
scitex-notebook --version
scitex-notebook --help
```

## Editable install (development)

```bash
git clone https://github.com/ywatanabe1989/scitex-notebook
cd scitex-notebook
pip install -e '.[dev]'
```

## Umbrella alternative

`pip install scitex` exposes the same module as `scitex.notebook`.
