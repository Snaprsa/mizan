"""Deterministic Monitor calculations: reconciliation, attribution, evidence grade, alerts, priority, stress.

No database or UI here. Every value comes from the shared `calculate` engine; nothing is estimated by an LLM.
"""
from datetime import date
from itertools import combinations
from math import factorial
from statistics import median
from api.app.services.valuation_calculations import calculate

MODEL_VERSION = 'mizan.monitor.1'
DEFAULT_SETTINGS = {'stable_band_pct': 2, 'move_watch_pct': 5, 'move_warning_pct': 10, 'move_critical_pct': 15,
    'divergence_watch_pct': 15, 'divergence_warning_pct': 25, 'ltv_warning_pct': 60, 'ltv_critical_pct': 70,
    'stale_evidence_days': 180, 'official_age_months': 12, 'comparable_gap_pct': 10, 'concentration_watch_pct': 40}
SEVERITY_RANK = {'info': 0, 'watch': 1, 'warning': 2, 'critical': 3}

# Which driver each input belongs to, so "why did it change" reads in the valuer's terms.
DRIVERS = {'annual_rent': 'rent', 'other_income': 'rent', 'rent_growth': 'rent', 'vacancy': 'occupancy',
    'operating_expenses': 'expenses', 'expense_growth': 'expenses', 'cap_rate': 'yields', 'exit_cap_rate': 'yields', 'discount_rate': 'yields',
    'annual_capex': 'capex', 'selling_cost': 'capex', 'holding_years': 'capex', 'area_sqm': 'evidence',
    'land_value': 'construction', 'building_area': 'construction', 'construction_cost': 'construction', 'soft_cost_ratio': 'construction',
    'physical_depreciation': 'depreciation', 'functional_obsolescence': 'depreciation', 'economic_obsolescence': 'depreciation',
    'gdv': 'development', 'construction_cost_total': 'development', 'professional_fees': 'development', 'financing_cost': 'development',
    'selling_cost_total': 'development', 'contingency': 'development', 'developer_profit': 'development'}
DRIVER_LABELS = {'rent': 'Rental income', 'occupancy': 'Occupancy', 'expenses': 'Operating costs', 'yields': 'Cap rate and yields',
    'capex': 'Capex and exit costs', 'evidence': 'Comparable sales', 'construction': 'Land and construction cost', 'depreciation': 'Depreciation',
    'development': 'Development budget', 'weights': 'Method weights', 'methods': 'Methods available', 'model': 'Model version'}


def reconcile(values, weights=None):
    """Reviewer's weights when they cover what is available; otherwise the median, which invents no weights."""
    values = {k: v for k, v in values.items() if v is not None}
    if not values:
        return None, {'basis': 'none', 'weights': {}}
    usable = {k: float(w) for k, w in (weights or {}).items() if k in values and float(w) > 0}
    if usable and set(usable) == set(values):
        total = sum(usable.values())
        normal = {k: w/total for k, w in usable.items()}
        return sum(values[k]*w for k, w in normal.items()), {'basis': 'reviewer_weights', 'weights': normal}
    return median(values.values()), {'basis': 'median', 'weights': {}}


def divergence(values):
    """Spread between the highest and lowest method, as a share of the lowest. Needs two positive values."""
    values = {k: v for k, v in values.items() if v is not None and v > 0}
    if len(values) < 2:
        return None
    low, high = min(values, key=values.get), max(values, key=values.get)
    return {'spread_pct': (values[high]-values[low])/values[low]*100, 'low_method': low, 'high_method': high,
            'low': values[low], 'high': values[high]}


def value_range(values, sales_indication=None):
    """Range from what the model actually produced, not a confidence interval. One non-sales method has none."""
    points = [v for v in values.values() if v is not None]
    if sales_indication:
        points += [sales_indication.get('low'), sales_indication.get('high')]
        points = [p for p in points if p is not None]
    return (min(points), max(points)) if len(points) >= 2 else (None, None)


def run_method(method, state):
    return calculate(method, state['inputs'], state.get('comparables') or [], include_sensitivity=False,
        adjustments=state.get('adjustments'), as_of=state.get('as_of'), subject=state.get('subject'))


def _method_value(method, old, new, chosen):
    """One method's value with only the chosen drivers moved to their new inputs."""
    base, target = old.get(method), new.get(method)
    if base is None:
        return calculate_state(method, target)
    if target is None:
        return calculate_state(method, base)
    inputs = {k: (target['inputs'].get(k, v) if DRIVERS.get(k, 'other') in chosen else v) for k, v in base['inputs'].items()}
    state = dict(base, inputs=inputs)
    if 'evidence' in chosen:
        state.update(comparables=target.get('comparables'), adjustments=target.get('adjustments'), as_of=target.get('as_of'), subject=target.get('subject'))
    return calculate_state(method, state)


def calculate_state(method, state):
    return float(run_method(method, state)['value'])


def changed_drivers(old, new, old_weights=None, new_weights=None):
    found = set()
    for method in set(old) & set(new):
        a, b = old[method], new[method]
        for key in set(a['inputs']) | set(b['inputs']):
            if a['inputs'].get(key) != b['inputs'].get(key):
                found.add(DRIVERS.get(key, 'other'))
        if method == 'sales_comparison' and (
                [c.get('id') for c in a.get('comparables') or []] != [c.get('id') for c in b.get('comparables') or []]
                or a.get('adjustments') != b.get('adjustments') or a.get('subject') != b.get('subject') or a.get('as_of') != b.get('as_of')):
            found.add('evidence')
    if set(old) != set(new):
        found.add('methods')
    if (old_weights or None) != (new_weights or None):
        found.add('weights')
    return sorted(found)


def attribute(old, new, old_value, new_value, old_weights=None, new_weights=None):
    """Explain a change by rerunning the valuation with each driver moved.

    Shapley allocation over the changed drivers: the parts sum exactly to the change, and where two drivers
    interact (rent and cap rate multiply) the interaction is shared equally rather than given to whichever ran first.
    Anything the rerun cannot reproduce is reported as a model-version line, never spread over the drivers.
    """
    total = new_value-old_value
    drivers = changed_drivers(old, new, old_weights, new_weights)
    memo = {}
    def f(chosen):
        key = frozenset(chosen)
        if key not in memo:
            methods = new if 'methods' in key else old
            values = {m: _method_value(m, old, new, key) for m in methods}
            memo[key] = reconcile(values, new_weights if 'weights' in key else old_weights)[0]
        return memo[key]
    try:
        start, end = f(()), f(drivers)
        n = len(drivers)
        shares = {d: 0.0 for d in drivers}
        for d in drivers:
            others = [x for x in drivers if x != d]
            for size in range(n):
                weight = factorial(size)*factorial(n-size-1)/factorial(n)
                for subset in combinations(others, size):
                    shares[d] += weight*(f(subset+(d,))-f(subset))
    except (ValueError, ZeroDivisionError, OverflowError, KeyError, TypeError) as exc:
        return {'total': total, 'drivers': [], 'exact': False, 'basis': 'unavailable',
                'note': f'This change could not be decomposed: {exc}'}
    lines = [{'key': d, 'label': DRIVER_LABELS.get(d, 'Other inputs'), 'amount': a, 'pct': a/old_value*100 if old_value else None}
             for d, a in shares.items() if abs(a) > 0.005]
    residual = total-(end-start)
    if abs(residual) > max(1.0, abs(old_value)*1e-6):
        lines.append({'key': 'model', 'label': DRIVER_LABELS['model'], 'amount': residual, 'pct': residual/old_value*100 if old_value else None})
    lines.sort(key=lambda l: -abs(l['amount']))
    return {'total': total, 'drivers': lines, 'exact': True, 'basis': 'rerun_shapley',
            'note': 'Calculated by rerunning the valuation for each driver. Effects that depend on two drivers together are shared equally.'}


def _age_days(day, as_of):
    try:
        return (date.fromisoformat(str(as_of)) - date.fromisoformat(str(day))).days
    except (TypeError, ValueError):
        return None


def evidence_grade(methods, as_of, settings=None, demonstration=False):
    """A rule-based grade of the evidence behind a value. Checks are listed so it can be challenged.

    It is deliberately not a percentage: nothing here has been calibrated against achieved prices.
    A real asset that leans on demo sales is always low; a demo portfolio is graded on its own synthetic
    evidence so it can show differences, and carries the demo label instead.
    """
    s = {**DEFAULT_SETTINGS, **(settings or {})}
    checks = []
    def check(key, label, state, detail):
        checks.append({'key': key, 'label': label, 'state': state, 'detail': detail})
    values = {m: v.get('value') for m, v in methods.items()}
    check('methods', 'Methods', 'good' if len(values) >= 2 else 'fair' if values else 'poor',
          f'{len(values)} method{"" if len(values) == 1 else "s"} produced a value')
    spread = divergence(values)
    if spread:
        check('agreement', 'Method agreement', 'good' if spread['spread_pct'] < s['divergence_watch_pct'] else
              'fair' if spread['spread_pct'] < s['divergence_warning_pct'] else 'poor', f"{spread['spread_pct']:.0f}% between highest and lowest")
    sales = methods.get('sales_comparison')
    if sales:
        comps = sales.get('comparables') or []
        check('comparable_count', 'Comparable sales', 'good' if len(comps) >= 6 else 'fair' if len(comps) >= 3 else 'poor', f'{len(comps)} eligible')
        ages = sorted(a for a in (_age_days(c.get('date'), as_of) for c in comps) if a is not None)
        if ages:
            typical = ages[len(ages)//2]
            check('comparable_age', 'Comparable recency', 'good' if typical <= s['stale_evidence_days']/2 else
                  'fair' if typical <= s['stale_evidence_days'] else 'poor', f'Typical sale is {typical} days old')
    ages, statuses = [], []
    for method in methods.values():
        for meta in method.get('meta') or []:
            age = _age_days(meta.get('as_of'), as_of)
            if age is not None: ages.append(age)
            statuses.append(meta.get('status'))
    if ages:
        oldest = max(ages)
        check('input_age', 'Input freshness', 'good' if oldest <= s['stale_evidence_days'] else 'fair' if oldest <= s['stale_evidence_days']*2 else 'poor',
              f'Oldest input is {oldest} days old')
    if statuses:
        observed = sum(x in {'observed', 'market_derived'} for x in statuses)/len(statuses)
        check('input_source', 'Input sources', 'good' if observed >= .6 else 'fair' if observed >= .25 else 'poor', f'{observed*100:.0f}% observed or market-derived')
    uses_demo = not demonstration and any(m.get('uses_demo') for m in methods.values())
    if uses_demo:
        check('demo', 'Demo data', 'poor', 'Uses synthetic data; not a market indication')
    poor = sum(c['state'] == 'poor' for c in checks)
    good = sum(c['state'] == 'good' for c in checks)
    level = 'low' if uses_demo or poor >= 2 or not values else 'high' if not poor and good >= max(3, len(checks)-1) else 'medium'
    return {'level': level, 'checks': checks, 'passed': good, 'total': len(checks),
            'basis': 'Rule-based grade of the evidence. Not a calibrated probability.'}


def months_between(day, as_of):
    age = _age_days(day, as_of)
    return age/30.4375 if age is not None else None


def priority(summary, settings=None):
    """Which assets to formally revalue first. Points are shown, so the ranking can be argued with."""
    s = {**DEFAULT_SETTINGS, **(settings or {})}
    reasons = []
    def add(points, text):
        reasons.append({'points': points, 'reason': text})
    move = summary.get('change_vs_official_pct')
    if move is None:
        if summary.get('value') is not None: add(25, 'No official valuation on record')
    else:
        if abs(move) >= s['move_critical_pct']: add(40, f'{move:+.1f}% against the official valuation')
        elif abs(move) >= s['move_warning_pct']: add(30, f'{move:+.1f}% against the official valuation')
        elif abs(move) >= s['move_watch_pct']: add(15, f'{move:+.1f}% against the official valuation')
    age = summary.get('official_age_months')
    if age is not None:
        if age >= s['official_age_months']*1.5: add(25, f'Official valuation is {age:.0f} months old')
        elif age >= s['official_age_months']: add(15, f'Official valuation is {age:.0f} months old')
    if summary.get('confidence') == 'low': add(15, 'Low evidence grade')
    if summary.get('confidence_fell'): add(10, 'Evidence grade has fallen')
    spread = summary.get('divergence_pct')
    if spread is not None:
        if spread >= s['divergence_warning_pct']: add(15, f'Methods disagree by {spread:.0f}%')
        elif spread >= s['divergence_watch_pct']: add(8, f'Methods disagree by {spread:.0f}%')
    new_sales = summary.get('new_sales_since_official') or 0
    if new_sales >= 3: add(10, f'{new_sales} new sales since the official valuation')
    ltv = summary.get('ltv_pct')
    if ltv is not None and ltv >= s['ltv_warning_pct']: add(15, f'LTV is {ltv:.0f}%')
    score = sum(r['points'] for r in reasons)
    band = 'high' if score >= 45 else 'medium' if score >= 20 else 'low'
    reasons.sort(key=lambda r: -r['points'])
    return {'score': score, 'band': band, 'reasons': reasons}


def asset_alerts(name, summary, settings=None):
    """Conditions that hold now. Each returns (kind, severity, title, message, details)."""
    s = {**DEFAULT_SETTINGS, **(settings or {})}
    out = []
    move = summary.get('change_vs_official_pct')
    if move is not None and abs(move) >= s['move_watch_pct']:
        sev = 'critical' if abs(move) >= s['move_critical_pct'] else 'warning' if abs(move) >= s['move_warning_pct'] else 'watch'
        word = 'above' if move > 0 else 'below'
        out.append(('valuation_move', sev, f'{abs(move):.1f}% {word} official valuation',
            f'{name} is indicated {abs(move):.1f}% {word} its latest official valuation.', {'change_pct': move}))
    spread = summary.get('divergence_pct')
    if spread is not None and spread >= s['divergence_watch_pct']:
        d = summary.get('divergence') or {}
        out.append(('method_divergence', 'warning' if spread >= s['divergence_warning_pct'] else 'watch', f'Methods disagree by {spread:.0f}%',
            f"{name}: {METHOD_LABELS.get(d.get('high_method'), 'highest method')} is {spread:.0f}% above {METHOD_LABELS.get(d.get('low_method'), 'lowest method')}. "
            'Check for an unusual sale, abnormal rent or stale evidence before relying on the reconciled value.', d))
    if summary.get('confidence_fell'):
        before, after = summary.get('previous_confidence'), summary.get('confidence')
        out.append(('confidence_fall', 'warning' if after == 'low' else 'watch', f'Evidence grade fell to {after}',
            f"{name}: evidence grade fell from {before} to {after}. {summary.get('confidence_reason') or ''}".strip(), {'from': before, 'to': after}))
    ltv = summary.get('ltv_pct')
    if ltv is not None and ltv >= s['ltv_warning_pct']:
        out.append(('asset_ltv', 'critical' if ltv >= s['ltv_critical_pct'] else 'warning', f'LTV at {ltv:.1f}%',
            f'{name}: loan to indicated value is {ltv:.1f}%.', {'ltv_pct': ltv}))
    gap = summary.get('new_sale_gap')
    if gap and abs(gap['pct']) >= s['comparable_gap_pct']:
        word = 'below' if gap['pct'] < 0 else 'above'
        out.append(('comparable_gap', 'watch', f'New sale {abs(gap["pct"]):.1f}% {word} implied value',
            f"{name}: a sale dated {gap['date']} was recorded {abs(gap['pct']):.1f}% {word} the asset's implied SAR/m².", gap))
    age = summary.get('official_age_months')
    if age is not None and age >= s['official_age_months']:
        out.append(('official_age', 'watch', f'Official valuation {age:.0f} months old', f'{name}: the latest official valuation is {age:.0f} months old.', {'months': age}))
    if summary.get('stale_inputs'):
        out.append(('stale_evidence', 'watch', 'Evidence is getting old', f"{name}: {summary['stale_inputs']}", None))
    if summary.get('value') is None:
        out.append(('no_indication', 'info', 'No indicative value yet',
            f"{name}: no method has complete reviewed inputs. {'; '.join((summary.get('gaps') or [])[:2])}".strip(), None))
    return out


def portfolio_alerts(totals, settings=None):
    s = {**DEFAULT_SETTINGS, **(settings or {})}
    out = []
    ltv = totals.get('ltv_pct')
    if ltv is not None and ltv >= s['ltv_warning_pct']:
        out.append(('portfolio_ltv', 'critical' if ltv >= s['ltv_critical_pct'] else 'warning', f'Portfolio LTV at {ltv:.1f}%',
            f"Portfolio LTV is {ltv:.1f}%, against a {s['ltv_warning_pct']:.0f}% threshold.", {'ltv_pct': ltv}))
    for key, label in (('by_city', 'geography'), ('by_type', 'sector')):
        for row in totals.get(key) or []:
            if row['share_pct'] >= s['concentration_watch_pct'] and len(totals.get(key)) > 1:
                out.append((f'concentration_{label}_{row["key"]}', 'watch', f'{row["share_pct"]:.0f}% in {row["label"]}',
                    f'{row["share_pct"]:.0f}% of portfolio value is in {row["label"]}.', {'share_pct': row['share_pct']}))
    return out


METHOD_LABELS = {'sales_comparison': 'Sales comparison', 'income_capitalization': 'Income capitalization', 'dcf': 'DCF',
                 'cost': 'Cost approach', 'residual_land': 'Residual land'}

# Mechanical stresses on saved inputs. Only methods that use the input move; others hold, and the result shows that.
STRESSES = {
    'cap_50': {'label': 'Cap rates +50 bps', 'shift': {'cap_rate': ('add', .005), 'exit_cap_rate': ('add', .005)}},
    'cap_100': {'label': 'Cap rates +100 bps', 'shift': {'cap_rate': ('add', .01), 'exit_cap_rate': ('add', .01)}},
    'rent_5': {'label': 'Rents −5%', 'shift': {'annual_rent': ('scale', .95)}},
    'rent_10': {'label': 'Rents −10%', 'shift': {'annual_rent': ('scale', .90)}},
    'occupancy_10': {'label': 'Occupancy −10 pts', 'shift': {'vacancy': ('add', .10)}},
    'discount_100': {'label': 'Discount rate +100 bps', 'shift': {'discount_rate': ('add', .01)}},
}


def stressed_value(methods, weights, stress):
    """(value, changed?) with one stress applied through the same engine. None when the asset has no method."""
    values, changed = {}, False
    for method, state in methods.items():
        inputs = dict(state['inputs'])
        for key, (op, amount) in stress['shift'].items():
            if key in inputs:
                inputs[key] = inputs[key]+amount if op == 'add' else inputs[key]*amount
                if key == 'vacancy': inputs[key] = min(inputs[key], 1)
                changed = True
        try:
            values[method] = calculate_state(method, dict(state, inputs=inputs))
        except (ValueError, ZeroDivisionError, OverflowError):
            values[method] = state.get('value')
    return reconcile(values, weights)[0], changed
