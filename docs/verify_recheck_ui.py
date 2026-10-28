"""Browser-only regression fixtures. All API writes are intercepted; actual app data is untouched."""
import base64
import copy
import json
import urllib.request
from playwright.sync_api import sync_playwright

CATALOG=json.load(urllib.request.urlopen('http://127.0.0.1:8000/api/v1/analysis/catalog'))
PIXEL=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=')
VERSION='mizan.map-workflow.1'
ID='11111111-1111-1111-1111-111111111111'


def definition(method,key,value=None):
    f=copy.deepcopy(next(f for m in CATALOG['methods'] if m['key']==method for f in m['fields'] if f['key']==key))
    return f | {'value':value,'source':'Browser fixture assumption' if value is not None else None,
        'as_of':'2026-10-20' if value is not None else None,'origin':'saved_assumption' if value is not None else None,
        'assumption_status':'user_input','state':'available' if value is not None else 'missing','error':None if value is not None else 'Required'}


def evidence(key,price):
    return {'id':key,'price':price,'area_sqm':500,'price_per_sqm':price/500,'coordinates':[24.7,46.7],
        'date':'2026-10-20','currency':'SAR','property_type':'land','source':'Browser fixture only',
        'status':'active','evidence_type':'transaction_achieved','title':key,'distance_km':0,
        'eligible':True,'exclusion_reasons':[]}


def prepared(method,fields,evidence_rows=None):
    return {'property_id':ID,'property_name':'Browser regression fixture','revision':2,'property_type':'land',
        'coordinates':[24.7,46.7],'method':method,'method_label':method,'description':'Browser-only fixture',
        'as_of':'2026-10-27','radius_km':3,'lookback_days':365,'fields':fields,'candidates':[],
        'eligible_comparables':evidence_rows or [],'gaps':[],'ready':True,'calculation_version':VERSION}


def run_snapshot(p,value):
    return {'id':'old-run','property_revision':p['revision'],'method':p['method'],'data_date':p['as_of'],
        'created_at':'2026-10-27T10:00:00','inputs':copy.deepcopy(p['fields']),
        'property':{'analysis':{'radius_km':3,'lookback_days':365}},'comparables':copy.deepcopy(p['eligible_comparables']),
        'outputs':{'value':value,'currency':'SAR','confidence':None,'calculation_version':VERSION,'evidence':{},'limitations':[]}}


def route_page(page,state):
    page.route('https://tile.openstreetmap.org/**',lambda r:r.fulfill(content_type='image/png',body=PIXEL))
    def api(route):
        url=route.request.url;method=route.request.method
        if '/analysis/catalog' in url: return route.fulfill(json=CATALOG)
        if '/map/records' in url: return route.fulfill(json={'data':[],'total':0,'truncated':False,'available':{'cities':[],'property_types':[]}})
        if '/analysis/'+ID in url:
            if url.endswith('/runs') and method=='GET': return route.fulfill(json=state['history'])
            if url.endswith('/inputs'):
                state['writes']+=1;body=route.request.post_data_json;state['p']['revision']+=1
                for f in state['p']['fields']:
                    d=body['inputs'][f['key']];f.update(value=d['value'],source=d['source'],as_of=d['as_of'],assumption_status=d['status'])
                return route.fulfill(json=state['p'])
            if url.endswith('/runs') and method=='POST':
                result=run_snapshot(state['p'],2000000);result['id']='new-run';state['history'].insert(0,{'id':'new-run','created_at':result['created_at'],'data':result})
                return route.fulfill(status=201,json=result)
            return route.fulfill(json=state['p'])
        return route.fulfill(status=404,json={'detail':'Not part of this fixture'})
    page.route('**/api/**',api)


with sync_playwright() as playwright:
    browser=playwright.chromium.launch(headless=True)
    page=browser.new_page(viewport={'width':1560,'height':1100});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    old=prepared('sales_comparison',[definition('sales_comparison','area_sqm',500)],[evidence(str(i),1000000) for i in range(3)])
    changed=copy.deepcopy(old);changed['eligible_comparables']=[evidence(str(i),2000000) for i in range(3)]
    saved=run_snapshot(old,1000000)
    state={'p':changed,'history':[{'id':'old-run','created_at':saved['created_at'],'data':saved}],'writes':0}
    route_page(page,state);page.goto('http://127.0.0.1:3100/map?analysis='+ID)
    page.get_by_text('Previous saved result · inputs may have changed',exact=True).wait_for()
    page.get_by_text('SAR 2,000,000',exact=True).wait_for(timeout=15000)
    page.get_by_text('Current saved indication',exact=True).wait_for()
    assert state['writes']==1 and len(state['history'])==2
    page.close()
    page=browser.new_page(viewport={'width':1560,'height':1100});page.on('pageerror',lambda e:errors.append(str(e)))
    keys=['annual_rent','vacancy','other_income','operating_expenses','cap_rate']
    state={'p':prepared('income_capitalization',[definition('income_capitalization',key) for key in keys]),'history':[],'writes':0}
    route_page(page,state);page.goto('http://127.0.0.1:3100/map?analysis='+ID)
    page.get_by_label('Gross potential annual rent',exact=True).wait_for()
    page.get_by_label('Calculate automatically when required inputs are complete',exact=True).uncheck()
    page.get_by_label('Gross potential annual rent',exact=True).fill('111')
    state['p']['fields']=[definition('income_capitalization',key,val) for key,val in zip(keys,[999,0.1,0,100,0.075])]
    page.get_by_role('button',name='Refresh evidence',exact=True).click()
    page.wait_for_function("document.querySelector('input[aria-label=\"Capitalization rate\"]').value === '0.075'")
    assert page.get_by_label('Gross potential annual rent',exact=True).input_value()=='111'
    assert page.get_by_label('Source for Capitalization rate',exact=True).input_value()=='Browser fixture assumption'
    assert state['writes']==0
    assert not errors,errors
    browser.close()
    print('PASS: changed sales evidence invalidates and recalculates an old result; refresh fills new values while preserving unsaved edits. No real database writes or browser errors.')
