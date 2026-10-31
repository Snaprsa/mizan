"""Owned property/comparable map evidence. Unknown locations/dates are never inferred."""
import math
import uuid
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.app.database import get_db
from api.app.auth import get_current_user
from api.app.models import Case, Comparable, Source, ExtractedField, Override
from api.app.models.foundation import Property, MarketObservation, DataSource
from api.app.services.foundation import owner_id

router = APIRouter(prefix='/map', tags=['Property intelligence map'])
TRANSACTION_TYPES = {'transaction_achieved', 'official_record', 'auction_result'}


def iso_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)).isoformat()
    except (ValueError, TypeError):
        return None


def number(value):
    try:
        n = float(value)
        return n if math.isfinite(n) else None
    except (ValueError, TypeError):
        return None


def in_bbox(coords, south, west, north, east):
    """Coordinates are [latitude, longitude]. A west > east box crosses the antimeridian."""
    if coords is None:
        return False
    lat, lng = coords
    if not south <= lat <= north:
        return False
    return west <= lng <= east if west <= east else (lng >= west or lng <= east)


def coordinates(lat, lng):
    lat, lng = number(lat), number(lng)
    if lat is None or lng is None or not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return None
    return [lat, lng]


@router.get('/records')
async def map_records(q: str = Query('', max_length=255), city: str | None = None,
        district: str | None = None, property_type: str | None = None,
        case_id: uuid.UUID | None = None, date_from: date | None = None, date_to: date | None = None,
        include_invalid: bool = False, limit: int = Query(5000, ge=1, le=5000),
        south: float | None = Query(None, ge=-90, le=90), west: float | None = Query(None, ge=-180, le=180),
        north: float | None = Query(None, ge=-90, le=90), east: float | None = Query(None, ge=-180, le=180),
        db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(422, 'Start date must not be after end date')
    bbox = (south, west, north, east)
    if any(v is not None for v in bbox) and any(v is None for v in bbox):
        raise HTTPException(422, 'Viewport bounds need south, west, north and east together')
    if south is not None and south > north:
        raise HTTPException(422, 'South bound must not be north of the north bound')
    bbox = bbox if south is not None else None
    records = []
    # Scope both endpoints of the legacy case/comparable relationship to the caller.
    comps = (await db.execute(select(Comparable, Source.url, Source.file_name)
        .join(Case, Case.id == Comparable.case_id).join(Source, Source.id == Comparable.source_id)
        .where(Case.created_by == owner_id(user), Source.case_id == Case.id).order_by(Comparable.created_at.desc()))).all()
    comp_ids = {c.id for c, _, _ in comps}
    effective = {}
    if comp_ids:
        # Join rather than a large IN clause (SQLite variable limits).
        fields = (await db.scalars(select(ExtractedField).join(Comparable, Comparable.id == ExtractedField.comparable_id)
            .join(Case, Case.id == Comparable.case_id).where(Case.created_by == owner_id(user))
            .order_by(ExtractedField.extracted_at, ExtractedField.id))).all()
        overrides = (await db.scalars(select(Override).join(ExtractedField, ExtractedField.id == Override.extracted_field_id)
            .join(Comparable, Comparable.id == ExtractedField.comparable_id).join(Case, Case.id == Comparable.case_id)
            .where(Case.created_by == owner_id(user)).order_by(Override.created_at, Override.id))).all()
        latest_override = {o.extracted_field_id: o.new_value for o in overrides}
        for f in fields:
            effective.setdefault(f.comparable_id, {})[f.field_name] = latest_override.get(f.id,
                f.normalized_value if f.normalized_value is not None else f.raw_value)
    for c, url, filename in comps:
        if not include_invalid and c.status in {'invalid', 'outlier'}:
            continue
        if case_id and c.case_id != case_id:
            continue
        fields = effective.get(c.id, {})
        def value(key):
            return fields[key] if key in fields else getattr(c, key, None)
        evidence = value('evidence_type')
        trans_price = number(value('transacted_price'))
        trans_date = iso_date(value('transaction_date'))
        kind = 'transaction' if evidence in TRANSACTION_TYPES and trans_price is not None and trans_date else (
            'listing' if evidence == 'listing_asking' else 'other')
        observed = trans_date if kind == 'transaction' else iso_date(value('listing_date'))
        price = trans_price if kind == 'transaction' else number(value('asking_price')) if kind == 'listing' else None
        area = number(value('primary_area_sqm'))
        records.append({'id': 'comparable:'+str(c.id), 'entity_id': str(c.id), 'kind': kind,
            'title': value('property_title') or 'Untitled comparable', 'city': value('city'),
            'district': value('district'), 'property_type': value('property_type'),
            'coordinates': coordinates(value('latitude'), value('longitude')),
            'location_precision': 'source_reported' if coordinates(value('latitude'), value('longitude')) else 'missing',
            'date': observed, 'date_basis': 'transaction_date' if kind == 'transaction' else 'listing_date',
            'evidence_type': evidence, 'status': c.status, 'price': price, 'currency': c.currency or 'SAR',
            'area_sqm': area, 'price_per_sqm': price / area if price is not None and area and area > 0 else None,
            'source': url or filename or 'Manual / unspecified source', 'source_id': str(c.source_id),
            'attributes': c.attributes or {}, 'reliability_score': c.reliability_score, 'case_id': str(c.case_id),
            'href': '/cases/'+str(c.case_id)})
    props = (await db.scalars(select(Property).where(Property.created_by == owner_id(user))
                              .order_by(Property.updated_at.desc()))).all()
    for p in props:
        if case_id and p.case_id != case_id:
            continue
        loc = p.data.get('location', {})
        financial = p.data.get('financial', {})
        price = number(financial.get('asking_price_sar'))
        area = number(p.data.get('land', {}).get('area_sqm'))
        records.append({'id': 'property:'+str(p.id), 'entity_id': str(p.id), 'kind': 'property',
            'title': p.name, 'city': p.city, 'district': p.district, 'property_type': p.property_type,
            'coordinates': coordinates(loc.get('latitude'), loc.get('longitude')),
            'location_precision': (loc.get('coordinate_precision') or 'unspecified')
                if coordinates(loc.get('latitude'), loc.get('longitude')) else 'missing',
            'coordinate_source': loc.get('coordinate_source'),
            'has_site_outline': bool(loc.get('site_outline')),
            'date': iso_date(p.data.get('provenance', {}).get('collected_on')), 'date_basis': 'collected_on',
            'evidence_type': 'subject_property', 'status': 'property', 'price': price, 'currency': p.currency,
            'area_sqm': area, 'price_per_sqm': price / area if price is not None and area and area > 0 else None,
            'source': p.data.get('provenance', {}).get('source') or 'User property',
            'reliability_score': None, 'case_id': str(p.case_id) if p.case_id else None,
            'href': '/properties/'+str(p.id)})
    observations = (await db.execute(select(MarketObservation, DataSource.name).join(DataSource)
        .where(DataSource.created_by == owner_id(user)).order_by(MarketObservation.observed_on.desc()))).all()
    for o, source_name in observations:
        if case_id: continue  # Market data is global; a case-scoped view does not imply a case relationship.
        exact = o.details.get('location_precision') in {'exact', 'property'}
        records.append({'id': 'market:'+str(o.id), 'entity_id': str(o.id), 'kind': 'market',
            'title': o.metric.replace('_', ' ').title(), 'city': o.city, 'district': o.district,
            'property_type': o.property_type,
            'coordinates': coordinates(o.details.get('latitude'), o.details.get('longitude')) if exact else None,
            'location_precision': o.details.get('location_precision') or ('area' if o.city or o.district else 'missing'),
            'date': iso_date(o.observed_on), 'date_basis': 'observation_date', 'evidence_type': 'market_observation',
            'status': 'source_observation', 'price': None, 'currency': 'SAR', 'area_sqm': None,
            'price_per_sqm': None, 'source': source_name, 'source_id': str(o.data_source_id),
            'reliability_score': None, 'case_id': None, 'href': '/data',
            'metric': o.metric, 'value': o.normalized_value, 'unit': o.unit,
            'raw_value': o.raw_value, 'reliability_percent': o.reliability})
    from api.app.routers.market import local_datasets
    datasets = await local_datasets(user=user)
    coverage = {'properties': len(props), 'comparables': len(comps), 'market_observations': len(observations),
                'unverified_datasets': len(datasets), 'datasets': datasets,
                'demo_comparables': sum(1 for c, _, _ in comps if (c.attributes or {}).get('is_demo')),
                'missing_location': sum(r['coordinates'] is None for r in records)}
    def matches(r):
        if city and r['city'] != city: return False
        if district and r['district'] != district: return False
        if property_type and r['property_type'] != property_type: return False
        if q and q.casefold() not in ' '.join(str(r.get(k) or '') for k in
            ['title', 'city', 'district', 'property_type', 'source']).casefold(): return False
        if date_from or date_to:
            if r['date'] is None: return False
            if date_from and r['date'] < date_from.isoformat(): return False
            if date_to and r['date'] > date_to.isoformat(): return False
        return True
    selected = [r for r in records if matches(r)]
    matching_filters = len(selected)
    if bbox:
        selected = [r for r in selected if in_bbox(r['coordinates'], *bbox)]
    # Newest first, undated last, stable by ID, so a truncated subset is reproducible.
    selected.sort(key=lambda r: r['id'])
    selected.sort(key=lambda r: r['date'] or '', reverse=True)
    return {'data': selected[:limit], 'total': len(selected), 'truncated': len(selected) > limit,
        'returned': min(len(selected), limit), 'matching_filters': matching_filters,
        'bbox': dict(zip(['south', 'west', 'north', 'east'], bbox)) if bbox else None,
        'coordinate_order': '[latitude, longitude]',
        'available': {'cities': sorted({str(r['city']) for r in records if r['city']}),
                      'property_types': sorted({str(r['property_type']) for r in records if r['property_type']})},
        'coverage': coverage,
        'counts': {'mapped': sum(r['coordinates'] is not None for r in selected),
                   'missing_location': sum(r['coordinates'] is None for r in selected),
                   'transactions': sum(r['kind'] == 'transaction' for r in selected),
                   'listings': sum(r['kind'] == 'listing' for r in selected),
                   'properties': sum(r['kind'] == 'property' for r in selected)},
        'scope': 'Saved Mizan records only; not total market activity. Counts are records, not deduplicated properties.'}
