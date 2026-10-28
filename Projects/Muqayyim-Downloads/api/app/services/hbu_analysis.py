"""Evidence-gated HBU screening using Mizan's existing static residual calculator."""
import copy
import datetime as dt
import hashlib
import json
import math
from api.app.services.valuation_calculations import calculate

VERSION='mizan.hbu-screen.1'
COST_KEYS=['gdv','construction_cost_total','professional_fees','financing_cost','selling_cost_total','contingency','developer_profit']

def number(value,label,minimum=None):
    if not isinstance(value,(float,int)) or isinstance(value,bool) or not math.isfinite(value):raise ValueError(f'{label} must be finite numeric')
    if minimum is not None and value<minimum:raise ValueError(f'{label} must be >= {minimum}')
    return value

def gate(item):
    if not isinstance(item,dict):return 'UNKNOWN'
    status=item.get('status','UNKNOWN')
    if status not in {'PASS','FAIL','UNKNOWN'}:raise ValueError('Gate status must be PASS, FAIL or UNKNOWN')
    if status=='UNKNOWN':return status
    # Evidence is declared by a reviewer, not authenticated by this function.
    source=item.get('source');date=item.get('date')
    if not isinstance(source,str) or not source.strip() or not item.get('reviewed_by'):return 'UNKNOWN'
    try:dt.date.fromisoformat(date)
    except (ValueError,TypeError):return 'UNKNOWN'
    return status

def analyze_hbu(payload):
    land=number(payload.get('land_area_sqm'),'land_area_sqm',.000001)
    options=payload.get('alternatives')
    if not isinstance(options,list) or not options:raise ValueError('At least one alternative required')
    ids=[x.get('id') for x in options]
    if any(not isinstance(x,str) or not x.strip() for x in ids) or len(set(ids))!=len(ids):raise ValueError('Alternative IDs must be unique and nonempty')
    results=[]
    for option in options:
        budget=option.get('budget',{})
        for key in COST_KEYS:number(budget.get(key),key,0)
        legal=gate(option.get('legal'));physical=gate(option.get('physical'))
        residual=calculate('residual_land',budget,[],include_sensitivity=True)
        appraisal=option.get('timed_appraisal');npv=None;financial='UNKNOWN'
        if appraisal is not None:
            flows=appraisal.get('cash_flows_sar');rate=number(appraisal.get('discount_rate'),'discount_rate',0)
            if not isinstance(flows,list) or len(flows)<2:raise ValueError('Timed appraisal needs time0 plus future annual cash flows')
            for value in flows:number(value,'cash flow')
            if flows[0]>=0:raise ValueError('Time0 must include a negative acquisition/development outlay')
            if not appraisal.get('source') or not appraisal.get('assumptions_note'):raise ValueError('Timed appraisal source and assumptions note required')
            npv=sum(x/(1+rate)**i for i,x in enumerate(flows))
            if not math.isfinite(npv):raise ValueError('Timed appraisal produced a non-finite NPV')
            financial='PASS' if npv>=0 else 'FAIL'
            if residual['value']<0:financial='FAIL'
        eligible=legal==physical==financial=='PASS'
        results.append({'id':option['id'],'name':option.get('name',option['id']),'legal':legal,'physical':physical,'financial':financial,'eligible_for_screened_ranking':eligible,'residual_land_sar':residual['value'],'residual_sar_sqm':residual['value']/land,'project_npv_sar':npv,'inputs':copy.deepcopy(option),'static_residual':residual})
    ranked=sorted([r for r in results if r['eligible_for_screened_ranking']],key=lambda r:r['residual_land_sar'],reverse=True)
    for rank,row in enumerate(ranked,1):row['screened_rank']=rank
    best=[x['id'] for x in ranked if math.isclose(x['residual_land_sar'],ranked[0]['residual_land_sar'],abs_tol=.01,rel_tol=0)] if ranked else []
    incomplete=any('UNKNOWN' in [r['legal'],r['physical'],r['financial']] for r in results)
    return {'version':VERSION,'currency':'SAR','input_sha256':hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()).hexdigest(),'alternatives':results,'ranked_ids':[r['id'] for r in ranked],'best_screened_candidates':best,'conclusion':'INCOMPLETE EVIDENCE — no final HBU determination' if incomplete else 'SCREENED COMPARISON — professional HBU determination pending','limitations':['Ranking uses static residual across eligible alternatives, not a substitute for consistent timed residual land values.','Legal/physical evidence is reviewer-declared and has not been independently authenticated.','Timed cash flows must include land, development, taxes and disposal consistently; supplied cash flows are not derived from the static budget.','No geometry, planning lookup, market demand model or automatic legal opinion.','AI-written narratives must use these outputs and sources without inventing planning or market facts.']}
