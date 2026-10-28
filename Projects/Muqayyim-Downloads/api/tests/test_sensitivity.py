"""Financial oracles and invariants for mechanically stressed saved assumptions."""
import copy
import pytest
from api.app.services.valuation_calculations import calculate

INCOME=dict(annual_rent=1000000,vacancy=.1,other_income=50000,operating_expenses=200000,cap_rate=.075)
DCF=dict(annual_rent=1000000,vacancy=0,other_income=0,operating_expenses=200000,rent_growth=0,expense_growth=0,annual_capex=0,holding_years=2,discount_rate=.1,exit_cap_rate=.08,selling_cost=0)
COST=dict(land_value=1000000,building_area=1000,construction_cost=2000,soft_cost_ratio=0,physical_depreciation=.1,functional_obsolescence=0,economic_obsolescence=0)
RESIDUAL=dict(gdv=10000000,construction_cost_total=5000000,professional_fees=500000,financing_cost=200000,selling_cost_total=100000,contingency=300000,developer_profit=1000000)
@pytest.mark.parametrize('method,values',[('income_capitalization',INCOME),('dcf',DCF),('cost',COST),('residual_land',RESIDUAL)])
def test_center_reproduces_base_without_mutating_inputs(method,values):
 before=copy.deepcopy(values);r=calculate(method,values,[]);assert values==before
 assert r['sensitivity']['cells'][1][1]['value']==pytest.approx(r['value'])
 assert len(r['sensitivity']['cells'])==3

def test_income_independent_oracle_and_monotonicity():
 s=calculate('income_capitalization',INCOME,[])['sensitivity']
 assert s['cells'][0][0]['value']==pytest.approx((900000*.9+50000-200000)/.065)
 for row in s['cells']:assert row[0]['value']<row[1]['value']<row[2]['value']
 for col in range(3):assert s['cells'][0][col]['value']>s['cells'][1][col]['value']>s['cells'][2][col]['value']

def test_invalid_rate_is_explicit_not_clamped_or_divided_by_zero():
 s=calculate('income_capitalization',INCOME|{'cap_rate':.005},[])['sensitivity']
 assert all(c['value'] is None and c['reason'] for c in s['cells'][0])
 assert s['cells'][1][1]['value'] is not None

def test_combined_depreciation_bound_and_no_fabricated_sales_stress():
 s=calculate('cost',COST|{'physical_depreciation':.99},[])['sensitivity']
 assert all(c['value'] is None for c in s['cells'][2])
 r=calculate('sales_comparison',{'area_sqm':100},[{'price_per_sqm':10},{'price_per_sqm':20},{'price_per_sqm':30}])
 assert r['value']==2000 and r['sensitivity'] is None

def test_dcf_rate_and_exit_sensitivity_direction():
 s=calculate('dcf',DCF,[])['sensitivity']
 assert s['cells'][0][0]['value']>s['cells'][1][1]['value']>s['cells'][2][2]['value']
