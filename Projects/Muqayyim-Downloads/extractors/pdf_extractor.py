"""
PDF Extractor — extracts structured fields from uploaded PDFs.

Pipeline:
1. Open PDF with pdfplumber
2. Extract text blocks with page/line references
3. Try table extraction
4. Apply regex patterns for prices, areas, dates
5. Detect property type from keywords
6. Normalize and build citations with page references
"""

from uuid import UUID

from extractors.base import BaseExtractor, ExtractionResult
from extractors.citation import build_citation
from extractors.confidence import score_confidence
from extractors.field_mapping import PRICE_PATTERNS, AREA_PATTERNS, DATE_PATTERNS, detect_property_type
from extractors.normalizer import extract_number, normalize_date


class PDFExtractor(BaseExtractor):
    name = "pdf_extractor"
    version = "1.0.0"

    def can_handle(self, source_type: str) -> bool:
        return source_type == "pdf"

    async def extract(self, source_id: UUID, content: bytes | str, **kwargs) -> ExtractionResult:
        file_path = kwargs.get("file_path", "")
        file_name = kwargs.get("file_name", "unknown.pdf")

        try:
            import pdfplumber
        except ImportError:
            return ExtractionResult(
                source_id=source_id, fields=[], extractor_name=self.name,
                extractor_version=self.version, error="pdfplumber not installed",
            )

        fields = []
        full_text = ""

        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text() or ""
                    full_text += f"\n{page_text}"

                    # Try table extraction
                    tables = page.extract_tables()
                    for table in tables:
                        table_fields = self._extract_from_table(
                            table, page_num, source_id, file_name
                        )
                        fields.extend(table_fields)

                    # Regex extraction per page
                    page_fields = self._extract_regex(
                        page_text, page_num, source_id, file_name
                    )
                    fields.extend(page_fields)

        except Exception as e:
            return ExtractionResult(
                source_id=source_id, fields=[], extractor_name=self.name,
                extractor_version=self.version, error=f"PDF parse error: {e}",
            )

        # Detect property type from full text
        ptype = detect_property_type(full_text[:5000])
        if ptype:
            fields.append(self._make_field(
                "property_type", ptype, ptype,
                source_id, file_name, "keyword_detection:all_pages", ptype, 0.65,
            ))

        # Store raw text for LLM fallback
        if full_text.strip():
            fields.append({
                "field_name": "raw_page_text",
                "raw_value": full_text[:5000],
                "normalized_value": None,
                "display_value": None,
                "confidence": 1.0,
                "classification": "fact",
                "value_type": "string",
                "citation": build_citation(
                    source_id=source_id, source_type="pdf",
                    source_url_or_name=file_name,
                    locator="pages:1-all",
                    snippet=full_text[:200],
                    extractor_name=self.name,
                    extractor_version=self.version,
                    parse_confidence=1.0,
                ),
            })

        # Deduplicate
        seen = {}
        for f in fields:
            name = f["field_name"]
            if name not in seen or f["confidence"] > seen[name]["confidence"]:
                seen[name] = f
        fields = list(seen.values())

        return ExtractionResult(
            source_id=source_id,
            fields=fields,
            extractor_name=self.name,
            extractor_version=self.version,
            raw_content=full_text,
        )

    def _extract_from_table(self, table: list, page_num: int, source_id: UUID, file_name: str) -> list[dict]:
        """Extract fields from a parsed table."""
        fields = []
        if not table:
            return fields

        for row in table:
            if not row or len(row) < 2:
                continue

            label = str(row[0] or "").strip().lower()
            value = str(row[1] or "").strip()
            if not label or not value:
                continue

            locator = f"page:{page_num}:table"

            # Match known labels
            if any(k in label for k in ["سعر", "price", "قيمة", "value"]):
                num = extract_number(value)
                if num and num > 1000:
                    fields.append(self._make_field(
                        "asking_price", value, str(num),
                        source_id, file_name, locator, f"{row[0]}: {value}", 0.8,
                    ))

            elif any(k in label for k in ["مساحة", "area", "المساحة"]):
                num = extract_number(value)
                if num and num > 0:
                    fields.append(self._make_field(
                        "primary_area_sqm", value, str(num),
                        source_id, file_name, locator, f"{row[0]}: {value}", 0.8,
                    ))

            elif any(k in label for k in ["مدينة", "city", "المدينة"]):
                fields.append(self._make_field(
                    "city", value, value,
                    source_id, file_name, locator, f"{row[0]}: {value}", 0.85,
                ))

            elif any(k in label for k in ["حي", "district", "الحي"]):
                fields.append(self._make_field(
                    "district", value, value,
                    source_id, file_name, locator, f"{row[0]}: {value}", 0.85,
                ))

        return fields

    def _extract_regex(self, text: str, page_num: int, source_id: UUID, file_name: str) -> list[dict]:
        """Extract using regex patterns on page text."""
        fields = []

        for pattern in PRICE_PATTERNS:
            match = pattern.search(text)
            if match:
                num = extract_number(match.group(1))
                if num and num > 10000:
                    fields.append(self._make_field(
                        "asking_price", match.group(0), str(num),
                        source_id, file_name, f"page:{page_num}:regex",
                        match.group(0)[:200], 0.7,
                    ))
                    break

        for pattern in AREA_PATTERNS:
            match = pattern.search(text)
            if match:
                num = extract_number(match.group(1))
                if num and num > 0:
                    fields.append(self._make_field(
                        "primary_area_sqm", match.group(0), str(num),
                        source_id, file_name, f"page:{page_num}:regex",
                        match.group(0)[:200], 0.7,
                    ))
                    break

        for pattern in DATE_PATTERNS:
            match = pattern.search(text)
            if match:
                normalized = normalize_date(match.group(0))
                if normalized:
                    fields.append(self._make_field(
                        "listing_date", match.group(0), normalized,
                        source_id, file_name, f"page:{page_num}:regex",
                        match.group(0), 0.6,
                    ))
                    break

        return fields

    def _make_field(
        self, field_name: str, raw: str, normalized: str,
        source_id: UUID, file_name: str, locator: str, snippet: str,
        parse_conf: float,
    ) -> dict:
        return {
            "field_name": field_name,
            "raw_value": raw,
            "normalized_value": normalized,
            "display_value": normalized,
            "confidence": score_confidence(parse_conf, source_reliability=3),
            "classification": "fact",
            "value_type": "string",
            "citation": build_citation(
                source_id=source_id,
                source_type="pdf",
                source_url_or_name=file_name,
                locator=locator,
                snippet=snippet[:500],
                extractor_name=self.name,
                extractor_version=self.version,
                parse_confidence=parse_conf,
            ),
        }
