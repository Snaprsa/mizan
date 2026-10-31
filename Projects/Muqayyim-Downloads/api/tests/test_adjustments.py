"""Reviewed comparable adjustment grid: arithmetic, ordering, approval, weighting and persistence."""
import uuid
import pytest
from api.app.services.comparable_adjustments import analyse, weighted_median
from api.tests.test_analysis import client, start, payload  # noqa: F401  (shared fixture and helpers)
from api.app.database import async_session
from api.app.models import Comparable, Source


def comps(*rates, area=500, dated='2026-04-28'):
    return [{'id': f'c{i}', 'title': f'Sale {i}', 'price_per_sqm': r, 'area_sqm': area, 'date': dated, 'distance_km': 1.0}
            for i, r in enumerate(rates)]


def line(cid, factor, basis, amount, status='approved'):
    return {'comparable_id': cid, 'factor': factor, 'basis': basis, 'amount': amount, 'rationale': 'test rationale',
            'source': None, 'status': status}


def test_default_grid_reproduces_unadjusted_median():
    g = analyse(comps(1000, 2000, 3000), None, 500, '2026-10-28')
    assert g['concluded_sar_sqm'] == 2000 and not g['gaps']
    assert g['indication']['base'] == 1_000_000
    assert g['indication']['low'] == 1500 * 500 and g['indication']['high'] == 2500 * 500


def test_transactional_adjustments_compound_and_property_adjustments_add():
    setup = {'lines': [line('c0', 'conditions_of_sale', 'percent', 0.10), line('c0', 'location', 'percent', -0.05),
                       line('c0', 'size', 'sar_per_sqm', 50), line('c0', 'corner', 'sar_total', 25_000)],
             'time': {'annual_rate': 0.10, 'source': 'Reviewer index', 'as_of': '2026-10-28', 'status': 'approved'}}
    row = analyse(comps(1000, 1000, 1000), setup, 500, '2026-10-28')['rows'][0]
    months = (183) / 30.4375
    time_pct = 1.10 ** (months / 12) - 1
    transaction = 1000 * 1.10 * (1 + time_pct)  # conditions of sale first, then time, compounding
    assert row['transaction_adjusted_sar_sqm'] == pytest.approx(transaction)
    # Property adjustments: -5% of transaction-adjusted, +50 SAR/m², +25,000 SAR ÷ 500 m².
    assert row['adjusted_sar_sqm'] == pytest.approx(transaction * 0.95 + 50 + 50)
    assert [s['factor'] for s in row['steps']][:2] == ['conditions_of_sale', 'market_conditions']
    assert row['gross_adjustment'] == pytest.approx(sum(abs(s['delta_sar_sqm']) for s in row['steps']) / 1000)


def test_proposed_adjustments_and_unapproved_time_are_not_applied():
    setup = {'lines': [line('c0', 'location', 'percent', 0.5, status='proposed')],
             'time': {'annual_rate': 0.2, 'source': 'Draft', 'as_of': '2026-10-28', 'status': 'proposed'}}
    g = analyse(comps(1000, 2000, 3000), setup, 100, '2026-10-28')
    assert g['rows'][0]['adjusted_sar_sqm'] == 1000 and g['pending_count'] == 1


def test_weighting_options_and_weighted_statistics():
    base = comps(1000, 2000, 3000)
    manual = analyse(base, {'weighting': 'manual', 'manual_weights': {'c0': 1, 'c1': 1, 'c2': 2},
                            'weighting_rationale': 'c2 is most similar', 'conclusion_basis': 'weighted_mean'}, 100, '2026-10-28')
    assert manual['concluded_sar_sqm'] == pytest.approx((1000 + 2000 + 6000) / 4)
    assert manual['adjusted']['weighted_median'] == 2000
    no_reason = analyse(base, {'weighting': 'manual', 'manual_weights': {'c0': 1, 'c1': 1, 'c2': 2}}, 100, '2026-10-28')
    assert any('rationale' in g for g in no_reason['gaps']) and no_reason['concluded_sar_sqm'] is None
    inverse = analyse(base, {'weighting': 'inverse_gross_adjustment', 'lines': [line('c2', 'quality', 'percent', -0.30)]}, 100, '2026-10-28')
    weights = {r['id']: r['weight'] for r in inverse['rows']}
    assert weights['c2'] < weights['c0'] == weights['c1']
    assert sum(weights.values()) == pytest.approx(1)
    assert weighted_median([1, 2, 3], [1, 1, 10]) == 3


def test_exclusions_need_three_remaining_and_outliers_are_only_flagged():
    g = analyse(comps(1000, 2000, 3000), {'exclusions': {'c2': 'different zoning'}}, 100, '2026-10-28')
    assert g['concluded_sar_sqm'] is None and g['excluded'][0]['exclusion_reason'] == 'different zoning'
    flagged = analyse(comps(1000, 1010, 1020, 1030, 9000), None, 100, '2026-10-28')
    assert len(flagged['rows']) == 5 and any('interquartile fences' in n for n in flagged['rows'][4]['notes'])


def test_lump_sum_without_area_is_rejected_and_heavy_adjustment_flagged():
    with pytest.raises(ValueError):
        analyse(comps(1000, 2000, 3000, area=None), {'lines': [line('c0', 'corner', 'sar_total', 1000)]}, 100, '2026-10-28')
    g = analyse(comps(1000, 2000, 3000), {'lines': [line('c0', 'condition', 'percent', 0.4)]}, 100, '2026-10-28')
    assert any('Heavily adjusted' in n for n in g['rows'][0]['notes'])


async def seed_sales(client, p):
    case_id = (await client.get('/api/v1/properties/' + p['property_id'])).json()['property']['case_id']
    async with async_session() as db:
        for i, price in enumerate([500000, 1000000, 1500000]):
            source = Source(case_id=uuid.UUID(case_id), source_type='url', url=f'https://example.com/adj/{i}')
            db.add(source); await db.flush()
            db.add(Comparable(case_id=uuid.UUID(case_id), source_id=source.id, property_title=f'Achieved {i}',
                property_type='land', city='Riyadh', latitude=24.7 + i * 0.001, longitude=46.7,
                evidence_type='transaction_achieved', transacted_price=price, primary_area_sqm=500,
                transaction_date='2026-10-12', status='active'))
        await db.commit()


@pytest.mark.asyncio
async def test_saved_adjustments_drive_the_run_and_survive_input_saves(client):
    p = await start(client, 'sales_comparison'); path = '/api/v1/analysis/' + p['property_id']
    p = (await client.put(path + '/inputs', json=payload(p, {'area_sqm': 500}))).json()
    await seed_sales(client, p)
    p = (await client.get(path)).json()
    assert p['ready'] and p['adjustment_analysis']['concluded_sar_sqm'] == 2000
    target = p['eligible_comparables'][0]['id']
    bad = await client.put(path + '/adjustments', json={'expected_revision': p['revision'], 'reason': 'x',
        'adjustments': {'lines': [], 'exclusions': {target: ''}}})
    assert bad.status_code == 422
    body = {'expected_revision': p['revision'], 'reason': 'Reviewed location differences', 'adjustments': {
        'lines': [{'comparable_id': target, 'factor': 'location', 'basis': 'percent', 'amount': 0.10,
                   'rationale': 'Inferior street access', 'status': 'approved'}]}}
    saved = await client.put(path + '/adjustments', json=body)
    assert saved.status_code == 200, saved.text
    p2 = saved.json(); assert p2['revision'] == p['revision'] + 1
    stale = await client.put(path + '/adjustments', json=body)
    assert stale.status_code == 409, 'stale revision must not overwrite reviewed adjustments'
    # Saving method inputs again must keep the adjustment grid.
    p3 = (await client.put(path + '/inputs', json=payload(p2, {'area_sqm': 500}))).json()
    assert p3['adjustment_setup']['lines'][0]['rationale'] == 'Inferior street access'
    run = (await client.post(path + '/runs', json={'expected_revision': p3['revision']})).json()
    grid = {r['id']: r for r in run['outputs']['evidence']['grid']}
    assert grid[target]['adjusted_sar_sqm'] == pytest.approx(grid[target]['raw_sar_sqm'] * 1.1)
    assert run['adjustment_setup']['lines'][0]['factor'] == 'location'
    assert run['outputs']['evidence']['applied_adjustments'] == 1
    revisions = (await client.get(f"/api/v1/properties/{p['property_id']}/revisions")).json()
    assert any('Comparable adjustments' in (r.get('reason') or '') for r in revisions)


def test_rules_adjust_from_subject_and_comparable_differences():
    comp = lambda i, **a: {'id': i, 'title': i, 'price_per_sqm': 1000, 'area_sqm': 100, 'date': '2026-10-01', 'attributes': a}
    rows = [comp('low', floor=2, grade='B'), comp('same', floor=5, grade='A'), comp('unknown')]
    setup = {'rules': [{'factor': 'floor', 'percent': 0.01, 'source': 'Reviewer', 'status': 'approved'},
                       {'factor': 'grade', 'percent': 0.10, 'source': 'Reviewer', 'status': 'approved'},
                       {'factor': 'size', 'percent': 0.05, 'source': 'Draft', 'status': 'proposed'}]}
    g = analyse(rows, setup, 200, '2026-10-28', {'floor': 5, 'grade': 'A'})
    by = {r['id']: r for r in g['rows']}
    # Subject is 3 floors higher and one grade better than "low": additive +3% and +10%.
    assert by['low']['adjusted_sar_sqm'] == pytest.approx(1130)
    assert by['same']['adjusted_sar_sqm'] == 1000 and not by['same']['steps']
    # Unknown values are never adjusted for, and the note says why.
    assert by['unknown']['adjusted_sar_sqm'] == 1000
    assert any('No floor adjustment' in n for n in by['unknown']['notes'])
    assert all(s['factor'] != 'size' for r in g['rows'] for s in r['steps']), 'a proposed rule is not applied'


def test_rule_direction_size_and_manual_override():
    comps = [{'id': f'c{i}', 'price_per_sqm': 1000, 'area_sqm': 100, 'date': '2026-10-01', 'attributes': {'floor': 8}} for i in range(3)]
    setup = {'rules': [{'factor': 'floor', 'percent': 0.01, 'source': 'R', 'status': 'approved'}, {'factor': 'size', 'percent': -0.02, 'source': 'R', 'status': 'approved'}],
             'lines': [line('c0', 'floor', 'percent', 0.05)]}
    rows = {r['id']: r for r in analyse(comps, setup, 300, '2026-10-28', {'floor': 5})['rows']}
    # Subject 3 floors lower (-3%) and 200 m² larger at -2% per 100 m² (-4%).
    assert rows['c1']['adjusted_sar_sqm'] == pytest.approx(930)
    # An approved manual floor line replaces the floor rule for that comparable only.
    assert rows['c0']['adjusted_sar_sqm'] == pytest.approx(1010)
    assert sum(s['factor'] == 'floor' for s in rows['c0']['steps']) == 1


@pytest.mark.asyncio
async def test_demo_import_is_labelled_validated_and_removable(client):
    good = {'title': 'Olaya flat', 'property_type': 'apartment', 'evidence_type': 'transaction_achieved', 'price_sar': 900000, 'area_sqm': 150,
            'date': '2026-09-01', 'latitude': 24.7, 'longitude': 46.68, 'district': 'Al Olaya', 'attributes': {'floor': 4, 'position': 'front'}}
    forged = {**good, 'title': 'Forged', 'attributes': {'is_demo': False}}
    r = await client.post('/api/v1/evidence/demo', json={'records': [good, good, {**good, 'title': 'Jeddah', 'latitude': 21.5, 'longitude': 39.2},
        {**good, 'title': 'Swapped', 'latitude': 46.68, 'longitude': 24.7}, {**good, 'title': 'Future', 'date': '2099-01-01'}, forged]})
    assert r.status_code == 201, r.text
    body = r.json()
    assert (body['inserted'], body['duplicates'], body['rejected_count']) == (1, 1, 4)
    assert any('outside Riyadh' in x['reason'] for x in body['rejected'])
    data = (await client.get('/api/v1/map/records')).json()
    assert data['coverage']['demo_comparables'] == 1
    rec = data['data'][0]
    assert rec['title'].startswith('DEMO · ') and rec['attributes']['is_demo'] is True and rec['reliability_score'] == 1
    assert rec['kind'] == 'transaction' and rec['coordinates'] == [24.7, 46.68] and rec['price_per_sqm'] == 6000
    # Editing details cannot remove the demo label.
    saved = await client.put(f"/api/v1/evidence/{rec['entity_id']}/attributes", json={'reason': 'Reviewed floor', 'attributes': {'floor': 7}})
    assert saved.status_code == 200 and saved.json()['attributes']['is_demo'] is True and saved.json()['attributes']['floor'] == 7
    assert (await client.delete('/api/v1/evidence/demo')).json()['removed'] == 1
    assert (await client.get('/api/v1/map/records')).json()['total'] == 0


@pytest.mark.asyncio
async def test_subject_details_drive_rules_and_demo_is_flagged_in_the_result(client):
    p = await start(client, 'sales_comparison'); path = '/api/v1/analysis/' + p['property_id']
    prop = (await client.get('/api/v1/properties/' + p['property_id'])).json()
    body = {**prop['property'], 'property_type': 'apartment', 'building': {**prop['property']['building'], 'floor_number': 6}}
    updated = await client.put('/api/v1/properties/' + p['property_id'], json={'property': body, 'expected_revision': prop['revision'], 'reason': 'Unit details'})
    assert updated.status_code == 200, updated.text
    recs = [{'title': f'Sale {i}', 'property_type': 'apartment', 'evidence_type': 'transaction_achieved', 'price_sar': 500000, 'area_sqm': 100,
             'date': '2026-10-01', 'latitude': 24.7 + i * 0.001, 'longitude': 46.7, 'attributes': {'floor': 2}} for i in range(3)]
    assert (await client.post('/api/v1/evidence/demo', json={'records': recs})).json()['inserted'] == 3
    p = (await client.put(path + '/inputs', json=payload(updated.json(), {'area_sqm': 100}, 'sales_comparison'))).json()
    assert p['comparison_factors'] == ['size', 'floor', 'position'] and p['subject_attributes']['floor'] == 6
    p = (await client.put(path + '/adjustments', json={'expected_revision': p['revision'], 'reason': 'Floor premium', 'adjustments': {
        'rules': [{'factor': 'floor', 'percent': 0.01, 'source': 'Reviewer judgement', 'status': 'approved'}]}})).json()
    run = (await client.post(path + '/runs', json={'expected_revision': p['revision']})).json()
    assert run['outputs']['value'] == pytest.approx(5000 * 1.04 * 100)
    assert any('synthetic demo' in l for l in run['outputs']['limitations']) and run['outputs']['evidence']['demo_comparables'] == 3
