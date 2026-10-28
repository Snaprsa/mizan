# Phase 1 implementation and verification — 25 October 2026

## Delivered

The existing Next.js/FastAPI Muqayyim application was extended in place. New tables: properties, property_revisions, property_assumptions, data_sources, market_observations. Existing cases, comparables, citations, overrides, exports, models and historical databases remain preserved.

New property endpoints support minimal creation, identity/geography search, full validated input replacement, case linking, assumption updates, history listing and exact snapshot retrieval. Source/observation endpoints support provider-independent registration, append-only JSON/CSV ingestion, idempotent replays and filtered/paginated retrieval. A local-file catalog exposes candidate datasets as unverified. No market record is seeded by the new workflows.

New frontend routes: `/properties`, `/properties/[id]`, `/data`. Existing case screens and styles are retained. New workspace tabs are Overview, Assumptions, Comparables, Market and History. Unsupported modules are explicitly identified as not implemented. Arabic labels and locale metadata are present; this is not a completed Arabic translation.

The auth dependency now persists the development identity so foreign keys can be enforced. JWT subjects must resolve to an active user; roles are loaded from the database. New workflows are owner-scoped, with viewer/reviewer writes rejected. SQLite foreign keys are enabled. Existing case APIs still need a separate tenancy/access-control pass before shared deployment.

## Evidence

- **58 backend tests pass**: existing case/source, extraction normalization/confidence and CSV/XLSX/PDF export tests, plus new property validation/search/history, stale revision rejection, explicit zero override, source/observation scope, CSV validation, atomic conflicting imports and idempotency.
- **Migration round trips pass** on an empty database and a disposable recovered copy of the historical database. All legacy table row counts are unchanged by the additive migration and rollback. PostgreSQL migrations are defined but were not executed against a PostgreSQL server.
- **Next.js production build succeeds**, including TypeScript and ESLint validation.
- **Browser workflow passes** using local headless Chromium: property creation, edits, persistence after reload, sourced assumption entry, historical revision retrieval, source registration and CSV import. No page errors occurred. All synthetic verification records were confined to `/tmp/mizan-phase1-ui-test.db`, separate from the runtime database.
- **Mizan-Desktop: 20 tests pass. Mizan-Antigravity: 17 tests pass.** Their calculation code was not changed.
- Existing code emits datetime deprecation warnings; frontend tooling reports stale Browserslist metadata. These did not prevent passing checks.

## Database preservation

Runtime DB is `Projects/Muqayyim-Downloads/storage/mizan.db`. Its initial content came from a disposable recovered clone of `muqayyim_dev.db` because the relocated historical snapshot includes a rollback journal. Historical DB and journal were not migrated in place. Startup backs up the runtime DB and applies Alembic migrations. Qaim's older database remains separate; automatic merging would risk duplicate evidence.

## Next phase

Audit and adapt the existing Mizan sales/income/DCF/cost/reconciliation modules through the property snapshot contract. Require explicit assumptions and verified comparable provenance; add calculation/model/data versions, stable decimal financial maths, method applicability and defensible confidence. No placeholder valuation results, risk scores or investment recommendations were introduced in Phase 1.
