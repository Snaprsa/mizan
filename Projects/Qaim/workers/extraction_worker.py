"""Extraction worker — runs extraction pipeline and persists results.

Uses Playwright (headless browser) to render JS-heavy pages like Aqar,
then runs the extraction pipeline on the fully rendered content.
"""
import sys
import os
import uuid
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def run_extraction_sync(
    db: AsyncSession,
    job_id: str,
    case_id: str,
    source_id: str,
):
    """Run extraction for a source."""
    from api.app.models.database import ExtractionJob, Source, Comparable, ExtractedField

    job_result = await db.execute(select(ExtractionJob).where(ExtractionJob.id == job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        return

    job.status = "running"
    job.started_at = datetime.now(timezone.utc)
    await db.flush()

    src_result = await db.execute(select(Source).where(Source.id == source_id))
    source = src_result.scalar_one_or_none()
    if not source:
        job.status = "failed"
        job.error_message = "Source not found"
        job.completed_at = datetime.now(timezone.utc)
        await db.flush()
        return

    try:
        fields = {}

        if source.source_type == "url":
            # Fetch with Playwright (renders JavaScript)
            html_content, text_content = await _fetch_with_playwright(source.url)
            
            if not html_content and not text_content:
                # Fallback to simple HTTP
                html_content = await _fetch_url_simple(source.url)
                text_content = None
            
            if not html_content:
                job.status = "failed"
                job.error_message = "Failed to fetch URL content"
                job.completed_at = datetime.now(timezone.utc)
                await db.flush()
                return

            source.raw_content = (text_content or html_content)[:50000]
            source.fetch_status = "fetched"
            source.fetched_at = datetime.now(timezone.utc)

            from extractors.html_extractor import extract_from_html
            fields = extract_from_html(
                html_content=html_content,
                source_url=source.url,
                source_id=source_id,
                rendered_text=text_content,  # pass the JS-rendered text
            )
            job.extractor_name = "html_extractor"

        elif source.source_type == "pdf":
            from extractors.pdf_extractor import extract_from_pdf
            fields = extract_from_pdf(
                file_path=source.file_path,
                source_id=source_id,
                filename=source.filename or "unknown.pdf",
            )
            job.extractor_name = "pdf_extractor"

        else:
            job.status = "failed"
            job.error_message = f"Unsupported source type: {source.source_type}"
            job.completed_at = datetime.now(timezone.utc)
            await db.flush()
            return

        if "_error" in fields:
            job.status = "failed"
            job.error_message = fields["_error"].get("raw_value", "Unknown extraction error")
            job.completed_at = datetime.now(timezone.utc)
            await db.flush()
            return

        # Create Comparable record
        comp_id = str(uuid.uuid4())
        comp = Comparable(
            id=comp_id,
            case_id=case_id,
            source_id=source_id,
            extraction_job_id=job_id,
            source_url=source.url,
            source_type=source.source_type,
        )

        field_column_map = {
            "property_title": "property_title",
            "city": "city",
            "district": "district",
            "subdistrict": "subdistrict",
            "property_category": "property_category",
            "property_subtype": "property_subtype",
            "evidence_type": "evidence_type",
            "currency": "currency",
            "tenure": "tenure",
            "listing_date": "listing_date",
            "transaction_date": "transaction_date",
            "notes": "notes",
        }

        for field_name, col_name in field_column_map.items():
            if field_name in fields:
                setattr(comp, col_name, fields[field_name]["normalized_value"])

        # Numeric fields
        for num_field, attr in [("asking_price", "asking_price"), ("transacted_price", "transacted_price"),
                                 ("latitude", "latitude"), ("longitude", "longitude")]:
            if num_field in fields:
                try:
                    setattr(comp, attr, float(fields[num_field]["normalized_value"]))
                except (ValueError, TypeError):
                    pass

        if "reliability_score" in fields:
            try:
                comp.reliability_score = int(fields["reliability_score"]["normalized_value"])
            except (ValueError, TypeError):
                comp.reliability_score = 2

        # Area
        if "land_area" in fields:
            try:
                area_val = float(fields["land_area"]["normalized_value"])
                comp.areas = [{
                    "raw_value": area_val, "raw_unit": "sqm",
                    "normalized_value": area_val, "normalized_unit": "sqm",
                    "area_type": "land_area",
                }]
                price = comp.asking_price or comp.transacted_price
                if price and area_val > 0:
                    comp.price_per_sqm = round(price / area_val, 2)
            except (ValueError, TypeError):
                pass

        db.add(comp)
        await db.flush()

        # Create ExtractedField records
        field_count = 0
        for field_name, field_data in fields.items():
            if field_name.startswith("_"):
                continue
            ef = ExtractedField(
                id=str(uuid.uuid4()),
                comparable_id=comp_id,
                source_id=source_id,
                field_name=field_name,
                raw_value=field_data.get("raw_value"),
                normalized_value=field_data.get("normalized_value"),
                confidence=field_data.get("confidence", 0.0),
                citation=field_data.get("citation"),
                extraction_version="0.3.0",
                fact_type="fact",
            )
            db.add(ef)
            field_count += 1

        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        job.fields_extracted = field_count
        await db.flush()

    except Exception as e:
        job.status = "failed"
        job.error_message = f"{type(e).__name__}: {str(e)}"
        job.completed_at = datetime.now(timezone.utc)
        await db.flush()
        traceback.print_exc()


async def _fetch_with_playwright(url: str) -> tuple:
    """Fetch URL using Playwright headless browser to render JavaScript.
    Returns (html_content, rendered_text_content).
    """
    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 900},
                locale="ar-SA",
            )
            page = await context.new_page()
            
            # Navigate and wait for network to settle
            try:
                await page.goto(url, timeout=30000, wait_until="networkidle")
            except Exception:
                # Fallback: just wait for load
                try:
                    await page.goto(url, timeout=30000, wait_until="load")
                except Exception:
                    pass
            
            # Extra wait for JS rendering
            await page.wait_for_timeout(6000)
            
            # Scroll down to trigger lazy-loaded content
            await page.evaluate("window.scrollBy(0, 500)")
            await page.wait_for_timeout(1000)
            
            # Click the map tab if present (reveals coordinates on Aqar)
            try:
                map_btn = page.locator('text=الخريطة').first
                if await map_btn.is_visible(timeout=2000):
                    await map_btn.click()
                    await page.wait_for_timeout(2000)
            except Exception:
                pass
            
            html = await page.content()
            text = await page.inner_text('body')
            await browser.close()
            
            print(f"[Playwright] Fetched {url[:80]}...: {len(html)} HTML, {len(text)} text chars")
            return html, text
    except Exception as e:
        print(f"[Playwright] Failed for {url}: {e}")
        import traceback
        traceback.print_exc()
        return None, None


async def _fetch_url_simple(url: str) -> Optional[str]:
    """Fallback: simple HTTP fetch without JS rendering."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            })
            resp.raise_for_status()
            return resp.text
    except Exception as e:
        print(f"[HTTP] Failed to fetch {url}: {e}")
        return None
