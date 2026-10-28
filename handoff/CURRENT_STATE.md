# Current state — Mizan

Public-source preparation inspected 28 October 2026. Newer sensitivity, ownership and experimental HBU work is preserved alongside the earlier map workflow. The public checkout is source-only; historical delivery notes are dated context.

## Product and entry point

Saudi real-estate valuation, underwriting and investment intelligence. Primary workflow: map → subject location → property type → approach → sourced inputs → calculation → saved results. The user now specifically requests real satellite/hybrid imagery and a substantially improved professional map-first interface. That upgrade is specified, not yet implemented.

The active application is `Projects/Muqayyim-Downloads`. Keep this relative path and the sibling Mizan-Antigravity engine until intentionally refactoring and testing them. Other preserved projects are not additional primary apps to launch.

## What exists

| Area | Current implementation |
|---|---|
| Frontend | Next.js 14.2 / React 18 / TypeScript, Tailwind, Lucide; root redirects to `/map`; dashboard at `/dashboard` |
| Backend | FastAPI, Pydantic, async SQLAlchemy, Alembic; REST under `/api/v1`; health at `/api/health` |
| Local database | SQLite runtime `Projects/Muqayyim-Downloads/storage/mizan.db`; legacy database cloned/recovered for local startup if present; backups before startup migration |
| Deployment direction | PostgreSQL-oriented schema/migrations; PostGIS and institutional operations not yet implemented/verified |
| Map | Leaflet/OpenStreetMap road tiles, grid clusters, subject pin/radius, layers, date/city/type/text filters, viewport counts and adjacent evidence list; Google Maps outbound links |
| Properties | Identity/geography plus validated land/planning/building/financial/provenance sections; owner scope; case link; optimistic revision checks |
| Assumptions | Explicit value/unit/category/source/date/status/override; stored history and immutable property input snapshots |
| Market data | Provider-neutral source registry, append-only normalized observations, JSON/CSV import with duplicate/conflict checks; unverified local dataset inventory |
| Comparable workflow | URL/PDF ingestion, Arabic normalization, extracted field citations, reviewed overrides, status changes, CSV/XLSX/PDF exports |
| Valuation | Initial sales baseline, direct income cap, annual unlevered DCF, cost/DRC, static residual land; automatic sourced preparation/readiness; input/result histories |
| Sensitivities | Two-way model sensitivities for income, annual DCF, cost and residual; invalid stresses remain unavailable |
| HBU utility | Experimental sourced-gate / timed-cash-flow screening service with unit tests; not an integrated HBU workspace |
| Reuse | Income/DCF/cost classes loaded from `Projects/Mizan-Antigravity/src/mizan_engine/approaches` through an adapter |
| Auth | Local development identity; JWT/persisted-user checks and ownership across property and legacy case/evidence routes, with read-only-role mutation guards. Production authentication and institutional tenancy remain incomplete |
| Design | Blue/slate palette, dense tables, functional but basic map screen; no completed professional redesign |

## Real limitations

There is no embedded satellite/hybrid imagery, Google SDK map, complete geocoding/parcel service, authorized planning lookup, complete GIS, calibrated AVM, connected public transaction feed, full debt/HBU/development workflow, institutional portfolio/reporting/collaboration or complete bilingual translation.

The five connected methods are initial indications, not the complete original platform specification. Sales uses an unadjusted median from at least three distinct, active, dated, nearby achieved transactions of the same property type. DCF is annual and unlevered. Residual land is static. Legacy heuristic confidence/ranges are not exposed as calibrated confidence.

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

The public-source preparation run passed 93 backend tests on 28 October, including the portable migration fixture, sensitivity, ownership and experimental HBU utility tests. The prior full recheck passed 7 frontend tests and a production build; publication checks rerun the relevant commands on an export of committed source. CI results are the current reference for a clean Linux installation.

These checks do not verify live satellite imagery, provider feeds, professional standards compliance or a production deployment.

## Active API groups

- `/api/v1/properties`: create/search/detail/replace, case link, assumptions and revisions.
- `/api/v1/market`: sources, JSON/CSV observations, filtering and local-dataset inventory.
- `/api/v1/map/records`: owned property/comparable/observation projection, counts, source precision and coverage.
- `/api/v1/analysis`: method catalog, start, prepare, save inputs, calculate runs and saved history.
- Existing `/api/v1/cases`, sources, extraction jobs, comparables/overrides/status, export routes.

Use the running API's `/docs` or source routers for the exact contract; do not guess endpoints from a retired prototype.
