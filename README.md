<div align="center">

# 🧭 SAGE — Search, Answer, & Generative Engine Auditor

### `sage-audit` — The Unified 3-Pillar Audit Engine for SEO, Entity AEO, and Generative Engine Optimization (GEO)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![GitHub Stars](https://img.shields.io/github/stars/tmolavi/sage-audit?style=social)](https://github.com/tmolavi/sage-audit)
[![SAGE Pillars: SEO · AEO · GEO](https://img.shields.io/badge/SAGE%20Pillars-SEO%20%C2%B7%20AEO%20%C2%B7%20GEO-7c3aed)](https://github.com/tmolavi/sage-audit)
[![MCP Server](https://img.shields.io/badge/MCP-Server%20Ready-0ea5e9)](https://modelcontextprotocol.io)
[![llms.txt](https://img.shields.io/badge/generates-llms.txt-10b981)](https://llmstxt.org)

**Inspect any URL or raw HTML and score it for the era of AI answers — from classical technical SEO to JSON-LD entity graphs to RAG Citation Survival Probability — in one deterministic, crash-proof command.**

[English](#-english) · [فارسی](#-فارسی) · [Türkçe](#-türkçe)

</div>

---

<a id="-english"></a>

# 🇬🇧 English

## The Problem: Ten Blue Links Are Dying

Search is undergoing its biggest architectural shift since PageRank. Users no longer click **10 blue links** — they get *synthesized answers* from **ChatGPT Search, Perplexity, Claude, Google AI Overviews and Copilot**. These engines do not rank pages; they run **vector RAG pipelines**: they fetch your HTML, strip boilerplate, split it into passages, embed it, retrieve top-k chunks, and let an LLM cite whatever survives.

Classical SEO tools stop at title tags and page speed. They tell you *nothing* about:

- whether `robots.txt` is **blocking GPTBot, PerplexityBot, ClaudeBot, Google-Extended, Amazonbot or Applebot-Extended**;
- whether your **JSON-LD entity graph** is rich, complete, and anchored to Wikidata/Crunchbase via `sameAs`;
- whether the **first 50–70 words** of each section form a direct, fluff-free, factual answer an engine can quote;
- whether your passages are **chunked at coherent semantic boundaries (60–120 tokens)**;
- whether your content **survives retrieval** — or drowns in semantic entropy and is never cited.

**SAGE (`sage-audit`) closes that gap.** One open-source engine, three pillars, four interfaces (CLI · Python library · MCP server · JSON/Markdown exports).

## The 3 Pillars

| Pillar | Module | What it measures |
| --- | --- | --- |
| **1️⃣ Technical SEO** | `seo_auditor.py` | Clean-DOM extraction, text-to-code ratio, canonicals, meta robots (`noindex`/`nosnippet`), Open Graph, H1 hygiene, security/cache HTTP headers, and AI-crawler `robots.txt` policy (GPTBot, PerplexityBot, ClaudeBot, Google-Extended, Amazonbot, Applebot-Extended) |
| **2️⃣ Answer Engine Optimization (AEO)** | `aeo_auditor.py` | Recursive JSON-LD entity-graph validation (`Organization`, `Person`, `Product`, `Article`, `FAQPage`), entity completeness, `sameAs` authority signals (Wikidata, Wikipedia, Crunchbase, official profiles), FAQ structuring, machine-readable freshness, and **direct-answer density** of the first 50–70 words of every section |
| **3️⃣ Generative Engine Optimization (GEO)** | `geo_auditor.py` | Semantic passage chunking (60–120 tokens), local vector embeddings with graceful fallback, in-memory RAG retrieval simulation, cosine-distance & semantic-entropy analysis, **Citation Survival Probability (CSP)**, and auto-generation of `llms.txt` + `rag_ready_chunks.json` |

### The 5-Layer GEO Pyramid

```text
                    ┌───────────────────────────────────────┐
          L5        │  CITATION SURVIVAL PROBABILITY +      │
                    │  llms.txt / rag_ready_chunks.json     │
                    ├───────────────────────────────────────┤
          L4        │  RAG RETRIEVAL SIMULATION             │
                    │  top-k ranking · cosine distance      │
                    ├───────────────────────────────────────┤
          L3        │  VECTOR EMBEDDINGS                    │
                    │  fastembed → sentence-transformers →  │
                    │  deterministic hashed n-gram fallback │
                    ├───────────────────────────────────────┤
          L2        │  SEMANTIC CHUNKING                    │
                    │  60–120 token passage boundaries      │
                    ├───────────────────────────────────────┤
          L1        │  CLEAN DOM EXTRACTION                 │
                    │  boilerplate stripping (Trafilatura)  │
                    └───────────────────────────────────────┘
```

## Installation

```bash
pip install sage-audit

# recommended: local neural embeddings for the GEO pillar
pip install "sage-audit[embeddings]"

# MCP server for Claude Desktop / Cursor / AI agents
pip install "sage-audit[mcp]"

# everything at once
pip install "sage-audit[all]"
```

> **Zero-crash guarantee:** if no neural embedding package is installed (or a model download fails), the GEO pillar silently falls back to a deterministic hashed n-gram TF vectorizer. Results stay stable and reproducible — the tool *never* crashes.

## Quickstart (CLI)

```bash
sage audit https://your-site.com
sage audit https://your-site.com --format markdown -o report.md --save-artifacts ./out
sage audit --raw-html page.html --format json | jq .overall_score
sage generate-llms https://your-site.com -o llms.txt --also-chunks
sage audit https://your-site.com --fail-under 70    # CI quality gate → exit 1
```

Sample (rich) terminal output:

```text
╭────────────────────────────── SAGE AUDIT REPORT ──────────────────────────────╮
│  https://acme-analytics.example.com/                                          │
│  2026-09-01 09:45 UTC · 9 ms · sage-audit v1.0.0                              │
│  ████████████████████░░░░  84.8/100  (Grade B)                                │
╰────────────────────────────────────────────────────────────────────────────────╯
Pillar 1 — Technical SEO            —  96.9/100 (Grade A+)
│ Canonical URL           ✔ pass  │ canonical → https://acme-analytics.example.com
│ Meta robots directives  ✔ pass  │ content="index,follow"
│ robots.txt AI-crawlers  ⚠ warn  │ GPTBot: blocked; ClaudeBot: allowed; …
Pillar 2 — Answer Engine Optimization (AEO) —  90.5/100 (Grade A)
│ Entity authority        ✔ pass  │ 5 sameAs URL(s); anchors: GitHub, LinkedIn,
│                                 │ Wikidata, Wikipedia, X/Twitter
│ Direct-answer density   ✔ pass  │ 5 sections · avg window score 0.74 ·
│                                 │ 5/5 open with an explicit answer
Pillar 3 — Generative Engine Optimization (GEO) —  68.6/100 (Grade C)
│ Chunk size compliance   ✔ pass  │ 100% of chunks inside 60–120 tokens
│ Citation Survival       ✖ fail  │ CSP 43.1% across 8 simulated RAG queries
│ Semantic retrieval      ⚠ warn  │ entropy 0.67 — passages look alike
╭────────────────────── Priority recommendations ───────────────────────╮
│ ✖ Citation Survival Probability (GEO)                                 │
│     Retrieval attention is diffuse — consolidate per-topic sections   │
│     and front-load definitional sentences.                            │
╰─────────────────────────────────────────────────────────────────────────╯
Artifacts generated: llms.txt, rag_ready_chunks.json
```

## Python API (Library)

```python
from sage_audit import SageAuditor

auditor = SageAuditor(embedding_backend="auto", top_k=3)

# Live URL — fetches the page AND its robots.txt
report = auditor.audit("https://molavi.pro")

# Raw HTML — fully offline
report = auditor.audit_html(html_source, url="https://example.local/")

print(report.overall_score, report.grade)          # e.g. 84.8 'B'
print(report.seo.score, report.aeo.score, report.geo.score)
print(report.artifacts["llms.txt"])                # ready-to-serve manifest

for finding in report.geo.findings:
    if finding.recommendation:
        print(finding.title, "→", finding.recommendation)
```

## MCP Server (Claude Desktop · Cursor · Agents)

SAGE ships a **FastMCP** server exposing four autonomous tools:
`sage_audit_url`, `sage_audit_html`, `sage_generate_llms_txt`, `sage_version`.

```bash
sage mcp                       # stdio transport (default)
sage mcp --transport sse --host 127.0.0.1 --port 8642
```

Register it in **`claude_desktop_config.json`**:

```json
{
  "mcpServers": {
    "sage-audit": {
      "command": "sage",
      "args": ["mcp"]
    }
  }
}
```

Or without installing, via `uvx`:

```json
{
  "mcpServers": {
    "sage-audit": {
      "command": "uvx",
      "args": ["--from", "sage-audit[mcp]", "sage", "mcp"]
    }
  }
}
```

## Scoring Model

- Every check is a weighted **Finding** (`pass / warn / fail / info`, 0–1 score, evidence + fix).
- Pillar score = weighted mean × 100. Overall = `0.30·SEO + 0.35·AEO + 0.35·GEO`.
- Grades: **A+ ≥ 93 · A ≥ 85 · B ≥ 75 · C ≥ 65 · D ≥ 50 · F < 50**.
- **Citation Survival Probability (CSP):** per simulated entity query, SAGE embeds query + passages, ranks by cosine similarity, and combines *retrieval prominence* (z-score of the winner vs. the field) with *(1 − normalized semantic entropy)* of the similarity softmax: `CSP = mean(0.6·prominence + 0.4·(1−entropy)) × 100`.

## Project Structure

```text
sage-audit/
├── LICENSE                     # MIT — Copyright (c) 2026 Taqi Molavi
├── pyproject.toml              # build system, metadata, deps, `sage` entrypoint
├── requirements.txt
├── .gitignore
├── src/
│   └── sage_audit/
│       ├── __init__.py         # exports SageAuditor, models, __version__
│       ├── _version.py         # single source of truth
│       ├── models.py           # pydantic schemas (Finding/Pillar/AuditReport)
│       ├── cli.py              # sage audit | generate-llms | mcp
│       ├── core.py             # SAGE orchestrator (0.30/0.35/0.35 fusion)
│       ├── auditors/
│       │   ├── __init__.py
│       │   ├── seo_auditor.py  # Pillar 1 — Technical SEO
│       │   ├── aeo_auditor.py  # Pillar 2 — Entity AEO
│       │   └── geo_auditor.py  # Pillar 3 — GEO / RAG simulation
│       ├── server/
│       │   ├── __init__.py
│       │   └── mcp_server.py   # FastMCP tools for AI agents
│       └── utils/
│           ├── __init__.py
│           ├── extractor.py    # clean text / DOM parser (Trafilatura + BS4)
│           ├── formatter.py    # terminal / JSON / Markdown renderers
│           └── text.py         # tokenizer, sentence splitter, vector math
├── tests/
│   ├── __init__.py
│   └── test_auditors.py        # SEO, AEO, GEO, core, CLI unit tests
└── README.md
```

## Development

```bash
git clone https://github.com/tmolavi/sage-audit.git
cd sage-audit
pip install -e ".[dev]"
pytest -q
```

## GitHub Topics

`seo` · `aeo` · `geo` · `generative-engine-optimization` · `ai-search` · `rag` · `mcp-server` · `perplexity` · `chatgpt-search` · `llms-txt` · `schema-markup` · `entity-seo`

---

<a id="-فارسی"></a>

# 🇮🇷 فارسی

<div dir="rtl">

## SAGE — سِیج: اولین موتور ممیزی متن‌باز سه‌گانهٔ سئو، AEO و GEO در دنیا

**sage-audit** (مخفف Search, Answer, & Generative Engine Auditor) اولین ابزار متن‌باز جهان است که هر سه ستون بهینه‌سازی برای موتورهای جست‌وجو، موتورهای پاسخ‌گو و موتورهای مولد را **در یک دستور واحد** ممیزی می‌کند. توسعه‌دهنده و معمار این پروژه **[تقی مولوی](https://molavi.pro)** است.

### چرا SAGE؟

دوران ده لینک آبی تمام شده است. کاربران امروز پاسخ خود را از ChatGPT، Perplexity، Claude و Google AI Overviews می‌گیرند؛ سیستم‌هایی که صفحهٔ شما را «رتبه‌بندی» نمی‌کنند، بلکه آن را به قطعات برداری (Chunk) تقسیم کرده و از طریق خط‌لولهٔ RAG بازیابی می‌کنند. ابزارهای کلاسیک سئو هیچ‌چیز دربارهٔ این‌ها نمی‌گویند:

- سیاست `robots.txt` در برابر خزنده‌های هوش مصنوعی (GPTBot، PerplexityBot، ClaudeBot، Google-Extended، Amazonbot، Applebot-Extended)؛
- عمق گراف موجودیت JSON-LD و لنگرهای اعتبار `sameAs` (ویکی‌دیتا، ویکی‌پدیا، Crunchbase)؛
- چگالی «پاسخ مستقیم» در ۵۰ تا ۷۰ کلمهٔ نخست هر بخش؛
- و **احتمال بقای ارجاع (Citation Survival Probability)** در خط‌لولهٔ بازیابی برداری.

### معماری هرم ۵ لایهٔ GEO

```text
          لایهٔ ۵  │  احتمال بقای ارجاع + تولید llms.txt و rag_ready_chunks.json
          لایهٔ ۴  │  شبیه‌سازی بازیابی RAG (رتبه‌بندی top-k با شباهت کسینوسی)
          لایهٔ ۳  │  تعبیهٔ برداری: fastembed ← sentence-transformers ← بردارساز قطعی n-gram
          لایهٔ ۲  │  قطعه‌بندی معنایی متن (مرزهای ۶۰ تا ۱۲۰ توکن)
          لایهٔ ۱  │  استخراج DOM تمیز و حذف صفحه‌آرایی (Trafilatura)
```

یکی از خروجی‌های خودکار، فایل **`llms.txt`** است: سندی استاندارد که به LLMها اعلام می‌کند صفحهٔ شما چه ساختاری دارد — SAGE آن را همراه با `rag_ready_chunks.json` به‌صورت خودکار تولید می‌کند.

### نصب و اجرای سریع

```bash
pip install sage-audit
pip install "sage-audit[embeddings]"   # توصیه‌شده: تعبیهٔ عصبی محلی
pip install "sage-audit[mcp]"          # سرور پروتکل MCP

sage audit https://molavi.pro
sage audit https://molavi.pro --format markdown -o report.md --save-artifacts ./out
sage generate-llms https://molavi.pro -o llms.txt --also-chunks
sage audit https://molavi.pro --fail-under 70   # دروازهٔ کیفی در CI
sage mcp                                        # اتصال به Claude Desktop / Cursor
```

### تضمین پایداری

اگر بستهٔ تعبیهٔ عصبی نصب نباشد یا دانلود مدل شکست بخورد، ستون GEO به‌صورت خودکار به بردارساز قطعی و بازتولیدپذیر n-gram کاهش می‌یابد؛ ابزار **هرگز متوقف نمی‌شود** و نتایج همواره قطعی و قابل اتکا می‌مانند.

### توسعه‌دهنده

| | |
| --- | --- |
| **توسعه‌دهنده و معمار** | تقی مولوی (Taqi Molavi) |
| **وب‌سایت رسمی** | [molavi.pro](https://molavi.pro) |
| **مرکز پژوهش (Think Tank)** | [molavi.pro/research](https://molavi.pro/research) |
| **گیت‌هاب** | [github.com/tmolavi](https://github.com/tmolavi) |
| **مجوز** | MIT — © ۲۰۲۶ تقی مولوی |

</div>

---

<a id="-türkçe"></a>

# 🇹🇷 Türkçe

## SAGE Projesi: SEO, AEO ve GEO için Dünyanın İlk Birleşik Açık Kaynak Denetim Motoru

**sage-audit** (Search, Answer, & Generative Engine Auditor), bir web sayfasını üç sütunda birden denetleyen dünyanın ilk birleşik açık kaynak motorudur: **klasik teknik SEO**, **varlık tabanlı AEO** (Cevap Motoru Optimizasyonu) ve **GEO** (Üretken Motor Optimizasyonu). Projenin geliştiricisi ve mimarı **[Taqi Molavi](https://molavi.pro)**'dir.

### Neden SAGE?

Mavi bağlantılar çağı kapanıyor. Kullanıcılar artık yanıtları ChatGPT, Perplexity, Claude ve Google AI Overviews gibi sistemlerden alıyor. Bu sistemler sayfanızı sıralamaz; HTML'inizi alır, metni 60–120 tokenlık parçalara böler, vektör uzayına gömer ve yalnızca RAG hattından sağ çıkan pasajları alıntılar. SAGE şunları ölçer:

- `robots.txt` dosyasının yapay zekâ tarayıcılarına (GPTBot, PerplexityBot, ClaudeBot, Google-Extended, Amazonbot, Applebot-Extended) karşı politikası;
- JSON-LD varlık grafiğinin derinliği ve Wikidata / Wikipedia / Crunchbase gibi `sameAs` otorite sinyalleri;
- Her bölümün ilk 50–70 kelimesindeki **doğrudan yanıt yoğunluğu**;
- Kosinüs uzaklığı + anlamsal entropi ile **Alıntı Hayatta Kalma Olasılığı (CSP)**;
- **5 katmanlı GEO piramidi** sonunda otomatik olarak `llms.txt` ve `rag_ready_chunks.json` üretimi.

### Kurulum ve Hızlı Başlangıç

```bash
pip install sage-audit
pip install "sage-audit[embeddings]"   # önerilen: yerel sinirsel gömme
pip install "sage-audit[mcp]"          # MCP sunucusu

sage audit https://ornek-siteniz.com
sage audit https://ornek-siteniz.com --format markdown -o rapor.md --save-artifacts ./cikti
sage generate-llms https://ornek-siteniz.com -o llms.txt --also-chunks
sage audit https://ornek-siteniz.com --fail-under 70   # CI kalite kapısı
sage mcp                                               # Claude Desktop / Cursor bağlantısı
```

### Geliştirici

| | |
| --- | --- |
| **Geliştirici & Mimar** | Taqi Molavi |
| **Resmî Web Sitesi** | [molavi.pro](https://molavi.pro) |
| **Araştırma Merkezi (Think Tank)** | [molavi.pro/research](https://molavi.pro/research) |
| **GitHub** | [github.com/tmolavi](https://github.com/tmolavi) |
| **Lisans** | MIT — © 2026 Taqi Molavi |

SAGE; sinirsel gömme modeli bulunamadığında otomatik olarak deterministik n-gram vektörleştiriciye geçer — araç **asla çökmez**, sonuçlar her zaman tekrar üretilebilirdir.

---

<div align="center">

## Author & Architect

### [Taqi Molavi (Taghi Molavi)](https://molavi.pro)

🌐 **[molavi.pro](https://molavi.pro)** · 🔬 **[Molavi R&D Think Tank — molavi.pro/research](https://molavi.pro/research)** · 🐙 **[github.com/tmolavi](https://github.com/tmolavi)**

If SAGE helps your research or your rankings, please **star ⭐ the repository** — it keeps the engine open-source and evolving.

**License:** [MIT](LICENSE) — Copyright (c) 2026 Taqi Molavi

</div>
