"""Extraction service — orchestrates async extraction jobs."""
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from ..models.database import ExtractionJob, Source, Comparable, ExtractedField


class ExtractionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_extraction(self, case_id: str, source_id: str) -> ExtractionJob:
        """Create an extraction job record. The actual work is done by the worker."""
        job = ExtractionJob(
            id=str(uuid.uuid4()),
            case_id=case_id,
            source_id=source_id,
            status="pending",
            extractor_version="0.1.0",
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(job)
        await self.db.flush()
        return job

    async def get_job(self, job_id: str) -> Optional[ExtractionJob]:
        result = await self.db.execute(
            select(ExtractionJob).where(ExtractionJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def list_jobs(self, case_id: str) -> List[ExtractionJob]:
        result = await self.db.execute(
            select(ExtractionJob)
            .where(ExtractionJob.case_id == case_id)
            .order_by(ExtractionJob.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_comps(self, case_id: str) -> List[Comparable]:
        result = await self.db.execute(
            select(Comparable)
            .where(Comparable.case_id == case_id)
            .options(
                selectinload(Comparable.extracted_fields),
                selectinload(Comparable.overrides),
            )
            .order_by(Comparable.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_comp(self, comp_id: str) -> Optional[Comparable]:
        result = await self.db.execute(
            select(Comparable)
            .where(Comparable.id == comp_id)
            .options(
                selectinload(Comparable.extracted_fields),
                selectinload(Comparable.overrides),
            )
        )
        return result.scalar_one_or_none()

    async def update_comp_status(self, comp_id: str, is_invalid: bool = None, is_outlier: bool = None) -> Optional[Comparable]:
        comp = await self.get_comp(comp_id)
        if not comp:
            return None
        if is_invalid is not None:
            comp.is_invalid = is_invalid
        if is_outlier is not None:
            comp.is_outlier = is_outlier
        comp.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return comp
