"""`sage` — the SAGE command-line interface.

Commands:
    sage audit <url>          run the full 3-pillar audit
    sage audit --raw-html f   audit a local HTML file (offline)
    sage generate-llms <url>  emit an optimized llms.txt
    sage mcp                  start the FastMCP server for AI agents

(c) 2026 Taqi Molavi — https://molavi.pro — MIT License
"""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.markup import escape

from sage_audit._version import __version__
from sage_audit.core import SageAuditor
from sage_audit.utils.extractor import FetchError
from sage_audit.utils.formatter import (
    render_json,
    render_markdown,
    render_terminal,
)

BANNER = "SAGE — Search, Answer, & Generative Engine Auditor"

err_console = Console(stderr=True)


def _build_auditor(
    timeout: float, embedding_backend: str, top_k: int, no_robots: bool
) -> SageAuditor:
    return SageAuditor(
        timeout=timeout,
        fetch_robots=not no_robots,
        embedding_backend=embedding_backend,
        top_k=top_k,
    )


def _common_options(func):
    func = click.option(
        "--embedding-backend",
        type=click.Choice(["auto", "fastembed", "sentence-transformers", "hashing"]),
        default="auto",
        show_default=True,
        help="Vector backend for the GEO retrieval simulation.",
    )(func)
    func = click.option(
        "--timeout", type=float, default=20.0, show_default=True,
        help="Per-request network timeout (seconds).",
    )(func)
    return func


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, "-V", "--version", prog_name="sage-audit")
def main() -> None:
    """SAGE (sage-audit) — the Unified 3-Pillar Audit Engine for SEO, Entity
    AEO, and Generative Engine Optimization (GEO).

    \b
    Examples:
      sage audit https://molavi.pro
      sage audit https://molavi.pro --format markdown -o report.md
      sage audit --raw-html page.html --format json | jq .overall_score
      sage generate-llms https://molavi.pro -o llms.txt
      sage mcp                    # serve AI agents via Model Context Protocol
    """


@main.command()
@click.argument("target", required=False)
@click.option(
    "--raw-html",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Audit a local HTML file instead of fetching a live URL.",
)
@click.option(
    "--base-url",
    default=None,
    help="Logical URL to attribute when using --raw-html.",
)
@click.option(
    "--format", "fmt",
    type=click.Choice(["terminal", "json", "markdown"]),
    default="terminal",
    show_default=True,
    help="Report rendering format.",
)
@click.option(
    "--output", "-o",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Write the report to a file (JSON/Markdown per --format).",
)
@click.option(
    "--save-artifacts",
    type=click.Path(file_okay=False, path_type=Path),
    help="Directory to write llms.txt and rag_ready_chunks.json into.",
)
@click.option("--top-k", type=int, default=3, show_default=True,
              help="Simulated RAG top-k retrieval depth.")
@click.option("--no-robots", is_flag=True, help="Skip robots.txt fetching.")
@click.option(
    "--fail-under",
    type=float,
    default=None,
    metavar="SCORE",
    help="Exit 1 when the overall score is below SCORE (CI quality gates).",
)
@_common_options
def audit(
    target: str | None,
    raw_html: Path | None,
    base_url: str | None,
    fmt: str,
    output: Path | None,
    save_artifacts: Path | None,
    top_k: int,
    no_robots: bool,
    fail_under: float | None,
    embedding_backend: str,
    timeout: float,
) -> None:
    """Run the full SAGE 3-pillar audit against TARGET (a URL)."""

    if not target and not raw_html:
        raise click.UsageError("Provide a URL (e.g. `sage audit https://site.com`) "
                               "or `--raw-html page.html`.")
    if target and raw_html:
        raise click.UsageError("TARGET and --raw-html are mutually exclusive.")

    auditor = _build_auditor(timeout, embedding_backend, top_k, no_robots)
    spinner = err_console if fmt != "terminal" else Console(stderr=True)
    try:
        with spinner.status(f"[bold cyan]{BANNER}[/] — auditing…", spinner="dots"):
            if raw_html:
                report = auditor.audit_html(
                    raw_html.read_text(encoding="utf-8", errors="replace"),
                    url=base_url or "https://example.local/",
                )
            else:
                report = auditor.audit(str(target))
    except FetchError as exc:
        err_console.print(f"[red]✖ Fetch failed:[/] {escape(str(exc))}")
        sys.exit(2)

    if fmt == "terminal":
        render_terminal(report)
        if output:
            output.write_text(render_markdown(report), encoding="utf-8")
            err_console.print(f"[green]✔ Markdown report written to {output}[/]")
    else:
        payload = render_json(report) if fmt == "json" else render_markdown(report)
        if output:
            output.write_text(payload, encoding="utf-8")
            err_console.print(f"[green]✔ Report written to {output}[/]")
        else:
            click.echo(payload)

    if save_artifacts:
        save_artifacts.mkdir(parents=True, exist_ok=True)
        for name, content in report.artifacts.items():
            destination = save_artifacts / name
            destination.write_text(content, encoding="utf-8")
            err_console.print(f"[green]✔ Artifact saved: {destination}[/]")

    if fail_under is not None and report.overall_score < fail_under:
        err_console.print(
            f"[red]✖ Overall score {report.overall_score:.1f} is below the "
            f"--fail-under gate ({fail_under:.1f}).[/]"
        )
        sys.exit(1)


@main.command("generate-llms")
@click.argument("target")
@click.option("--output", "-o", type=click.Path(dir_okay=False, path_type=Path),
              help="Write llms.txt to this path (default: stdout).")
@click.option("--also-chunks", is_flag=True,
              help="Also write rag_ready_chunks.json next to --output.")
@_common_options
def generate_llms(
    target: str,
    output: Path | None,
    also_chunks: bool,
    embedding_backend: str,
    timeout: float,
) -> None:
    """Generate an optimized llms.txt for TARGET (llmstxt.org convention)."""

    auditor = _build_auditor(timeout, embedding_backend, top_k=3, no_robots=False)
    try:
        with err_console.status("[bold cyan]Analyzing page & synthesizing llms.txt…[/]",
                                spinner="dots"):
            report = auditor.audit(target)
    except FetchError as exc:
        err_console.print(f"[red]✖ Fetch failed:[/] {escape(str(exc))}")
        sys.exit(2)

    llms_txt = report.artifacts["llms.txt"]
    if output:
        output.write_text(llms_txt, encoding="utf-8")
        err_console.print(f"[green]✔ llms.txt written to {output}[/]")
        if also_chunks:
            chunks_path = output.with_name("rag_ready_chunks.json")
            chunks_path.write_text(report.artifacts["rag_ready_chunks.json"],
                                   encoding="utf-8")
            err_console.print(f"[green]✔ rag_ready_chunks.json written to {chunks_path}[/]")
    else:
        click.echo(llms_txt)


@main.command(name="mcp")
@click.option("--transport",
              type=click.Choice(["stdio", "sse", "streamable-http"]),
              default="stdio", show_default=True,
              help="MCP transport (stdio for Claude Desktop / Cursor).")
@click.option("--host", default="127.0.0.1", show_default=True,
              help="Bind host for HTTP transports.")
@click.option("--port", default=8642, type=int, show_default=True,
              help="Bind port for HTTP transports.")
def mcp_command(transport: str, host: str, port: int) -> None:
    """Start the SAGE Model Context Protocol server (FastMCP).

    Exposes sage_audit_url / sage_audit_html / sage_generate_llms_txt as
    autonomous tools for Claude Desktop, Cursor and other MCP clients.
    """

    try:
        from sage_audit.server.mcp_server import create_server

        server = create_server(host=host, port=port)
    except RuntimeError as exc:
        err_console.print(f"[red]✖[/] {escape(str(exc))}")
        sys.exit(2)
    err_console.print(
        f"[bold cyan]{BANNER}[/] — MCP server on [bold]{transport}[/]"
        + (f" ({host}:{port})" if transport != "stdio" else "")
    )
    server.run(transport=transport)


if __name__ == "__main__":  # pragma: no cover
    main()
