"""Tests for SAGE configuration overrides and threshold customizations.

(c) 2026 Taqi Molavi — https://molavi.pro — MIT License
"""

from __future__ import annotations

import pytest
from sage_audit import SageAuditor, SageConfig
from sage_audit.utils.extractor import parse_snapshot

SAMPLE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<title>Short</title>
<meta name="description" content="Short desc.">
</head>
<body>
<h1>Heading</h1>
<p>Short paragraph text for threshold testing.</p>
</body>
</html>
"""


def test_default_config_values():
    cfg = SageConfig()
    assert cfg.word_count_target == 600
    assert cfg.chunk_min_tokens == 60
    assert cfg.chunk_max_tokens == 120
    assert cfg.weight_seo == 0.30
    assert cfg.weight_aeo == 0.35
    assert cfg.weight_geo == 0.35
    assert cfg.csp_prominence_weight == 0.6
    assert cfg.csp_entropy_weight == 0.4


def test_custom_config_threshold_propagation():
    custom_cfg = SageConfig(
        word_count_target=8,
        word_count_min=4,
        title_min_chars=3,
        title_max_chars=20,
        chunk_min_tokens=5,
        chunk_max_tokens=30,
        weight_seo=0.50,
        weight_aeo=0.25,
        weight_geo=0.25,
    )
    auditor = SageAuditor(config=custom_cfg, embedding_backend="hashing")
    report = auditor.audit_html(SAMPLE_HTML)

    # Title "Short" is 5 chars, which passes custom min=3, max=20
    title_finding = next(f for f in report.seo.findings if f.check_id == "seo.title")
    assert title_finding.status == "pass"

    # Word count passes custom target of 20
    wc_finding = next(f for f in report.seo.findings if f.check_id == "seo.word_count")
    assert wc_finding.status in ("pass", "warn")
    assert wc_finding.score >= 0.7


def test_cli_config_override(tmp_path):
    import json
    from click.testing import CliRunner
    from sage_audit.cli import main as cli

    html_file = tmp_path / "page.html"
    html_file.write_text(SAMPLE_HTML, encoding="utf-8")
    
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"word_count_target": 10, "word_count_min": 5}))

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["audit", "--raw-html", str(html_file), "--config-file", str(config_file),
         "--embedding-backend", "hashing", "--format", "json"],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output.strip())
    assert payload["overall_score"] >= 0
