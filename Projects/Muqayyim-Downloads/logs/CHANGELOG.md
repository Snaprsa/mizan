# Muqayyim Changelog

All notable changes to the Muqayyim (مقيم) project are documented here.

---

## [0.2.0] - 2026-03-24 — Muqayyim Rebrand & Intelligence Layer

### Changed
- **Project Rebrand**: Renamed from Tathmin (تثمين) to Muqayyim (مقيم) across all codebase references
  - Updated API service title and identifiers
  - Updated database credentials and package names
  - Updated all documentation and configuration files

### Added
- **Data Collection Layer**: New infrastructure for systematic data sourcing
  - `data/transactions_scaffold.csv` — Transaction database structure
  - `data/listings_scaffold.csv` — Active listing database structure
  - `data/source_registry.csv` — Master registry of Saudi data sources
- **Monitoring Script**: `scripts/monitoring/monitor_sources.py` (10+ Saudi sources tracked)
  - Real-time monitoring of Aqar.fm, AqarSAS, Paseetah transactions and listings
  - Change detection and notification system
- **Collection Script**: `scripts/collection/aqar_collector.py`
  - Automated property listing data collection from Aqar.fm
  - Structured field extraction and normalization
- **Source Documentation**: `docs/SOURCE_MAP.md`
  - Comprehensive map of 20+ Saudi real estate data sources
  - Coverage, reliability scores, and integration notes for each source
- **ChatGPT Extraction Templates**: Prompt templates for structured data extraction
  - Available in extraction service for fallback parsing
- **Professional Outreach Materials**: Bilingual (Arabic/English) data partnership email
  - Template for approaching Aqar.fm and other data providers
- **Quick Start Script**: `start_api.sh` for one-command API startup
  - Sets up SQLite dev environment automatically

### Fixed
- **SQLite Path Issue**: Database now uses absolute path `/tmp/muqayyim_dev.db`
  - Resolved disk I/O errors from relative path handling
  - Improved reliability for local development
- **API Endpoint Verification**: All Stage 1 endpoints tested and verified working
  - Cases CRUD: create, list, get
  - Sources: add URL, upload PDF, list
  - Extraction: trigger job, get status
  - Comparables: retrieve extracted data
  - Exports: CSV, XLSX formats

### Verified
- ✅ API health check functional
- ✅ Case creation with proper UUID and timestamps
- ✅ Source ingestion (URL + PDF)
- ✅ Extraction job triggering and status tracking
- ✅ Graceful 404 handling for invalid URLs
- ✅ Comparable data retrieval
- ✅ CSV and XLSX export generation
- ✅ OpenAPI/Swagger documentation

---

## [0.1.0] - 2026-03-20 — Initial Build (Tathmin)

### Added
- **FastAPI Backend**
  - Async SQLAlchemy ORM with SQLite (dev) + PostgreSQL (prod) support
  - Core entity models: Organization, User, Case, Source, ExtractionJob, ExtractedField, Comparable, Override, AuditLog
  - Future entity stubs: SubjectProperty, Adjustment, ValuationRun, ReportArtifact

- **Stage 1 API Endpoints**
  - Case management: create, list, retrieve, update
  - Source ingestion: add URL source, upload PDF
  - Extraction orchestration: trigger jobs, get status
  - Comparable data: retrieve, filter, update status
  - Exports: CSV, XLSX, PDF summary

- **Data Extraction Pipeline**
  - HTML extractor with BeautifulSoup and site-specific field mappings
    - Support for Aqar.fm, AqarSAS, Paseetah
  - PDF extractor using pdfplumber
  - LLM fallback extraction via Anthropic Claude API
  - Confidence scoring engine
  - Citation objects on all extracted fields

- **Data Processing & Normalization**
  - Saudi-specific normalizer: SAR currency, sqm area units
  - Hijri/Gregorian date support
  - City/district/subdistrict location normalization
  - Property type and deal type classification

- **Export Functionality**
  - CSV export with full field data
  - XLSX export with formatting
  - PDF summary report generation

- **Security & Audit**
  - JWT authentication with dev bypass option
  - Full audit logging on all mutations
  - RBAC-ready role structure

- **Frontend (Next.js 14)**
  - Dashboard: case list with create button
  - Create Case: title and description form
  - Case Detail with three tabs:
    - Sources: URL paste form, PDF upload, source list
    - Comparables: interactive data table, citation popovers, override modal, status toggles
    - Export: download buttons for XLSX, CSV, PDF
  - Responsive Tailwind + shadcn/ui components

- **Async Processing**
  - Celery worker integration for extraction jobs
  - Redis queue support
  - Synchronous fallback for dev without Redis

- **Containerization**
  - Docker Compose setup
  - Services: PostgreSQL, Redis, API, Worker, Frontend
  - Development-friendly networking and volumes

- **Testing**
  - Test suite with pytest
  - Fixtures and conftest setup
  - Sample test cases for cases, extraction, export

- **Documentation**
  - CLAUDE.md: architecture and rules
  - TASKS.md: phased build plan
  - ARCHITECTURE.md: system design
  - API.md: endpoint documentation
  - SETUP.md: local development guide
  - DATA_MODEL.md: database schema reference

---

## Version Notes

**Muqayyim** (مقيم) means "Appraiser" in Arabic and represents the platform's core function: automated support for professional real estate appraisers and valuers in Saudi Arabia.

The transition from Tathmin (تثمين — "Valuation") to Muqayyim reflects a shift toward a more human-centered workflow where the platform assists appraisers rather than attempting full automation.
