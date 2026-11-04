"""Building outline under a map point, from OpenStreetMap through the public Overpass API (free, ODbL).

Only buildings: no free, authorised source of Saudi land-parcel boundaries is connected, so none is guessed.
An outline is community-mapped and approximate, never a cadastral or legal boundary.
"""
import asyncio
import math
import os
import time
from datetime import datetime, timezone
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from api.app.auth import get_current_user

router = APIRouter(prefix='/footprint', tags=['Map footprints'])
# Public instances are often slow or at capacity, so all are asked at once and the first answer wins.
# MIZAN_OVERPASS_URL adds your own instance.
OVERPASS = [u for u in [os.environ.get('MIZAN_OVERPASS_URL'), 'https://overpass-api.de/api/interpreter',
            'https://maps.mail.ru/osm/tools/overpass/api/interpreter', 'https://overpass.kumi.systems/api/interpreter'] if u]
SEARCH_M = 30        # look this far around the pin
NEAREST_M = 12       # accept an outline the pin misses by at most this much
CACHE_TTL = 86400
SOURCE = 'OpenStreetMap contributors (ODbL), via Overpass API'
_cache: dict[tuple[float, float], tuple[float, dict]] = {}
_client: httpx.AsyncClient | None = None
EARTH_RADIUS_M = 6371008.8


def client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=httpx.Timeout(45, connect=8), headers={'User-Agent': 'Mizan local valuation tool (building outline lookup)'})
    return _client


def geodesic_area_sqm(ring):
    """Spherical polygon area for [lat, lng] rings; the same formula the map uses for drawn outlines."""
    if len(ring) < 3:
        return 0.0
    total = 0.0
    for (lat1, lng1), (lat2, lng2) in zip(ring, ring[1:] + ring[:1]):
        total += math.radians(lng2 - lng1) * (2 + math.sin(math.radians(lat1)) + math.sin(math.radians(lat2)))
    return abs(total * EARTH_RADIUS_M ** 2 / 2)


def contains(ring, lat, lng):
    inside = False
    for (lat1, lng1), (lat2, lng2) in zip(ring, ring[1:] + ring[:1]):
        if (lat1 > lat) != (lat2 > lat) and lng < (lng2 - lng1) * (lat - lat1) / (lat2 - lat1) + lng1:
            inside = not inside
    return inside


def distance_to_edge_m(ring, lat, lng):
    """Metres from the point to the nearest edge, on a local flat projection (fine at building scale)."""
    kx = math.cos(math.radians(lat)) * math.pi * EARTH_RADIUS_M / 180
    ky = math.pi * EARTH_RADIUS_M / 180
    best = math.inf
    for (lat1, lng1), (lat2, lng2) in zip(ring, ring[1:] + ring[:1]):
        ax, ay, bx, by = (lng1 - lng) * kx, (lat1 - lat) * ky, (lng2 - lng) * kx, (lat2 - lat) * ky
        dx, dy = bx - ax, by - ay
        t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(ax + t * dx, ay + t * dy))
    return best


def levels(tags):
    try:
        n = float(str(tags.get('building:levels', '')).strip())
        return int(n) if n.is_integer() and 0 < n <= 200 else None
    except ValueError:
        return None


def pick(elements, lat, lng):
    """The smallest outline containing the pin; otherwise the closest within a few metres."""
    candidates = []
    for e in elements:
        ring = [[p['lat'], p['lon']] for p in e.get('geometry') or []]
        if len(ring) > 3 and ring[0] == ring[-1]:
            ring = ring[:-1]
        if len(ring) < 3:
            continue
        area = geodesic_area_sqm(ring)
        if contains(ring, lat, lng):
            candidates.append((0, area, 0.0, e, ring))
        else:
            gap = distance_to_edge_m(ring, lat, lng)
            if gap <= NEAREST_M:
                candidates.append((1, gap, gap, e, ring))
    if not candidates:
        return None
    match, _, gap, e, ring = min(candidates, key=lambda c: (c[0], c[1]))
    tags = e.get('tags') or {}
    return {'found': True, 'kind': 'building', 'match': 'contains' if match == 0 else 'nearest', 'distance_m': round(gap, 1),
            'ring': ring, 'area_sqm': round(geodesic_area_sqm(ring), 1), 'levels': levels(tags), 'building': tags.get('building'),
            'name': tags.get('name'), 'osm': {'type': e['type'], 'id': e['id'], 'url': f"https://www.openstreetmap.org/{e['type']}/{e['id']}"}}


async def ask(url, query):
    try:
        response = await client().post(url, data={'data': query})
        return response.json().get('elements') or [] if response.status_code == 200 else None
    except (httpx.HTTPError, ValueError):
        return None


async def first_answer(query):
    tasks = [asyncio.create_task(ask(url, query)) for url in OVERPASS]
    try:
        for done in asyncio.as_completed(tasks):
            elements = await done
            if elements is not None:
                return elements
        return None
    finally:
        for t in tasks:
            t.cancel()


@router.get('')
async def footprint(lat: float = Query(ge=-90, le=90), lng: float = Query(ge=-180, le=180), user=Depends(get_current_user)):
    key = (round(lat, 5), round(lng, 5))
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < CACHE_TTL:
        return hit[1]
    query = f'[out:json][timeout:15];way(around:{SEARCH_M},{lat},{lng})["building"];out geom tags;'
    elements = await first_answer(query)
    if elements is None:
        raise HTTPException(503, 'OpenStreetMap is busy right now. Try again in a minute, or trace the outline yourself.')
    found = pick(elements, lat, lng)
    result = {**(found or {'found': False, 'reason': 'No building is mapped at this spot in OpenStreetMap.'}),
              'source': SOURCE, 'fetched_at': datetime.now(timezone.utc).date().isoformat(),
              'notice': 'Community-mapped outline. Approximate, not a cadastral or legal boundary. Land plots are not available from any connected source.'}
    _cache[key] = (time.time(), result)
    return result
