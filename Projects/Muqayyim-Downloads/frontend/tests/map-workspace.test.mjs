import test from 'node:test';
import assert from 'node:assert/strict';
import { toGeoJSONPosition, fromGeoJSONPosition, polygonFromLatLngs, latLngsFromPolygon, haversineMeters,
  geodesicAreaSqm, circleRing, pointInRing, inSearchArea, parseCoordinates, destination } from '../src/lib/geo.ts';
import { clusterProjected } from '../src/lib/map-clustering.ts';
import { evidenceSummaries, activityCounts, applyEvidenceFilters, EMPTY_FILTERS, sourceLabel } from '../src/lib/map-evidence.ts';
import { sanitizeState, defaultState, loadState, saveState, STORAGE_KEY } from '../src/lib/map-workspace-state.ts';

const near = (a, b, tolerance) => assert.ok(Math.abs(a - b) <= tolerance, `${a} not within ${tolerance} of ${b}`);

test('GeoJSON is [lng, lat] and Mizan/Leaflet records are [lat, lng]', () => {
  const riyadh = [24.7136, 46.6753];
  assert.deepEqual(toGeoJSONPosition(riyadh), [46.6753, 24.7136]);
  assert.deepEqual(fromGeoJSONPosition(toGeoJSONPosition(riyadh)), riyadh);
  const square = [[24.70, 46.70], [24.70, 46.71], [24.71, 46.71], [24.71, 46.70]];
  const polygon = polygonFromLatLngs(square);
  assert.equal(polygon.type, 'Polygon');
  assert.deepEqual(polygon.coordinates[0][0], [46.70, 24.70]);
  assert.deepEqual(polygon.coordinates[0].at(-1), polygon.coordinates[0][0], 'ring is closed');
  assert.deepEqual(latLngsFromPolygon(polygon), square);
  assert.throws(() => polygonFromLatLngs(square.slice(0, 2)));
});

test('geodesic distance and area are approximately correct at Saudi latitudes', () => {
  // One degree of latitude ≈ 111.2 km.
  near(haversineMeters([24, 46], [25, 46]), 111195, 50);
  // 0.01° × 0.01° square near Riyadh ≈ 1112 m × 1011 m.
  const square = [[24.70, 46.70], [24.70, 46.71], [24.71, 46.71], [24.71, 46.70]];
  near(geodesicAreaSqm(square), 1112 * 1011, 1112 * 1011 * 0.01);
  // A 1 km circle approximates π km².
  near(geodesicAreaSqm(circleRing([24.7, 46.7], 1000, 256)), Math.PI * 1e6, Math.PI * 1e6 * 0.005);
  near(haversineMeters([24.7, 46.7], destination([24.7, 46.7], 90, 2500)), 2500, 1);
});

test('area membership honours radius and polygon', () => {
  const ring = [[24.70, 46.70], [24.70, 46.71], [24.71, 46.71], [24.71, 46.70]];
  assert.equal(pointInRing([24.705, 46.705], ring), true);
  assert.equal(pointInRing([46.705, 24.705], ring), false, 'swapped point is outside');
  assert.equal(inSearchArea([24.705, 46.705], { kind: 'polygon', ring }), true);
  assert.equal(inSearchArea([24.7, 46.7], { kind: 'radius', center: [24.7, 46.71], radius_m: 1100 }), true);
  assert.equal(inSearchArea([24.7, 46.7], { kind: 'radius', center: [24.7, 46.73], radius_m: 1100 }), false);
  assert.equal(inSearchArea(null, { kind: 'polygon', ring }), false, 'missing coordinates are never inside');
});

test('coordinate entry never swaps silently', () => {
  assert.deepEqual(parseCoordinates('24.7136, 46.6753'), { ok: true, value: [24.7136, 46.6753] });
  assert.deepEqual(parseCoordinates('24.7136 46.6753'), { ok: true, value: [24.7136, 46.6753] });
  const swapped = parseCoordinates('46.6753, 24.7136');
  assert.equal(swapped.ok, false); assert.deepEqual(swapped.swapped, [24.7136, 46.6753]);
  const big = parseCoordinates('146.1, 24.1');
  assert.equal(big.ok, false);
  assert.equal(parseCoordinates('51.5, -0.12').warning, 'This location is outside Saudi Arabia.');
  assert.equal(parseCoordinates('King Fahd Road'), null, 'text is not coordinates');
});

test('clustering handles a 10,000-point synthetic fixture quickly and loses no records', () => {
  const items = Array.from({ length: 10000 }, (_, i) => ({ record: { id: `fixture-${i}` },
    coordinates: [24.5 + (i % 100) * 0.005, 46.5 + Math.floor(i / 100) * 0.005], x: (i % 100) * 9, y: Math.floor(i / 100) * 9 }));
  const started = performance.now();
  const clusters = clusterProjected(items, 56);
  const elapsed = performance.now() - started;
  assert.equal(clusters.reduce((n, c) => n + c.records.length, 0), 10000);
  assert.ok(clusters.length < 500, `expected clustering, got ${clusters.length}`);
  assert.ok(elapsed < 250, `clustering took ${elapsed} ms`);
  assert.equal(clusterProjected([{ record: 1, coordinates: [0, 0], x: NaN, y: 0 }]).length, 0);
});

const rec = (over) => ({ id: over.id || Math.random().toString(), kind: 'transaction', price_per_sqm: 2000, currency: 'SAR',
  date: '2026-10-01', status: 'active', source: 'https://www.example.com/x', reliability_score: 4, coordinates: [24.7, 46.7], title: 't', ...over });

test('summaries never pool sales, listings or observations and require a minimum sample', () => {
  const records = [rec({ price_per_sqm: 1000 }), rec({ price_per_sqm: 2000 }), rec({ price_per_sqm: 3000 }),
    rec({ kind: 'listing', price_per_sqm: 9000 }), rec({ kind: 'market', metric: 'rent', unit: 'SAR/m²/year', value: 500, title: 'Rent' })];
  const s = evidenceSummaries(records);
  const sales = s.find(x => x.key === 'transaction:SAR');
  assert.equal(sales.median, 2000); assert.equal(sales.n, 3); assert.equal(sales.unit, 'SAR/m²');
  const listings = s.find(x => x.key === 'listing:SAR');
  assert.equal(listings.insufficient, true); assert.equal(listings.median, null);
  assert.equal(s.find(x => x.key.startsWith('market:')).unit, 'SAR/m²/year');
});

test('activity windows and evidence filters', () => {
  const records = [rec({ date: '2026-10-20' }), rec({ date: '2026-06-01' }), rec({ kind: 'listing', date: '2026-10-25' }), rec({ date: null })];
  const [d30, d90, d365] = activityCounts(records, '2026-10-28');
  assert.deepEqual([d30.transactions, d30.listings, d90.transactions, d365.transactions], [1, 1, 1, 2]);
  assert.equal(sourceLabel('https://www.example.com/a'), 'example.com');
  assert.equal(applyEvidenceFilters(records, { ...EMPTY_FILTERS, minReliability: 5 }).length, 0);
  assert.equal(applyEvidenceFilters([rec({ reliability_score: null })], { ...EMPTY_FILTERS, minReliability: 1 }).length, 0, 'unscored is not reliable');
});

test('persisted workspace state is validated and survives round trips', () => {
  const state = { ...defaultState(), basemap: 'satellite', camera: { center: [24.7, 46.7], zoom: 15, heading: 0, tilt: 0 },
    subject: { coordinates: [24.7, 46.7], source: 'geocoded', precision: 'approximate', confirmed: true },
    searchArea: { kind: 'polygon', ring: [[24.7, 46.7], [24.71, 46.7], [24.71, 46.71]] }, selectedId: 'comparable:1' };
  const store = new Map();
  const storage = { getItem: k => store.get(k) ?? null, setItem: (k, v) => store.set(k, v) };
  saveState(storage, state);
  assert.deepEqual(loadState(storage), state);
  store.set(STORAGE_KEY, '{not json');
  assert.deepEqual(loadState(storage), defaultState());
  const hostile = sanitizeState({ version: 1, basemap: 'scraped-tiles', camera: { center: [200, 1], zoom: 3 },
    subject: { coordinates: [24.7, 46.7], precision: 'cadastral' }, searchArea: { kind: 'radius', center: [24, 46], radius_m: -5 } });
  assert.equal(hostile.basemap, 'hybrid'); assert.equal(hostile.camera, null); assert.equal(hostile.searchArea, null);
  assert.equal(hostile.subject.precision, 'approximate', 'unknown precision is downgraded, never upgraded');
  assert.equal(hostile.subject.confirmed, false);
  assert.deepEqual(sanitizeState({ version: 2 }), defaultState());
});

test('Esri provider: tile URL shape and geocode x/y become [latitude, longitude]', async () => {
  const { esriTileUrl, esriGeocode, ESRI_STYLES } = await import('../src/lib/map-provider.ts');
  assert.equal(esriTileUrl('arcgis/imagery', 'k&y'),
    'https://static-map-tiles-api.arcgis.com/arcgis/rest/services/static-basemap-tiles-service/v1/arcgis/imagery/static/tile/{z}/{y}/{x}?token=k%26y');
  assert.equal(ESRI_STYLES.hybrid.overlay, 'arcgis/imagery/labels');
  const realFetch = globalThis.fetch;
  globalThis.fetch = async url => ({ json: async () => (String(url).includes('countryCode=SAU')
    ? { candidates: [{ address: 'Olaya St, Riyadh', location: { x: 46.68, y: 24.69 }, score: 98, attributes: { Addr_type: 'StreetName' } }] } : {}) });
  try {
    const [r] = await esriGeocode('Olaya', 'key');
    assert.deepEqual(r.coordinates, [24.69, 46.68]);
    assert.equal(r.precision, 'StreetName');
    globalThis.fetch = async () => ({ json: async () => ({ error: { code: 498, message: 'Invalid token' } }) });
    await assert.rejects(esriGeocode('Olaya', 'bad'), /not enabled for this Esri key/);
  } finally { globalThis.fetch = realFetch; }
});
