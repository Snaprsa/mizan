"""Market-derived size adjustment: recovers a known effect, refuses thin evidence, and never applies itself."""
import math
import uuid
import pytest
from api.app.services.size_effect import derive
from api.tests.test_analysis import client, start, payload  # noqa: F401
from api.app.database import async_session
from api.app.models import Comparable, Source

AS_OF = '2026-11-05'


def record(area, rate, kind='transaction', d='2026-06-01'):
    return {'kind': kind, 'property_type': 'land', 'status': 'active', 'currency': 'SAR', 'area_sqm': area, 'price_per_sqm': rate, 'date': d}


def market(b=-0.15, wobble=0.03, listing_premium=0.0):
    # A deterministic synthetic market with a known size effect and small alternating noise.
    out = []
    for i, area in enumerate([600, 800, 1000, 1250, 1500, 2000, 2500, 3000, 4000, 5000, 6000, 8000]):
        noise = 1 + wobble * (1 if i % 2 else -1)
        out.append(record(area, 4000 * (area / 1000) ** b * noise))
        out.append(record(area * 1.1, 4000 * (area * 1.1 / 1000) ** b * (1 + listing_premium) / noise, kind='listing'))
    return out


def test_recovers_a_known_size_effect_and_turns_it_into_adjustments():
    r = derive(market(listing_premium=0.12), property_type='land', as_of=AS_OF, lookback_days=1095, subject_area=5000,
               comparables=[{'id': 'small', 'area_sqm': 1000}, {'id': 'same', 'area_sqm': 5000}, {'id': 'big', 'area_sqm': 10000}])
    m = r['model']
    assert m['elasticity'] == pytest.approx(-0.15, abs=0.01) and m['clear']
    assert m['asking_premium'] == pytest.approx(0.12, abs=0.02), 'asking prices are separated from sales'
    s = {x['comparable_id']: x for x in r['suggestions']}
    assert s['small']['percent'] == pytest.approx(5 ** -0.15 - 1, abs=0.01)   # about −21%: a 1,000 m² plot sells higher per m²
    assert s['same']['percent'] == pytest.approx(0, abs=1e-9)
    assert s['big']['percent'] > 0 and s['small']['low'] <= s['small']['percent'] <= s['small']['high']


def test_thin_or_narrow_evidence_suggests_nothing():
    thin = derive(market()[:5], property_type='land', as_of=AS_OF, lookback_days=1095, subject_area=5000, comparables=[{'id': 'a', 'area_sqm': 1000}])
    assert thin['model'] is None and not thin['suggestions'] and 'at least' in thin['notes'][0]
    narrow = [record(1000 + i * 20, 4000 + i) for i in range(12)]
    r = derive(narrow, property_type='land', as_of=AS_OF, lookback_days=1095, subject_area=5000, comparables=[{'id': 'a', 'area_sqm': 1000}])
    assert r['model'] is None and 'too narrow' in r['notes'][0]
    other = derive([{**x, 'property_type': 'villa'} for x in market()], property_type='land', as_of=AS_OF, lookback_days=1095, subject_area=5000, comparables=[])
    assert other['records_considered'] == 0
    old = derive([{**x, 'date': '2020-01-01'} for x in market()], property_type='land', as_of=AS_OF, lookback_days=1095, subject_area=5000, comparables=[])
    assert old['records_considered'] == 0


def test_no_clear_effect_is_reported_as_such():
    flat = [record(a, 4000 * (1.2 if i % 3 == 0 else 0.85 if i % 3 == 1 else 1.0)) for i, a in enumerate([600, 900, 1200, 2000, 3000, 4500, 6000, 8000, 700, 5000])]
    r = derive(flat, property_type='land', as_of=AS_OF, lookback_days=1095, subject_area=3000, comparables=[{'id': 'a', 'area_sqm': 1000}])
    assert r['model'] and not r['model']['clear'] and any('no clear size effect' in n for n in r['notes'])


@pytest.mark.asyncio
async def test_endpoint_reads_nearby_evidence_and_saves_nothing(client):
    p = await start(client, 'sales_comparison'); path = '/api/v1/analysis/' + p['property_id']
    p = (await client.put(path + '/inputs', json=payload(p, {'area_sqm': 5000}))).json()
    case_id = (await client.get('/api/v1/properties/' + p['property_id'])).json()['property']['case_id']
    async with async_session() as db:
        for i, area in enumerate([600, 800, 1000, 1500, 2000, 3000, 4000, 6000, 8000, 900]):
            source = Source(case_id=uuid.UUID(case_id), source_type='url', url=f'https://example.com/size/{i}')
            db.add(source); await db.flush()
            rate = 4000 * (area / 1000) ** -0.2 * (1.02 if i % 2 else 0.98)
            db.add(Comparable(case_id=uuid.UUID(case_id), source_id=source.id, property_title=f'Size {i}', property_type='land', city='Riyadh',
                latitude=24.7 + i * 0.002, longitude=46.7, evidence_type='transaction_achieved', transacted_price=rate * area,
                primary_area_sqm=area, transaction_date='2026-10-12', status='active'))
        await db.commit()
    before = (await client.get(path)).json()['revision']
    r = (await client.get(path + '/size-effect')).json()
    assert r['model']['elasticity'] == pytest.approx(-0.2, abs=0.03) and r['subject_area'] == 5000 and r['sales'] == 10
    assert r['suggestions'] and all(s['percent'] is not None for s in r['suggestions'])
    assert (await client.get(path)).json()['revision'] == before, 'deriving a suggestion must not save anything'
    assert math.isfinite(r['model']['per_doubling'])
