"""
Exports router — download comparables as CSV, XLSX, or PDF summary.
"""

import re
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.app.auth import get_current_user
from api.app.audit import log_action
from api.app.database import get_db
from api.app.models import Case, Comparable, ExtractedField, Source

from api.app.services.legacy_access import owned_case

router = APIRouter()


def _safe_filename(title: str) -> str:
    """Sanitize title for use in Content-Disposition filename (ASCII only)."""
    # Replace non-ASCII with underscore, then collapse multiple underscores
    safe = re.sub(r"[^\x20-\x7e]", "_", title)
    safe = re.sub(r"[^\w\s\-]", "_", safe)
    safe = re.sub(r"_+", "_", safe).strip("_")
    return safe[:80] or "export"


async def _get_case_comps(case_id: uuid.UUID, db: AsyncSession, user: dict) -> tuple:
    """Load case with all comparables and their extracted fields."""
    case = await owned_case(db, case_id, user)

    result = await db.execute(
        select(Comparable).where(Comparable.case_id == case_id).order_by(Comparable.created_at)
    )
    comps = result.scalars().all()

    # Load fields for each comp
    comps_with_fields = []
    for comp in comps:
        fields_result = await db.execute(
            select(ExtractedField)
            .options(selectinload(ExtractedField.overrides))
            .where(ExtractedField.comparable_id == comp.id)
        )
        fields = fields_result.scalars().all()
        source = await db.scalar(select(Source).where(Source.id == comp.source_id))
        comps_with_fields.append((comp, fields, source))

    return case, comps_with_fields


@router.get("/cases/{case_id}/export/csv")
async def export_csv(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    case, comps_with_fields = await _get_case_comps(case_id, db, user)

    from reporting.csv_export import generate_csv
    output = generate_csv(case, comps_with_fields)

    await log_action(db, "case", case_id, "exported", user["id"], {"format": "csv"})

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="comps_{_safe_filename(case.title)}.csv"'},
    )


@router.get("/cases/{case_id}/export/xlsx")
async def export_xlsx(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    case, comps_with_fields = await _get_case_comps(case_id, db, user)

    from reporting.xlsx_export import generate_xlsx
    output = generate_xlsx(case, comps_with_fields)

    await log_action(db, "case", case_id, "exported", user["id"], {"format": "xlsx"})

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="comps_{_safe_filename(case.title)}.xlsx"'},
    )


@router.get("/cases/{case_id}/export/pdf")
async def export_pdf(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    case, comps_with_fields = await _get_case_comps(case_id, db, user)

    from reporting.pdf_summary import generate_pdf_summary
    output = generate_pdf_summary(case, comps_with_fields)

    await log_action(db, "case", case_id, "exported", user["id"], {"format": "pdf"})

    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="comps_summary_{_safe_filename(case.title)}.pdf"'},
    )
