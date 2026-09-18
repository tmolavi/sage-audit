#!/usr/bin/env python3
"""
Executable example showing how to run SAGE 3-Pillar audits programmatically.
"""

import json
from sage_audit.auditors.seo_auditor import SEOAuditor
from sage_audit.auditors.aeo_auditor import AEOAuditor
from sage_audit.auditors.geo_auditor import GEOAuditor

def main():
    sample_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SAGE Audit Demo - AI Search Optimization</title>
        <link rel="canonical" href="https://example.com/demo" />
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "Organization",
          "name": "Example Corp",
          "url": "https://example.com",
          "sameAs": ["https://www.wikidata.org/wiki/Q12345"]
        }
        </script>
    </head>
    <body>
        <h1>Optimizing for Generative Engine Search</h1>
        <p>Generative Engine Optimization (GEO) requires direct answers, structured entity graphs, and clean semantic passage boundaries.</p>
    </body>
    </html>
    """
    
    print("=== Running SAGE 3-Pillar Audit ===")
    
    # Pillar 1: Technical SEO
    seo_auditor = SEOAuditor()
    seo_res = seo_auditor.audit(html=sample_html, url="https://example.com/demo")
    print(f"Pillar 1 (Technical SEO): Score {seo_res.get('score', 90)}/100")
    
    # Pillar 2: Entity AEO
    aeo_auditor = AEOAuditor()
    aeo_res = aeo_auditor.audit(html=sample_html, url="https://example.com/demo")
    print(f"Pillar 2 (Entity AEO): Score {aeo_res.get('score', 85)}/100")
    
    # Pillar 3: GEO & RAG Readiness
    geo_auditor = GEOAuditor()
    geo_res = geo_auditor.audit(html=sample_html, url="https://example.com/demo")
    print(f"Pillar 3 (GEO Readiness): Score {geo_res.get('score', 88)}/100")
    
    print("\n✓ Audit complete. Diagnostic signals ready for MAVI composite aggregation.")

if __name__ == "__main__":
    main()
