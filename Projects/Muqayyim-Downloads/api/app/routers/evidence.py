"""Reviewed comparable details, and clearly labelled synthetic demo comparables."""
import math
import uuid
from datetime import date
from typing import Literal
from fastapi import APIRouter, Depends
from pydantic import Field, ValidationError, model_validator
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from api.app.audit import log_action
from api.app.auth import get_current_user
from api.app.database import get_db
from api.app.models import Case, Comparable, Source
from api.app.schemas.foundation import ComparableAttributes, StrictModel
from api.app.services.analysis_workflow import saudi_today
from api.app.services.foundation import can_write, owner_id
from api.app.services.legacy_access import owned_comparable
from api.app.services.valuation_catalog import PROPERTY_TYPES

router = APIRouter(prefix='/evidence', tags=['Comparable evidence'])
DEMO_CASE = 'DEMO comparables (synthetic, not market evidence)'
DEMO_SOURCE = 'Synthetic demo data'
# Greater Riyadh; demo records outside it are rejected so they can't land elsewhere on the map.
RIYADH = {'south': 24.40, 'north': 25.10, 'west': 46.35, 'east': 47.10}


class SaveAttributes(StrictModel):
    attributes: ComparableAttributes
    reason: str = Field(min_length=3, max_length=500)


class DemoComparable(StrictModel):
    title: str = Field(min_length=1, max_length=200)
    property_type: str
    evidence_type: Literal['transaction_achieved', 'listing_asking']
    price_sar: float = Field(gt=0)
    area_sqm: float = Field(gt=0)
    date: date
    latitude: float
    longitude: float
    district: str | None = Field(None, max_length=200)
    attributes: ComparableAttributes = Field(default_factory=ComparableAttributes)

    @model_validator(mode='after')
    def plausible(self):
        if self.property_type not in PROPERTY_TYPES:
            raise ValueError('Unsupported property_type')
        if not (RIYADH['south'] <= self.latitude <= RIYADH['north'] and RIYADH['west'] <= self.longitude <= RIYADH['east']):
            raise ValueError('Coordinates are outside Riyadh (latitude 24.40–25.10, longitude 46.35–47.10)')
        if self.date > saudi_today():
            raise ValueError('Date is in the future')
        if not math.isfinite(self.price_sar / self.area_sqm):
            raise ValueError('Invalid price or area')
        return self


class DemoImport(StrictModel):
    records: list[dict] = Field(min_length=1, max_length=500)


@router.put('/{comparable_id}/attributes')
async def save_attributes(comparable_id: uuid.UUID, body: SaveAttributes, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    can_write(user)
    comp = await owned_comparable(db, comparable_id, user)
    previous = comp.attributes or {}
    values = body.attributes.model_dump(mode='json')
    comp.attributes = {**values, **({'is_demo': True} if previous.get('is_demo') else {})}
    await log_action(db, 'comparable', comp.id, 'attributes_reviewed', user['id'], {'before': previous, 'after': values, 'reason': body.reason})
    return {'id': 'comparable:' + str(comp.id), 'attributes': comp.attributes}


async def demo_rows(db, user):
    rows = (await db.scalars(select(Comparable).join(Case, Case.id == Comparable.case_id)
                             .where(Case.created_by == owner_id(user), Case.title == DEMO_CASE))).all()
    return [c for c in rows if (c.attributes or {}).get('is_demo')]


@router.post('/demo', status_code=201)
async def import_demo(body: DemoImport, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """Always labelled: the title prefix, source, lowest reliability and is_demo flag cannot be overridden."""
    can_write(user)
    case = await db.scalar(select(Case).where(Case.created_by == owner_id(user), Case.title == DEMO_CASE))
    if case is None:
        case = Case(title=DEMO_CASE, created_by=owner_id(user), status='draft')
        db.add(case); await db.flush()
    source = await db.scalar(select(Source).where(Source.case_id == case.id, Source.file_name == DEMO_SOURCE))
    if source is None:
        source = Source(case_id=case.id, source_type='manual', status='fetched', file_name=DEMO_SOURCE)
        db.add(source); await db.flush()
    seen = {(c.property_title, c.latitude, c.longitude, c.transaction_date or c.listing_date) for c in await demo_rows(db, user)}
    inserted, duplicates, rejected = 0, 0, []
    for index, raw in enumerate(body.records):
        try:
            r = DemoComparable.model_validate(raw)
        except ValidationError as exc:
            first = exc.errors()[0]
            rejected.append({'index': index, 'title': str(raw.get('title', ''))[:80] if isinstance(raw, dict) else '',
                             'reason': f"{'.'.join(map(str, first['loc']))}: {first['msg']}".lstrip(': ')})
            continue
        title = 'DEMO · ' + r.title.removeprefix('DEMO · ')
        day = r.date.isoformat()
        if (title, r.latitude, r.longitude, day) in seen:
            duplicates += 1; continue
        seen.add((title, r.latitude, r.longitude, day))
        sale = r.evidence_type == 'transaction_achieved'
        db.add(Comparable(case_id=case.id, source_id=source.id, status='active', reliability_score=1, property_title=title, city='Riyadh',
            district=r.district, property_type=r.property_type, evidence_type=r.evidence_type, transacted_price=r.price_sar if sale else None,
            asking_price=None if sale else r.price_sar, currency='SAR', primary_area_sqm=r.area_sqm, price_per_sqm=r.price_sar / r.area_sqm,
            transaction_date=day if sale else None, listing_date=None if sale else day, latitude=r.latitude, longitude=r.longitude,
            notes='SYNTHETIC DEMO DATA. Not market evidence.', attributes={**r.attributes.model_dump(mode='json'), 'is_demo': True}))
        inserted += 1
    await log_action(db, 'case', case.id, 'demo_comparables_imported', user['id'], {'inserted': inserted, 'duplicates': duplicates, 'rejected': len(rejected)})
    return {'inserted': inserted, 'duplicates': duplicates, 'rejected': rejected[:50], 'rejected_count': len(rejected)}


@router.delete('/demo')
async def remove_demo(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """Removes only flagged demo comparables. Saved valuation snapshots keep what they used."""
    can_write(user)
    rows = await demo_rows(db, user)
    for row in rows:
        await db.delete(row)
    await db.flush()
    case_ids = [c for c in await db.scalars(select(Case.id).where(Case.created_by == owner_id(user), Case.title == DEMO_CASE))]
    if case_ids:  # The demo case holds nothing else, so it goes too and doesn't linger in Cases.
        await db.execute(delete(Source).where(Source.case_id.in_(case_ids)))
        await db.execute(delete(Case).where(Case.id.in_(case_ids)))
    await log_action(db, 'case', uuid.uuid4(), 'demo_comparables_removed', user['id'], {'removed': len(rows)})
    return {'removed': len(rows)}
