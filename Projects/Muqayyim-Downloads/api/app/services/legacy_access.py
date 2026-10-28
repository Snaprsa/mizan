"""Owner-scoped access for the legacy case/evidence API.

Return 404 for absent and unowned resources to avoid disclosing their existence.
"""
from fastapi import HTTPException
from sqlalchemy import select
from api.app.models import Case, Source, Comparable, ExtractionJob
from api.app.services.foundation import owner_id

async def owned_case(db, case_id, user):
    row = await db.scalar(select(Case).where(Case.id == case_id, Case.created_by == owner_id(user)))
    if row is None: raise HTTPException(404, 'Case not found')
    return row

async def owned_legacy_source(db, source_id, user):
    row = await db.scalar(select(Source).join(Case, Source.case_id == Case.id).where(
        Source.id == source_id, Case.created_by == owner_id(user)))
    if row is None: raise HTTPException(404, 'Source not found')
    return row

async def owned_comparable(db, comp_id, user):
    row = await db.scalar(select(Comparable).join(Case, Comparable.case_id == Case.id).where(
        Comparable.id == comp_id, Case.created_by == owner_id(user)))
    if row is None: raise HTTPException(404, 'Comparable not found')
    return row

async def owned_job(db, job_id, user):
    row = await db.scalar(select(ExtractionJob).join(Source, ExtractionJob.source_id == Source.id)
        .join(Case, Source.case_id == Case.id).where(ExtractionJob.id == job_id, Case.created_by == owner_id(user)))
    if row is None: raise HTTPException(404, 'Extraction job not found')
    return row
