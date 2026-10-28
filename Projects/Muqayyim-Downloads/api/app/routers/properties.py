"""Permanent property workspaces linked to the existing comparable case workflow."""
import re
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from api.app.auth import get_current_user
from api.app.audit import log_action
from api.app.database import get_db
from api.app.models.foundation import Property, PropertyRevision, PropertyAssumption
from api.app.schemas.foundation import PropertyInput, PropertyUpdate, AssumptionUpdate, CaseLink
from api.app.services.foundation import (owner_id, can_write, owned_property, validate_case,
    search_columns, property_response, save_snapshot, advance_revision)

router = APIRouter(prefix='/properties', tags=['Properties'])


@router.get('')
async def list_properties(q: str = Query('', max_length=255), city: str | None = None,
        property_type: str | None = None, limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0), db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    filters = [Property.created_by == owner_id(user)]
    if q:
        filters.append(or_(*(c.icontains(q, autoescape=True) for c in
            [Property.name, Property.city, Property.district, Property.address, Property.plot_number])))
    if city:
        filters.append(Property.city == city)
    if property_type:
        filters.append(Property.property_type == property_type)
    total = await db.scalar(select(func.count()).select_from(Property).where(*filters))
    rows = (await db.scalars(select(Property).where(*filters).order_by(Property.updated_at.desc())
                             .limit(limit).offset(offset))).all()
    return {'data': [{'id': str(p.id), 'name': p.name, 'city': p.city, 'district': p.district,
        'property_type': p.property_type, 'revision': p.revision, 'case_id': p.case_id,
        'updated_at': p.updated_at} for p in rows], 'total': total}


@router.post('', status_code=201)
async def create_property(body: PropertyInput, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    can_write(user)
    await validate_case(db, body.case_id, user)
    data = body.model_dump(mode='json')
    p = Property(data=data, created_by=owner_id(user), **search_columns(data))
    db.add(p)
    await db.flush()
    await save_snapshot(db, p, 'Property created', user)
    await log_action(db, 'property', p.id, 'created', user['id'], {'revision': p.revision})
    return await property_response(db, p)


@router.get('/{property_id}')
async def get_property(property_id: uuid.UUID, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return await property_response(db, await owned_property(db, property_id, user))


@router.put('/{property_id}')
async def replace_property(property_id: uuid.UUID, body: PropertyUpdate,
        db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    can_write(user)
    p = await owned_property(db, property_id, user)
    await validate_case(db, body.property.case_id, user)
    data = body.property.model_dump(mode='json')
    await advance_revision(db, p, body.expected_revision, {'data': data, **search_columns(data)})
    await save_snapshot(db, p, body.reason, user)
    await log_action(db, 'property', p.id, 'updated', user['id'], {'revision': p.revision, 'reason': body.reason})
    return await property_response(db, p)


@router.post('/{property_id}/case')
async def link_case(property_id: uuid.UUID, body: CaseLink,
        db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    can_write(user)
    p = await owned_property(db, property_id, user)
    await validate_case(db, body.case_id, user)
    data = {**p.data, 'case_id': str(body.case_id)}
    await advance_revision(db, p, body.expected_revision, {'data': data, 'case_id': body.case_id})
    await save_snapshot(db, p, body.reason, user)
    await log_action(db, 'property', p.id, 'case_linked', user['id'], {'case_id': str(body.case_id)})
    return await property_response(db, p)


@router.put('/{property_id}/assumptions/{key}')
async def set_assumption(property_id: uuid.UUID, key: str, body: AssumptionUpdate,
        db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    can_write(user)
    if not re.fullmatch(r'[a-z][a-z0-9_]{0,99}', key):
        raise HTTPException(422, 'Assumption key must be lowercase snake_case, up to 100 characters')
    p = await owned_property(db, property_id, user)
    await advance_revision(db, p, body.expected_revision)
    row = await db.scalar(select(PropertyAssumption).where(PropertyAssumption.property_id == p.id, PropertyAssumption.key == key))
    if row is None:
        row = PropertyAssumption(property_id=p.id, key=key)
        db.add(row)
    row.data = body.assumption.model_dump(mode='json')
    await save_snapshot(db, p, body.reason, user)
    await log_action(db, 'assumption', p.id, 'updated', user['id'], {'key': key, 'revision': p.revision, 'reason': body.reason})
    return await property_response(db, p)


@router.get('/{property_id}/revisions')
async def revisions(property_id: uuid.UUID, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    await owned_property(db, property_id, user)
    rows = (await db.scalars(select(PropertyRevision).where(PropertyRevision.property_id == property_id)
                             .order_by(PropertyRevision.revision.desc()))).all()
    return [{'revision': r.revision, 'reason': r.reason, 'created_at': r.created_at} for r in rows]


@router.get('/{property_id}/revisions/{revision}')
async def revision_detail(property_id: uuid.UUID, revision: int,
        db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    await owned_property(db, property_id, user)
    r = await db.scalar(select(PropertyRevision).where(PropertyRevision.property_id == property_id, PropertyRevision.revision == revision))
    if r is None:
        raise HTTPException(404, 'Revision not found')
    return {'revision': r.revision, 'reason': r.reason, 'created_at': r.created_at, 'snapshot': r.snapshot}
