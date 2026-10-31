"""Mizan Monitor: what is the portfolio worth now, what changed, why, how sure are we, what needs attention."""
import uuid
from datetime import date, datetime
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from api.app.audit import log_action
from api.app.auth import get_current_user
from api.app.database import get_db
from api.app.models import AuditLog
from api.app.models.foundation import Property, PropertyAssumption
from api.app.models.monitor import MonitorAlert, MonitorEvent, Portfolio, PortfolioAsset, ValuationSnapshot
from api.app.schemas.foundation import StrictModel
from api.app.services.analysis_workflow import saudi_today, validate_input
from api.app.services.foundation import advance_revision, can_write, owned_property, owner_id, save_snapshot
from api.app.services.monitor import (FREQUENCY_DAYS, USER_EVENTS, assess, history, latest_snapshot, portfolio_rows, refresh, scan, settings_of, share, totals)
from api.app.services.monitor_calc import (DEFAULT_SETTINGS, METHOD_LABELS, SEVERITY_RANK, STRESSES, attribute, stressed_value)
from api.app.services.monitor_demo import create_demo_portfolio, remove_demo_portfolio
from api.app.services.valuation_catalog import METHODS

router = APIRouter(prefix='/monitor', tags=['Mizan Monitor'])
Frequency = Literal['event_driven', 'daily', 'weekly', 'monthly', 'quarterly']


class PortfolioIn(StrictModel):
    name: str = Field(min_length=1, max_length=255)
    owner_entity: str | None = Field(None, max_length=255)
    fund: str | None = Field(None, max_length=255)
    asset_manager: str | None = Field(None, max_length=255)
    official_nav_sar: float | None = Field(None, ge=0)


class PortfolioPatch(StrictModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    owner_entity: str | None = None
    fund: str | None = None
    asset_manager: str | None = None
    official_nav_sar: float | None = Field(None, ge=0)
    settings: dict[str, float] | None = None


class AddAssets(StrictModel):
    property_ids: list[uuid.UUID] = Field(min_length=1, max_length=2000)


class AssetPatch(StrictModel):
    ownership_pct: float | None = Field(None, gt=0, le=100)
    acquisition_cost_sar: float | None = Field(None, ge=0)
    acquisition_date: date | None = None
    book_value_sar: float | None = Field(None, ge=0)
    debt_sar: float | None = Field(None, ge=0)
    monitoring_frequency: Frequency | None = None
    formal_frequency: Frequency | None = None
    next_formal_on: date | None = None
    noi_sar_year: float | None = None
    occupancy_pct: float | None = Field(None, ge=0, le=100)
    wault_years: float | None = Field(None, ge=0)
    method_weights: dict[str, float] | None = None


class OfficialIn(StrictModel):
    value_sar: float = Field(gt=0)
    valued_on: date
    valuer: str = Field(min_length=1, max_length=255)
    note: str | None = Field(None, max_length=1000)


class OverrideIn(StrictModel):
    field: str = Field(min_length=1, max_length=60)
    value: float | None = None  # None removes the override and returns to the reviewed value.
    reason: str = Field(min_length=3, max_length=500)


class EventIn(StrictModel):
    event_type: str
    occurred_on: date
    summary: str = Field(min_length=3, max_length=1000)


class AlertPatch(StrictModel):
    status: Literal['open', 'investigating', 'accepted', 'resolved']
    note: str | None = Field(None, max_length=1000)


class FormalRequest(StrictModel):
    reason: str = Field(min_length=3, max_length=500)


async def owned_portfolio(db, portfolio_id, user):
    p = await db.scalar(select(Portfolio).where(Portfolio.id == portfolio_id, Portfolio.created_by == owner_id(user)))
    if p is None:
        raise HTTPException(404, 'Portfolio not found')
    return p


async def owned_asset(db, asset_id, user):
    row = (await db.execute(select(PortfolioAsset, Property, Portfolio).join(Property, Property.id == PortfolioAsset.property_id)
        .join(Portfolio, Portfolio.id == PortfolioAsset.portfolio_id)
        .where(PortfolioAsset.id == asset_id, Portfolio.created_by == owner_id(user)))).first()
    if row is None:
        raise HTTPException(404, 'Asset not found')
    return row


def asset_row(asset, prop):
    s = asset.summary or {}
    return {'id': str(asset.id), 'property_id': str(prop.id), 'name': prop.name, 'city': prop.city, 'district': prop.district, 'property_type': prop.property_type,
        'ownership_pct': asset.ownership_pct, 'debt_sar': asset.debt_sar, 'is_demo': prop.is_demo, 'value': s.get('value'), 'low': s.get('low'), 'high': s.get('high'),
        'valued_on': s.get('valued_on'), 'origin': s.get('origin'), 'official_value': s.get('official_value'), 'official_on': s.get('official_on'),
        'change_vs_official_pct': s.get('change_vs_official_pct'), 'change_pct': s.get('change_pct'), 'confidence': s.get('confidence'), 'divergence_pct': s.get('divergence_pct'),
        'ltv_pct': s.get('ltv_pct'), 'occupancy_pct': s.get('occupancy_pct'), 'cap_rate_pct': s.get('cap_rate_pct'), 'noi': s.get('noi'), 'official_age_months': s.get('official_age_months'),
        'priority': s.get('priority') or {'score': 0, 'band': 'low', 'reasons': []}, 'next_formal_on': asset.next_formal_on, 'formal_requested_at': asset.formal_requested_at}


def alert_row(a, names=None):
    return {'id': str(a.id), 'asset_id': str(a.asset_id) if a.asset_id else None, 'asset_name': (names or {}).get(a.asset_id), 'kind': a.kind, 'severity': a.severity,
            'status': a.status, 'title': a.title, 'message': a.message, 'raised_on': a.raised_on, 'updated_at': a.updated_at, 'note': a.note}


def snapshot_row(s):
    return {'id': str(s.id), 'kind': s.kind, 'valued_on': s.valued_on, 'value': s.value_sar, 'low': s.low_sar, 'high': s.high_sar,
            'confidence': s.confidence, 'trigger': s.trigger, 'origin': s.origin, 'created_at': s.created_at}


@router.get('/portfolios')
async def list_portfolios(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    rows = (await db.scalars(select(Portfolio).where(Portfolio.created_by == owner_id(user)).order_by(Portfolio.is_demo, Portfolio.created_at))).all()
    out = []
    for p in rows:
        t = totals(await portfolio_rows(db, p), settings_of(p))
        out.append({'id': str(p.id), 'name': p.name, 'is_demo': p.is_demo, 'asset_count': t['asset_count'], 'value': t['value'], 'change_pct': t['change_pct']})
    return out


@router.post('/portfolios', status_code=201)
async def create_portfolio(body: PortfolioIn, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    can_write(user)
    p = Portfolio(created_by=owner_id(user), settings=dict(DEFAULT_SETTINGS), **body.model_dump())
    db.add(p); await db.flush()
    await log_action(db, 'portfolio', p.id, 'created', user['id'], {'name': p.name})
    return {'id': str(p.id), 'name': p.name}


@router.post('/demo', status_code=201)
async def add_demo(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    can_write(user)
    p = await create_demo_portfolio(db, user)
    if p is None:
        raise HTTPException(409, 'The demo portfolio already exists')
    await log_action(db, 'portfolio', p.id, 'demo_portfolio_created', user['id'], {})
    return {'id': str(p.id), 'name': p.name}


@router.delete('/demo')
async def delete_demo(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    can_write(user)
    removed = await remove_demo_portfolio(db, user)
    await log_action(db, 'portfolio', uuid.uuid4(), 'demo_portfolio_removed', user['id'], removed)
    return removed


@router.get('/portfolios/{portfolio_id}')
async def dashboard(portfolio_id: uuid.UUID, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    p = await owned_portfolio(db, portfolio_id, user)
    settings = settings_of(p)
    rows = await portfolio_rows(db, p)
    t = totals(rows, settings)
    alerts = (await db.scalars(select(MonitorAlert).where(MonitorAlert.portfolio_id == p.id, MonitorAlert.status.in_(['open', 'investigating'])))).all()
    names = {a.id: prop.name for a, prop in rows}
    serious = {a.asset_id for a in alerts if a.asset_id and SEVERITY_RANK[a.severity] >= SEVERITY_RANK['warning']}
    by_asset = {}
    for a in alerts:
        if a.asset_id and (a.asset_id not in by_asset or SEVERITY_RANK[a.severity] > SEVERITY_RANK[by_asset[a.asset_id].severity]):
            by_asset[a.asset_id] = a
    attention = sorted(((asset, prop) for asset, prop in rows if asset.id in serious), key=lambda r: (-SEVERITY_RANK[by_asset[r[0].id].severity], -r[0].priority_score))
    ranked = sorted(alerts, key=lambda a: (-SEVERITY_RANK[a.severity], a.raised_on), )
    priority = sorted(rows, key=lambda r: -r[0].priority_score)
    return {'id': str(p.id), 'name': p.name, 'owner_entity': p.owner_entity, 'fund': p.fund, 'asset_manager': p.asset_manager, 'is_demo': p.is_demo,
        'official_nav_sar': p.official_nav_sar, 'settings': settings, 'last_checked_at': p.last_checked_at, 'totals': t,
        'attention': [{**asset_row(a, prop), 'top_alert': alert_row(by_asset[a.id])} for a, prop in attention[:50]], 'attention_count': len(attention),
        'alerts': [alert_row(a, names) for a in ranked[:100]], 'alert_counts': {s: sum(a.severity == s for a in alerts) for s in SEVERITY_RANK},
        'priority': [asset_row(a, prop) for a, prop in priority if (a.summary or {}).get('priority', {}).get('band') != 'low'][:25],
        'history': await history(db, p, rows), 'as_of': saudi_today()}


@router.patch('/portfolios/{portfolio_id}')
async def patch_portfolio(portfolio_id: uuid.UUID, body: PortfolioPatch, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    can_write(user)
    p = await owned_portfolio(db, portfolio_id, user)
    changes = body.model_dump(exclude_unset=True)
    if 'settings' in changes:
        unknown = set(changes['settings'])-set(DEFAULT_SETTINGS)
        if unknown:
            raise HTTPException(422, 'Unknown thresholds: '+', '.join(sorted(unknown)))
        changes['settings'] = {**settings_of(p), **changes['settings']}
    for key, value in changes.items():
        setattr(p, key, value)
    p.updated_at = datetime.utcnow()
    await refresh(db, p)
    await log_action(db, 'portfolio', p.id, 'updated', user['id'], {k: str(v) for k, v in changes.items()})
    return {'id': str(p.id)}


@router.delete('/portfolios/{portfolio_id}')
async def delete_portfolio(portfolio_id: uuid.UUID, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """Removes the grouping and its alerts. Properties, snapshots and their history stay."""
    can_write(user)
    p = await owned_portfolio(db, portfolio_id, user)
    if p.is_demo:
        raise HTTPException(409, 'Use Remove demo portfolio')
    for alert in await db.scalars(select(MonitorAlert).where(MonitorAlert.portfolio_id == p.id)):
        await db.delete(alert)
    for asset in await db.scalars(select(PortfolioAsset).where(PortfolioAsset.portfolio_id == p.id)):
        await db.delete(asset)
    await db.flush()
    await db.delete(p)
    await log_action(db, 'portfolio', portfolio_id, 'deleted', user['id'], {'name': p.name})
    return {'deleted': True}


@router.post('/portfolios/{portfolio_id}/assets', status_code=201)
async def add_assets(portfolio_id: uuid.UUID, body: AddAssets, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    can_write(user)
    p = await owned_portfolio(db, portfolio_id, user)
    existing = set(await db.scalars(select(PortfolioAsset.property_id).where(PortfolioAsset.portfolio_id == p.id)))
    added = 0
    for property_id in dict.fromkeys(body.property_ids):
        prop = await owned_property(db, property_id, user)
        if prop.is_demo:
            raise HTTPException(422, 'Demo properties cannot join a real portfolio')
        if property_id in existing:
            continue
        asset = PortfolioAsset(portfolio_id=p.id, property_id=property_id, facts={}, summary={})
        db.add(asset); await db.flush()
        await assess(db, asset, prop, user, settings_of(p))
        added += 1
    await refresh(db, p)
    await log_action(db, 'portfolio', p.id, 'assets_added', user['id'], {'added': added})
    return {'added': added, 'already_in_portfolio': len(set(body.property_ids))-added}


@router.get('/portfolios/{portfolio_id}/assets')
async def list_assets(portfolio_id: uuid.UUID, q: str = Query('', max_length=255), city: str | None = None, property_type: str | None = None,
        confidence: str | None = None, movement: Literal['up', 'stable', 'down'] | None = None, attention: bool = False,
        sort: Literal['priority', 'value', 'change', 'confidence', 'ltv', 'occupancy', 'cap_rate', 'age', 'name'] = 'priority', limit: int = Query(100, ge=1, le=20000), offset: int = Query(0, ge=0),
        db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    p = await owned_portfolio(db, portfolio_id, user)
    settings = settings_of(p)
    rows = await portfolio_rows(db, p)
    band = settings['stable_band_pct']
    serious = set()
    if attention:
        serious = set(await db.scalars(select(MonitorAlert.asset_id).where(MonitorAlert.portfolio_id == p.id, MonitorAlert.status.in_(['open', 'investigating']), MonitorAlert.severity.in_(['warning', 'critical']))))
    def keep(asset, prop):
        s = asset.summary or {}
        move = s.get('change_vs_official_pct')
        return ((not q or q.casefold() in prop.name.casefold()) and (not city or prop.city == city) and (not property_type or prop.property_type == property_type)
                and (not confidence or s.get('confidence') == confidence) and (not attention or asset.id in serious)
                and (not movement or (move is not None and ('up' if move > band else 'down' if move < -band else 'stable') == movement)))
    chosen = [r for r in rows if keep(*r)]
    order = {'high': 0, 'medium': 1, 'low': 2}
    keys = {'priority': lambda a, _: -a.priority_score, 'value': lambda a, _: -((a.summary or {}).get('value') or 0),
        'change': lambda a, _: (a.summary or {}).get('change_vs_official_pct') if (a.summary or {}).get('change_vs_official_pct') is not None else 1e9,
        'confidence': lambda a, _: order.get((a.summary or {}).get('confidence'), 3), 'ltv': lambda a, _: -((a.summary or {}).get('ltv_pct') or 0),
        'occupancy': lambda a, _: (a.summary or {}).get('occupancy_pct') if (a.summary or {}).get('occupancy_pct') is not None else 1e9,
        'cap_rate': lambda a, _: -((a.summary or {}).get('cap_rate_pct') or 0), 'age': lambda a, _: -((a.summary or {}).get('official_age_months') or 0), 'name': lambda _, x: x.name}
    chosen.sort(key=lambda r: keys[sort](*r))
    return {'data': [asset_row(a, prop) for a, prop in chosen[offset:offset+limit]], 'total': len(chosen),
            'facets': {'cities': sorted({x.city for _, x in rows if x.city}), 'types': sorted({x.property_type for _, x in rows if x.property_type})}}


@router.post('/portfolios/{portfolio_id}/check')
async def check(portfolio_id: uuid.UUID, only_due: bool = False, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    can_write(user)
    p = await owned_portfolio(db, portfolio_id, user)
    result = await scan(db, p, user, only_due=only_due)
    await log_action(db, 'portfolio', p.id, 'monitor_checked', user['id'], result)
    return result


@router.get('/portfolios/{portfolio_id}/stress')
async def stress(portfolio_id: uuid.UUID, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """Mechanical what-ifs through the same engine, on each asset's latest inputs. Nothing is saved."""
    p = await owned_portfolio(db, portfolio_id, user)
    rows = await portfolio_rows(db, p)
    latest = {}
    for asset, prop in rows:
        s = await latest_snapshot(db, prop.id, 'indicative')
        if s is not None: latest[asset.id] = s
    base = sum(s.value_sar*share(a) for a, _ in rows if (s := latest.get(a.id)))
    debt = sum((a.debt_sar or 0)*share(a) for a, _ in rows if a.id in latest)
    out = []
    for key, definition in STRESSES.items():
        total, affected, details = 0.0, 0, []
        for asset, prop in rows:
            s = latest.get(asset.id)
            if s is None: continue
            value, changed = stressed_value(s.data['methods'], asset.method_weights, definition)
            total += (value if value is not None else s.value_sar)*share(asset)
            if changed and value is not None and s.value_sar:
                affected += 1
                details.append({'id': str(asset.id), 'name': prop.name, 'before': s.value_sar, 'after': value, 'change_pct': (value-s.value_sar)/s.value_sar*100,
                                'ltv_after': (asset.debt_sar or 0)/value*100 if asset.debt_sar and value > 0 else None})
        details.sort(key=lambda d: d['change_pct'])
        out.append({'key': key, 'label': definition['label'], 'value': total, 'change': total-base, 'change_pct': (total-base)/base*100 if base else None,
                    'ltv_pct': debt/total*100 if debt and total > 0 else None, 'affected': affected, 'unaffected': len(latest)-affected, 'worst': details[:5]})
    return {'base_value': base, 'base_ltv_pct': debt/base*100 if debt and base else None, 'asset_count': len(latest), 'scenarios': out,
            'notice': 'Mechanical stresses on saved inputs, not forecasts. Only methods that use the stressed input move; the debt balance is held. Interest rates are not modelled directly because debt terms are not stored.'}


@router.get('/assets/{asset_id}')
async def asset_detail(asset_id: uuid.UUID, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    asset, prop, portfolio = await owned_asset(db, asset_id, user)
    snaps = (await db.scalars(select(ValuationSnapshot).where(ValuationSnapshot.property_id == prop.id).order_by(ValuationSnapshot.valued_on, ValuationSnapshot.created_at))).all()
    indicative = [s for s in snaps if s.kind == 'indicative']
    officials = [s for s in snaps if s.kind == 'official']
    current = indicative[-1] if indicative else None
    since_previous = (current.data.get('attribution') if current else None)
    since_official = baseline = None
    if current and officials:
        official = officials[-1]
        before = [s for s in indicative if s.valued_on <= official.valued_on]
        if before and before[-1].id != current.id:
            baseline = before[-1]
            since_official = attribute(baseline.data['methods'], current.data['methods'], baseline.value_sar, current.value_sar,
                                       (baseline.data.get('reconciliation') or {}).get('input_weights'), asset.method_weights)
            since_official.update(from_date=baseline.valued_on, model_value_at_official=baseline.value_sar, official_value=official.value_sar, official_on=official.valued_on,
                                  gap_at_official=baseline.value_sar-official.value_sar)
    data = current.data if current else {}
    methods = data.get('methods') or {}
    comps = (methods.get('sales_comparison') or {}).get('comparables') or []
    old_comps = {c.get('id') for c in ((baseline.data.get('methods') or {}).get('sales_comparison') or {}).get('comparables') or []} if baseline else set()
    implied = current.value_sar/methods['sales_comparison']['inputs']['area_sqm'] if current and methods.get('sales_comparison') else None
    alerts = (await db.scalars(select(MonitorAlert).where(MonitorAlert.asset_id == asset.id).order_by(MonitorAlert.updated_at.desc()))).all()
    events = (await db.scalars(select(MonitorEvent).where(MonitorEvent.property_id == prop.id).order_by(MonitorEvent.occurred_on.desc(), MonitorEvent.created_at.desc()).limit(40))).all()
    return {**asset_row(asset, prop), 'portfolio': {'id': str(portfolio.id), 'name': portfolio.name, 'is_demo': portfolio.is_demo}, 'summary': asset.summary, 'facts': asset.facts,
        'acquisition_cost_sar': asset.acquisition_cost_sar, 'book_value_sar': asset.book_value_sar, 'acquisition_date': asset.acquisition_date,
        'monitoring_frequency': asset.monitoring_frequency, 'formal_frequency': asset.formal_frequency, 'last_checked_at': asset.last_checked_at, 'method_weights': asset.method_weights,
        'history': [snapshot_row(s) for s in snaps], 'methods': [{'key': m, 'label': METHOD_LABELS[m], 'value': s['value'], 'weight': ((data.get('reconciliation') or {}).get('weights') or {}).get(m),
            'limitations': s.get('limitations'), 'inputs': s.get('meta')} for m, s in methods.items()],
        'reconciliation': data.get('reconciliation'), 'confidence_detail': data.get('confidence'), 'divergence': data.get('divergence'), 'attribution': since_previous, 'attribution_since_official': since_official,
        'changes': data.get('changes') or [], 'gaps': data.get('gaps') or (asset.summary or {}).get('gaps') or [],
        'evidence': sorted([{'id': c.get('id'), 'title': c.get('title'), 'date': c.get('date'), 'price_per_sqm': c.get('price_per_sqm'), 'area_sqm': c.get('area_sqm'), 'distance_km': c.get('distance_km'),
            'is_new': bool(baseline) and c.get('id') not in old_comps, 'vs_implied_pct': (c['price_per_sqm']-implied)/implied*100 if implied and c.get('price_per_sqm') else None,
            'origin': 'demo' if (c.get('attributes') or {}).get('is_demo') else 'real'} for c in comps], key=lambda c: c['date'] or '', reverse=True),
        'alerts': [alert_row(a) for a in alerts], 'events': [{'id': str(e.id), 'type': e.event_type, 'category': e.category, 'occurred_on': e.occurred_on, 'summary': e.summary, 'origin': e.origin} for e in events]}


@router.patch('/assets/{asset_id}')
async def patch_asset(asset_id: uuid.UUID, body: AssetPatch, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    can_write(user)
    asset, prop, portfolio = await owned_asset(db, asset_id, user)
    changes = body.model_dump(exclude_unset=True)
    facts = {**(asset.facts or {})}
    for key in ['noi_sar_year', 'occupancy_pct', 'wault_years']:
        if key in changes:
            facts[key] = changes.pop(key)
    asset.facts = facts
    weights = changes.get('method_weights')
    if weights is not None and (set(weights)-set(METHOD_LABELS) or any(w < 0 for w in weights.values())):
        raise HTTPException(422, 'Weights must be non-negative and name known methods')
    for key, value in changes.items():
        setattr(asset, key, value)
    if 'method_weights' in changes:
        await assess(db, asset, prop, user, settings_of(portfolio), trigger='weights_changed')
    await refresh(db, portfolio)
    await log_action(db, 'portfolio_asset', asset.id, 'updated', user['id'], {k: str(v) for k, v in body.model_dump(exclude_unset=True).items()})
    return await asset_detail(asset_id, db, user)


@router.delete('/assets/{asset_id}')
async def remove_asset(asset_id: uuid.UUID, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """Takes the asset out of this portfolio. Its property and valuation history stay."""
    can_write(user)
    asset, prop, portfolio = await owned_asset(db, asset_id, user)
    for alert in await db.scalars(select(MonitorAlert).where(MonitorAlert.asset_id == asset.id)):
        await db.delete(alert)
    await db.flush()
    await db.delete(asset)
    await db.flush()
    await refresh(db, portfolio)
    await log_action(db, 'portfolio', portfolio.id, 'asset_removed', user['id'], {'property_id': str(prop.id)})
    return {'removed': True}


@router.post('/assets/{asset_id}/official', status_code=201)
async def add_official(asset_id: uuid.UUID, body: OfficialIn, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    can_write(user)
    asset, prop, portfolio = await owned_asset(db, asset_id, user)
    if body.valued_on > saudi_today():
        raise HTTPException(422, 'The valuation date cannot be in the future')
    origin = 'demo' if prop.is_demo else 'user_provided'
    s = ValuationSnapshot(property_id=prop.id, kind='official', valued_on=body.valued_on, value_sar=body.value_sar, trigger='official_valuation', origin=origin,
        created_by=owner_id(user), data={'schema_version': 'mizan.monitor-official.v1', 'valuer': body.valuer, 'note': body.note})
    db.add(s); await db.flush()
    db.add(MonitorEvent(property_id=prop.id, event_type='official_valuation', category='property', occurred_on=body.valued_on, origin=origin, snapshot_id=s.id, created_by=owner_id(user),
        summary=f'Official valuation recorded: SAR {body.value_sar:,.0f} by {body.valuer}'))
    asset.formal_requested_at = None
    await assess(db, asset, prop, user, settings_of(portfolio))
    await refresh(db, portfolio)
    await log_action(db, 'portfolio_asset', asset.id, 'official_valuation_recorded', user['id'], {'value': body.value_sar, 'valued_on': body.valued_on.isoformat(), 'valuer': body.valuer})
    return await asset_detail(asset_id, db, user)


@router.post('/assets/{asset_id}/revalue')
async def revalue(asset_id: uuid.UUID, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    can_write(user)
    asset, prop, portfolio = await owned_asset(db, asset_id, user)
    made = await assess(db, asset, prop, user, settings_of(portfolio))
    await refresh(db, portfolio)
    await log_action(db, 'portfolio_asset', asset.id, 'checked', user['id'], {'new_snapshot': bool(made)})
    return {'changed': bool(made), 'asset': await asset_detail(asset_id, db, user)}


@router.post('/assets/{asset_id}/override')
async def override(asset_id: uuid.UUID, body: OverrideIn, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """A reasoned change to a saved assumption. The reviewed value is kept; who, when and why stay in the trail."""
    can_write(user)
    asset, prop, portfolio = await owned_asset(db, asset_id, user)
    rows = [r for r in await db.scalars(select(PropertyAssumption).where(PropertyAssumption.property_id == prop.id))
            if r.key.startswith('valuation_') and r.key.endswith('_'+body.field) and r.key.removeprefix('valuation_').removesuffix('_'+body.field) in METHOD_LABELS]
    if not rows:
        raise HTTPException(404, 'This asset has no saved input with that name')
    changed = []
    for row in rows:
        method = row.key.removeprefix('valuation_').removesuffix('_'+body.field)
        definition = next(f for f in METHODS[method]['fields'] if f['key'] == body.field)
        if body.value is not None:
            error = validate_input(definition, body.value)
            if error:
                raise HTTPException(422, f"{definition['label']}: {error}")
        before = row.data['user_override'] if row.data['user_override'] is not None else row.data['value']
        row.data = {**row.data, 'user_override': body.value, 'notes': body.reason}
        changed.append({'method': method, 'label': definition['label'], 'before': before, 'after': body.value if body.value is not None else row.data['value']})
    await advance_revision(db, prop, prop.revision)
    await save_snapshot(db, prop, 'Monitor override: '+body.reason, user)
    made = await assess(db, asset, prop, user, settings_of(portfolio), trigger='user_override')
    await refresh(db, portfolio)
    await log_action(db, 'portfolio_asset', asset.id, 'assumption_overridden', user['id'], {'field': body.field, 'changes': changed, 'reason': body.reason, 'snapshot': str(made.id) if made else None})
    return await asset_detail(asset_id, db, user)


@router.post('/assets/{asset_id}/events', status_code=201)
async def add_event(asset_id: uuid.UUID, body: EventIn, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    can_write(user)
    asset, prop, _ = await owned_asset(db, asset_id, user)
    if body.event_type not in USER_EVENTS:
        raise HTTPException(422, 'Unknown event type')
    e = MonitorEvent(property_id=prop.id, event_type=body.event_type, category=USER_EVENTS[body.event_type], occurred_on=body.occurred_on, summary=body.summary,
                     origin='demo' if prop.is_demo else 'user_provided', created_by=owner_id(user))
    db.add(e); await db.flush()
    await log_action(db, 'portfolio_asset', asset.id, 'event_recorded', user['id'], {'type': body.event_type})
    return {'id': str(e.id)}


@router.post('/assets/{asset_id}/formal-request')
async def request_formal(asset_id: uuid.UUID, body: FormalRequest, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    can_write(user)
    asset, prop, _ = await owned_asset(db, asset_id, user)
    asset.formal_requested_at = datetime.utcnow()
    db.add(MonitorEvent(property_id=prop.id, event_type='formal_valuation_requested', category='property', occurred_on=saudi_today(), summary='Formal valuation recommended: '+body.reason,
                        origin='demo' if prop.is_demo else 'user_provided', created_by=owner_id(user)))
    await log_action(db, 'portfolio_asset', asset.id, 'formal_valuation_requested', user['id'], {'reason': body.reason})
    return await asset_detail(asset_id, db, user)


@router.get('/assets/{asset_id}/audit')
async def audit(asset_id: uuid.UUID, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """Why did Mizan change this value? Valuations, what triggered them, and every human action, newest first."""
    asset, prop, _ = await owned_asset(db, asset_id, user)
    entries = []
    previous = {}
    snaps = (await db.scalars(select(ValuationSnapshot).where(ValuationSnapshot.property_id == prop.id).order_by(ValuationSnapshot.valued_on, ValuationSnapshot.created_at))).all()
    for s in snaps:
        before = previous.get(s.kind)
        previous[s.kind] = s
        entries.append({'at': s.created_at, 'on': s.valued_on, 'kind': 'official' if s.kind == 'official' else 'valuation', 'snapshot_id': str(s.id), 'before': before.value_sar if before else None, 'after': s.value_sar,
            'text': (f"Official valuation by {s.data.get('valuer')}" if s.kind == 'official' else 'Reconciled value '+('recorded' if before is None else 'updated')), 'trigger': s.trigger,
            'model': s.data.get('model_version'), 'calculation_version': s.data.get('calculation_version'), 'origin': s.origin})
    events = (await db.scalars(select(MonitorEvent).where(MonitorEvent.property_id == prop.id).order_by(MonitorEvent.created_at.desc()).limit(500))).all()
    entries += [{'at': e.created_at, 'on': e.occurred_on, 'kind': 'event', 'text': e.summary, 'trigger': e.event_type, 'origin': e.origin} for e in events]
    logs = (await db.scalars(select(AuditLog).where(or_(AuditLog.entity_id == asset.id, AuditLog.entity_id == prop.id)).order_by(AuditLog.timestamp.desc()).limit(200))).all()
    entries += [{'at': l.timestamp, 'on': l.timestamp.date(), 'kind': 'action', 'text': l.action.replace('_', ' ').capitalize(), 'details': l.details, 'user_id': str(l.user_id) if l.user_id else None, 'origin': 'user'} for l in logs]
    entries.sort(key=lambda e: (e['on'], e['at']), reverse=True)
    return {'entries': entries[:500]}


@router.get('/snapshots/{snapshot_id}')
async def snapshot_detail(snapshot_id: uuid.UUID, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    s = await db.get(ValuationSnapshot, snapshot_id)
    if s is None:
        raise HTTPException(404, 'Snapshot not found')
    await owned_property(db, s.property_id, user)
    return {**snapshot_row(s), 'data': s.data}


@router.patch('/alerts/{alert_id}')
async def patch_alert(alert_id: uuid.UUID, body: AlertPatch, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    can_write(user)
    alert = await db.get(MonitorAlert, alert_id)
    if alert is None:
        raise HTTPException(404, 'Alert not found')
    await owned_portfolio(db, alert.portfolio_id, user)
    before = alert.status
    alert.status, alert.note, alert.updated_at = body.status, body.note, datetime.utcnow()
    await log_action(db, 'portfolio_asset' if alert.asset_id else 'portfolio', alert.asset_id or alert.portfolio_id, 'alert_'+body.status, user['id'], {'alert': alert.title, 'from': before, 'note': body.note})
    return alert_row(alert)


@router.get('/catalog')
async def catalog(user=Depends(get_current_user)):
    return {'event_types': USER_EVENTS, 'frequencies': list(FREQUENCY_DAYS), 'default_settings': DEFAULT_SETTINGS, 'stresses': {k: v['label'] for k, v in STRESSES.items()}}
