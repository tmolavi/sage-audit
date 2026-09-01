"""Unit tests for sage-audit — SEO, AEO, GEO pillars, extractor, formatter,
core orchestrator and CLI. All tests are offline and deterministic.

(c) 2026 Taqi Molavi — https://molavi.pro — MIT License
"""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from sage_audit import SageAuditor, __version__
from sage_audit.auditors.aeo_auditor import (
    AeoAuditor,
    answer_quality,
    flatten_same_as,
    is_question_heading,
    iter_entity_nodes,
)
from sage_audit.auditors.geo_auditor import (
    GeoAuditor,
    HashingVectorBackend,
    build_llms_txt,
    build_queries,
    chunk_sections,
    resolve_backend,
    simulate_rag,
)
from sage_audit.auditors.seo_auditor import (
    SeoAuditor,
    ai_crawler_verdicts,
    parse_robots,
)
from sage_audit.cli import main as cli
from sage_audit.core import audit_url  # noqa: F401  (import smoke)
from sage_audit.models import grade_for
from sage_audit.utils.extractor import Section, ensure_url, parse_snapshot
from sage_audit.utils.formatter import render_json, render_markdown, render_terminal
from sage_audit.utils.text import (
    count_tokens,
    cosine_similarity,
    normalized_softmax_entropy,
    split_sentences,
)

BASE_URL = "https://acme-analytics.example.com/"

SAMPLE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Acme Analytics — Real-Time Data Platform</title>
<meta name="description" content="Acme Analytics is a real-time data platform that ingests, processes and visualizes streaming events for product teams around the world.">
<link rel="canonical" href="https://acme-analytics.example.com/">
<meta name="robots" content="index,follow">
<meta property="og:title" content="Acme Analytics — Real-Time Data Platform">
<meta property="og:description" content="Real-time streaming analytics for product teams.">
<meta property="og:image" content="https://acme-analytics.example.com/og.png">
<meta property="og:type" content="website">
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://acme-analytics.example.com/#org",
      "name": "Acme Analytics",
      "url": "https://acme-analytics.example.com/",
      "logo": "https://acme-analytics.example.com/logo.png",
      "description": "Real-time data platform for streaming events.",
      "sameAs": [
        "https://www.wikidata.org/wiki/Q123456",
        "https://en.wikipedia.org/wiki/Acme_Analytics",
        "https://www.linkedin.com/company/acme-analytics",
        "https://twitter.com/acmeanalytics"
      ]
    },
    {"@type": "WebSite", "name": "Acme Analytics", "url": "https://acme-analytics.example.com/"},
    {
      "@type": "FAQPage",
      "mainEntity": [
        {"@type": "Question", "name": "What is Acme Analytics?",
         "acceptedAnswer": {"@type": "Answer", "text": "Acme Analytics is a real-time data platform that processes 2 million events per second."}},
        {"@type": "Question", "name": "How much does Acme Analytics cost?",
         "acceptedAnswer": {"@type": "Answer", "text": "Acme Analytics costs 0.40 USD per million events on the self-serve plan."}}
      ]
    },
    {
      "@type": "Article",
      "headline": "Acme Analytics Benchmark Report 2026",
      "datePublished": "2026-01-15",
      "dateModified": "2026-06-20",
      "author": {"@type": "Person", "name": "Jane Doe", "sameAs": "https://github.com/janedoe"}
    }
  ]
}
</script>
</head>
<body>
<header><nav><a href="/">Home</a> <a href="https://external.example.com/x">Docs</a></nav></header>
<main>
<h1>Acme Analytics: Real-Time Answers for Product Teams</h1>
<p>Acme Analytics is a real-time data platform that ingests, processes, and
visualizes streaming events for product teams. The platform processes more
than 2 million events per second and answers queries in under 120
milliseconds on commodity hardware. Founded in 2021, Acme Analytics serves
3,400 companies across 40 countries, and it integrates with 120 data
sources through native connectors and an open API.</p>

<h2>What is Acme Analytics?</h2>
<p>Acme Analytics is a streaming analytics engine that turns raw event data
into answers within 120 milliseconds. It is built on a columnar storage
layer, a distributed query planner, and exactly-once ingestion, so
dashboards stay accurate even at 2 million events per second. In 2025 the
platform processed 18 trillion events for customers in fintech, gaming, and
retail, including 9 of the 50 largest online marketplaces.</p>

<h2>How much does Acme Analytics cost?</h2>
<p>Acme Analytics costs 0.40 USD per million ingested events on the
self-serve plan, and the enterprise plan starts at 2,900 USD per month.
There are no per-seat fees, and the free tier includes 10 million events
per month with full API access. A 14-day trial is available without a
credit card, and annual contracts include a 20 percent discount and
dedicated support with a 15-minute response time.</p>

<h2>Why choose Acme Analytics?</h2>
<p>Acme Analytics delivers 99.99 percent uptime, end-to-end encryption, and
SOC 2 Type II compliance. Unlike batch warehouses that refresh hourly,
Acme Analytics updates every dashboard in real time, which lets on-call
teams detect revenue-impacting incidents 11 times faster according to a
2025 benchmark of 240 production deployments.</p>

<h2>Integration and SDKs</h2>
<p>Acme Analytics ships SDKs for Python, JavaScript, Go, and Rust, and each
SDK is versioned in lockstep with the API. The Python SDK installs with pip
and sends its first event in four lines of code. Terraform modules, a
Grafana plugin, and webhooks are included, and 92 percent of new accounts
stream their first event within 9 minutes of signup.</p>
</main>
<footer>© 2026 Acme Analytics</footer>
</body>
</html>
"""

SAMPLE_HEADERS = {
    "content-type": "text/html; charset=utf-8",
    "strict-transport-security": "max-age=63072000",
    "content-security-policy": "default-src 'self'; frame-ancestors 'self'",
    "x-content-type-options": "nosniff",
    "cache-control": "public, max-age=3600",
    "etag": '"abc123"',
}

SAMPLE_ROBOTS = """# robots.txt for acme-analytics.example.com
User-agent: GPTBot
Disallow: /

User-agent: ClaudeBot
Disallow: /private/

User-agent: *
Disallow: /staging/
"""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def snapshot():
    return parse_snapshot(BASE_URL, SAMPLE_HTML, status_code=0)


@pytest.fixture(scope="module")
def live_like_snapshot():
    return parse_snapshot(
        BASE_URL,
        SAMPLE_HTML,
        status_code=200,
        headers=SAMPLE_HEADERS,
        final_url=BASE_URL,
        robots_txt=SAMPLE_ROBOTS,
        fetch_ms=123.4,
    )


@pytest.fixture(scope="module")
def report():
    return SageAuditor(embedding_backend="hashing").audit_html(SAMPLE_HTML, url=BASE_URL)


def _finding(pillar_report, check_id):
    for finding in pillar_report.findings:
        if finding.check_id == check_id:
            return finding
    raise AssertionError(f"finding {check_id} not found")


# ---------------------------------------------------------------------------
# text utilities
# ---------------------------------------------------------------------------

def test_count_tokens_basic():
    assert count_tokens("hello world!") == 3
    assert count_tokens("") == 0
    assert count_tokens("یک دو سه") == 3  # Persian words tokenize


def test_split_sentences_multilingual():
    parts = split_sentences("One sentence. Another one? A third! آخرین؟ بله")
    assert parts[0].startswith("One")
    assert len(parts) >= 4


def test_cosine_similarity_identical_and_orthogonal():
    assert cosine_similarity([1.0, 2.0], [1.0, 2.0]) == pytest.approx(1.0)
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)
    assert cosine_similarity([], [1.0]) == 0.0


def test_entropy_bounds():
    assert normalized_softmax_entropy([0.5]) == 0.0
    assert normalized_softmax_entropy([0.25, 0.25, 0.25, 0.25]) == pytest.approx(1.0)
    peaked = normalized_softmax_entropy([1.0, 0.0, 0.0], temperature=0.1)
    flat = normalized_softmax_entropy([1.0, 0.9, 0.8], temperature=0.1)
    assert peaked < 0.15
    assert flat > peaked


def test_grade_for_thresholds():
    assert grade_for(95) == "A+"
    assert grade_for(85) == "A"
    assert grade_for(80) == "B"
    assert grade_for(66) == "C"
    assert grade_for(55) == "D"
    assert grade_for(12) == "F"


def test_ensure_url():
    assert ensure_url("example.com") == "https://example.com"
    assert ensure_url("http://a.io") == "http://a.io"


# ---------------------------------------------------------------------------
# extractor
# ---------------------------------------------------------------------------

def test_extractor_head_signals(snapshot):
    assert snapshot.title == "Acme Analytics — Real-Time Data Platform"
    assert snapshot.canonical == BASE_URL
    assert snapshot.meta_robots == "index,follow"
    assert snapshot.language == "en"
    assert snapshot.meta_description and len(snapshot.meta_description) >= 70
    assert snapshot.open_graph.get("image", "").endswith("og.png")


def test_extractor_body_structure(snapshot):
    assert snapshot.text_to_code_ratio > 0.05
    assert snapshot.word_count > 250
    assert snapshot.token_count > snapshot.word_count
    h1s = [t for lvl, t in snapshot.headings if lvl == 1]
    assert len(h1s) == 1
    assert len(snapshot.sections) >= 4
    assert all(s.word_count >= 8 for s in snapshot.sections)


def test_extractor_json_ld(snapshot):
    assert len(snapshot.json_ld) == 1
    assert snapshot.json_ld_errors == 0
    nodes = list(iter_entity_nodes(snapshot.json_ld))
    types: set[str] = set()
    for node in nodes:
        raw = node["@type"]
        types.update([raw] if isinstance(raw, str) else list(raw))
    assert {"Organization", "FAQPage", "Article", "Person"} <= types


def test_extractor_links(snapshot):
    assert snapshot.links_internal >= 1
    assert snapshot.links_external >= 1


# ---------------------------------------------------------------------------
# SEO pillar
# ---------------------------------------------------------------------------

def test_robots_parser_and_ai_verdicts():
    groups = parse_robots(SAMPLE_ROBOTS)
    assert ("disallow", "/") in groups["gptbot"]
    verdicts = ai_crawler_verdicts(SAMPLE_ROBOTS)
    assert verdicts["GPTBot"] == "blocked"
    assert verdicts["ClaudeBot"] == "allowed"  # only /private/ disallowed
    assert verdicts["PerplexityBot"] == "allowed"  # falls back to '*'


def test_seo_pillar_scores(snapshot):
    seo = SeoAuditor().audit(snapshot)
    assert 0 <= seo.score <= 100
    assert _finding(seo, "seo.canonical").status == "pass"
    assert _finding(seo, "seo.meta_robots").status == "pass"
    assert _finding(seo, "seo.open_graph").status == "pass"
    assert _finding(seo, "seo.http_status").weight == 0  # offline info only
    robots = _finding(seo, "seo.robots_ai_crawlers")
    assert robots.weight == 0 and robots.status == "info"


def test_seo_pillar_live_headers(live_like_snapshot):
    seo = SeoAuditor().audit(live_like_snapshot)
    assert _finding(seo, "seo.http_status").status == "pass"
    assert _finding(seo, "seo.security_headers").score >= 0.99
    assert _finding(seo, "seo.cache_headers").status == "pass"
    robots = _finding(seo, "seo.robots_ai_crawlers")
    assert robots.status == "warn"  # GPTBot blocked
    assert "GPTBot: blocked" in robots.details


def test_seo_noindex_is_critical():
    html = SAMPLE_HTML.replace('content="index,follow"', 'content="noindex"')
    snap = parse_snapshot(BASE_URL, html)
    seo = SeoAuditor().audit(snap)
    assert _finding(seo, "seo.meta_robots").status == "fail"


# ---------------------------------------------------------------------------
# AEO pillar
# ---------------------------------------------------------------------------

def test_is_question_heading():
    assert is_question_heading("What is Acme Analytics?")
    assert is_question_heading("How much does it cost?")
    assert is_question_heading("چرا باید استفاده کنم؟")
    assert not is_question_heading("Integration and SDKs")


def test_answer_quality_definitional_section(snapshot):
    section = next(s for s in snapshot.sections if s.heading == "What is Acme Analytics?")
    score, note = answer_quality(section)
    assert score >= 0.6, note
    assert "definitional=✓" in note


def test_answer_quality_fluff_penalty():
    section = Section(
        heading="Intro",
        level=2,
        text=("Welcome to our blog! In this article we will explore many things. "
              "At the end of the day, as we all know, content is really quite important "
              "for everybody in the modern digital age of marketing."),
        word_count=38,
    )
    score, note = answer_quality(section)
    assert score < 0.4, note
    assert "fluff" in note


def test_aeo_pillar(snapshot):
    aeo = AeoAuditor().audit(snapshot)
    assert aeo.score >= 60
    assert _finding(aeo, "aeo.jsonld_presence").status == "pass"
    assert _finding(aeo, "aeo.authority_sameas").status == "pass"
    assert _finding(aeo, "aeo.faq_structuring").status == "pass"
    density = _finding(aeo, "aeo.direct_answer_density")
    assert density.score >= 0.55, density.details
    assert _finding(aeo, "aeo.freshness").status == "pass"


def test_aeo_empty_schema():
    snap = parse_snapshot(BASE_URL, "<html><body><p>Hi there.</p></body></html>")
    aeo = AeoAuditor().audit(snap)
    assert _finding(aeo, "aeo.jsonld_presence").status == "fail"
    assert _finding(aeo, "aeo.entity_graph").status == "fail"
    assert flatten_same_as(iter_entity_nodes(snap.json_ld)) == []


# ---------------------------------------------------------------------------
# GEO pillar
# ---------------------------------------------------------------------------

def test_chunker_bounds(snapshot):
    chunks = chunk_sections(snapshot.sections, min_tokens=60, max_tokens=120, overlap=25)
    assert 2 <= len(chunks) <= 6
    assert all(c.token_count <= 120 + 60 // 2 for c in chunks)
    assert all(c.id == f"chunk-{c.index:03d}" for c in chunks)
    joined = " ".join(c.text for c in chunks)
    assert "real-time" in joined


def test_hashing_backend_deterministic():
    backend = HashingVectorBackend()
    v1 = backend.embed(["semantic chunking of passages"])
    v2 = backend.embed(["semantic chunking of passages"])
    v3 = backend.embed(["completely unrelated gibberish zebra"])
    assert v1 == v2
    assert cosine_similarity(v1[0], v2[0]) == pytest.approx(1.0)
    assert cosine_similarity(v1[0], v3[0]) < 0.3


def test_resolve_backend_fallback():
    backend = resolve_backend("hashing")
    assert isinstance(backend, HashingVectorBackend)
    assert resolve_backend("auto") is not None  # never raises


def test_simulate_rag_and_csp(snapshot):
    chunks = chunk_sections(snapshot.sections)
    queries = build_queries(snapshot)
    assert 2 <= len(queries) <= 8
    result = simulate_rag(queries, chunks, HashingVectorBackend(), top_k=2)
    assert result["csp"] is not None
    assert 0.0 <= result["csp"] <= 100.0
    assert 0.0 <= result["avg_entropy"] <= 1.0
    assert 0.0 < result["retrieval_coverage"] <= 1.0
    assert all("survival_probability" in q for q in result["per_query"])


def test_geo_pillar_and_artifacts(report):
    geo = report.geo
    assert 0 <= geo.score <= 100
    csp = geo.metrics["citation_survival_probability"]
    assert csp is None or 0 <= csp <= 100
    assert geo.metrics["chunk_count"] >= 2
    assert geo.metrics["embedding_backend"].startswith("hashed-ngram")
    llms = geo.artifacts["llms.txt"]
    assert llms.startswith("# Acme Analytics")
    assert "llms" not in llms.lower() or "Citation Survival" in llms
    payload = json.loads(geo.artifacts["rag_ready_chunks.json"])
    assert payload["chunk_count"] == len(payload["chunks"])
    assert payload["chunking"]["max_tokens"] == 120


def test_llms_txt_structure(snapshot):
    chunks = chunk_sections(snapshot.sections)
    sim = simulate_rag(build_queries(snapshot), chunks, HashingVectorBackend())
    text = build_llms_txt(snapshot, chunks, sim)
    assert text.startswith("# ")
    assert "> Acme Analytics" in text
    assert "## " in text
    assert "chunk-000" in text


def test_geo_empty_page_graceful():
    snap = parse_snapshot(BASE_URL, "<html><body></body></html>")
    pillar = GeoAuditor(backend="hashing").audit(snap)
    assert 0 <= pillar.score <= 100
    assert json.loads(pillar.artifacts["rag_ready_chunks.json"])["chunk_count"] == 0


# ---------------------------------------------------------------------------
# core orchestrator + formatters
# ---------------------------------------------------------------------------

def test_core_report_composition(report):
    assert report.url == BASE_URL
    assert 0 <= report.overall_score <= 100
    assert report.grade in {"A+", "A", "B", "C", "D", "F"}
    expected = round(report.seo.score * 0.30 + report.aeo.score * 0.35
                     + report.geo.score * 0.35, 1)
    assert report.overall_score == expected
    assert "llms.txt" in report.artifacts
    assert report.page["word_count"] > 250


def test_render_json_roundtrip(report):
    payload = json.loads(render_json(report))
    assert payload["overall_score"] == report.overall_score
    assert payload["seo"]["pillar"] == "seo"
    assert payload["geo"]["metrics"]["embedding_backend"].startswith("hashed-ngram")
    assert isinstance(payload["audited_at"], str)


def test_render_markdown(report):
    md = render_markdown(report)
    assert md.startswith("# 🧭 SAGE Audit")
    assert "Technical SEO" in md
    assert "Citation Survival Probability" in md
    assert "```json" in md
    assert "molavi.pro" in md


def test_render_terminal_smoke(report):
    from rich.console import Console

    console = Console(record=True, width=110)
    render_terminal(report, console=console)
    output = console.export_text()
    assert "SAGE AUDIT REPORT" in output
    assert "Pillar 3" in output


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_audit_raw_html_json(tmp_path):
    html_file = tmp_path / "page.html"
    html_file.write_text(SAMPLE_HTML, encoding="utf-8")
    artifacts = tmp_path / "artifacts"
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["audit", "--raw-html", str(html_file), "--base-url", BASE_URL,
         "--format", "json", "--embedding-backend", "hashing",
         "--save-artifacts", str(artifacts)],
    )
    assert result.exit_code == 0, result.output
    # CliRunner merges stderr (progress notes) into output; decode the first
    # JSON document on the stream.
    payload, _ = json.JSONDecoder().raw_decode(result.output.lstrip())
    assert payload["overall_score"] >= 0
    assert (artifacts / "llms.txt").exists()
    chunks = json.loads((artifacts / "rag_ready_chunks.json").read_text())
    assert chunks["chunk_count"] >= 2


def test_cli_audit_terminal_and_fail_under(tmp_path):
    html_file = tmp_path / "page.html"
    html_file.write_text(SAMPLE_HTML, encoding="utf-8")
    runner = CliRunner()
    ok = runner.invoke(
        cli,
        ["audit", "--raw-html", str(html_file), "--embedding-backend", "hashing",
         "--fail-under", "10"],
    )
    assert ok.exit_code == 0, ok.output
    gated = runner.invoke(
        cli,
        ["audit", "--raw-html", str(html_file), "--embedding-backend", "hashing",
         "--fail-under", "101"],
    )
    assert gated.exit_code == 1


def test_cli_usage_error_without_target():
    result = CliRunner().invoke(cli, ["audit"])
    assert result.exit_code != 0


def test_cli_version_flag():
    result = CliRunner().invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


# ---------------------------------------------------------------------------
# MCP server (optional dependency)
# ---------------------------------------------------------------------------

def test_mcp_server_creation():
    pytest.importorskip("mcp")
    from sage_audit.server.mcp_server import create_server

    server = create_server()
    assert server is not None
    assert getattr(server, "name", "sage-audit") == "sage-audit"
