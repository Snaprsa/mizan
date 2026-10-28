"""Browser-only map fixture test. Intercepts evidence/tiles; never writes market records.
Run with the built app on :3100 and the Mac's Python Playwright/Chromium.
"""
import base64
import json
from playwright.sync_api import sync_playwright


def record(key, coords, kind='listing'):
    return {'id': key, 'entity_id': key, 'kind': kind, 'title': 'UI test fixture '+key,
        'city': 'Riyadh', 'district': 'Test district', 'property_type': 'land',
        'coordinates': coords, 'date': '2026-10-12', 'date_basis': 'listing_date',
        'evidence_type': 'listing_asking', 'status': 'draft', 'price': 1000000,
        'currency': 'SAR', 'area_sqm': 500, 'price_per_sqm': 2000, 'source': 'UI test fixture, not market evidence',
        'reliability_score': 2, 'case_id': None, 'href': '/properties'}


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1560, 'height': 1100})
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    # Do not repeatedly request real OSM tiles while testing pan/zoom/clustering.
    pixel = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=')
    page.route('https://tile.openstreetmap.org/**', lambda route: route.fulfill(content_type='image/png', body=pixel))
    records = [record('one', [24.7, 46.7]), record('two', [24.7, 46.7], 'transaction'),
               record('three', [24.75, 46.75], 'property'), record('missing', None)]
    payload = {'data': records, 'total': 4, 'truncated': False,
               'available': {'cities': ['Riyadh'], 'property_types': ['land']},
               'counts': {'mapped': 3, 'missing_location': 1, 'transactions': 1, 'listings': 2, 'properties': 1},
               'scope': 'UI test fixture'}
    page.route('**/api/v1/map/records?*', lambda route: route.fulfill(json=payload))
    page.goto('http://127.0.0.1:3100/map')
    page.locator('[data-record-id]').first.wait_for()
    page.locator('.leaflet-marker-icon').filter(has_text='2').click()
    page.get_by_role('button', name='Clear group', exact=True).wait_for()
    assert page.locator('[data-record-id]').count() == 2
    page.get_by_role('button', name='Clear group', exact=True).click()
    assert page.locator('[data-record-id]').count() == 4
    page.locator('[data-record-id="one"]').click()
    page.get_by_role('link', name='Open in Google Maps', exact=False).wait_for()
    assert 'query=24.7%2C46.7' in page.get_by_role('link', name='Open in Google Maps', exact=False).get_attribute('href')
    page.get_by_role('button', name='Clear selected record').click()
    page.get_by_label('Recorded transactions', exact=True).uncheck()
    assert page.locator('[data-record-id]').count() == 3
    page.get_by_label('Only records in current map view').check()
    assert page.locator('[data-record-id="missing"]').count() == 0
    page.get_by_label('Only records in current map view').uncheck()
    page.locator('[data-record-id="missing"]').click()
    page.get_by_role('link', name='Search area in Google Maps', exact=False).wait_for()
    assert not errors, errors
    print('PASS: clustered marker selection, adjacent group/list selection, Google links, layer filtering and unknown locations; no browser errors. No database writes or OSM tile downloads.')
    browser.close()
