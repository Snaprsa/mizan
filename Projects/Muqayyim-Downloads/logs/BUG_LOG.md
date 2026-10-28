# Muqayyim Bug Log

Status tracking for known issues, fixes, and pending resolutions.

---

## Fixed Issues

### SQLite Relative Path Caused Disk I/O Error
- **Severity**: High
- **Status**: ✅ FIXED (2026-03-24)
- **Description**: When using `sqlite:///./storage/dev.db`, relative path resolution would fail inconsistently depending on working directory at startup, causing "database disk image is malformed" errors.
- **Root Cause**: SQLAlchemy and asyncio SQLite driver did not handle relative paths reliably across subprocess contexts.
- **Solution**: Changed to absolute path `/tmp/muqayyim_dev.db` for local development. Production still uses PostgreSQL.
- **Verification**: API starts cleanly, creates/reads database consistently.
- **Code Location**: `api/app/config.py` — DATABASE_URL configuration

---

## Known Issues

### AqarSAS and Paseetah Extractors Require Login Credentials
- **Severity**: Medium
- **Status**: ⚠️ KNOWN (2026-03-20)
- **Description**: These sites require authentication to access property listing details. The extractors handle session management but need initial credentials.
- **Workaround**: Set `AQARSAS_EMAIL` and `AQARSAS_PASSWORD` (or `PASEETAH_EMAIL`/`PASEETAH_PASSWORD`) in `.env` file.
- **Impact**: Without credentials, extraction from these sources will fail gracefully with "authentication required" message.
- **Code Location**: `extractors/html_extractor.py` lines 142-160

### Celery Worker Requires Redis
- **Severity**: Low
- **Status**: ⚠️ KNOWN (2026-03-20)
- **Description**: Async extraction jobs are dispatched to Celery, which requires Redis broker. Without Redis, Celery tasks will fail to queue.
- **Workaround**: For development without Redis, extraction can run synchronously. Set `CELERY_ALWAYS_EAGER=true` in `.env` to run tasks inline.
- **Impact**: Extraction jobs appear to hang if Redis is not running.
- **Code Location**: `api/app/services/extraction_service.py` line 89
- **Docker Compose**: Redis service is included in `docker-compose.yml` — use Docker setup for full async experience.

### PDF Upload Requires Multipart/Form-Data Content-Type
- **Severity**: Low
- **Status**: ⚠️ KNOWN (2026-03-20)
- **Description**: FastAPI file upload endpoint expects `Content-Type: multipart/form-data`. Some API clients may default to different content types.
- **Workaround**: Always use multipart encoding. Example curl command:
  ```bash
  curl -X POST http://localhost:8000/api/v1/cases/{id}/sources/pdf \
    -F "file=@document.pdf" \
    -H "Authorization: Bearer YOUR_JWT_TOKEN"
  ```
- **Impact**: Plain POST with file body will return 422 validation error.
- **Code Location**: `api/app/routers/sources.py` line 74

---

## Pending Issues

### Frontend npm Dependencies Need Installation
- **Severity**: Low
- **Status**: ⏳ PENDING
- **Description**: Frontend requires `npm install` to be run if `node_modules` directory is not present.
- **Workaround**:
  ```bash
  cd frontend
  npm install
  npm run dev
  ```
- **Impact**: Frontend will not start without dependencies installed.
- **Code Location**: `frontend/package.json`
- **Docker**: Handled automatically in `docker-compose.yml` via Dockerfile.frontend

### LLM Fallback Requires Valid ANTHROPIC_API_KEY
- **Severity**: Medium
- **Status**: ⏳ PENDING
- **Description**: When primary extraction methods fail, the system falls back to Claude API for structured extraction. Without a valid API key, LLM fallback will fail silently and return zero-confidence fields.
- **Workaround**: Set `ANTHROPIC_API_KEY` in `.env` file with a valid Anthropic Claude API key.
- **Impact**: Extraction may not recover from ambiguous or malformed source data.
- **Code Location**: `extractors/llm_fallback.py` line 34
- **Note**: This is acceptable for Stage 1; LLM fallback is intentionally limited to avoid hallucination.

---

## Testing & Verification

### Recent Test Run: 2026-03-24
All Stage 1 endpoints verified as functional:

- ✅ API health check: `/api/health` returns `{"status":"ok"}`
- ✅ Case creation: POST `/api/v1/cases` creates case with UUID
- ✅ Case listing: GET `/api/v1/cases` returns paginated list
- ✅ URL source ingestion: POST `/api/v1/cases/{id}/sources/url` accepts valid URLs
- ✅ Extraction triggering: POST `/api/v1/sources/{id}/extract` queues job
- ✅ Job status: GET `/api/v1/extraction-jobs/{id}` returns state
- ✅ Comparable retrieval: GET `/api/v1/cases/{id}/comparables` returns data
- ✅ CSV export: GET `/api/v1/cases/{id}/export/csv` generates file
- ✅ XLSX export: GET `/api/v1/cases/{id}/export/xlsx` generates file
- ✅ OpenAPI docs: `/docs` renders Swagger UI

No regressions detected since Stage 0.

---

## Reporting a Bug

When reporting issues:
1. **Severity**: Critical / High / Medium / Low
2. **Steps to Reproduce**: Exact commands or actions
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**: OS, Python version, Docker vs. local
6. **Logs**: Relevant error messages or stack traces

File issues to the development team or update this log directly.

---

*Last Updated: 2026-03-24*
