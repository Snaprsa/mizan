"""Source management service."""
import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.database import Source
from ..core.config import settings


class SourceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_url_source(self, case_id: str, url: str) -> Source:
        source = Source(
            id=str(uuid.uuid4()),
            case_id=case_id,
            source_type="url",
            url=url,
            fetch_status="pending",
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(source)
        await self.db.flush()
        return source

    async def add_pdf_source(self, case_id: str, filename: str, file_content: bytes) -> Source:
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        file_id = str(uuid.uuid4())
        safe_filename = f"{file_id}_{filename}"
        file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
        with open(file_path, "wb") as f:
            f.write(file_content)

        source = Source(
            id=file_id,
            case_id=case_id,
            source_type="pdf",
            filename=filename,
            file_path=file_path,
            fetch_status="fetched",
            fetched_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(source)
        await self.db.flush()
        return source

    async def list_sources(self, case_id: str) -> List[Source]:
        result = await self.db.execute(
            select(Source).where(Source.case_id == case_id).order_by(Source.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_source(self, source_id: str) -> Optional[Source]:
        result = await self.db.execute(select(Source).where(Source.id == source_id))
        return result.scalar_one_or_none()
