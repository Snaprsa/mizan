"""Pick location → property type → method → sourced inputs → reproducible calculation."""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.app.database import get_db
from api.app.auth import get_current_user
from api.app.audit import log_action
from api.app.models import Case, ValuationRun
from api.app.models.foundation import Property, PropertyAssumption
from api.app.schemas.foundation import PropertyInput
from api.app.schemas.analysis import StartAnalysis, SaveAnalysis, RunAnalysis, SaveAdjustments
from api.app.services.foundation import (owner_id, can_write, owned_property, search_columns,
    save_snapshot, advance_revision, assumptions)
from api.app.services.valuation_catalog import catalog, PROPERTY_TYPES
from api.app.services.analysis_workflow import method_config, saudi_today, prepare, validate_input
from api.app.services.valuation_calculations import calculate

router = APIRouter(prefix='/analysis', tags=['Map-first valuation'])


@router.get('/catalog')
async def method_catalog(user=Depends(get_current_user)):
    return {'methods': catalog(), 'property_types': PROPERTY_TYPES}


@router.post('/start', status_code=201)
async def start(body: StartAnalysis, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    can_write(user)
    method_config(body.method)
    if body.property_type not in PROPERTY_TYPES:
        raise HTTPException(422, 'Unsupported property type')
    today = saudi_today()
    name = body.name or f"{body.property_type.replace('_', ' ').title()} · {body.latitude:.5f}, {body.longitude:.5f}"
    case = Case(title=name, created_by=owner_id(user), status='draft')
    db.add(case); await db.flush()
    data = PropertyInput(name=name, case_id=case.id, property_type=body.property_type,
        location={'latitude': body.latitude, 'longitude': body.longitude, 'city': body.city, 'district': body.district,
                  'coordinate_source': body.coordinate_source, 'coordinate_precision': body.coordinate_precision},
        provenance={'source': 'User-selected map location', 'collected_on': today},
        analysis={'method': body.method, 'as_of': today}).model_dump(mode='json')
    p = Property(data=data, created_by=owner_id(user), **search_columns(data))
    db.add(p); await db.flush()
    await save_snapshot(db, p, 'Started from map: location, property type and valuation method', user)
    await log_action(db, 'property', p.id, 'analysis_started', user['id'], {'method': body.method, 'case_id': str(case.id)})
    return await prepare(db, p, user)


@router.get('/{property_id}')
async def get_prepared(property_id: uuid.UUID, method: str | None = None,
        db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return await prepare(db, await owned_property(db, property_id, user), user, method)


@router.put('/{property_id}/inputs')
async def save_inputs(property_id: uuid.UUID, body: SaveAnalysis,
        db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    can_write(user)
    config = method_config(body.method)
    definitions = {f['key']: f for f in config['fields']}
    if body.inputs.keys()-definitions.keys():
        raise HTTPException(422, 'Unexpected input fields for the selected approach')
    for key, item in body.inputs.items():
        error = validate_input(definitions[key], item.value)
        if error: raise HTTPException(422, f'{definitions[key]["label"]}: {error}')
        if item.as_of > body.as_of:
            raise HTTPException(422, 'Input source dates cannot be after the valuation date')
    p = await owned_property(db, property_id, user)
    # Keep other analysis settings (e.g. reviewed comparable adjustments) when saving method inputs.
    data = {**p.data, 'analysis': {**(p.data.get('analysis') or {}), 'method': body.method, 'as_of': body.as_of.isoformat(),
             'radius_km': body.radius_km, 'lookback_days': body.lookback_days}}
    changes = {'data': data}
    if p.case_id is None:
        case = Case(title=p.name, created_by=owner_id(user), status='draft')
        db.add(case); await db.flush()
        data['case_id'] = str(case.id)
        changes['case_id'] = case.id
    await advance_revision(db, p, body.expected_revision, changes)
    for key, definition in definitions.items():
        assumption_key = f'valuation_{body.method}_{key}'
        row = await db.scalar(select(PropertyAssumption).where(PropertyAssumption.property_id == p.id,
                                                               PropertyAssumption.key == assumption_key))
        if key not in body.inputs:
            if row is not None: await db.delete(row)
            continue
        item = body.inputs[key]
        if row is None:
            row = PropertyAssumption(property_id=p.id, key=assumption_key)
            db.add(row)
        row.data = {'name': definition['label'], 'value': item.value, 'unit': definition['unit'],
            'category': 'valuation:'+body.method, 'source': item.source, 'as_of': item.as_of.isoformat(),
            'status': item.status, 'user_override': None, 'notes': item.notes or 'Saved from map workflow; provenance is recorded in the source field'}
    await save_snapshot(db, p, 'Saved '+config['label']+' inputs from map workspace', user)
    await log_action(db, 'property', p.id, 'valuation_inputs_saved', user['id'], {'method': body.method, 'revision': p.revision})
    return await prepare(db, p, user)


@router.put('/{property_id}/adjustments')
async def save_adjustments(property_id: uuid.UUID, body: SaveAdjustments,
        db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """Persist the reviewed sales-comparison adjustment grid as a new property revision."""
    can_write(user)
    p = await owned_property(db, property_id, user)
    setup = body.adjustments.model_dump(mode='json')
    data = {**p.data, 'analysis': {**(p.data.get('analysis') or {}), 'adjustments': setup}}
    await advance_revision(db, p, body.expected_revision, {'data': data})
    await save_snapshot(db, p, 'Comparable adjustments: '+body.reason, user)
    await log_action(db, 'property', p.id, 'comparable_adjustments_saved', user['id'],
                     {'revision': p.revision, 'lines': len(setup['lines']), 'excluded': len(setup['exclusions'])})
    return await prepare(db, p, user)


@router.post('/{property_id}/runs', status_code=201)
async def run(property_id: uuid.UUID, body: RunAnalysis,
        db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    can_write(user)
    p = await owned_property(db, property_id, user)
    if p.revision != body.expected_revision:
        raise HTTPException(409, 'Inputs changed. Reload before calculating.')
    prepared = await prepare(db, p, user)
    if not prepared['ready']:
        raise HTTPException(409, {'message': 'Required evidence / inputs are missing', 'gaps': prepared['gaps']})
    # A run only uses reviewed persisted assumptions; market suggestions must first be saved.
    stored = await assumptions(db, p)
    if any(f'valuation_{prepared["method"]}_{f["key"]}' not in stored for f in prepared['fields']):
        raise HTTPException(409, 'Save and review the prepared inputs before calculating')
    values = {f['key']: f['value'] for f in prepared['fields']}
    try:
        outputs = calculate(prepared['method'], values, prepared['eligible_comparables'],
                            adjustments=prepared.get('adjustment_setup'), as_of=prepared['as_of'])
    except (ValueError, OverflowError) as exc:
        raise HTTPException(422, str(exc)) from exc
    snapshot = {'schema_version': 'mizan.valuation-run.v1', 'property_id': str(p.id), 'property_revision': p.revision,
        'property': p.data, 'assumptions': stored, 'method': prepared['method'], 'data_date': prepared['as_of'],
        'inputs': prepared['fields'], 'comparables': prepared['eligible_comparables'],
        'adjustment_setup': prepared.get('adjustment_setup'),
        'calculation_version': outputs['calculation_version'], 'model_version': None, 'outputs': outputs}
    result = ValuationRun(case_id=p.case_id, subject_id=p.id, status='completed', data=snapshot)
    if p.case_id is None:
        case = Case(title=p.name, created_by=owner_id(user), status='draft')
        db.add(case); await db.flush()
        result.case_id = case.id
    db.add(result); await db.flush()
    await log_action(db, 'valuation_run', result.id, 'calculated', user['id'], {'property_id': str(p.id), 'revision': p.revision})
    return {'id': str(result.id), 'created_at': result.created_at, **snapshot}


@router.get('/{property_id}/runs')
async def list_runs(property_id: uuid.UUID, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    await owned_property(db, property_id, user)
    rows = (await db.scalars(select(ValuationRun).where(ValuationRun.subject_id == property_id)
                            .order_by(ValuationRun.created_at.desc()))).all()
    return [{'id': r.id, 'created_at': r.created_at, 'data': r.data} for r in rows]
