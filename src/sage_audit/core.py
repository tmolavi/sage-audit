"""SAGE orchestrator — runs the SEO, AEO and GEO pipelines and fuses them
into a single weighted verdict.

Weights (tunable):
    SEO 0.30 · AEO 0.35 · GEO 0.35
The AI-search pillars carry slightly more weight than classical hygiene,
reflecting where discovery traffic is heading.

(c) 2026 Taqi Molavi — https://molavi.pro — MIT License
"""

from __future__ import annotations

import time
from typing import Optional

import requests

from sage_audit._version import __version__
from sage_audit.auditors.aeo_auditor import AeoAuditor
from sage_audit.auditors.geo_auditor import GeoAuditor, GeoConfig
from sage_audit.auditors.seo_auditor import SeoAuditor
from sage_audit.models import AuditReport, grade_for
from sage_audit.utils.extractor import (
    DEFAULT_TIMEOUT,
    USER_AGENT,
    PageSnapshot,
    ensure_url,
    fetch_robots_txt,
    fetch_url,
    parse_snapshot,
)

#: Pillar weights for the overall SAGE score.
PILLAR_WEIGHTS = {"seo": 0.30, "aeo": 0.35, "geo": 0.35}


class SageAuditor:
    """One-stop facade for full 3-pillar audits.

    Parameters
    ----------
    timeout:            per-request network timeout (seconds)
    fetch_robots:       also fetch and analyze /robots.txt on live audits
    embedding_backend:  'auto' | 'fastembed' | 'sentence-transformers' | 'hashing'
    top_k:              simulated RAG top-k retrieval depth
    chunk_min_tokens / chunk_max_tokens / chunk_overlap: GEO chunker envelope
    session:            optional pre-configured requests.Session
    """

    def __init__(
        self,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        fetch_robots: bool = True,
        embedding_backend: str = "auto",
        top_k: int = 3,
        chunk_min_tokens: int = 60,
        chunk_max_tokens: int = 120,
        chunk_overlap: int = 25,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.timeout = timeout
        self.fetch_robots = fetch_robots
        self.geo_config = GeoConfig(
            min_tokens=chunk_min_tokens,
            max_tokens=chunk_max_tokens,
            overlap=chunk_overlap,
            top_k=top_k,
            backend=embedding_backend,
        )
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    # ------------------------------------------------------------------ #
    # public API
    # ------------------------------------------------------------------ #

    def audit(self, url: str) -> AuditReport:
        """Audit a live URL (fetches the page plus its robots.txt)."""

        started = time.perf_counter()
        url = ensure_url(url)
        status, headers, html, final_url, fetch_ms = fetch_url(
            url, timeout=self.timeout, session=self.session
        )
        robots_txt = (
            fetch_robots_txt(final_url or url, timeout=self.timeout, session=self.session)
            if self.fetch_robots
            else None
        )
        snapshot = parse_snapshot(
            url,
            html,
            status_code=status,
            headers=headers,
            final_url=final_url,
            robots_txt=robots_txt,
            fetch_ms=fetch_ms,
        )
        return self._run(snapshot, started)

    def audit_html(self, html: str, url: str = "https://example.local/") -> AuditReport:
        """Audit raw HTML without any network access (robots.txt skipped)."""

        started = time.perf_counter()
        snapshot = parse_snapshot(ensure_url(url), html, status_code=0)
        return self._run(snapshot, started)

    def generate_llms_txt(self, url: str) -> str:
        """Convenience: audit a URL and return only the generated llms.txt."""

        return self.audit(url).artifacts["llms.txt"]

    # ------------------------------------------------------------------ #
    # internals
    # ------------------------------------------------------------------ #

    def _run(self, snapshot: PageSnapshot, started: float) -> AuditReport:
        seo = SeoAuditor().audit(snapshot)
        aeo = AeoAuditor().audit(snapshot)
        geo = GeoAuditor(config=self.geo_config).audit(snapshot)

        overall = round(
            seo.score * PILLAR_WEIGHTS["seo"]
            + aeo.score * PILLAR_WEIGHTS["aeo"]
            + geo.score * PILLAR_WEIGHTS["geo"],
            1,
        )
        artifacts = {**geo.artifacts}
        page = {
            "title": snapshot.title,
            "meta_description": snapshot.meta_description,
            "language": snapshot.language,
            "status_code": snapshot.status_code,
            "fetch_ms": snapshot.fetch_ms,
            "word_count": snapshot.word_count,
            "token_count": snapshot.token_count,
            "text_to_code_ratio": snapshot.text_to_code_ratio,
            "json_ld_blocks": len(snapshot.json_ld),
            "chunk_count": geo.metrics.get("chunk_count"),
            "audited_with": f"sage-audit v{__version__}",
        }
        return AuditReport(
            url=snapshot.url,
            final_url=snapshot.final_url or snapshot.url,
            duration_ms=round((time.perf_counter() - started) * 1000.0, 2),
            overall_score=overall,
            grade=grade_for(overall),
            seo=seo,
            aeo=aeo,
            geo=geo,
            artifacts=artifacts,
            page=page,
        )


def audit_url(url: str, **kwargs) -> AuditReport:
    """Module-level convenience: ``audit_url("https://example.com")``."""

    return SageAuditor(**kwargs).audit(url)
