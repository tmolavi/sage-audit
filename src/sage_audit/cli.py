"""`sage` — the SAGE command-line interface.

Commands:
    sage audit <url>          run the full 3-pillar audit with Evidence Taxonomy
    sage audit --raw-html f   audit a local HTML file (offline)
    sage generate-llms <url>  emit an optimized llms.txt with CSP metadata
    sage validate             validate SAGE/CSP predictions against empirical observations
    sage mcp                  start the FastMCP server for AI agents

(c) 2026 Taqi Molavi — https://molavi.pro — MIT License
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.markup import escape

from sage_audit._version import __version__
from sage_audit.config import SageConfig
from sage_audit.core import SageAuditor
from sage_audit.utils.extractor import FetchError
from sage_audit.utils.formatter import (
    render_json,
    render_markdown,
    render_terminal,
)
from sage_audit.validation import evaluate_sage_vs_observed

BANNER = "SAGE — Search, Answer, & Generative Engine Auditor"

err_console = Console(stderr=True)


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
    Features:
      - Epistemic Evidence Taxonomy (E0–E5) on all audit checks
      - Hardened Citation Survival Proxy (CSP) heuristic metrics
      - Configurable heuristic thresholds
      - Empirical validation & calibration framework

    \b
    Examples:
      sage audit https://molavi.pro
      sage audit https://molavi.pro --format markdown -o report.md
      sage audit --raw-html page.html --format json | jq .overall_score
      sage generate-llms https://molavi.pro -o llms.txt
      sage validate --predictions preds.json --observations obs.json
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
    "--chunk-min-tokens", type=int, default=60, show_default=True,
    help="Minimum token boundary for semantic chunking.",
)
@click.option(
    "--chunk-max-tokens", type=int, default=120, show_default=True,
    help="Maximum token boundary for semantic chunking.",
)
@click.option(
    "--config-file", type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to JSON file containing SageConfig threshold overrides.",
)
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
    chunk_min_tokens: int,
    chunk_max_tokens: int,
    config_file: Path | None,
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

    cfg = SageConfig(
        timeout=timeout,
        fetch_robots=not no_robots,
        embedding_backend=embedding_backend,
        top_k=top_k,
        chunk_min_tokens=chunk_min_tokens,
        chunk_max_tokens=chunk_max_tokens,
    )
    if config_file:
        try:
            overrides = json.loads(config_file.read_text(encoding="utf-8"))
            cfg = cfg.update_from_dict(overrides)
        except Exception as exc:
            err_console.print(f"[red]✖ Failed to parse config file:[/] {escape(str(exc))}")
            sys.exit(2)

    auditor = SageAuditor(config=cfg)
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

    cfg = SageConfig(timeout=timeout, embedding_backend=embedding_backend, top_k=3, fetch_robots=False)
    auditor = SageAuditor(config=cfg)
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


@main.command("validate")
@click.option(
    "--predictions", "-p",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help="JSON file containing array of predicted SAGE or CSP scores.",
)
@click.option(
    "--observations", "-o",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help="JSON file containing array of binary observed citation outcomes (1/0).",
)
@click.option("--dataset-name", default="benchmark-dataset", help="Name of validation dataset.")
@click.option("--k", type=int, default=5, show_default=True, help="Cutoff k for Precision@k.")
def validate_command(predictions: Path, observations: Path, dataset_name: str, k: int) -> None:
    """Validate SAGE or CSP scores against real observed AI citation outcomes."""
    try:
        preds = json.loads(predictions.read_text(encoding="utf-8"))
        obs = json.loads(observations.read_text(encoding="utf-8"))
    except Exception as exc:
        err_console.print(f"[red]✖ Failed to read input files:[/] {escape(str(exc))}")
        sys.exit(2)

    result = evaluate_sage_vs_observed(preds, obs, k=k, dataset_name=dataset_name)
    click.echo(json.dumps(result.to_dict(), indent=2))


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
