# Data Model

## Entity Relationship Summary

```
Organization 1──* User
Organization 1──* Case
User 1──* Case (created_by)
Case 1──* Source
Case 1──* Comparable
Source 1──* ExtractionJob
Source 1──* Comparable
ExtractionJob 1──* ExtractedField
ExtractionJob 1──* Comparable
Comparable 1──* ExtractedField
ExtractedField 1──* Override
User 1──* Override
```

## Core Tables

### organizations
Tenant isolation. Every case belongs to an organization.

### users
Internal users with role-based access. Roles: admin, valuer, analyst, reviewer, viewer.

### cases
A valuation project. Contains sources and comparables. Status tracks workflow progress.

### sources
A comparable data source — either a URL, uploaded PDF, or manual entry.
- `raw_content`: Stored HTML or extracted text for re-processing
- `file_path`: Local/S3 path for uploaded files

### extraction_jobs
Tracks each extraction run. Supports versioning — same source can be re-extracted.
- Links to the extractor name/version used
- Stores error logs for failed jobs

### extracted_fields
The heart of provenance. Every value extracted from a source.
- `field_name`: Canonical name (e.g. "asking_price", "city")
- `raw_value`: Exactly as found in source
- `normalized_value`: Cleaned/converted (stored as text, parsed by application)
- `confidence`: 0.0–1.0 combined score
- `citation`: Full CitationObject as JSONB
- `classification`: fact / assumption / judgment

### comparables
Denormalized view of a comparable property for fast querying and display.
- Key fields are copied from extracted_fields for query performance
- Full provenance lives in the related extracted_fields
- `reliability_score`: 1–5 evidence quality scale

### overrides
Audit trail for every manual edit.
- `old_value` + `new_value` + `reason` (required) + `user_id` + `timestamp`
- Links back to the specific extracted_field

### audit_log
Generic action log for all entity changes.
- `entity_type` + `entity_id` + `action` + `user_id` + `details` (JSONB) + `timestamp`

## Future Tables (Scaffolded)

### subject_properties (Stage 2)
The property being valued. Currently a stub with JSON data column.

### adjustments (Stage 3)
Individual adjustments applied to comparables. Has `approved` flag for workflow.

### valuation_runs (Stage 3)
A complete valuation calculation aggregating all adjustments.

### report_artifacts (Stage 5)
Generated report files with metadata.

### market_reference_data
Reference data for indices, benchmarks, rates used in adjustments.

## Citation Object (JSONB)

Stored in `extracted_fields.citation`. Structure:

| Field | Type | Description |
|-------|------|-------------|
| source_id | UUID | FK to source |
| source_type | string | url, pdf, manual |
| source_url_or_name | string | Original URL or filename |
| retrieval_timestamp | datetime | When fetched (UTC) |
| locator | string? | CSS selector / page:line / bbox |
| snippet | string? | Raw excerpt ≤500 chars |
| extractor_name | string | Which extractor produced this |
| extractor_version | string | Semver |
| parse_confidence | float | 0.0–1.0 deterministic confidence |
| llm_confidence | float? | 0.0–1.0 if LLM was used |
| crosscheck_confidence | float? | 0.0–1.0 cross-field validation |
| normalization_notes | string? | How value was normalized |
