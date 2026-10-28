# Mizan platform scope and priorities

This records the owner's product requirements for transfer. It is a specification, not a claim that the features below exist. See `CURRENT_STATE.md` for implemented behavior and `UPGRADE_PROMPT.md` for the immediate satellite-map/UI task. Do not attempt all future modules in one unstable change.

## Purpose and workflow

Mizan is Saudi real-estate valuation, underwriting and investment intelligence. Answer: what is this asset worth now; what should I pay; what could alternative uses produce; what return can acquisition/development generate; and what risks affect that investment?

The intended complete workflow is property/land → location/property facts → market evidence → comparable analysis → independent valuation methods → reconciliation → highest and best use → development feasibility → financing → returns → scenarios/sensitivity → risks → investment recommendation → professional report.

The immediate user experience starts on the map. Existing evidence is already visible before choosing a subject. Select location, property type and valuation approach; automatically populate supported information and show the missing inputs required by that method. Allow progressive enrichment from coordinates, address, plot number, URL or manual details. Automation must never conceal absent data or invent market facts.

## Central property workspace

Each property has a permanent workspace, with overview, location, market, comparables, valuation, HBU, development, financing, returns, scenarios, risk, documents and report. Persist assumptions and outputs.

Property data should support:

- Identity: stable ID, user name, address, city/district/municipality, coordinates, parcel/plot, block and plan.
- Land: area, dimensions, frontage, street width/frontages, corner status, shape, topography, orientation and utilities.
- Planning: classification, permitted use, FAR, coverage, height, setbacks, parking and restrictions, each with a real source.
- Building: built-up area, GFA, GLA/NLA, floors, units, year/age, condition, occupancy and use.
- Financial: asking/purchase price, current rent and unit rent, expenses and NOI.
- Metadata: source, collection date, confidence/uncertainty and last update.

## Market data and comparables

Use provider-neutral adapters, not a single hardcoded feed. Potential sources include Saudi Ministry of Justice, REGA, Open Data, Balady, Sakani, Ejar, municipalities, listing portals, brokers, user/internal transactions, rental/construction cost databases, SAMA, GASTAT, REIT disclosures and public-company reports. These are intended sources, not existing access rights or connected feeds.

Every observation retains source, date, geography/precision, property type, reliability, raw value, normalized value/unit and metadata. Preserve ingestion batches, duplicate/conflict decisions and source provenance. Review licensing and data grain before importing legacy files.

Comparables need manual and automatic selection by distance/district/date/type/use, land/building area, street/frontage/corner, age, quality, occupancy and relevant attributes. Show location/distance, date, achieved sale versus listing, sale SAR and SAR/m², rent SAR/year and SAR/m²/year, attributes, source and confidence.

Adjustments should support absolute SAR, SAR/m² and percentage for time, location, size, frontage, street, corner, shape, condition, age, quality, occupancy, zoning and potential. Make adjustment order and basis explicit. Compute raw/adjusted evidence, mean/median, weighted mean/median, distributions, defensible intervals and outliers, with manual overrides and an audit trail. Do not treat three listings as three completed transactions.

## Independent valuation methods

All methods feed a reconciliation rather than an unqualified average:

1. **Sales comparison:** adjusted unit prices, weights, implied value and low/base/high.
2. **Income capitalization:** potential rent minus vacancy/credit loss plus other income gives effective income; less expenses gives NOI; value = NOI / cap rate. Market/user/exit yields and sensitivity.
3. **DCF:** 1–30 years, escalation/occupancy/expense inflation, capex, tenant improvements, leasing commissions, applicable taxes, debt and exit. Annual NOI, unlevered/levered flows, PV and terminal value using exit cap or appropriate perpetual growth. NPV, project/equity IRR, multiples and cash yield.
4. **Cost:** land plus replacement/reproduction cost less physical, functional and external depreciation; age-life and condition alternatives.
5. **Residual land:** GDV less development, professional, financing, sales/leasing, contingency and required developer profit. Maximum land price and SAR/m² with sensitivity; a high-priority eventual tool.
6. **Development appraisal:** acquisition, construction/infrastructure, soft costs, permits, marketing, finance, contingency, duration and absorption. GDV, total cost, profit on cost/GDV, development/equity IRR and residual.
7. **Investment method:** current/market rent, lease expiry, term/reversion, yields; rack-, over- and under-rented interests, hardcore/layer where applicable.
8. **Profits method:** maintainable operating profit and attributable property portion; extensible hotel/resort/healthcare/entertainment models.
9. **DRC:** land plus modern equivalent asset cost less physical, functional and economic obsolescence for specialized assets.
10. **Hedonic pricing:** feature-based statistical architecture using location, area, frontage/street/corner, age, type, amenities, density and time. Train only with adequate appropriate data.
11. **AVM:** extensible regression, RF/boosting/XGBoost, neural/spatial and ensemble adapters. Output value/unit value, range, explainable drivers and defensible confidence. Use an honestly labelled deterministic/statistical baseline when training data is insufficient.
12. **Mass appraisal:** common assumptions/models over multiple assets, preserving per-asset evidence and uncertainty.
13. **Comparable rent:** adjusted market rent, SAR/m²/year, range and supported growth assumptions.
14. **Ground rent/land lease:** PV of contractual/market rent streams for long leases/concessions.
15. **Separate interests:** extensible freehold, lessor, lessee, headlease and sublease valuation.
16. **Special assets:** extensible hotel, serviced apartment, mall, office, warehouse/logistics, industrial, data center, healthcare/education, mixed-use, compound, build-to-suit and masterplan modules.

Reconciliation assigns applicability, data quality, confidence and method weights, explains the weighting, and permits user overrides. Produce reconciled low/base/high, unit value and confidence. Confidence must not become false precision or an arbitrary score.

## Development, HBU, financing and returns

HBU alternatives pass four distinct tests: legally permissible, physically possible, financially feasible and maximally productive. Rank supported residential/apartment/villa/office/retail/hospitality/warehouse/logistics/industrial/mixed-use alternatives by residual, IRR, NPV, margin and risk. An unsourced zoning assumption cannot establish legal permission.

Development models combine land area/price/acquisition fees, FAR/coverage/efficiency, GFA/GLA/sellable area, construction/fit-out/infrastructure/external works/landscape, design/engineering/PM/QS/legal/permits/marketing, schedule, sale/rent, occupancy, absorption and escalation. Calculate cost, GDV, profit, ROI, IRR/equity IRR and NPV with explicit timing.

Financing supports no debt and senior debt first, then mezzanine/multiple layers. Inputs: LTC/LTV, interest, fees, term, amortization, grace and construction draws. Outputs: construction interest, balances, service, DSCR, debt yield, equity requirement and levered flows/IRR.

Return metrics, where applicable: ROI, project/equity IRR, NPV, equity multiple/MOIC, cash-on-cash, yield on cost, cap rate, development margin, profit on cost/GDV, payback, DSCR and debt yield. Treat undefined/no-solution/multiple-IRR cases honestly.

Maximum bid price solves what acquisition price satisfies a required IRR, equity IRR, NPV, margin or yield on cost. Do not approximate every target using an unrelated static formula.

Scenarios: downside/base/upside, independently variable land/sale/rent/construction/interest/time/occupancy/cap/exit/absorption inputs. Sensitivities: two-variable grids for meaningful model outputs and tornado charts. Risks: market/pricing/rent/construction/finance/liquidity/regulatory/planning/demand/tenant/execution/exit/location, each with probability, impact, score, mitigation and related assumptions.

Investment decisions combine property, market value, asking/acquisition price, discount/premium, HBU/residual, returns and risks. Strong Buy/Buy/Attractive/Fairly Priced/Marginal/Unattractive/Avoid thresholds must be configurable and explained, not arbitrary labels.

## GIS, dashboards, portfolios and reports

Map layers should cover subject, sales/rent evidence, actual-data price/density summaries, transactions, sourced districts/parcels/planning, amenities/roads and projects. Immediate imagery and spatial UX requirements are in the upgrade prompt. Always distinguish exact location from area-level or missing-location data.

Suggested eventual navigation: Dashboard, Properties, Valuation, Comparables, Development, Investments, Market, Map, Reports, Portfolio, Data and Settings. Do not add empty screens merely to complete this list.

Portfolio metrics: value/cost/gain/NOI/yield, geographic/type/risk exposure and supported return aggregation. Do not mechanically average IRRs when portfolio cash flows are required.

Professional reports: executive summary, asset/location/market, comparable evidence, assumptions, approaches/reconciliation, HBU/development, financing/returns/sensitivity, risks, conclusion, sources and disclaimer. PDF export is an eventual requirement, beyond preserved legacy case exports.

## Shared architecture requirements

Every assumption has name, value, unit, category, source/date, override and notes. Status: observed, market-derived, system estimate, user input or model-derived. Significant displayed numbers expose provenance and update date. Confidence considers comparable quantity/recency/proximity/similarity, completeness, source quality, method agreement and uncertainty, with coarse labels and justified 0–100 values only when defensible.

Separate reusable financial calculations from UI. Keep valuation, investment, development and risk calculation modules independent of rendering; do not duplicate formulas in components. Persist input/assumption snapshots, data date, calculation/model versions and outputs so prior valuations remain reproducible when inputs change.

Extend the current schema with additive migrations and real foreign keys/history. Intended entities: users/organizations; properties/parcels; transactions/listings/sale and rental evidence; valuations/methods/assumptions/results; developments/assumptions/cashflows; financing; scenarios/sensitivity; risks; market data/sources; reports; portfolios/membership. Reuse existing equivalent tables rather than creating duplicate competing entities. Enforce owner/organization access consistently before shared deployment.

Future roles: investor, developer, valuer, broker, analyst, fund manager, institutional client and admin. Use SAR, Saudi administrative geography/planning/valuation terminology and financing context; English/Arabic/RTL architecture with future GCC expansion. Do not imply regulatory approval or professional certification.

Institutional UX: restrained existing accent, readable dense tables, financial models, maps, charts, expandable assumptions and clear attribution. Avoid excessive gradients, oversized cards, unnecessary animations and AI branding. Preserve functioning screens unless the requested improvement justifies changing them.

## Incremental sequence

1. Foundation: inspect/reuse; property/schema, assumptions, market-source architecture and existing integration. Initial foundation already exists; assess gaps before replacing it.
2. Valuation: professional comparables, sales/income/DCF/cost, reconciliation and confidence. Five initial methods exist; full scope remains incomplete.
3. Development: residual, timed appraisal, HBU and maximum bid.
4. Investment: financing, returns, scenarios and sensitivity.
5. Intelligence: risk, honest AVM/hedonic architecture, analytics and GIS.
6. Professional output: portfolio, reports/PDF, collaboration and institutional features.

The owner's latest request prioritizes the rich satellite map and professional interface across this roadmap. Implement that scoped upgrade first; keep future modules extensible and explicitly unavailable until functional.
