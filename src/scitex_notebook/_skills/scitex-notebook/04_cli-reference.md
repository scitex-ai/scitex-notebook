---
description: |
  [TOPIC] CLI reference
  [DETAILS] `scitex-notebook` console entry — verify-notebook, check-notebook, compile-notebook, convert-notebook, mcp.
tags: [scitex-notebook-cli-reference]
---

# CLI Reference

```
scitex-notebook [OPTIONS] COMMAND [ARGS]...
```

Jupyter notebook verification, compilation, and conversion.

## Global options

| Flag | Purpose |
|---|---|
| `-V`, `--version` | Show the version and exit |
| `--help-recursive` | Show help for all subcommands |
| `--json` | Emit structured JSON output (propagates to subcommands) |
| `-h`, `--help` | Show this message and exit |

## Configuration precedence

```
config.yaml -> $SCITEX_NOTEBOOK_CONFIG -> ~/.scitex/notebook/config.yaml -> defaults
```

## Commands

| Command | Purpose |
|---|---|
| `verify-notebook` | Verify all clew sessions associated with a notebook |
| `check-notebook` | Find cells with `scitex.io` calls not wrapped in `@stx.session` |
| `compile-notebook` | Compile notebook execution history into a DAG |
| `convert-notebook` | Convert a Jupyter notebook to a SciTeX Python script |
| `list-python-apis` | List public Python APIs in scitex-notebook |
| `mcp` | MCP (Model Context Protocol) server commands |

## Examples

```bash
scitex-notebook verify-notebook  experiment.ipynb
scitex-notebook check-notebook   experiment.ipynb
scitex-notebook compile-notebook experiment.ipynb --format mermaid
scitex-notebook convert-notebook experiment.ipynb --mode unified -o out.py
```

For per-command flags, run `scitex-notebook <command> --help` or
`scitex-notebook --help-recursive`.
