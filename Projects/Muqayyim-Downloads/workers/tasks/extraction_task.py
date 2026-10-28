"""
Extraction task — orchestrates the full extraction pipeline.

Pipeline:
1. Load source from DB
2. Fetch/read raw content
3. Route to appropriate extractor (HTML or PDF)
4. Normalize extracted values
5. LLM fallback for unresolved fields
6. Score confidence
7. Attach citations
8. Create Comparable + ExtractedFields in DB
9. Update job status
"""

import uuid
from datetime import datetime

from workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def run_extraction(self, job_id: str, source_id: str):
    """
    Main extraction task. Runs synchronously within the Celery worker.

    Args:
        job_id: UUID of the ExtractionJob
        source_id: UUID of the Source to extract from
    """
    # Use sync database access within the worker
    import os
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    DATABASE_URL = os.environ.get(
        "DATABASE_URL_SYNC",
        "postgresql://muqayyim:muqayyim@localhost:5432/muqayyim"
    )
    engine = create_engine(DATABASE_URL)

    with Session(engine) as db:
        from api.app.models import Source, ExtractionJob, Comparable, ExtractedField

        # Load job and source
        job = db.query(ExtractionJob).filter(ExtractionJob.id == uuid.UUID(job_id)).first()
        source = db.query(Source).filter(Source.id == uuid.UUID(source_id)).first()

        if not job or not source:
            return {"error": "Job or source not found"}

        # Mark job as running
        job.status = "running"
        job.started_at = datetime.utcnow()
        db.commit()

        try:
            # Route to extractor based on source type
            if source.source_type == "url":
                fields, raw_content = _extract_from_url(source)
                source.raw_content = raw_content
            elif source.source_type == "pdf":
                fields, raw_content = _extract_from_pdf(source)
                source.raw_content = raw_content
            else:
                raise ValueError(f"Unknown source type: {source.source_type}")

            source.status = "fetched"

            # Create comparable
            comp = Comparable(
                id=uuid.uuid4(),
                case_id=source.case_id,
                source_id=source.id,
                extraction_job_id=job.id,
                status="draft",
                reliability_score=_infer_reliability(source),
            )

            # Populate denormalized fields from extracted data
            field_map = {f["field_name"]: f for f in fields}
            comp.property_title = _get_norm(field_map, "property_title") or _get_norm(field_map, "title")
            # city: prefer city_en (English normalized), fall back to city
            comp.city = _get_norm(field_map, "city_en") or _get_norm(field_map, "city")
            comp.district = _get_norm(field_map, "district")
            comp.property_type = _get_norm(field_map, "property_type")
            comp.evidence_type = _get_norm(field_map, "evidence_type")
            comp.asking_price = _get_float(field_map, "asking_price")
            comp.transacted_price = _get_float(field_map, "transacted_price")
            comp.currency = _get_norm(field_map, "currency") or "SAR"
            comp.primary_area_sqm = _get_float(field_map, "primary_area_sqm") or _get_float(field_map, "area_sqm")
            comp.listing_date = _get_norm(field_map, "listing_date")
            comp.transaction_date = _get_norm(field_map, "transaction_date")
            comp.tenure = _get_norm(field_map, "tenure")
            comp.latitude = _get_float(field_map, "latitude")
            comp.longitude = _get_float(field_map, "longitude")
            comp.notes = _get_norm(field_map, "notes")

            # Price per sqm: use extracted value if available, else compute
            extracted_ppsm = _get_float(field_map, "price_per_sqm")
            if extracted_ppsm:
                comp.price_per_sqm = extracted_ppsm
            else:
                price = comp.asking_price or comp.transacted_price
                if price and comp.primary_area_sqm and comp.primary_area_sqm > 0:
                    comp.price_per_sqm = round(price / comp.primary_area_sqm, 2)

            db.add(comp)
            db.flush()

            # Create ExtractedField records
            for f in fields:
                ef = ExtractedField(
                    id=uuid.uuid4(),
                    extraction_job_id=job.id,
                    comparable_id=comp.id,
                    field_name=f["field_name"],
                    raw_value=f.get("raw_value"),
                    normalized_value=f.get("normalized_value"),
                    display_value=f.get("display_value") or f.get("normalized_value") or f.get("raw_value"),
                    value_type=f.get("value_type", "string"),
                    confidence=f.get("confidence", 0.0),
                    classification=f.get("classification", "fact"),
                    citation=f.get("citation"),
                    extraction_version="1.0.0",
                    extracted_at=datetime.utcnow(),
                )
                db.add(ef)

            # Mark job complete
            if source.source_type == "url":
                url = source.url or ""
                if "aqarsas.sa" in url:
                    job.extractor_name = "aqarsas_extractor"
                    job.extractor_version = "1.3.0"
                elif "paseetah.com" in url:
                    job.extractor_name = "paseetah_extractor"
                    job.extractor_version = "1.2.0"
                else:
                    job.extractor_name = "html_extractor"
                    job.extractor_version = "1.0.0"
            else:
                job.extractor_name = "pdf_extractor"
                job.extractor_version = "1.0.0"
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            db.commit()

            return {"status": "completed", "comparable_id": str(comp.id)}

        except Exception as e:
            job.status = "failed"
            job.error_log = str(e)
            job.completed_at = datetime.utcnow()
            source.status = "failed"
            source.error_message = str(e)
            db.commit()

            # Retry on transient errors
            if self.request.retries < self.max_retries:
                raise self.retry(exc=e)

            return {"status": "failed", "error": str(e)}


def _extract_from_url(source) -> tuple[list[dict], str]:
    """
    Extract fields from a URL source.
    Routes to specialized extractors for known platforms (AqarSAS, Paseetah),
    falls back to generic HTML extraction for unknown URLs.
    """
    url = source.url or ""

    # ── Route to specialized extractors ───────────────────────────────────────
    if "aqarsas.sa" in url:
        return _run_async(_extract_aqarsas(source))
    if "paseetah.com" in url:
        return _run_async(_extract_paseetah(source))

    # ── Generic HTML fallback ──────────────────────────────────────────────────
    return _extract_generic_html(source)


def _run_async(coro):
    """Run an async coroutine from sync Celery context."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


async def _extract_aqarsas(source) -> tuple[list[dict], str]:
    """Run AqarSAS specialized extractor."""
    from extractors.aqarsas_extractor import AqarSASExtractor

    extractor = AqarSASExtractor()
    result = await extractor.extract(
        source_id=source.id,
        url=source.url,
    )
    if result.error:
        raise RuntimeError(result.error)
    return result.fields, result.raw_content or ""


async def _extract_paseetah(source) -> tuple[list[dict], str]:
    """Run Paseetah specialized extractor."""
    from extractors.paseetah_extractor import PaseetahExtractor

    extractor = PaseetahExtractor()
    result = await extractor.extract(
        source_id=source.id,
        url=source.url,
    )
    if result.error:
        raise RuntimeError(result.error)
    return result.fields, result.raw_content or ""


def _extract_generic_html(source) -> tuple[list[dict], str]:
    """
    Generic HTML extraction fallback for unknown URLs.
    """
    import httpx
    from bs4 import BeautifulSoup

    url = source.url
    raw_html = ""

    try:
        resp = httpx.get(url, timeout=30, follow_redirects=True)
        raw_html = resp.text
    except Exception as e:
        return [{
            "field_name": "error",
            "raw_value": str(e),
            "normalized_value": str(e),
            "confidence": 0.0,
            "citation": _make_citation(source, "", "Error fetching URL"),
        }], ""

    soup = BeautifulSoup(raw_html, "lxml")

    # Extract title
    title = soup.title.string if soup.title else None

    fields = []

    if title:
        fields.append({
            "field_name": "property_title",
            "raw_value": title,
            "normalized_value": title.strip(),
            "display_value": title.strip(),
            "confidence": 0.7,
            "classification": "fact",
            "value_type": "string",
            "citation": _make_citation(source, "title", title[:200]),
        })

    # Placeholder: extract page text for future LLM processing
    page_text = soup.get_text(separator="\n", strip=True)[:5000]
    fields.append({
        "field_name": "raw_page_text",
        "raw_value": page_text[:2000],
        "normalized_value": None,
        "confidence": 1.0,
        "classification": "fact",
        "value_type": "string",
        "citation": _make_citation(source, "body", page_text[:200]),
    })

    return fields, raw_html


def _extract_from_pdf(source) -> tuple[list[dict], str]:
    """
    Extract fields from a PDF source.
    TODO: Replace with full PDFExtractor pipeline.
    """
    import pdfplumber

    fields = []
    full_text = ""

    try:
        with pdfplumber.open(source.file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ""
                full_text += f"\n--- Page {page_num} ---\n{text}"
    except Exception as e:
        return [{
            "field_name": "error",
            "raw_value": str(e),
            "normalized_value": str(e),
            "confidence": 0.0,
            "citation": _make_citation(source, "file", f"Error reading PDF: {e}"),
        }], ""

    if full_text.strip():
        fields.append({
            "field_name": "raw_page_text",
            "raw_value": full_text[:5000],
            "normalized_value": None,
            "confidence": 1.0,
            "classification": "fact",
            "value_type": "string",
            "citation": _make_citation(source, "pages:1-all", full_text[:200]),
        })

    # TODO: Implement full PDF extraction
    # - Table extraction via pdfplumber.extract_tables()
    # - Pattern matching for prices, areas, dates
    # - LLM fallback for narrative sections

    return fields, full_text


def _make_citation(source, locator: str, snippet: str) -> dict:
    """Build a citation dict for an extracted field."""
    return {
        "source_id": str(source.id),
        "source_type": source.source_type,
        "source_url_or_name": source.url or source.file_name or "unknown",
        "retrieval_timestamp": datetime.utcnow().isoformat(),
        "locator": locator,
        "snippet": (snippet or "")[:500],
        "extractor_name": "html_extractor" if source.source_type == "url" else "pdf_extractor",
        "extractor_version": "1.0.0",
        "parse_confidence": 0.5,
        "llm_confidence": None,
        "crosscheck_confidence": None,
        "normalization_notes": None,
    }


def _infer_reliability(source) -> int:
    """Infer reliability score from source type."""
    if source.source_type == "pdf":
        return 3  # Broker material
    elif source.source_type == "url":
        return 2  # Marketplace listing
    return 1  # Manual / unknown


def _get_norm(field_map: dict, name: str) -> str | None:
    f = field_map.get(name)
    return f["normalized_value"] if f else None


def _get_float(field_map: dict, name: str) -> float | None:
    f = field_map.get(name)
    if not f or not f.get("normalized_value"):
        return None
    try:
        return float(f["normalized_value"])
    except (ValueError, TypeError):
        return None
