# Qaim — Saudi Real Estate Valuation Platform

Internal workflow platform for real estate valuation in Saudi Arabia.  
**Stage 1: Comparable Link Ingestor** — fully functional MVP.

## Quick Start

### Option 1: Docker Compose (recommended)
```bash
cd qaim/infra
cp .env.example .env
docker compose up --build
```
- API: http://localhost:8000 (Swagger: http://localhost:8000/docs)
- Frontend: http://localhost:3000

### Option 2: Manual Setup

**Prerequisites:** Python 3.11+, Node 20+, PostgreSQL, Redis

```bash
# 1. Database
createdb qaim  # or use Docker: docker run -d -p 5432:5432 -e POSTGRES_USER=qaim -e POSTGRES_PASSWORD=qaim_dev -e POSTGRES_DB=qaim postgres:16-alpine

# 2. Redis
docker run -d -p 6379:6379 redis:7-alpine

# 3. API
cd qaim
pip install -r api/requirements.txt
PYTHONPATH=. uvicorn api.app.main:app --reload --port 8000

# 4. Frontend
cd frontend
npm install
npm run dev
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://qaim:qaim_dev@localhost:5432/qaim` | Async DB connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis URL |
| `UPLOAD_DIR` | `/tmp/qaim_uploads` | File upload directory |
| `EXPORT_DIR` | `/tmp/qaim_exports` | Export output directory |
| `SECRET_KEY` | `qaim-dev-secret-change-in-prod` | JWT secret |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` | Frontend API base URL |

## API Endpoints (Stage 1)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/cases` | Create case |
| `GET` | `/api/v1/cases` | List cases |
| `GET` | `/api/v1/cases/{id}` | Get case |
| `POST` | `/api/v1/cases/{id}/sources/url` | Add URL source |
| `POST` | `/api/v1/cases/{id}/sources/pdf` | Upload PDF source |
| `GET` | `/api/v1/cases/{id}/sources` | List sources |
| `POST` | `/api/v1/cases/{id}/sources/{sid}/extract` | Start extraction |
| `GET` | `/api/v1/cases/{id}/jobs` | List extraction jobs |
| `GET` | `/api/v1/jobs/{id}` | Get job status |
| `GET` | `/api/v1/cases/{id}/comps` | Get comparables |
| `PATCH` | `/api/v1/comps/{id}/status` | Mark invalid/outlier |
| `POST` | `/api/v1/comps/{id}/override` | Override field |
| `GET` | `/api/v1/cases/{id}/export/csv` | Export CSV |
| `GET` | `/api/v1/cases/{id}/export/xlsx` | Export XLSX |

## Defaults

- **Currency:** SAR
- **Area unit:** sqm (sqft conversion available)
- **Confidence scale:** 0.0–1.0 per field
- **Reliability scale:** 1–5 (1=user-entered → 5=authenticated transaction)
- **Extraction:** deterministic regex first, LLM stub for ambiguous fields

## Architecture

```
qaim/
├── api/          FastAPI backend (routes, services, models)
├── frontend/     Next.js frontend (case UI, comps table, export)
├── workers/      Extraction worker (inline MVP, Celery-ready)
├── extractors/   HTML + PDF extraction pipelines
├── schemas/      Shared Pydantic schemas + enums
├── providers/    Stage 4 provider interfaces (Aqar, Pasteah, Aqarsas stubs)
├── valuation-engine/  Stage 3 adjustment engine (stubs)
├── reporting/    CSV/XLSX/PDF export
├── infra/        Docker Compose + env config
└── docs/         Architecture docs
```

## Stage Status

| Stage | Status | Description |
|-------|--------|-------------|
| 0 | ✅ Done | Schemas, provenance, audit logs, repo architecture |
| 1 | ✅ Done | Comparable link ingestor (URL + PDF → extract → review → export) |
| 2 | 📋 Scaffolded | Subject property profile (schemas + stubs) |
| 3 | 📋 Scaffolded | Adjustment engine (interfaces + rule stubs) |
| 4 | 📋 Scaffolded | Comparable discovery (provider interfaces) |
| 5 | 📋 Scaffolded | Valuation report generator (interface + PDF stub) |
