"""Tests for SAGE Evidence Taxonomy (E0–E5) and Ranking-Factor Claims prohibition.

(c) 2026 Taqi Molavi — https://molavi.pro — MIT License
"""

from __future__ import annotations

import pytest
from sage_audit import SageAuditor
from sage_audit.models import EvidenceLevel, EvidenceMetadata

BASE_URL = "https://example.com/"
SAMPLE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<title>Evidence Taxonomy Test Page Title</title>
<meta name="description" content="A comprehensive test description for epistemic taxonomy verification in the SAGE framework.">
<link rel="canonical" href="https://example.com/">
<script type="application/ld+json">
{"@context": "https://schema.org", "@type": "Organization", "name": "Taxonomy Corp", "url": "https://example.com"}
</script>
</head>
<body>
<h1>Evidence Taxonomy Test Heading</h1>
<p>Substantive paragraph with more than thirty words of factual description explaining how epistemic taxonomy tiers are categorized from deterministic facts to experimental proxies in modern retrieval auditing.</p>
</body>
</html>
"""


def test_all_findings_have_valid_evidence_metadata():
    report = SageAuditor(embedding_backend="hashing").audit_html(SAMPLE_HTML, url=BASE_URL)
    
    all_findings = report.seo.findings + report.aeo.findings + report.geo.findings
    assert len(all_findings) >= 20, "Should have audited all checks across 3 pillars"

    for finding in all_findings:
        assert finding.evidence is not None, f"Finding {finding.check_id} missing evidence metadata"
        assert isinstance(finding.evidence, EvidenceMetadata)
        assert finding.evidence.level in (
            EvidenceLevel.E0,
            EvidenceLevel.E1,
            EvidenceLevel.E2,
            EvidenceLevel.E3,
            EvidenceLevel.E4,
            EvidenceLevel.E5,
        )
        assert finding.evidence.ranking_factor_claim is False, (
            f"Finding {finding.check_id} must strictly set ranking_factor_claim=False"
        )
        assert finding.evidence.signal_type, f"Finding {finding.check_id} missing signal_type"
        assert finding.evidence.evidence_type, f"Finding {finding.check_id} missing evidence_type"


def test_specific_check_evidence_levels():
    report = SageAuditor(embedding_backend="hashing").audit_html(SAMPLE_HTML, url=BASE_URL)
    findings_by_id = {f.check_id: f for f in report.seo.findings + report.aeo.findings + report.geo.findings}

    # E0 Deterministic facts
    assert findings_by_id["seo.http_status"].evidence.level == EvidenceLevel.E0
    assert findings_by_id["seo.https"].evidence.level == EvidenceLevel.E0
    assert findings_by_id["geo.embedding_backend"].evidence.level == EvidenceLevel.E0
    assert findings_by_id["geo.artifacts"].evidence.level == EvidenceLevel.E0

    # E1 Standards backed
    assert findings_by_id["seo.canonical"].evidence.level == EvidenceLevel.E1
    assert findings_by_id["seo.open_graph"].evidence.level == EvidenceLevel.E1
    assert findings_by_id["seo.h1"].evidence.level == EvidenceLevel.E1
    assert findings_by_id["seo.lang"].evidence.level == EvidenceLevel.E1
    assert findings_by_id["aeo.jsonld_presence"].evidence.level == EvidenceLevel.E1
    assert findings_by_id["aeo.entity_graph"].evidence.level == EvidenceLevel.E1
    assert findings_by_id["aeo.authority_sameas"].evidence.level == EvidenceLevel.E1

    # E2 Platform guidance
    assert findings_by_id["seo.title"].evidence.level == EvidenceLevel.E2
    assert findings_by_id["seo.meta_description"].evidence.level == EvidenceLevel.E2
    assert findings_by_id["seo.robots_ai_crawlers"].evidence.level == EvidenceLevel.E2
    assert findings_by_id["aeo.entity_completeness"].evidence.level == EvidenceLevel.E2
    assert findings_by_id["aeo.faq_structuring"].evidence.level == EvidenceLevel.E2
    assert findings_by_id["aeo.freshness"].evidence.level == EvidenceLevel.E2

    # E4 Industry heuristics
    assert findings_by_id["seo.word_count"].evidence.level == EvidenceLevel.E4
    assert findings_by_id["seo.text_to_code"].evidence.level == EvidenceLevel.E4
    assert findings_by_id["aeo.direct_answer_density"].evidence.level == EvidenceLevel.E4
    assert findings_by_id["geo.content_volume"].evidence.level == EvidenceLevel.E4
    assert findings_by_id["geo.chunkability"].evidence.level == EvidenceLevel.E4
    assert findings_by_id["geo.chunk_shape"].evidence.level == EvidenceLevel.E4
    assert findings_by_id["geo.retrieval_coverage"].evidence.level == EvidenceLevel.E4

    # E5 Experimental proxies
    assert findings_by_id["geo.citation_survival"].evidence.level == EvidenceLevel.E5
    assert findings_by_id["geo.retrieval_focus"].evidence.level == EvidenceLevel.E5


def test_no_ranking_factor_claims_in_recommendations():
    report = SageAuditor(embedding_backend="hashing").audit_html(SAMPLE_HTML, url=BASE_URL)
    for p in (report.seo, report.aeo, report.geo):
        for f in p.findings:
            rec = f.recommendation.lower()
            details = f.details.lower()
            assert "negative ranking factor" not in rec, f"Unproven claim in {f.check_id} recommendation: {f.recommendation}"
            assert "positive ranking factor" not in rec, f"Unproven claim in {f.check_id} recommendation: {f.recommendation}"
            assert "is a ranking factor" not in rec, f"Unproven claim in {f.check_id} recommendation: {f.recommendation}"
            assert "ranking factor" not in details, f"Unproven claim in {f.check_id} details: {f.details}"
