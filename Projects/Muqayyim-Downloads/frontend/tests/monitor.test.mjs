import test from 'node:test';
import assert from 'node:assert/strict';
import { ageLabel, assetsCsv, errorText, inRange, pct, sar, triggerLabel } from '../src/lib/monitor.ts';

test('money is compact and missing stays visibly missing, never zero', () => {
  assert.equal(sar(9_380_000_000), 'SAR 9.38bn');
  assert.equal(sar(53_200_000), 'SAR 53.2m');
  assert.equal(sar(280_000_000, true), '+SAR 280m');
  assert.equal(sar(-1_500_000), '−SAR 1.5m');
  assert.equal(sar(null), '—');
  assert.equal(sar(undefined, true), '—');
  assert.equal(sar(0), 'SAR 0');
});
test('percentages carry a sign unless asked not to', () => {
  assert.equal(pct(3.08, 2), '+3.08%');
  assert.equal(pct(-11.2), '−11.2%');
  assert.equal(pct(51.8, 1, false), '51.8%');
  assert.equal(pct(null), '—');
});
test('history ranges cut on the window and All keeps everything', () => {
  const points = ['2023-01-31', '2025-10-31', '2026-05-31', '2026-09-30', '2026-10-31'].map(date => ({ date }));
  assert.deepEqual(inRange(points, '1m', '2026-10-31').map(p => p.date), ["2026-10-31"]);
  assert.equal(inRange(points, '6m', '2026-10-31').length, 3);
  assert.equal(inRange(points, '1y', '2026-10-31').length, 4);
  assert.equal(inRange(points, 'all', '2026-10-31').length, 5);
});
test('age labels read naturally and unknown dates say so', () => {
  assert.equal(ageLabel('2026-10-31', '2026-10-31'), 'Today');
  assert.equal(ageLabel('2026-10-27', '2026-10-31'), '4 days ago');
  assert.equal(ageLabel('2026-04-30', '2026-10-31'), '6 months ago');
  assert.equal(ageLabel(null, '2026-10-31'), 'Unknown');
});
test('CSV escapes quotes and keeps blanks blank', () => {
  const row = { name: 'Tower "A"', city: 'Riyadh', property_type: 'office', ownership_pct: 100, value: 10, low: null, high: null, official_value: null, official_on: null, change_vs_official_pct: null, confidence: 'low', divergence_pct: null, ltv_pct: null, priority: { band: 'high' }, origin: 'demo' };
  const [, line] = assetsCsv([row]).split('\n');
  assert.ok(line.startsWith('"Tower ""A""","Riyadh"'));
  assert.ok(line.endsWith('"","low","","","high","demo"'));
});
test('trigger labels and API errors are readable', () => {
  assert.equal(triggerLabel('new_comparable'), 'New comparable sale');
  assert.equal(triggerLabel('something_new'), 'Something new');
  assert.equal(errorText(new Error('{"detail":"Portfolio not found"}')), 'Portfolio not found');
  assert.equal(errorText(new Error('plain')), 'plain');
});
