"""Server-side Esri imagery. The API key stays on this server: browsers only see /api/v1/imagery URLs."""
import logging
import time
import httpx
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from pydantic import Field
from api.app.auth import get_current_user
from api.app.schemas.foundation import StrictModel
from api.app.services.foundation import can_write
from api.app.services.secret_store import SecretStoreError, delete_arcgis_key, read_arcgis_key, store_arcgis_key

# httpx logs full request URLs at INFO, and Esri's raster server only accepts the key in the URL.
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)

router = APIRouter(prefix='/imagery', tags=['Map imagery'])
RASTER = 'https://ibasemaps-api.arcgis.com/arcgis/rest/services/World_Imagery/MapServer'
STATIC = 'https://static-map-tiles-api.arcgis.com/arcgis/rest/services/static-basemap-tiles-service/v1/'
GEOCODE = 'https://geocode-api.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates'
STATIC_LAYERS = {'labels': 'arcgis/imagery/labels', 'streets': 'arcgis/streets', 'outdoor': 'arcgis/outdoor'}
LAYERS = {'imagery', *STATIC_LAYERS}
STATUS_TTL = 300
HEADERS = {'Referer': 'http://127.0.0.1:3100/'}  # Satisfies a referrer-restricted key from this local app.
_status: tuple[float, dict] | None = None
_client: httpx.AsyncClient | None = None


class KeyInput(StrictModel):
    key: str = Field(min_length=20, max_length=4000)


def client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=20, headers=HEADERS)
    return _client


async def esri_json(url: str, key: str, params: dict | None = None) -> dict:
    """Never let transport errors or Esri bodies carry the key-bearing URL to callers."""
    try:
        response = await client().get(url, params={'f': 'json', 'token': key, **(params or {})})
        return response.json()
    except (httpx.HTTPError, ValueError):
        return {'error': {'code': 0, 'message': 'unreachable'}}


async def esri_tile(url: str, key: str) -> tuple[bytes, str]:
    try:
        response = await client().get(url, params={'token': key})
    except httpx.HTTPError:
        raise HTTPException(502, 'Esri could not be reached') from None
    kind = response.headers.get('content-type', '')
    if response.status_code != 200 or not kind.startswith('image/'):  # Esri can send JSON errors with HTTP 200.
        raise HTTPException(502, 'Esri did not return a map tile')
    return response.content, kind


async def probe(key: str) -> dict:
    imagery, static, copyright_text = await _probe_services(key)
    message = None
    if not imagery:
        message = 'Esri didn’t accept this key for satellite imagery. Check its basemap permission.'
    return {'configured': True, 'provider': 'esri' if imagery else 'osm', 'message': message,
            'capabilities': {'satellite': imagery, 'hybrid': imagery and static, 'roadmap': True, 'terrain': static, 'geocoding': True},
            'esri_streets': static, 'attribution': copyright_text}


async def _probe_services(key: str):
    info = await esri_json(RASTER, key)
    imagery = 'error' not in info and 'tileInfo' in info
    static = 'error' not in await esri_json(STATIC + 'self', key)
    return imagery, static, info.get('copyrightText') if imagery else None


@router.get('/status')
async def status(user=Depends(get_current_user)):
    """What this server can offer. Contains no key material."""
    global _status
    key = read_arcgis_key()
    if not key:
        return {'configured': False, 'provider': 'osm', 'message': None, 'esri_streets': False, 'attribution': None,
                'capabilities': {'satellite': False, 'hybrid': False, 'roadmap': True, 'terrain': False, 'geocoding': False}}
    if _status and time.monotonic() - _status[0] < STATUS_TTL:
        return _status[1]
    result = await probe(key)
    _status = (time.monotonic(), result)
    return result


@router.get('/tiles/{layer}/{z}/{y}/{x}')
async def tile(layer: str, z: int = Path(ge=0, le=23), y: int = Path(ge=0), x: int = Path(ge=0), user=Depends(get_current_user)):
    if layer not in LAYERS:
        raise HTTPException(404, 'Unknown imagery layer')
    if x >= 2 ** z or y >= 2 ** z:
        raise HTTPException(404, 'Tile outside the map')
    key = read_arcgis_key()
    if not key:
        raise HTTPException(503, 'No Esri key is configured')
    url = f'{RASTER}/tile/{z}/{y}/{x}' if layer == 'imagery' else f'{STATIC}{STATIC_LAYERS[layer]}/static/tile/{z}/{y}/{x}'
    content, kind = await esri_tile(url, key)
    return Response(content, media_type=kind, headers={'Cache-Control': 'private, max-age=3600'})


@router.get('/geocode')
async def geocode(q: str = Query(min_length=3, max_length=200), user=Depends(get_current_user)):
    """Saudi address search (not stored). Results only move the map; the user places the pin."""
    key = read_arcgis_key()
    if not key:
        raise HTTPException(503, 'No Esri key is configured')
    body = await esri_json(GEOCODE, key, {'singleLine': q, 'countryCode': 'SAU', 'maxLocations': 6, 'outFields': 'Addr_type'})
    if 'error' in body:
        raise HTTPException(502, 'Address search isn’t available for this key')
    # Esri x/y are longitude/latitude; Mizan coordinates are [latitude, longitude].
    return {'data': [{'label': c['address'], 'coordinates': [c['location']['y'], c['location']['x']], 'score': c.get('score'),
                      'precision': (c.get('attributes') or {}).get('Addr_type') or 'unknown'} for c in body.get('candidates', [])]}


@router.put('/key')
async def save_key(body: KeyInput, user=Depends(get_current_user)):
    """Checks a key with Esri, then stores it in the Keychain. It is never returned."""
    global _status
    can_write(user)
    key = body.key.strip()
    result = await probe(key)
    if result['provider'] != 'esri':
        raise HTTPException(422, 'Esri rejected this key, or it has no basemap permission.')
    try:
        store_arcgis_key(key)
    except SecretStoreError as exc:
        raise HTTPException(422, str(exc)) from None
    _status = (time.monotonic(), result)
    return result


@router.delete('/key')
async def remove_key(user=Depends(get_current_user)):
    global _status
    can_write(user)
    delete_arcgis_key()
    _status = None
    return {'configured': False}
