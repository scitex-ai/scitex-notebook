#!/usr/bin/env python3
"""SciTeX Notebook CLI."""

from __future__ import annotations

import json as _json
import sys
from pathlib import Path

import click


def _get_version() -> str:
    try:
        from importlib.metadata import version

        return version("scitex-notebook")
    except Exception:
        return "0.0.0"


def _show_recursive_help(ctx: click.Context) -> None:
    click.echo(ctx.get_help())
    click.echo()
    group = ctx.command
    if isinstance(group, click.Group):
        for name in sorted(group.list_commands(ctx)):
            cmd = group.get_command(ctx, name)
            if cmd is None or cmd.hidden:
                continue
            sub_ctx = click.Context(cmd, parent=ctx, info_name=name)
            click.echo(f"{'=' * 60}")
            click.echo(f"Command: {name}")
            click.echo(f"{'=' * 60}")
            click.echo(sub_ctx.get_help())
            click.echo()


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
)
@click.version_option(version=_get_version(), prog_name="scitex-notebook")
@click.option("--help-recursive", is_flag=True, help="Show help for all subcommands.")
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Emit structured JSON output (propagates to subcommands that honour it).",
)
@click.pass_context
def cli(ctx, help_recursive, as_json):
    """Jupyter notebook verification, compilation, and conversion.

    \b
    Config is loaded with the SciTeX precedence chain:
      config.yaml -> $SCITEX_NOTEBOOK_CONFIG -> ~/.scitex/notebook/config.yaml -> defaults

    \b
    Commands:
      verify-notebook   Verify clew sessions for a notebook
      check-notebook    Find cells with untracked scitex.io calls
      compile-notebook  Compile execution history into a DAG
      convert-notebook  Convert .ipynb to .py with @stx.session

    \b
    Examples:
      scitex-notebook verify-notebook experiment.ipynb
      scitex-notebook check-notebook experiment.ipynb
      scitex-notebook compile-notebook experiment.ipynb --format mermaid
      scitex-notebook convert-notebook experiment.ipynb --mode unified -o out.py
    """
    ctx.ensure_object(dict)
    ctx.obj["as_json"] = as_json
    if help_recursive:
        _show_recursive_help(ctx)
        ctx.exit(0)
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


def _deprecated_redirect(old: str, new: str):
    """Build a hidden Click command that exits 2 with a re-run hint."""

    @click.pass_context
    def _impl(ctx, **_):
        click.echo(
            f"error: `scitex-notebook {old}` was renamed to `scitex-notebook {new}`.\n"
            f"Re-run with: scitex-notebook {new} <args>",
            err=True,
        )
        ctx.exit(2)

    cmd = click.command(
        old,
        hidden=True,
        context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
    )(_impl)
    return cmd


cli.add_command(_deprecated_redirect("verify", "verify-notebook"))
cli.add_command(_deprecated_redirect("check", "check-notebook"))
cli.add_command(_deprecated_redirect("compile", "compile-notebook"))
cli.add_command(_deprecated_redirect("convert", "convert-notebook"))


@cli.command("verify-notebook")
@click.argument("notebook", type=click.Path(exists=True, dir_okay=False))
@click.option("--json", "as_json", is_flag=True, help="Output JSON")
def verify_notebook_cmd(notebook, as_json):
    """Verify all clew sessions associated with a notebook.

    \b
    Example:
      $ scitex-notebook verify-notebook experiment.ipynb
      $ scitex-notebook verify-notebook experiment.ipynb --json
    """
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


@cli.command("check-notebook")
@click.argument("notebook", type=click.Path(exists=True, dir_okay=False))
@click.option("--json", "as_json", is_flag=True, help="Output JSON")
def check_notebook_cmd(notebook, as_json):
    """Find cells with scitex.io calls not wrapped in @stx.session.

    \b
    Example:
      $ scitex-notebook check-notebook experiment.ipynb
      $ scitex-notebook check-notebook experiment.ipynb --json
    """
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


@cli.command("compile-notebook")
@click.argument("notebook", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["mermaid", "script", "json"]),
    default="mermaid",
    help="Output format",
)
@click.option("-o", "--output", type=click.Path(), help="Output file path")
@click.option("--dry-run", is_flag=True, help="Print compile plan without writing.")
@click.option(
    "-y", "--yes", is_flag=True, help="Suppress interactive confirmation (assume yes)."
)
def compile_notebook_cmd(notebook, fmt, output, dry_run, yes):
    """Compile notebook execution history into a DAG.

    \b
    Example:
      $ scitex-notebook compile-notebook experiment.ipynb
      $ scitex-notebook compile-notebook experiment.ipynb --format script -o pipeline.py
      $ scitex-notebook compile-notebook experiment.ipynb --dry-run
    """
    if dry_run:
        click.echo(
            f"DRY RUN — would compile {notebook} (format={fmt}, output={output or 'stdout'})"
        )
        return
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


@cli.command("convert-notebook")
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
@click.option("--dry-run", is_flag=True, help="Print convert plan without writing.")
@click.option(
    "-y", "--yes", is_flag=True, help="Suppress interactive confirmation (assume yes)."
)
def convert_notebook_cmd(notebook, mode, order, output, dry_run, yes):
    """Convert a Jupyter notebook to a SciTeX Python script.

    \b
    Example:
      $ scitex-notebook convert-notebook experiment.ipynb -o experiment.py
      $ scitex-notebook convert-notebook experiment.ipynb --mode unified -o uni.py
      $ scitex-notebook convert-notebook experiment.ipynb --dry-run
    """
    if dry_run:
        click.echo(
            f"DRY RUN — would convert {notebook} (mode={mode}, output={output or 'stdout'})"
        )
        return
    from scitex_notebook import convert_notebook

    script = convert_notebook(notebook, output=output, order=order, mode=mode)
    if not output:
        click.echo(script)


# -- Introspection ----------------------------------------------------------


@cli.command("list-python-apis")
@click.option("-v", "--verbose", count=True, help="-v names, -vv +sigs, -vvv +docs")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def list_python_apis(verbose, as_json):
    """List public Python APIs in scitex-notebook.

    \b
    Example:
      $ scitex-notebook list-python-apis
      $ scitex-notebook list-python-apis -vv
      $ scitex-notebook list-python-apis --json
    """
    import inspect

    import scitex_notebook

    names = sorted(getattr(scitex_notebook, "__all__", []))
    apis = []
    for name in names:
        obj = getattr(scitex_notebook, name, None)
        if obj is None:
            continue
        entry = {"name": name, "type": type(obj).__name__}
        if callable(obj):
            try:
                entry["signature"] = str(inspect.signature(obj))
            except (TypeError, ValueError):
                pass
        doc = inspect.getdoc(obj) or ""
        if doc:
            entry["doc"] = doc.strip().split("\n")[0]
        apis.append(entry)

    if as_json:
        click.echo(_json.dumps({"module": "scitex_notebook", "apis": apis}, indent=2))
        return

    click.secho("scitex_notebook Python APIs", fg="cyan", bold=True)
    for api in apis:
        sig = api.get("signature", "")
        click.echo(f"  {click.style(api['name'], fg='green')}{sig}")
        if verbose >= 2 and api.get("doc"):
            click.echo(f"    {api['doc']}")


# -- MCP --------------------------------------------------------------------


@cli.group(invoke_without_command=True)
@click.pass_context
def mcp(ctx):
    """MCP (Model Context Protocol) server commands."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@mcp.command("start")
@click.option("--dry-run", is_flag=True, help="Print launch plan without starting.")
@click.option(
    "-y", "--yes", is_flag=True, help="Suppress interactive confirmation (assume yes)."
)
def mcp_start(dry_run, yes):
    """Start the scitex-notebook MCP server.

    \b
    Example:
      $ scitex-notebook mcp start
      $ scitex-notebook mcp start --dry-run
    """
    if dry_run:
        click.echo("DRY RUN — would start scitex-notebook MCP server (stdio transport)")
        return
    from scitex_notebook.mcp_server import main as mcp_main

    mcp_main()


@mcp.command("list-tools")
@click.option("-v", "--verbose", count=True, help="Verbosity: -v +desc, -vv full doc")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def mcp_list_tools(verbose, as_json):
    """List available MCP tools.

    \b
    Example:
      $ scitex-notebook mcp list-tools
      $ scitex-notebook mcp list-tools -vv
      $ scitex-notebook mcp list-tools --json
    """
    from scitex_notebook._mcp.tool_schemas import get_tool_schemas

    tools = get_tool_schemas()

    if as_json:
        payload = {
            "total": len(tools),
            "tools": [
                {
                    "name": getattr(t, "name", str(t)),
                    "description": getattr(t, "description", "") or "",
                }
                for t in tools
            ],
        }
        click.echo(_json.dumps(payload, indent=2))
        return

    click.secho(f"scitex-notebook MCP: {len(tools)} tools", fg="cyan", bold=True)
    for t in sorted(tools, key=lambda x: getattr(x, "name", str(x))):
        name = getattr(t, "name", str(t))
        desc = getattr(t, "description", "") or ""
        click.echo(f"  {name}")
        if verbose >= 1 and desc:
            line = desc.split("\n")[0] if verbose == 1 else desc.strip()
            click.echo(f"    {line}")


if __name__ == "__main__":
    cli()

# EOF
