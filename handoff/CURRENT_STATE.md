# Current state — Mizan

Public-source preparation inspected 28 October 2026. Newer sensitivity, ownership and experimental HBU work is preserved alongside the earlier map workflow. The public checkout is source-only; historical delivery notes are dated context.

## Product and entry point

Saudi real-estate valuation, underwriting and investment intelligence. Primary workflow: map → subject location → property type → approach → sourced inputs → calculation → saved results. A map-first workspace with a Google Maps JavaScript API imagery provider was implemented on 28 October 2026. Live satellite imagery has **not** been verified: no Google key is configured on this machine, so the app currently runs the labelled OpenStreetMap road-map fallback. See `handoff/CONTINUATION_LOG.md`.

The active application is `Projects/Muqayyim-Downloads`. Keep this relative path and the sibling Mizan-Antigravity engine until intentionally refactoring and testing them. Other preserved projects are not additional primary apps to launch.

## What exists

| Area | Current implementation |
|---|---|
| Frontend | Next.js 14.2 / React 18 / TypeScript, Tailwind, Lucide; root redirects to `/map`; dashboard at `/dashboard` |
| Backend | FastAPI, Pydantic, async SQLAlchemy, Alembic; REST under `/api/v1`; health at `/api/health` |
| Local database | SQLite runtime `Projects/Muqayyim-Downloads/storage/mizan.db`; legacy database cloned/recovered for local startup if present; backups before startup migration |
| Deployment direction | PostgreSQL-oriented schema/migrations; PostGIS and institutional operations not yet implemented/verified |
| Map | Full-bleed workspace: slim header with coordinate/saved-record/Google-geocoding search, collapsible layers & filters (type, date, status, source, location precision, reliability), central map with tools, resizable inspector (Evidence / Subject / Valuation / Coverage) and optional linked table. Provider boundary: Google Maps JS API (satellite/hybrid/road/terrain, Geocoder, Street View with provider-reported capture dates, rotate/tilt only on vector maps) when `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` is set; otherwise, or on Google auth failure, a labelled Leaflet/OSM road-map fallback. Subject pin place/drag/arrow-key nudge/confirm, polygon and radius search areas (editable), approximate site outline saved to the property as GeoJSON with `cadastral: false`, geodesic distance/area measurement, fit subject/evidence, north reset, fullscreen. State (camera, basemap, subject, geometry, selection, layers, filters, panels) persists in localStorage. `/map/records` accepts viewport bounds and returns precision labels; the UI switches to bounded viewport queries only when results are truncated. |
| Properties | Identity/geography plus validated land/planning/building/financial/provenance sections; owner scope; case link; optimistic revision checks |
| Assumptions | Explicit value/unit/category/source/date/status/override; stored history and immutable property input snapshots |
| Market data | Provider-neutral source registry, append-only normalized observations, JSON/CSV import with duplicate/conflict checks; unverified local dataset inventory |
| Comparable workflow | URL/PDF ingestion, Arabic normalization, extracted field citations, reviewed overrides, status changes, CSV/XLSX/PDF exports |
| Valuation | Sales comparison with a reviewed adjustment grid (28 Oct 2026): per-comparable adjustments for 16 factors in %, SAR/m² or SAR lump sum, each with rationale/source and proposed/approved status; sourced compound time rule; transactional adjustments compound in order, property adjustments additive; equal / inverse-gross / manual (rationale) weights; mean, median, weighted mean/median, IQR, CV; outlier and heavy-adjustment flags; reviewed exclusions; IQR low/base/high (not a confidence interval). Default grid reproduces the former unadjusted median. Also direct income cap, annual unlevered DCF, cost/DRC, static residual land; automatic sourced preparation/readiness; input/result histories |
| Sensitivities | Two-way model sensitivities for income, annual DCF, cost and residual; invalid stresses remain unavailable |
| HBU utility | Experimental sourced-gate / timed-cash-flow screening service with unit tests; not an integrated HBU workspace |
| Reuse | Income/DCF/cost classes loaded from `Projects/Mizan-Antigravity/src/mizan_engine/approaches` through an adapter |
| Auth | Local development identity; JWT/persisted-user checks and ownership across property and legacy case/evidence routes, with read-only-role mutation guards. Production authentication and institutional tenancy remain incomplete |
| Design | Blue/slate palette, dense tables, functional but basic map screen; no completed professional redesign |

## Real limitations

Satellite imagery is implemented but unverified pending a Google key. There is no parcel/cadastral service, authorized planning lookup, complete GIS, calibrated AVM, connected public transaction feed, full debt/HBU/development workflow, institutional portfolio/reporting/collaboration or complete bilingual translation.

The five connected methods are initial indications, not the complete original platform specification. Sales still requires at least three distinct, active, dated, nearby achieved transactions of the same property type (and three after exclusions); adjustments are reviewer judgements, not market-derived, unless their recorded source says so. Comparables carry few structured attributes (area, date, location, tenure), so attribute-driven automatic adjustment proposals are not implemented. Rental comparables are not implemented. DCF is annual and unlevered. Residual land is static. Legacy heuristic confidence/ranges are not exposed as calibrated confidence.

The public checkout contains no private runtime records, raw Saudi indicator workbooks, training CSVs, model binaries or uploaded evidence. Fresh migrations create an empty database. The local dataset inventory can be empty; no fictional records are added to populate the map.

The owner's local collection retains candidate datasets and original-location history. Their grain, quality, freshness and redistribution rights have not been established for public release. Aggregated indicators must not be treated as individual transactions.

## Protections to preserve

- No fabricated geographic points, market facts, observations or confidence scores.
- Geographic matching does not borrow a different district when the subject's district is unknown.
- Saved-result freshness compares input/evidence snapshots and calculation version, not just the property's revision.
- Refresh fills untouched blanks and preserves unsaved edits.
- Reopening unchanged analysis does not create duplicate runs.
- Listings are not counted/used as achieved sales.
- Test data belongs only in isolated fixtures/databases.

## Verification

Map upgrade, 28 October 2026: 97 backend tests, 15 frontend tests (including coordinate-order, geodesic, clustering with a 10,000-point synthetic fixture and persisted-state validation), lint, type-check and production build passed locally. Browser checks used synthetic fixtures in a disposable API on 8100 and the OSM fallback; an intentionally invalid Google key confirmed the auth-failure fallback. Not verified: real Google satellite/hybrid/terrain tiles, geocoding, Street View, vector rotation/tilt.


The public-source preparation run passed 93 backend tests on 28 October, including the portable migration fixture, sensitivity, ownership and experimental HBU utility tests. The prior full recheck passed 7 frontend tests and a production build; publication checks rerun the relevant commands on an export of committed source. CI results are the current reference for a clean Linux installation.

These checks do not verify live satellite imagery, provider feeds, professional standards compliance or a production deployment.

## Active API groups

- `/api/v1/properties`: create/search/detail/replace, case link, assumptions and revisions.
- `/api/v1/market`: sources, JSON/CSV observations, filtering and local-dataset inventory.
- `/api/v1/map/records`: owned property/comparable/observation projection, counts, source precision and coverage.
- `/api/v1/analysis`: method catalog, start, prepare, save inputs, calculate runs and saved history.
- Existing `/api/v1/cases`, sources, extraction jobs, comparables/overrides/status, export routes.

Use the running API's `/docs` or source routers for the exact contract; do not guess endpoints from a retired prototype.
