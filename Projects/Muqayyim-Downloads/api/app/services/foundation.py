"""Persisted input history and provider-neutral ingestion; no implicit market assumptions."""
import uuid
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select, update
from api.app.models import Case
from api.app.models.foundation import Property, PropertyRevision, PropertyAssumption, DataSource, MarketObservation
from api.app.schemas.foundation import PropertyInput


def owner_id(user):
    return uuid.UUID(user['id'])


def can_write(user):
    if user['role'] in {'viewer', 'reviewer'}:
        raise HTTPException(403, 'This role cannot change analysis inputs')


async def owned_property(db, property_id, user):
    p = await db.scalar(select(Property).where(Property.id == property_id, Property.created_by == owner_id(user)))
    if p is None:
        raise HTTPException(404, 'Property not found')
    return p


async def validate_case(db, case_id, user):
    if case_id is None:
        return
    case = await db.scalar(select(Case).where(Case.id == case_id, Case.created_by == owner_id(user)))
    if case is None:
        raise HTTPException(404, 'Owned case not found')


def search_columns(data):
    return {'name': data['name'], 'case_id': uuid.UUID(data['case_id']) if data['case_id'] else None,
            'country': data['country'], 'currency': data['currency'], 'locale': data['locale'],
            'city': data['location']['city'], 'district': data['location']['district'],
            'address': data['location']['address'], 'plot_number': data['location']['plot_number'],
            'property_type': data['property_type']}


async def assumptions(db, p):
    rows = (await db.scalars(select(PropertyAssumption).where(PropertyAssumption.property_id == p.id)
                             .order_by(PropertyAssumption.key))).all()
    return {r.key: {**r.data, 'effective_value': r.data['user_override'] if r.data['user_override'] is not None else r.data['value']} for r in rows}


async def property_response(db, p):
    return {'id': str(p.id), 'revision': p.revision, 'property': p.data,
            'created_at': p.created_at, 'updated_at': p.updated_at, 'assumptions': await assumptions(db, p)}


async def save_snapshot(db, p, reason, user):
    await db.flush()
    db.add(PropertyRevision(property_id=p.id, revision=p.revision, reason=reason,
        created_by=owner_id(user), snapshot={'schema_version': 'mizan.foundation.v1',
        'property': p.data, 'assumptions': await assumptions(db, p),
        'calculation_status': 'not_calculated', 'calculation_version': None,
        'model_version': None, 'outputs': None}))
    await db.flush()


async def advance_revision(db, p, expected, changes=None):
    """Atomic compare-and-swap works for both SQLite and PostgreSQL."""
    result = await db.execute(update(Property).where(Property.id == p.id, Property.revision == expected)
        .values(revision=expected + 1, updated_at=datetime.utcnow(), **(changes or {}))
        .execution_options(synchronize_session=False))
    if result.rowcount != 1:
        raise HTTPException(409, 'Property changed. Reload before saving; your edit was not applied.')
    await db.refresh(p)


async def owned_source(db, source_id, user):
    s = await db.scalar(select(DataSource).where(DataSource.id == source_id, DataSource.created_by == owner_id(user)))
    if s is None:
        raise HTTPException(404, 'Data source not found')
    return s


async def ingest(db, source, observations):
    """Append-only observations. Replays are idempotent; corrected evidence needs a new record key."""
    new, duplicates = 0, 0
    seen = {}
    for item in observations:
        data = item.model_dump(mode='json')
        previous = seen.get(item.external_id)
        if previous is None:
            existing = await db.scalar(select(MarketObservation).where(
                MarketObservation.data_source_id == source.id, MarketObservation.external_id == item.external_id))
            if existing:
                previous = observation_data(existing)
        if previous is not None:
            if previous != data:
                raise HTTPException(409, f'Conflicting evidence for {item.external_id}; use a new record key')
            duplicates += 1
            continue
        seen[item.external_id] = data
        columns = dict(data)
        columns['details'] = columns.pop('metadata')
        db.add(MarketObservation(data_source_id=source.id, **columns))
        new += 1
    await db.flush()
    return {'inserted': new, 'duplicates': duplicates}


def observation_data(row):
    return {k: getattr(row, k) for k in ('external_id', 'observed_on', 'country', 'city', 'district',
        'property_type', 'metric', 'unit', 'raw_value', 'normalized_value', 'reliability')} | {'metadata': row.details}
