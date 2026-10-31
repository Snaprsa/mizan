"""Monitor orchestration: run the shared valuation pipeline per asset, snapshot real changes, keep alerts honest."""
import hashlib
import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from sqlalchemy import select
from api.app.models.foundation import Property
from api.app.models.monitor import MonitorAlert, MonitorEvent, PortfolioAsset, ValuationSnapshot
from api.app.routers.map import map_records
from api.app.services.analysis_workflow import prepare, saudi_today
from api.app.services.foundation import assumptions, owner_id
from api.app.services.monitor_calc import (DEFAULT_SETTINGS, METHOD_LABELS, MODEL_VERSION, SEVERITY_RANK, asset_alerts, attribute,
    divergence, evidence_grade, months_between, portfolio_alerts, priority, reconcile, value_range)
from api.app.services.valuation_calculations import VERSION, calculate

MONITORED_METHODS = list(METHOD_LABELS)
EVENT_FOR_INPUT = {'annual_rent': ('rent_change', 'property'), 'vacancy': ('occupancy_change', 'property'),
    'operating_expenses': ('operating_cost_change', 'property'), 'annual_capex': ('capex_change', 'property'),
    'cap_rate': ('cap_rate_movement', 'market'), 'exit_cap_rate': ('cap_rate_movement', 'market'), 'discount_rate': ('discount_rate_movement', 'market'),
    'construction_cost': ('construction_cost_movement', 'market'), 'rent_growth': ('rent_growth_change', 'market')}
# Things a user can record. Recording never changes a value by itself; only a changed input does.
USER_EVENTS = {'new_lease': 'property', 'lease_expiry': 'property', 'tenant_departure': 'property', 'occupancy_change': 'property', 'rent_change': 'property',
    'noi_change': 'property', 'capex_change': 'property', 'renovation': 'property', 'development_completion': 'property',
    'market_vacancy': 'market', 'supply_change': 'market', 'financing_rate': 'market', 'interest_rate': 'market',
    'zoning_change': 'location', 'planning_change': 'location', 'infrastructure': 'location', 'transport_project': 'location',
    'nearby_development': 'location', 'regulatory_change': 'location', 'other': 'property'}
FREQUENCY_DAYS = {'event_driven': 0, 'daily': 1, 'weekly': 7, 'monthly': 30, 'quarterly': 91}


def settings_of(portfolio):
    return {**DEFAULT_SETTINGS, **(portfolio.settings or {})}


def share(asset):
    return (asset.ownership_pct or 0)/100


def empty_evidence():
    return {'data': [], 'truncated': False, 'coverage': None}


async def evidence_for(db, user):
    """One evidence read per scan, so checking many assets does not re-read every record per method."""
    return await map_records(q='', city=None, district=None, property_type=None, case_id=None, date_from=None, date_to=None,
        include_invalid=False, limit=5000, south=None, west=None, north=None, east=None, db=db, user=user)


async def method_states(db, prop, user, asset, as_of, evidence):
    """Everything the shared engine needs per method. Same gates as a saved run: reviewed inputs and a ready method."""
    stored = await assumptions(db, prop)
    states, gaps = {}, []
    if asset.demo_evidence is not None:
        evidence = {**empty_evidence(), 'data': asset.demo_evidence}
    for method in MONITORED_METHODS:
        if not any(k.startswith(f'valuation_{method}_') for k in stored):
            continue
        prepared = await prepare(db, prop, user, method, as_of=as_of, evidence=evidence)
        missing = [f['label'] for f in prepared['fields'] if f'valuation_{method}_{f["key"]}' not in stored]
        if not prepared['ready'] or missing:
            gaps.extend(f'{METHOD_LABELS[method]}: {gap}' for gap in (prepared['gaps'] or [f'{m} not reviewed' for m in missing]))
            continue
        inputs = {f['key']: f['value'] for f in prepared['fields']}
        sales = method == 'sales_comparison'
        comps = prepared['eligible_comparables'] if sales else []
        state = {'inputs': inputs, 'comparables': comps, 'adjustments': prepared.get('adjustment_setup'), 'as_of': as_of,
                 'subject': prepared.get('subject_attributes') if sales else None}
        try:
            output = calculate(method, inputs, comps, include_sensitivity=False, adjustments=state['adjustments'], as_of=as_of, subject=state['subject'])
        except (ValueError, OverflowError, ZeroDivisionError) as exc:
            gaps.append(f'{METHOD_LABELS[method]}: {exc}')
            continue
        evidence_out = output.get('evidence') or {}
        states[method] = {**state, 'value': float(output['value']), 'limitations': output.get('limitations') or [],
            'indication': evidence_out.get('indication') if sales else None, 'uses_demo': bool(evidence_out.get('demo_comparables')),
            'meta': [{'key': f['key'], 'label': f['label'], 'unit': f['unit'], 'value': f['value'], 'source': f['source'], 'as_of': f['as_of'],
                      'status': f.get('assumption_status'), 'override': (stored.get(f'valuation_{method}_{f["key"]}') or {}).get('user_override') is not None}
                     for f in prepared['fields']]}
    return states, gaps


def fingerprint(states, weights):
    """Identifies what the value depends on. The date is left out, so a quiet day makes no new snapshot."""
    body = {m: {'inputs': s['inputs'], 'adjustments': s.get('adjustments'), 'subject': s.get('subject'),
                'comparables': sorted((c.get('id'), c.get('price'), c.get('area_sqm'), json.dumps(c.get('attributes') or {}, sort_keys=True)) for c in s.get('comparables') or [])}
            for m, s in states.items()}
    raw = json.dumps({'states': body, 'weights': weights or None, 'version': VERSION}, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def detect_changes(previous, states):
    """Plain-language list of what differs from the last snapshot; each one becomes an event."""
    old = (previous.data.get('methods') if previous else None) or {}
    changes, seen_inputs = [], set()
    if previous is None:
        changes.append({'type': 'baseline', 'category': 'system', 'text': 'First indicative valuation'})
    for method in sorted(set(states) - set(old)):
        if previous is not None:
            changes.append({'type': 'method_added', 'category': 'system', 'text': f'{METHOD_LABELS[method]} became available'})
    for method in sorted(set(old) - set(states)):
        changes.append({'type': 'method_removed', 'category': 'system', 'text': f'{METHOD_LABELS[method]} no longer has complete evidence'})
    for method in set(old) & set(states):
        before, after = old[method]['inputs'], states[method]['inputs']
        labels = {m['key']: m for m in states[method].get('meta') or []}
        for key in after:
            if key in before and before[key] != after[key] and key not in seen_inputs:
                seen_inputs.add(key)
                kind, category = EVENT_FOR_INPUT.get(key, ('input_change', 'property'))
                meta = labels.get(key, {})
                changes.append({'type': kind, 'category': category, 'input': key, 'before': before[key], 'after': after[key],
                    'text': f"{meta.get('label', key)}: {_show(before[key], meta.get('unit'))} → {_show(after[key], meta.get('unit'))}", 'override': meta.get('override')})
    old_sales = {c.get('id'): c for c in (old.get('sales_comparison') or {}).get('comparables') or []}
    new_sales = {c.get('id'): c for c in (states.get('sales_comparison') or {}).get('comparables') or []}
    if old_sales or previous is not None:
        for key, c in new_sales.items():
            if key not in old_sales:
                changes.append({'type': 'new_comparable', 'category': 'market', 'comparable': key,
                    'text': f"New comparable sale: {c.get('title')} at SAR {c.get('price_per_sqm') or 0:,.0f}/m² ({c.get('date')})"})
        for key, c in old_sales.items():
            if key not in new_sales:
                changes.append({'type': 'comparable_dropped', 'category': 'market', 'comparable': key,
                    'text': f"Comparable no longer eligible: {c.get('title')} ({c.get('date')})"})
    return changes


def _show(value, unit):
    if unit == 'ratio':
        return f'{value*100:.2f}%'
    return f'{value:,.0f}'+(f' {unit}' if unit else '')


async def latest_snapshot(db, property_id, kind):
    return await db.scalar(select(ValuationSnapshot).where(ValuationSnapshot.property_id == property_id, ValuationSnapshot.kind == kind)
        .order_by(ValuationSnapshot.valued_on.desc(), ValuationSnapshot.created_at.desc()).limit(1))


async def assess(db, asset, prop, user, settings, *, as_of=None, evidence=None, trigger=None, force=False):
    """Revalue one asset if what it depends on has changed. Returns the new snapshot, or None when nothing changed."""
    as_of = as_of or saudi_today().isoformat()
    day = date.fromisoformat(str(as_of))
    if evidence is None and asset.demo_evidence is None:
        evidence = await evidence_for(db, user)
    demonstration = asset.demo_evidence is not None
    states, gaps = await method_states(db, prop, user, asset, as_of, evidence)
    previous = await latest_snapshot(db, prop.id, 'indicative')
    weights = asset.method_weights
    snapshot = None
    if states:
        print_ = fingerprint(states, weights)
        if force or previous is None or previous.data.get('fingerprint') != print_:
            changes = detect_changes(previous, states)
            values = {m: s['value'] for m, s in states.items()}
            value, recon = reconcile(values, weights)
            low, high = value_range(values, (states.get('sales_comparison') or {}).get('indication'))
            grade = evidence_grade(states, as_of, settings, demonstration=demonstration)
            attribution = None
            if previous is not None and previous.data.get('methods'):
                attribution = attribute(previous.data['methods'], states, previous.value_sar, value,
                                        (previous.data.get('reconciliation') or {}).get('input_weights'), weights)
            uses_demo = demonstration or any(s.get('uses_demo') for s in states.values())
            label = trigger or next((c['type'] for c in changes if c['type'] != 'baseline'), 'baseline' if previous is None else 'manual_recheck')
            snapshot = ValuationSnapshot(property_id=prop.id, kind='indicative', valued_on=day, value_sar=value, low_sar=low, high_sar=high,
                confidence=grade['level'], trigger=label, origin='demo' if uses_demo else 'derived', previous_id=previous.id if previous else None,
                created_by=owner_id(user), data={'schema_version': 'mizan.monitor-snapshot.v1', 'model_version': MODEL_VERSION,
                    'calculation_version': VERSION, 'property_revision': prop.revision, 'as_of': as_of, 'methods': states,
                    'reconciliation': {**recon, 'input_weights': weights, 'values': values}, 'confidence': grade, 'divergence': divergence(values),
                    'attribution': attribution, 'changes': changes, 'gaps': gaps, 'fingerprint': print_})
            db.add(snapshot)
            await db.flush()
            for change in changes:
                db.add(MonitorEvent(property_id=prop.id, event_type=change['type'], category=change['category'], occurred_on=day, summary=change['text'],
                    origin='demo' if uses_demo else 'detected', snapshot_id=snapshot.id, details=change, created_by=owner_id(user)))
    asset.last_checked_at = datetime.utcnow()
    current = snapshot or previous
    previous_for_summary = None
    if current is not None and current.previous_id:
        previous_for_summary = await db.get(ValuationSnapshot, current.previous_id)
    official = await latest_snapshot(db, prop.id, 'official')
    new_sales = 0
    if official is not None and current is not None:
        comps = ((current.data.get('methods') or {}).get('sales_comparison') or {}).get('comparables') or []
        new_sales = sum(1 for c in comps if c.get('date') and c['date'] > official.valued_on.isoformat())
    asset.summary = base_summary(current, previous_for_summary, official, gaps, new_sales)
    return snapshot


def base_summary(current, previous, official, gaps, new_sales):
    """What changes only when a valuation changes. Ages and LTV are added by `finish_summary`."""
    out = {'value': None, 'gaps': gaps[:6], 'official_value': official.value_sar if official else None,
           'official_on': official.valued_on.isoformat() if official else None, 'official_origin': official.origin if official else None,
           'official_valuer': (official.data or {}).get('valuer') if official else None, 'new_sales_since_official': new_sales}
    if current is None:
        return out
    data = current.data
    methods = data.get('methods') or {}
    out.update(value=current.value_sar, low=current.low_sar, high=current.high_sar, valued_on=current.valued_on.isoformat(), origin=current.origin,
        snapshot_id=str(current.id), confidence=current.confidence, confidence_passed=(data.get('confidence') or {}).get('passed'),
        confidence_total=(data.get('confidence') or {}).get('total'), trigger=current.trigger, methods={m: s['value'] for m, s in methods.items()},
        basis=(data.get('reconciliation') or {}).get('basis'))
    spread = data.get('divergence')
    if spread:
        out.update(divergence_pct=spread['spread_pct'], divergence=spread)
    if previous is not None:
        out.update(previous_value=previous.value_sar, previous_on=previous.valued_on.isoformat(), previous_confidence=previous.confidence,
                   change_pct=(current.value_sar-previous.value_sar)/previous.value_sar*100 if previous.value_sar else None)
        order = {'low': 0, 'medium': 1, 'high': 2}
        if previous.confidence in order and current.confidence in order and order[current.confidence] < order[previous.confidence]:
            before = {c['key']: c['state'] for c in (previous.data.get('confidence') or {}).get('checks') or []}
            worse = [c for c in (data.get('confidence') or {}).get('checks') or [] if c['state'] != before.get(c['key']) and c['state'] in {'poor', 'fair'}]
            out.update(confidence_fell=True, confidence_reason='; '.join(f"{c['label']}: {c['detail']}" for c in worse[:2]))
    if official is not None and official.value_sar:
        out['change_vs_official_pct'] = (current.value_sar-official.value_sar)/official.value_sar*100
    income = methods.get('income_capitalization') or methods.get('dcf')
    if income:
        i = income['inputs']
        out['model_noi'] = i['annual_rent']*(1-i['vacancy'])+i['other_income']-i['operating_expenses']
        out['model_occupancy_pct'] = (1-i['vacancy'])*100
        out['model_rent'] = i['annual_rent']
    sales = methods.get('sales_comparison')
    if sales and sales['inputs'].get('area_sqm'):
        implied = current.value_sar/sales['inputs']['area_sqm']
        fresh = [c for c in data.get('changes') or [] if c['type'] == 'new_comparable']
        rows = {c.get('id'): c for c in sales.get('comparables') or []}
        gaps_found = [(rows[c['comparable']], (rows[c['comparable']].get('price_per_sqm', 0)-implied)/implied*100) for c in fresh if c.get('comparable') in rows and rows[c['comparable']].get('price_per_sqm')]
        if gaps_found:
            comp, pct = max(gaps_found, key=lambda g: abs(g[1]))
            out['new_sale_gap'] = {'pct': pct, 'date': comp.get('date'), 'title': comp.get('title'), 'sar_sqm': comp.get('price_per_sqm')}
    dates = [m.get('as_of') for s in methods.values() for m in s.get('meta') or [] if m.get('as_of')]
    sale_dates = [c.get('date') for s in methods.values() for c in s.get('comparables') or [] if c.get('date')]
    out['freshness'] = {'newest_input': max(dates) if dates else None, 'oldest_input': min(dates) if dates else None, 'newest_sale': max(sale_dates) if sale_dates else None}
    return out


def finish_summary(asset, summary, settings, as_of):
    """Add what moves with the calendar or the asset's facts; priority is derived last."""
    s = dict(summary)
    facts = asset.facts or {}
    if s.get('official_on'):
        s['official_age_months'] = months_between(s['official_on'], as_of)
    value = s['value'] if s.get('value') is not None else s.get('official_value')
    s['ltv_pct'] = asset.debt_sar/value*100 if asset.debt_sar and value else None
    fact_noi, fact_occ = facts.get('noi_sar_year'), facts.get('occupancy_pct')
    s['noi'], s['noi_origin'] = (fact_noi, 'user_provided') if fact_noi is not None else (s.get('model_noi'), 'derived' if s.get('model_noi') is not None else None)
    s['occupancy_pct'], s['occupancy_origin'] = (fact_occ, 'user_provided') if fact_occ is not None else (s.get('model_occupancy_pct'), 'derived' if s.get('model_occupancy_pct') is not None else None)
    s['cap_rate_pct'] = s['noi']/value*100 if s.get('noi') is not None and value else None
    fresh = s.get('freshness') or {}
    days = settings['stale_evidence_days']
    stale = []
    if fresh.get('newest_sale') and (months_between(fresh['newest_sale'], as_of) or 0)*30.4375 > days:
        stale.append(f"newest comparable sale is from {fresh['newest_sale']}")
    if fresh.get('oldest_input') and (months_between(fresh['oldest_input'], as_of) or 0)*30.4375 > days*2:
        stale.append(f"oldest input is from {fresh['oldest_input']}")
    s['stale_inputs'] = ('Evidence is stale: ' + ' and '.join(stale) + '.') if stale else None
    rank = priority(s, settings)
    s['priority'] = rank
    asset.priority_score = rank['score']
    asset.summary = s
    return s


def totals(rows, settings):
    """Portfolio figures at the owned share. Each figure says how many assets it covers, so gaps are not hidden."""
    t = dict(asset_count=len(rows), value=0.0, official=0.0, like_value=0.0, like_official=0.0, cost=0.0, book=0.0, debt=0.0, noi=0.0, noi_value=0.0,
             occupancy_weight=0.0, occupancy_value=0.0, indicative_count=0, official_only_count=0, unvalued_count=0, up=0, stable=0, down=0, not_comparable=0,
             cost_count=0, cost_value=0.0, book_count=0, debt_count=0, noi_count=0, occupancy_count=0, demo_count=0, move_count=0)
    conf = defaultdict(float)
    city, kind = defaultdict(float), defaultdict(float)
    band = settings['stable_band_pct']
    for asset, prop in rows:
        s, own = asset.summary or {}, share(asset)
        indicated = s.get('value')
        value = indicated if indicated is not None else s.get('official_value')
        if indicated is not None: t['indicative_count'] += 1
        elif value is not None: t['official_only_count'] += 1
        else: t['unvalued_count'] += 1
        if value is None:
            t['not_comparable'] += 1
            continue
        held = value*own
        t['value'] += held
        city[prop.city or 'Unknown'] += held
        kind[prop.property_type or 'unknown'] += held
        if s.get('origin') == 'demo': t['demo_count'] += 1
        if indicated is not None:
            conf[s.get('confidence') or 'none'] += held
        if s.get('official_value') is not None:
            t['official'] += s['official_value']*own
        move = s.get('change_vs_official_pct')
        if move is None:
            t['not_comparable'] += 1
        else:
            t['like_value'] += indicated*own
            t['like_official'] += s['official_value']*own
            t['up' if move > band else 'down' if move < -band else 'stable'] += 1
            if abs(move) >= settings['move_watch_pct']: t['move_count'] += 1
        if asset.acquisition_cost_sar is not None:
            t['cost'] += asset.acquisition_cost_sar*own; t['cost_value'] += held; t['cost_count'] += 1
        if asset.book_value_sar is not None:
            t['book'] += asset.book_value_sar*own; t['book_count'] += 1
        if asset.debt_sar is not None:
            t['debt'] += asset.debt_sar*own; t['debt_count'] += 1
        if s.get('noi') is not None:
            t['noi'] += s['noi']*own; t['noi_value'] += held; t['noi_count'] += 1
        if s.get('occupancy_pct') is not None:
            t['occupancy_weight'] += s['occupancy_pct']*held; t['occupancy_value'] += held; t['occupancy_count'] += 1
    v = t['value']
    t['change'] = t['like_value']-t['like_official'] if t['like_official'] else None
    t['change_pct'] = t['change']/t['like_official']*100 if t['like_official'] else None
    t['unrealised'] = t['cost_value']-t['cost'] if t['cost_count'] else None
    t['cap_rate_pct'] = t['noi']/t['noi_value']*100 if t['noi_value'] else None
    t['occupancy_pct'] = t['occupancy_weight']/t['occupancy_value'] if t['occupancy_value'] else None
    t['ltv_pct'] = t['debt']/v*100 if t['debt_count'] and v else None
    t['nav'] = v-t['debt'] if t['debt_count'] else None
    t['official_nav'] = t['official']-t['debt'] if t['debt_count'] and t['official'] else None
    t['confidence_share'] = {k: a/v*100 for k, a in conf.items()} if v else {}
    def rollup(group):
        return [{'key': k, 'label': k.replace('_', ' ').capitalize(), 'value': a, 'share_pct': a/v*100} for k, a in sorted(group.items(), key=lambda x: -x[1])] if v else []
    t['by_city'], t['by_type'] = rollup(city), rollup(kind)
    t['origin'] = 'demo' if t['asset_count'] and t['demo_count'] == t['indicative_count'] and t['demo_count'] else 'derived'
    t['compared_count'] = t['up']+t['stable']+t['down']
    for key in ['like_value', 'cost_value', 'noi_value', 'occupancy_weight', 'occupancy_value']:
        t.pop(key)
    return t


async def portfolio_rows(db, portfolio):
    return (await db.execute(select(PortfolioAsset, Property).join(Property, Property.id == PortfolioAsset.property_id)
        .where(PortfolioAsset.portfolio_id == portfolio.id))).all()


async def refresh(db, portfolio, as_of=None):
    """Recompute ages, priority and alerts. Alerts reflect what holds now: cleared ones resolve, repeats do not stack."""
    as_of = as_of or saudi_today().isoformat()
    settings = settings_of(portfolio)
    rows = await portfolio_rows(db, portfolio)
    wanted = {}
    for asset, prop in rows:
        summary = finish_summary(asset, asset.summary or {}, settings, as_of)
        for kind, severity, title, message, details in asset_alerts(prop.name, summary, settings):
            wanted[(asset.id, kind)] = dict(severity=severity, title=title, message=message, details=details)
    for kind, severity, title, message, details in portfolio_alerts(totals(rows, settings), settings):
        wanted[(None, kind)] = dict(severity=severity, title=title, message=message, details=details)
    existing = (await db.scalars(select(MonitorAlert).where(MonitorAlert.portfolio_id == portfolio.id, MonitorAlert.status != 'resolved'))).all()
    day = date.fromisoformat(str(as_of))
    seen = set()
    for alert in existing:
        key = (alert.asset_id, alert.kind)
        now = wanted.get(key)
        if now is None:
            alert.status, alert.note, alert.updated_at = 'resolved', 'Condition no longer holds', datetime.utcnow()
            continue
        seen.add(key)
        if alert.status == 'accepted' and SEVERITY_RANK[now['severity']] > SEVERITY_RANK[alert.severity]:
            alert.status = 'open'  # Accepted at a lower level; it has got worse, so it needs a fresh look.
        if alert.message != now['message'] or alert.severity != now['severity']:
            alert.severity, alert.title, alert.message, alert.details, alert.updated_at = now['severity'], now['title'], now['message'], now['details'], datetime.utcnow()
    for key, now in wanted.items():
        if key not in seen:
            db.add(MonitorAlert(portfolio_id=portfolio.id, asset_id=key[0], kind=key[1], raised_on=day, **now))
    portfolio.last_checked_at = datetime.utcnow()
    await db.flush()


async def scan(db, portfolio, user, *, only_due=False, as_of=None):
    """Look for changed evidence across a portfolio; only what actually changed gets a new snapshot."""
    settings = settings_of(portfolio)
    now = datetime.utcnow()
    rows = await portfolio_rows(db, portfolio)
    evidence = None
    checked = updated = skipped = 0
    for asset, prop in rows:
        if only_due and asset.last_checked_at is not None:
            wait = FREQUENCY_DAYS.get(asset.monitoring_frequency, 0)
            if now-asset.last_checked_at < (timedelta(days=wait) if wait else timedelta(hours=1)):
                skipped += 1
                continue
        if evidence is None and asset.demo_evidence is None:
            evidence = await evidence_for(db, user)
        made = await assess(db, asset, prop, user, settings, as_of=as_of, evidence=evidence)
        checked += 1
        updated += 1 if made else 0
    await refresh(db, portfolio, as_of)
    return {'checked': checked, 'updated': updated, 'unchanged': checked-updated, 'skipped': skipped}


def month_end(day):
    next_month = (day.replace(day=28)+timedelta(days=4)).replace(day=1)
    return next_month-timedelta(days=1)


async def history(db, portfolio, rows, as_of=None):
    """Portfolio value through time, carrying each asset's last known value forward. Month-end points keep it bounded."""
    ownership = {prop.id: share(asset) for asset, prop in rows}
    if not ownership:
        return []
    found = (await db.execute(select(ValuationSnapshot.property_id, ValuationSnapshot.kind, ValuationSnapshot.valued_on, ValuationSnapshot.value_sar)
        .join(PortfolioAsset, PortfolioAsset.property_id == ValuationSnapshot.property_id)
        .where(PortfolioAsset.portfolio_id == portfolio.id).order_by(ValuationSnapshot.valued_on, ValuationSnapshot.created_at))).all()
    if not found:
        return []
    today = date.fromisoformat(as_of) if as_of else saudi_today()
    points, cursor = [], month_end(found[0].valued_on)
    while cursor < today:
        points.append(cursor); cursor = month_end(cursor+timedelta(days=1))
    points.append(today)
    last = {'indicative': {}, 'official': {}}
    out, i = [], 0
    for point in points:
        while i < len(found) and found[i].valued_on <= point:
            last[found[i].kind][found[i].property_id] = found[i].value_sar
            i += 1
        out.append({'date': point.isoformat(), 'indicative': sum(v*ownership[k] for k, v in last['indicative'].items()) if last['indicative'] else None,
                    'official': sum(v*ownership[k] for k, v in last['official'].items()) if last['official'] else None,
                    'assets': len(last['indicative'])})
    return out
