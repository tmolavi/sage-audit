"""Pillar 2 — Answer Engine Optimization (AEO).

Deep JSON-LD entity-graph validation, entity authority (sameAs) analysis,
FAQ structuring checks, and direct-answer density: do the first 50–70
words of each section state an explicit, factual, fluff-free answer?

Every finding carries explicit epistemic Evidence Taxonomy metadata (E1–E4)
and never asserts unproven direct ranking-factor claims.

(c) 2026 Taqi Molavi — https://molavi.pro — MIT License
"""

from __future__ import annotations

import re
import time
from typing import Any, Iterable, Iterator, Optional

from sage_audit.config import SageConfig
from sage_audit.models import (
    EvidenceLevel,
    EvidenceMetadata,
    Finding,
    PillarReport,
    Status,
    finalize_pillar,
)
from sage_audit.utils.extractor import PageSnapshot, Section
from sage_audit.utils.text import mean, split_sentences

# ---------------------------------------------------------------------------
# Entity-graph helpers (also reused by the GEO pillar to derive sim queries)
# ---------------------------------------------------------------------------

def iter_entity_nodes(json_ld: Iterable[Any]) -> Iterator[dict[str, Any]]:
    """Yield every typed node (``@type``) in a JSON-LD corpus, recursively.

    Traverses top-level objects, arrays, ``@graph`` collections and nested
    objects (e.g. Question/Answer inside FAQPage). JSON is acyclic, so a
    simple stack walk is complete and safe.
    """

    stack: list[Any] = list(json_ld)
    while stack:
        node = stack.pop()
        if isinstance(node, list):
            stack.extend(node)
        elif isinstance(node, dict):
            if "@type" in node:
                yield node
            for value in node.values():
                if isinstance(value, (dict, list)):
                    stack.append(value)


def node_types(node: dict[str, Any]) -> set[str]:
    """Normalize a node's ``@type`` (str or list) to a set of strings."""

    raw = node.get("@type", [])
    if isinstance(raw, str):
        return {raw}
    if isinstance(raw, list):
        return {str(item) for item in raw}
    return set()


def flatten_same_as(nodes: Iterable[dict[str, Any]]) -> list[str]:
    """Collect every sameAs URL across an entity graph."""

    urls: list[str] = []
    for node in nodes:
        value = node.get("sameAs")
        if isinstance(value, str):
            urls.append(value)
        elif isinstance(value, list):
            urls.extend(str(item) for item in value if isinstance(item, str))
    return urls


# ---------------------------------------------------------------------------
# AEO knowledge bases
# ---------------------------------------------------------------------------

#: Entity types the audit scans for (with generous subtype acceptance).
TARGET_TYPES: dict[str, set[str]] = {
    "Organization": {"Organization", "Corporation", "LocalBusiness", "NGO"},
    "Person": {"Person"},
    "Product": {"Product", "Service", "SoftwareApplication"},
    "Article": {"Article", "NewsArticle", "BlogPosting", "TechArticle", "Report"},
    "FAQPage": {"FAQPage", "QAPage"},
}

#: Fields that make a primary entity machine-usable, per family.
COMPLETENESS_FIELDS: dict[str, tuple[str, ...]] = {
    "Organization": ("name", "url", "logo", "description", "sameAs", "@id"),
    "Person": ("name", "url", "image", "description", "sameAs", "jobTitle"),
    "Product": ("name", "url", "image", "description", "brand", "offers"),
    "Article": ("headline", "datePublished", "dateModified", "author", "image", "@id"),
}

#: Authority domains that disambiguate entities for knowledge graphs.
AUTHORITY_DOMAINS: dict[str, tuple[str, ...]] = {
    "Wikidata": ("wikidata.org",),
    "Wikipedia": ("wikipedia.org",),
    "Crunchbase": ("crunchbase.com",),
    "LinkedIn": ("linkedin.com",),
    "X/Twitter": ("twitter.com", "x.com"),
    "Facebook": ("facebook.com",),
    "Instagram": ("instagram.com",),
    "YouTube": ("youtube.com",),
    "GitHub": ("github.com",),
}

#: Fluff openers that answer engines have learned to skip.
FLUFF_PHRASES: tuple[str, ...] = (
    "in today's fast-paced world",
    "in todays fast paced world",
    "in this article",
    "this article will",
    "as we all know",
    "welcome to",
    "welcome back",
    "without further ado",
    "let's dive in",
    "lets dive in",
    "first and foremost",
    "at the end of the day",
    "needless to say",
    "it goes without saying",
    "have you ever wondered",
    "in the digital age",
    "in this day and age",
    "now more than ever",
    "look no further",
    "buckle up",
)

DEFINITIONAL_RE = re.compile(
    r"\b(?:is|are|was|were|means|refers to|describes|defined as|"
    r"consists of|comprises|represents|provides|enables|offers)\b",
    re.IGNORECASE,
)
QUESTION_START_RE = re.compile(
    r"^(?:who|what|why|how|when|where|which|whose|whom|"
    r"is|are|was|were|do|does|did|can|could|should|will|would)\b",
    re.IGNORECASE,
)
NUMERIC_RE = re.compile(r"\d")


def is_question_heading(text: Optional[str]) -> bool:
    """True when a heading reads like a question (Latin + Persian marks)."""

    if not text:
        return False
    stripped = text.strip()
    return stripped.endswith(("?", "؟")) or bool(QUESTION_START_RE.match(stripped))


def answer_quality(
    section: Section,
    word_window: int = 70,
    min_words: int = 8,
) -> tuple[float, str]:
    """Score the direct-answer quality of a section's first ~70 words.

    Composite heuristic (0–1):
      +0.35  first sentence is definitional/declarative ("X is …")
      +0.20  factual payload present (numbers, dates, percentages)
      +0.15  crisp sentences (8–35 words average over first 3 sentences)
      +0.15  question heading answered directly in sentence one
      -0.25  per fluff phrase detected
      (base 0.15; clamped to [0, 1])
    """

    words = section.text.split()
    if len(words) < min_words:
        return 0.1, f"section too thin to answer (<{min_words} words)"

    window = " ".join(words[:word_window])
    sentences = [s for s in split_sentences(window) if s]
    first = sentences[0] if sentences else window

    definitional = bool(DEFINITIONAL_RE.search(first))
    factual = bool(NUMERIC_RE.search(window))
    sample = sentences[:3] or [window]
    avg_sentence = mean([float(len(s.split())) for s in sample])
    crisp = 8.0 <= avg_sentence <= 35.0
    fluff_hits = sum(1 for phrase in FLUFF_PHRASES if phrase in window.lower())
    question_bonus = is_question_heading(section.heading) and definitional

    score = (
        0.15
        + 0.35 * definitional
        + 0.20 * factual
        + 0.15 * crisp
        + (0.15 if question_bonus else 0.0)
        - 0.25 * fluff_hits
    )
    score = max(0.0, min(1.0, score))
    note = (
        f"definitional={'✓' if definitional else '✗'}, "
        f"factual={'✓' if factual else '✗'}, "
        f"crisp={'✓' if crisp else '✗'} ({avg_sentence:.0f}w/sent), "
        f"fluff={fluff_hits}"
    )
    return score, note


# ---------------------------------------------------------------------------
# The auditor
# ---------------------------------------------------------------------------

class AeoAuditor:
    """Executes all Pillar-2 (AEO) checks against a :class:`PageSnapshot`."""

    pillar_name = "Pillar 2 — Answer Engine Optimization (AEO)"

    def __init__(self, config: Optional[SageConfig] = None) -> None:
        self.config = config or SageConfig()

    def audit(self, snap: PageSnapshot) -> PillarReport:
        started = time.perf_counter()
        nodes = list(iter_entity_nodes(snap.json_ld))
        type_index = self._index_types(nodes)

        findings = [
            self._check_jsonld_presence(snap),
            self._check_entity_graph(type_index),
            self._check_entity_completeness(nodes, type_index),
            self._check_authority_signals(nodes),
            self._check_faq_structuring(snap, type_index),
            self._check_direct_answer_density(snap),
            self._check_freshness(snap, nodes),
            self._check_entity_linking(nodes),
        ]
        per_section_scores = [
            {
                "section": (section.heading or "Introduction"),
                "score": round(score, 3),
                "signals": note,
            }
            for section in snap.sections
            if section.word_count >= self.config.direct_answer_min_words
            for score, note in [
                answer_quality(
                    section,
                    word_window=self.config.direct_answer_word_window,
                    min_words=self.config.direct_answer_min_words,
                )
            ]
        ]
        metrics = {
            "json_ld_blocks": len(snap.json_ld),
            "json_ld_parse_errors": snap.json_ld_errors,
            "entity_nodes": len(nodes),
            "entity_types": sorted({t for types in type_index for t in types}),
            "question_headings": sum(
                1 for _, text in snap.headings if is_question_heading(text)
            ),
            "section_answer_scores": per_section_scores,
        }
        return finalize_pillar("aeo", self.pillar_name, findings, metrics=metrics, started=started)

    # ------------------------------------------------------------------ #

    @staticmethod
    def _index_types(nodes: list[dict[str, Any]]) -> list[set[str]]:
        return [node_types(node) for node in nodes]

    @staticmethod
    def _families_found(type_index: list[set[str]]) -> dict[str, set[str]]:
        found: dict[str, set[str]] = {}
        for family, members in TARGET_TYPES.items():
            matched = set()
            for types in type_index:
                matched |= types & members
            if matched:
                found[family] = matched
        return found

    def _check_jsonld_presence(self, snap: PageSnapshot) -> Finding:
        blocks = len(snap.json_ld)
        evidence = EvidenceMetadata(
            level=EvidenceLevel.E1,
            evidence_type="standards_backed",
            source="W3C JSON-LD 1.1 / Schema.org Syntax",
            ranking_factor_claim=False,
            signal_type="standards_compliance",
            configurable=False,
        )
        if blocks == 0:
            return Finding(
                check_id="aeo.jsonld_presence",
                title="JSON-LD structured data",
                status=Status.FAIL,
                score=0.0,
                weight=10.0,
                details="No parseable application/ld+json blocks found"
                + (f" ({snap.json_ld_errors} malformed block(s) skipped)."
                   if snap.json_ld_errors else "."),
                recommendation="Publish JSON-LD (Organization + WebSite at minimum). Without "
                "an explicit entity graph, answer engines must rely on heuristic text extraction.",
                evidence=evidence,
            )
        details = f"{blocks} JSON-LD block(s) parsed"
        if snap.json_ld_errors:
            details += f"; {snap.json_ld_errors} block(s) failed to parse"
        return Finding(
            check_id="aeo.jsonld_presence",
            title="JSON-LD structured data",
            status=Status.PASS if not snap.json_ld_errors else Status.WARN,
            score=1.0 if not snap.json_ld_errors else 0.6,
            weight=10.0,
            details=details + ".",
            recommendation="" if not snap.json_ld_errors else
            "Fix the malformed JSON-LD block(s) — syntax errors prevent parsing in strict JSON-LD processors.",
            evidence=evidence,
        )

    def _check_entity_graph(self, type_index: list[set[str]]) -> Finding:
        found = self._families_found(type_index)
        coverage = len(found) / len(TARGET_TYPES)
        evidence = EvidenceMetadata(
            level=EvidenceLevel.E1,
            evidence_type="standards_backed",
            source="Schema.org Core Entity Types",
            ranking_factor_claim=False,
            signal_type="standards_compliance",
            configurable=False,
        )
        if not found:
            return Finding(
                check_id="aeo.entity_graph",
                title="Entity-graph coverage",
                status=Status.FAIL,
                score=0.0,
                weight=8.0,
                details="No Organization, Person, Product, Article or FAQPage entities found.",
                recommendation="Model the page's core entity in JSON-LD — answer engines "
                "ground their citations on explicit entity relationships.",
                evidence=evidence,
            )
        listing = "; ".join(f"{family} ({', '.join(sorted(types))})"
                            for family, types in sorted(found.items()))
        status = Status.PASS if coverage >= 0.5 else Status.WARN
        return Finding(
            check_id="aeo.entity_graph",
            title="Entity-graph coverage",
            status=status,
            score=min(1.0, 0.4 + coverage),
            weight=8.0,
            details=listing + ".",
            recommendation="" if coverage >= 0.5 else
            "Broaden the graph: Organization, Person, Product and Article entities let "
            "answer engines resolve the page's subject without disambiguation ambiguity.",
            evidence=evidence,
        )

    def _check_entity_completeness(
        self, nodes: list[dict[str, Any]], type_index: list[set[str]]
    ) -> Finding:
        evidence = EvidenceMetadata(
            level=EvidenceLevel.E2,
            evidence_type="platform_guidance",
            source="Google Structured Data Guidelines & Knowledge Graph Standards",
            ranking_factor_claim=False,
            signal_type="retrieval_readiness_signal",
            configurable=False,
        )
        primary: Optional[dict[str, Any]] = None
        expected: tuple[str, ...] = ()
        family_picked = ""
        for family, members in TARGET_TYPES.items():
            if family == "FAQPage":
                continue
            for node, types in zip(nodes, type_index):
                if types & members:
                    primary = node
                    expected = COMPLETENESS_FIELDS.get(family, ("name", "@id", "sameAs"))
                    family_picked = family
                    break
            if primary:
                break
        if primary is None:
            return Finding(
                check_id="aeo.entity_completeness",
                title="Primary-entity completeness",
                status=Status.FAIL,
                score=0.0,
                weight=8.0,
                details="No primary entity (Organization/Person/Product/Article) to evaluate.",
                recommendation="Declare a primary entity with name, url, image, description "
                "and sameAs so answer engines can reliably extract entity properties.",
                evidence=evidence,
            )
        present = [field for field in expected if primary.get(field)]
        missing = [field for field in expected if not primary.get(field)]
        score = len(present) / len(expected)
        status = Status.PASS if score >= 0.8 else (Status.WARN if score >= 0.5 else Status.FAIL)
        return Finding(
            check_id="aeo.entity_completeness",
            title="Primary-entity completeness",
            status=status,
            score=score,
            weight=8.0,
            details=f"{family_picked} entity: {len(present)}/{len(expected)} key fields "
            f"— present: {', '.join(present)}"
            + (f"; missing: {', '.join(missing)}" if missing else "") + ".",
            recommendation="" if not missing else
            f"Fill the missing {family_picked} fields ({', '.join(missing)}); complete "
            "attributes improve knowledge graph linking confidence.",
            evidence=evidence,
        )

    def _check_authority_signals(self, nodes: list[dict[str, Any]]) -> Finding:
        urls = flatten_same_as(nodes)
        matched = {
            label for label, domains in AUTHORITY_DOMAINS.items()
            if any(domain in url.lower() for url in urls for domain in domains)
        }
        count = len(matched)
        target = self.config.authority_sameas_target_count
        evidence = EvidenceMetadata(
            level=EvidenceLevel.E1,
            evidence_type="standards_backed",
            source="Schema.org sameAs Reference / Linked Data Principles",
            ranking_factor_claim=False,
            signal_type="standards_compliance",
            configurable=True,
        )
        if count >= target:
            score, status, rec = 1.0, Status.PASS, ""
        elif count == 2:
            score, status, rec = 0.75, Status.WARN, (
                f"Add Wikidata/Crunchbase cross-references — {target}+ authority sameAs links "
                "materially raise entity-disambiguation confidence."
            )
        elif count == 1:
            score, status, rec = 0.5, Status.WARN, (
                "Only one authority reference found; add Wikidata, Wikipedia and official "
                "profiles so knowledge graphs can anchor the entity."
            )
        else:
            score, status, rec = 0.0, Status.FAIL, (
                "No sameAs authority links found. Link the entity to Wikidata, Wikipedia "
                "and official profiles to establish verified external entity references."
            )
        return Finding(
            check_id="aeo.authority_sameas",
            title="Entity authority (sameAs)",
            status=status,
            score=score,
            weight=10.0,
            details=(
                f"{len(urls)} sameAs URL(s); authority anchors: "
                f"{', '.join(sorted(matched)) if matched else 'none'}."
            ),
            recommendation=rec,
            evidence=evidence,
        )

    def _check_faq_structuring(
        self, snap: PageSnapshot, type_index: list[set[str]]
    ) -> Finding:
        has_faq_schema = any(types & TARGET_TYPES["FAQPage"] for types in type_index)
        question_headings = [text for _, text in snap.headings if is_question_heading(text)]
        evidence = EvidenceMetadata(
            level=EvidenceLevel.E2,
            evidence_type="platform_guidance",
            source="Schema.org FAQPage & Google Search Q&A Specification",
            ranking_factor_claim=False,
            signal_type="retrieval_readiness_signal",
            configurable=False,
        )
        if has_faq_schema:
            return Finding(
                check_id="aeo.faq_structuring",
                title="FAQ structuring",
                status=Status.PASS,
                score=1.0,
                weight=6.0,
                details=f"FAQPage/QAPage schema present; {len(question_headings)} "
                "question-style heading(s) in body copy.",
                recommendation="",
                evidence=evidence,
            )
        if len(question_headings) >= 2:
            return Finding(
                check_id="aeo.faq_structuring",
                title="FAQ structuring",
                status=Status.WARN,
                score=0.6,
                weight=6.0,
                details=f"{len(question_headings)} question-style headings found but no "
                "FAQPage schema marks them up.",
                recommendation="Wrap the existing Q&A content in FAQPage JSON-LD to explicitly "
                "pair questions with answers for machine consumption.",
                evidence=evidence,
            )
        return Finding(
            check_id="aeo.faq_structuring",
            title="FAQ structuring",
            status=Status.WARN,
            score=0.4,
            weight=6.0,
            details="Neither FAQPage schema nor question-style headings detected.",
            recommendation="Add a Q&A block (real user questions, direct 40–70 word answers) and "
            "mark it up as FAQPage for explicit question-answer pairing.",
            evidence=evidence,
        )

    def _check_direct_answer_density(self, snap: PageSnapshot) -> Finding:
        min_words = self.config.direct_answer_min_words
        window_size = self.config.direct_answer_word_window
        target_density = self.config.direct_answer_target_density
        min_density = self.config.direct_answer_min_density

        sections = [s for s in snap.sections if s.word_count >= min_words]
        evidence = EvidenceMetadata(
            level=EvidenceLevel.E4,
            evidence_type="industry_heuristic",
            source="Direct Answer & Information Extraction Optimization (VPA)",
            ranking_factor_claim=False,
            signal_type="industry_heuristic",
            configurable=True,
        )
        if not sections:
            return Finding(
                check_id="aeo.direct_answer_density",
                title="Direct-answer density",
                status=Status.FAIL,
                score=0.0,
                weight=14.0,
                details="No substantive sections to analyze.",
                recommendation=f"Structure the page as headed sections whose first {window_size} "
                "words contain a self-contained, factual answer.",
                evidence=evidence,
            )
        scored = [
            answer_quality(section, word_window=window_size, min_words=min_words)
            for section in sections
        ]
        density = round(mean([score for score, _ in scored]), 3)
        definitional_openers = sum(1 for score, _ in scored if score >= 0.5)
        weakest_idx = min(range(len(scored)), key=lambda i: scored[i][0])
        weakest = sections[weakest_idx]
        if density >= target_density:
            status = Status.PASS
            rec = ""
        elif density >= min_density:
            status = Status.WARN
            rec = (f"Open every section with a {window_size}-word self-contained answer (definition "
                   "+ key fact/data). Avoid rhetorical warm-ups to facilitate direct answer extraction.")
        else:
            status = Status.FAIL
            rec = ("Sections open with conversational fluff instead of direct factual answers. "
                   "Rewrite section opening sentences declaratively ('X is/provides …') for clean answer extraction.")
        return Finding(
            check_id="aeo.direct_answer_density",
            title="Direct-answer density",
            status=status,
            score=density,
            weight=14.0,
            details=f"{len(sections)} sections analyzed · avg first-window answer score "
            f"{density:.2f} · {definitional_openers}/{len(sections)} open with an explicit "
            f"answer · weakest: “{weakest.heading or 'Introduction'}” "
            f"({scored[weakest_idx][1]}).",
            recommendation=rec,
            evidence=evidence,
        )

    def _check_freshness(
        self, snap: PageSnapshot, nodes: list[dict[str, Any]]
    ) -> Finding:
        evidence = EvidenceMetadata(
            level=EvidenceLevel.E2,
            evidence_type="platform_guidance",
            source="Google / Schema.org Temporal Metadata Guidance",
            ranking_factor_claim=False,
            signal_type="retrieval_readiness_signal",
            configurable=False,
        )
        date_fields = ("datePublished", "dateModified", "dateCreated", "uploadDate")
        schema_dates = [node[f] for node in nodes for f in date_fields if node.get(f)]
        meta_dates = [
            value
            for key, value in snap.meta.items()
            if key in ("article:published_time", "article:modified_time", "date",
                       "publish_date", "last-modified")
        ]
        html_time = bool(
            re.search(r'<time[^>]+datetime\s*=', snap.html or "", re.IGNORECASE)
        )
        found = schema_dates or meta_dates or ([html_time] if html_time else [])
        if found:
            sample = str((schema_dates or meta_dates or ["<time datetime>"])[0])
            return Finding(
                check_id="aeo.freshness",
                title="Machine-readable freshness",
                status=Status.PASS,
                score=1.0,
                weight=4.0,
                details=f"Date signal found ({sample[:40]}).",
                recommendation="",
                evidence=evidence,
            )
        return Finding(
            check_id="aeo.freshness",
            title="Machine-readable freshness",
            status=Status.WARN,
            score=0.3,
            weight=4.0,
            details="No datePublished/dateModified/meta dates/<time datetime> found.",
            recommendation="Expose machine-readable timestamps (JSON-LD dateModified preferred) "
            "to establish publication and update freshness.",
            evidence=evidence,
        )

    def _check_entity_linking(self, nodes: list[dict[str, Any]]) -> Finding:
        evidence = EvidenceMetadata(
            level=EvidenceLevel.E1,
            evidence_type="standards_backed",
            source="W3C Linked Data / Schema.org @id Graph Identity",
            ranking_factor_claim=False,
            signal_type="standards_compliance",
            configurable=False,
        )
        with_ids = [node for node in nodes if node.get("@id")]
        with_links = [
            node for node in nodes if node.get("about") or node.get("mentions")
        ]
        if not nodes:
            return Finding(
                check_id="aeo.entity_linking",
                title="Entity linking (@id/about/mentions)",
                status=Status.INFO,
                score=0.0,
                weight=0.0,
                details="No entity graph to inspect.",
                recommendation="",
                evidence=evidence,
            )
        ratio = len(with_ids) / max(len(nodes), 1)
        score = min(1.0, ratio + 0.25 * bool(with_links) + 0.1 * bool(with_ids))
        status = Status.PASS if score >= 0.8 else (Status.WARN if score >= 0.4 else Status.FAIL)
        return Finding(
            check_id="aeo.entity_linking",
            title="Entity linking (@id/about/mentions)",
            status=status,
            score=score,
            weight=3.0,
            details=f"{len(with_ids)}/{len(nodes)} nodes carry stable @id anchors; "
            f"{len(with_links)} use about/mentions cross-links.",
            recommendation="" if score >= 0.8 else
            "Assign entities stable @id URIs (#org, #product) and cross-reference them with "
            "about/mentions for connected graph traversal.",
            evidence=evidence,
        )
