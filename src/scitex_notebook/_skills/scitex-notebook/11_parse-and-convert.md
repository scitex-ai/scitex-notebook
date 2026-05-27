---
description: |
  [TOPIC] Parse And Convert
  [DETAILS] Extract cells from .ipynb files and convert notebooks to @stx.session .py scripts.
tags: [scitex-notebook-parse-and-convert, scitex-notebook]
---


# Parse and Convert Notebooks

Uses stdlib `json` only — no `nbformat` dependency.

## parse_notebook

Parse a `.ipynb` file into a list of all cell dicts.

```python
from scitex_notebook import parse_notebook, get_code_cells, get_notebook_name

cells = parse_notebook("experiment.ipynb")
# [
#   {"index": 0, "cell_id": "abc123", "cell_type": "markdown", "source": "# Title"},
#   {"index": 1, "cell_id": "def456", "cell_type": "code",     "source": "import ..."},
#   ...
# ]

code_cells = get_code_cells("experiment.ipynb")
# Only cells where cell_type == "code"

name = get_notebook_name("experiment.ipynb")
# "experiment"   (stem, no extension)
```

Each cell dict contains:
- `index` — position in the notebook
- `cell_id` — notebook cell ID (or `"cell_N"` if absent)
- `cell_type` — `"code"`, `"markdown"`, or `"raw"`
- `source` — joined source string

## convert_notebook

Convert a notebook to an `@stx.session`-based Python script.

```python
from scitex_notebook import convert, convert_notebook

# Per-cell: each code cell becomes its own @stx.session function
script = convert_notebook("experiment.ipynb", mode="per_cell")
# or using the bare-verb alias:
script = convert("experiment.ipynb", mode="per_cell")

# Unified: all cells merged into a single @stx.session main()
# with imports hoisted to module level and markdown → comments
script = convert_notebook("experiment.ipynb", mode="unified")
```

Parameters:
| Param | Default | Description |
|---|---|---|
| `mode` | `"per_cell"` | `"per_cell"` (individual sessions) or `"unified"` (single `main()`) |
| `order` | `"cell"` | `"cell"` (notebook order) or `"dag"` (execution order from clew DB) |
| `output` | `None` | If set, write the `.py` to this path |

The `"unified"` mode automatically converts common notebook patterns:
`plt.show()` → `# stx.io.save(...)`, `pd.read_csv(...)` → `stx.io.load(...)`,
`df.to_csv(...)` → `stx.io.save(...)`, etc.

## CLI

```bash
scitex-notebook convert-notebook experiment.ipynb --mode unified -o experiment.py
scitex-notebook convert-notebook experiment.ipynb --order dag -o dag-ordered.py
```
