"""Method-specific requirements are shared by preparation, validation and the UI."""


def field(key, label, unit, minimum=0, maximum=None, positive=False, property_path=None):
    return dict(key=key, label=label, unit=unit, minimum=minimum, maximum=maximum,
                positive=positive, property_path=property_path)


METHODS = {
    'sales_comparison': {'label': 'Sales comparison', 'implemented': True,
        'description': 'Unadjusted indication from at least three reviewed, dated, nearby achieved transactions of the same property type.',
        'fields': [field('area_sqm', 'Subject comparison area', 'sqm', positive=True)]},
    'income_capitalization': {'label': 'Income capitalization', 'implemented': True,
        'description': 'Build NOI from annual income, vacancy and expenses, then capitalize at the explicit selected rate.',
        'fields': [field('annual_rent', 'Gross potential annual rent', 'SAR/year', property_path='financial.annual_rent_sar'),
            field('vacancy', 'Vacancy / credit loss', 'ratio', maximum=1),
            field('other_income', 'Other annual income', 'SAR/year'),
            field('operating_expenses', 'Annual operating expenses', 'SAR/year', property_path='financial.operating_expenses_sar_year'),
            field('cap_rate', 'Capitalization rate', 'ratio', maximum=1, positive=True)]},
    'dcf': {'label': 'Discounted cash flow', 'implemented': True,
        'description': 'Annual unlevered property DCF with end-of-year cash flows and exit capitalization. Debt, tenant-level leasing and taxes are not yet modeled.',
        'fields': [field('annual_rent', 'Year-one gross potential rent', 'SAR/year', property_path='financial.annual_rent_sar'),
            field('vacancy', 'Vacancy / credit loss', 'ratio', maximum=1), field('other_income', 'Other annual income', 'SAR/year'),
            field('operating_expenses', 'Year-one operating expenses', 'SAR/year', property_path='financial.operating_expenses_sar_year'),
            field('rent_growth', 'Annual rent growth', 'ratio', minimum=-0.99, maximum=1),
            field('expense_growth', 'Annual expense inflation', 'ratio', minimum=-0.99, maximum=1),
            field('annual_capex', 'Annual capital expenditure', 'SAR/year'),
            field('holding_years', 'Holding period (whole years)', 'years', minimum=1, maximum=30),
            field('discount_rate', 'Discount rate', 'ratio', maximum=1, positive=True),
            field('exit_cap_rate', 'Exit capitalization rate', 'ratio', maximum=1, positive=True),
            field('selling_cost', 'Exit selling costs', 'ratio', maximum=1)]},
    'cost': {'label': 'Cost approach / DRC', 'implemented': True,
        'description': 'Land plus replacement cost less explicit physical, functional and external deductions. Requires sourced land and cost inputs.',
        'fields': [field('land_value', 'Land value', 'SAR'),
            field('building_area', 'Building area', 'sqm', positive=True, property_path='building.built_up_area_sqm'),
            field('construction_cost', 'Replacement construction cost', 'SAR/sqm', positive=True),
            field('soft_cost_ratio', 'Soft costs / hard costs', 'ratio', maximum=1),
            field('physical_depreciation', 'Physical depreciation', 'ratio', maximum=1),
            field('functional_obsolescence', 'Functional obsolescence', 'ratio', maximum=1),
            field('economic_obsolescence', 'Economic obsolescence', 'ratio', maximum=1)]},
    'residual_land': {'label': 'Residual land valuation', 'implemented': True,
        'description': 'Maximum residual land budget after development costs and required developer profit. Static appraisal; timing and leveraged IRR are not included.',
        'fields': [field('gdv', 'Gross development value', 'SAR', positive=True),
            field('construction_cost_total', 'Construction / infrastructure', 'SAR'),
            field('professional_fees', 'Professional fees / permits', 'SAR'),
            field('financing_cost', 'Financing costs', 'SAR'), field('selling_cost_total', 'Sales / leasing costs', 'SAR'),
            field('contingency', 'Contingency', 'SAR'), field('developer_profit', 'Required developer profit', 'SAR')]},
}
for key, label in [('investment_method', 'Term & reversion / investment method'), ('profits', 'Profits method'),
                   ('ground_rent', 'Ground rent / leasehold interests'), ('avm', 'AVM / hedonic pricing')]:
    METHODS[key] = {'label': label, 'implemented': False, 'description': 'Not yet connected to the map workflow.', 'fields': []}

PROPERTY_TYPES = ['land', 'apartment', 'villa', 'residential_building', 'office', 'retail', 'warehouse',
                  'logistics', 'industrial', 'hotel', 'mixed_use', 'special_purpose']


def catalog():
    return [{'key': key, **value} for key, value in METHODS.items()]
