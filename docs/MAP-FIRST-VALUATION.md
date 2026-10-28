# Map-first valuation workspace — 25 October 2026

Mizan now starts at the map. The existing case dashboard remains at `/dashboard`.

## User workflow

1. Inspect saved properties, comparables and market observations on the same map. All evidence layers are enabled initially. The coverage overlay identifies exact locations, missing/area-only locations and unverified dataset files.
2. Click a subject location, choose property type and valuation approach, then start. The app creates a permanent property and links a case automatically. Existing properties can be selected as the subject instead.
3. The adjacent valuation panel shows only the chosen approach's required inputs. Saved method assumptions, compatible central assumptions, appropriate property fields and exact metric/unit/geography/type matching market observations can fill inputs automatically. Matching observations must be dated no later than the valuation date, within the last year, and have a supplied reliability of at least 60/100; these are configurable implementation selection criteria, not calibrated confidence.
4. Missing values remain explicit. Typing one marks it as a user assumption at the selected valuation date. Changing a sourced numeric value identifies it as a user override. Sources/dates remain editable. No vacancy, cap rate, growth, cost or profit defaults are silently supplied.
5. Automatic calculation is enabled when all required inputs are present. Inputs and sources are saved first. A calculation only runs when method-specific evidence/readiness tests also pass. Manual save/calculation controls remain available. Changing assumptions recalculates; reopening the same saved analysis does not create duplicate runs.
6. Previous calculations retain their property revision, inputs, assumptions, data date, selected comparable snapshots, calculation version, preserved engine hash and outputs.

## Connected methods and honest scope

- **Sales comparison:** automatic geographic/date/type/status/currency/price filtering. At least three distinct active achieved transactions are required. Repeated equivalent evidence from the same source does not inflate the sample. Listings and draft/undated evidence remain context, not achieved sales. Output is an unadjusted median unit-price indication, not a fully adjusted professional appraisal or calibrated confidence interval.
- **Income capitalization:** potential annual rent less vacancy, plus other income, less operating expenses; capitalize NOI at the explicit rate. Reuses the existing Mizan IncomeApproach.
- **DCF:** unlevered annual cash flows, revenue and expense growth, constant vacancy, annual capex, 1–30 whole-year holding period, next-year NOI exit capitalization and disposal costs. Reuses existing Mizan DCF valuation. No debt, tenant-by-tenant lease model, varying occupancy schedule or taxes yet.
- **Cost / DRC:** land plus replacement cost, explicit soft costs and physical/functional/economic deductions. Reuses existing Mizan CostApproach with explicit zero handling. Combined depreciation over 100% blocks the run.
- **Residual land:** static GDV less explicit development/financing/selling/contingency/profit deductions. No development timing or leveraged IRR yet.

Legacy hardcoded confidence scores and fixed heuristic ranges are not exposed as calibrated results. Confidence remains null until a defensible confidence model is connected. Negative economic indications remain visible with explanatory limitations.

Other approach choices are explicitly disabled as not yet implemented. External provider feeds, automatic geocoding, planning retrieval, lease abstraction and cost databases are not connected; the app cannot supply absent evidence merely from a map point.

## Map data coverage

Registered market observations join the property/comparable map projection. Exact observation pins require metadata `location_precision` equal to `exact` or `property`, with valid `latitude` and `longitude`. All other observations stay in the adjacent list with city/district/source/value/unit. Area-level records are not plotted at fabricated district centroids. Local CSV/XLSX candidate files are listed in coverage with unverified/not imported status; their rows are not asserted to be normalized market transactions.

Counts describe saved evidence records, not complete Saudi market coverage or necessarily distinct transactions. Existing extraction/data-quality issues remain visible. No test observations or financial inputs were seeded into the actual runtime database.

## Reuse and storage

Existing Next.js screens/styles, map component, effective comparable-field override projection, Property/Case/PropertyAssumption/PropertyRevision models, source registry, provenance and audit services remain in use. The existing `valuation_runs` table now stores complete calculation snapshots in its data column; no destructive schema migration is required. New optional `PropertyInput.analysis` metadata stores the selected method/search scope/date.

`api/app/services/legacy_valuation.py` loads preserved income/cost classes from the sibling Mizan-Antigravity project without starting its Flask/ML application. The only legacy edit removes an unused numpy import. Keep that project in the consolidated workspace when running this adapter.

## Verification

- 70 API tests pass, including seven new workflow/calculation tests.
- Tests cover automatic property/case creation, per-method requirements, input provenance filling, partial/invalid input gating, historical snapshots, stale revisions, owner scope, exact versus area-only observation coverage, source deduplication, income/DCF/cost/residual math and lack of invented confidence.
- 17 preserved Mizan-Antigravity tests pass after the unused import removal.
- Next.js production build passes TypeScript/ESLint checks.
- `docs/verify_map_workflow_ui.py` routes browser API calls exclusively to a disposable database on port 8100 and stubs map tiles. It verifies map entry, location/type/method selection, approach-specific fields, automatic calculation and recalculation, persistent reopening without duplicate runs, method switching and run history. Actual runtime data is not modified.
