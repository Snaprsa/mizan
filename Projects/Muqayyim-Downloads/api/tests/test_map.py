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
