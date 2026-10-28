# Architecture Overview

## System Diagram

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend (Next.js)                  │
│  Cases → Sources → Extraction Status → Comps Table → Export │
└────────────────────────┬────────────────────────────────┘
                         │ REST API
┌────────────────────────▼────────────────────────────────┐
│                    API (FastAPI)                          │
│  Routers → Services → Models → Database                  │
│  Auth (JWT) │ Audit Logger │ Validation                  │
└──────┬─────────────────────────────────┬────────────────┘
       │ Dispatch                         │ Query
┌──────▼──────────┐              ┌───────▼────────────────┐
│  Worker (Celery) │              │   PostgreSQL + PostGIS  │
│  Extraction Jobs │              │   users, cases, sources │
│  ┌─────────────┐ │              │   extraction_jobs       │
│  │ Extractors  │ │              │   extracted_fields      │
│  │ HTML → PDF  │ │              │   comparables, overrides│
│  │ Normalizer  │ │              │   audit_log             │
│  │ LLM Fallback│ │              └─────────────────────────┘
│  └─────────────┘ │
└──────────────────┘
       │
┌──────▼──────────┐
│   Redis          │
│   Job Queue      │
│   Result Cache   │
└──────────────────┘
```

## Data Flow (Stage 1)

```
User creates Case
  → User pastes URL or uploads PDF
    → Source record created in DB
      → User clicks "Extract"
        → Celery job dispatched
          → Extractor fetches/parses content
            → Deterministic extraction (regex, selectors)
              → Saudi normalization (SAR, sqm, dates, locations)
                → LLM fallback for unresolved fields
                  → Confidence scoring
                    → Citation objects attached
                      → Comparable + ExtractedFields saved to DB
                        → Frontend polls job status
                          → Comps table rendered with citations
                            → User reviews, edits, overrides (all logged)
                              → User exports XLSX/CSV/PDF
```

## Key Design Decisions

1. **Citations are mandatory** — No field exists without provenance
2. **Rules-first extraction** — LLM is fallback, not primary
3. **Human-in-the-loop** — AI suggests, humans approve
4. **Saudi-first** — SAR, sqm, Arabic/English, Hijri dates as defaults
5. **Async extraction** — Celery workers prevent API blocking
6. **Versioned extraction** — Can re-run and compare versions
7. **Module boundaries** — Each folder has a clear responsibility
