# Mizan Monitor: implementation report

31 October 2026. Monitor answers: what is the portfolio worth now, what changed, why, how sure are we, and what needs attention.

## A. What was found and reused

| Existing system | How Monitor uses it |
|---|---|
| `prepare()` and `calculate()` | Every value comes from these, with the same readiness gates as a saved run. No formulas were copied |
| Sales, income, DCF, cost and residual methods | Whichever an asset has complete reviewed inputs for. None is forced |
| `PropertyAssumption` (`user_override`, source, date, status) | Overrides use it, so the reviewed value is kept |
| Property revisions, `log_action`, owner and role checks | Reused for overrides and all actions |
| Comparable grid and demo labelling | Reused for evidence and for the `uses_demo` warning |
| Design primitives in `sheet-ui.tsx` | Reused; the look is unchanged |

There was no reconciliation between methods, no portfolio concept and no value history apart from saved runs. Those are new.

## B. What was built

| Area | Behaviour |
|---|---|
| Portfolios | Create, add existing properties, ownership share, debt, cost, book value, NOI, occupancy, WAULT |
| Dashboard | Value, change against official, assets needing attention, rising/stable/falling, value history, NAV, LTV, NOI, cap rate, occupancy, unrealised gain, sector and geography |
| Indicative value | Latest value, range, confidence, last material update, official valuation, next formal date |
| Event-driven revaluation | A new snapshot only when inputs, eligible evidence, weights or the calculation version change. A quiet check adds nothing |
| Attribution | Reruns the valuation for each driver, since the last update and since the official valuation. Parts sum to the change |
| Asset page | Value, alerts, why it changed, history with official line and range, methods, comparables, assumptions, confidence checks, freshness, holding, audit trail |
| Alerts | Info, watch, warning, critical. One per condition, closes itself when the condition clears, an accepted alert returns only if it gets worse. Thresholds editable per portfolio |
| Surveillance | Filters and sorting, table and bubble chart, CSV |
| History | 1M to 3Y and All, at portfolio and asset level |
| Snapshots | Immutable. Keep inputs, sources, evidence, weights, values, grade, attribution, versions and timestamp |
| Confidence | High, medium or low from listed checks |
| Revaluation priority | Points with the reason for each |
| Method disagreement | Flagged with what to investigate; the value stays the median or your weights, not a blind average |
| Stress tests | Cap rate, rent, occupancy and discount rate, through the engine, showing value, LTV and affected assets |
| Human overrides | Reason required; who, when, before and after are all kept; removable |
| Journey actions | Accept, investigate, adjust assumption, recommend formal valuation, record official valuation, record event, report |
| Report | Printable portfolio report: what changed, why, which assets, confidence, recommended action |
| Demo fund | Opt-in, 72 fictional assets over two years, removable in one click |

## C. Architecture

Monitor and Value share properties, assumptions, evidence, calculations and users. `monitor_calc.py` is pure and deterministic, `monitor.py` orchestrates, and the router and pages present. A future agent could gather or classify evidence, but no financial calculation depends on an LLM.

## D. Database changes

Additive migration `20261031_mizan_monitor`.

| Table | Purpose |
|---|---|
| `portfolios` | Portfolio details and alert thresholds |
| `portfolio_assets` | Property in a portfolio: holding facts, frequencies, weights, cached summary, priority |
| `valuation_snapshots` | Immutable official and indicative valuations; belongs to the property |
| `monitor_events` | Detected or user-recorded events |
| `monitor_alerts` | Alert state |
| `properties.is_demo` | Keeps demo properties off the map and out of Properties |

## E. Monitoring logic

1. A check runs each method through the shared pipeline and fingerprints what the value depends on.
2. If the fingerprint is unchanged, nothing is recorded.
3. If it changed, Mizan reconciles (your weights if they cover every method, otherwise the median), grades the evidence, attributes the change, and saves a snapshot with an event per change.
4. Ages, LTV, priority and alerts are then recomputed for the portfolio.

Monitoring frequency decides how often assets are checked. Formal frequency is recorded separately and is not automated.

## F. Pages

| Page | Purpose |
|---|---|
| `/monitor` | Portfolios, new portfolio, demo fund |
| `/monitor/[id]` | Overview, Assets, Alerts, Revalue first, Stress, Settings |
| `/monitor/assets/[assetId]` | One asset, drilling down from answer to audit |
| `/monitor/[id]/report` | Printable report |

## G. Assumptions and approximations

- **Median reconciliation:** used when no weights are set, because any default weights would be invented.
- **Thresholds, grade rules and priority points:** my software defaults, not market benchmarks or calibrated figures. They should be reviewed by a valuer.
- **Range:** the spread of methods and sales, not a confidence interval. A single method shows no range.
- **Confidence has no percentage:** nothing has been calibrated against achieved prices, so a percentage would be invented.
- **Portfolio totals:** at ownership share, with debt scaled the same way and held constant under stress.
- **Official comparison:** only assets with both values count towards the headline change.
- **The gap between Mizan and official at the official date:** shown separately, because official valuations hold no model inputs to attribute.
- **Demo fund:** inputs, sales and official valuations are made up. Its values are calculated, not scripted.

## H. Not built, and what needs outside access

| Item | Status |
|---|---|
| Live Saudi transactions, listings, rents, cap rates, zoning, construction indices | No feeds connected. Monitor sees only what is saved in Mizan |
| Background monitoring | Checks run on opening a portfolio or on Check now, not while the app is closed |
| Rental evidence and lease-level data | No record type yet, so tenant and lease-expiry concentration and rental-opportunity alerts are not built |
| Interest-rate stress and covenants | Debt terms are not stored. Discount-rate stress is shown instead, labelled as such |
| Market intelligence panel, map and geographic heatmap views | Not built. Sector and geography breakdowns and the bubble chart are |
| Watchlist | Not built (the brief marks it secondary) |
| Organisation controls | Owner-scoped only; no shared organisation access |
| CSV bulk import | Not built; assets are added from existing properties |
| Official NAV input | Stored by the API, no screen for it yet |
| TAQEEM, IVS, IFRS | No compliance is claimed |
| AI agents | Not built; the design leaves room for them |

## I. Testing

| Check | Result |
|---|---|
| Backend tests | 132 passed, 16 of them new |
| Frontend tests | 24 passed, 6 new |
| Type-check, lint, production build | Passed |
| Migration rehearsal on a copy of the local database | Record counts unchanged, integrity ok |
| Browser, on a disposable API and made-up data | Full journey from dashboard to override and audit trail; stress, priority, report, chart, new portfolio, add property, phone width |
| 10,000 synthetic assets, 80,000 snapshots | Dashboard 0.63 s, asset list 0.32 s |

Not tested: printing to paper, a portfolio of real assets with real official valuations, and a full check across 10,000 assets, which reruns the engine per asset and is likely to need a background job at that size.

## J. Next priorities

1. CSV import of assets, holdings and official valuations, so a real portfolio can be loaded quickly.
2. Rental evidence as its own record type, which also unlocks rent and lease alerts.
3. Scheduled background checks.
4. Debt terms, for interest-rate stress and covenant tests.
5. Valuer review of the thresholds, grade rules and priority points.
6. Organisation access and roles, before anyone else uses it.
