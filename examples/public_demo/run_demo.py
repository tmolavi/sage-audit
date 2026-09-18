#!/usr/bin/env python3
"""
SAGE Audit Public Demo
[STANDALONE_DEMO_FIXTURE] — Multi-Pillar Technical SEO, AEO & GEO Audit

Audits an HTML target across technical structure, entity graph clarity,
and generative AI readability without making external network calls.
"""

import json
from pathlib import Path

from sage_audit.utils.extractor import parse_snapshot
from sage_audit.auditors.seo_auditor import SeoAuditor
from sage_audit.auditors.aeo_auditor import AeoAuditor
from sage_audit.auditors.geo_auditor import GeoAuditor

DEMO_DIR = Path(__file__).parent

def run():
    html_file = DEMO_DIR / "sample_page.html"
    output_file = DEMO_DIR / "sample_audit.json"

    with open(html_file, "r", encoding="utf-8") as f:
        html_content = f.read()

    url = "https://web24.ir/services/technical-seo"
    headers = {
        "content-type": "text/html; charset=utf-8",
        "strict-transport-security": "max-age=31536000",
        "content-security-policy": "default-src 'self'",
        "x-content-type-options": "nosniff",
        "cache-control": "public, max-age=3600",
    }
    robots_txt = "User-agent: *\nAllow: /\n"

    snapshot = parse_snapshot(url, html_content, status_code=200, headers=headers, robots_txt=robots_txt)

    print("=" * 70)
    print("SAGE Audit: Multi-Pillar Diagnostic Audit Demo")
    print("=" * 70)
    print(f"• Target URL      : {url}")
    print(f"• Input HTML Size : {len(html_content)} bytes")
    print(f"• Execution Mode  : standalone_demo_fixture (offline)")
    print("-" * 70)

    # 1. Technical SEO Audit
    seo_auditor = SeoAuditor()
    seo_rep = seo_auditor.audit(snapshot)
    print(f"✓ Pillar 1: Technical SEO Audit  — Score: {seo_rep.score}/100 (Grade: {seo_rep.grade})")

    # 2. Entity AEO Audit
    aeo_auditor = AeoAuditor()
    aeo_rep = aeo_auditor.audit(snapshot)
    print(f"✓ Pillar 2: Entity & AEO Graph   — Score: {aeo_rep.score}/100 (Grade: {aeo_rep.grade})")

    # 3. Generative Engine GEO Audit
    geo_auditor = GeoAuditor()
    geo_rep = geo_auditor.audit(snapshot)
    print(f"✓ Pillar 3: GEO & RAG Readiness  — Score: {geo_rep.score}/100 (Grade: {geo_rep.grade})")

    composite_score = round((seo_rep.score * 0.35) + (aeo_rep.score * 0.35) + (geo_rep.score * 0.30), 1)

    audit_result = {
        "status": "success",
        "demo_version": "2026.1",
        "url": url,
        "composite_score": composite_score,
        "pillars": {
            "technical_seo": {
                "score": seo_rep.score,
                "grade": seo_rep.grade,
                "findings_count": len(seo_rep.findings)
            },
            "entity_aeo": {
                "score": aeo_rep.score,
                "grade": aeo_rep.grade,
                "findings_count": len(aeo_rep.findings)
            },
            "generative_geo": {
                "score": geo_rep.score,
                "grade": geo_rep.grade,
                "findings_count": len(geo_rep.findings)
            }
        },
        "recommendations": [
            "Add explicit QAPage schema to FAQ section for direct AI grounding.",
            "Include primary author entity linking to recognized knowledge bases.",
            "Maintain fast TTFB and semantic passage chunk boundaries."
        ]
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(audit_result, f, indent=2, ensure_ascii=False)

    print("-" * 70)
    print(f"Composite SAGE Health Score: {composite_score}/100")
    print(f"✓ Diagnostic report written to: {output_file.name}")
    print("=" * 70)

if __name__ == "__main__":
    run()
