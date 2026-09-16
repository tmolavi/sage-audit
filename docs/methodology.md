# 🧭 SAGE Audit: Evidence Taxonomy & CSP Methodology Specification

**Version:** `2.0.0`  
**Author:** Taqi Molavi ([molavi.pro](https://molavi.pro))  
**License:** MIT License  

---

## 1. Executive Summary & Epistemic Framework

**SAGE (Search, Answer, & Generative Engine Auditor)** provides a rigorous, 3-pillar diagnostic evaluation of digital content for classical web search, AI answer engines, and generative retrieval-augmented generation (RAG) pipelines.

In automated auditing, tools often blur the boundary between **provable technical facts** and **uncalibrated heuristics**. SAGE Methodology v2.0 establishes strict epistemic transparency by:
1. **Classifying every check into an explicit Evidence Taxonomy (E0–E5)**.
2. **Prohibiting unproven direct ranking-factor claims**.
3. **Hardening Citation Survival Proxy (CSP)** as an explicit heuristic retrieval proxy rather than a literal calibrated probability.
4. **Exposing configurable heuristic thresholds** across all three pillars.
5. **Providing an empirical validation and statistical calibration framework** to evaluate SAGE and CSP against real observed AI search citation logs.

---

## 2. SAGE Evidence Taxonomy (E0 – E5)

Every audit finding emitted by SAGE carries structured epistemic metadata (`level`, `evidence_type`, `source`, `ranking_factor_claim`, `signal_type`, `configurable`).

```
┌────────────────────────────────────────────────────────────────────────┐
│                      SAGE EVIDENCE TAXONOMY TIER                       │
├────┬─────────────────────────────┬─────────────────────────────────────┤
│ E0 │ Deterministic Technical Fact│ Byte-level, protocol, syntax facts  │
│ E1 │ Standards / Specification   │ W3C, IETF RFC, Schema.org standards │
│ E2 │ Documented Platform Guidance│ Official Google/Bing/Bot guidelines │
│ E3 │ Empirical Evidence          │ Validated on external observations  │
│ E4 │ Industry Heuristic          │ Common engineering/SEO thresholds   │
│ E5 │ Experimental Proxy          │ Internal mathematical proxy models  │
└────┴─────────────────────────────┴─────────────────────────────────────┘
```

### Taxonomy Tier Definitions

* **`E0` — Deterministic Technical Fact**:
  Directly measured protocol facts without interpretation or probabilistic assumptions (e.g. HTTP status codes, TLS certificate presence, response header existence, HTML tag presence, syntax parsing errors).
* **`E1` — Standards / Specification Backed**:
  Explicitly governed by formal open standards and specifications (e.g. W3C HTML5 document outlines, Schema.org vocabulary, IETF RFC 9110/9111 HTTP specifications, RFC 6596 canonical links, Open Graph Protocol).
* **`E2` — Documented Platform Guidance**:
  Derived directly from published search engine or AI platform engineering documentation (e.g. Google Search Central title/meta guidelines, Google structured data requirements, OpenAI/Anthropic/Perplexity bot exclusion documentation).
* **`E3` — Empirical Evidence**:
  Claims and scoring weights backed by published, statistically significant observations from real external AI search engines (e.g. measured citation correlations in benchmark datasets).
* **`E4` — Industry Heuristic**:
  Empirical rules of thumb and operational engineering best practices (e.g. 600+ word count floors, 60–120 token chunk boundaries, direct answer sentence lengths). All E4 thresholds are explicitly configurable.
* **`E5` — Experimental Hypothesis / Heuristic Proxy**:
  Mathematical formulation or synthetic simulation designed as a proxy for complex downstream behaviors (e.g. Citation Survival Proxy, Softmax Semantic Entropy).

---

## 3. Complete Audit Check Inventory & Taxonomy Mapping

| Pillar | Check ID | Check Name | Tier | Evidence Type | Source Reference | Configurable |
| :--- | :--- | :--- | :---: | :--- | :--- | :---: |
| **SEO** | `seo.http_status` | HTTP status | **`E0`** | `deterministic_fact` | RFC 9110 HTTP Semantics | No |
| **SEO** | `seo.https` | HTTPS transport | **`E0`** | `deterministic_fact` | RFC 2818 / Transport Security | No |
| **SEO** | `seo.title` | Title tag | **`E2`** | `platform_guidance` | Google Search Central Title Guidelines | **Yes** |
| **SEO** | `seo.meta_description` | Meta description | **`E2`** | `platform_guidance` | Google Search Central Snippet Guidelines | **Yes** |
| **SEO** | `seo.canonical` | Canonical URL | **`E1`** | `standards_backed` | RFC 6596 Canonical Link Relation | No |
| **SEO** | `seo.meta_robots` | Meta robots directives | **`E1`** | `standards_backed` | RFC 9309 / Robots Exclusion Protocol | No |
| **SEO** | `seo.open_graph` | Open Graph protocol | **`E1`** | `standards_backed` | The Open Graph Protocol Specification | No |
| **SEO** | `seo.h1` | H1 heading | **`E1`** | `standards_backed` | W3C HTML5 Document Structure | No |
| **SEO** | `seo.lang` | Document language | **`E1`** | `standards_backed` | W3C HTML5 / BCP 47 Language Tags | No |
| **SEO** | `seo.image_alts` | Image alt coverage | **`E1`** | `standards_backed` | W3C WCAG 2.1 (SC 1.1.1) | **Yes** |
| **SEO** | `seo.word_count` | Content volume | **`E4`** | `industry_heuristic` | Information Retrieval Best Practice | **Yes** |
| **SEO** | `seo.text_to_code` | Text-to-code ratio | **`E4`** | `industry_heuristic` | DOM Cleanliness Heuristic | **Yes** |
| **SEO** | `seo.security_headers` | Security headers | **`E1`** | `standards_backed` | RFC 6797 / W3C CSP / RFC 7034 | No |
| **SEO** | `seo.cache_headers` | Cache/validation headers | **`E1`** | `standards_backed` | RFC 9111 HTTP Caching | No |
| **SEO** | `seo.robots_ai_crawlers` | robots.txt AI-crawler policy | **`E2`** | `platform_guidance` | Documented AI Crawler Specs | No |
| **AEO** | `aeo.jsonld_presence` | JSON-LD structured data | **`E1`** | `standards_backed` | W3C JSON-LD 1.1 / Schema.org | No |
| **AEO** | `aeo.entity_graph` | Entity-graph coverage | **`E1`** | `standards_backed` | Schema.org Core Entity Types | No |
| **AEO** | `aeo.entity_completeness`| Primary-entity completeness | **`E2`** | `platform_guidance` | Google Structured Data Guidelines | No |
| **AEO** | `aeo.authority_sameas` | Entity authority (sameAs) | **`E1`** | `standards_backed` | Schema.org sameAs Reference | **Yes** |
| **AEO** | `aeo.faq_structuring` | FAQ structuring | **`E2`** | `platform_guidance` | Schema.org FAQPage & Google Q&A Spec | No |
| **AEO** | `aeo.direct_answer_density`| Direct-answer density | **`E4`** | `industry_heuristic` | Vector Perturbation Architecture (VPA) | **Yes** |
| **AEO** | `aeo.freshness` | Machine-readable freshness | **`E2`** | `platform_guidance` | Google / Schema.org Temporal Guidance| No |
| **AEO** | `aeo.entity_linking` | Entity linking (@id/about) | **`E1`** | `standards_backed` | W3C Linked Data / Schema.org Graph | No |
| **GEO** | `geo.content_volume` | Retrievable content volume | **`E4`** | `industry_heuristic` | RAG Passage Extraction Token Floor | **Yes** |
| **GEO** | `geo.chunkability` | Semantic chunkability | **`E4`** | `industry_heuristic` | Semantic Passage Segmentation Pattern| **Yes** |
| **GEO** | `geo.chunk_shape` | Chunk size compliance | **`E4`** | `industry_heuristic` | Dense Embedding Token Window Envelope | **Yes** |
| **GEO** | `geo.citation_survival` | Citation Survival Proxy (CSP)| **`E5`** | `experimental_hypothesis`| Molavi Citation Survival Proxy (VPA)| **Yes** |
| **GEO** | `geo.retrieval_focus` | Semantic retrieval focus | **`E5`** | `experimental_hypothesis`| Softmax Semantic Entropy Focus Metric| No |
| **GEO** | `geo.retrieval_coverage`| Retrieval coverage | **`E4`** | `industry_heuristic` | Corpus Coverage Diagnostic | **Yes** |
| **GEO** | `geo.embedding_backend` | Embedding backend | **`E0`** | `deterministic_fact` | Local Runtime Vector Environment | No |
| **GEO** | `geo.artifacts` | RAG artifacts generated | **`E0`** | `deterministic_fact` | Artifact Synthesis Engine Output | No |

---

## 4. Prohibition of Unproven Ranking-Factor Claims

SAGE strictly prohibits presenting unverified heuristics as "official ranking factors."

* **Replaced Phrasing**:
  * ❌ *"HTTPS is a positive ranking factor"* $\rightarrow$ ✅ *"HTTPS provides encrypted transport security and is a documented platform prerequisite."*
  * ❌ *"Word count below 300 hurts your Google rank"* $\rightarrow$ ✅ *"Thin content (<300 words) provides minimal factual density for retrieval systems."*
  * ❌ *"CSP gives your 84% probability of being cited by ChatGPT"* $\rightarrow$ ✅ *"CSP 84.0/100 is an uncalibrated heuristic proxy for passage retrieval prominence and low semantic entropy in simulated dense retrieval."*

---

## 5. Citation Survival Proxy (CSP) Mathematical Specification

### 5.1 Definition & Formula

**Citation Survival Proxy (CSP)** is a deterministic heuristic proxy (scale $0–100$) evaluating whether an in-memory dense retrieval simulator identifies unambiguous, non-diffuse candidate passages for derived probe queries.

For a set of $M$ derived probe queries $Q = \{q_1, \dots, q_M\}$ and passage chunks $C = \{c_1, \dots, c_N\}$ embedded into unit-normalized vectors:

$$\text{sim}(q, c_i) = \cos(\mathbf{v}_q, \mathbf{v}_{c_i}) = \mathbf{v}_q \cdot \mathbf{v}_{c_i}$$

For query $q$, let $\mathbf{s} = (s_1, \dots, s_N)$ be the array of cosine similarities.

#### 1. Retrieval Prominence ($P_q \in [0, 1]$):
Measures whether the top-ranked chunk stands out significantly from the corpus similarity distribution:

$$\mu_s = \frac{1}{N}\sum_{i=1}^N s_i, \quad \sigma_s = \sqrt{\frac{1}{N}\sum_{i=1}^N (s_i - \mu_s)^2}$$

$$Z_q = \frac{\max(\mathbf{s}) - \mu_s}{\sigma_s + \epsilon}$$

$$P_q = \text{clamp}\left(\frac{Z_q}{3.0}, 0.0, 1.0\right)$$

#### 2. Softmax Semantic Entropy ($H_q \in [0, 1]$):
Measures the dispersion / ambiguity of retriever attention over candidate chunks using an adaptive temperature $T = \max(\sigma_s, 10^{-9})$:

$$p_i = \frac{e^{s_i / T}}{\sum_{j=1}^N e^{s_j / T}}$$

$$H_q = -\frac{1}{\ln(N)} \sum_{i=1}^N p_i \ln(p_i + 10^{-12})$$

#### 3. Per-Query Survival Proxy ($S_q \in [0, 1]$):

$$S_q = w_p \cdot P_q + w_e \cdot (1.0 - H_q)$$

*(Methodology defaults: $w_p = 0.6$, $w_e = 0.4$)*

#### 4. Composite CSP Score:

$$\text{CSP} = 100 \times \frac{1}{M}\sum_{q \in Q} S_q$$

### 5.2 Assumptions & Explicit Limitations

* **Assumptions**:
  1. Dense vector similarity in a local vector space (e.g. bge-small-en-v1.5 or hashed n-gram TF) acts as a proxy for dense retrieval candidate scoring.
  2. Clear winner passages with peaked softmax distributions have higher likelihood of surviving multi-document context truncation.
* **Limitations**:
  1. **Uncalibrated**: CSP is NOT a statistical likelihood of citation by live LLM engines (ChatGPT, Perplexity, Gemini, Claude).
  2. **No Web Index Rank**: Does not model web search index rank, link equity, domain authority, or multi-site candidate retrieval.
  3. **No Generative Reasoning**: Does not simulate post-retrieval LLM instruction following, synthesis, or source citation filtering.

---

## 6. Configurable Heuristic Thresholds

All heuristic thresholds are configurable programmatically via `SageConfig` or via CLI `--config-file config.json`:

```python
from sage_audit import SageAuditor, SageConfig

config = SageConfig(
    word_count_target=800,
    chunk_min_tokens=50,
    chunk_max_tokens=150,
    csp_prominence_weight=0.7,
    csp_entropy_weight=0.3,
    csp_pass_threshold=75.0,
)
auditor = SageAuditor(config=config)
report = auditor.audit("https://example.com")
```

---

## 7. Empirical Validation & Statistical Calibration Framework

SAGE includes an empirical validation engine in `sage_audit.validation` to evaluate SAGE / CSP scores against real observed AI search citation outcomes:

$$\text{ValidationResult} = \text{evaluate\_sage\_vs\_observed}(\mathbf{y}_{\text{pred}}, \mathbf{y}_{\text{obs}}, k=5)$$

### Statistical Metrics:

1. **Spearman Rank Correlation ($\rho, p$)**:
   $$\rho = 1 - \frac{6 \sum d_i^2}{n(n^2 - 1)}$$
   Assesses monotonic ranking concordance between SAGE scores and observed citation frequency.
2. **Area Under the ROC Curve (AUROC)**:
   Measures discriminative ability to separate cited URLs from non-cited URLs (0.5 = random, 1.0 = perfect separation).
3. **Precision@k**:
   Calculates citation precision among the top-$k$ highest-scoring pages.
4. **Brier Score (Mean Squared Calibration Error)**:
   $$\text{BS} = \frac{1}{N} \sum_{i=1}^N (P_i - Y_i)^2$$
   Measures squared probability calibration error against binary citation outcomes.
5. **Calibration Bins (0–20%, 20–40%, 40–60%, 60–80%, 80–100%)**:
   Breaks predictions into 5 probability intervals to compare mean predicted score vs observed empirical positive rate.

---

## 8. Provenance & Serialization

Every SAGE report exports full machine-readable provenance in JSON format:
- `methodology_version`: `"2.0.0"`
- `validation_status`: `"unvalidated"` (or `"validated"` if evaluated against a benchmark dataset)
- Every finding contains its complete `evidence` block.
- GEO metrics expose complete `csp_details` specifying formula, weights, assumptions, and limitations.
