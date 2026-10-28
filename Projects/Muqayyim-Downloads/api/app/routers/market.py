"""Source registration and append-only evidence imports with provenance."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from api.app.auth import get_current_user
from api.app.audit import log_action
from api.app.database import get_db
from api.app.models.foundation import DataSource, MarketObservation
from api.app.schemas.foundation import SourceInput, ObservationBatch
from api.app.services.foundation import owner_id, can_write, owned_source, ingest, observation_data
from api.app.services.market_adapters import CsvObservationAdapter

router = APIRouter(prefix='/market', tags=['Market data'])


@router.get('/sources')
async def list_sources(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    rows = (await db.scalars(select(DataSource).where(DataSource.created_by == owner_id(user))
                            .order_by(DataSource.created_at.desc()))).all()
    return [{'id': r.id, 'name': r.name, 'provider': r.provider, 'source_type': r.source_type,
             'uri': r.uri, 'notes': r.notes, 'created_at': r.created_at} for r in rows]


@router.post('/sources', status_code=201)
async def create_source(body: SourceInput, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    can_write(user)
    row = DataSource(created_by=owner_id(user), **body.model_dump())
    db.add(row)
    await db.flush()
    await log_action(db, 'data_source', row.id, 'created', user['id'], {'provider': row.provider})
    return {'id': row.id, **body.model_dump()}


@router.post('/sources/{source_id}/observations', status_code=201)
async def add_observations(source_id: uuid.UUID, body: ObservationBatch,
        db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    can_write(user)
    source = await owned_source(db, source_id, user)
    result = await ingest(db, source, body.observations)
    await log_action(db, 'data_source', source.id, 'observations_imported', user['id'], result)
    return result


@router.post('/sources/{source_id}/csv', status_code=201)
async def upload_csv(source_id: uuid.UUID, file: UploadFile = File(...),
        db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    can_write(user)
    source = await owned_source(db, source_id, user)
    data = await file.read(2_000_001)
    if len(data) > 2_000_000:
        raise HTTPException(413, 'Maximum CSV size is 2 MB')
    try:
        rows = CsvObservationAdapter().normalize(data.decode('utf-8-sig'))
    except (ValueError, UnicodeDecodeError) as exc:
        raise HTTPException(422, str(exc)) from exc
    result = await ingest(db, source, rows)
    await log_action(db, 'data_source', source.id, 'csv_imported', user['id'], result)
    return result


@router.get('/observations')
async def list_observations(city: str | None = None, metric: str | None = None,
        source_id: uuid.UUID | None = None, limit: int = Query(100, ge=1, le=500),
        offset: int = Query(0, ge=0), db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    filters = [DataSource.created_by == owner_id(user)]
    if city:
        filters.append(MarketObservation.city == city)
    if metric:
        filters.append(MarketObservation.metric == metric)
    if source_id:
        filters.append(MarketObservation.data_source_id == source_id)
    stmt = select(MarketObservation, DataSource.name).join(DataSource).where(*filters)
    rows = (await db.execute(stmt.order_by(MarketObservation.observed_on.desc()).limit(limit).offset(offset))).all()
    total = await db.scalar(select(func.count()).select_from(MarketObservation).join(DataSource).where(*filters))
    return {'data': [{'id': r.id, 'source_id': r.data_source_id, 'source': name, **observation_data(r)} for r, name in rows], 'total': total}


@router.get('/local-datasets')
async def local_datasets(user=Depends(get_current_user)):
    """Inventory only: local files are not asserted to be verified market observations."""
    from pathlib import Path
    workspace = Path(__file__).resolve().parents[5]
    candidates = []
    for relative in ['Projects/Mizan-Desktop/Data real estate',
                     'Projects/Mizan-Desktop/data/raw',
                     'Projects/Mizan-Antigravity/data/raw',
                     'Related-Materials-To-Review']:
        folder = workspace / relative
        if folder.is_dir():
            for path in sorted(folder.iterdir()):
                if path.is_file() and path.suffix.lower() in {'.csv', '.xlsx'}:
                    candidates.append({'name': path.name, 'path': str(path.relative_to(workspace)),
                        'bytes': path.stat().st_size, 'status': 'unverified_not_imported'})
    return candidates
