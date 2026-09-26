---
description: |
  [TOPIC] MCP tools — scitex-notebook FastMCP server
  [DETAILS] Nine `@mcp.tool()` callables registered on the canonical `mcp` instance in `_mcp_server.py`. Mounted by the umbrella under the `notebook_*` namespace.
tags: [scitex-notebook-mcp-tools]
---

# MCP tools — scitex-notebook

Tools are defined in `src/scitex_notebook/_mcp_server.py` on a single
`FastMCP(name="scitex-notebook")` instance. The umbrella `scitex._mcp_tools`
mounts this server via `safe_mount(namespace=...)` so every tool is exposed
as `notebook_<verb>` at the umbrella level.

## Tools

| Tool | Signature | Purpose |
|------|-----------|---------|
| `notebook_verify` | `(path: str)` | Run every recorded `@scitex.session` block in the `.ipynb` against the Clew DB and return per-session pass/fail. |
| `notebook_check` | `(path: str)` | Find every `scitex.io` save/load call outside a `@scitex.session` block (untracked I/O audit). |
| `notebook_compile` | `(path: str, format: str = "mermaid")` | Reconstruct the cell-dependency DAG from Clew timestamps; emit as `mermaid`, `script`, or `json`. |
| `notebook_convert` | `(path, mode="per_cell", order="cell", output=None)` | Convert notebook to a SciTeX `.py` script with `@stx.session` decorators. `mode` ∈ `per_cell`/`unified`; `order` ∈ `cell`/`dag`. |
| `notebook_parse_notebook` | `(path: str)` | Parse a `.ipynb` file and return every cell (index, source, cell_id, cell_type). |
| `notebook_get_code_cells` | `(path: str)` | Return only the code cells of a `.ipynb`, dropping markdown/raw cells. |
| `notebook_get_notebook_name` | `(path: str)` | Return the notebook's stem name (filename without extension). |
| `notebook_skills_list` | `()` | List the bundled skill pages under `_skills/scitex-notebook/`. |
| `notebook_skills_get` | `(name: str)` | Return the body of a named skill page (e.g. `"SKILL"`). |

## Run

```bash
fastmcp run scitex_notebook._mcp_server:mcp
# or
scitex-notebook mcp start
```

## Source of truth

`src/scitex_notebook/_mcp_server.py` — the single `mcp` instance is the
single source of truth; do not re-wrap tools elsewhere.
