# Stages Roadmap

## Stage 0: Foundations ✅ (Built)
- Monorepo structure
- Shared schemas with enums, CitationObject, ExtractedField, Comparable
- SQLAlchemy ORM models for all core + future tables
- Alembic migrations
- Docker Compose dev environment
- JWT auth (dev mode)
- Audit logging
- RBAC stubs

## Stage 1: Comparable Link Ingestor ✅ (Built)
- Case CRUD
- URL source ingestion
- PDF source upload
- Celery extraction pipeline (HTML + PDF extractors)
- Deterministic extraction with citation objects
- LLM fallback extractor stub
- Saudi normalization (SAR, sqm, dates, locations)
- Confidence scoring
- Editable comps table with citation viewer
- Override flow with required reason + audit log
- Mark comp as invalid/outlier
- CSV/XLSX/PDF export

### What Needs Improvement in Stage 1
1. **HTML extractor**: Currently minimal — needs field-specific regex patterns for Aqar, Pasteah, etc.
2. **PDF extractor**: Currently extracts raw text — needs table parsing and field extraction
3. **LLM fallback**: Stub exists but not wired into the pipeline yet
4. **Normalizer**: Needs full Arabic↔English transliteration, Hijri date parsing
5. **Tests**: Need more coverage — especially extraction pipeline tests

## Stage 2: Subject Property Profile

### What to Build
- SubjectProperty full schema (expand from stub)
- Subject creation UI at `/subject`
- Subject document upload (title deeds, surveys, plans)
- Structured extraction from subject docs
- Subject info API endpoints
- Link subject to case

### Entry Points (Already Scaffolded)
- `schemas/_future.py` → `SubjectProperty` Pydantic model
- `api/app/models/__init__.py` → `SubjectProperty` ORM model (stub with JSON data column)
- Frontend route placeholder needed at `/cases/[id]/subject`

### Key Design Decisions
- Subject needs all KSA-specific fields: Deed number, plot number, plan number, municipality
- Must support multiple area measurements with citations
- Coordinates should be verifiable against deed/plan

## Stage 3: Adjustment Engine

### What to Build
- Full `Adjustment` schema with types: time, location, size, condition, tenure, other
- Rules engine with configurable adjustment rules
- Time adjustment: support index-based and manual percentage
- Location adjustment: district premium/discount tables
- Size adjustment: per-sqm rate curves
- Approval workflow: propose → review → approve/reject
- Pattern learning from historical reports (future phase)
- Valuation run: aggregate adjusted values → indicated value

### Entry Points (Already Scaffolded)
- `schemas/_future.py` → `Adjustment`, `ValuationRun` models
- `valuation_engine/base.py` → `AdjustmentEngine` ABC, `RulesEngine` stub, `ApprovalWorkflow` stub
- `api/app/models/__init__.py` → `Adjustment`, `ValuationRun` ORM stubs

### Key Design Decisions
- Every adjustment must be classified as FACT/ASSUMPTION/JUDGMENT
- Multiple adjustment methods may exist — user picks or system proposes
- Never auto-apply — always human-approved
- Support both percentage and absolute adjustments
- Keep full audit trail of proposals, rejections, approvals

## Stage 4: Comparable Discovery

### What to Build
- Provider plugin system (interface already exists)
- AqarProvider: API integration or structured user-assisted flow
- PasteahProvider: Same approach
- AqarsasProvider: Same approach
- InternalProvider: Search past cases/comps in our database
- Candidate ranking: relevance scoring based on subject similarity
- User selection UI: review candidates, select, import as sources

### Entry Points (Already Scaffolded)
- `providers/base.py` → `BaseProvider` ABC + all provider stubs
- `schemas/_future.py` → `ProviderSearchCriteria`, `CandidateComparable`

### Compliance Rules
- No scraping that violates Terms of Service
- Prefer official APIs where available
- User-assisted ingestion as fallback (user pastes URL, system extracts)
- Internal data sources always acceptable
- Document which providers have API access vs user-assisted

## Stage 5: Valuation Report Generator

### What to Build
- Report template system (Word/PDF templates with placeholders)
- Template engine: populate from case + subject + comps + adjustments + valuation run
- Narrative generation from approved data only (no hallucinations)
- Support for TAQEEM/RICS standard report structures
- PDF and DOCX output
- Report artifact storage and versioning

### Entry Points (Already Scaffolded)
- `schemas/_future.py` → `ReportTemplate`, `ReportArtifact`
- `reporting/report_generator.py` → Stub file
- `reporting/templates/` → Template directory
- `api/app/models/__init__.py` → `ReportArtifact` ORM stub

### Key Design Decisions
- Templates define structure, system fills in approved data
- Narrative must be generated from logged facts/assumptions/judgments only
- Every statement in the report must be traceable
- Support Arabic and English report output
- Version reports — track which data version was used
