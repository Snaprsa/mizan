# Muqayyim (مقيم) — Saudi Real Estate Valuation Platform

Internal platform for automating real estate valuation workflows in Saudi Arabia. Muqayyim helps valuers and analysts collect, organize, and review comparable property data to support RICS-standard valuation reports.

---

## Quick Start (No Docker Required)

### Prerequisites
- Python 3.11+
- pip package manager

### Install & Run

```bash
# Install Python dependencies (one time)
pip install --break-system-packages fastapi uvicorn[standard] sqlalchemy[asyncio] aiosqlite alembic pydantic pydantic-settings python-multipart httpx beautifulsoup4 lxml pdfplumber anthropic openpyxl reportlab celery redis aiofiles python-jose[cryptography] passlib[bcrypt]

# Start the API
bash start_api.sh

# API is live at:
# http://localhost:8000       — API
# http://localhost:8000/docs  — Interactive API docs (Swagger)
# http://localhost:8000/redoc — Alternative API docs (ReDoc)
```

The script sets up SQLite for local development automatically. Database file: `/tmp/muqayyim_dev.db`

---

## Quick Start (Docker)

### Prerequisites
- Docker and Docker Compose installed
- ANTHROPIC_API_KEY for Claude API (optional, fallback extraction only)

### Run

```bash
# Copy and configure environment
cp .env.example .env
# Edit .env if needed — set ANTHROPIC_API_KEY

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api
```

**Access**:
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432 (user: muqayyim, pass: muqayyim, db: muqayyim)
- Redis: localhost:6379

**Stop**:
```bash
docker-compose down
```

---

## Current Capabilities (Stage 1)

Muqayyim in Stage 1 provides the **Comparable Ingestor** — the foundation for valuation workflows:

### Create & Manage Cases
- Create new valuation cases (title + description)
- Track case status and source organization
- View comparable summaries at a glance

### Ingest Comparable Sources
- **URL Paste**: Add property listings by URL (Aqar.fm, AqarSAS, Paseetah, etc.)
- **PDF Upload**: Upload property brochures or market analysis documents
- Automatic source scheduling for extraction

### Auto-Extract Property Data
- **Site-Specific Extraction**: Field mappings for Aqar.fm, AqarSAS, Paseetah
- **HTML Parsing**: BeautifulSoup-based deterministic extraction (no hallucination)
- **PDF Parsing**: pdfplumber for table and text extraction from documents
- **LLM Fallback**: Claude API for ambiguous/unstructured data (opt-in, tagged)

### Review & Override
- **Interactive Data Table**: All extracted fields in one view
- **Citation Popover**: Click any field to see the source excerpt and confidence score
- **Manual Override**: Edit values with audit trail (reason + timestamp)
- **Status Management**: Mark comparables as active, invalid, or outlier

### Full Provenance
- **Citation Objects**: Every extracted field includes:
  - Source URL and retrieval timestamp
  - Text locator (CSS selector or page reference)
  - Raw snippet (≤500 chars)
  - Confidence score (deterministic + LLM if used)
  - Extractor version for reproducibility
- **Audit Log**: All manual edits recorded with old/new values and reason

### Export Workflows
- **CSV Export**: Standard format for spreadsheet analysis
- **XLSX Export**: Excel with formatted headers and proper data types
- **PDF Summary**: One-page comparable summary (optional)

---

## Data Quality Standards

Muqayyim enforces strict data integrity:

### No Hallucinations
- Missing data stored as `null` with `confidence: 0`
- Every value traces to source (never invented)
- LLM is fallback parser only, not a data source

### Human-in-the-Loop
- AI suggests, human approves
- Every manual edit recorded in audit log
- Confidence scores guide reviewer attention

### Saudi-First Defaults
- Currency: **SAR** (Saudi Riyal)
- Area: **sqm** (square meter, with sqft conversion)
- Locations: City/district/subdistrict normalization
- Dates: Support Hijri + Gregorian, store both
- Languages: Arabic + English where available

### Reliability Scoring
Every comparable carries a reliability score:
- **5**: Authenticated transaction / contract / official record
- **4**: Official filing / regulatory disclosure / Ejar
- **3**: Broker brochure / agency listing
- **2**: Marketplace listing (Aqar, Pasteah, etc.)
- **1**: User-entered / unverified data

---

## Roadmap

Muqayyim follows a phased approach:

| Stage | Status | Focus |
|-------|--------|-------|
| **0** | ✅ Done | Foundations: schemas, auth, audit, repo structure |
| **1** | ✅ Done | Comparable ingestor: paste URLs / upload PDFs → extract → review → export |
| **2** | 🔲 Next | Subject property profile builder — define the property being valued |
| **3** | 🔲 Planned | Adjustment engine — rules-first comparable adjustments |
| **4** | 🔲 Planned | Comparable discovery — automated sourcing via provider plugins |
| **5** | 🔲 Planned | Full valuation report — RICS-compliant PDF/DOCX generation |

**Timeline**: ~3-4 months to production Stages 1-3. Stages 4-5 follow based on business priorities.

---

## Data Intelligence

### Source Map
See `docs/SOURCE_MAP.md` for a comprehensive map of **20+ Saudi real estate data sources**:
- Property marketplaces (Aqar.fm, AqarSAS, Paseetah, etc.)
- Government registries (Ejar, MHRSD)
- Broker networks and MLS systems
- Transaction databases
- Mortgage data providers

### Monitoring
Watch for new transactions and listings in real-time:

```bash
python3 scripts/monitoring/monitor_sources.py
```

This script monitors 10+ major Saudi sources and alerts on new activity.

### Collection
Extract individual property listings:

```bash
python3 scripts/collection/aqar_collector.py "https://aqar.fm/property/URL"
```

Output includes normalized fields (price, area, location, type, dates) with citations.

### Data Partnership Outreach
See `docs/DATA_PARTNERSHIP_OUTREACH.md` for professional templates to approach data providers (Aqar.fm, AqarSAS, etc.) for API access or data feeds.

---

## Architecture

### Technology Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Frontend** | Next.js 14 + TypeScript + Tailwind + shadcn/ui | Fast internal UI, SSR-ready |
| **Backend API** | FastAPI (Python 3.11+) | Typed, async, perfect for extraction pipelines |
| **Database** | PostgreSQL 16 + PostGIS (prod) / SQLite (dev) | Relational + geospatial ready |
| **Queue** | Celery + Redis | Async extraction jobs at scale |
| **File Storage** | Local filesystem (S3-abstracted) | Dev-first, swap to S3 later |
| **PDF Parsing** | pdfplumber + PyMuPDF | Robust table/text extraction |
| **HTML Parsing** | BeautifulSoup + httpx | Lightweight, no browser needed |
| **LLM** | Anthropic Claude API | Structured extraction fallback only |
| **Export** | openpyxl (XLSX) + csv + reportlab (PDF) | Standard Python libraries |
| **Auth** | Simple JWT (internal) | RBAC-ready structure |
| **Containerization** | Docker + docker-compose | One-command local setup |

### Key Design Decisions

1. **Deterministic-First Extraction**: HTML and PDF parsing before LLM (avoids hallucination)
2. **Full Citation Objects**: Every field links to source (not just values)
3. **Human Approval Loop**: AI extracts, humans review and approve
4. **Audit Everything**: Mutation logging for compliance and debugging
5. **Fail Gracefully**: Invalid URLs, PDFs, etc. mark jobs as "failed" (no crashes)
6. **Modular Stages**: Stage 1 works end-to-end; stages 2-5 build incrementally

---

## Project Structure

```
/
├── start_api.sh                 ← Quick start script (no Docker needed)
├── docker-compose.yml           ← Full stack with PostgreSQL + Redis + API + Worker + Frontend
├── CLAUDE.md                    ← Architecture and rules (detailed)
├── TASKS.md                     ← Phased build plan
├── README.md                    ← You are here
│
├── api/                         ← FastAPI backend
│   ├── app/
│   │   ├── main.py              ← FastAPI app entry
│   │   ├── models/              ← SQLAlchemy ORM models
│   │   ├── schemas/             ← Pydantic request/response schemas
│   │   ├── routers/             ← API route handlers
│   │   ├── services/            ← Business logic
│   │   └── auth/                ← JWT auth + RBAC
│   └── tests/                   ← Test suite
│
├── extractors/                  ← Data extraction pipelines
│   ├── html_extractor.py        ← URL → structured data
│   ├── pdf_extractor.py         ← PDF → structured data
│   ├── normalizer.py            ← Saudi-specific normalization
│   ├── confidence.py            ← Confidence scoring
│   ├── citation.py              ← Citation object builder
│   └── llm_fallback.py          ← Claude API (fallback only)
│
├── frontend/                    ← Next.js app
│   ├── src/app/
│   │   ├── page.tsx             ← Dashboard / case list
│   │   ├── cases/new/page.tsx   ← Create case
│   │   └── cases/[id]/page.tsx  ← Case detail (Sources/Comps/Export)
│   └── src/components/          ← React components
│
├── scripts/
│   ├── monitoring/
│   │   └── monitor_sources.py   ← Real-time monitoring of 10+ Saudi sources
│   └── collection/
│       └── aqar_collector.py    ← Extract individual property listings
│
├── logs/                        ← Activity & test results
│   ├── CHANGELOG.md             ← Version history
│   ├── BUG_LOG.md               ← Known issues & fixes
│   └── TEST_RESULTS.md          ← Latest verification
│
└── docs/
    ├── ARCHITECTURE.md          ← System design details
    ├── API.md                   ← Endpoint reference
    ├── SOURCE_MAP.md            ← Saudi data sources (20+)
    ├── DATA_PARTNERSHIP_OUTREACH.md ← Email templates
    └── ...
```

For complete architecture details, see `CLAUDE.md`.

---

## API Reference

### Core Endpoints (Stage 1)

```
POST   /api/v1/cases                      — Create case
GET    /api/v1/cases                      — List cases
GET    /api/v1/cases/{id}                 — Get case detail

POST   /api/v1/cases/{id}/sources/url     — Add URL source
POST   /api/v1/cases/{id}/sources/pdf     — Upload PDF
GET    /api/v1/cases/{id}/sources         — List sources

POST   /api/v1/sources/{id}/extract       — Trigger extraction
GET    /api/v1/extraction-jobs/{id}       — Get job status

GET    /api/v1/cases/{id}/comparables     — List comparables
PATCH  /api/v1/comparables/{id}/fields/{field_id}  — Override field
PATCH  /api/v1/comparables/{id}/status    — Update status

GET    /api/v1/cases/{id}/export/csv      — Export CSV
GET    /api/v1/cases/{id}/export/xlsx     — Export XLSX
GET    /api/v1/cases/{id}/export/pdf      — Export PDF summary
```

**Interactive Docs**: http://localhost:8000/docs (requires running API)

---

## Environment Variables

```env
# Database (auto-set in start_api.sh)
DATABASE_URL=sqlite+aiosqlite:////tmp/muqayyim_dev.db
DATABASE_URL_SYNC=sqlite:////tmp/muqayyim_dev.db

# Auth
JWT_SECRET=dev-secret-change-in-prod
JWT_ALGORITHM=HS256

# LLM Fallback (optional but recommended)
ANTHROPIC_API_KEY=sk-ant-...

# Storage
STORAGE_BACKEND=local         # local | s3
STORAGE_LOCAL_PATH=./storage

# App
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_URL=http://localhost:3000
API_URL=http://localhost:8000

# Optional: Celery
CELERY_ALWAYS_EAGER=false     # Set true to run extraction synchronously (no Redis needed)

# Optional: Site Credentials (for authenticated sources)
AQARSAS_EMAIL=...
AQARSAS_PASSWORD=...
```

See `.env.example` for defaults.

---

## Development

### Local Setup (Without Docker)

```bash
# 1. Install Python dependencies
pip install --break-system-packages [see pip install command above]

# 2. Start the API
bash start_api.sh

# 3. In another terminal, start the frontend
cd frontend
npm install  # if needed
npm run dev

# Frontend is now at http://localhost:3000
```

### Running Tests

```bash
cd api
pytest -v

# Or specific test file
pytest tests/test_cases.py -v

# With coverage
pytest --cov=app tests/
```

### Database Migrations (PostgreSQL only)

```bash
cd api
alembic upgrade head          # Apply migrations
alembic downgrade -1          # Rollback one migration
alembic revision --autogenerate -m "Description"  # Generate migration
```

**Note**: SQLite (dev) auto-migrates; no manual migrations needed.

### Code Style

- **Python**: Black formatter, isort, type hints
- **TypeScript**: Strict mode, no `any`
- **Run formatter**: `black api/` and `isort api/`

---

## Troubleshooting

### API won't start
```bash
# Check database file
ls -la /tmp/muqayyim_dev.db

# Check port 8000 is free
lsof -i :8000

# Check Python version
python3 --version  # Should be 3.11+
```

### Extraction job stuck
```bash
# Check Redis running (if using Celery)
redis-cli ping  # Should return PONG

# Check worker logs
docker-compose logs worker

# Or run synchronously
export CELERY_ALWAYS_EAGER=true
bash start_api.sh
```

### PDF upload fails
```bash
# Make sure to use multipart/form-data
curl -X POST http://localhost:8000/api/v1/cases/{id}/sources/pdf \
  -F "file=@document.pdf" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### LLM fallback not working
- Set `ANTHROPIC_API_KEY` in `.env`
- Check API key is valid: `curl -H "Authorization: Bearer $ANTHROPIC_API_KEY" https://api.anthropic.com/...`

---

## Support

### Documentation
- **Architecture**: See `CLAUDE.md` for system design and rules
- **Phased Plan**: See `TASKS.md` for build roadmap
- **Known Issues**: See `logs/BUG_LOG.md`
- **Test Results**: See `logs/TEST_RESULTS.md`
- **Changelog**: See `logs/CHANGELOG.md`

### Reporting Issues
- File a bug: Update `logs/BUG_LOG.md` with reproducible steps
- Test results: Run test suite and attach output
- Environment: Include OS, Python version, Docker vs. local

---

## License

**Proprietary** — Internal use only

---

## Credits

**Muqayyim** (مقيم) — *Appraiser* in Arabic

Built for Saudi real estate professionals by the valuation technology team.

---

*Last Updated: 2026-03-24*
*Version: 0.2.0 (Muqayyim Rebrand & Intelligence Layer)*
