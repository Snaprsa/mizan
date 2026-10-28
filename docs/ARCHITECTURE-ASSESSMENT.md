# Mizan architecture assessment — 25 October 2026

## 1. Existing application and data

This workspace is a collection of separate applications, not a single repository. No AGENTS.md or Git checkout was found in the collected projects. `pre-phase1-inventory.json` records the source, documentation and data inventory before implementation; generated dependency trees and credentials are excluded.

| Project | Existing functionality | Limits |
|---|---|---|
| Mizan-Desktop | Flask/Jinja/JS interface; CSV comparables; Ridge/HGB estimators; feature encoding/imputation; segment anchor bands; confidence; CLI training/prediction; comparable lookup; ROI/risk modules; tests | No persistent property database; ROI and market factors include hardcoded assumptions; trained model and sample CSV provenance need review |
| Mizan-Antigravity | Related Flask app; extended Pydantic schemas for land, planning, tenure, income, financing, development and risk; sales/income/DCF/cost approach classes and quality-weighted reconciliation | Engines are not integrated into a durable multiuser workflow; implicit rate defaults and validation gaps require work before reuse |
| Muqayyim-Downloads | Next.js 14/React 18/TypeScript/Tailwind/Lucide; FastAPI; SQLAlchemy async; SQLite local / PostgreSQL configured; case/source/comparable APIs; deterministic HTML/PDF extraction, optional LLM fallback; Arabic normalization; field citations; overrides; audit; CSV/XLSX/PDF exports | Subject, adjustment, valuation and market tables partly stubs; provider discovery stubs; extraction runs inline despite Celery scaffolding; development auth bypass, no complete login/RBAC/tenant isolation |
| Qaim | Earlier Next.js/FastAPI comparable-ingestion workflow, SQLite DB, provider interface, adjustment rules, exports | Overlapping predecessor; reporting/generators.py contains a syntax error; do not choose it as primary app |
| Muqayyim-OpenClaw / backups | Discovery reports, reuse notes, runbooks | Documentation, not another runnable platform |

Muqayyim's existing SQLite database contains 8 cases, 20 sources, 18 comparables, 38 extracted fields and one override. Qaim contains one case and one comparable. Inspection used disposable DB copies, including the Muqayyim journal; existing databases were not migrated or seeded during assessment. Preserve both and migrate explicitly later.

Existing APIs: cases create/list/detail; URL/PDF source creation/list/raw content; extraction start/status; comparable list, field override and status; CSV/XLSX/PDF export; health. Flask APIs include valuation/prediction, city/district lists and filtered comparable retrieval. The standalone Node/HTML local app is an alternative prototype that seeds demo data; it is not the canonical backend.

Search exists as case lists, comparable filtering and source ingestion, not a unified property search. No functioning map/GIS, district polygons or geospatial database integration was found. Coordinates are supported by extractors and comparable models. Dashboard counts actual cases/sources/comparables. Blue/slate dense tables and citation/review patterns are the reusable design system. Arabic exists in extraction, normalization and the legacy Flask UI; the Next.js app is English, without a full translation system.

Saudi data: Desktop contains Riyadh 2024 sales-indicator CSV/XLSX files and rental indicators for Riyadh, Eastern Province and Najran; Antigravity has additional CSV training datasets. These are preserved. File names and old notes suggest official sources, but row-level provenance, licensing, grain, freshness and synthetic status have NOT been established. Aggregate indicators must not be treated as individual transactions or training evidence. Blueprint/variable-library files remain candidates for review. No live market feed is configured.

## 2. Reuse and gaps

Retain the Muqayyim app as the platform foundation and preserve its endpoints/screens. Reuse its SQLAlchemy UUID type, session lifecycle, organization/user/case/source/comparable models, audit pattern, extraction/normalization and exports. Keep both Mizan engines intact. Later wrap their loaders/features/estimators/approaches through adapters with explicit assumptions, model/data versions and validated evidence. Do not import old ROI constants or model artifacts into live market views without provenance review.

Missing: permanent properties/parcels, versioned assumptions, normalized market observations, reproducible analysis snapshots, integrated method reconciliation, HBU/residual/development/financing, robust IRR/max bid/sensitivity, portfolio, GIS, complete roles/tenancy/collaboration and professional integrated reports. An export of comparables is not yet a valuation report. Phase 1 adds only working foundation workflows; it does not claim these later modules are complete.

## 3. Database architecture

Use additive SQLAlchemy/Alembic changes. Keep SQLite for local development; PostgreSQL is the intended deployment database, with PostGIS added in the GIS phase after geometry requirements are known. Do not replace existing case/comparable/source tables or silently ingest historical databases.

Phase 1: `properties` with searchable identity/geography and validated land/planning/building/financial JSON sections, case link and owner; `property_revisions` with immutable full input/assumption snapshots; `property_assumptions` with unit/status/source/date/override; `data_sources`; append-only `market_observations` with raw/normalized value, geography, reliability and source record key. Owner scope is enforced for new workflows. Optimistic revision checks prevent overwritten edits. Database foreign keys and unique constraints protect links/history/import idempotency.

Subsequent phases: normalized parcels/transactions/listings as their workflows become concrete; `valuations`, `valuation_methods`, results and reconciliation snapshots linked to property revision; development/cashflow/financing/scenario/sensitivity/risk tables; portfolio memberships; report artifacts linked to the exact analysis revision. Every run must store calculation/data/model versions and source references. Explicit null means unknown; zero is not a missing-value substitute. Decimal-safe financial calculations are required when implementing methods.

## 4. Application architecture

Keep `Projects/Muqayyim-Downloads` as the active app (historical path retained for traceability). Next.js → typed REST client → FastAPI routers → services/validation → SQLAlchemy. Extend existing styles rather than redesign working case screens. New Properties and Data screens are real workflows, not navigation placeholders.

Financial engines remain separate Python modules, never TS components. Reuse Mizan through adapters, not copies of formulas. Market providers produce a common observation schema; a manual/CSV path works without external APIs. Existing extractors continue to supply comparable evidence through cases. Phase 1 links properties to those cases, without converting asking prices into completed sales.

Authentication remains a local development capability, not institutional security. New APIs use persisted identities and owner scoping; the old case endpoints need a separate tenancy/RBAC hardening pass before shared deployment. Roles and organizations are reused rather than replaced. Country/currency/locale are explicit, permit GCC expansion, and default to Saudi Arabia/SAR; complete bilingual UI is future work.

## 5. Implementation sequence and first files

1. Foundation: additive `api/app/models/foundation.py`, validation schemas, property/history/assumption service and router, source/observation ingestion, Alembic migration, real Properties/Data pages, legacy case links, reproducibility and migration tests.
2. Valuation: evidence-backed comparable/rent selection and adjustment; audit/adapt existing sales/income/DCF/cost; reconciliation and confidence; save calculation runs.
3. Development: residual land, appraisal, four HBU tests, maximum bid.
4. Investment: tested IRR/NPV/debt/cashflows/scenarios/sensitivity with explicit units and timings.
5. Intelligence: configurable risk, audited AVM/hedonic baselines, market analytics, GIS.
6. Output: portfolios, complete versioned reports/PDF, collaboration and institutional access controls.

Modify first: `api/app/main.py`, `database.py`, `auth/__init__.py`, add foundation modules/migration, extend `frontend/src/app/layout.tsx` and typed API client. Preserve case review and existing calculations. Add a root launch guide so the active app is unambiguous. Use isolated test databases; never migrate originals just to run tests.

## Subsequent map increment

After the initial assessment and Phase 1, a Leaflet/OpenStreetMap workspace was added in the existing Next.js/FastAPI app with Google Maps links, saved property/comparable layers, current-view counts, time filters and a synchronized evidence list. See `MAP-WORKSPACE.md` for scope, verification and remaining GIS work. The initial assessment above describes the pre-change codebase.
