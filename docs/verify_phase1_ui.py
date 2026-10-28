"""Run ONLY with a disposable backend database and the built frontend on :3100.
Uses Playwright's locally installed Chromium; never seeds the actual Mizan database.
"""
from playwright.sync_api import sync_playwright
from pathlib import Path

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 1000})
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto('http://127.0.0.1:3100/properties')
    page.get_by_label('Property name', exact=True).fill('Phase 1 browser test')
    page.get_by_label('City', exact=True).fill('Riyadh')
    page.get_by_label('Plot number', exact=True).fill('UI-TEST')
    page.get_by_role('button', name='Add property', exact=True).click()
    page.wait_for_url('**/properties/*')
    page.get_by_role('heading', name='Phase 1 browser test', exact=True).wait_for()
    page.get_by_label('Address', exact=True).fill('Browser verification only')
    page.get_by_label('Reason for change', exact=True).fill('Verify persistent inputs')
    page.get_by_role('button', name='Save revision', exact=True).click()
    page.get_by_text('Saved as a new revision.', exact=True).wait_for()
    page.reload()
    page.get_by_role('heading', name='Phase 1 browser test', exact=True).wait_for()
    assert page.get_by_label('Address', exact=True).input_value() == 'Browser verification only'
    page.get_by_role('button', name='Assumptions', exact=True).click()
    page.get_by_label('Key (snake_case)').fill('cap_rate')
    page.get_by_label('Name', exact=True).fill('Cap rate')
    page.get_by_label('Original value', exact=True).fill('0.07')
    page.get_by_label('Value type', exact=True).select_option('number')
    page.get_by_label('Unit', exact=True).fill('ratio')
    page.get_by_label('Category', exact=True).fill('income')
    page.get_by_label('Source', exact=True).fill('Browser test input, not market evidence')
    page.get_by_label('As-of date', exact=True).fill('2026-10-25')
    page.get_by_label('Reason for change', exact=True).fill('Browser test')
    page.get_by_role('button', name='Save assumption', exact=True).click()
    page.get_by_role('cell', name='0.07', exact=True).wait_for()
    page.get_by_role('button', name='History', exact=True).click()
    page.get_by_role('button', name='Revision 1', exact=True).click()
    page.get_by_text('Saved input snapshot', exact=True).wait_for()
    page.screenshot(path=str(Path(__file__).with_name('phase1-workspace-test.png')), full_page=True)
    page.get_by_role('link', name='Market Data', exact=True).click()
    page.get_by_label('Source name', exact=True).fill('Browser test evidence')
    page.get_by_label('Provider / organization', exact=True).fill('Test only')
    page.get_by_role('button', name='Register source', exact=True).click()
    page.get_by_text('Source registered. Import observations below.', exact=True).wait_for()
    page.get_by_label('CSV file', exact=True).set_input_files({'name': 'observations.csv', 'mimeType': 'text/csv', 'buffer': b'external_id,observed_on,city,property_type,metric,unit,raw_value,normalized_value,reliability\nui-1,2026-10-25,Riyadh,office,test_metric,SAR,100,100,50\n'})
    page.get_by_role('button', name='Import CSV', exact=True).click()
    page.get_by_text('1 observations imported; 0 unchanged duplicates skipped.', exact=True).wait_for()
    page.get_by_role('cell', name='test_metric', exact=True).wait_for()
    assert not errors, errors
    print('PASS: property creation, saved edits, reload persistence, assumptions, revision snapshots, source registration, CSV import. No browser errors.')
    browser.close()
