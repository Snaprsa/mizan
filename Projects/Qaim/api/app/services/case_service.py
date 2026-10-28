"""Case management service."""
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from ..models.database import Case, Source, Comparable


class CaseService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_case(self, title: str, description: str = None, city: str = None) -> Case:
        case = Case(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            city=city,
            created_by="admin",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(case)
        await self.db.flush()
        return case

    async def list_cases(self) -> List[dict]:
        result = await self.db.execute(
            select(Case).order_by(Case.created_at.desc())
        )
        cases = result.scalars().all()
        out = []
        for case in cases:
            src_count = await self.db.execute(
                select(func.count(Source.id)).where(Source.case_id == case.id)
            )
            comp_count = await self.db.execute(
                select(func.count(Comparable.id)).where(Comparable.case_id == case.id)
            )
            d = {
                "id": case.id,
                "title": case.title,
                "description": case.description,
                "city": case.city,
                "created_by": case.created_by,
                "created_at": case.created_at,
                "updated_at": case.updated_at,
                "source_count": src_count.scalar() or 0,
                "comp_count": comp_count.scalar() or 0,
            }
            out.append(d)
        return out

    async def get_case(self, case_id: str) -> Optional[dict]:
        result = await self.db.execute(select(Case).where(Case.id == case_id))
        case = result.scalar_one_or_none()
        if not case:
            return None
        src_count = await self.db.execute(
            select(func.count(Source.id)).where(Source.case_id == case.id)
        )
        comp_count = await self.db.execute(
            select(func.count(Comparable.id)).where(Comparable.case_id == case.id)
        )
        return {
            "id": case.id,
            "title": case.title,
            "description": case.description,
            "city": case.city,
            "created_by": case.created_by,
            "created_at": case.created_at,
            "updated_at": case.updated_at,
            "source_count": src_count.scalar() or 0,
            "comp_count": comp_count.scalar() or 0,
        }
