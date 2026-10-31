"""The Esri key must stay server-side: never in responses, errors or logs."""
import logging
import pytest
import httpx
from httpx import ASGITransport, AsyncClient
from api.app.main import app
from api.app.database import Base, engine
from api.app.routers import imagery
from api.app.services import secret_store

SECRET = 'TESTKEY_not_a_real_key_0123456789'


@pytest.fixture
async def client():
    async with engine.begin() as conn: await conn.run_sync(Base.metadata.create_all)
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as c: yield c
    async with engine.begin() as conn: await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def esri(monkeypatch):
    """Fake Esri; records outgoing requests. No network and no Keychain access."""
    calls = []
    state = {'static_ok': False, 'accept': True}
    def handler(request):
        calls.append(request)
        url = str(request.url)
        if not state['accept']:
            return httpx.Response(200, json={'error': {'code': 498, 'message': f'Invalid token {url}'}})
        if 'World_Imagery/MapServer/tile' in url:
            return httpx.Response(200, content=b'jpeg', headers={'content-type': 'image/jpeg'})
        if 'World_Imagery/MapServer' in url:
            return httpx.Response(200, json={'tileInfo': {}, 'copyrightText': 'Source: Esri test'})
        if 'static-basemap-tiles-service' in url:
            return httpx.Response(200, json={'styles': []}) if state['static_ok'] else httpx.Response(403, json={'error': {'code': 403}})
        if 'findAddressCandidates' in url:
            return httpx.Response(200, json={'candidates': [{'address': 'Al Olaya, Riyadh', 'score': 99, 'location': {'x': 46.68, 'y': 24.69}, 'attributes': {'Addr_type': 'Locality'}}]})
        return httpx.Response(404)
    monkeypatch.setattr(imagery, '_client', httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    monkeypatch.setattr(imagery, '_status', None)
    monkeypatch.setattr(imagery, 'read_arcgis_key', lambda: SECRET)
    return calls, state


@pytest.mark.asyncio
async def test_no_key_offers_only_the_standard_map(client, monkeypatch):
    monkeypatch.setattr(imagery, '_status', None)
    monkeypatch.setattr(imagery, 'read_arcgis_key', lambda: None)
    body = (await client.get('/api/v1/imagery/status')).json()
    assert body['configured'] is False and body['provider'] == 'osm'
    assert body['capabilities'] == {'satellite': False, 'hybrid': False, 'roadmap': True, 'terrain': False, 'geocoding': False}
    assert (await client.get('/api/v1/imagery/tiles/imagery/1/0/0')).status_code == 503


@pytest.mark.asyncio
async def test_capabilities_follow_the_keys_real_permissions(client, esri):
    _, state = esri
    body = (await client.get('/api/v1/imagery/status')).json()
    assert body['capabilities']['satellite'] and not body['capabilities']['hybrid'] and not body['capabilities']['terrain']
    assert body['attribution'] == 'Source: Esri test' and SECRET not in str(body)
    state['static_ok'] = True
    imagery._status = None
    body = (await client.get('/api/v1/imagery/status')).json()
    assert body['capabilities']['hybrid'] and body['capabilities']['terrain'] and body['esri_streets']


@pytest.mark.asyncio
async def test_tile_proxy_hides_the_key_and_only_allows_known_layers(client, esri):
    calls, _ = esri
    r = await client.get('/api/v1/imagery/tiles/imagery/13/3515/5158')
    assert r.status_code == 200 and r.content == b'jpeg' and r.headers['content-type'] == 'image/jpeg'
    assert SECRET not in str(r.headers) and r.headers['cache-control'].startswith('private')
    assert '/tile/13/3515/5158' in str(calls[-1].url), 'Esri raster paths are z/y/x'
    assert (await client.get('/api/v1/imagery/tiles/evil/1/0/0')).status_code == 404
    assert (await client.get('/api/v1/imagery/tiles/imagery/1/5/0')).status_code == 404
    assert (await client.get('/api/v1/imagery/tiles/imagery/99/0/0')).status_code == 422


@pytest.mark.asyncio
async def test_upstream_failures_never_leak_the_key(client, monkeypatch, esri, caplog):
    def boom(request):
        raise httpx.ConnectError(f'failed {request.url}')
    monkeypatch.setattr(imagery, '_client', httpx.AsyncClient(transport=httpx.MockTransport(boom)))
    with caplog.at_level(logging.INFO):
        r = await client.get('/api/v1/imagery/tiles/imagery/1/0/0')
        g = await client.get('/api/v1/imagery/geocode', params={'q': 'Olaya'})
    assert r.status_code == 502 and g.status_code == 502
    assert SECRET not in r.text + g.text and SECRET not in caplog.text
    # Esri JSON errors that echo the URL with HTTP 200 are not passed through either.
    _, state = esri
    state['accept'] = False
    monkeypatch.setattr(imagery, '_client', httpx.AsyncClient(transport=httpx.MockTransport(lambda q: httpx.Response(200, json={'error': {'message': str(q.url)}}))))
    r = await client.get('/api/v1/imagery/tiles/imagery/1/0/0')
    assert r.status_code == 502 and SECRET not in r.text


@pytest.mark.asyncio
async def test_geocode_returns_latitude_longitude(client, esri):
    body = (await client.get('/api/v1/imagery/geocode', params={'q': 'Olaya'})).json()
    assert body['data'][0]['coordinates'] == [24.69, 46.68] and body['data'][0]['precision'] == 'Locality'
    assert SECRET not in str(body)


@pytest.mark.asyncio
async def test_saving_a_key_validates_stores_and_never_returns_it(client, esri, monkeypatch):
    calls, state = esri
    stored = []
    monkeypatch.setattr(imagery, 'store_arcgis_key', stored.append)
    ok = await client.put('/api/v1/imagery/key', json={'key': 'NEWKEY_not_a_real_key_012345678'})
    assert ok.status_code == 200 and stored == ['NEWKEY_not_a_real_key_012345678'] and 'NEWKEY' not in ok.text
    stored.clear(); state['accept'] = False
    bad = await client.put('/api/v1/imagery/key', json={'key': 'BADKEY_not_a_real_key_012345678'})
    assert bad.status_code == 422 and not stored and 'BADKEY' not in bad.text


def test_key_shape_blocks_keychain_command_injection(monkeypatch):
    for bad in ['short', 'abc"; delete-keychain "x' + 'a' * 20, 'a' * 20 + '\nb']:
        with pytest.raises(secret_store.SecretStoreError):
            secret_store.store_arcgis_key(bad)


def test_environment_override_wins(monkeypatch):
    monkeypatch.setenv('MIZAN_ARCGIS_API_KEY', ' from-env ')
    assert secret_store.read_arcgis_key() == 'from-env'
