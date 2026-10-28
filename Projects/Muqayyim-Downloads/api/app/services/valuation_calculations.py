"""Financial calculations separated from API/UI; no market rates or prices are invented."""
from decimal import Decimal
import math
from api.app.services.legacy_valuation import engines
from api.app.services.comparable_adjustments import analyse

VERSION = 'mizan.map-workflow.3'  # .3: reviewed comparable adjustment grid for sales comparison


def calculate(method, v, eligible, *, include_sensitivity=True, adjustments=None, as_of=None):
    Income, Cost, legacy_hash = engines()
    result = {'method': method, 'currency': 'SAR', 'confidence': None, 'calculation_version': VERSION,
              'legacy_engine_hash': legacy_hash, 'limitations': []}
    if method == 'sales_comparison':
        grid = analyse(eligible, adjustments, v['area_sqm'], str(as_of) if as_of else None)
        if grid['gaps']:
            raise ValueError('; '.join(grid['gaps']))
        rate = grid['concluded_sar_sqm']
        rates = [r['raw_sar_sqm'] for r in grid['rows']]
        applied = sum(len(r['steps']) for r in grid['rows'])
        result.update(value=rate*v['area_sqm'], price_per_sqm=rate,
            evidence={'concluded_sar_sqm': rate, 'conclusion_basis': grid['conclusion_basis'], 'weighting': grid['weighting'],
                      'comparable_count': len(grid['rows']), 'excluded_count': len(grid['excluded']), 'area_sqm': v['area_sqm'],
                      'observed_unit_price_min': min(rates), 'observed_unit_price_max': max(rates),
                      'raw_statistics': grid['raw'], 'adjusted_statistics': grid['adjusted'], 'indication': grid['indication'],
                      'applied_adjustments': applied, 'pending_adjustments': grid['pending_count'],
                      'grid': grid['rows'], 'excluded': grid['excluded'], 'conventions': grid['conventions'],
                      **({'median_sar_sqm': rate} if grid['conclusion_basis'] == 'median' and not applied else {})},
            limitations=(['Unadjusted comparable indication; differences in area basis, condition, time and location still need professional review.']
                         if not applied else ['Adjustments are reviewer judgements recorded with rationales; they are not market-derived unless their source says so.'])
                        + ['The interquartile range of adjusted unit values is not a confidence interval.']
                        + ([f"{grid['pending_count']} proposed adjustment(s) were not approved and were not applied."] if grid['pending_count'] else []))
    elif method == 'income_capitalization':
        effective = v['annual_rent']*(1-v['vacancy'])+v['other_income']
        noi = effective-v['operating_expenses']
        indication = Income().value_direct_cap(noi, v['cap_rate'])
        result.update(value=indication.value_mid, evidence={'effective_gross_income': effective, 'noi': noi, 'cap_rate': v['cap_rate']})
    elif method == 'dcf':
        n = int(v['holding_years'])
        flows, schedule = [], []
        for year in range(1, n+1):
            rent = v['annual_rent']*(1+v['rent_growth'])**(year-1)
            expense = v['operating_expenses']*(1+v['expense_growth'])**(year-1)
            noi = rent*(1-v['vacancy'])+v['other_income']-expense
            cash = noi-v['annual_capex']
            flows.append(cash)
            schedule.append({'year': year, 'gross_rent': rent, 'expenses': expense, 'noi': noi,
                             'capex': v['annual_capex'], 'unlevered_cash_flow': cash})
        next_noi = v['annual_rent']*(1+v['rent_growth'])**n*(1-v['vacancy'])+v['other_income']-v['operating_expenses']*(1+v['expense_growth'])**n
        terminal = next_noi/v['exit_cap_rate']*(1-v['selling_cost'])
        indication = Income().value_dcf(flows, terminal, v['discount_rate'])
        result.update(value=indication.value_mid, evidence={'schedule': schedule, 'exit_noi': next_noi,
            'net_terminal_value': terminal, 'discount_rate': v['discount_rate'], 'exit_cap_rate': v['exit_cap_rate']},
            limitations=['Unlevered annual property cash flows; debt, tenant-level leasing, taxes and varying occupancy are not modeled.'])
    elif method == 'cost':
        rcn = v['building_area']*v['construction_cost']*(1+v['soft_cost_ratio'])
        depreciation = v['physical_depreciation']+v['functional_obsolescence']+v['economic_obsolescence']
        indication = Cost().value_from_rcn(v['land_value'], rcn, depreciation)
        result.update(value=indication.value_mid, evidence={'land_value': v['land_value'], 'replacement_cost_new': rcn,
            'total_depreciation_ratio': depreciation, 'depreciated_building_value': rcn*(1-depreciation)})
    elif method == 'residual_land':
        keys = ['construction_cost_total', 'professional_fees', 'financing_cost', 'selling_cost_total', 'contingency', 'developer_profit']
        total = sum(Decimal(str(v[k])) for k in keys)
        residual = Decimal(str(v['gdv']))-total
        result.update(value=float(residual), evidence={'gdv': v['gdv'], 'deductions_including_required_profit': float(total)},
            limitations=['Static residual budget; no development timing or leveraged returns modeled.'])
    else:
        raise ValueError('Method not implemented')
    if not math.isfinite(result['value']):
        raise ValueError('Calculation produced a non-finite result')
    if result['value'] < 0:
        result['limitations'].append('The selected assumptions produce a negative indication; review economic feasibility.')
    if include_sensitivity:
        result['sensitivity'] = sensitivity(method, v, eligible)
    return result


def sensitivity(method, values, eligible):
    """Mechanical stresses around supplied assumptions, never market forecasts.

    Rate shifts are percentage points, currency shifts are proportional. Reuse
    the exact base calculator so the center cell must reproduce the saved value.
    """
    configurations = {
        'income_capitalization': ('annual_rent', 'Gross annual rent', 'relative', [-0.1, 0, 0.1],
                                  'cap_rate', 'Capitalization rate', 'points', [-0.01, 0, 0.01]),
        'dcf': ('discount_rate', 'Discount rate', 'points', [-0.01, 0, 0.01],
                'exit_cap_rate', 'Exit capitalization rate', 'points', [-0.01, 0, 0.01]),
        'cost': ('construction_cost', 'Construction cost SAR/sqm', 'relative', [-0.1, 0, 0.1],
                 'physical_depreciation', 'Physical depreciation', 'points', [-0.05, 0, 0.05]),
        'residual_land': ('gdv', 'Gross development value', 'relative', [-0.1, 0, 0.1],
                          'construction_cost_total', 'Construction budget', 'relative', [-0.1, 0, 0.1]),
    }
    if method not in configurations:
        return None  # No implicit alteration of observed sales evidence.
    x, xlabel, xtype, xshifts, y, ylabel, ytype, yshifts = configurations[method]
    def shifted(key, kind, shifts):
        return [values[key] * (1+s) if kind == 'relative' else values[key]+s for s in shifts]
    xs, ys = shifted(x, xtype, xshifts), shifted(y, ytype, yshifts)
    from api.app.services.valuation_catalog import METHODS
    definitions = {f['key']: f for f in METHODS[method]['fields']}
    cells = []
    for yvalue in ys:
        row=[]
        for xvalue in xs:
            stressed = {**values, x:xvalue, y:yvalue}
            invalid = None
            for key in [x,y]:
                d=definitions[key]; value=stressed[key]
                if value < d['minimum'] or (d['positive'] and value <= 0) or (d['maximum'] is not None and value>d['maximum']):
                    invalid=f"{d['label']} outside supported bounds"
            if method == 'cost' and sum(stressed[k] for k in ['physical_depreciation','functional_obsolescence','economic_obsolescence']) > 1:
                invalid='Combined depreciation exceeds 100%'
            if invalid:
                row.append({'value':None,'reason':invalid}); continue
            try:
                output=calculate(method,stressed,eligible,include_sensitivity=False)
                row.append({'value':output['value'],'reason':None})
            except (ValueError,OverflowError,ZeroDivisionError) as exc:
                row.append({'value':None,'reason':str(exc)})
        cells.append(row)
    return {'kind':'two_way_assumption_stress','x':{'key':x,'label':xlabel,'unit':definitions[x]['unit'],'values':xs},
            'y':{'key':y,'label':ylabel,'unit':definitions[y]['unit'],'values':ys},'cells':cells,
            'base_cell':{'row':1,'column':1},'currency':'SAR',
            'notice':'Mechanical assumption stresses around the saved inputs; not market forecasts, probability ranges or confidence intervals.'}
