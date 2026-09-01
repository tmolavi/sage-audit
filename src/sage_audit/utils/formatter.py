"""Report renderers: rich terminal, JSON, and Markdown.

(c) 2026 Taqi Molavi — https://molavi.pro — MIT License
"""

from __future__ import annotations

import json
from typing import Optional

from rich import box
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from sage_audit._version import __version__
from sage_audit.models import AuditReport, PillarReport

STATUS_ICON = {"pass": "✔", "warn": "⚠", "fail": "✖", "info": "ℹ"}
STATUS_STYLE = {"pass": "green", "warn": "yellow", "fail": "red", "info": "cyan"}
STATUS_EMOJI = {"pass": "✅", "warn": "⚠️", "fail": "❌", "info": "ℹ️"}


def score_color(score: float) -> str:
    if score >= 80:
        return "green"
    if score >= 60:
        return "yellow"
    return "red"


def score_bar(score: float, width: int = 24) -> str:
    filled = round(width * score / 100.0)
    return "█" * filled + "░" * (width - filled)


# ---------------------------------------------------------------------------
# Terminal (rich)
# ---------------------------------------------------------------------------

def _pillar_table(pillar: PillarReport) -> Table:
    color = score_color(pillar.score)
    table = Table(
        title=(
            f"[bold]{escape(pillar.name)}[/]  —  "
            f"[{color}]{pillar.score:.1f}/100 (Grade {pillar.grade})[/]"
        ),
        title_justify="left",
        box=box.ROUNDED,
        expand=True,
        highlight=True,
    )
    table.add_column("Check", ratio=3, overflow="fold")
    table.add_column("Status", justify="center", width=8)
    table.add_column("Wt", justify="right", width=5)
    table.add_column("Evidence", ratio=5, overflow="fold")
    for finding in pillar.findings:
        status = str(finding.status)
        icon = STATUS_ICON.get(status, "•")
        style = STATUS_STYLE.get(status, "white")
        table.add_row(
            escape(finding.title),
            Text(f"{icon} {status}", style=style),
            f"{finding.weight:.0f}" if finding.weight > 0 else "–",
            escape(finding.details),
        )
    return table


def _geo_metrics_line(pillar: PillarReport) -> Text:
    m = pillar.metrics
    csp = m.get("citation_survival_probability")
    csp_str = f"{csp:.1f}%" if csp is not None else "n/a"
    coverage = m.get("retrieval_coverage")
    coverage_str = f"{coverage:.0%}" if coverage is not None else "n/a"
    return Text(
        "  ▸ GEO simulation: "
        f"backend={m.get('embedding_backend', 'n/a')} · chunks={m.get('chunk_count', 0)} "
        f"(compliance {m.get('chunk_size_compliance', 0):.0%}) · "
        f"CSP={csp_str} · "
        f"entropy={m.get('avg_semantic_entropy', 'n/a')} · "
        f"coverage={coverage_str}",
        style="dim",
    )


def _recommendations_panel(report: AuditReport) -> Panel:
    lines: list[str] = []
    for pillar in (report.seo, report.aeo, report.geo):
        for finding in pillar.actionable()[:4]:
            status = str(finding.status)
            icon = STATUS_ICON.get(status, "•")
            style = STATUS_STYLE.get(status, "white")
            lines.append(
                f"[{style}]{icon}[/] [bold]{escape(finding.title)}[/] "
                f"[dim]({pillar.pillar.upper()})[/]\n    {escape(finding.recommendation)}"
            )
    body = "\n".join(lines[:10]) if lines else (
        "[green]Outstanding — no actionable issues. This page is SAGE-clean.[/]"
    )
    return Panel(
        body,
        title="[bold]Priority recommendations[/]",
        border_style="blue",
        padding=(1, 2),
    )


def render_terminal(report: AuditReport, console: Optional[Console] = None) -> None:
    """Pretty-print the full report to the terminal via rich."""

    console = console or Console()
    score = report.overall_score
    color = score_color(score)
    header = (
        f"[bold]{escape(report.url)}[/]\n"
        f"[dim]{report.audited_at:%Y-%m-%d %H:%M UTC} · {report.duration_ms:.0f} ms · "
        f"sage-audit v{__version__}[/]\n\n"
        f"[{color}]{score_bar(score)}[/{color}]  "
        f"[bold {color}]{score:.1f}/100[/]  "
        f"[bold {color}](Grade {report.grade})[/]"
    )
    console.print(
        Panel(header, title="[bold white]SAGE AUDIT REPORT[/]", border_style=color,
              padding=(1, 2))
    )
    page = report.page
    console.print(
        f"  [dim]HTTP {page.get('status_code') or 'offline'} · "
        f"{page.get('word_count', 0)} words · "
        f"T2C {page.get('text_to_code_ratio', 0.0):.0%} · "
        f"lang {page.get('language') or 'n/a'} · "
        f"JSON-LD {page.get('json_ld_blocks', 0)} block(s)[/]\n"
    )
    for pillar in (report.seo, report.aeo, report.geo):
        console.print(_pillar_table(pillar))
        if pillar.pillar == "geo":
            console.print(_geo_metrics_line(pillar))
        console.print()
    console.print(_recommendations_panel(report))
    if report.artifacts:
        names = ", ".join(sorted(report.artifacts))
        console.print(
            f"\n[dim]Artifacts generated: {escape(names)} — "
            "save with [bold]sage audit … --save-artifacts ./out[/][/]"
        )


# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------

def render_json(report: AuditReport) -> str:
    """Full machine-readable report (findings, metrics, artifacts)."""

    return json.dumps(report.to_dict(), indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------

def _md_escape(text: str) -> str:
    return (text or "").replace("|", "\\|").replace("\n", " ")


def render_markdown(report: AuditReport) -> str:
    """GitHub-friendly Markdown report."""

    lines: list[str] = []
    lines.append(f"# 🧭 SAGE Audit — {report.final_url or report.url}")
    lines.append("")
    lines.append(
        f"> **Overall score: {report.overall_score:.1f}/100 (Grade {report.grade})**  "
        f"\n> Audited {report.audited_at:%Y-%m-%d %H:%M UTC} · "
        f"{report.duration_ms:.0f} ms · sage-audit v{__version__}"
    )
    lines.append("")
    lines.append("| Pillar | Score | Grade |")
    lines.append("| --- | ---: | :---: |")
    for pillar in (report.seo, report.aeo, report.geo):
        lines.append(
            f"| {pillar.name} | **{pillar.score:.1f}** / 100 | {pillar.grade} |"
        )
    lines.append("")

    page = report.page
    lines.append("## Page snapshot")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Title | {_md_escape(str(page.get('title') or '—'))} |")
    lines.append(f"| HTTP status | {page.get('status_code') or 'offline (raw HTML)'} |")
    lines.append(f"| Words (clean text) | {page.get('word_count', 0)} |")
    lines.append(f"| Text-to-code ratio | {page.get('text_to_code_ratio', 0.0):.0%} |")
    lines.append(f"| Language | {page.get('language') or '—'} |")
    lines.append(f"| JSON-LD blocks | {page.get('json_ld_blocks', 0)} |")
    lines.append("")

    for pillar in (report.seo, report.aeo, report.geo):
        lines.append(f"## {pillar.name}")
        lines.append("")
        lines.append(f"**Score: {pillar.score:.1f}/100 (Grade {pillar.grade})**")
        lines.append("")
        lines.append("| Check | Status | Weight | Evidence |")
        lines.append("| --- | :---: | ---: | --- |")
        for finding in pillar.findings:
            status = str(finding.status)
            lines.append(
                f"| {_md_escape(finding.title)} | {STATUS_EMOJI.get(status, status)} "
                f"{status} | {finding.weight:.0f} | {_md_escape(finding.details)} |"
            )
        lines.append("")
        if pillar.pillar == "geo":
            m = pillar.metrics
            csp = m.get("citation_survival_probability")
            lines.append("**GEO simulation metrics**")
            lines.append("")
            lines.append(f"- Embedding backend: `{m.get('embedding_backend')}`")
            lines.append(
                f"- Chunks: {m.get('chunk_count')} "
                f"(compliance {m.get('chunk_size_compliance', 0):.0%})"
            )
            lines.append(
                f"- Citation Survival Probability: "
                f"**{f'{csp:.1f}%' if csp is not None else 'n/a'}**"
            )
            lines.append(f"- Avg semantic entropy: {m.get('avg_semantic_entropy')}")
            coverage = m.get("retrieval_coverage")
            lines.append(
                f"- Retrieval coverage: "
                f"{f'{coverage:.0%}' if coverage is not None else 'n/a'}"
            )
            lines.append("")

    recommendations: list[tuple[str, str, str]] = []
    for pillar in (report.seo, report.aeo, report.geo):
        for finding in pillar.actionable():
            recommendations.append((pillar.pillar.upper(), finding.title, finding.recommendation))
    lines.append("## Priority recommendations")
    lines.append("")
    if recommendations:
        for label, title, rec in recommendations[:10]:
            lines.append(f"- **[{label}] {title}** — {rec}")
    else:
        lines.append("Outstanding — no actionable issues. This page is SAGE-clean. ✅")
    lines.append("")

    if report.artifacts:
        lines.append("## Generated artifacts")
        lines.append("")
        for name in sorted(report.artifacts):
            lines.append(f"### `{name}`")
            lines.append("")
            fence = "markdown" if name.endswith(".txt") else "json"
            lines.append(f"```{fence}")
            lines.append(report.artifacts[name].rstrip())
            lines.append("```")
            lines.append("")

    lines.append("---")
    lines.append(
        "Generated by [sage-audit](https://github.com/tmolavi/sage-audit) "
        f"v{__version__} — by [Taqi Molavi](https://molavi.pro), MIT License."
    )
    return "\n".join(lines) + "\n"
