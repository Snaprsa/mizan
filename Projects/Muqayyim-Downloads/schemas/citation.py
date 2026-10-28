"""
CitationObject — Every extracted field must carry one of these.
This is the provenance backbone of the platform.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CitationObject(BaseModel):
    """
    Provenance record for any extracted or derived value.
    
    Every populated field in a Comparable MUST have a citation.
    This makes every value traceable to its raw source.
    """

    source_id: UUID = Field(
        ..., description="FK to the source record (URL or PDF upload)"
    )
    source_type: str = Field(
        ..., description="url | pdf | manual"
    )
    source_url_or_name: str = Field(
        ..., description="Original URL or filename"
    )
    retrieval_timestamp: datetime = Field(
        ..., description="When the source was fetched/uploaded (UTC)"
    )

    # Locator — where exactly in the source this value came from
    locator: Optional[str] = Field(
        None,
        description=(
            "How to find this value in the source. "
            "CSS selector, XPath, page:line range, bounding box hint, "
            "or text block identifier."
        ),
    )
    snippet: Optional[str] = Field(
        None,
        max_length=500,
        description="Raw text excerpt from source containing this value",
    )

    # Extraction metadata
    extractor_name: str = Field(
        ..., description="e.g. html_extractor, pdf_extractor, llm_fallback"
    )
    extractor_version: str = Field(
        ..., description="Semver of the extractor, e.g. 1.0.0"
    )

    # Confidence scores (0.0 – 1.0)
    parse_confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Confidence from deterministic parsing"
    )
    llm_confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="Confidence from LLM extraction (only if LLM was used)"
    )
    crosscheck_confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="Confidence from cross-checking against other fields/sources"
    )

    normalization_notes: Optional[str] = Field(
        None,
        description="Notes about how the value was normalized (unit conversion, transliteration, etc.)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "source_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "source_type": "url",
                "source_url_or_name": "https://sa.aqar.fm/listing/12345",
                "retrieval_timestamp": "2025-03-15T10:30:00Z",
                "locator": "div.listing-price > span.amount",
                "snippet": "1,250,000 ريال",
                "extractor_name": "html_extractor",
                "extractor_version": "1.0.0",
                "parse_confidence": 0.95,
                "llm_confidence": None,
                "crosscheck_confidence": 0.90,
                "normalization_notes": "Converted from Arabic numerals, confirmed SAR"
            }
        }
