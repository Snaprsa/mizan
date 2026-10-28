"""Cases API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.database import get_db
from ..schemas.api_schemas import CaseCreateRequest, CaseResponse, MessageResponse
from ..services.case_service import CaseService

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("", response_model=CaseResponse)
async def create_case(req: CaseCreateRequest, db: AsyncSession = Depends(get_db)):
    svc = CaseService(db)
    case = await svc.create_case(title=req.title, description=req.description, city=req.city)
    return CaseResponse(
        id=case.id, title=case.title, description=case.description,
        city=case.city, created_by=case.created_by,
        created_at=case.created_at, updated_at=case.updated_at,
    )


@router.get("", response_model=list[CaseResponse])
async def list_cases(db: AsyncSession = Depends(get_db)):
    svc = CaseService(db)
    cases = await svc.list_cases()
    return [CaseResponse(**c) for c in cases]


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(case_id: str, db: AsyncSession = Depends(get_db)):
    svc = CaseService(db)
    case = await svc.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return CaseResponse(**case)
