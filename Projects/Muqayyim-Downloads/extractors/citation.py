"""
Citation builder — constructs CitationObject dicts for extracted fields.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID


def build_citation(
    source_id: UUID,
    source_type: str,
    source_url_or_name: str,
    locator: Optional[str] = None,
    snippet: Optional[str] = None,
    extractor_name: str = "unknown",
    extractor_version: str = "1.0.0",
    parse_confidence: float = 0.5,
    llm_confidence: Optional[float] = None,
    crosscheck_confidence: Optional[float] = None,
    normalization_notes: Optional[str] = None,
) -> dict:
    """
    Build a citation dict matching the CitationObject schema.
    Returns a plain dict suitable for JSON storage.
    """
    return {
        "source_id": str(source_id),
        "source_type": source_type,
        "source_url_or_name": source_url_or_name,
        "retrieval_timestamp": datetime.utcnow().isoformat() + "Z",
        "locator": locator,
        "snippet": (snippet or "")[:500] if snippet else None,
        "extractor_name": extractor_name,
        "extractor_version": extractor_version,
        "parse_confidence": parse_confidence,
        "llm_confidence": llm_confidence,
        "crosscheck_confidence": crosscheck_confidence,
        "normalization_notes": normalization_notes,
    }
