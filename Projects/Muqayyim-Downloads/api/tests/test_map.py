"""Map evidence must preserve ownership, dates, source classification and missing locations."""
import uuid
from datetime import datetime
import pytest
from httpx import ASGITransport, AsyncClient
from api.app.main import app
from api.app.database import Base, engine, async_session
from api.app.models import Comparable, Source, User, ExtractionJob, ExtractedField, Override
from api.app.auth import DEV_USER, create_token


@pytest.fixture
async def client():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as c:
        yield c
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def seed(client):
    c = await client.post('/api/v1/cases', json={'title': 'Map evidence test'})
    case_id = uuid.UUID(c.json()['id'])
    source_id = uuid.uuid4()
    async with async_session() as db:
        db.add(Source(id=source_id, case_id=case_id, source_type='manual', status='fetched'))
        await db.flush()
        rows = [
            Comparable(case_id=case_id, source_id=source_id, property_title='Recorded sale', city='Riyadh', district='A',
                property_type='land', latitude=24.7, longitude=46.7, evidence_type='transaction_achieved',
                transacted_price=1000000, primary_area_sqm=500, transaction_date='2026-10-12', status='active'),
            Comparable(case_id=case_id, source_id=source_id, property_title='Listing not sale', city='Riyadh', district='A',
                property_type='villa', latitude=24.71, longitude=46.71, evidence_type='listing_asking', asking_price=2000000,
                primary_area_sqm=400, listing_date='2026-10-15', status='draft'),
            Comparable(case_id=case_id, source_id=source_id, property_title='Missing location', city='Jeddah',
                property_type='land', evidence_type='official_record', transacted_price=500000,
                transaction_date='2026-10-10', status='active'),
            Comparable(case_id=case_id, source_id=source_id, property_title='Undated evidence', city='Riyadh',
                evidence_type='transaction_achieved', transacted_price=99999, latitude=100, longitude=46, status='active'),
            Comparable(case_id=case_id, source_id=source_id, property_title='Invalid record', city='Riyadh', status='invalid'),
        ]
        db.add_all(rows); await db.commit()
    return case_id, source_id, rows


@pytest.mark.asyncio
async def test_map_evidence_and_missing_coordinates(client):
    case_id, _, _ = await seed(client)
    p = await client.post('/api/v1/properties', json={'name': 'Subject', 'case_id': str(case_id),
        'location': {'city': 'Riyadh', 'latitude': 24.72, 'longitude': 46.72}})
    assert p.status_code == 201
    r = await client.get('/api/v1/map/records')
    assert r.status_code == 200, r.text
    body = r.json()
    assert body['total'] == 5
    assert body['counts'] == {'mapped': 3, 'missing_location': 2, 'transactions': 2, 'listings': 1, 'properties': 1}
    sale = next(x for x in body['data'] if x['title'] == 'Recorded sale')
    assert sale['price_per_sqm'] == 2000
    assert sale['kind'] == 'transaction'
    listing = next(x for x in body['data'] if x['title'] == 'Listing not sale')
    assert listing['kind'] == 'listing' and listing['price'] == 2000000
    invalid_coords = next(x for x in body['data'] if x['title'] == 'Undated evidence')
    assert invalid_coords['kind'] == 'other' and invalid_coords['coordinates'] is None
    assert (await client.get('/api/v1/map/records?include_invalid=true')).json()['total'] == 6


@pytest.mark.asyncio
async def test_map_dates_use_evidence_not_creation_date(client):
    await seed(client)
    r = (await client.get('/api/v1/map/records?date_from=2026-10-12&date_to=2026-10-15')).json()
    assert r['total'] == 2
    assert {x['title'] for x in r['data']} == {'Recorded sale', 'Listing not sale'}
    assert (await client.get('/api/v1/map/records?date_from=2027-01-01')).json()['total'] == 0
    assert (await client.get('/api/v1/map/records?date_from=2026-10-20&date_to=2026-10-01')).status_code == 422
    assert (await client.get('/api/v1/map/records?date_from=not-a-date')).status_code == 422


@pytest.mark.asyncio
async def test_map_filters_and_truncation(client):
    case_id, _, _ = await seed(client)
    assert (await client.get('/api/v1/map/records?city=Jeddah')).json()['total'] == 1
    assert (await client.get('/api/v1/map/records?district=A&property_type=villa')).json()['total'] == 1
    assert (await client.get('/api/v1/map/records?q=Recorded%20sale')).json()['total'] == 1
    assert (await client.get(f'/api/v1/map/records?case_id={case_id}')).json()['total'] == 4
    assert (await client.get(f'/api/v1/map/records?case_id={uuid.uuid4()}')).json()['total'] == 0
    r = (await client.get('/api/v1/map/records?limit=1')).json()
    assert len(r['data']) == 1 and r['total'] == 4 and r['truncated']


@pytest.mark.asyncio
async def test_map_owner_scope(client):
    await seed(client)
    other = uuid.uuid4()
    async with async_session() as db:
        db.add(User(id=other, email='map_other@test.local', name='Other', role='analyst'))
        await db.commit()
    r = await client.get('/api/v1/map/records', headers={'Authorization': 'Bearer '+create_token(str(other), 'map_other@test.local', 'analyst')})
    assert r.status_code == 200
    assert r.json()['total'] == 0 and r.json()['available']['cities'] == []


@pytest.mark.asyncio
async def test_map_uses_reviewed_coordinate_override(client):
    case_id, source_id, rows = await seed(client)
    async with async_session() as db:
        job = ExtractionJob(source_id=source_id, status='completed')
        db.add(job); await db.flush()
        field = ExtractedField(extraction_job_id=job.id, comparable_id=rows[0].id,
            field_name='latitude', raw_value='24.7', normalized_value='24.7', value_type='number')
        db.add(field); await db.flush()
        db.add(Override(extracted_field_id=field.id, old_value='24.7', new_value='24.75',
            reason='Reviewed survey coordinates', user_id=uuid.UUID(DEV_USER['id'])))
        await db.commit()
    r = (await client.get('/api/v1/map/records')).json()
    sale = next(x for x in r['data'] if x['title'] == 'Recorded sale')
    assert sale['coordinates'] == [24.75, 46.7]


@pytest.mark.asyncio
async def test_map_viewport_bounds_use_latitude_longitude_order(client):
    await seed(client)
    # Box around the Riyadh points only: latitude 24.65–24.75, longitude 46.65–46.75.
    r = await client.get('/api/v1/map/records', params={'south': 24.65, 'west': 46.65, 'north': 24.75, 'east': 46.75})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body['coordinate_order'] == '[latitude, longitude]'
    assert {x['title'] for x in body['data']} == {'Recorded sale', 'Listing not sale'}
    assert body['matching_filters'] == 4 and body['total'] == 2 and body['returned'] == 2
    assert all(x['location_precision'] == 'source_reported' for x in body['data'])
    # The same numbers in GeoJSON [longitude, latitude] order must not match.
    swapped = await client.get('/api/v1/map/records', params={'south': 46.65, 'west': 24.65, 'north': 46.75, 'east': 24.75})
    assert swapped.json()['total'] == 0
    partial = await client.get('/api/v1/map/records', params={'south': 24.65, 'north': 24.75})
    assert partial.status_code == 422
    inverted = await client.get('/api/v1/map/records', params={'south': 25, 'west': 46, 'north': 24, 'east': 47})
    assert inverted.status_code == 422


@pytest.mark.asyncio
async def test_missing_locations_keep_precision_and_stay_listed(client):
    await seed(client)
    body = (await client.get('/api/v1/map/records')).json()
    missing = next(x for x in body['data'] if x['title'] == 'Missing location')
    assert missing['coordinates'] is None and missing['location_precision'] == 'missing'
    # Newest evidence first; undated records last.
    dates = [x['date'] for x in body['data']]
    assert dates[-1] is None and dates[0] == '2026-10-15'


@pytest.mark.asyncio
async def test_site_outline_is_geojson_and_never_cadastral(client):
    ring = [[46.70, 24.70], [46.71, 24.70], [46.71, 24.71], [46.70, 24.70]]
    outline = {'type': 'Polygon', 'coordinates': [ring], 'drawn_on': '2026-10-28', 'basemap': 'satellite'}
    ok = await client.post('/api/v1/properties', json={'name': 'Outlined', 'location': {
        'latitude': 24.705, 'longitude': 46.705, 'coordinate_source': 'map_pin',
        'coordinate_precision': 'user_selected', 'site_outline': outline}})
    assert ok.status_code == 201, ok.text
    saved = ok.json()['property']['location']['site_outline']
    assert saved['cadastral'] is False and saved['source'] == 'user_drawn'
    assert 'not a certified cadastral' in saved['note']
    for bad in ({**outline, 'cadastral': True},
                {**outline, 'coordinates': [ring[:-1]]},  # unclosed ring
                {**outline, 'coordinates': [[[24.70, 146.70], [24.71, 46.70], [24.71, 46.71], [24.70, 146.70]]]}):
        r = await client.post('/api/v1/properties', json={'name': 'Bad', 'location': {'site_outline': bad}})
        assert r.status_code == 422, bad
    body = (await client.get('/api/v1/map/records')).json()
    prop = next(x for x in body['data'] if x['kind'] == 'property')
    assert prop['has_site_outline'] is True and prop['location_precision'] == 'user_selected'
    assert prop['coordinate_source'] == 'map_pin'


@pytest.mark.asyncio
async def test_map_start_records_coordinate_provenance(client):
    r = await client.post('/api/v1/analysis/start', json={'latitude': 24.7, 'longitude': 46.7,
        'property_type': 'land', 'method': 'sales_comparison', 'coordinate_source': 'geocoded',
        'coordinate_precision': 'approximate'})
    assert r.status_code == 201, r.text
    p = (await client.get(f"/api/v1/properties/{r.json()['property_id']}")).json()
    assert p['property']['location']['coordinate_source'] == 'geocoded'
    assert p['property']['location']['coordinate_precision'] == 'approximate'
