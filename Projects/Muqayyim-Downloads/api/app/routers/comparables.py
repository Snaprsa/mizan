"""
Comparables router — list comps, override fields, mark invalid/outlier.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.app.auth import get_current_user
from api.app.audit import log_action
from api.app.database import get_db
from api.app.models import Comparable, ExtractedField, Override, Source
from api.app.schemas import (
    ComparableResponse, ComparableListResponse, ComparableStatusUpdate,
    ExtractedFieldResponse, FieldOverrideRequest,
)

from api.app.services.foundation import can_write
from api.app.services.legacy_access import owned_case, owned_comparable

router = APIRouter()


def _build_comp_response(comp: Comparable, fields: list, source: Source = None) -> ComparableResponse:
    field_responses = [
        ExtractedFieldResponse(
            id=f.id,
            field_name=f.field_name,
            raw_value=f.raw_value,
            normalized_value=f.normalized_value,
            display_value=f.display_value,
            confidence=f.confidence,
            classification=f.classification or "fact",
            citation=f.citation,
            is_overridden=len(f.overrides) > 0 if hasattr(f, 'overrides') and f.overrides else False,
            override_value=f.overrides[-1].new_value if hasattr(f, 'overrides') and f.overrides else None,
        )
        for f in fields
    ]

    return ComparableResponse(
        id=comp.id,
        case_id=comp.case_id,
        source_id=comp.source_id,
        status=comp.status,
        reliability_score=comp.reliability_score,
        property_title=comp.property_title,
        city=comp.city,
        district=comp.district,
        property_type=comp.property_type,
        evidence_type=comp.evidence_type,
        asking_price=comp.asking_price,
        transacted_price=comp.transacted_price,
        currency=comp.currency or "SAR",
        primary_area_sqm=comp.primary_area_sqm,
        price_per_sqm=comp.price_per_sqm,
        listing_date=comp.listing_date,
        transaction_date=comp.transaction_date,
        tenure=comp.tenure,
        latitude=comp.latitude,
        longitude=comp.longitude,
        notes=comp.notes,
        created_at=comp.created_at,
        extracted_fields=field_responses,
        source_url=source.url if source else None,
        source_type=source.source_type if source else None,
    )


@router.get("/cases/{case_id}/comparables", response_model=ComparableListResponse)
async def list_comparables(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    await owned_case(db, case_id, user)
    result = await db.execute(
        select(Comparable)
        .where(Comparable.case_id == case_id)
        .order_by(Comparable.created_at.desc())
    )
    comps = result.scalars().all()

    responses = []
    for comp in comps:
        # Load extracted fields with overrides
        fields_result = await db.execute(
            select(ExtractedField)
            .options(selectinload(ExtractedField.overrides))
            .where(ExtractedField.comparable_id == comp.id)
        )
        fields = fields_result.scalars().all()

        # Load source
        source = await db.scalar(select(Source).where(Source.id == comp.source_id))

        responses.append(_build_comp_response(comp, fields, source))

    return ComparableListResponse(data=responses, total=len(responses))


@router.patch("/comparables/{comp_id}/fields/{field_id}")
async def override_field(
    comp_id: uuid.UUID,
    field_id: uuid.UUID,
    body: FieldOverrideRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    can_write(user)
    await owned_comparable(db, comp_id, user)
    # Verify field exists and belongs to comparable
    field = await db.scalar(
        select(ExtractedField).where(
            ExtractedField.id == field_id,
            ExtractedField.comparable_id == comp_id,
        )
    )
    if not field:
        raise HTTPException(status_code=404, detail="Field not found for this comparable")

    # Create override record
    override = Override(
        id=uuid.uuid4(),
        extracted_field_id=field_id,
        old_value=field.normalized_value or field.raw_value,
        new_value=body.new_value,
        reason=body.reason,
        user_id=uuid.UUID(user["id"]),
        created_at=datetime.utcnow(),
    )
    db.add(override)

    # Update the field's display value
    field.display_value = body.new_value

    await log_action(db, "extracted_field", field_id, "overridden", user["id"], {
        "comparable_id": str(comp_id),
        "field_name": field.field_name,
        "old_value": override.old_value,
        "new_value": body.new_value,
        "reason": body.reason,
    })

    return {"status": "ok", "message": f"Field '{field.field_name}' overridden"}


@router.patch("/comparables/{comp_id}/status")
async def update_comparable_status(
    comp_id: uuid.UUID,
    body: ComparableStatusUpdate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    can_write(user)
    comp = await owned_comparable(db, comp_id, user)

    old_status = comp.status
    comp.status = body.status
    comp.updated_at = datetime.utcnow()

    await log_action(db, "comparable", comp_id, "status_changed", user["id"], {
        "old_status": old_status,
        "new_status": body.status,
        "reason": body.reason,
    })

    return {"status": "ok", "new_status": body.status}
