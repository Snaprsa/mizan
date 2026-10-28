"""
Shared domain schemas for the Muqayyim platform.
Import from here: `from schemas import CitationObject, Comparable, ...`
"""

from .enums import *  # noqa: F401, F403  — intentional wildcard for all enums
from .citation import CitationObject  # noqa: F401
from .extracted_field import ExtractedField  # noqa: F401
from .comparable import Comparable, AreaMeasurement  # noqa: F401
from ._future import (  # noqa: F401
    SubjectProperty,
    Adjustment,
    ValuationRun,
    ProviderSearchCriteria,
    CandidateComparable,
    ReportTemplate,
    ReportArtifact,
)

__all__ = [
    # Enums (re-exported via *)
    # Core schemas
    "CitationObject",
    "ExtractedField",
    "Comparable",
    "AreaMeasurement",
    # Future schemas (Stage 2-5 stubs)
    "SubjectProperty",
    "Adjustment",
    "ValuationRun",
    "ProviderSearchCriteria",
    "CandidateComparable",
    "ReportTemplate",
    "ReportArtifact",
]
