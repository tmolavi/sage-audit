"""SAGE orchestrator — runs the SEO, AEO and GEO pipelines and fuses them
into a single weighted verdict.

Evidence Taxonomy & Methodology Hardening:
- All checks classified under E0–E5 epistemic certainty tiers.
- CSP formulated as Citation Survival Proxy (heuristic proxy, not calibrated probability).
- Configurable heuristic thresholds across all 3 pillars.

Weights (tunable via config):
    SEO 0.30 · AEO 0.35 · GEO 0.35

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
from sage_audit.config import SageConfig
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


class SageAuditor:
    """One-stop facade for full 3-pillar audits.

    Parameters
    ----------
    config:             optional SageConfig instance with custom heuristic thresholds
    timeout:            per-request network timeout (seconds)
    fetch_robots:       also fetch and analyze /robots.txt on live audits
    embedding_backend:  'auto' | 'fastembed' | 'sentence-transformers' | 'hashing'
    top_k:              simulated RAG top-k retrieval depth
    chunk_min_tokens / chunk_max_tokens / chunk_overlap: GEO chunker envelope
    session:            optional pre-configured requests.Session
    """

    def __init__(
        self,
        config: Optional[SageConfig] = None,
        *,
        timeout: Optional[float] = None,
        fetch_robots: Optional[bool] = None,
        embedding_backend: Optional[str] = None,
        top_k: Optional[int] = None,
        chunk_min_tokens: Optional[int] = None,
        chunk_max_tokens: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        session: Optional[requests.Session] = None,
        **kwargs,
    ) -> None:
        base_config = config or SageConfig()
        overrides = {
            "timeout": timeout,
            "fetch_robots": fetch_robots,
            "embedding_backend": embedding_backend,
            "top_k": top_k,
            "chunk_min_tokens": chunk_min_tokens,
            "chunk_max_tokens": chunk_max_tokens,
            "chunk_overlap": chunk_overlap,
            **kwargs,
        }
        self.config = base_config.update_from_dict(overrides)
        self.geo_config = GeoConfig(
            min_tokens=self.config.chunk_min_tokens,
            max_tokens=self.config.chunk_max_tokens,
            overlap=self.config.chunk_overlap,
            top_k=self.config.top_k,
            backend=self.config.embedding_backend,
            max_queries=self.config.max_sim_queries,
            csp_prominence_weight=self.config.csp_prominence_weight,
            csp_entropy_weight=self.config.csp_entropy_weight,
            csp_pass_threshold=self.config.csp_pass_threshold,
            csp_warn_threshold=self.config.csp_warn_threshold,
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
            url, timeout=self.config.timeout, session=self.session
        )
        robots_txt = (
            fetch_robots_txt(final_url or url, timeout=self.config.timeout, session=self.session)
            if self.config.fetch_robots
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
        seo = SeoAuditor(config=self.config).audit(snapshot)
        aeo = AeoAuditor(config=self.config).audit(snapshot)
        geo = GeoAuditor(config=self.geo_config).audit(snapshot)

        cfg = self.config
        overall = round(
            seo.score * cfg.weight_seo
            + aeo.score * cfg.weight_aeo
            + geo.score * cfg.weight_geo,
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
            methodology_version="2.0.0",
            validation_status="unvalidated",
            seo=seo,
            aeo=aeo,
            geo=geo,
            artifacts=artifacts,
            page=page,
        )


def audit_url(url: str, **kwargs) -> AuditReport:
    """Module-level convenience: ``audit_url("https://example.com")``."""

    return SageAuditor(**kwargs).audit(url)
