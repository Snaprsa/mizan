"""Mizan Monitor: values come from the shared engine, changes are explained, and demo data stays separate."""
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from api.app.main import app
from api.app.database import Base, engine, async_session
from api.app.auth import create_token
from api.app.models import Case, Comparable, Source, User
from api.app.models.foundation import Property
from api.app.models.monitor import ValuationSnapshot
from api.app.services.monitor_calc import attribute, evidence_grade, priority, reconcile, value_range

TODAY_INPUT = '2026-10-01'


@pytest.fixture
async def client():
    async with engine.begin() as conn: await conn.run_sync(Base.metadata.create_all)
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as c: yield c
    async with engine.begin() as conn: await conn.run_sync(Base.metadata.drop_all)


INCOME = dict(annual_rent=1_000_000, vacancy=.1, other_income=0, operating_expenses=200_000, cap_rate=.08)


def income_state(**changes):
    return {'income_capitalization': {'inputs': {**{k: float(v) for k, v in INCOME.items()}, **changes}}}


async def income_property(client, name='Office A', **inputs):
    p = (await client.post('/api/v1/analysis/start', json={'latitude': 24.7, 'longitude': 46.7, 'property_type': 'office', 'method': 'income_capitalization', 'name': name, 'city': 'Riyadh'})).json()
    r = await client.put(f"/api/v1/analysis/{p['property_id']}/inputs", json={'expected_revision': p['revision'], 'method': 'income_capitalization', 'as_of': TODAY_INPUT, 'radius_km': 3, 'lookback_days': 365,
        'inputs': {k: {'value': float(v), 'source': 'Test rent roll', 'as_of': TODAY_INPUT} for k, v in {**INCOME, **inputs}.items()}})
    assert r.status_code == 200, r.text
    return p['property_id']


async def portfolio_with(client, *property_ids):
    pid = (await client.post('/api/v1/monitor/portfolios', json={'name': 'Test fund'})).json()['id']
    r = await client.post(f'/api/v1/monitor/portfolios/{pid}/assets', json={'property_ids': list(property_ids)})
    assert r.status_code == 201, r.text
    return pid


async def first_asset(client, pid):
    return (await client.get(f'/api/v1/monitor/portfolios/{pid}/assets')).json()['data'][0]


# ── Pure calculations ─────────────────────────────────────────────

def test_reconcile_uses_median_unless_reviewer_weights_cover_every_method():
    assert reconcile({'a': 100, 'b': 200, 'c': 900})[0] == 200
    assert reconcile({'a': 100, 'b': 200}, {'a': 3, 'b': 1})[0] == 125
    value, detail = reconcile({'a': 100, 'b': 200, 'c': 900}, {'a': 1})
    assert value == 200 and detail['basis'] == 'median'


def test_range_needs_two_points():
    assert value_range({'income_capitalization': 100}) == (None, None)
    assert value_range({'a': 100, 'b': 120}) == (100, 120)


def test_attribution_sums_exactly_and_names_the_drivers():
    old, new = income_state(), income_state(cap_rate=.09, vacancy=.2, annual_rent=1_100_000.0)
    start, end = (900_000-200_000)/.08, (1_100_000*.8-200_000)/.09
    result = attribute(old, new, start, end)
    assert {d['key'] for d in result['drivers']} == {'rent', 'occupancy', 'yields'}
    assert sum(d['amount'] for d in result['drivers']) == pytest.approx(end-start)
    amounts = {d['key']: d['amount'] for d in result['drivers']}
    assert amounts['rent'] > 0 and amounts['occupancy'] < 0 and amounts['yields'] < 0


def test_attribution_single_driver_matches_rerun():
    start, end = 700_000/.08, 700_000/.1
    result = attribute(income_state(), income_state(cap_rate=.1), start, end)
    assert result['drivers'][0]['key'] == 'yields'
    assert result['drivers'][0]['amount'] == pytest.approx(end-start)


def test_grade_has_no_percentage_and_real_assets_on_demo_sales_are_low():
    states = income_state()
    states['income_capitalization'].update(value=8_750_000, meta=[{'as_of': '2026-10-01', 'status': 'observed'}])
    grade = evidence_grade(states, '2026-10-05')
    assert grade['level'] in {'high', 'medium'} and 'score' not in grade
    states['income_capitalization']['uses_demo'] = True
    assert evidence_grade(states, '2026-10-05')['level'] == 'low'


def test_priority_explains_itself():
    result = priority({'value': 100, 'change_vs_official_pct': -16, 'official_age_months': 19, 'confidence': 'low'})
    assert result['band'] == 'high' and len(result['reasons']) == 3
    assert result['score'] == sum(r['points'] for r in result['reasons'])


# ── API ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_asset_value_comes_from_the_shared_engine_and_quiet_rechecks_make_no_snapshot(client):
    prop = await income_property(client)
    pid = await portfolio_with(client, prop)
    asset = await first_asset(client, pid)
    assert asset['value'] == pytest.approx(700_000/.08)
    assert asset['confidence'] and asset['origin'] == 'derived'
    r = await client.post(f'/api/v1/monitor/portfolios/{pid}/check')
    assert r.json()['updated'] == 0 and r.json()['unchanged'] == 1
    detail = (await client.get(f"/api/v1/monitor/assets/{asset['id']}")).json()
    assert len(detail['history']) == 1
    # The grade stays a plain word on the row; its checks travel separately.
    assert detail['confidence'] in {'high', 'medium', 'low'} and detail['confidence_detail']['checks']


@pytest.mark.asyncio
async def test_asset_without_reviewed_inputs_has_no_invented_value(client):
    p = (await client.post('/api/v1/analysis/start', json={'latitude': 24.7, 'longitude': 46.7, 'property_type': 'office', 'method': 'income_capitalization'})).json()
    pid = await portfolio_with(client, p['property_id'])
    asset = await first_asset(client, pid)
    assert asset['value'] is None
    board = (await client.get(f'/api/v1/monitor/portfolios/{pid}')).json()
    assert board['totals']['value'] == 0 and board['totals']['unvalued_count'] == 1


@pytest.mark.asyncio
async def test_override_keeps_the_reviewed_value_explains_the_change_and_can_be_undone(client):
    prop = await income_property(client)
    pid = await portfolio_with(client, prop)
    asset = await first_asset(client, pid)
    url = f"/api/v1/monitor/assets/{asset['id']}"
    r = await client.post(url+'/override', json={'field': 'cap_rate', 'value': .1, 'reason': 'Valuer view on yield'})
    assert r.status_code == 200, r.text
    detail = r.json()
    assert detail['value'] == pytest.approx(7_000_000)
    assert detail['attribution']['drivers'][0]['key'] == 'yields'
    assert sum(d['amount'] for d in detail['attribution']['drivers']) == pytest.approx(7_000_000-8_750_000)
    meta = next(m for m in detail['methods'][0]['inputs'] if m['key'] == 'cap_rate')
    assert meta['override'] is True
    log = (await client.get(url+'/audit')).json()['entries']
    action = next(e for e in log if e['kind'] == 'action' and e['text'] == 'Assumption overridden')
    assert action['details']['reason'] == 'Valuer view on yield' and action['details']['changes'][0]['before'] == .08 and action['user_id']
    assert (await client.post(url+'/override', json={'field': 'cap_rate', 'value': -1, 'reason': 'Bad value'})).status_code == 422
    undone = (await client.post(url+'/override', json={'field': 'cap_rate', 'value': None, 'reason': 'Back to reviewed'})).json()
    assert undone['value'] == pytest.approx(8_750_000)
    assert len([h for h in undone['history'] if h['kind'] == 'indicative']) == 3


@pytest.mark.asyncio
async def test_official_valuation_move_raises_one_alert_that_resolves_when_it_clears(client):
    prop = await income_property(client)
    pid = await portfolio_with(client, prop)
    asset = await first_asset(client, pid)
    url = f"/api/v1/monitor/assets/{asset['id']}"
    r = await client.post(url+'/official', json={'value_sar': 10_000_000, 'valued_on': '2026-06-30', 'valuer': 'Test valuer'})
    assert r.status_code == 201, r.text
    assert r.json()['change_vs_official_pct'] == pytest.approx(-12.5)
    board = (await client.get(f'/api/v1/monitor/portfolios/{pid}')).json()
    moves = [a for a in board['alerts'] if a['kind'] == 'valuation_move']
    assert len(moves) == 1 and moves[0]['severity'] == 'warning'
    assert board['attention_count'] == 1 and board['totals']['down'] == 1
    assert (await client.post(f'/api/v1/monitor/portfolios/{pid}/check')).status_code == 200
    again = (await client.get(f'/api/v1/monitor/portfolios/{pid}')).json()
    assert len([a for a in again['alerts'] if a['kind'] == 'valuation_move']) == 1
    # A newer official valuation close to the model clears the condition.
    await client.post(url+'/official', json={'value_sar': 8_800_000, 'valued_on': '2026-09-30', 'valuer': 'Test valuer'})
    cleared = (await client.get(f'/api/v1/monitor/portfolios/{pid}')).json()
    assert not [a for a in cleared['alerts'] if a['kind'] == 'valuation_move'] and cleared['attention_count'] == 0


@pytest.mark.asyncio
async def test_accepted_alert_stays_quiet_until_it_gets_worse(client):
    prop = await income_property(client)
    pid = await portfolio_with(client, prop)
    asset = await first_asset(client, pid)
    url = f"/api/v1/monitor/assets/{asset['id']}"
    await client.post(url+'/official', json={'value_sar': 9_400_000, 'valued_on': '2026-06-30', 'valuer': 'V'})  # -6.9%: watch
    alert = next(a for a in (await client.get(url)).json()['alerts'] if a['kind'] == 'valuation_move')
    assert alert['severity'] == 'watch'
    assert (await client.patch(f"/api/v1/monitor/alerts/{alert['id']}", json={'status': 'accepted', 'note': 'Reviewed'})).json()['status'] == 'accepted'
    await client.post(url+'/override', json={'field': 'cap_rate', 'value': .1, 'reason': 'Yield moved out'})  # -25.5%: critical
    now = next(a for a in (await client.get(url)).json()['alerts'] if a['kind'] == 'valuation_move')
    assert now['severity'] == 'critical' and now['status'] == 'open'


@pytest.mark.asyncio
async def test_totals_use_owned_share_and_disclose_coverage(client):
    a, b = await income_property(client, 'A'), await income_property(client, 'B')
    pid = await portfolio_with(client, a, b)
    rows = (await client.get(f'/api/v1/monitor/portfolios/{pid}/assets')).json()['data']
    await client.patch(f"/api/v1/monitor/assets/{rows[0]['id']}", json={'ownership_pct': 50, 'debt_sar': 4_375_000})
    t = (await client.get(f'/api/v1/monitor/portfolios/{pid}')).json()['totals']
    assert t['value'] == pytest.approx(8_750_000*1.5)
    assert t['debt'] == pytest.approx(2_187_500) and t['ltv_pct'] == pytest.approx(2_187_500/(8_750_000*1.5)*100)
    assert t['debt_count'] == 1 and t['change'] is None and t['not_comparable'] == 2


@pytest.mark.asyncio
async def test_stress_runs_the_engine_and_only_moves_methods_using_the_input(client):
    prop = await income_property(client)
    pid = await portfolio_with(client, prop)
    result = (await client.get(f'/api/v1/monitor/portfolios/{pid}/stress')).json()
    cap = next(s for s in result['scenarios'] if s['key'] == 'cap_100')
    assert cap['value'] == pytest.approx(700_000/.09) and cap['affected'] == 1
    assert next(s for s in result['scenarios'] if s['key'] == 'discount_100')['change'] == 0


@pytest.mark.asyncio
async def test_snapshots_are_immutable(client):
    prop = await income_property(client)
    await portfolio_with(client, prop)
    async with async_session() as db:
        snap = await db.scalar(select(ValuationSnapshot))
        snap.value_sar = 1
        with pytest.raises(ValueError):
            await db.commit()


@pytest.mark.asyncio
async def test_portfolios_are_private_and_read_only_roles_cannot_write(client):
    prop = await income_property(client)
    pid = await portfolio_with(client, prop)
    async with async_session() as db:
        other = User(id=uuid.uuid4(), email='other@test.local', name='Other', role='viewer')
        db.add(other); await db.commit()
    headers = {'Authorization': 'Bearer '+create_token(str(other.id), other.email, other.role)}
    assert (await client.get(f'/api/v1/monitor/portfolios/{pid}', headers=headers)).status_code == 404
    assert (await client.post('/api/v1/monitor/portfolios', json={'name': 'X'}, headers=headers)).status_code == 403


@pytest.mark.asyncio
async def test_demo_portfolio_is_labelled_computed_separate_and_removable(client):
    real = await income_property(client, 'Real office')
    r = await client.post('/api/v1/monitor/demo')
    assert r.status_code == 201, r.text
    assert (await client.post('/api/v1/monitor/demo')).status_code == 409
    pid = r.json()['id']
    board = (await client.get(f'/api/v1/monitor/portfolios/{pid}')).json()
    assert board['is_demo'] and board['name'].startswith('DEMO')
    t = board['totals']
    assert t['asset_count'] == 72 and t['origin'] == 'demo' and t['unvalued_count'] == 0
    # The headline change compares only assets with an official value, so its base must say the same.
    assert t['compared_count'] == 70 and t['like_official'] <= t['official'] and t['change'] == pytest.approx(t['value']-t['like_official'], abs=t['value']*.05)
    assert t['up'] and t['down'] and t['stable'] and board['attention_count'] >= 3
    assert {'valuation_move', 'method_divergence'} <= {a['kind'] for a in board['alerts']}
    assert len(board['history']) >= 18 and board['priority']
    decline = next(a for a in board['attention'] if (a['change_vs_official_pct'] or 0) < -5)
    detail = (await client.get(f"/api/v1/monitor/assets/{decline['id']}")).json()
    assert detail['origin'] == 'demo' and detail['history'][-1]['origin'] == 'demo'
    window = detail['attribution_since_official']
    assert window and window['drivers'] and sum(d['amount'] for d in window['drivers']) == pytest.approx(window['total'], abs=1)
    # Demo records stay away from the map, Properties and real valuations.
    records = (await client.get('/api/v1/map/records')).json()['data']
    assert [x['title'] for x in records] == ['Real office']
    assert [x['id'] for x in (await client.get('/api/v1/properties')).json()['data']] == [real]
    prepared = (await client.get(f'/api/v1/analysis/{real}?method=sales_comparison')).json()
    assert prepared['candidates'] == []
    demo_prop = detail['property_id']
    other = (await client.post('/api/v1/monitor/portfolios', json={'name': 'Real'})).json()['id']
    assert (await client.post(f'/api/v1/monitor/portfolios/{other}/assets', json={'property_ids': [demo_prop]})).status_code == 422
    removed = (await client.delete('/api/v1/monitor/demo')).json()
    assert removed == {'portfolios': 1, 'properties': 72}
    assert (await client.get(f'/api/v1/monitor/portfolios/{pid}')).status_code == 404
    async with async_session() as db:
        assert (await db.scalars(select(Property))).all()[0].name == 'Real office'
        assert (await db.scalars(select(ValuationSnapshot))).all() == []
    assert (await client.get(f'/api/v1/properties/{real}')).status_code == 200
