"""Shared pydantic schemas for sage-audit reports.

Every auditor emits a list of :class:`Finding` objects. Findings are
aggregated into a :class:`PillarReport` (SEO / AEO / GEO), and the three
pillars are composed into a single :class:`AuditReport` by the orchestrator
(:class:`sage_audit.core.SageAuditor`).

(c) 2026 Taqi Molavi — https://molavi.pro — MIT License
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Iterable, Optional

from pydantic import BaseModel, Field


class Status(str, Enum):
    """The outcome of a single audit check."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    INFO = "info"


#: Ordered (min_score, letter) grade thresholds, highest first.
GRADE_THRESHOLDS: tuple[tuple[float, str], ...] = (
    (93.0, "A+"),
    (85.0, "A"),
    (75.0, "B"),
    (65.0, "C"),
    (50.0, "D"),
    (0.0, "F"),
)


def grade_for(score: float) -> str:
    """Map a 0-100 score to a letter grade."""

    for threshold, letter in GRADE_THRESHOLDS:
        if score >= threshold:
            return letter
    return "F"


def status_from_score(score: float, pass_at: float = 0.85, warn_at: float = 0.5) -> Status:
    """Derive a pass/warn/fail status from a 0-1 sub-score."""

    if score >= pass_at:
        return Status.PASS
    if score >= warn_at:
        return Status.WARN
    return Status.FAIL


class Finding(BaseModel):
    """One atomic check result inside a pillar.

    ``score`` is in [0, 1]; ``weight`` expresses the relative importance of
    the check inside its pillar. Findings with ``weight == 0`` are excluded
    from the weighted pillar score (they are purely informational).
    """

    check_id: str = Field(description="Stable, namespaced check identifier, e.g. 'seo.title'.")
    title: str = Field(description="Human readable check name.")
    status: Status
    score: float = Field(ge=0.0, le=1.0)
    weight: float = Field(ge=0.0, default=1.0)
    details: str = Field(default="", description="Measured facts / evidence.")
    recommendation: str = Field(default="", description="Actionable fix guidance.")

    model_config = {"use_enum_values": True}


class PillarReport(BaseModel):
    """Aggregated result for one audit pillar (SEO, AEO or GEO)."""

    pillar: str
    name: str
    score: float = Field(ge=0.0, le=100.0, default=0.0)
    grade: str = "F"
    findings: list[Finding] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    artifacts: dict[str, str] = Field(
        default_factory=dict,
        description="Generated artifacts, e.g. {'llms.txt': ..., 'rag_ready_chunks.json': ...}.",
    )
    duration_ms: float = 0.0

    def actionable(self) -> list[Finding]:
        """Findings that need attention, most impactful first."""

        items = [f for f in self.findings if f.recommendation and str(f.status) in ("warn", "fail")]
        return sorted(items, key=lambda f: f.weight * (1.0 - f.score), reverse=True)


class AuditReport(BaseModel):
    """Full 3-pillar audit result."""

    url: str
    final_url: str = ""
    audited_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: float = 0.0
    overall_score: float = Field(ge=0.0, le=100.0, default=0.0)
    grade: str = "F"
    seo: PillarReport
    aeo: PillarReport
    geo: PillarReport
    artifacts: dict[str, str] = Field(default_factory=dict)
    page: dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable dictionary (datetimes as ISO-8601 strings)."""

        return self.model_dump(mode="json")


def compute_score(findings: Iterable[Finding]) -> float:
    """Weighted mean (0-100) of finding scores; weight-0 findings are excluded."""

    total_weight = 0.0
    total = 0.0
    for finding in findings:
        if finding.weight <= 0:
            continue
        total_weight += finding.weight
        total += finding.score * finding.weight
    if total_weight <= 0:
        return 0.0
    return round(100.0 * total / total_weight, 1)


def finalize_pillar(
    pillar: str,
    name: str,
    findings: list[Finding],
    metrics: Optional[dict[str, Any]] = None,
    artifacts: Optional[dict[str, str]] = None,
    started: Optional[float] = None,
) -> PillarReport:
    """Assemble a :class:`PillarReport` from a list of findings."""

    score = compute_score(findings)
    duration_ms = (time.perf_counter() - started) * 1000.0 if started else 0.0
    return PillarReport(
        pillar=pillar,
        name=name,
        score=score,
        grade=grade_for(score),
        findings=findings,
        metrics=metrics or {},
        artifacts=artifacts or {},
        duration_ms=round(duration_ms, 2),
    )
