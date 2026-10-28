"""Citation Object — every populated extracted field must carry one."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CitationLocator(BaseModel):
    """Points to where in the source the data was found."""
    css_selector: Optional[str] = None
    xpath: Optional[str] = None
    text_block: Optional[str] = None
    page_number: Optional[int] = None
    line_range_start: Optional[int] = None
    line_range_end: Optional[int] = None
    bounding_hint: Optional[str] = None  # e.g. "top-right table, row 3"


class CitationObject(BaseModel):
    """Full provenance for any extracted field value."""
    source_id: str
    source_type: str  # url, pdf, manual
    source_name: Optional[str] = None  # URL or filename
    retrieval_timestamp: datetime
    locator: CitationLocator = Field(default_factory=CitationLocator)
    snippet: Optional[str] = None  # Raw excerpt from source
    extractor_name: str = "unknown"
    extractor_version: str = "0.1.0"
    parse_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    llm_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    crosscheck_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    normalization_notes: Optional[str] = None
