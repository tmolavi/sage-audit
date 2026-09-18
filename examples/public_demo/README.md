# SAGE Audit Public Demo

`[STANDALONE_DEMO_FIXTURE]` — **Multi-Pillar Technical SEO, AEO & GEO Diagnostic Engine**

This demo shows how SAGE Audit analyzes web pages across 3 core pillars:
1. **Technical SEO**: Canonical links, metadata, heading hierarchy, viewport.
2. **Entity AEO**: JSON-LD Schema.org graphs, entity disambiguation, Wikidata links.
3. **Generative GEO**: Semantic passage boundaries, citation extraction signals, and AI engine readability.

---

## Files

| File | Description |
|------|-------------|
| `sample_page.html` | Sample localized landing page with Schema.org markup |
| `sample_audit.json` | Generated multi-pillar diagnostic report with composite scoring |
| `run_demo.py` | Executable script that audits `sample_page.html` locally |

---

## 🚀 How to Run (Under 10 Seconds)

```bash
python examples/public_demo/run_demo.py
```

### Expected Output
```text
======================================================================
SAGE Audit: Multi-Pillar Diagnostic Audit Demo
======================================================================
• Target URL      : https://web24.ir/services/technical-seo
• Input HTML Size : 1600+ bytes
• Execution Mode  : standalone_demo_fixture (offline)
----------------------------------------------------------------------
✓ Pillar 1: Technical SEO Audit  — Score: 92/100
✓ Pillar 2: Entity & AEO Graph   — Score: 88/100
✓ Pillar 3: GEO & RAG Readiness  — Score: 90/100
----------------------------------------------------------------------
Composite SAGE Health Score: 90.0/100
✓ Diagnostic report written to: sample_audit.json
======================================================================
```
