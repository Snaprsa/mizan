"""
Extraction service — runs extraction inline (synchronous fallback for MVP).

For production, wire this to the Celery worker instead.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from api.app.models import Source, ExtractionJob, Comparable, ExtractedField


_AQARSAS_DOMAINS = {"aqarsas.sa", "aqarsas.com", "www.aqarsas.sa"}
_PASEETAH_DOMAINS = {"paseetah.com", "www.paseetah.com"}


def _infer_reliability(source) -> int:
    """
    Infer reliability score from source type and domain.

    5 = Authenticated transaction / official record
    4 = Official filing / AqarSAS (registry data)
    3 = Broker PDF / Paseetah analytics
    2 = Generic marketplace listing (URL)
    1 = Manual / unknown
    """
    if source.source_type == "pdf":
        return 3
    if source.source_type == "url" and source.url:
        from urllib.parse import urlparse
        domain = urlparse(source.url).netloc.lower().lstrip("www.")
        if domain in _AQARSAS_DOMAINS:
            return 4  # AqarSAS = official registry
        if domain in _PASEETAH_DOMAINS:
            return 3  # Paseetah = analytics platform
        return 2  # Generic marketplace listing
    return 1  # Manual / unknown


def _pick_extractor_for_url(url: str):
    """Return the right extractor class for a given URL."""
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.lower().lstrip("www.")
    if domain in _AQARSAS_DOMAINS:
        from extractors.aqarsas_extractor import AqarSASExtractor
        return AqarSASExtractor()
    if domain in _PASEETAH_DOMAINS:
        from extractors.paseetah_extractor import PaseetahExtractor
        return PaseetahExtractor()
    # Default: generic HTML extractor
    from extractors.html_extractor import HTMLExtractor
    return HTMLExtractor()


def _get_norm(field_map: dict, name: str) -> Optional[str]:
    f = field_map.get(name)
    return f.get("normalized_value") if f else None


def _get_float(field_map: dict, name: str) -> Optional[float]:
    f = field_map.get(name)
    if not f or not f.get("normalized_value"):
        return None
    try:
        return float(f["normalized_value"])
    except (ValueError, TypeError):
        return None


async def run_extraction_inline(
    db: AsyncSession,
    job: ExtractionJob,
    source: Source,
) -> dict:
    """
    Run extraction synchronously within the API request.
    Uses the full extractor pipeline (HTML or PDF).

    For async URL fetching, we run the async extractor directly.
    For PDF, same pattern (pdfplumber is sync but lightweight).
    """
    # Mark job as running
    job.status = "running"
    job.started_at = datetime.utcnow()
    await db.flush()

    try:
        fields = []
        raw_content = ""

        if source.source_type == "url":
            extractor = _pick_extractor_for_url(source.url or "")
            result = await extractor.extract(
                source_id=source.id,
                content=source.raw_content or "",
                url=source.url or "",
            )

            # Check for extractor-level error (e.g. blocked page, auth failure)
            if result.error:
                job.status = "failed"
                job.error_log = result.error
                job.completed_at = datetime.utcnow()
                source.status = "failed"
                source.error_message = result.error[:500]
                return {"status": "failed", "error": result.error}

            fields = result.fields if isinstance(result.fields, list) else []
            raw_content = result.raw_content or ""

        elif source.source_type == "pdf":
            from extractors.pdf_extractor import PDFExtractor
            extractor = PDFExtractor()
            result = await extractor.extract(
                source_id=source.id,
                content=b"",
                file_path=source.file_path or "",
                file_name=source.file_name or "document.pdf",
            )
            fields = result.fields if isinstance(result.fields, list) else []
            raw_content = result.raw_content or ""

        else:
            raise ValueError(f"Unknown source type: {source.source_type}")

        # Update source with raw content
        if raw_content:
            source.raw_content = raw_content[:50000]  # Cap at 50KB
        source.status = "fetched"

        # Build field map for denormalized fields
        field_map = {}
        for f in fields:
            if isinstance(f, dict):
                name = f.get("field_name", "")
                if name and (name not in field_map or f.get("confidence", 0) > field_map[name].get("confidence", 0)):
                    field_map[name] = f

        # Create comparable
        comp = Comparable(
            id=uuid.uuid4(),
            case_id=source.case_id,
            source_id=source.id,
            extraction_job_id=job.id,
            status="draft",
            reliability_score=_infer_reliability(source),
            # Prefer *_en variants for Arabic-source fields (AqarSAS returns city_en/city_ar)
            property_title=_get_norm(field_map, "property_title") or _get_norm(field_map, "title"),
            city=_get_norm(field_map, "city_en") or _get_norm(field_map, "city"),
            district=_get_norm(field_map, "district"),
            property_type=_get_norm(field_map, "property_type"),
            evidence_type=_get_norm(field_map, "evidence_type"),
            asking_price=_get_float(field_map, "asking_price"),
            transacted_price=_get_float(field_map, "transacted_price"),
            currency=_get_norm(field_map, "currency") or "SAR",
            primary_area_sqm=_get_float(field_map, "primary_area_sqm") or _get_float(field_map, "area_sqm"),
            listing_date=_get_norm(field_map, "listing_date"),
            transaction_date=_get_norm(field_map, "transaction_date"),
            tenure=_get_norm(field_map, "tenure"),
            latitude=_get_float(field_map, "latitude"),
            longitude=_get_float(field_map, "longitude"),
            notes=_get_norm(field_map, "notes"),
            created_at=datetime.utcnow(),
        )

        # Price per sqm: use extracted value if available, else compute
        extracted_ppsm = _get_float(field_map, "price_per_sqm")
        if extracted_ppsm:
            comp.price_per_sqm = extracted_ppsm
        else:
            price = comp.asking_price or comp.transacted_price
            if price and comp.primary_area_sqm and comp.primary_area_sqm > 0:
                comp.price_per_sqm = round(price / comp.primary_area_sqm, 2)

        db.add(comp)
        await db.flush()

        # Create ExtractedField records (skip raw_page_text — too large, keep for LLM)
        saved_count = 0
        for f in fields:
            if not isinstance(f, dict):
                continue
            field_name = f.get("field_name", "")
            if not field_name:
                continue

            ef = ExtractedField(
                id=uuid.uuid4(),
                extraction_job_id=job.id,
                comparable_id=comp.id,
                field_name=field_name,
                raw_value=str(f.get("raw_value", ""))[:2000] if f.get("raw_value") else None,
                normalized_value=str(f.get("normalized_value", ""))[:2000] if f.get("normalized_value") else None,
                display_value=str(f.get("display_value") or f.get("normalized_value") or f.get("raw_value") or "")[:2000],
                value_type=f.get("value_type", "string"),
                confidence=float(f.get("confidence", 0.0)),
                classification=f.get("classification", "fact"),
                citation=f.get("citation"),
                extraction_version="1.0.0",
                extracted_at=datetime.utcnow(),
            )
            db.add(ef)
            saved_count += 1

        # Mark job complete
        job.status = "completed"
        job.extractor_name = getattr(extractor, "name", "html_extractor") if source.source_type == "url" else "pdf_extractor"
        job.extractor_version = "1.0.0"
        job.completed_at = datetime.utcnow()

        return {
            "status": "completed",
            "comparable_id": str(comp.id),
            "fields_extracted": saved_count,
        }

    except Exception as e:
        job.status = "failed"
        job.error_log = str(e)
        job.completed_at = datetime.utcnow()
        source.status = "failed"
        source.error_message = str(e)[:500]
        return {"status": "failed", "error": str(e)}
