# API Reference — Stage 1

Base URL: `http://localhost:8000`
Interactive docs: `http://localhost:8000/docs`

## Health

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/health | Health check |

## Cases

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/cases | Create a new valuation case |
| GET | /api/v1/cases | List all cases |
| GET | /api/v1/cases/{id} | Get case details |

## Sources

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/cases/{id}/sources/url | Add a URL source |
| POST | /api/v1/cases/{id}/sources/pdf | Upload a PDF source |
| GET | /api/v1/cases/{id}/sources | List sources for a case |

## Extractions

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/sources/{id}/extract | Start extraction job |
| GET | /api/v1/extraction-jobs/{id} | Get job status |

## Comparables

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/cases/{id}/comparables | List comparables with extracted fields |
| PATCH | /api/v1/comparables/{id}/fields/{field_id} | Override a field value |
| PATCH | /api/v1/comparables/{id}/status | Mark as active/invalid/outlier |

## Exports

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/cases/{id}/export/csv | Download CSV |
| GET | /api/v1/cases/{id}/export/xlsx | Download XLSX |
| GET | /api/v1/cases/{id}/export/pdf | Download PDF summary |

## Authentication

In development mode, all endpoints use a default dev user. No auth header required.

For production, include: `Authorization: Bearer <jwt_token>`
