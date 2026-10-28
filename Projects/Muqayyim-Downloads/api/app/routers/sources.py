"""
Sources router — add URLs, upload PDFs, list sources for a case.
"""

import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.auth import get_current_user
from api.app.audit import log_action
from api.app.config import get_settings
from api.app.database import get_db
from api.app.models import Case, Source
from api.app.schemas import SourceAddURL, SourceResponse

from api.app.services.foundation import can_write
from api.app.services.legacy_access import owned_case, owned_legacy_source

router = APIRouter()
settings = get_settings()


@router.post("/cases/{case_id}/sources/url", response_model=SourceResponse, status_code=201)
async def add_url_source(
    case_id: uuid.UUID,
    body: SourceAddURL,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    can_write(user)
    await owned_case(db, case_id, user)

    source = Source(
        id=uuid.uuid4(),
        case_id=case_id,
        source_type="url",
        url=body.url,
        status="pending",
        created_at=datetime.utcnow(),
    )
    db.add(source)
    await db.flush()

    await log_action(db, "source", source.id, "created", user["id"], {"url": body.url})

    return SourceResponse(
        id=source.id,
        case_id=source.case_id,
        source_type=source.source_type,
        url=source.url,
        file_name=None,
        status=source.status,
        error_message=None,
        created_at=source.created_at,
    )


@router.post("/cases/{case_id}/sources/pdf", response_model=SourceResponse, status_code=201)
async def upload_pdf_source(
    case_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    can_write(user)
    await owned_case(db, case_id, user)

    # Reject path components before any filesystem mutation.
    filename = file.filename or ''
    if '/' in filename or '\\' in filename or not filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="A plain PDF filename is required")
    source_id = uuid.uuid4()
    storage_dir = Path(settings.storage_local_path) / str(case_id) / str(source_id)
    storage_dir.mkdir(parents=True, exist_ok=True)
    file_path = storage_dir / filename
    content = await file.read()
    file_path.write_bytes(content)

    source = Source(
        id=source_id,
        case_id=case_id,
        source_type="pdf",
        file_path=str(file_path),
        file_name=file.filename,
        status="pending",
        created_at=datetime.utcnow(),
    )
    db.add(source)
    await db.flush()

    await log_action(db, "source", source.id, "created", user["id"], {"file": file.filename})

    return SourceResponse(
        id=source.id,
        case_id=source.case_id,
        source_type=source.source_type,
        url=None,
        file_name=source.file_name,
        status=source.status,
        error_message=None,
        created_at=source.created_at,
    )


@router.get("/sources/{source_id}/raw", response_model=dict)
async def get_source_raw(
    source_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Debug endpoint: return raw_content of a source."""
    source = await owned_legacy_source(db, source_id, user)
    return {"source_id": str(source.id), "raw_content": source.raw_content}


@router.get("/cases/{case_id}/sources", response_model=list[SourceResponse])
async def list_sources(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    await owned_case(db, case_id, user)
    result = await db.execute(
        select(Source).where(Source.case_id == case_id).order_by(Source.created_at.desc())
    )
    sources = result.scalars().all()
    return [
        SourceResponse(
            id=s.id,
            case_id=s.case_id,
            source_type=s.source_type,
            url=s.url,
            file_name=s.file_name,
            status=s.status,
            error_message=s.error_message,
            created_at=s.created_at,
        )
        for s in sources
    ]
