"""Sources API routes."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.database import get_db
from ..schemas.api_schemas import SourceAddURLRequest, SourceResponse

from ..services.source_service import SourceService

router = APIRouter(prefix="/cases/{case_id}/sources", tags=["sources"])


@router.post("/url", response_model=SourceResponse)
async def add_url_source(case_id: str, req: SourceAddURLRequest, db: AsyncSession = Depends(get_db)):
    svc = SourceService(db)
    source = await svc.add_url_source(case_id, req.url)
    return SourceResponse(
        id=source.id, case_id=source.case_id, source_type=source.source_type,
        url=source.url, fetch_status=source.fetch_status,
        created_at=source.created_at,
    )


@router.post("/pdf", response_model=SourceResponse)
async def upload_pdf_source(case_id: str, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    content = await file.read()
    svc = SourceService(db)
    source = await svc.add_pdf_source(case_id, file.filename, content)
    return SourceResponse(
        id=source.id, case_id=source.case_id, source_type=source.source_type,
        filename=source.filename, fetch_status=source.fetch_status,
        fetched_at=source.fetched_at, created_at=source.created_at,
    )


@router.get("", response_model=list[SourceResponse])
async def list_sources(case_id: str, db: AsyncSession = Depends(get_db)):
    svc = SourceService(db)
    sources = await svc.list_sources(case_id)
    return [
        SourceResponse(
            id=s.id, case_id=s.case_id, source_type=s.source_type,
            url=s.url, filename=s.filename, fetch_status=s.fetch_status,
            fetched_at=s.fetched_at, created_at=s.created_at,
        )
        for s in sources
    ]
