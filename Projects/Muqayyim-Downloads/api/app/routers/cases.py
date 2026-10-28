"""
Cases router — create, list, get valuation cases.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.auth import get_current_user
from api.app.audit import log_action
from api.app.database import get_db
from api.app.models import Case, Source, Comparable
from api.app.schemas import CaseCreate, CaseResponse, CaseListResponse

from api.app.services.foundation import can_write, owner_id
from api.app.services.legacy_access import owned_case

router = APIRouter()


@router.post("", response_model=CaseResponse, status_code=201)
async def create_case(
    body: CaseCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    can_write(user)
    case = Case(
        id=uuid.uuid4(),
        title=body.title,
        description=body.description,
        status="draft",
        created_by=uuid.UUID(user["id"]),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(case)
    await db.flush()

    await log_action(db, "case", case.id, "created", user["id"], {"title": body.title})

    return CaseResponse(
        id=case.id,
        title=case.title,
        description=case.description,
        status=case.status,
        created_by=case.created_by,
        created_at=case.created_at,
        updated_at=case.updated_at,
        source_count=0,
        comparable_count=0,
    )


@router.get("", response_model=CaseListResponse)
async def list_cases(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Case).where(Case.created_by == owner_id(user)).order_by(Case.created_at.desc()))
    cases = result.scalars().all()

    responses = []
    for c in cases:
        src_count = await db.scalar(select(func.count(Source.id)).where(Source.case_id == c.id))
        comp_count = await db.scalar(select(func.count(Comparable.id)).where(Comparable.case_id == c.id))
        responses.append(CaseResponse(
            id=c.id,
            title=c.title,
            description=c.description,
            status=c.status,
            created_by=c.created_by,
            created_at=c.created_at,
            updated_at=c.updated_at,
            source_count=src_count or 0,
            comparable_count=comp_count or 0,
        ))

    return CaseListResponse(data=responses, total=len(responses))


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    case = await owned_case(db, case_id, user)

    src_count = await db.scalar(select(func.count(Source.id)).where(Source.case_id == case.id))
    comp_count = await db.scalar(select(func.count(Comparable.id)).where(Comparable.case_id == case.id))

    return CaseResponse(
        id=case.id,
        title=case.title,
        description=case.description,
        status=case.status,
        created_by=case.created_by,
        created_at=case.created_at,
        updated_at=case.updated_at,
        source_count=src_count or 0,
        comparable_count=comp_count or 0,
    )
