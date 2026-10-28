"""Prepare method-specific inputs from persisted evidence, with explicit readiness gaps."""
import math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from sqlalchemy import select
from api.app.models.foundation import MarketObservation, DataSource
from api.app.services.foundation import assumptions, owner_id
from api.app.services.valuation_catalog import METHODS
from api.app.routers.map import map_records
from api.app.services.valuation_calculations import VERSION
from api.app.services.comparable_adjustments import analyse


def saudi_today():
    return datetime.now(ZoneInfo('Asia/Riyadh')).date()


def method_config(key):
    config = METHODS.get(key)
    if not config or not config['implemented']:
        raise HTTPException(422, 'This valuation method is not yet implemented')
    return config


def distance_km(a, b):
    lat1, lng1, lat2, lng2 = map(math.radians, [*a, *b])
    h = math.sin((lat2-lat1)/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin((lng2-lng1)/2)**2
    return 6371.0088*2*math.asin(min(1, math.sqrt(h)))


def numeric(value):
    if isinstance(value, bool): return None
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def validate_input(field, value):
    if value is None: return 'Required'
    if value < field['minimum'] or (field['positive'] and value <= 0):
        return 'Must be positive' if field['positive'] else f"Minimum {field['minimum']}"
    if field['maximum'] is not None and value > field['maximum']:
        return f"Maximum {field['maximum']}"
    if field['key'] == 'holding_years' and value != int(value):
        return 'Holding period must be whole years'
    return None


def path_value(data, path):
    if not path: return None
    result = data
    for part in path.split('.'):
        result = result.get(part) if isinstance(result, dict) else None
    return numeric(result)


async def prepare(db, p, user, method=None):
    setup = p.data.get('analysis') or {}
    key = method or setup.get('method') or 'sales_comparison'
    config = method_config(key)
    as_of = setup.get('as_of') or saudi_today().isoformat()
    from datetime import date
    cutoff = date.fromisoformat(as_of)
    radius = setup.get('radius_km', 3)
    lookback = setup.get('lookback_days', 365)
    saved = await assumptions(db, p)
    observations = []
    if p.city:
        observations = (await db.execute(select(MarketObservation, DataSource.name)
            .join(DataSource).where(DataSource.created_by == owner_id(user), MarketObservation.city == p.city,
                MarketObservation.property_type == p.property_type, MarketObservation.observed_on <= as_of,
                MarketObservation.observed_on >= (cutoff-timedelta(days=365)).isoformat(), MarketObservation.reliability >= 60)
            .order_by(MarketObservation.observed_on.desc(), MarketObservation.created_at.desc()))).all()
    fields = []
    for definition in config['fields']:
        f = dict(definition)
        a = saved.get(f'valuation_{key}_{f["key"]}')
        # Reuse matching central assumptions too, but only when the unit matches.
        if a is None:
            a = saved.get(f['key'])
        value = numeric(a['effective_value']) if a and a['unit'] == f['unit'] else None
        source = a['source'] if value is not None else None
        observed_on = a['as_of'] if value is not None else None
        origin = 'saved_assumption' if value is not None else None
        if value is None:
            path = f['property_path']
            if key == 'sales_comparison':
                path = 'land.area_sqm' if p.property_type == 'land' else 'building.built_up_area_sqm'
            value = path_value(p.data, path)
            if value is not None:
                source = 'Property workspace: '+path
                observed_on = p.data.get('provenance', {}).get('collected_on')
                origin = 'property_record'
        if value is None:
            # Exact metric/unit/type/city matching only; never infer cap rates from prices.
            observation = next(((o, name) for o, name in observations if o.metric == f['key'] and o.unit == f['unit']
                                and (o.district or None) == (p.district or None) and numeric(o.normalized_value) is not None), None)
            if observation:
                o, name = observation
                value = numeric(o.normalized_value)
                source = f'{name} · observation {o.id}'
                observed_on = o.observed_on
                origin = 'market_observation'
        error = validate_input(f, value)
        if value is not None and not observed_on:
            error = 'Source date is required'
        if observed_on and observed_on > as_of:
            error = 'Source date is after valuation date'
        f.update(value=value, source=source, as_of=observed_on, origin=origin,
                 assumption_status=a['status'] if origin == 'saved_assumption' else 'observed' if origin == 'market_observation' else 'user_input',
                 state='missing' if value is None else 'invalid' if error else 'available', error=error)
        fields.append(f)
    # Reuse the existing owner-scoped map projection and all reviewed field overrides.
    evidence = await map_records(q='', city=None, district=None, property_type=None, case_id=None,
        date_from=None, date_to=None, include_invalid=False, limit=5000,
        south=None, west=None, north=None, east=None, db=db, user=user)
    location = p.data.get('location', {})
    coords = [location.get('latitude'), location.get('longitude')]
    candidates, eligible, seen = [], [], set()
    for record in evidence['data']:
        if record['kind'] in {'property', 'market'}: continue
        if not record['coordinates'] or None in coords: continue
        distance = distance_km(coords, record['coordinates'])
        if distance > radius: continue
        reasons = []
        if record['property_type'] != p.property_type: reasons.append('Different property type')
        if record['kind'] != 'transaction': reasons.append('Not an achieved transaction')
        if record['status'] != 'active': reasons.append('Not reviewed active evidence')
        if not record['date'] or not ((cutoff-timedelta(days=lookback)).isoformat() <= record['date'] <= as_of): reasons.append('Missing / outside evidence period')
        if record['currency'] != 'SAR': reasons.append('Currency is not SAR')
        if record['price_per_sqm'] is None or record['price_per_sqm'] <= 0: reasons.append('Missing / invalid price or area')
        fingerprint = (record['source'] if str(record['source']).startswith(('https://', 'http://')) else record.get('source_id') or record['source'], tuple(record['coordinates']), record['date'], record['price'], record['area_sqm'])
        if not reasons:
            if fingerprint in seen: reasons.append('Repeated source / transaction evidence')
            else: seen.add(fingerprint)
        candidate = {**record, 'distance_km': round(distance, 3), 'eligible': not reasons, 'exclusion_reasons': reasons}
        candidates.append(candidate)
        if not reasons: eligible.append(candidate)
    candidates.sort(key=lambda r: r['distance_km'])
    gaps = [f"{f['label']}: {f['error']}" for f in fields if f['error']]
    values = {f['key']: f['value'] for f in fields if f['value'] is not None}
    if key == 'sales_comparison' and len(eligible) < 3:
        gaps.append(f'Need at least 3 distinct, active, dated, nearby achieved transactions; found {len(eligible)}')
    adjustment_setup = (setup.get('adjustments') or None) if key == 'sales_comparison' else None
    adjustment_analysis = None
    if key == 'sales_comparison' and len(eligible) >= 3:
        try:
            adjustment_analysis = analyse(eligible, adjustment_setup, values.get('area_sqm'), as_of)
            gaps.extend(adjustment_analysis['gaps'])
        except ValueError as exc:
            gaps.append(f'Comparable adjustments: {exc}')
    if key == 'sales_comparison' and evidence['truncated']:
        gaps.append('Evidence exceeds the map record limit; the evidence query must be narrowed before automated selection')
    if key == 'cost' and sum(values.get(k, 0) for k in ['physical_depreciation','functional_obsolescence','economic_obsolescence']) > 1:
        gaps.append('Combined depreciation and obsolescence cannot exceed 1 (100%)')
    if None in coords:
        gaps.append('Subject coordinates are required')
    if not p.property_type:
        gaps.append('Choose a property type in the property workspace')
    return {'property_id': str(p.id), 'property_name': p.name, 'revision': p.revision,
        'property_type': p.property_type, 'coordinates': coords if None not in coords else None,
        'method': key, 'method_label': config['label'], 'description': config['description'],
        'as_of': as_of, 'radius_km': radius, 'lookback_days': lookback, 'fields': fields,
        'candidates': candidates, 'eligible_comparables': eligible, 'gaps': gaps, 'ready': not gaps,
        'coverage': evidence.get('coverage'),
        'adjustment_setup': adjustment_setup, 'adjustment_analysis': adjustment_analysis,
        'calculation_version': VERSION,
        'calculation_status': 'ready' if not gaps else 'needs_inputs'}
