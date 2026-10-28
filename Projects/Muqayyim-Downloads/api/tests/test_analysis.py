"""Map-first workflows: truthful readiness, reused calculations and immutable runs."""
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from api.app.main import app
from api.app.database import Base, engine, async_session
from api.app.models import Comparable, Source, Case, User, ValuationRun
from api.app.auth import create_token
from api.app.services.valuation_calculations import calculate
from api.app.services.analysis_workflow import distance_km


@pytest.fixture
async def client():
    async with engine.begin() as conn: await conn.run_sync(Base.metadata.create_all)
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as c: yield c
    async with engine.begin() as conn: await conn.run_sync(Base.metadata.drop_all)


async def start(client, method='income_capitalization'):
    r = await client.post('/api/v1/analysis/start', json={'latitude':24.7,'longitude':46.7,'property_type':'land','method':method})
    assert r.status_code == 201, r.text
    return r.json()


def payload(p, numbers, method=None):
    return {'expected_revision': p['revision'], 'method': method or p['method'], 'as_of':'2026-10-25',
        'radius_km':3,'lookback_days':365,'inputs': {k:{'value':float(v),'source':'Test explicit assumption', 'as_of':'2026-10-12'} for k,v in numbers.items()}}


@pytest.mark.asyncio
async def test_start_creates_subject_case_and_method_requirements(client):
    p = await start(client)
    assert p['coordinates'] == [24.7,46.7]
    assert not p['ready'] and all(f['value'] is None for f in p['fields'])
    assert {f['key'] for f in p['fields']} == {'annual_rent','vacancy','other_income','operating_expenses','cap_rate'}
    prop = (await client.get('/api/v1/properties/'+p['property_id'])).json()
    assert prop['property']['case_id']
    assert prop['property']['analysis']['method'] == 'income_capitalization'
    dcf = (await client.get('/api/v1/analysis/'+p['property_id']+'?method=dcf')).json()
    assert 'discount_rate' in {f['key'] for f in dcf['fields']}
    assert (await client.get('/api/v1/analysis/'+p['property_id']+'?method=avm')).status_code == 422
    assert len((await client.get('/api/v1/cases')).json()['data']) == 1


@pytest.mark.asyncio
async def test_income_autofill_saved_assumptions_and_reproducible_result(client):
    p = await start(client); path='/api/v1/analysis/'+p['property_id']
    values={'annual_rent':1000000,'vacancy':0.1,'other_income':50000,'operating_expenses':200000,'cap_rate':0.075}
    saved = await client.put(path+'/inputs', json=payload(p,values))
    assert saved.status_code == 200, saved.text
    p2=saved.json();assert p2['ready'] and p2['revision']==2
    assert all(f['origin']=='saved_assumption' for f in p2['fields'])
    run = await client.post(path+'/runs',json={'expected_revision':2})
    assert run.status_code == 201, run.text
    result=run.json();assert result['outputs']['value']==pytest.approx(10000000)
    assert result['outputs']['confidence'] is None
    assert result['property_revision']==2 and result['outputs']['legacy_engine_hash']
    changed=values | {'cap_rate':0.1}
    assert (await client.put(path+'/inputs',json=payload(p2,changed))).status_code==200
    history=(await client.get(path+'/runs')).json()
    assert history[0]['data']['outputs']['value']==result['outputs']['value']
    assert history[0]['data']['inputs'][-1]['value']==0.075
    assert (await client.post(path+'/runs',json={'expected_revision':2})).status_code==409
    old=(await client.get('/api/v1/properties/'+p['property_id']+'/revisions/2')).json()['snapshot']
    assert old['assumptions']['valuation_income_capitalization_cap_rate']['value']==0.075


@pytest.mark.asyncio
async def test_partial_inputs_and_invalid_rates_block_calculation(client):
    p=await start(client);path='/api/v1/analysis/'+p['property_id']
    assert (await client.post(path+'/runs',json={'expected_revision':1})).status_code==409
    r=await client.put(path+'/inputs',json=payload(p,{'annual_rent':0}))
    assert r.status_code==200 and not r.json()['ready']
    assert (await client.post(path+'/runs',json={'expected_revision':2})).status_code==409
    r=await client.put(path+'/inputs',json=payload(r.json(),{'cap_rate':0}))
    assert r.status_code==422
    p2=(await client.get(path)).json(); assert p2['revision']==2
    assert (await client.put(path+'/inputs',json=payload(p2,{'unknown':123}))).status_code==422
    bad=payload(p2,{'annual_rent':1});bad['inputs']['annual_rent']['as_of']='2027-01-01'
    assert (await client.put(path+'/inputs',json=bad)).status_code==422


@pytest.mark.asyncio
async def test_property_fields_and_matching_market_observations_autofill(client):
    p=await start(client);prop=(await client.get('/api/v1/properties/'+p['property_id'])).json()
    data=prop['property'];data['location']['city']='Riyadh';data['financial']['annual_rent_sar']=800000
    assert (await client.put('/api/v1/properties/'+p['property_id'], json={'expected_revision':1,'reason':'Add rent','property':data})).status_code==200
    source=(await client.post('/api/v1/market/sources',json={'name':'Reviewed benchmark','provider':'Internal','source_type':'internal'})).json()['id']
    observation={'external_id':'cap1','observed_on':'2026-10-12','city':'Riyadh','property_type':'land','metric':'cap_rate','unit':'ratio','raw_value':'7%','normalized_value':0.07,'reliability':80}
    assert (await client.post('/api/v1/market/sources/'+source+'/observations',json={'observations':[observation]})).status_code==201
    prepared=(await client.get('/api/v1/analysis/'+p['property_id'])).json()
    fields={f['key']:f for f in prepared['fields']}
    assert fields['annual_rent']['value']==800000 and fields['annual_rent']['origin']=='property_record'
    assert fields['cap_rate']['value']==0.07 and fields['cap_rate']['origin']=='market_observation'
    # No conversion of district benchmarks into invented annual operating costs.
    assert fields['operating_expenses']['value'] is None


@pytest.mark.asyncio
async def test_sales_requires_distinct_reviewed_recent_achieved_evidence(client):
    p=await start(client,'sales_comparison');path='/api/v1/analysis/'+p['property_id']
    p2=(await client.put(path+'/inputs',json=payload(p,{'area_sqm':500}))).json()
    assert not p2['ready']
    user=(await client.get('/api/v1/cases')).json()['data'][0]['created_by']
    case_id=(await client.get('/api/v1/properties/'+p['property_id'])).json()['property']['case_id']
    async with async_session() as db:
        for i,price in enumerate([500000,1000000,1500000]):
            source=Source(case_id=uuid.UUID(case_id),source_type='url',url=f'https://example.com/sale/{i}')
            db.add(source);await db.flush()
            db.add(Comparable(case_id=uuid.UUID(case_id),source_id=source.id,property_title=f'Achieved {i}',
                property_type='land',city='Riyadh',latitude=24.7+i*0.001,longitude=46.7,
                evidence_type='transaction_achieved',transacted_price=price,primary_area_sqm=500,
                transaction_date='2026-10-12',status='active'))
        # A repeated source under a different Source ID must not add another observation.
        source=Source(case_id=uuid.UUID(case_id),source_type='url',url='https://example.com/sale/0');db.add(source);await db.flush()
        db.add(Comparable(case_id=uuid.UUID(case_id),source_id=source.id,property_type='land',latitude=24.7,longitude=46.7,
            evidence_type='transaction_achieved',transacted_price=500000,primary_area_sqm=500,transaction_date='2026-10-12',status='active'))
        await db.commit()
    prepared=(await client.get(path)).json()
    assert prepared['ready'] and len(prepared['eligible_comparables'])==3
    assert any('Repeated source / transaction evidence' in c['exclusion_reasons'] for c in prepared['candidates'])
    result=(await client.post(path+'/runs',json={'expected_revision':p2['revision']})).json()
    assert result['outputs']['value']==1000000
    assert len(result['comparables'])==3


@pytest.mark.asyncio
async def test_analysis_ownership_and_market_map_coverage(client):
    p=await start(client);other=uuid.uuid4()
    async with async_session() as db:
        db.add(User(id=other,email='analysis_other@test.local',name='Other',role='analyst'));await db.commit()
    headers={'Authorization':'Bearer '+create_token(str(other),'analysis_other@test.local','analyst')}
    assert (await client.get('/api/v1/analysis/'+p['property_id'],headers=headers)).status_code==404
    assert (await client.get('/api/v1/analysis/'+p['property_id']+'/runs',headers=headers)).status_code==404
    assert (await client.put('/api/v1/analysis/'+p['property_id']+'/inputs',headers=headers,json=payload(p,{}))).status_code==404
    source=(await client.post('/api/v1/market/sources',json={'name':'Area rent','provider':'Internal','source_type':'internal'})).json()['id']
    base={'external_id':'area','observed_on':'2026-10-12','city':'Riyadh','property_type':'land','metric':'rent','unit':'SAR/sqm/year','raw_value':100,'normalized_value':100,'reliability':70}
    exact=base | {'external_id':'exact','metadata':{'latitude':24.7,'longitude':46.7,'location_precision':'exact'}}
    await client.post('/api/v1/market/sources/'+source+'/observations',json={'observations':[base,exact]})
    r=(await client.get('/api/v1/map/records')).json()
    obs=[r for r in r['data'] if r['kind']=='market']
    assert len(obs)==2 and sum(r['coordinates'] is not None for r in obs)==1
    assert r['coverage']['market_observations']==2
    # Public source intentionally omits local datasets; coverage must remain honest
    # on both an empty checkout and the owner's populated development workspace.
    inventory=(await client.get('/api/v1/market/local-datasets')).json()
    assert r['coverage']['unverified_datasets']==len(inventory)
    assert (await client.get('/api/v1/map/records',headers=headers)).json()['coverage']['market_observations']==0


def test_preserved_cost_dcf_and_residual_math():
    cost=calculate('cost',dict(land_value=1000000,building_area=1000,construction_cost=2000,soft_cost_ratio=0,
        physical_depreciation=0.1,functional_obsolescence=0,economic_obsolescence=0),[])
    assert cost['value']==2800000
    dcf=calculate('dcf',dict(annual_rent=1000000,vacancy=0,other_income=0,operating_expenses=200000,
        rent_growth=0,expense_growth=0,annual_capex=0,holding_years=2,discount_rate=0.1,exit_cap_rate=0.08,selling_cost=0),[])
    assert dcf['value']==pytest.approx(800000/1.1+(800000+10000000)/1.1**2)
    residual=calculate('residual_land',dict(gdv=10000000,construction_cost_total=5000000,professional_fees=500000,
        financing_cost=200000,selling_cost_total=100000,contingency=300000,developer_profit=1000000),[])
    assert residual['value']==2900000
    assert distance_km([24.7,46.7],[24.7,46.7])==0


@pytest.mark.asyncio
async def test_unknown_district_does_not_borrow_another_district_benchmark(client):
    p = await start(client)
    prop = (await client.get('/api/v1/properties/'+p['property_id'])).json()
    data = prop['property']; data['location']['city'] = 'Riyadh'
    await client.put('/api/v1/properties/'+p['property_id'], json={'expected_revision':1, 'reason':'Set city', 'property':data})
    source = (await client.post('/api/v1/market/sources', json={'name':'Geographic benchmarks','provider':'Internal','source_type':'internal'})).json()['id']
    base = {'observed_on':'2026-10-12','city':'Riyadh','property_type':'land','metric':'cap_rate','unit':'ratio',
            'raw_value':'test benchmark','normalized_value':0.07,'reliability':80}
    observations = [base | {'external_id':'city-wide'}, base | {'external_id':'specific-district','district':'Al Nakheel',
                    'observed_on':'2026-10-13','normalized_value':0.04}]
    await client.post('/api/v1/market/sources/'+source+'/observations', json={'observations':observations})
    prepared = (await client.get('/api/v1/analysis/'+p['property_id'])).json()
    cap = next(f for f in prepared['fields'] if f['key']=='cap_rate')
    assert cap['value'] == 0.07
    # Knowing a different district must not silently fall back to the first district.
    prop = (await client.get('/api/v1/properties/'+p['property_id'])).json()
    data = prop['property']; data['location']['district'] = 'Al Malqa'
    await client.put('/api/v1/properties/'+p['property_id'], json={'expected_revision':prop['revision'], 'reason':'Set district', 'property':data})
    prepared = (await client.get('/api/v1/analysis/'+p['property_id'])).json()
    assert next(f for f in prepared['fields'] if f['key']=='cap_rate')['value'] is None
