# Qaim Architecture

## System Overview

Qaim is a monorepo platform for Saudi real estate valuation workflows.

### Stage 1 Flow (Current)
```
User → Create Case → Add Sources (URL/PDF) → Extract → Review Comps → Override → Export
```

### Data Flow
```
Source (URL/PDF) → Fetch/Store → Extractor Pipeline → Extracted Fields + Citations → Comparable Record → Review UI → Export
```

### Key Design Decisions

1. **Citation-first**: Every populated field carries a CitationObject with source, locator, snippet, extractor info, and confidence scores.

2. **Rules-first extraction**: Deterministic regex patterns run before any LLM. LLM is a fallback for ambiguous fields only.

3. **Saudi defaults**: SAR currency, sqm area, Arabic+English location patterns, Hijri/Gregorian date support ready.

4. **Audit logging**: All manual field overrides logged to `field_overrides` table with who/when/why.

5. **Inline extraction for MVP**: Extraction runs synchronously in the API route. The worker module is structured for Celery dispatch in production.

6. **Provider interface**: Stage 4 comparable discovery uses a plugin pattern. Each provider implements `BaseProvider` (search, get_listing, reliability_score).

### Database Schema Summary

| Table | Stage | Purpose |
|-------|-------|---------|
| users, organizations | 0 | Auth, tenant isolation |
| cases | 1 | Valuation projects |
| sources | 1 | URL/PDF inputs |
| extraction_jobs | 1 | Job tracking |
| comparables | 1 | Structured comp records |
| extracted_fields | 1 | Per-field provenance |
| field_overrides | 1 | Audit log |
| report_artifacts | 1 | Generated exports |
| subject_properties | 2 | Subject profiles |
| adjustments | 3 | Valuation adjustments |
| valuation_runs | 5 | Concluded values |
| market_reference_data | 3+ | Market indices |

### Reliability Scale
| Score | Meaning |
|-------|---------|
| 1 | User-entered manual data |
| 2 | Marketplace listing (Aqar, etc.) |
| 3 | Broker brochure / PDF |
| 4 | Official filing / regulatory disclosure |
| 5 | Authenticated transaction / contract |
