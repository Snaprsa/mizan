"""
BaseExtractor — Interface for all extraction pipelines.

Extraction order of operations:
1. Ingest source (URL or PDF)
2. Fetch + store raw content
3. Parse into text/DOM blocks
4. Deterministic extraction (regex, selectors, structured data)
5. Normalize (SAR, sqm, dates, locations)
6. LLM fallback ONLY for unresolved/ambiguous fields
7. Score confidence
8. Attach citations
9. Return versioned results
"""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

class ExtractionResult:
    """Result of running an extractor on a source."""

    def __init__(
        self,
        source_id: UUID,
        fields: list,  # list of field dicts
        extractor_name: str,
        extractor_version: str,
        raw_content: Optional[str] = None,
        error: Optional[str] = None,
    ):
        self.source_id = source_id
        self.fields = fields
        self.extractor_name = extractor_name
        self.extractor_version = extractor_version
        self.raw_content = raw_content
        self.error = error

    @property
    def success(self) -> bool:
        return self.error is None and len(self.fields) > 0


class BaseExtractor(ABC):
    """
    All extractors implement this interface.

    Subclasses:
    - HTMLExtractor: URL → fetch HTML → parse → extract fields
    - PDFExtractor: PDF file → parse text/tables → extract fields
    - LLMFallbackExtractor: Unresolved text → Claude → extract fields
    """

    name: str = "base"
    version: str = "0.0.0"

    @abstractmethod
    async def extract(self, source_id: UUID, content: bytes | str, **kwargs) -> ExtractionResult:
        """
        Extract structured fields from raw content.

        Args:
            source_id: UUID of the source record in DB
            content: Raw HTML string or PDF bytes
            **kwargs: Additional context (url, filename, etc.)

        Returns:
            ExtractionResult with list of ExtractedFields, each with CitationObject
        """
        ...

    @abstractmethod
    def can_handle(self, source_type: str) -> bool:
        """Whether this extractor can handle the given source type."""
        ...
