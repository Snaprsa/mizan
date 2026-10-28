"""
ExtractedField — A single extracted value with its citation and confidence.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .citation import CitationObject
from .enums import DataClassification


class ExtractedField(BaseModel):
    """
    One field extracted from a source.
    
    Stores raw + normalized values, confidence, and full citation.
    Every populated field in the comps table is backed by one of these.
    """

    id: UUID = Field(default_factory=uuid4)
    field_name: str = Field(
        ..., description="Canonical field name, e.g. 'asking_price', 'land_area', 'city'"
    )

    # Values
    raw_value: Optional[str] = Field(
        None, description="Value exactly as found in source"
    )
    normalized_value: Optional[Any] = Field(
        None, description="Cleaned/converted value (number, date, enum, etc.)"
    )
    display_value: Optional[str] = Field(
        None, description="Human-readable formatted value for UI"
    )

    # Confidence & classification
    confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Combined confidence score"
    )
    classification: DataClassification = Field(
        default=DataClassification.FACT,
        description="FACT / ASSUMPTION / JUDGMENT"
    )

    # Provenance
    citation: CitationObject = Field(
        ..., description="Full provenance for this value"
    )

    # Versioning
    extraction_version: str = Field(
        ..., description="Version of the extraction run that produced this"
    )
    extracted_at: datetime = Field(
        default_factory=datetime.utcnow
    )

    # Override tracking (populated only if user edited this field)
    is_overridden: bool = Field(default=False)
    override_value: Optional[str] = Field(None)
    override_reason: Optional[str] = Field(None)
    overridden_by: Optional[UUID] = Field(None)
    overridden_at: Optional[datetime] = Field(None)
