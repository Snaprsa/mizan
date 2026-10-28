import test from 'node:test';
import assert from 'node:assert/strict';
import { preparedSignature, savedRunMatchesPrepared, valuationSignature } from '../src/lib/valuation-state.ts';

const field = { key:'area_sqm', value:500, source:'Survey', as_of:'2026-10-20', assumption_status:'observed' };
const comp = id => ({ id, price:1000000, area_sqm:500, price_per_sqm:2000, coordinates:[24.7,46.7],
  date:'2026-10-12', currency:'SAR', property_type:'land', source:'Surveyed transaction', status:'active', evidence_type:'transaction_achieved' });
const prepared = () => ({ method:'sales_comparison', as_of:'2026-10-25', radius_km:3, lookback_days:365,
  revision:2, fields:[field], eligible_comparables:[comp('one'),comp('two'),comp('three')], calculation_version:'mizan.map-workflow.1' });
const run = () => ({ method:'sales_comparison', data_date:'2026-10-25', property_revision:2, inputs:[field],
  property:{ analysis:{radius_km:3,lookback_days:365} }, comparables:[comp('one'),comp('two'),comp('three')],
  outputs:{calculation_version:'mizan.map-workflow.1'} });

test('unchanged saved evidence matches; response order does not matter', () => {
  const p=prepared();p.eligible_comparables.reverse();assert.equal(savedRunMatchesPrepared(p,run()),true);
});
test('changed comparable values invalidate a saved run without a property revision change', () => {
  const p=prepared();p.eligible_comparables[0].price=2000000;assert.equal(savedRunMatchesPrepared(p,run()),false);
});
test('changed location, source date or source invalidate the saved evidence snapshot', () => {
  for(const [key,value] of [['coordinates',[24.72,46.72]],['date','2026-10-20'],['source','Corrected deed']]) {
    const p=prepared();p.eligible_comparables[0][key]=value;assert.equal(savedRunMatchesPrepared(p,run()),false);
  }
});
test('a changed calculation version cannot be labelled current', () => {
  const p=prepared();p.calculation_version='mizan.map-workflow.2';assert.equal(savedRunMatchesPrepared(p,run()),false);
});
test('legacy or incomplete runs remain accessible but are not called current', () => {
  const r=run();delete r.inputs;assert.equal(savedRunMatchesPrepared(prepared(),r),false);
});
test('unrelated comparable changes do not repeat income calculations', () => {
  const p=prepared();p.method='income_capitalization';const r=run();r.method=p.method;
  p.eligible_comparables=[];assert.equal(savedRunMatchesPrepared(p,r),true);
});
test('normalized draft and prepared signatures agree', () => {
  const p=prepared();assert.equal(preparedSignature(p),valuationSignature({method:p.method,asOf:p.as_of,
    radius:3,lookback:365,inputs:{area_sqm:{value:500,source:' Survey ',as_of:'2026-10-20',status:'observed'}}, evidence:p.eligible_comparables}));
});

test('changed reviewed adjustments make a saved sales result stale', () => {
  const grid = { lines: [{ comparable_id: 'one', factor: 'location', basis: 'percent', amount: 0.1, rationale: 'access', status: 'approved' }],
    time: null, weighting: 'equal', manual_weights: {}, weighting_rationale: null, conclusion_basis: 'median', exclusions: {} };
  const p = { ...prepared(), adjustment_setup: grid };
  assert.equal(savedRunMatchesPrepared(p, { ...run(), adjustment_setup: grid }), true);
  const changed = { ...grid, lines: [{ ...grid.lines[0], amount: 0.2 }] };
  assert.equal(savedRunMatchesPrepared(p, { ...run(), adjustment_setup: changed }), false);
  assert.equal(savedRunMatchesPrepared(p, run()), false, 'a run saved before adjustments is not current');
});
