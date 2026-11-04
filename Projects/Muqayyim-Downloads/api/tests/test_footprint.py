"""Building outline lookup: real geometry or nothing, never a guessed parcel. No network in tests."""
import math
import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from api.app.main import app
from api.app.database import Base, engine
from api.app.routers import footprint

# A 20 m x 30 m building around 24.7136, 46.6753, closed as OSM returns it.
LAT, LNG = 24.7136, 46.6753
DLAT, DLNG = 20 / 111195, 30 / (111195 * math.cos(math.radians(LAT)))
SQUARE = [(LAT - DLAT / 2, LNG - DLNG / 2), (LAT - DLAT / 2, LNG + DLNG / 2), (LAT + DLAT / 2, LNG + DLNG / 2), (LAT + DLAT / 2, LNG - DLNG / 2)]
BUILDING = {'type': 'way', 'id': 42, 'tags': {'building': 'yes', 'building:levels': '4'},
            'geometry': [{'lat': a, 'lon': b} for a, b in SQUARE + SQUARE[:1]]}


@pytest.fixture
async def client():
    async with engine.begin() as conn: await conn.run_sync(Base.metadata.create_all)
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as c: yield c
    async with engine.begin() as conn: await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def overpass(monkeypatch):
    state = {'elements': [BUILDING], 'status': 200, 'calls': 0}
    def handler(request):
        state['calls'] += 1
        return httpx.Response(state['status'], json={'elements': state['elements']})
    monkeypatch.setattr(footprint, '_client', httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    monkeypatch.setattr(footprint, '_cache', {})
    return state


def test_area_and_containment():
    ring = [list(p) for p in SQUARE]
    assert footprint.geodesic_area_sqm(ring) == pytest.approx(600, rel=0.01)
    assert footprint.contains(ring, LAT, LNG)
    assert not footprint.contains(ring, LAT + DLAT, LNG)


@pytest.mark.asyncio
async def test_pin_inside_a_building_returns_its_outline_area_and_levels(client, overpass):
    r = (await client.get(f'/api/v1/footprint?lat={LAT}&lng={LNG}')).json()
    assert r['found'] and r['match'] == 'contains' and r['levels'] == 4
    assert r['area_sqm'] == pytest.approx(600, rel=0.01) and len(r['ring']) == 4
    assert r['osm']['url'].endswith('/way/42') and 'ODbL' in r['source']
    asked = overpass['calls']
    await client.get(f'/api/v1/footprint?lat={LAT}&lng={LNG}')
    assert overpass['calls'] == asked  # a repeated pin is answered from the cache


@pytest.mark.asyncio
async def test_pin_on_open_ground_finds_nothing_rather_than_guessing(client, overpass):
    far = LAT + 200 / 111195
    r = (await client.get(f'/api/v1/footprint?lat={far}&lng={LNG}')).json()
    assert r['found'] is False and 'reason' in r and 'ring' not in r
    overpass['elements'] = []
    r = (await client.get(f'/api/v1/footprint?lat={LAT}&lng={LNG}')).json()
    assert r['found'] is False


@pytest.mark.asyncio
async def test_a_pin_just_outside_matches_the_nearest_outline(client, overpass):
    near = LAT + DLAT / 2 + 5 / 111195
    r = (await client.get(f'/api/v1/footprint?lat={near}&lng={LNG}')).json()
    assert r['found'] and r['match'] == 'nearest' and 4 <= r['distance_m'] <= 6


@pytest.mark.asyncio
async def test_busy_service_is_reported_plainly(client, overpass):
    overpass['status'] = 429
    r = await client.get(f'/api/v1/footprint?lat={LAT}&lng={LNG}')
    assert r.status_code == 503 and 'busy' in r.json()['detail']
    assert overpass['calls'] == len(footprint.OVERPASS)  # every mirror was tried before giving up
