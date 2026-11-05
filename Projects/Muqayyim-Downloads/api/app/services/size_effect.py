"""Market-derived size adjustment: how price per m² changes with plot or building area, measured from saved evidence.

Model (ordinary least squares on the reviewer's own evidence):
    ln(price per m²) = a + b · ln(area) [+ c · asking-price indicator]
b is the size elasticity: a plot twice as large sells for 2^b − 1 more (usually less) per m².
The adjustment for a comparable is (subject area ÷ comparable area)^b − 1.

Nothing is invented: with too little or too narrow evidence the result says so and suggests nothing.
The result is a suggestion with its evidence and fit; the valuer decides whether to use it.
"""
import math
from datetime import date, timedelta

MIN_RECORDS = 8          # fewer than this cannot separate a size effect from noise
MIN_AREA_SPREAD = 2.0    # largest ÷ smallest area must be at least this
# Two-sided 95% t critical values by degrees of freedom; 1.96 beyond the table.
T95 = {1: 12.71, 2: 4.30, 3: 3.18, 4: 2.78, 5: 2.57, 6: 2.45, 7: 2.36, 8: 2.31, 9: 2.26, 10: 2.23, 12: 2.18, 15: 2.13, 20: 2.09, 25: 2.06, 30: 2.04, 40: 2.02, 60: 2.00, 120: 1.98}


def t95(df):
    if df <= 0:
        return math.inf
    keys = sorted(T95)
    for k in keys:
        if df <= k:
            return T95[k]
    return 1.96


def solve(a, b):
    """Gaussian elimination with partial pivoting; returns None for a singular system."""
    n = len(a); m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[pivot][col]) < 1e-12:
            return None
        m[col], m[pivot] = m[pivot], m[col]
        for r in range(n):
            if r != col:
                f = m[r][col] / m[col][col]
                m[r] = [x - f * y for x, y in zip(m[r], m[col])]
    return [m[i][n] / m[i][i] for i in range(n)]


def inverse(a):
    n = len(a); cols = [solve(a, [1.0 if i == j else 0.0 for i in range(n)]) for j in range(n)]
    return None if any(c is None for c in cols) else [[cols[j][i] for j in range(n)] for i in range(n)]


def ols(rows, ys):
    k = len(rows[0]); n = len(rows)
    xtx = [[sum(r[i] * r[j] for r in rows) for j in range(k)] for i in range(k)]
    xty = [sum(r[i] * y for r, y in zip(rows, ys)) for i in range(k)]
    inv = inverse(xtx)
    if inv is None:
        return None
    beta = [sum(inv[i][j] * xty[j] for j in range(k)) for i in range(k)]
    fitted = [sum(b * x for b, x in zip(beta, r)) for r in rows]
    sse = sum((y - f) ** 2 for y, f in zip(ys, fitted))
    mean_y = sum(ys) / n; sst = sum((y - mean_y) ** 2 for y in ys)
    df = n - k
    s2 = sse / df if df > 0 else math.inf
    se = [math.sqrt(s2 * inv[i][i]) if df > 0 and inv[i][i] >= 0 else math.inf for i in range(k)]
    return {'beta': beta, 'se': se, 'df': df, 'r2': 1 - sse / sst if sst > 0 else None, 'residuals': [y - f for y, f in zip(ys, fitted)]}


def quartiles(values):
    v = sorted(values); n = len(v)
    def q(p):
        pos = (n - 1) * p; lo, hi = math.floor(pos), math.ceil(pos)
        return v[lo] + (v[hi] - v[lo]) * (pos - lo)
    return q(0.25), q(0.75)


def usable(record, property_type, as_of, lookback_days):
    if record.get('kind') not in {'transaction', 'listing'} or record.get('property_type') != property_type:
        return False
    if record.get('status') != 'active' or record.get('currency', 'SAR') != 'SAR':
        return False
    area, rate = record.get('area_sqm'), record.get('price_per_sqm')
    if not area or area <= 0 or not rate or rate <= 0:
        return False
    d = record.get('date')
    return bool(d) and (date.fromisoformat(as_of) - timedelta(days=lookback_days)).isoformat() <= d <= as_of


def derive(records, *, property_type, as_of, lookback_days, subject_area, comparables):
    """records: evidence already limited to the search area (each with area_sqm, price_per_sqm, kind, date, ...)."""
    pool = [r for r in records if usable(r, property_type, as_of, lookback_days)]
    out = {'records_considered': len(pool), 'sales': 0, 'listings': 0, 'outliers_removed': 0, 'model': None, 'suggestions': [], 'notes': []}
    # Drop extreme unit prices (outside 1.5 × interquartile range of ln price) so a few errors cannot steer the slope.
    if len(pool) >= 4:
        logs = [math.log(r['price_per_sqm']) for r in pool]
        q1, q3 = quartiles(logs); fence = 1.5 * (q3 - q1)
        kept = [r for r, y in zip(pool, logs) if q1 - fence <= y <= q3 + fence]
        out['outliers_removed'] = len(pool) - len(kept); pool = kept
    out['sales'] = sum(1 for r in pool if r['kind'] == 'transaction'); out['listings'] = len(pool) - out['sales']
    if len(pool) < MIN_RECORDS:
        out['notes'].append(f'Needs at least {MIN_RECORDS} priced sales or listings of this type with an area; found {len(pool)}. Widen the search area or add evidence.')
        return out
    areas = [r['area_sqm'] for r in pool]
    out['area_range'] = [min(areas), max(areas)]
    if max(areas) / min(areas) < MIN_AREA_SPREAD:
        out['notes'].append(f'The evidence covers too narrow a range of areas ({min(areas):,.0f}–{max(areas):,.0f} m²) to measure a size effect.')
        return out
    both = 0 < out['listings'] < len(pool)
    rows = [[1.0, math.log(r['area_sqm'])] + ([1.0 if r['kind'] == 'listing' else 0.0] if both else []) for r in pool]
    fit = ols(rows, [math.log(r['price_per_sqm']) for r in pool])
    if fit is None or fit['df'] <= 0:
        out['notes'].append('The evidence cannot separate the effect of area from the other terms.')
        return out
    b, se = fit['beta'][1], fit['se'][1]; t = t95(fit['df'])
    low, high = b - t * se, b + t * se
    model = {'elasticity': b, 'elasticity_low': low, 'elasticity_high': high, 'r2': fit['r2'], 'n': len(pool), 'df': fit['df'],
             'per_doubling': 2 ** b - 1, 'per_doubling_low': 2 ** low - 1, 'per_doubling_high': 2 ** high - 1,
             'clear': low > 0 or high < 0,
             'asking_premium': (math.exp(fit['beta'][2]) - 1) if both else None,
             'formula': 'ln(price per m²) = a + b·ln(area)' + (' + c·asking' if both else '')}
    out['model'] = model
    if not model['clear']:
        out['notes'].append('The 95% range includes zero: this evidence shows no clear size effect. Use the suggestion with caution or not at all.')
    if subject_area and not (min(areas) <= subject_area <= max(areas)):
        out['notes'].append(f'The subject area ({subject_area:,.0f} m²) is outside the evidence range ({min(areas):,.0f}–{max(areas):,.0f} m²); the suggestion extrapolates.')
    if out['listings'] and not both:
        out['notes'].append('All evidence is asking prices; the size effect of achieved sales may differ.')
    if not subject_area:
        out['notes'].append('Enter the subject area to get an adjustment for each comparable.')
        return out
    for c in comparables:
        area = c.get('area_sqm')
        if not area or area <= 0:
            out['suggestions'].append({'comparable_id': c['id'], 'area_sqm': area, 'percent': None, 'reason': 'No area recorded for this comparable'})
            continue
        ratio = subject_area / area
        out['suggestions'].append({'comparable_id': c['id'], 'area_sqm': area, 'percent': ratio ** b - 1,
                                   'low': min(ratio ** low, ratio ** high) - 1, 'high': max(ratio ** low, ratio ** high) - 1})
    return out
