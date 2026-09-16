"""Tests for hardened Citation Survival Proxy (CSP) semantics and methodology.

(c) 2026 Taqi Molavi — https://molavi.pro — MIT License
"""

from __future__ import annotations

import json
import pytest
from sage_audit import SageAuditor
from sage_audit.auditors.geo_auditor import (
    Chunk,
    HashingVectorBackend,
    build_llms_txt,
    build_queries,
    chunk_sections,
    simulate_rag,
)
from sage_audit.models import CspDetails, EvidenceLevel
from sage_audit.utils.extractor import parse_snapshot

SAMPLE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<title>Cloud Architecture Framework</title>
<meta name="description" content="A comprehensive framework for modern resilient multi-region cloud systems.">
</head>
<body>
<h1>Cloud Architecture Framework</h1>
<p>Cloud architecture is the structural design of software applications running on distributed cloud infrastructure. It encompasses network topologies, compute isolation, data consistency models, and multi-region failover automation across enterprise workloads.</p>
<h2>What is Multi-Region Failover?</h2>
<p>Multi-region failover is an automated routing mechanism that shifts traffic between geographical regions in under 30 seconds when an outage occurs. It relies on global DNS load balancing, health checks, and asynchronous database replication across availability zones.</p>
<h2>How are State Machines Designed?</h2>
<p>State machines in distributed systems maintain atomic transaction state using event-driven consensus protocols like Raft. They guarantee that partition events do not produce split-brain scenarios or data loss during network degradation.</p>
</body>
</html>
"""


def test_csp_details_and_metadata_structure():
    report = SageAuditor(embedding_backend="hashing").audit_html(SAMPLE_HTML, url="https://cloud.example.com")
    geo_metrics = report.geo.metrics

    assert "csp_details" in geo_metrics
    csp_details = geo_metrics["csp_details"]
    assert csp_details is not None
    assert csp_details["metric_name"] == "Citation Survival Proxy"
    assert csp_details["abbreviation"] == "CSP"
    assert csp_details["metric_type"] == "heuristic_proxy"
    assert csp_details["calibrated_probability"] is False
    assert csp_details["evidence_level"] == "E5"
    assert csp_details["scale"] == "0-100"
    assert "formula" in csp_details
    assert "weights" in csp_details
    assert len(csp_details["assumptions"]) >= 2
    assert len(csp_details["limitations"]) >= 2
    assert csp_details["validation_status"] == "unvalidated"


def test_csp_finding_title_and_details():
    report = SageAuditor(embedding_backend="hashing").audit_html(SAMPLE_HTML, url="https://cloud.example.com")
    csp_finding = next(f for f in report.geo.findings if f.check_id == "geo.citation_survival")
    
    assert "Citation Survival Proxy" in csp_finding.title
    assert "heuristic proxy" in csp_finding.details
    assert "uncalibrated" in csp_finding.details
    assert csp_finding.evidence.level == EvidenceLevel.E5
    assert csp_finding.evidence.signal_type == "heuristic_proxy"


def test_csp_mathematical_bounds_and_components():
    chunks = [
        Chunk(index=0, id="chunk-000", text="Cloud architecture is the structural design of software.", token_count=10),
        Chunk(index=1, id="chunk-001", text="Multi-region failover is an automated routing mechanism.", token_count=10),
        Chunk(index=2, id="chunk-002", text="State machines in distributed systems maintain atomic transaction state.", token_count=10),
    ]
    queries = ["What is Cloud Architecture?", "How does failover work?", "State machine design"]
    backend = HashingVectorBackend()

    sim = simulate_rag(queries, chunks, backend, top_k=2)
    assert sim["csp"] is not None
    assert 0.0 <= sim["csp"] <= 100.0
    assert sim["citation_survival_proxy"] == sim["csp"]
    
    for item in sim["per_query"]:
        assert "survival_proxy" in item
        assert 0.0 <= item["survival_proxy"] <= 1.0
        assert 0.0 <= item["retrieval_prominence"] <= 1.0
        assert 0.0 <= item["semantic_entropy"] <= 1.0


def test_llms_txt_uses_hardened_csp_label():
    snap = parse_snapshot("https://cloud.example.com", SAMPLE_HTML)
    chunks = chunk_sections(snap.sections)
    sim = simulate_rag(build_queries(snap), chunks, HashingVectorBackend())
    llms = build_llms_txt(snap, chunks, sim)
    
    assert "Citation Survival Proxy (CSP):" in llms
    assert "Probability:" not in llms or "Citation Survival Proxy" in llms
