#!/usr/bin/env python3
"""SciTeX Notebook CLI."""

from __future__ import annotations

import json as _json
import sys
from pathlib import Path

import click


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
)
@click.pass_context
def cli(ctx):
    """Jupyter notebook verification, compilation, and conversion.

    \b
    Commands:
      verify   Verify clew sessions for a notebook
      check    Find cells with untracked scitex.io calls
      compile  Compile execution history into a DAG
      convert  Convert .ipynb to .py with @stx.session

    \b
    Examples:
      scitex-notebook verify experiment.ipynb
      scitex-notebook check experiment.ipynb
      scitex-notebook compile experiment.ipynb --format mermaid
      scitex-notebook convert experiment.ipynb --mode unified -o out.py
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command("verify")
@click.argument("notebook", type=click.Path(exists=True, dir_okay=False))
@click.option("--json", "as_json", is_flag=True, help="Output JSON")
def verify_cmd(notebook, as_json):
    """Verify all clew sessions associated with a notebook."""
    from scitex_notebook import verify_notebook

    results = verify_notebook(notebook)
    if as_json:
        click.echo(_json.dumps(results, indent=2, default=str))
    else:
        if not results:
            click.echo("No clew sessions found for this notebook.")
            return
        for r in results:
            status = r.get("status", "?")
            sid = r.get("session_id", "?")
            verified = r.get("is_verified")
            click.echo(f"  {sid}  status={status}  verified={verified}")


@cli.command("check")
@click.argument("notebook", type=click.Path(exists=True, dir_okay=False))
@click.option("--json", "as_json", is_flag=True, help="Output JSON")
def check_cmd(notebook, as_json):
    """Find cells with scitex.io calls not wrapped in @stx.session."""
    from scitex_notebook import check_notebook

    issues = check_notebook(notebook)
    if as_json:
        click.echo(_json.dumps(issues, indent=2))
        return
    if not issues:
        click.echo("No untracked IO calls detected.")
        return
    for iss in issues:
        click.echo(
            f"  cell {iss['index']}: "
            f"load={iss['has_load']}  save={iss['has_save']}  "
            f"session={iss['has_session']}"
        )
    sys.exit(1)


@cli.command("compile")
@click.argument("notebook", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["mermaid", "script", "json"]),
    default="mermaid",
    help="Output format",
)
@click.option("-o", "--output", type=click.Path(), help="Output file path")
def compile_cmd(notebook, fmt, output):
    """Compile notebook execution history into a DAG."""
    from scitex_notebook import compile_notebook

    compiled = compile_notebook(notebook)

    if fmt == "mermaid":
        text = compiled.to_mermaid()
    elif fmt == "script":
        text = compiled.to_script()
    elif fmt == "json":
        text = _json.dumps(
            {
                "notebook_path": compiled.notebook_path,
                "execution_order": compiled.execution_order,
                "dag": compiled.dag,
            },
            indent=2,
            default=str,
        )
    else:
        raise click.UsageError(f"Unknown format: {fmt}")

    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(text, encoding="utf-8")
        click.echo(f"Wrote {output}")
    else:
        click.echo(text)


@cli.command("convert")
@click.argument("notebook", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--mode",
    type=click.Choice(["per_cell", "unified"]),
    default="per_cell",
    help="Conversion mode",
)
@click.option(
    "--order",
    type=click.Choice(["cell", "dag"]),
    default="cell",
    help="Cell ordering (per_cell mode only)",
)
@click.option("-o", "--output", type=click.Path(), help="Output .py path")
def convert_cmd(notebook, mode, order, output):
    """Convert a Jupyter notebook to a SciTeX Python script."""
    from scitex_notebook import convert_notebook

    script = convert_notebook(notebook, output=output, order=order, mode=mode)
    if not output:
        click.echo(script)


if __name__ == "__main__":
    cli()

# EOF
