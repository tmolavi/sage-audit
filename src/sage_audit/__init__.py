"""sage-audit — SAGE: Search, Answer, & Generative Engine Auditor.

The Unified 3-Pillar Audit Engine for SEO, Entity AEO, and Generative
Engine Optimization (GEO).

Author & Architect: Taqi Molavi (Taghi Molavi)
Website:            https://molavi.pro
Research Hub:       https://molavi.pro/research
GitHub:             https://github.com/tmolavi
License:            MIT (c) 2026 Taqi Molavi

Quick usage as a library::

    from sage_audit import SageAuditor

    auditor = SageAuditor()
    report = auditor.audit("https://example.com")
    print(report.overall_score, report.grade)
"""

from sage_audit._version import __version__
from sage_audit.core import SageAuditor, audit_url
from sage_audit.models import (
    AuditReport,
    Finding,
    PillarReport,
    Status,
    grade_for,
)

__author__ = "Taqi Molavi (Taghi Molavi)"
__author_email__ = "taqi@molavi.pro"
__url__ = "https://molavi.pro"
__license__ = "MIT"

__all__ = [
    "SageAuditor",
    "audit_url",
    "AuditReport",
    "PillarReport",
    "Finding",
    "Status",
    "grade_for",
    "__version__",
    "__author__",
    "__url__",
]
