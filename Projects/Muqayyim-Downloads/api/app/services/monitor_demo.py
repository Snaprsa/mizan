"""A synthetic demonstration fund, built only when asked for and removable in one action.

Inputs and sales are made up from a fixed seed and labelled. Values are not: every one comes from the same
pipeline a real asset uses, so history, attribution, grades and alerts are computed rather than scripted.
Demo properties stay off the map and out of Properties, and their sales never reach a real valuation.
"""
import random
from datetime import date, timedelta
from sqlalchemy import delete, select, update
from api.app.models.foundation import Property, PropertyAssumption, PropertyRevision
from api.app.models.monitor import MonitorAlert, MonitorEvent, Portfolio, PortfolioAsset, ValuationSnapshot
from api.app.schemas.foundation import PropertyInput
from api.app.services.analysis_workflow import saudi_today
from api.app.services.foundation import owner_id, search_columns
from api.app.services.monitor import assess, refresh, settings_of
from api.app.services.monitor_calc import DEFAULT_SETTINGS
from api.app.services.valuation_catalog import METHODS

SOURCE = 'SYNTHETIC DEMO DATA'
FUND = 'DEMO · Mizan Saudi Real Estate Fund'
CITIES = {'Riyadh': (24.7136, 46.6753, ['Al Olaya', 'Al Malaz', 'King Fahd', 'Al Wurud']), 'Jeddah': (21.5433, 39.1728, ['Al Rawdah', 'Al Salamah', 'Al Khalidiyah']),
          'Khobar': (26.2172, 50.1971, ['Al Aqrabiyah', 'Al Corniche']), 'Dammam': (26.4207, 50.0888, ['Al Faisaliyah', 'Al Shatea'])}
# type: synthetic cap rate, rent SAR/m²/yr, sale SAR/m² range is derived from those.
TYPES = {'office': (.08, 1150), 'residential_building': (.07, 620), 'logistics': (.078, 380), 'retail': (.082, 1500), 'mixed_use': (.076, 1000)}
ASSET_COUNT = 72


def quarter_ends(today, count=8):
    ends, year, month = [], today.year, today.month
    while len(ends) < count:
        month -= 1
        if month == 0: month, year = 12, year-1
        if month in (3, 6, 9, 12):
            next_month = date(year+(month == 12), 1 if month == 12 else month+1, 1)
            end = next_month-timedelta(days=1)
            if end < today: ends.append(end)
    return sorted(ends)


def plan_assets(rng):
    """Mostly ordinary assets, plus a few with a story so the journey has something to find."""
    assets, types = [], list(TYPES)+['land']
    for i in range(ASSET_COUNT):
        city = rng.choices(list(CITIES), weights=[5, 3, 2, 2])[0]
        kind = types[i % len(types)]
        lat, lng, districts = CITIES[city]
        assets.append(dict(index=i+1, city=city, kind=kind, district=rng.choice(districts), lat=lat+rng.uniform(-.05, .05), lng=lng+rng.uniform(-.05, .05),
            area=rng.randint(1200, 26000), own=rng.choice([100, 100, 100, 75, 50]), story=None, debt_ratio=rng.choice([0, 0, .3, .4, .45, .5]),
            full=rng.random() < .45, cost=rng.random() < .3))
    stories = {3: 'decline', 15: 'decline', 28: 'decline', 8: 'divergence', 33: 'divergence', 12: 'stale', 40: 'stale', 21: 'leverage', 50: 'leverage', 44: 'upside', 57: 'upside', 62: 'no_official', 66: 'no_official'}
    for index, story in stories.items():
        a = assets[index]
        a['story'] = story
        if a['kind'] == 'land': a['kind'] = 'office'
        if story == 'decline': a['city'], a['kind'] = 'Jeddah', 'logistics'; a['lat'], a['lng'] = 21.5433+rng.uniform(-.05, .05), 39.1728+rng.uniform(-.05, .05); a['district'] = 'Al Khalidiyah'
        if story == 'leverage': a['debt_ratio'] = .68
    return assets


def _sale(rng, a, n, day, sar_sqm):
    lat, lng = a['lat']+rng.uniform(-.012, .012), a['lng']+rng.uniform(-.012, .012)
    area = max(200, int(a['area']*rng.uniform(.5, 1.4)))
    return {'id': f"comparable:demo-{a['index']}-{n}", 'entity_id': f"demo-{a['index']}-{n}", 'kind': 'transaction', 'title': f"DEMO · Sale {n} near asset {a['index']}",
        'city': a['city'], 'district': a['district'], 'property_type': a['kind'], 'coordinates': [lat, lng], 'location_precision': 'source_reported',
        'date': day.isoformat(), 'date_basis': 'transaction_date', 'evidence_type': 'transaction_achieved', 'status': 'active', 'price': sar_sqm*area, 'currency': 'SAR',
        'area_sqm': area, 'price_per_sqm': sar_sqm, 'source': SOURCE, 'source_id': 'demo', 'reliability_score': 1, 'case_id': None, 'href': '', 'attributes': {'is_demo': True}}


def build_inputs(a, step, steps, market):
    """This asset's synthetic inputs at one point in time, from its city-and-sector path and its story."""
    base_cap, rent_sqm = TYPES.get(a['kind'], TYPES['office'])
    progress = step/max(1, steps-1)
    key = (a['city'], a['kind'])
    cap = base_cap+market[key]['cap']*progress
    rent = a['area']*rent_sqm*(1+a['rent_jitter'])*(1+market[key]['rent']*progress)
    vacancy = a['vacancy']
    if a['story'] == 'decline':
        cap += .012*progress; vacancy = min(.45, vacancy+.22*max(0, progress-.3)/.7)
    if a['story'] == 'upside':
        rent *= 1+.16*progress; vacancy = max(.02, vacancy-.05*progress)
    opex = rent*a['opex']
    return {'annual_rent': round(rent, -2), 'vacancy': round(vacancy, 4), 'other_income': round(rent*.015, -2), 'operating_expenses': round(opex, -2), 'cap_rate': round(cap, 4)}


def all_inputs(a, income):
    cap = income['cap_rate']
    out = {'income_capitalization': income} if a['kind'] != 'land' else {}
    if a['kind'] != 'land' and a['full']:
        out['dcf'] = {**income, 'rent_growth': .02, 'expense_growth': .025, 'annual_capex': round(income['annual_rent']*.02, -2), 'holding_years': 5.0,
                      'discount_rate': round(cap+.025, 4), 'exit_cap_rate': round(cap+.0025, 4), 'selling_cost': .015}
        out['dcf'].pop('cap_rate')
    if a['kind'] != 'land' and a['cost']:
        # Sized from the asset's opening income value, then held, so cost sits near the other methods as it would in practice.
        out['cost'] = {'land_value': a['cost_land'], 'building_area': float(a['area']), 'construction_cost': a['cost_build'], 'soft_cost_ratio': .12,
                       'physical_depreciation': .18, 'functional_obsolescence': .03, 'economic_obsolescence': .02}
    out['sales_comparison'] = {'area_sqm': float(a['area'])}
    return out


async def write_assumptions(db, prop, inputs, day):
    existing = {r.key: r for r in await db.scalars(select(PropertyAssumption).where(PropertyAssumption.property_id == prop.id))}
    statuses = {'cap_rate': 'market_derived', 'exit_cap_rate': 'market_derived', 'discount_rate': 'market_derived', 'construction_cost': 'market_derived'}
    for method, values in inputs.items():
        definitions = {f['key']: f for f in METHODS[method]['fields']}
        for key, value in values.items():
            name = f'valuation_{method}_{key}'
            row = existing.get(name)
            data = {'name': definitions[key]['label'], 'value': value, 'unit': definitions[key]['unit'], 'category': 'valuation:'+method, 'source': SOURCE,
                    'as_of': day.isoformat(), 'status': statuses.get(key, 'observed'), 'user_override': None, 'notes': 'Synthetic input for the demo portfolio'}
            if row is None:
                db.add(PropertyAssumption(property_id=prop.id, key=name, data=data))
            else:
                row.data = data
    await db.flush()


async def create_demo_portfolio(db, user):
    if await db.scalar(select(Portfolio).where(Portfolio.created_by == owner_id(user), Portfolio.is_demo.is_(True))):
        return None
    rng, today = random.Random(20261031), saudi_today()
    steps = quarter_ends(today)+[today]
    portfolio = Portfolio(created_by=owner_id(user), name=FUND, asset_manager='DEMO · Fictional manager',
        settings=dict(DEFAULT_SETTINGS), is_demo=True)
    db.add(portfolio); await db.flush()
    plans = plan_assets(rng)
    market = {(c, k): {'cap': rng.uniform(-.006, .007), 'rent': rng.uniform(-.03, .09)} for c in CITIES for k in [*TYPES, 'land']}
    settings = settings_of(portfolio)
    pairs = []
    for a in plans:
        a['rent_jitter'], a['vacancy'], a['opex'] = rng.uniform(-.1, .1), rng.uniform(.04, .16), rng.uniform(.14, .26)
        name = f"DEMO · Asset {a['index']:03d}"
        data = PropertyInput(name=name, property_type=a['kind'], location={'latitude': a['lat'], 'longitude': a['lng'], 'city': a['city'], 'district': a['district'],
            'coordinate_source': 'imported', 'coordinate_precision': 'approximate'}, provenance={'source': SOURCE, 'collected_on': steps[0], 'notes': 'Fictional property'},
            analysis={'method': 'income_capitalization' if a['kind'] != 'land' else 'sales_comparison', 'as_of': today}).model_dump(mode='json')
        prop = Property(data=data, created_by=owner_id(user), is_demo=True, **search_columns(data))
        db.add(prop); await db.flush()
        asset = PortfolioAsset(portfolio_id=portfolio.id, property_id=prop.id, ownership_pct=a['own'], next_formal_on=today+timedelta(days=rng.randint(10, 80)),
            acquisition_date=steps[0]-timedelta(days=rng.randint(200, 1500)), monitoring_frequency='daily', formal_frequency='quarterly', facts={}, summary={}, demo_evidence=[])
        db.add(asset); await db.flush()
        pairs.append((a, prop, asset))
    await db.flush()
    for step, day in enumerate(steps):
        for a, prop, asset in pairs:
            income = build_inputs(a, step, len(steps), market)
            noi = income['annual_rent']*(1-income['vacancy'])+income['other_income']-income['operating_expenses']
            sar_sqm = (noi/income['cap_rate']/a['area']) if a['kind'] != 'land' else 3000*(1+market[(a['city'], 'office')]['rent']*step/len(steps))*(1+a['rent_jitter'])
            if a['story'] == 'divergence': sar_sqm *= 1.38
            if a['story'] == 'decline': sar_sqm *= 1-.05*step/len(steps)
            # A sale or two each quarter; stale assets stop getting new evidence early, so their grade and method set decay on their own.
            frozen = a['story'] == 'stale' and step > 2
            sales = 4 if step == 0 else 0 if frozen else rng.randint(1, 2)
            for _ in range(sales):
                n = len(asset.demo_evidence)+1
                when = max(day-timedelta(days=rng.randint(5, 80)), date(2000, 1, 1))
                asset.demo_evidence = [*asset.demo_evidence, _sale(rng, a, n, when, round(sar_sqm*rng.uniform(.93, 1.07), 2))]
            if step == 0 and a['kind'] != 'land':
                opening = noi/income['cap_rate']
                a['cost_land'] = round(opening*.32, -3)
                a['cost_build'] = round(opening*.8/(a['area']*1.12*.77), 0)
            if not frozen:
                await write_assumptions(db, prop, all_inputs(a, income), day)
            await assess(db, asset, prop, user, settings, as_of=day.isoformat())
            if asset.acquisition_cost_sar is None and (asset.summary or {}).get('value'):
                value = asset.summary['value']
                asset.acquisition_cost_sar = round(value*rng.uniform(.82, 1.02), -3)
                asset.book_value_sar = round(value*rng.uniform(.95, 1.03), -3)
                if a['debt_ratio']: asset.debt_sar = round(value*a['debt_ratio'], -3)
            if day.month in (6, 12) and a['story'] != 'no_official' and (asset.summary or {}).get('value'):
                official = round(asset.summary['value']*rng.uniform(.985, 1.015), -3)
                db.add(ValuationSnapshot(property_id=prop.id, kind='official', valued_on=day, value_sar=official, trigger='official_valuation', origin='demo',
                    created_by=owner_id(user), data={'schema_version': 'mizan.monitor-official.v1', 'valuer': 'DEMO · Fictional valuer', 'note': 'Synthetic official valuation'}))
                await db.flush()
                # Summary reads the official row, so reassess picks it up without a new snapshot.
                await assess(db, asset, prop, user, settings, as_of=day.isoformat())
        await refresh(db, portfolio, day.isoformat())
    return portfolio


async def remove_demo_portfolio(db, user):
    """Deletes only demo-flagged rows and everything hanging off them. Real records are never touched."""
    owner = owner_id(user)
    portfolios = list(await db.scalars(select(Portfolio.id).where(Portfolio.created_by == owner, Portfolio.is_demo.is_(True))))
    props = list(await db.scalars(select(Property.id).where(Property.created_by == owner, Property.is_demo.is_(True))))
    if portfolios:
        await db.execute(delete(MonitorAlert).where(MonitorAlert.portfolio_id.in_(portfolios)))
        await db.execute(delete(PortfolioAsset).where(PortfolioAsset.portfolio_id.in_(portfolios)))
        await db.execute(delete(Portfolio).where(Portfolio.id.in_(portfolios)))
    if props:
        await db.execute(delete(MonitorEvent).where(MonitorEvent.property_id.in_(props)))
        await db.execute(update(ValuationSnapshot).where(ValuationSnapshot.property_id.in_(props)).values(previous_id=None))
        await db.execute(delete(ValuationSnapshot).where(ValuationSnapshot.property_id.in_(props)))
        await db.execute(delete(PropertyAssumption).where(PropertyAssumption.property_id.in_(props)))
        await db.execute(delete(PropertyRevision).where(PropertyRevision.property_id.in_(props)))
        await db.execute(delete(Property).where(Property.id.in_(props)))
    db.expire_all()
    return {'portfolios': len(portfolios), 'properties': len(props)}
