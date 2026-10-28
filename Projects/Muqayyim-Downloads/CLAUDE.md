# CLAUDE.md — Saudi Real Estate Valuation Platform

## Project Identity
- **Name**: Muqayyim (مقيم) — Saudi Real Estate Valuation Platform
- **Type**: Internal enterprise tool, monorepo
- **Current Phase**: Stage 1 — Comparable Link Ingestor (MVP)
- **Goal**: Build a production-quality real estate valuation workflow starting with comp ingestion

---

## Quick Reference — What's Built vs Scaffolded

| Stage | Status | Description |
|-------|--------|-------------|
| 0 | ✅ Build now | Foundations: schemas, auth, audit, repo structure |
| 1 | ✅ Build now | Comparable ingestor: paste URLs / upload PDFs → extract → review → export |
| 2 | 🔲 Scaffold | Subject property profile builder |
| 3 | 🔲 Scaffold | Adjustment engine (rules-first, AI-assisted) |
| 4 | 🔲 Scaffold | Comparable discovery via provider plugins |
| 5 | 🔲 Scaffold | Full valuation report generator |

---

## Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | Next.js 14 + TypeScript + Tailwind + shadcn/ui | Fast internal UI, SSR-ready |
| Backend API | FastAPI (Python 3.11+) | Typed, async, fast to build |
| Database | PostgreSQL 16 + PostGIS | Relational + geospatial ready |
| Queue | Celery + Redis | Async extraction jobs |
| File Storage | Local filesystem (S3-abstracted interface) | Dev-first, swap to S3 later |
| PDF Parsing | pdfplumber + PyMuPDF | Robust table/text extraction |
| HTML Parsing | BeautifulSoup + httpx | Lightweight, no browser needed for MVP |
| LLM | Anthropic Claude API (via `anthropic` SDK) | Structured extraction fallback only |
| Export | openpyxl (XLSX) + csv + reportlab (PDF) | Standard Python libs |
| Auth | Simple JWT (internal) | RBAC-ready structure |
| Containerization | Docker + docker-compose | One-command local setup |

---

## Repo Structure

```
/
├── CLAUDE.md                    ← You are here
├── TASKS.md                     ← Phased build tasks
├── docker-compose.yml
├── .env.example
├── README.md
│
├── frontend/                    ← Next.js app
│   ├── package.json
│   ├── next.config.js
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── src/
│   │   ├── app/                 ← App Router pages
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx         ← Dashboard / case list
│   │   │   ├── cases/
│   │   │   │   ├── new/page.tsx
│   │   │   │   └── [id]/page.tsx  ← Case detail + comps table
│   │   │   └── (future)/       ← Placeholder routes for stages 2-5
│   │   ├── components/
│   │   │   ├── ui/              ← shadcn primitives
│   │   │   ├── cases/           ← Case-related components
│   │   │   ├── sources/         ← Source input/upload components
│   │   │   ├── comps/           ← Comps table, citation viewer, override modal
│   │   │   └── layout/          ← Shell, nav, sidebar
│   │   ├── lib/
│   │   │   ├── api.ts           ← API client (fetch wrapper)
│   │   │   ├── types.ts         ← TypeScript types mirroring backend schemas
│   │   │   └── utils.ts
│   │   └── hooks/
│   └── public/
│
├── api/                         ← FastAPI backend
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/                 ← DB migrations
│   ├── app/
│   │   ├── main.py              ← FastAPI app entry
│   │   ├── config.py            ← Settings from env
│   │   ├── database.py          ← SQLAlchemy engine + session
│   │   ├── models/              ← SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── case.py
│   │   │   ├── source.py
│   │   │   ├── extraction.py
│   │   │   ├── comparable.py
│   │   │   ├── override.py
│   │   │   └── _future.py       ← Stub models for stages 2-5
│   │   ├── schemas/             ← Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── common.py        ← Citation, ExtractedField, enums
│   │   │   ├── case.py
│   │   │   ├── source.py
│   │   │   ├── extraction.py
│   │   │   ├── comparable.py
│   │   │   ├── export.py
│   │   │   └── _future.py       ← SubjectProperty, Adjustment, ValuationRun stubs
│   │   ├── routers/             ← API route handlers
│   │   │   ├── cases.py
│   │   │   ├── sources.py
│   │   │   ├── extractions.py
│   │   │   ├── comparables.py
│   │   │   ├── exports.py
│   │   │   └── _future.py
│   │   ├── services/            ← Business logic
│   │   │   ├── case_service.py
│   │   │   ├── source_service.py
│   │   │   ├── extraction_service.py
│   │   │   ├── comparable_service.py
│   │   │   ├── export_service.py
│   │   │   └── _future.py
│   │   ├── auth/                ← JWT auth + RBAC hooks
│   │   │   ├── __init__.py
│   │   │   ├── jwt.py
│   │   │   └── rbac.py
│   │   └── audit/               ← Audit logging
│   │       ├── __init__.py
│   │       └── logger.py
│   └── tests/
│       ├── conftest.py
│       ├── test_cases.py
│       ├── test_extraction.py
│       └── test_export.py
│
├── workers/                     ← Celery async tasks
│   ├── __init__.py
│   ├── celery_app.py
│   ├── tasks/
│   │   ├── extraction_task.py   ← Main extraction orchestrator
│   │   └── _future.py
│   └── config.py
│
├── extractors/                  ← Extraction pipelines
│   ├── __init__.py
│   ├── base.py                  ← BaseExtractor interface
│   ├── html_extractor.py        ← URL → structured data
│   ├── pdf_extractor.py         ← PDF → structured data
│   ├── normalizer.py            ← Saudi-specific normalization
│   ├── confidence.py            ← Confidence scoring engine
│   ├── citation.py              ← Citation object builder
│   ├── llm_fallback.py          ← LLM-assisted extraction (fallback only)
│   └── field_mapping.py         ← Known site field mappings
│
├── providers/                   ← Stage 4 provider plugins (scaffold)
│   ├── __init__.py
│   ├── base.py                  ← BaseProvider interface
│   ├── aqar.py                  ← AqarProvider stub
│   ├── pasteah.py               ← PasteahProvider stub
│   ├── aqarsas.py               ← AqarsasProvider stub
│   └── manual.py                ← ManualProvider (user-entered comps)
│
├── valuation_engine/            ← Stage 3 scaffold
│   ├── __init__.py
│   ├── base.py                  ← AdjustmentEngine interface
│   ├── rules.py                 ← Rules engine stub
│   ├── schemas.py               ← Adjustment, ValuationRun schemas
│   └── approval.py              ← Approval workflow stub
│
├── reporting/                   ← Export + report generation
│   ├── __init__.py
│   ├── csv_export.py
│   ├── xlsx_export.py
│   ├── pdf_summary.py           ← Simple comp summary PDF
│   ├── templates/               ← Report templates (Stage 5)
│   │   └── _placeholder.md
│   └── report_generator.py      ← Stage 5 stub
│
├── schemas/                     ← Shared domain schemas (importable by all)
│   ├── __init__.py
│   ├── enums.py                 ← PropertyType, DealType, AreaType, etc.
│   ├── citation.py              ← CitationObject
│   ├── extracted_field.py       ← ExtractedField with citation
│   ├── comparable.py            ← Comparable
│   ├── subject.py               ← SubjectProperty (Stage 2 stub)
│   ├── adjustment.py            ← Adjustment (Stage 3 stub)
│   ├── valuation.py             ← ValuationRun (Stage 3 stub)
│   └── report.py                ← ReportTemplate (Stage 5 stub)
│
├── infra/
│   ├── docker/
│   │   ├── Dockerfile.api
│   │   ├── Dockerfile.frontend
│   │   └── Dockerfile.worker
│   ├── nginx/
│   │   └── dev.conf
│   └── scripts/
│       ├── init-db.sh
│       └── seed-demo.py
│
└── docs/
    ├── ARCHITECTURE.md
    ├── API.md
    ├── SETUP.md
    ├── STAGES.md
    └── DATA_MODEL.md
```

---

## Absolute Rules (Enforce These Always)

### 1. No Hallucinations
- If data is missing → store as `null` with `confidence: 0`
- Never invent prices, locations, dates, or legal status
- Every value must trace to a source

### 2. Human-in-the-Loop
- AI suggests, human approves
- Every manual edit → audit log entry with `user_id`, `timestamp`, `reason`, `old_value`, `new_value`

### 3. Full Provenance (Citation Objects)
Every extracted field MUST carry a `CitationObject`:
```python
class CitationObject(BaseModel):
    source_id: UUID
    source_type: SourceType          # url, pdf, manual
    source_url_or_name: str
    retrieval_timestamp: datetime
    locator: Optional[str]           # CSS selector / XPath / page:line / bbox
    snippet: Optional[str]           # Raw text excerpt (≤500 chars)
    extractor_name: str
    extractor_version: str
    parse_confidence: float          # 0.0–1.0
    llm_confidence: Optional[float]  # Only if LLM was used
    crosscheck_confidence: Optional[float]
    normalization_notes: Optional[str]
```

### 4. Saudi-First Defaults
- Currency: **SAR** (Saudi Riyal)
- Area unit: **sqm** (support sqft conversion)
- Languages: Arabic + English (store both where available)
- Dates: Support Hijri + Gregorian, store both
- Locations: Store raw text + normalized (city/district/subdistrict/coords)

### 5. Evidence Reliability Scale
```
5 = Authenticated transaction / contract / official record
4 = Official filing / regulatory disclosure / Ejar
3 = Broker brochure / broker PDF / agency listing
2 = Marketplace listing (Aqar, Pasteah, etc.)
1 = User-entered / unverified / hearsay
```
Store as `reliability_score: int` on every comparable.

### 6. Fact / Assumption / Judgment Classification
```python
class DataClassification(str, Enum):
    FACT = "fact"              # Directly from source with citation
    ASSUMPTION = "assumption"  # Requires human confirmation
    JUDGMENT = "judgment"      # Human valuation decision
```
Tag fields where appropriate. Required for Stage 3+, optional metadata in Stage 1.

---

## Data Model (Key Entities)

### Core Tables (Build Now)
- **users**: id, email, name, role, org_id, created_at
- **organizations**: id, name, tenant isolation
- **cases**: id, title, description, status, org_id, created_by, created_at
- **sources**: id, case_id, source_type (url/pdf/manual), url, file_path, raw_content, status, created_at
- **extraction_jobs**: id, source_id, status (pending/running/completed/failed), extractor_version, started_at, completed_at, error_log
- **extracted_fields**: id, extraction_job_id, comparable_id, field_name, raw_value, normalized_value, confidence, citation (JSONB), extraction_version
- **comparables**: id, case_id, source_id, extraction_job_id, status (active/invalid/outlier), reliability_score, created_at
- **overrides**: id, extracted_field_id, old_value, new_value, reason, user_id, timestamp
- **audit_log**: id, entity_type, entity_id, action, user_id, details (JSONB), timestamp

### Future Tables (Scaffold as Empty Migrations)
- **subject_properties**: Stage 2
- **adjustments**: Stage 3
- **valuation_runs**: Stage 3
- **provider_configs**: Stage 4
- **report_templates**: Stage 5
- **report_artifacts**: Stage 5

---

## Stage 1 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/cases | Create case |
| GET | /api/v1/cases | List cases |
| GET | /api/v1/cases/{id} | Get case detail |
| POST | /api/v1/cases/{id}/sources/url | Add URL source |
| POST | /api/v1/cases/{id}/sources/pdf | Upload PDF source |
| GET | /api/v1/cases/{id}/sources | List sources |
| POST | /api/v1/sources/{id}/extract | Start extraction job |
| GET | /api/v1/extraction-jobs/{id} | Get job status |
| GET | /api/v1/cases/{id}/comparables | Get extracted comps |
| PATCH | /api/v1/comparables/{id}/fields/{field_id} | Override field value |
| PATCH | /api/v1/comparables/{id}/status | Mark invalid/outlier |
| GET | /api/v1/cases/{id}/export/xlsx | Export XLSX |
| GET | /api/v1/cases/{id}/export/csv | Export CSV |
| GET | /api/v1/cases/{id}/export/pdf | Export summary PDF (optional) |

---

## Extraction Pipeline (Order of Operations)

```
1. Ingest source (URL or PDF)
2. Fetch + store raw content (HTML or PDF bytes)
3. Parse into text/DOM blocks
4. Run deterministic extraction (regex, known field patterns, structured selectors)
5. Normalize values (SAR, sqm, dates, locations)
6. LLM fallback ONLY for unresolved/ambiguous fields
7. Score confidence (deterministic_conf × source_reliability × llm_conf if used)
8. Attach citation objects to every field
9. Persist versioned results
10. Surface in review table
```

**LLM usage rule**: The LLM is a fallback parser, not a data source. It extracts from provided text. It must NEVER invent values.

---

## Frontend Pages (Stage 1)

1. **Dashboard** (`/`) — List of cases, create new
2. **Create Case** (`/cases/new`) — Title, description form
3. **Case Detail** (`/cases/[id]`) — Tabs: Sources | Comparables | Export
   - **Sources tab**: Paste URL form, PDF upload, source list with status
   - **Comparables tab**: Data table with all extracted fields, inline citation popover, override modal, status toggle (active/invalid/outlier)
   - **Export tab**: Download XLSX/CSV/PDF buttons

---

## Environment Variables

```env
# Database
DATABASE_URL=postgresql://tathmin:tathmin@localhost:5432/tathmin
REDIS_URL=redis://localhost:6379/0

# Auth
JWT_SECRET=dev-secret-change-in-prod
JWT_ALGORITHM=HS256

# LLM (fallback extraction)
ANTHROPIC_API_KEY=sk-ant-...

# Storage
STORAGE_BACKEND=local         # local | s3
STORAGE_LOCAL_PATH=./storage
S3_BUCKET=                    # For production
S3_REGION=me-south-1          # Bahrain region for KSA

# App
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_URL=http://localhost:3000
API_URL=http://localhost:8000
```

---

## Commands

```bash
# Full local startup
docker-compose up -d

# Backend only
cd api && uvicorn app.main:app --reload

# Frontend only
cd frontend && npm run dev

# Worker only
cd workers && celery -A celery_app worker --loglevel=info

# Run migrations
cd api && alembic upgrade head

# Run tests
cd api && pytest

# Seed demo data
python infra/scripts/seed-demo.py
```

---

## Code Style & Conventions

- **Python**: Black formatter, isort, type hints everywhere, Pydantic v2 for schemas
- **TypeScript**: Strict mode, no `any` unless truly necessary
- **Naming**: snake_case for Python, camelCase for TS, SCREAMING_SNAKE for env vars
- **IDs**: UUID v4 everywhere
- **Timestamps**: UTC always, ISO 8601 format
- **API responses**: Consistent envelope: `{ data, meta, errors }`
- **Error handling**: Never swallow exceptions silently; log and surface

---

## What NOT To Do

- ❌ Don't invent real estate data or prices
- ❌ Don't use LLM as primary extractor — it's a fallback
- ❌ Don't build scraping that violates ToS
- ❌ Don't auto-apply adjustments without human approval
- ❌ Don't store untyped JSON blobs without schemas
- ❌ Don't skip citation objects for extracted fields
- ❌ Don't build a pretty UI before the workflow works
- ❌ Don't overengineer — get Stage 1 working end-to-end first
