"""Pillar 3 — Generative Engine Optimization (GEO).

Five-layer GEO pyramid:

    L1  Clean DOM extraction (shared :class:`PageSnapshot`)
    L2  Semantic passage chunking on approximate token boundaries (60–120)
    L3  Vector embeddings — fastembed → sentence-transformers → deterministic
        hashed n-gram TF fallback (the pipeline *never* crashes)
    L4  In-memory RAG retrieval simulation against derived entity queries
    L5  Citation Survival Probability + auto-generated llms.txt /
        rag_ready_chunks.json

Citation Survival Probability (CSP) aggregates, per simulated query:
  * retrieval prominence — z-score of the best chunk's cosine similarity vs.
    the similarity distribution (is there a clear winner?), and
  * (1 - normalized semantic entropy) of the similarity softmax (how diffuse
    is the retriever's attention?).
CSP = mean(0.6 * prominence + 0.4 * (1 - entropy)) × 100.

(c) 2026 Taqi Molavi — https://molavi.pro — MIT License
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import time
from dataclasses import dataclass
from typing import Any, Optional, Sequence

from sage_audit._version import __version__
from sage_audit.auditors.aeo_auditor import iter_entity_nodes
from sage_audit.models import Finding, PillarReport, Status, finalize_pillar
from sage_audit.utils.extractor import PageSnapshot, Section
from sage_audit.utils.text import (
    LOWER_TOKEN_RE,
    count_tokens,
    cosine_similarity,
    mean,
    normalized_softmax_entropy,
    split_sentences,
    stddev,
    truncate,
)

logger = logging.getLogger("sage_audit.geo")


# ---------------------------------------------------------------------------
# Semantic chunking
# ---------------------------------------------------------------------------

@dataclass
class Chunk:
    """One retrievable passage."""

    index: int
    id: str
    text: str
    token_count: int
    heading: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "index": self.index,
            "heading": self.heading,
            "token_count": self.token_count,
            "char_count": len(self.text),
            "text": self.text,
        }


def _slice_oversized(sentence: str, max_tokens: int) -> list[str]:
    """Hard-split a sentence that alone exceeds ``max_tokens``."""

    words = sentence.split()
    # ~0.75 words per token keeps slices comfortably below the token ceiling.
    step = max(8, int(max_tokens * 0.6))
    return [" ".join(words[i:i + step]) for i in range(0, len(words), step)]


def chunk_sections(
    sections: Sequence[Section],
    min_tokens: int = 60,
    max_tokens: int = 120,
    overlap: int = 25,
    fallback_text: str = "",
) -> list[Chunk]:
    """Pack heading-anchored sentences into 60–120 token passages.

    Sentence-aware packing with a rolling carry-buffer (sections may share a
    chunk), trailing-sentence overlap for context continuity, and tail-merge
    so no orphan micro-chunk is left behind.
    """

    overlap = max(0, min(overlap, min_tokens // 2))

    units: list[tuple[Optional[str], str]] = []
    source = list(sections)
    if not source and fallback_text.strip():
        source = [Section(heading=None, level=0, text=fallback_text,
                          word_count=len(fallback_text.split()))]
    for section in source:
        if not section.text.strip():
            continue
        for sentence in split_sentences(section.text):
            if not sentence:
                continue
            if count_tokens(sentence) > max_tokens:
                for piece in _slice_oversized(sentence, max_tokens):
                    units.append((section.heading, piece))
            else:
                units.append((section.heading, sentence))

    chunks: list[Chunk] = []
    buffer: list[str] = []
    buffer_tokens = 0
    buffer_heading: Optional[str] = None

    def flush() -> None:
        nonlocal buffer, buffer_tokens
        text = " ".join(buffer).strip()
        if text:
            chunks.append(
                Chunk(
                    index=len(chunks),
                    id=f"chunk-{len(chunks):03d}",
                    text=text,
                    token_count=count_tokens(text),
                    heading=buffer_heading,
                )
            )
        # Seed next chunk with trailing sentences up to the overlap budget.
        seed: list[str] = []
        seed_tokens = 0
        for sentence in reversed(buffer):
            sentence_tokens = count_tokens(sentence)
            if seed_tokens + sentence_tokens > overlap:
                break
            seed.insert(0, sentence)
            seed_tokens += sentence_tokens
        buffer = seed
        buffer_tokens = seed_tokens

    for heading, sentence in units:
        sentence_tokens = count_tokens(sentence)
        if (
            buffer
            and buffer_tokens + sentence_tokens > max_tokens
            and buffer_tokens >= min_tokens // 2
        ):
            flush()
        if buffer_heading is None:
            buffer_heading = heading
        buffer.append(sentence)
        buffer_tokens += sentence_tokens
        if heading != buffer_heading and buffer_tokens < min_tokens:
            buffer_heading = heading  # small chunk drifts to the newer section
    flush()

    # Merge a trailing micro-chunk into its predecessor when this does not
    # blow the size envelope past max_tokens + min_tokens // 2.
    while len(chunks) >= 2 and chunks[-1].token_count < min_tokens:
        previous, last = chunks[-2], chunks[-1]
        if previous.token_count + last.token_count > max_tokens + min_tokens // 2:
            break
        merged_text = f"{previous.text} {last.text}"
        chunks[-2] = Chunk(
            index=previous.index,
            id=previous.id,
            text=merged_text,
            token_count=count_tokens(merged_text),
            heading=previous.heading,
        )
        chunks.pop()

    for index, chunk in enumerate(chunks):  # normalize ids after merges
        chunk.index = index
        chunk.id = f"chunk-{index:03d}"
    return chunks


# ---------------------------------------------------------------------------
# Embedding backends — graceful degradation chain
# ---------------------------------------------------------------------------

class HashingVectorBackend:
    """Deterministic hashed n-gram TF vectorizer (zero dependencies).

    Token unigrams + bigrams are hashed (BLAKE2b — stable across processes,
    unlike Python's salted ``hash()``) into a fixed-dimension vector with
    sublinear TF and L2 normalization. Cosine similarity over these vectors
    is a solid lexical-retrieval stand-in when neural embeddings are absent.
    """

    display = "hashed-ngram-tf (deterministic fallback)"

    def __init__(self, dim: int = 1024) -> None:
        self.dim = dim

    def _features(self, text: str) -> list[str]:
        tokens = LOWER_TOKEN_RE.findall(text.lower())
        bigrams = [f"{a}~{b}" for a, b in zip(tokens, tokens[1:])]
        return tokens + bigrams

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            vec = [0.0] * self.dim
            for feature in self._features(text):
                digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
                vec[int.from_bytes(digest, "big") % self.dim] += 1.0
            vec = [math.log1p(value) if value > 0.0 else 0.0 for value in vec]
            norm = math.sqrt(sum(value * value for value in vec)) or 1.0
            vectors.append([value / norm for value in vec])
        return vectors


class FastEmbedBackend:
    """Local ONNX embeddings via fastembed (BAAI/bge-small-en-v1.5)."""

    display = "fastembed (BAAI/bge-small-en-v1.5)"

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5") -> None:
        from fastembed import TextEmbedding  # type: ignore

        self._model = TextEmbedding(model_name=model_name)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [
            [float(x) for x in vector]
            for vector in self._model.embed(list(texts))
        ]


class SentenceTransformersBackend:
    """sentence-transformers backend (all-MiniLM-L6-v2)."""

    display = "sentence-transformers (all-MiniLM-L6-v2)"

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        from sentence_transformers import SentenceTransformer  # type: ignore

        self._model = SentenceTransformer(model_name)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        encoded = self._model.encode(list(texts), convert_to_numpy=True)
        return [[float(x) for x in vector] for vector in encoded.tolist()]


_BACKEND_REGISTRY = {
    "fastembed": FastEmbedBackend,
    "sentence-transformers": SentenceTransformersBackend,
    "hashing": HashingVectorBackend,
}


def resolve_backend(prefer: str = "auto") -> Any:
    """Pick the best available embedding backend; never raises.

    Order for ``auto``: fastembed → sentence-transformers → hashing fallback.
    """

    if prefer != "auto":
        cls = _BACKEND_REGISTRY[prefer]
        try:
            return cls()
        except Exception as exc:  # pragma: no cover - env dependent
            logger.warning("Requested backend %s unavailable (%s); using fallback.",
                           prefer, exc)
            return HashingVectorBackend()
    for cls in (FastEmbedBackend, SentenceTransformersBackend):
        try:
            backend = cls()
            logger.info("GEO embedding backend: %s", backend.display)
            return backend
        except Exception as exc:
            logger.debug("Embedding backend %s unavailable: %s", cls.display, exc)
    logger.info("GEO embedding backend: %s", HashingVectorBackend.display)
    return HashingVectorBackend()


# ---------------------------------------------------------------------------
# RAG retrieval simulation
# ---------------------------------------------------------------------------

def build_queries(snap: PageSnapshot, max_queries: int = 8) -> list[str]:
    """Derive probe queries a RAG pipeline might issue against this page."""

    queries: list[str] = []

    def add(candidate: str) -> None:
        candidate = " ".join(candidate.split()).strip(" –—-|")
        if len(candidate) >= 8 and candidate.lower() not in {q.lower() for q in queries}:
            queries.append(candidate)

    if snap.title:
        add(snap.title)
    for level, text in snap.headings:
        if level == 1:
            add(text)
    entity_names: list[str] = []
    for node in iter_entity_nodes(snap.json_ld):
        name = node.get("name") or node.get("headline")
        if isinstance(name, str) and 3 <= len(name) <= 80:
            entity_names.append(name)
    for name in entity_names[:2]:
        add(f"What is {name}?")
    for level, text in snap.headings:
        if text.strip().endswith(("?", "؟")):
            add(text)
    if snap.meta_description:
        first = split_sentences(snap.meta_description)
        if first:
            add(first[0])
    for level, text in snap.headings:
        if level in (2, 3):
            add(text)
    return queries[:max_queries]


def simulate_rag(
    queries: Sequence[str],
    chunks: Sequence[Chunk],
    embedder: Any,
    top_k: int = 3,
) -> dict[str, Any]:
    """Simulate dense retrieval of ``chunks`` for each query.

    Returns per-query diagnostics plus aggregate CSP / entropy / coverage.
    """

    if not queries or not chunks:
        return {
            "per_query": [],
            "csp": None,
            "avg_entropy": None,
            "retrieval_coverage": None,
            "backend": getattr(embedder, "display", "unknown"),
        }

    query_vectors = embedder.embed(list(queries))
    chunk_vectors = embedder.embed([chunk.text for chunk in chunks])

    per_query: list[dict[str, Any]] = []
    retrieved: set[int] = set()
    entropies: list[float] = []
    survivals: list[float] = []

    for query, q_vec in zip(queries, query_vectors):
        sims = [cosine_similarity(q_vec, c_vec) for c_vec in chunk_vectors]
        order = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)
        k = max(1, min(top_k, len(order)))
        top = order[:k]
        retrieved.update(top)

        if len(sims) > 1:
            spread = stddev(sims)
            dispersion = (sims[order[0]] - mean(sims)) / (spread + 1e-9)
            # Adaptive temperature: entropy is measured relative to the
            # similarity spread, so genuinely diffuse rankings score ~1 and
            # peaked rankings ~0 regardless of absolute cosine magnitudes.
            entropy = normalized_softmax_entropy(sims, temperature=max(spread, 1e-9))
        else:
            dispersion = 1.5  # single-chunk corpus: neutral prominence
            entropy = 0.0
        prominence = max(0.0, min(1.0, dispersion / 3.0))
        survival = 0.6 * prominence + 0.4 * (1.0 - entropy)

        entropies.append(entropy)
        survivals.append(survival)
        per_query.append(
            {
                "query": query,
                "top_chunk": chunks[order[0]].id,
                "top_similarity": round(sims[order[0]], 4),
                "top_k_chunks": [chunks[i].id for i in top],
                "retrieval_prominence": round(prominence, 3),
                "semantic_entropy": round(entropy, 3),
                "survival_probability": round(survival, 3),
            }
        )

    return {
        "per_query": per_query,
        "csp": round(100.0 * mean(survivals), 1),
        "avg_entropy": round(mean(entropies), 3),
        "retrieval_coverage": round(len(retrieved) / len(chunks), 3),
        "backend": getattr(embedder, "display", "unknown"),
    }


# ---------------------------------------------------------------------------
# Artifact generation
# ---------------------------------------------------------------------------

def build_llms_txt(
    snap: PageSnapshot, chunks: Sequence[Chunk], simulation: dict[str, Any]
) -> str:
    """Render an llms.txt manifest (llmstxt.org convention)."""

    lines: list[str] = [f"# {snap.title or snap.url}", ""]
    if snap.meta_description:
        lines.append(f"> {snap.meta_description}")
        lines.append("")
    if chunks:
        intro = truncate(chunks[0].text, 320)
        lines.append(intro)
        lines.append("")

    grouped: dict[str, list[Chunk]] = {}
    for chunk in chunks:
        grouped.setdefault(chunk.heading or "Overview", []).append(chunk)
    for heading, items in grouped.items():
        lines.append(f"## {heading}")
        for chunk in items:
            first = split_sentences(chunk.text)
            digest = truncate(first[0] if first else chunk.text, 220)
            lines.append(f"- {digest} [{chunk.id}]")
        lines.append("")

    csp = simulation.get("csp")
    lines.append("---")
    lines.append(f"Generated by sage-audit v{__version__} — https://molavi.pro")
    lines.append(
        f"Chunks: {len(chunks)} · Tokens: {snap.token_count}"
        + (f" · Citation Survival Probability: {csp:.1f}%" if csp is not None else "")
    )
    return "\n".join(lines).rstrip() + "\n"


def build_chunks_json(
    snap: PageSnapshot,
    chunks: Sequence[Chunk],
    min_tokens: int,
    max_tokens: int,
    overlap: int,
) -> str:
    """Render rag_ready_chunks.json — ingestion-ready passage export."""

    payload = {
        "source": snap.final_url or snap.url,
        "title": snap.title,
        "generated_by": f"sage-audit v{__version__}",
        "chunking": {
            "strategy": "sentence-aware semantic boundaries",
            "min_tokens": min_tokens,
            "max_tokens": max_tokens,
            "overlap_tokens": overlap,
        },
        "chunk_count": len(chunks),
        "chunks": [chunk.to_dict() for chunk in chunks],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# The auditor
# ---------------------------------------------------------------------------

@dataclass
class GeoConfig:
    min_tokens: int = 60
    max_tokens: int = 120
    overlap: int = 25
    top_k: int = 3
    backend: str = "auto"
    max_queries: int = 8


class GeoAuditor:
    """Executes all Pillar-3 (GEO) checks against a :class:`PageSnapshot`."""

    pillar_name = "Pillar 3 — Generative Engine Optimization (GEO)"

    def __init__(self, config: Optional[GeoConfig] = None, **overrides: Any) -> None:
        self.config = config or GeoConfig()
        for key, value in overrides.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

    def audit(self, snap: PageSnapshot) -> PillarReport:
        started = time.perf_counter()
        cfg = self.config

        chunks = chunk_sections(
            snap.sections,
            min_tokens=cfg.min_tokens,
            max_tokens=cfg.max_tokens,
            overlap=cfg.overlap,
            fallback_text=snap.text,
        )
        embedder = resolve_backend(cfg.backend)
        queries = build_queries(snap, max_queries=cfg.max_queries)
        simulation = simulate_rag(queries, chunks, embedder, top_k=cfg.top_k)

        compliant = [
            chunk for chunk in chunks
            if cfg.min_tokens <= chunk.token_count <= cfg.max_tokens
        ]
        compliance = (len(compliant) / len(chunks)) if chunks else 0.0

        artifacts = {
            "llms.txt": build_llms_txt(snap, chunks, simulation),
            "rag_ready_chunks.json": build_chunks_json(
                snap, chunks, cfg.min_tokens, cfg.max_tokens, cfg.overlap
            ),
        }

        findings = [
            self._check_content_volume(snap),
            self._check_chunkability(chunks),
            self._check_chunk_shape(chunks, compliance, cfg),
            self._check_citation_survival(simulation),
            self._check_retrieval_focus(simulation),
            self._check_retrieval_coverage(simulation, chunks),
            self._backend_note(simulation, cfg),
            Finding(
                check_id="geo.artifacts",
                title="RAG artifacts generated",
                status=Status.PASS,
                score=1.0,
                weight=0.0,
                details="llms.txt and rag_ready_chunks.json synthesized and attached "
                "to the report (use --save-artifacts to write them to disk).",
                recommendation="",
            ),
        ]

        metrics = {
            "total_tokens": snap.token_count,
            "chunk_count": len(chunks),
            "chunk_token_counts": [c.token_count for c in chunks],
            "chunk_size_compliance": round(compliance, 3),
            "citation_survival_probability": simulation.get("csp"),
            "avg_semantic_entropy": simulation.get("avg_entropy"),
            "retrieval_coverage": simulation.get("retrieval_coverage"),
            "embedding_backend": simulation.get("backend"),
            "queries": queries,
            "retrieval": simulation.get("per_query"),
            "chunk_config": {
                "min_tokens": cfg.min_tokens,
                "max_tokens": cfg.max_tokens,
                "overlap": cfg.overlap,
                "top_k": cfg.top_k,
            },
        }
        return finalize_pillar(
            "geo", self.pillar_name, findings,
            metrics=metrics, artifacts=artifacts, started=started,
        )

    # ------------------------------------------------------------------ #

    def _check_content_volume(self, snap: PageSnapshot) -> Finding:
        tokens = snap.token_count
        score = min(1.0, tokens / 600.0)
        if tokens >= 600:
            status, rec = Status.PASS, ""
        elif tokens >= 240:
            status, rec = Status.WARN, (
                "Roughly 600+ tokens of clean body text gives RAG pipelines enough "
                "material to form multiple coherent passages."
            )
        else:
            status, rec = Status.FAIL, (
                "Below ~240 tokens there is effectively nothing to chunk or retrieve — "
                "expand the factual body copy."
            )
        return Finding(
            check_id="geo.content_volume",
            title="Retrievable content volume",
            status=status,
            score=score,
            weight=6.0,
            details=f"{tokens} approximate tokens of clean text.",
            recommendation=rec,
        )

    def _check_chunkability(self, chunks: Sequence[Chunk]) -> Finding:
        count = len(chunks)
        if count >= 3:
            score, status, rec = 1.0, Status.PASS, ""
        elif count >= 1:
            score, status, rec = 0.5, Status.WARN, (
                "Only 1–2 passages can be built; one thin chunk gives a retriever "
                "a single, dilute target. Add headed sections with substance."
            )
        else:
            score, status, rec = 0.0, Status.FAIL, (
                "No retrievable passages could be built from the page text."
            )
        return Finding(
            check_id="geo.chunkability",
            title="Semantic chunkability",
            status=status,
            score=score,
            weight=8.0,
            details=f"{count} passage(s) formed (target: ≥3 coherent chunks).",
            recommendation=rec,
        )

    def _check_chunk_shape(
        self, chunks: Sequence[Chunk], compliance: float, cfg: GeoConfig
    ) -> Finding:
        sizes = ", ".join(str(c.token_count) for c in chunks) or "—"
        status = (
            Status.PASS if compliance >= 0.85
            else Status.WARN if compliance >= 0.5 and chunks
            else Status.FAIL
        )
        return Finding(
            check_id="geo.chunk_shape",
            title="Chunk size compliance",
            status=status,
            score=compliance,
            weight=6.0,
            details=f"{compliance:.0%} of chunks sit inside the "
            f"{cfg.min_tokens}–{cfg.max_tokens} token window (sizes: {sizes}).",
            recommendation="" if status is Status.PASS else
            "Very short sections fragment embeddings; very long ones dilute them. "
            "Group related sentences into 60–120 token passages.",
        )

    def _check_citation_survival(self, simulation: dict[str, Any]) -> Finding:
        csp = simulation.get("csp")
        if csp is None:
            return Finding(
                check_id="geo.citation_survival",
                title="Citation Survival Probability",
                status=Status.FAIL,
                score=0.0,
                weight=16.0,
                details="RAG simulation could not run (no queries/chunks).",
                recommendation="Provide extractable body text and a descriptive title/H1 "
                "so retrieval can be simulated.",
            )
        if csp >= 70:
            status, rec = Status.PASS, ""
        elif csp >= 45:
            status, rec = Status.WARN, (
                "Citations survive retrieval only sometimes. Sharpen the entity focus of "
                "each heading's first passage so one chunk clearly wins each query."
            )
        else:
            status, rec = Status.FAIL, (
                "Retrieval attention is diffuse — queries match many chunks almost "
                "equally, so the odds any single passage gets cited are low. Consolidate "
                "per-topic sections and front-load definitional sentences."
            )
        return Finding(
            check_id="geo.citation_survival",
            title="Citation Survival Probability",
            status=status,
            score=csp / 100.0,
            weight=16.0,
            details=f"CSP {csp:.1f}% across {len(simulation.get('per_query', []))} "
            "simulated RAG queries (prominence + low-entropy ranking).",
            recommendation=rec,
        )

    def _check_retrieval_focus(self, simulation: dict[str, Any]) -> Finding:
        entropy = simulation.get("avg_entropy")
        if entropy is None:
            return Finding(
                check_id="geo.retrieval_focus",
                title="Semantic retrieval focus",
                status=Status.INFO if not simulation.get("per_query") else Status.WARN,
                score=0.0,
                weight=0.0 if not simulation.get("per_query") else 6.0,
                details="Not computable without retrieval results.",
                recommendation="",
            )
        focus = 1.0 - entropy
        status = Status.PASS if entropy <= 0.45 else (Status.WARN if entropy <= 0.7 else Status.FAIL)
        return Finding(
            check_id="geo.retrieval_focus",
            title="Semantic retrieval focus",
            status=status,
            score=focus,
            weight=6.0,
            details=f"Average normalized similarity entropy {entropy:.2f} "
            f"(0 = laser-focused, 1 = uniform ambiguity).",
            recommendation="" if status is Status.PASS else
            "High entropy means the page's passages all look alike to the retriever — "
            "differentiate sections around distinct sub-questions.",
        )

    def _check_retrieval_coverage(
        self, simulation: dict[str, Any], chunks: Sequence[Chunk]
    ) -> Finding:
        coverage = simulation.get("retrieval_coverage")
        if coverage is None:
            return Finding(
                check_id="geo.retrieval_coverage",
                title="Retrieval coverage",
                status=Status.FAIL,
                score=0.0,
                weight=6.0,
                details="No chunks were ever retrieved.",
                recommendation="Add substantive, query-aligned passages.",
            )
        status = (
            Status.PASS if coverage >= 0.75
            else Status.WARN if coverage >= 0.4 else Status.FAIL
        )
        invisible = round(len(chunks) * (1.0 - coverage))
        return Finding(
            check_id="geo.retrieval_coverage",
            title="Retrieval coverage",
            status=status,
            score=coverage,
            weight=6.0,
            details=f"{coverage:.0%} of chunks appear in at least one top-k result "
            f"({invisible} chunk(s) invisible).",
            recommendation="" if status is Status.PASS else
            "Some passages are never retrieved — either merge them into stronger "
            "sections or align them with real user questions.",
        )

    def _backend_note(self, simulation: dict[str, Any], cfg: GeoConfig) -> Finding:
        backend = str(simulation.get("backend") or "hashing fallback")
        neural = "fastembed" in backend or "sentence-transformers" in backend
        return Finding(
            check_id="geo.embedding_backend",
            title="Embedding backend",
            status=Status.PASS if neural else Status.INFO,
            score=1.0,
            weight=0.0,
            details=f"Vector space: {backend}.",
            recommendation="" if neural else
            "Install `sage-audit[embeddings]` (fastembed) for neural embeddings; the "
            "deterministic fallback is stable but lexical.",
        )
