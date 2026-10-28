"""Extraction & Comparables API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.database import get_db
from ..schemas.api_schemas import (
    ExtractionJobResponse, ComparableResponse, ExtractedFieldResponse,
    FieldOverrideRequest, FieldOverrideResponse, CompStatusUpdate, MessageResponse,
)
from ..services.extraction_service import ExtractionService
from ..services.override_service import OverrideService

router = APIRouter(tags=["extraction"])


# ── Extraction Jobs ──

@router.post("/cases/{case_id}/sources/{source_id}/extract", response_model=ExtractionJobResponse)
async def start_extraction(case_id: str, source_id: str, db: AsyncSession = Depends(get_db)):
    """Kick off an extraction job for a source. Runs synchronously for MVP."""
    svc = ExtractionService(db)
    job = await svc.start_extraction(case_id, source_id)

    # In MVP, run extraction inline (sync). In production, dispatch to Celery.
    from workers.extraction_worker import run_extraction_sync
    await run_extraction_sync(db, job.id, case_id, source_id)

    # Refresh job
    updated_job = await svc.get_job(job.id)
    return ExtractionJobResponse(
        id=updated_job.id, case_id=updated_job.case_id, source_id=updated_job.source_id,
        status=updated_job.status, extractor_name=updated_job.extractor_name,
        extractor_version=updated_job.extractor_version, started_at=updated_job.started_at,
        completed_at=updated_job.completed_at, error_message=updated_job.error_message,
        fields_extracted=updated_job.fields_extracted, created_at=updated_job.created_at,
    )


@router.get("/cases/{case_id}/jobs", response_model=list[ExtractionJobResponse])
async def list_jobs(case_id: str, db: AsyncSession = Depends(get_db)):
    svc = ExtractionService(db)
    jobs = await svc.list_jobs(case_id)
    return [
        ExtractionJobResponse(
            id=j.id, case_id=j.case_id, source_id=j.source_id,
            status=j.status, extractor_name=j.extractor_name,
            extractor_version=j.extractor_version, started_at=j.started_at,
            completed_at=j.completed_at, error_message=j.error_message,
            fields_extracted=j.fields_extracted, created_at=j.created_at,
        )
        for j in jobs
    ]


@router.get("/jobs/{job_id}", response_model=ExtractionJobResponse)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    svc = ExtractionService(db)
    j = await svc.get_job(job_id)
    if not j:
        raise HTTPException(status_code=404, detail="Job not found")
    return ExtractionJobResponse(
        id=j.id, case_id=j.case_id, source_id=j.source_id,
        status=j.status, extractor_name=j.extractor_name,
        extractor_version=j.extractor_version, started_at=j.started_at,
        completed_at=j.completed_at, error_message=j.error_message,
        fields_extracted=j.fields_extracted, created_at=j.created_at,
    )


# ── Comparables ──

@router.get("/cases/{case_id}/comps", response_model=list[ComparableResponse])
async def get_comps(case_id: str, db: AsyncSession = Depends(get_db)):
    svc = ExtractionService(db)
    comps = await svc.get_comps(case_id)
    return [_comp_to_response(c) for c in comps]


@router.get("/comps/{comp_id}", response_model=ComparableResponse)
async def get_comp(comp_id: str, db: AsyncSession = Depends(get_db)):
    svc = ExtractionService(db)
    comp = await svc.get_comp(comp_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Comparable not found")
    return _comp_to_response(comp)


@router.patch("/comps/{comp_id}/status", response_model=ComparableResponse)
async def update_comp_status(comp_id: str, req: CompStatusUpdate, db: AsyncSession = Depends(get_db)):
    svc = ExtractionService(db)
    comp = await svc.update_comp_status(comp_id, is_invalid=req.is_invalid, is_outlier=req.is_outlier)
    if not comp:
        raise HTTPException(status_code=404, detail="Comparable not found")
    return _comp_to_response(comp)


# ── Overrides ──

@router.post("/comps/{comp_id}/override", response_model=FieldOverrideResponse)
async def override_field(comp_id: str, req: FieldOverrideRequest, db: AsyncSession = Depends(get_db)):
    svc = OverrideService(db)
    override = await svc.override_field(
        comp_id=comp_id,
        field_name=req.field_name,
        new_value=req.new_value,
        reason=req.reason,
    )
    if not override:
        raise HTTPException(status_code=404, detail="Comparable not found")
    return FieldOverrideResponse(
        id=override.id, comparable_id=override.comparable_id,
        field_name=override.field_name, old_value=override.old_value,
        new_value=override.new_value, reason=override.reason,
        overridden_by=override.overridden_by, overridden_at=override.overridden_at,
    )


def _comp_to_response(c) -> ComparableResponse:
    fields = [
        ExtractedFieldResponse(
            id=f.id, comparable_id=f.comparable_id,
            field_name=f.field_name, raw_value=f.raw_value,
            normalized_value=f.normalized_value, confidence=f.confidence,
            citation=f.citation, extraction_version=f.extraction_version,
            fact_type=f.fact_type,
        )
        for f in (c.extracted_fields or [])
    ]
    overrides = [
        FieldOverrideResponse(
            id=o.id, comparable_id=o.comparable_id,
            field_name=o.field_name, old_value=o.old_value,
            new_value=o.new_value, reason=o.reason,
            overridden_by=o.overridden_by, overridden_at=o.overridden_at,
        )
        for o in (c.overrides or [])
    ]
    return ComparableResponse(
        id=c.id, case_id=c.case_id, source_id=c.source_id,
        source_url=c.source_url, source_type=c.source_type,
        property_title=c.property_title, city=c.city,
        district=c.district, subdistrict=c.subdistrict,
        latitude=c.latitude, longitude=c.longitude,
        property_category=c.property_category,
        property_subtype=c.property_subtype,
        evidence_type=c.evidence_type,
        asking_price=c.asking_price, transacted_price=c.transacted_price,
        currency=c.currency, areas=c.areas or [],
        price_per_sqm=c.price_per_sqm,
        listing_date=c.listing_date, transaction_date=c.transaction_date,
        tenure=c.tenure, remaining_lease_term=c.remaining_lease_term,
        notes=c.notes, reliability_score=c.reliability_score,
        is_invalid=c.is_invalid, is_outlier=c.is_outlier,
        extracted_fields=fields, overrides=overrides,
        created_at=c.created_at, updated_at=c.updated_at,
    )
