"""Foundation integration tests use isolated SQLite and the existing API dependency graph."""
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from api.app.main import app
from api.app.database import Base, engine, async_session
from api.app.models import Case, User
from api.app.models.foundation import PropertyRevision
from api.app.auth import create_token


@pytest.fixture
async def client():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as c:
        yield c
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def property_created(client, **extra):
    r = await client.post('/api/v1/properties', json={'name': 'أرض الرياض', **extra})
    assert r.status_code == 201, r.text
    return r.json()


async def source_created(client):
    r = await client.post('/api/v1/market/sources', json={'name': 'User evidence', 'provider': 'Internal research', 'source_type': 'user_upload'})
    assert r.status_code == 201, r.text
    return r.json()['id']


def observation(key='r1', value=100):
    return {'external_id': key, 'observed_on': '2026-10-12', 'city': 'Riyadh', 'property_type': 'office',
        'metric': 'rent', 'unit': 'SAR/sqm/year', 'raw_value': '100 SAR', 'normalized_value': value, 'reliability': 60}


@pytest.mark.asyncio
async def test_minimal_property_search_and_link_to_existing_case(client):
    c = await client.post('/api/v1/cases', json={'title': 'Existing case'})
    assert c.status_code == 201, c.text
    p = await property_created(client, case_id=c.json()['id'], location={'city': 'Riyadh', 'plot_number': 'P-42'})
    assert p['property']['financial']['asking_price_sar'] is None
    assert p['revision'] == 1
    assert (await client.get('/api/v1/properties?q=P-42')).json()['total'] == 1
    assert (await client.get('/api/v1/properties?q=%')).json()['total'] == 0
    assert (await client.get('/api/v1/properties?city=Jeddah')).json()['total'] == 0
    assert (await client.get(f"/api/v1/cases/{c.json()['id']}")).status_code == 200


@pytest.mark.asyncio
async def test_revisions_preserve_inputs_and_conflicting_edits_rejected(client):
    p = await property_created(client)
    path = f"/api/v1/properties/{p['id']}"
    changed = {**p['property'], 'name': 'Updated'}
    body = {'property': changed, 'expected_revision': 1, 'reason': 'Confirmed title'}
    r = await client.put(path, json=body)
    assert r.status_code == 200, r.text
    assert r.json()['revision'] == 2
    assert (await client.put(path, json=body)).status_code == 409
    old = (await client.get(path+'/revisions/1')).json()['snapshot']
    assert old['property']['name'] == p['property']['name']
    assert old['outputs'] is None and old['calculation_status'] == 'not_calculated'
    assert len((await client.get(path+'/revisions')).json()) == 2


@pytest.mark.asyncio
async def test_assumption_override_zero_and_history(client):
    p = await property_created(client)
    path = f"/api/v1/properties/{p['id']}"
    a = {'name': 'Vacancy', 'value': 0.1, 'unit': 'ratio', 'category': 'income', 'source': 'User input',
         'as_of': '2026-10-25', 'status': 'user_input', 'user_override': 0, 'notes': 'Signed full occupancy'}
    body = {'expected_revision': 1, 'reason': 'Review lease', 'assumption': a}
    r = await client.put(path+'/assumptions/vacancy', json=body)
    assert r.status_code == 200, r.text
    assert r.json()['assumptions']['vacancy']['effective_value'] == 0
    assert r.json()['revision'] == 2
    assert (await client.get(path+'/revisions/1')).json()['snapshot']['assumptions'] == {}
    assert (await client.get(path+'/revisions/2')).json()['snapshot']['assumptions']['vacancy']['value'] == 0.1
    assert (await client.put(path+'/assumptions/vacancy', json=body)).status_code == 409
    a['notes'] = None; body['expected_revision'] = 2
    assert (await client.put(path+'/assumptions/vacancy', json=body)).status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize('extra', [
    {'land': {'area_sqm': -10}}, {'building': {'occupancy_ratio': 1.1}},
    {'location': {'latitude': 24.7}}, {'location': {'latitude': 100, 'longitude': 46}},
    {'planning': {'setbacks_m': {'front': -1}}}, {'financial': {'asking_price_sar': -1}},
    {'currency': 'USD'}, {'name': '  '}, {'unexpected': 'silently discard?'}])
async def test_invalid_property_rejected(client, extra):
    r = await client.post('/api/v1/properties', json={'name': 'Test', **extra})
    assert r.status_code == 422, r.text
    assert (await client.get('/api/v1/properties')).json()['total'] == 0


@pytest.mark.asyncio
async def test_missing_case_does_not_leave_property(client):
    r = await client.post('/api/v1/properties', json={'name': 'Test', 'case_id': str(uuid.uuid4())})
    assert r.status_code == 404
    assert (await client.get('/api/v1/properties')).json()['total'] == 0


@pytest.mark.asyncio
async def test_market_import_idempotency_and_atomic_conflict(client):
    s = await source_created(client); path = f'/api/v1/market/sources/{s}/observations'
    body = {'observations': [observation()]}
    r = await client.post(path, json=body)
    assert r.status_code == 201, r.text
    assert r.json() == {'inserted': 1, 'duplicates': 0}
    assert (await client.post(path, json=body)).json() == {'inserted': 0, 'duplicates': 1}
    conflict = await client.post(path, json={'observations': [observation('r2'), observation(value=200)]})
    assert conflict.status_code == 409, conflict.text
    rows = (await client.get('/api/v1/market/observations')).json()
    assert rows['total'] == 1
    assert rows['data'][0]['raw_value'] == '100 SAR'
    assert rows['data'][0]['source'] == 'User evidence'
    assert (await client.get('/api/v1/market/observations?city=Jeddah')).json()['total'] == 0


@pytest.mark.asyncio
async def test_csv_ingestion_and_invalid_rows_are_atomic(client):
    s = await source_created(client); path = f'/api/v1/market/sources/{s}/csv'
    header = 'external_id,observed_on,city,property_type,metric,unit,raw_value,normalized_value,reliability\n'
    valid = 'a,2026-10-12,الرياض,office,rent,SAR/sqm/year,100 SAR,100,70\n'
    r = await client.post(path, files={'file': ('rent.csv', header+valid, 'text/csv')})
    assert r.status_code == 201, r.text
    assert (await client.post(path, files={'file': ('rent.csv', header+valid, 'text/csv')})).json()['duplicates'] == 1
    bad = 'b,invalid-date,Riyadh,office,rent,SAR/sqm/year,100,100,200\n'
    assert (await client.post(path, files={'file': ('bad.csv', header+valid+bad, 'text/csv')})).status_code == 422
    assert (await client.get('/api/v1/market/observations')).json()['total'] == 1
    assert (await client.post(path, files={'file': ('bad.csv', 'price\n100', 'text/csv')})).status_code == 422


@pytest.mark.asyncio
async def test_owner_scope_and_viewer_write_restrictions(client):
    p = await property_created(client); s = await source_created(client)
    other = uuid.uuid4()
    async with async_session() as db:
        db.add(User(id=other, email='other@test.local', name='Other', role='viewer'))
        await db.commit()
    headers = {'Authorization': 'Bearer '+create_token(str(other), 'other@test.local', 'admin')}
    # Role comes from DB, not the token's role claim.
    assert (await client.get('/api/v1/properties', headers=headers)).json()['total'] == 0
    assert (await client.get(f"/api/v1/properties/{p['id']}", headers=headers)).status_code == 404
    assert (await client.get(f"/api/v1/properties/{p['id']}/revisions", headers=headers)).status_code == 404
    assert (await client.post('/api/v1/properties', headers=headers, json={'name': 'No'})).status_code == 403
    assert (await client.get('/api/v1/market/sources', headers=headers)).json() == []
    assert (await client.post(f'/api/v1/market/sources/{s}/observations', headers=headers, json={'observations': [observation()]})).status_code == 403
    assert (await client.get('/api/v1/properties', headers={'Authorization': 'invalid'})).status_code == 401
