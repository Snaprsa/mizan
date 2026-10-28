# TASKS.md — Build Execution Plan

Use this file to track progress. Work through tasks in order.
Mark each ✅ when complete.

---

## PHASE 0: Project Bootstrap (Do First)

- [x] **T0.1** Initialize monorepo root with this structure
- [x] **T0.2** Create `docker-compose.yml` with: PostgreSQL 16 + PostGIS, Redis 7, API (FastAPI), Worker (Celery), Frontend (Next.js)
- [x] **T0.3** Create `.env.example` with all env vars from CLAUDE.md
- [x] **T0.4** Set up `/api` — FastAPI project with `pyproject.toml`, dependencies
- [x] **T0.5** Set up `/frontend` — Next.js 14 with App Router, TypeScript strict, Tailwind
- [x] **T0.6** Create `/schemas` shared Python package with domain enums and base schemas
- [x] **T0.7** Set up Alembic migrations in `/api/alembic`
- [x] **T0.8** Create SQLAlchemy models for ALL core tables (users, orgs, cases, sources, extraction_jobs, extracted_fields, comparables, overrides, audit_log)
- [x] **T0.9** Create initial Alembic migration (auto-generate from models)
- [x] **T0.10** Create stub migration files for future tables (subject_properties, adjustments, valuation_runs, etc.)
- [x] **T0.11** Verify: API starts, DB is reachable via SQLite dev fallback

**Checkpoint**: Database is up, schema is migrated, API and frontend start without errors.

---

## PHASE 1: Shared Schemas & Core Types

- [x] **T1.1** Build `/schemas/enums.py` — PropertyType, DealType, EvidenceType, AreaType, SourceType, CaseStatus, ExtractionStatus, ComparableStatus, ReliabilityScore, Currency, DataClassification
- [x] **T1.2** Build `/schemas/citation.py` — CitationObject Pydantic model (full structure from CLAUDE.md)
- [x] **T1.3** Build `/schemas/extracted_field.py` — ExtractedField model with embedded CitationObject
- [x] **T1.4** Build `/schemas/comparable.py` — Comparable model with all KSA fields
- [x] **T1.5** Build future stubs: `/schemas/subject.py`, `/schemas/adjustment.py`, `/schemas/valuation.py`, `/schemas/report.py`
- [x] **T1.6** Build `/api/app/schemas/` — Pydantic request/response models for API (CreateCase, AddSource, etc.)

**Checkpoint**: All shared types compile, are importable, and match the data model spec.

---

## PHASE 2: Backend API — Cases & Sources

- [x] **T2.1** Build `/api/app/config.py` — Settings from environment
- [x] **T2.2** Build `/api/app/database.py` — Async SQLAlchemy engine + session maker
- [x] **T2.3** Build `/api/app/auth/jwt.py` — Simple JWT creation/verification (dev user for MVP)
- [x] **T2.4** Build `/api/app/auth/rbac.py` — Role check decorator stub (allow-all for MVP, structure for later)
- [x] **T2.5** Build `/api/app/audit/logger.py` — Audit log function: `log_action(entity_type, entity_id, action, user_id, details)`
- [x] **T2.6** Build `/api/app/routers/cases.py` — POST create, GET list, GET detail
- [x] **T2.7** Case CRUD logic (inline in routers)
- [x] **T2.8** Build `/api/app/routers/sources.py` — POST add URL, POST upload PDF, GET list for case
- [x] **T2.9** Source storage logic (inline in routers)
- [x] **T2.10** Build `/api/app/main.py` — FastAPI app with CORS, routers, lifespan events
- [x] **T2.11** Write tests: `test_cases.py` — Create, list, get case + source tests
- [x] **T2.12** Verify: Can create a case and add sources via curl/httpie

**Checkpoint**: Cases and sources API works end-to-end with database persistence.

---

## PHASE 3: Extraction Pipeline

- [x] **T3.1** Build `/extractors/base.py` — `BaseExtractor` ABC
- [x] **T3.2** Build `/extractors/citation.py` — `build_citation()` helper
- [x] **T3.3** Build `/extractors/confidence.py` — Confidence scoring
- [x] **T3.4** Build `/extractors/normalizer.py` — Saudi normalizations (currency, area, dates, locations, price/sqm)
- [x] **T3.5** Build `/extractors/html_extractor.py` — URL → structured data (+ Paseetah + AqarSAS extractors)
- [x] **T3.6** Build `/extractors/pdf_extractor.py` — PDF → structured data
- [x] **T3.7** Build `/extractors/llm_fallback.py` — LLM-assisted extraction (fallback only)
- [x] **T3.8** Build `/extractors/field_mapping.py` — Known field name mappings
- [x] **T3.9** Build `/workers/celery_app.py` — Celery app config with Redis broker
- [x] **T3.10** Build `/workers/tasks/extraction_task.py` — Extraction orchestrator
- [x] **T3.11** Build `/api/app/routers/extractions.py` — POST trigger extraction, GET job status
- [x] **T3.12** Build `/api/app/services/extraction_service.py` — Inline extraction (MVP, no Celery required)
- [x] **T3.13** Write tests: `test_extraction.py` — Normalizer + confidence scoring tests (24 tests)
- [x] **T3.14** Verify: Can trigger extraction on a source and see results in DB

**Checkpoint**: Full extraction pipeline works — URL or PDF → structured comparable with citations.

---

## PHASE 4: Comparables API & Review

- [x] **T4.1** Build `/api/app/routers/comparables.py` — GET list, PATCH override, PATCH status
- [x] **T4.2** Comp retrieval, field override with audit logging (inline in routers)
- [x] **T4.3** Verify: Can retrieve comps, override a field, mark invalid — all with audit trail

**Checkpoint**: Comparables are queryable, editable, and audited.

---

## PHASE 5: Export

- [x] **T5.1** Build `/reporting/csv_export.py` — Case comps → CSV bytes
- [x] **T5.2** Build `/reporting/xlsx_export.py` — Case comps → XLSX with formatting
- [x] **T5.3** Build `/reporting/pdf_summary.py` — Simple comp summary PDF
- [x] **T5.4** Build `/api/app/routers/exports.py` — GET CSV, GET XLSX, GET PDF endpoints
- [x] **T5.5** Write tests: `test_export.py` — Export with sample data produces valid files (7 tests)
- [x] **T5.6** Verify: Download XLSX/CSV from API with real extracted data

**Checkpoint**: Export works end-to-end with formatted output.

---

## PHASE 6: Frontend

- [x] **T6.1** Set up `/frontend/src/lib/api.ts` — Typed fetch wrapper for all API endpoints
- [x] **T6.2** Set up `/frontend/src/lib/types.ts` — TypeScript types mirroring all Pydantic schemas
- [x] **T6.3** Build layout shell: sidebar nav, header, content area
- [x] **T6.4** Build Dashboard page (`/`) — Case list table with status, create button, stat cards
- [x] **T6.5** Build Create Case page (`/cases/new`) — Simple form: title, description
- [x] **T6.6** Build Case Detail page (`/cases/[id]`) — Tabbed layout: Sources | Comparables | Export
- [x] **T6.7** Build Sources tab — URL paste, PDF upload, source list, Extract button, status polling
- [x] **T6.8** Build Comparables tab — Data table, confidence color coding, citation modal, override modal, status toggle, reliability stars
- [x] **T6.9** Build Export tab — Download XLSX, CSV, PDF buttons
- [x] **T6.10** Add toast notifications (replaced alert() with toast system)
- [x] **T6.11** Full user flow works — create case → add source → extract → review → edit → export

**Checkpoint**: Complete working UI for Stage 1.

---

## PHASE 7: Future Stage Scaffolding

- [x] **T7.1** Create `/providers/base.py` — `BaseProvider` ABC
- [x] **T7.2** Create provider stubs: `aqar.py`, `pasteah.py`, `aqarsas.py`, `manual.py` (all in base.py)
- [x] **T7.3** Create `/valuation_engine/base.py` — `AdjustmentEngine` ABC
- [x] **T7.4** Create `/valuation_engine/rules.py` — RulesEngine class (in base.py)
- [x] **T7.5** Create `/valuation_engine/approval.py` — ApprovalWorkflow class (in base.py)
- [x] **T7.6** Create `/reporting/report_generator.py` — `generate_report(valuation_run) -> ReportArtifact` stub
- [x] **T7.7** Create frontend route placeholders: `/subject`, `/adjustments`, `/discovery`, `/reports`
- [x] **T7.8** Create `/docs/STAGES.md` documenting what each future stage needs

**Checkpoint**: All future stages have clear entry points and interfaces.

---

## PHASE 8: Polish & Handoff

- [x] **T8.1** Write `/docs/SETUP.md` — Step-by-step local dev setup
- [x] **T8.2** Write `/docs/ARCHITECTURE.md` — System overview with diagram description
- [x] **T8.3** Write `/docs/API.md` — Endpoint reference
- [x] **T8.4** Write `/docs/DATA_MODEL.md` — ER description
- [x] **T8.5** Create `/infra/scripts/seed-demo.py` — Seeds a demo case with sample comps
- [x] **T8.6** Final `README.md` with quick start
- [ ] **T8.7** Verify: Fresh `docker-compose up` → migrations → seed → full flow works

**Checkpoint**: Project is handoff-ready.

---

## Execution Notes for Claude Code

1. **Work sequentially** through phases. Don't skip ahead.
2. **Test each checkpoint** before moving on.
3. **If blocked**, leave a TODO comment and move to the next task.
4. **Prefer working code over perfect code** — we can refine later.
5. **Every extracted field MUST have a citation** — this is non-negotiable.
6. **Use the LLM extraction fallback sparingly** — deterministic first.
7. **Keep the frontend functional, not beautiful** — internal tool aesthetic.
8. **All IDs are UUIDs**, all timestamps are UTC, all amounts default to SAR.
