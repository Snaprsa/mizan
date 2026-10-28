"""
Extractions router — trigger extraction jobs and check status.

MVP: extraction runs synchronously inline (no Celery needed for local dev).
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.auth import get_current_user
from api.app.audit import log_action
from api.app.database import get_db
from api.app.models import Source, ExtractionJob
from api.app.schemas import ExtractionJobResponse, StartExtractionResponse

from api.app.services.foundation import can_write
from api.app.services.legacy_access import owned_legacy_source, owned_job

router = APIRouter()


@router.post("/sources/{source_id}/extract", response_model=StartExtractionResponse, status_code=202)
async def start_extraction(
    source_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    can_write(user)
    source = await owned_legacy_source(db, source_id, user)

    # Create extraction job
    job = ExtractionJob(
        id=uuid.uuid4(),
        source_id=source_id,
        status="pending",
        created_at=datetime.utcnow(),
    )
    db.add(job)
    await db.flush()

    await log_action(db, "extraction_job", job.id, "created", user["id"], {
        "source_id": str(source_id),
        "source_type": source.source_type,
    })

    # Run extraction synchronously inline (MVP — no Celery required)
    from api.app.services.extraction_service import run_extraction_inline
    result = await run_extraction_inline(db, job, source)

    await log_action(db, "extraction_job", job.id, result["status"], user["id"], result)

    return StartExtractionResponse(
        job_id=job.id,
        status=job.status,
        message=(
            f"Extraction {job.status}. "
            f"{result.get('fields_extracted', 0)} fields extracted."
            if job.status == "completed"
            else f"Extraction failed: {result.get('error', 'unknown error')}"
        ),
    )


@router.get("/extraction-jobs/{job_id}", response_model=ExtractionJobResponse)
async def get_extraction_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    job = await owned_job(db, job_id, user)

    return ExtractionJobResponse(
        id=job.id,
        source_id=job.source_id,
        status=job.status,
        extractor_name=job.extractor_name,
        extractor_version=job.extractor_version,
        error_log=job.error_log,
        started_at=job.started_at,
        completed_at=job.completed_at,
        created_at=job.created_at,
    )
