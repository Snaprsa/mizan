"""PDF extraction pipeline — extracts structured property data from PDF files."""
import re
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional, Any
from schemas.citation import CitationObject, CitationLocator

EXTRACTOR_NAME = "pdf_extractor"
EXTRACTOR_VERSION = "0.1.0"


def extract_from_pdf(
    file_path: str,
    source_id: str,
    filename: str = "unknown.pdf",
    retrieval_timestamp: datetime = None,
) -> Dict[str, Any]:
    """Extract structured fields from a PDF file.
    
    Uses pdfplumber for text extraction, then applies the same deterministic
    rules as the HTML extractor.
    """
    if retrieval_timestamp is None:
        retrieval_timestamp = datetime.now(timezone.utc)

    fields = {}

    try:
        import pdfplumber
    except ImportError:
        return {
            "_error": {
                "raw_value": "pdfplumber not installed",
                "normalized_value": "extraction_failed",
                "confidence": 0.0,
                "citation": None,
            }
        }

    def make_citation(snippet: str, confidence: float, page_num: int = None, locator_hint: str = "") -> dict:
        return CitationObject(
            source_id=source_id,
            source_type="pdf",
            source_name=filename,
            retrieval_timestamp=retrieval_timestamp,
            locator=CitationLocator(
                page_number=page_num,
                text_block=snippet[:500],
                bounding_hint=locator_hint,
            ),
            snippet=snippet[:500],
            extractor_name=EXTRACTOR_NAME,
            extractor_version=EXTRACTOR_VERSION,
            parse_confidence=confidence,
        ).model_dump(mode="json")

    full_text = ""
    page_texts = []

    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                page_texts.append(page_text)
                full_text += page_text + "\n"

                # Also try to extract tables
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if row:
                            row_text = " | ".join(str(cell or "") for cell in row)
                            full_text += row_text + "\n"
    except Exception as e:
        return {
            "_error": {
                "raw_value": str(e),
                "normalized_value": "extraction_failed",
                "confidence": 0.0,
                "citation": None,
            }
        }

    if not full_text.strip():
        return {
            "_error": {
                "raw_value": "No text extracted from PDF",
                "normalized_value": "empty_pdf",
                "confidence": 0.0,
                "citation": None,
            }
        }

    text = full_text

    # ── Price extraction ──
    price_patterns = [
        (r'(?:السعر|price|سعر|asking|SAR|ريال)\s*[:\-]?\s*([\d,\.]+)', 0.7),
        (r'([\d,]{4,})\s*(?:ريال|SAR|sar)', 0.5),
        (r'(?:total|إجمالي|المبلغ)\s*[:\-]?\s*([\d,\.]+)', 0.5),
    ]
    for pattern, conf in price_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw_price = match.group(1).replace(",", "")
            try:
                price_val = float(raw_price)
                if price_val > 1000:
                    page_num = _find_page(match.group(0), page_texts)
                    fields["asking_price"] = {
                        "raw_value": match.group(0).strip(),
                        "normalized_value": str(price_val),
                        "confidence": conf,
                        "citation": make_citation(match.group(0).strip(), conf, page_num, "price section"),
                    }
                    break
            except ValueError:
                pass

    # ── Area extraction ──
    area_patterns = [
        (r'(?:المساحة|area|مساحة|الأرض|land)\s*[:\-]?\s*([\d,\.]+)\s*(?:م²|متر|sqm|م|m²)', 0.7),
        (r'([\d,\.]+)\s*(?:sqm|م²|متر مربع)', 0.6),
    ]
    for pattern, conf in area_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw_area = match.group(1).replace(",", "")
            try:
                area_val = float(raw_area)
                page_num = _find_page(match.group(0), page_texts)
                fields["land_area"] = {
                    "raw_value": match.group(0).strip(),
                    "normalized_value": str(area_val),
                    "confidence": conf,
                    "citation": make_citation(match.group(0).strip(), conf, page_num, "area section"),
                }
                break
            except ValueError:
                pass

    # ── City ──
    saudi_cities = [
        "Riyadh", "الرياض", "Jeddah", "جدة", "Makkah", "مكة",
        "Dammam", "الدمام", "Khobar", "الخبر", "Tabuk", "تبوك",
        "Abha", "أبها", "Taif", "الطائف", "Madinah", "المدينة",
    ]
    for city in saudi_cities:
        if city.lower() in text.lower() or city in text:
            page_num = _find_page(city, page_texts)
            fields["city"] = {
                "raw_value": city,
                "normalized_value": city,
                "confidence": 0.8,
                "citation": make_citation(f"City: {city}", 0.8, page_num, "location"),
            }
            break

    # ── District ──
    district_match = re.search(
        r'(?:الحي|district|حي)\s*[:\-]?\s*([^\d\n,]{2,40})',
        text, re.IGNORECASE
    )
    if district_match:
        page_num = _find_page(district_match.group(0), page_texts)
        fields["district"] = {
            "raw_value": district_match.group(1).strip(),
            "normalized_value": district_match.group(1).strip(),
            "confidence": 0.6,
            "citation": make_citation(district_match.group(0).strip(), 0.6, page_num, "location"),
        }

    # ── Property type ──
    type_patterns = {
        "villa": r'(?:فيلا|villa)',
        "apartment": r'(?:شقة|apartment)',
        "land": r'(?:أرض|ارض|land|قطعة)',
        "office": r'(?:مكتب|office)',
        "retail": r'(?:محل|retail|shop)',
    }
    for prop_type, pattern in type_patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            fields["property_subtype"] = {
                "raw_value": prop_type,
                "normalized_value": prop_type,
                "confidence": 0.6,
                "citation": make_citation(f"Type: {prop_type}", 0.6, None, "document text"),
            }
            cat_map = {
                "villa": "residential", "apartment": "residential",
                "land": "land", "office": "commercial", "retail": "commercial",
            }
            fields["property_category"] = {
                "raw_value": cat_map.get(prop_type, "other"),
                "normalized_value": cat_map.get(prop_type, "other"),
                "confidence": 0.6,
                "citation": make_citation(f"Category derived", 0.6, None, "derived"),
            }
            break

    # ── Title (first line or prominent text) ──
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if lines:
        title = lines[0][:200]
        fields["property_title"] = {
            "raw_value": title,
            "normalized_value": title,
            "confidence": 0.5,
            "citation": make_citation(title, 0.5, 1, "first line of document"),
        }

    # ── Source type ──
    fields["source_type"] = {
        "raw_value": "pdf",
        "normalized_value": "pdf",
        "confidence": 1.0,
        "citation": make_citation(f"File: {filename}", 1.0, None, "source file"),
    }

    # Default currency and reliability
    fields["currency"] = {
        "raw_value": "SAR",
        "normalized_value": "SAR",
        "confidence": 0.9,
        "citation": make_citation("Default: SAR", 0.9, None, "default"),
    }
    fields["reliability_score"] = {
        "raw_value": "3",
        "normalized_value": "3",
        "confidence": 1.0,
        "citation": make_citation("Broker PDF", 1.0, None, "source type"),
    }

    return fields


def _find_page(needle: str, page_texts: list) -> Optional[int]:
    """Find which page contains a text snippet."""
    for i, pt in enumerate(page_texts):
        if needle in pt:
            return i + 1
    return None
