"""Sales-comparison adjustment grid. Pure functions; no database, no invented adjustments.

Conventions (stated in every result):
- Everything is expressed in SAR per m² of the comparable's recorded area.
- Transactional adjustments (conditions of sale, financing, market conditions/time) are applied
  sequentially and compound, in that order. Property adjustments (location and physical) are then
  summed: percentages apply to the transaction-adjusted unit price, SAR/m² amounts are added, and
  SAR lump sums are divided by the comparable's area.
- Only reviewer-approved adjustments enter the calculation; proposed lines are reported, not applied.
- Weights are explicit (equal, inverse gross adjustment, or manual with a rationale).
"""
from datetime import date
from statistics import mean, median, pstdev
import math

TRANSACTIONAL = ['conditions_of_sale', 'financing', 'market_conditions']
PROPERTY = ['location', 'size', 'floor', 'position', 'grade', 'frontage', 'street_width', 'corner', 'shape', 'condition',
            'age', 'quality', 'occupancy', 'development_potential', 'zoning', 'other']
ORDERS = {'position': ['rear', 'side', 'front', 'corner'], 'grade': ['C', 'B', 'A', 'A+']}
RULE_LABELS = {'size': ('size', 'per 100 m²'), 'floor': ('floor', 'per floor'), 'position': ('position in the building', 'per step'),
               'grade': ('grade', 'per grade'), 'street_width': ('street width', 'per metre'), 'corner': ('corner', 'if it differs')}
FACTORS = TRANSACTIONAL + PROPERTY
HEAVY_GROSS = 0.25   # gross adjustment above 25% is flagged as heavily adjusted
INVERSE_FLOOR = 0.05  # inverse-gross weights use 1 / (gross + 5%) so unadjusted sales do not dominate infinitely


def months_between(earlier: str, later: str) -> float:
    a, b = date.fromisoformat(earlier), date.fromisoformat(later)
    return (b - a).days / 30.4375


def quantile(sorted_values, q):
    pos = (len(sorted_values) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (pos - lo)


def weighted_median(values, weights):
    """Lower weighted median: the smallest value whose cumulative weight reaches half the total."""
    pairs = sorted(zip(values, weights))
    total = sum(weights); running = 0.0
    for value, weight in pairs:
        running += weight
        if running >= total / 2 - 1e-12:
            return value
    return pairs[-1][0]


def statistics(values, weights=None):
    if not values:
        return None
    ordered = sorted(values)
    out = {'n': len(values), 'mean': mean(values), 'median': median(values), 'min': ordered[0], 'max': ordered[-1],
           'p25': quantile(ordered, 0.25), 'p75': quantile(ordered, 0.75),
           'std': pstdev(values) if len(values) > 1 else 0.0}
    out['cv'] = out['std'] / out['mean'] if out['mean'] else None
    if weights:
        total = sum(weights)
        out['weighted_mean'] = sum(v * w for v, w in zip(values, weights)) / total
        out['weighted_median'] = weighted_median(values, weights)
    return out


def rule_difference(factor, subject, comp, subject_area):
    """Subject minus comparable in the rule's units. None means a value is unknown: no adjustment is made."""
    attributes = comp.get('attributes') or {}
    if factor == 'size':
        area = comp.get('area_sqm')
        return (subject_area - area) / 100 if subject_area and area else None
    if factor == 'floor':
        a, b = subject.get('floor'), attributes.get('floor')
        return a - b if a is not None and b is not None else None
    if factor in ORDERS:
        a, b = subject.get(factor), attributes.get(factor)
        order = ORDERS[factor]
        return order.index(a) - order.index(b) if a in order and b in order else None
    if factor == 'street_width':
        a, b = subject.get('street_width_m'), attributes.get('street_width_m')
        return a - b if a is not None and b is not None else None
    if factor == 'corner':
        a, b = subject.get('corner'), attributes.get('corner')
        return int(a) - int(b) if a is not None and b is not None else None
    return None


def rule_lines(comp, rules, manual, subject, subject_area):
    """Per-comparable lines from the approved rules. An approved manual line for the same factor overrides the rule."""
    lines, notes = [], []
    for rule in rules or []:
        if rule.get('status') != 'approved' or rule['factor'] in manual:
            continue
        name, unit = RULE_LABELS[rule['factor']]
        difference = rule_difference(rule['factor'], subject or {}, comp, subject_area)
        if difference is None:
            notes.append(f"No {name} adjustment: the value is not recorded for this sale or the subject.")
        elif difference:
            lines.append({'comparable_id': comp['id'], 'factor': rule['factor'], 'basis': 'percent', 'amount': rule['percent'] * difference,
                'rationale': f"{rule['percent']:+.1%} {unit} × {difference:g}", 'source': rule['source'], 'status': 'approved', 'derived': True})
    return lines, notes


def adjust_comparable(comp, lines, time_rule, as_of):
    """Returns the step-by-step adjustment trail for one comparable."""
    raw = comp['price_per_sqm']; area = comp.get('area_sqm')
    steps, notes, pending = [], [], []
    unit = raw
    approved = [l for l in lines if l['status'] == 'approved']
    pending = [l for l in lines if l['status'] != 'approved']
    by_factor = {}
    for line in approved:
        by_factor.setdefault(line['factor'], []).append(line)

    def to_unit(line, base):
        if line['basis'] == 'percent':
            return base * line['amount']
        if line['basis'] == 'sar_per_sqm':
            return line['amount']
        if not area or area <= 0:
            raise ValueError(f"{comp['id']}: a SAR lump-sum adjustment needs the comparable's area")
        return line['amount'] / area

    # 1. Transactional adjustments compound in a fixed order.
    for factor in TRANSACTIONAL:
        lines_for = list(by_factor.get(factor, []))
        if factor == 'market_conditions' and time_rule and time_rule.get('status') == 'approved':
            if not as_of or not comp.get('date'):
                raise ValueError(f"{comp['id']}: the time adjustment needs the sale date and the valuation date")
            months = months_between(comp['date'], as_of)
            pct = (1 + time_rule['annual_rate']) ** (months / 12) - 1
            lines_for.insert(0, {'factor': 'market_conditions', 'basis': 'percent', 'amount': pct,
                'rationale': f"{time_rule['annual_rate']:.2%}/year × {months:.1f} months from {comp['date']} to {as_of}",
                'source': time_rule['source'], 'status': 'approved', 'derived': True})
        for line in lines_for:
            delta = to_unit(line, unit)
            steps.append({**line, 'stage': 'transactional', 'base_sar_sqm': unit, 'delta_sar_sqm': delta, 'result_sar_sqm': unit + delta})
            unit += delta
    transaction_adjusted = unit
    # 2. Property adjustments are additive on the transaction-adjusted unit price.
    total = 0.0
    for factor in PROPERTY:
        for line in by_factor.get(factor, []):
            delta = to_unit(line, transaction_adjusted)
            total += delta
            steps.append({**line, 'stage': 'property', 'base_sar_sqm': transaction_adjusted, 'delta_sar_sqm': delta})
    adjusted = transaction_adjusted + total
    if not math.isfinite(adjusted):
        raise ValueError(f"{comp['id']}: adjustments produce a non-finite unit value")
    gross = sum(abs(s['delta_sar_sqm']) for s in steps) / raw if raw else None
    net = (adjusted - raw) / raw if raw else None
    if adjusted <= 0:
        notes.append('Adjusted unit value is zero or negative; review the adjustments.')
    if gross is not None and gross > HEAVY_GROSS:
        notes.append(f'Heavily adjusted: gross adjustment {gross:.0%} exceeds {HEAVY_GROSS:.0%}.')
    return {'id': comp['id'], 'title': comp.get('title'), 'date': comp.get('date'), 'area_sqm': area, 'attributes': comp.get('attributes') or {},
            'distance_km': comp.get('distance_km'), 'raw_sar_sqm': raw, 'transaction_adjusted_sar_sqm': transaction_adjusted,
            'adjusted_sar_sqm': adjusted, 'gross_adjustment': gross, 'net_adjustment': net,
            'steps': steps, 'pending': pending, 'notes': notes}


def analyse(eligible, setup, subject_area, as_of, subject=None):
    """Adjust eligible comparables and reconcile them to one unit value. Raises ValueError on invalid setups."""
    setup = setup or {}
    # Callers outside the API may pass comparables without IDs; use stable positional IDs.
    eligible = [c if c.get('id') else {**c, 'id': f'#{i + 1}'} for i, c in enumerate(eligible)]
    lines = setup.get('lines') or []
    exclusions = setup.get('exclusions') or {}
    ids = {c['id'] for c in eligible}
    orphaned = [l for l in lines if l['comparable_id'] not in ids]
    rows, excluded = [], []
    for comp in eligible:
        own = [l for l in lines if l['comparable_id'] == comp['id']]
        derived, rule_notes = rule_lines(comp, setup.get('rules'), {l['factor'] for l in own if l['status'] == 'approved'}, subject, subject_area)
        trail = adjust_comparable(comp, own + derived, setup.get('time'), as_of)
        trail['notes'] = rule_notes + trail['notes']
        if comp['id'] in exclusions:
            excluded.append({**trail, 'exclusion_reason': exclusions[comp['id']]})
        else:
            rows.append(trail)
    gaps = []
    if len(rows) < 3:
        gaps.append(f'At least 3 comparables must remain after reviewed exclusions; {len(rows)} remain')
    if any(r['adjusted_sar_sqm'] <= 0 for r in rows):
        gaps.append('An included comparable has a zero or negative adjusted unit value')
    weighting = setup.get('weighting', 'equal')
    if weighting == 'manual':
        manual = setup.get('manual_weights') or {}
        missing = [r['id'] for r in rows if r['id'] not in manual]
        if missing:
            gaps.append(f'Manual weighting needs a weight for every included comparable ({len(missing)} missing)')
        if not (setup.get('weighting_rationale') or '').strip():
            gaps.append('Manual weighting needs a written rationale')
        weights = [float(manual.get(r['id'], 0)) for r in rows]
    elif weighting == 'inverse_gross_adjustment':
        weights = [1 / (INVERSE_FLOOR + (r['gross_adjustment'] or 0)) for r in rows]
    else:
        weights = [1.0] * len(rows)
    if rows and sum(weights) <= 0:
        gaps.append('Comparable weights must sum to more than zero')
    total_weight = sum(weights) or 1
    for r, w in zip(rows, weights):
        r['weight'] = w / total_weight
    raw_stats = statistics([r['raw_sar_sqm'] for r in rows])
    adjusted_values = [r['adjusted_sar_sqm'] for r in rows]
    adjusted_stats = statistics(adjusted_values, [r['weight'] for r in rows]) if rows and not gaps else statistics(adjusted_values)
    # Explainable outlier flags (Tukey fences); flags never exclude evidence automatically.
    if len(rows) >= 4:
        q1, q3 = adjusted_stats['p25'], adjusted_stats['p75']; fence = 1.5 * (q3 - q1)
        for r in rows:
            if r['adjusted_sar_sqm'] < q1 - fence or r['adjusted_sar_sqm'] > q3 + fence:
                r['notes'].append(f'Outside the interquartile fences ({q1 - fence:,.0f}–{q3 + fence:,.0f} SAR/m²); review or exclude with a reason.')
    basis = setup.get('conclusion_basis', 'median')
    concluded = None
    if not gaps and adjusted_stats:
        concluded = adjusted_stats.get(basis)
    indication = None
    if concluded is not None and subject_area:
        indication = {'low': adjusted_stats['p25'] * subject_area, 'base': concluded * subject_area,
                      'high': adjusted_stats['p75'] * subject_area,
                      'basis': 'Low/high are the interquartile adjusted unit values × subject area; not a confidence interval.'}
    pending = sum(len(r['pending']) for r in rows + excluded)
    demo_count = sum(1 for r in rows if r['attributes'].get('is_demo'))
    return {'rows': rows, 'excluded': excluded, 'orphaned_lines': orphaned, 'pending_count': pending, 'demo_count': demo_count,
            'raw': raw_stats, 'adjusted': adjusted_stats, 'weighting': weighting, 'conclusion_basis': basis,
            'concluded_sar_sqm': concluded, 'indication': indication, 'gaps': gaps,
            'conventions': ['Unit values are SAR per m² of each comparable\'s recorded area.',
                            'Transactional adjustments compound in order: conditions of sale → financing → market conditions (time).',
                            'Property adjustments are additive on the transaction-adjusted unit value.',
                            'Only approved adjustments are applied; proposed lines are listed but ignored.',
                            'Rules use subject minus comparable. Unknown values get no adjustment; a manual line for the same factor overrides the rule.',
                            'Outlier flags are informational; exclusions require a reviewer reason.']}
