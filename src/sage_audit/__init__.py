"""sage-audit — SAGE: Search, Answer, & Generative Engine Auditor.

The Unified 3-Pillar Audit Engine for SEO, Entity AEO, and Generative
Engine Optimization (GEO).

Features:
- Epistemic Evidence Taxonomy (E0–E5) tagging all audit findings.
- Hardened Citation Survival Proxy (CSP) heuristic semantics.
- Configurable heuristic thresholds across all three pillars.
- Empirical validation and calibration evaluation framework.

Author & Architect: Taqi Molavi (Taghi Molavi)
Website:            https://molavi.pro
Research Hub:       https://molavi.pro/research
GitHub:             https://github.com/tmolavi
License:            MIT (c) 2026 Taqi Molavi
"""

from sage_audit._version import __version__
from sage_audit.config import SageConfig
from sage_audit.core import SageAuditor, audit_url
from sage_audit.models import (
    AuditReport,
    CspDetails,
    EvidenceLevel,
    EvidenceMetadata,
    Finding,
    PillarReport,
    Status,
    grade_for,
)
from sage_audit.validation import (
    CalibrationBin,
    ValidationResult,
    evaluate_sage_vs_observed,
)

__author__ = "Taqi Molavi (Taghi Molavi)"
__author_email__ = "taqi@molavi.pro"
__url__ = "https://molavi.pro"
__license__ = "MIT"

__all__ = [
    "SageAuditor",
    "audit_url",
    "SageConfig",
    "AuditReport",
    "PillarReport",
    "Finding",
    "Status",
    "EvidenceLevel",
    "EvidenceMetadata",
    "CspDetails",
    "ValidationResult",
    "CalibrationBin",
    "evaluate_sage_vs_observed",
    "grade_for",
    "__version__",
    "__author__",
    "__url__",
]
