"""Map-first workflow test using a disposable API on :8100.
All browser /api calls are redirected to the isolated DB; actual app data is untouched.
"""
import base64
from pathlib import Path
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page(viewport={'width':1560,'height':1100})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    pixel=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=')
    page.route('https://tile.openstreetmap.org/**',lambda route:route.fulfill(content_type='image/png',body=pixel))
    def isolated(route):
        response=route.fetch(url=route.request.url.replace('127.0.0.1:3100','127.0.0.1:8100'))
        route.fulfill(response=response)
    page.route('**/api/**',isolated)
    page.goto('http://127.0.0.1:3100/')
    page.wait_for_url('**/map')
    page.get_by_label('Subject property type',exact=True).select_option('office')
    page.get_by_label('Choose valuation approach',exact=True).select_option('income_capitalization')
    page.locator('.leaflet-container').wait_for()
    page.locator('.leaflet-container').click(position={'x':340,'y':250})
    page.get_by_role('button',name='Start valuation',exact=True).click()
    panel=page.get_by_role('region',name='Valuation workspace',exact=True)
    panel.wait_for()
    page.get_by_label('Gross potential annual rent',exact=True).wait_for()
    values={'Gross potential annual rent':'1000000','Vacancy / credit loss':'0.1','Other annual income':'50000',
            'Annual operating expenses':'200000','Capitalization rate':'0.075'}
    for name,value in values.items():
        page.get_by_label(name,exact=True).fill(value)
        assert page.get_by_label('Source for '+name,exact=True).input_value().startswith('User input')
        page.get_by_label('Source for '+name,exact=True).fill('UI TEST explicit assumption; not market evidence')
        page.get_by_label('Source date for '+name,exact=True).fill('2026-10-12')
    page.get_by_text('SAR 10,000,000',exact=True).wait_for(timeout=20000)
    property_id=page.url.split('analysis=')[1].split('&')[0]
    history=page.request.get('http://127.0.0.1:8100/api/v1/analysis/'+property_id+'/runs').json()
    assert len(history)==1
    page.reload();page.get_by_text('SAR 10,000,000',exact=True).wait_for()
    # Wait through the auto-calculation debounce to ensure reopening doesn't add a run.
    page.wait_for_timeout(1600)
    assert len(page.request.get('http://127.0.0.1:8100/api/v1/analysis/'+property_id+'/runs').json())==1
    page.get_by_label('Capitalization rate',exact=True).fill('0.1')
    page.get_by_text('SAR 7,500,000',exact=True).wait_for(timeout=20000)
    assert len(page.request.get('http://127.0.0.1:8100/api/v1/analysis/'+property_id+'/runs').json())==2
    page.get_by_label('Valuation approach',exact=True).select_option('cost')
    page.get_by_label('Replacement construction cost',exact=True).wait_for()
    assert page.get_by_label('Capitalization rate',exact=True).count()==0
    page.get_by_label('Valuation approach',exact=True).select_option('income_capitalization')
    page.get_by_text('SAR 7,500,000',exact=True).wait_for()
    page.wait_for_timeout(1600)
    assert len(page.request.get('http://127.0.0.1:8100/api/v1/analysis/'+property_id+'/runs').json())==2
    page.screenshot(path=str(Path(__file__).with_name('map-workflow-test.png')),full_page=True)
    assert not errors,errors
    print('PASS: root opens map; select subject/type/approach; method-specific inputs; automatic sourced calculation; reload without duplicates; automatic recalculation; method switching; immutable run history. No page errors. Actual app DB untouched.')
    browser.close()
