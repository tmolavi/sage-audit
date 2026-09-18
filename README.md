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
| **3️⃣ Generative Engine Optimization (GEO)** | `geo_auditor.py` | Semantic passage chunking (60–120 tokens), local vector embeddings with graceful fallback, in-memory RAG retrieval simulation, cosine-distance & semantic-entropy analysis, **Citation Survival Proxy (CSP)**, and auto-generation of `llms.txt` + `rag_ready_chunks.json` |

```text
                    ┌───────────────────────────────────────┐
          L5        │  CITATION SURVIVAL PROXY (CSP) +      │
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

### 🏆 Integration with Molavi AI Visibility Index (MAVI) & Benchmark Contribution

`sage-audit` provides the foundational diagnostic signals (L1–L4) for the **Molavi AI Visibility Index (MAVI)** and supports the [GEO, SEO & Digital Marketing Agency Iran 2026 Benchmark](https://github.com/tmolavi/geo-scope/tree/main/benchmarks/geo-seo-digital-agency-iran-2026.1):

* **L1 Technical Accessibility**: Evaluated via SAGE Technical Auditor (`robots.txt` AI crawler policies for GPTBot, PerplexityBot, ClaudeBot; clean DOM extraction; HTTP security headers).
* **L2 Semantic Extractability**: Evaluated via SAGE semantic passage chunking (60–120 token boundaries) and clean text-to-code ratio.
* **L3 Entity Clarity**: Evaluated via SAGE AEO JSON-LD entity graph validation (`Organization`, `FAQPage`, `sameAs` Wikidata/Crunchbase disambiguation).
* **L4 Citation Readiness**: Evaluated via SAGE Citation Survival Proxy (CSP) using in-memory RAG retrieval simulation and semantic entropy scoring.
* **L5 Empirical AI Visibility**: Measured by [GEO-Scope](https://github.com/tmolavi/geo-scope) across real multi-model provider executions.
* **Ecosystem Architecture**: See [Benchmark Ecosystem Map](docs/BENCHMARK_ECOSYSTEM.md) for how SAGE diagnostics feed directly into MAVI composite scoring and SiteProbe automated remediation.

## 🏛️ Ecosystem

SAGE Audit operates as the static diagnostic component of the **Molavi AI Visibility Stack**:

- **Discovery**: [AnswerPath GEO](https://github.com/tmolavi/answerpath-geo)
- **Measurement**: [GEO-Scope](https://github.com/tmolavi/geo-scope)
- **Diagnostics**: [SAGE Audit](https://github.com/tmolavi/sage-audit)
- **Action**: [SiteProbe](https://github.com/tmolavi/siteprobe)
- **Protocol**: [MCP GEO Server](https://github.com/tmolavi/mcp-geo-server)

## 📖 Runnable Python Example

Run the bundled 3-pillar audit script:
```bash
python examples/audit_example.py
```
A complete JSON audit output sample is available at [`examples/example_audit.json`](examples/example_audit.json).

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

> **🚧 Not on PyPI yet?** Until the first PyPI release is cut (step-by-step runbook in
> **[Distribution & Publishing](#-distribution--publishing)** below), install
> straight from the repository:
>
> ```bash
> pip install git+https://github.com/tmolavi/sage-audit.git
> ```

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

## Scoring Model & Epistemic Evidence Taxonomy

- Every check is a weighted **Finding** tagged with structured epistemic **Evidence Taxonomy (E0–E5)** metadata:
  - **`E0`**: Deterministic technical facts (HTTP status, headers, HTML tag presence, syntax).
  - **`E1`**: Standards & specifications (W3C HTML5, Schema.org, IETF RFCs).
  - **`E2`**: Documented search engine & platform guidance (Google Search Central, bot policies).
  - **`E3`**: Empirical evidence from validated benchmark datasets.
  - **`E4`**: Industry heuristics & configurable thresholds (word counts, chunk sizes, answer density).
  - **`E5`**: Experimental proxies & mathematical models (CSP, softmax semantic entropy).
- **Prohibition of Unproven Claims**: SAGE strictly labels heuristics and proxies without asserting unproven direct ranking-factor claims.
- **Pillar score** = weighted mean × 100. Overall = `0.30·SEO + 0.35·AEO + 0.35·GEO` (configurable).
- **Grades**: **A+ ≥ 93 · A ≥ 85 · B ≥ 75 · C ≥ 65 · D ≥ 50 · F < 50**.
- **Citation Survival Proxy (CSP)**: A heuristic proxy score (0–100) evaluating candidate passage retrieval prominence and low semantic entropy under simulated dense vector retrieval:
  $$\text{CSP} = \text{mean}(0.6 \cdot \text{prominence} + 0.4 \cdot (1 - \text{entropy})) \times 100$$
  *(Note: CSP is an uncalibrated heuristic retrieval proxy, not a literal probability of external AI citation).*
- **Empirical Validation Framework**: Compare SAGE/CSP scores against real observed AI search citation logs via Spearman correlation ($\rho$), AUROC, Precision@k, Brier score, and probability calibration curves (`sage validate`).
- Detailed specification in **[docs/methodology.md](docs/methodology.md)**.

## Project Structure

```text
sage-audit/
├── LICENSE                     # MIT — Copyright (c) 2026 Taqi Molavi
├── pyproject.toml              # build system, metadata, deps, `sage` entrypoint
├── requirements.txt
├── .gitignore
├── docs/
│   └── methodology.md          # Full Evidence Taxonomy & CSP specification
├── src/
│   └── sage_audit/
│       ├── __init__.py         # exports SageAuditor, models, validation, __version__
│       ├── _version.py         # single source of truth
│       ├── config.py           # SageConfig & configurable heuristic thresholds
│       ├── models.py           # pydantic schemas (EvidenceMetadata, CspDetails, Reports)
│       ├── validation.py       # Spearman, AUROC, Precision@k, Brier score, calibration
│       ├── cli.py              # sage audit | generate-llms | validate | mcp
│       ├── core.py             # SAGE orchestrator (0.30/0.35/0.35 configurable fusion)
│       ├── auditors/
│       │   ├── __init__.py
│       │   ├── seo_auditor.py  # Pillar 1 — Technical SEO (E0–E4)
│       │   ├── aeo_auditor.py  # Pillar 2 — Entity AEO (E1–E4)
│       │   └── geo_auditor.py  # Pillar 3 — GEO / RAG simulation / CSP (E0, E4, E5)
│       ├── server/
│       │   ├── __init__.py
│       │   └── mcp_server.py   # FastMCP tools for AI agents
│       └── utils/
│           ├── __init__.py
│           ├── extractor.py    # clean text / DOM parser (Trafilatura + BS4)
│           ├── formatter.py    # terminal / JSON / Markdown renderers with taxonomy
│           └── text.py         # tokenizer, sentence splitter, vector math
├── tests/
│   ├── __init__.py
│   ├── test_auditors.py        # SEO, AEO, GEO, core, CLI unit tests
│   ├── test_taxonomy.py        # Evidence taxonomy & ranking claims tests
│   ├── test_csp_hardening.py   # Hardened CSP proxy semantics tests
│   ├── test_validation.py      # Statistical validation & calibration tests
│   └── test_config.py          # Heuristic threshold override tests
└── README.md
```

## Development

```bash
git clone https://github.com/tmolavi/sage-audit.git
cd sage-audit
pip install -e ".[dev]"
pytest -q
```

## 📦 Distribution & Publishing

### Two "publish" targets — don't confuse them

| Target | What it is | Status |
| --- | --- | --- |
| **GitHub** | Public source-code repository | ✅ **Published** — [github.com/tmolavi/sage-audit](https://github.com/tmolavi/sage-audit) |
| **PyPI** | The `pip install sage-audit` package on pypi.org | ⏳ Pending one-time maintainer step (below) |

> ⚠️ **Until the first PyPI release**, SAGE is installed directly from the repo:
>
> ```bash
> pip install git+https://github.com/tmolavi/sage-audit.git
> # with every optional extra (embeddings + mcp):
> pip install "sage-audit[all] @ git+https://github.com/tmolavi/sage-audit.git"
> ```

### Path A — Manual PyPI publish (≈5 minutes)

GitHub and PyPI are **separate services**: pushing code to GitHub never
publishes a pip package. To put `sage-audit` on PyPI the maintainer must:

1. **Create a PyPI account** at [pypi.org/account/register](https://pypi.org/account/register/),
   verify the email address, and **enable two-factor authentication**
   (PyPI refuses uploads from accounts without 2FA).
2. **Mint an API token** at [pypi.org/manage/account/token](https://pypi.org/manage/account/token/)
   → *Add API token*.
   - The project does not exist on PyPI yet, so the **first token must be
     scoped "Entire account"** — project-scoped tokens only become available
     *after* the first upload.
   - The token starts with `pypi-` — treat it like a password and never
     commit it to git.
3. **Build & upload** from the repo root:

   ```bash
   pip install --upgrade build twine
   python -m build        # → dist/sage_audit-1.0.0-py3-none-any.whl + .tar.gz
   twine upload dist/*    # username: __token__    password: pypi-...
   ```

4. **Verify** at [pypi.org/project/sage-audit](https://pypi.org/project/sage-audit/)
   — from that moment `pip install sage-audit` works worldwide.
5. **Hygiene** — revoke the token immediately after the upload
   (or create a new *project-scoped* one and keep the expiry short).

### Path B — Trusted Publishing (recommended, zero secrets)

This repository already ships
[`.github/workflows/publish.yml`](.github/workflows/publish.yml), which uses the
official [`pypa/gh-action-pypi-publish`](https://github.com/pypa/gh-action-pypi-publish)
action over GitHub OIDC — **no token is ever stored anywhere**.

One-time setup (PyPI side):

1. Go to [pypi.org/manage/account/publishing](https://pypi.org/manage/account/publishing/)
   → **Add a new pending publisher** and enter:
   - PyPI project name: `sage-audit`
   - Owner: `tmolavi` · Repository: `sage-audit`
   - Workflow filename: `publish.yml`
2. Cut a release on GitHub (*Releases → Draft a new release → tag `v1.0.0`*):
   the workflow builds the wheel + sdist and publishes them automatically —
   every future release is a one-click PyPI publish.

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

> **🚧 هنوز روی PyPI منتشر نشده؟** تا قبل از اولین انتشار رسمی (راهنمای گام‌به‌گام در بخش *انتشار روی PyPI* پایین‌تر)، مستقیم از ریپو نصب کنید:
>
> ```bash
> pip install git+https://github.com/tmolavi/sage-audit.git
> ```

### انتشار روی PyPI (اختیاری — راهنمای گام‌به‌گام نگهدارنده)

دو مقصد انتشار را با هم اشتباه نکنید: **گیت‌هاب** (سورس‌کد — منتشر شده ✅) و **PyPI** (پکیج `pip` روی pypi.org — نیازمند اکانت جدا و یک‌بار راه‌اندازی ⏳). پوش کردن کد به گیت‌هاب به‌هیچ‌وجه پکیج pip منتشر نمی‌کند.

تا قبل از اولین انتشار رسمی، هر کسی می‌تواند مستقیم از ریپو نصب کند:

```bash
pip install git+https://github.com/tmolavi/sage-audit.git
```

برای انتشار رسمی روی PyPI:

1. **ساخت اکانت PyPI** — در [pypi.org/account/register](https://pypi.org/account/register/) ثبت‌نام کنید، ایمیل را تأیید و **احراز هویت دو مرحله‌ای (2FA)** را فعال کنید (بدون 2FA پلتفرم اجازهٔ آپلود نمی‌دهد).
2. **ساخت API Token** — در [pypi.org/manage/account/token](https://pypi.org/manage/account/token/) روی *Add API token* بزنید. چون پروژه هنوز روی PyPI وجود ندارد، scope اولین توکن باید **«Entire account»** باشد (توکن پروژه‌محور فقط بعد از اولین آپلود قابل ساخت است). توکن با `pypi-` شروع می‌شود و مثل رمز عبور محرمانه است.
3. **Build و آپلود** — از ریشهٔ پروژه:

   ```bash
   pip install --upgrade build twine
   python -m build        # خروجی: dist/sage_audit-1.0.0-py3-none-any.whl و .tar.gz
   twine upload dist/*    # username: __token__ — password: همان توکن pypi-...
   ```

4. **کنترل نهایی** — صفحهٔ [pypi.org/project/sage-audit](https://pypi.org/project/sage-audit/) را باز کنید؛ از این لحظه `pip install sage-audit` در سراسر جهان کار می‌کند.
5. **امنیت** — بلافاصله بعد از آپلود، توکن را **Revoke** کنید (یا یک توکن جدید *پروژه‌محور* با تاریخ انقضای کوتاه بسازید). توکن را هرگز داخل git کامیت نکنید.

**مسیر جایگزین بدون توکن (Trusted Publishing):** فایل آمادهٔ [`.github/workflows/publish.yml`](.github/workflows/publish.yml) در ریپو موجود است؛ کافی است یک‌بار در [تنظیمات Publishing اکانت PyPI](https://pypi.org/manage/account/publishing/) گیت‌هاب (Owner: `tmolavi`، Repo: `sage-audit`، Workflow: `publish.yml`) را به‌عنوان Trusted Publisher معرفی کنید — از آن به بعد هر **Release** جدید روی گیت‌هاب، به‌طور خودکار روی PyPI منتشر می‌شود، بدون اینکه هیچ توکنی در جایی ذخیره شود.

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

> **🚧 Henüz PyPI'de yok mu?** İlk resmî PyPI sürümüne kadar (aşağıdaki kılavuz) doğrudan depodan kurun:
>
> ```bash
> pip install git+https://github.com/tmolavi/sage-audit.git
> ```

### PyPI'de Yayınlama (İsteğe Bağlı — Adım Adım Kılavuz)

İki yayın hedefini karıştırmayın: **GitHub** (kaynak kodu — yayınlandı ✅) ve **PyPI** (pypi.org'daki `pip` paketi — ayrı hesap ve tek seferlik kurulum gerekir ⏳). Kodu GitHub'a push etmek, asla bir pip paketi yayınlamaz.

İlk resmî PyPI sürümünden önce herkes doğrudan depodan kurabilir:

```bash
pip install git+https://github.com/tmolavi/sage-audit.git
```

Resmî PyPI yayını için:

1. **PyPI hesabı** — [pypi.org/account/register](https://pypi.org/account/register/) adresinden kaydolun, e-postayı doğrulayın ve **2FA**'yı etkinleştirin (2FA olmadan yükleme yapılamaz).
2. **API tokenı** — [pypi.org/manage/account/token](https://pypi.org/manage/account/token/) sayfasında *Add API token*. Proje henüz PyPI'de olmadığı için ilk tokenın kapsamı **«Entire account»** olmalıdır (proje bazlı token ancak ilk yüklemeden sonra oluşturulabilir). Token `pypi-` ile başlar ve parola gibi gizli tutulmalıdır.
3. **Derleme & yükleme** — depo kökünden:

   ```bash
   pip install --upgrade build twine
   python -m build        # çıktı: dist/sage_audit-1.0.0-py3-none-any.whl + .tar.gz
   twine upload dist/*    # kullanıcı adı: __token__ — parola: pypi-... tokenı
   ```

4. **Doğrulama** — [pypi.org/project/sage-audit](https://pypi.org/project/sage-audit/) sayfasını açıp `pip install sage-audit` komutunu test edin; artık tüm dünyada çalışır.
5. **Güvenlik** — yüklemeden hemen sonra tokenı **revoke** edin (ya da yalnızca bu projeye özel, kısa süreli bir token oluşturun). Tokenı asla git'e commit etmeyin.

**Tokensiz alternatif (Trusted Publishing):** depoda hazır bulunan [`.github/workflows/publish.yml`](.github/workflows/publish.yml) dosyası sayesinde; [PyPI Publishing ayarlarından](https://pypi.org/manage/account/publishing/) `tmolavi/sage-audit` (workflow: `publish.yml`) bir kez Trusted Publisher olarak tanımlandığında, bundan sonraki her GitHub **Release**'i otomatik olarak PyPI'de yayınlanır — hiçbir token saklanmadan.

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
