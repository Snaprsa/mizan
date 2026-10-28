# Repository map and reading order

## Canonical application

`Projects/Muqayyim-Downloads/` is the application to extend. The folder name is historical.

| Concern | Files to inspect first |
|---|---|
| Map page, filters, subject/type/method flow, coverage | `frontend/src/app/map/page.tsx` |
| Existing renderer/marker groups/subject radius | `frontend/src/components/intelligence-map.tsx` |
| Coordinate helpers and Google outbound links | `frontend/src/lib/map-utils.ts` |
| Valuation inspector/automatic save+calculate | `frontend/src/components/valuation-workflow.tsx` |
| Saved-result input/evidence freshness | `frontend/src/lib/valuation-state.ts`, `frontend/tests/valuation-state.test.mjs` |
| API client and shared frontend types | `frontend/src/lib/api.ts`, `frontend/src/lib/types.ts` |
| Layout/navigation/styles | `frontend/src/app/layout.tsx`, `frontend/src/app/globals.css` |
| Preserved dashboard/case workflow | `frontend/src/app/dashboard/page.tsx`, `frontend/src/app/cases/[id]/page.tsx` |
| Property editor | `frontend/src/app/properties/[id]/page.tsx`, `frontend/src/components/property-editor.tsx` |
| Sources/observation UI | `frontend/src/app/data/page.tsx` |
| API registration/settings/session | `api/app/main.py`, `api/app/config.py`, `api/app/database.py` |
| Legacy and new database models | `api/app/models/__init__.py`, `api/app/models/foundation.py` |
| Property/market/analysis validation | `api/app/schemas/foundation.py`, `api/app/schemas/analysis.py` |
| Map projection and coverage | `api/app/routers/map.py` |
| Method-specific required inputs | `api/app/services/valuation_catalog.py` |
| Provenance-aware preparation and comparable eligibility | `api/app/services/analysis_workflow.py` |
| Method calculations and preserved-engine adapter | `api/app/services/valuation_calculations.py`, `api/app/services/legacy_valuation.py` |
| Persisting inputs and immutable calculation runs | `api/app/routers/analysis.py`, `api/app/services/foundation.py` |
| Provider-neutral observations | `api/app/routers/market.py`, `api/app/services/market_adapters.py` |
| Citations/extraction/review | `extractors/`, `schemas/`, `api/app/services/extraction_service.py`, existing routers |
| Additive database migrations | `api/alembic/versions/` |
| Regression and API tests | `api/tests/` |
| Startup and local database preparation | `start_api.sh`, `scripts/prepare_mizan_database.py` |
| Frontend dependency lock | `frontend/package-lock.json` |

## Preserved work

| Folder | Role |
|---|---|
| `Projects/Mizan-Antigravity` | Preserved Flask/ML application, extended property schemas and valuation classes. The active app currently depends on its income/cost approach files. |
| `Projects/Mizan-Desktop` | Preserved original Flask app, Ridge/HGB/anchor-band models, ROI/risk prototypes, sample CSVs and Saudi indicator datasets. Not the main UI. |
| `Projects/Qaim` | Earlier comparable-ingestion prototype. Preserve/reference only; do not silently merge its database or treat its partially broken reporting as the canonical implementation. |
| `Projects/Muqayyim-OpenClaw` | Discovery/runbook/research/monitoring material; not the active application. |
| `Backups` | Historical OpenClaw reference snapshots. |
| `Related-Materials-To-Review` | Candidate blueprint/variable-library files; project membership/source quality requires review. |
| `Saved-Pages`, `Screenshots` | Historical UI references; saved HTML may require absent external assets. |
| `docs` | Dated architecture, implementation and recheck notes, test scripts and screenshots. Older statements describe older stages. |

## Local-only provenance and references

Outside public Git, `ORIGINAL-LOCATIONS.tsv`, `move-history.json` and `collection-manifest.json` preserve the earlier file consolidation history. They include many dependency paths and are large when expanded. Keep them for audit; use the current manifest/file map for normal code navigation.

The local private handoff ZIP has its own package manifests. Public source is the Git tree; see `docs/PUBLICATION.md` for the public component lineage and exclusion policy. Legacy data/model/reference folders listed above may intentionally be absent from a public checkout.

## Avoid confusing entry points

Use root `run_mizan.sh` or the active app's `start_api.sh` plus its Next.js frontend. Do not use the old standalone `server.js`/`muqayyim_app.html` prototype as the primary app; it has different storage and demo seeding. Do not launch multiple Flask/Next apps and assume their data is synchronized.
