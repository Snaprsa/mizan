import copy
import pytest
from api.app.services.hbu_analysis import analyze_hbu

def fixture():
 gate={'status':'PASS','source':'Synthetic evidence fixture','date':'2026-10-28','reviewed_by':'Test reviewer'}
 budget=dict(gdv=10000000,construction_cost_total=5000000,professional_fees=500000,financing_cost=200000,selling_cost_total=100000,contingency=300000,developer_profit=1000000)
 option=dict(id='A',legal=gate,physical=gate,budget=budget,timed_appraisal={'cash_flows_sar':[-6000000,0,8000000],'discount_rate':.1,'source':'Synthetic model','assumptions_note':'Includes assumed acquisition/development and sale, annual'})
 return {'land_area_sqm':5000,'alternatives':[option]}
def test_reuses_residual_and_does_not_mutate():
 p=fixture();before=copy.deepcopy(p);r=analyze_hbu(p);assert p==before
 assert r['alternatives'][0]['residual_land_sar']==2900000
 assert r['alternatives'][0]['project_npv_sar']==pytest.approx(-6000000+8000000/1.1**2)
 assert r['ranked_ids']==['A']
def test_unsourced_pass_cannot_rank():
 p=fixture();p['alternatives'][0]['legal']['source']='';r=analyze_hbu(p);assert r['ranked_ids']==[];assert 'INCOMPLETE' in r['conclusion']
def test_missing_timing_unknown():
 p=fixture();del p['alternatives'][0]['timed_appraisal'];assert analyze_hbu(p)['alternatives'][0]['financial']=='UNKNOWN'
def test_negative_npv_not_eligible():
 p=fixture();p['alternatives'][0]['timed_appraisal']['cash_flows_sar']=[-6000000,0,100];assert analyze_hbu(p)['ranked_ids']==[]
def test_failed_legal_gate():
 p=fixture();p['alternatives'][0]['legal']['status']='FAIL';assert analyze_hbu(p)['ranked_ids']==[]
def test_duplicate_rejected():
 p=fixture();p['alternatives']*=2
 with pytest.raises(ValueError):analyze_hbu(p)
@pytest.mark.parametrize('value',[float('nan'),True,-1])
def test_invalid_budget(value):
 p=fixture();p['alternatives'][0]['budget']['gdv']=value
 with pytest.raises(ValueError):analyze_hbu(p)
def test_tie_preserved():
 p=fixture();b=copy.deepcopy(p['alternatives'][0]);b['id']='B';p['alternatives'].append(b);assert analyze_hbu(p)['best_screened_candidates']==['A','B']
