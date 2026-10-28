# Data Collection & Monitoring Setup Guide

## Overview

This document provides a quick-start guide to the data collection and monitoring infrastructure that has been set up for the Muqayyim (مقيم) Saudi Real Estate Valuation Platform.

**Setup Date**: March 24, 2026
**Status**: Ready for use (Stage 1 MVP)

---

## What's Been Created

### 1. Directory Structure ✅
```
data/                          # Data storage
├── raw/                       # Raw ingested data
├── clean/                     # Cleaned standardized data
├── monitoring/                # Monitoring outputs
└── exports/                   # Generated reports

scripts/                       # Collection & monitoring scripts
├── collection/                # Data collection
│   └── aqar_collector.py     # Aqar.fm listing extractor
├── monitoring/                # Source monitoring
│   └── monitor_sources.py    # Monitor 10+ Saudi sources
└── requirements.txt           # Python dependencies

docs/                          # Documentation
└── SOURCE_MAP.md             # Complete Saudi source mapping (20+ sources)

prompts/                       # LLM prompts and templates
├── chatgpt_transaction_extraction.md  # ChatGPT prompt for data extraction
└── aqar_data_request_email.md         # Email template for data partnerships
```

### 2. Data Templates ✅

**`data/clean/transactions_scaffold.csv`**
- Headers for transaction data (source, date, price, location, property type, etc.)
- 5 sample rows with realistic Saudi real estate data
- Ready to append new transactions

**`data/clean/listings_scaffold.csv`**
- Headers for property listings (source, listing_id, price, area, bedrooms, location, etc.)
- 5 sample rows (Aqar, Bayut, PropertyFinder, Wafi, Aqarsas)
- Ready for marketplace data import

**`data/clean/source_registry.csv`**
- Registry of 20 Saudi real estate data sources
- Columns: name, URL, type, data types, accessibility, update frequency, status
- Tracks 10 web marketplaces, 3 government registries, 4 research firms, 3+ news sources

### 3. Collection Scripts ✅

**`scripts/collection/aqar_collector.py`** (Fully functional)
- Extract individual Aqar.fm property listings
- Extracts: price, area, location, property type, bedrooms, bathrooms, tenure, description
- Validates URL, respects robots.txt
- Outputs JSON with metadata and confidence scores
- Usage: `python aqar_collector.py "https://aqar.fm/property/ID"`

### 4. Monitoring Scripts ✅

**`scripts/monitoring/monitor_sources.py`** (Fully functional)
- Monitor 10+ Saudi real estate sources for new content
- Classifies relevance (high/medium/low)
- Daily source health monitoring
- Outputs JSON with source status and relevance
- Usage: `python monitor_sources.py` or `python monitor_sources.py --source aqar`

### 5. Comprehensive Documentation ✅

**`docs/SOURCE_MAP.md`** (8,000+ words)
- Complete mapping of 20+ Saudi real estate data sources
- For each source: name, URL, data types, accessibility, extractable fields, limitations
- Sources covered:
  - Web Marketplaces: Aqar.fm, Bayut, PropertyFinder, Wafi, Aqarsas, Paseetah
  - Government: Ejar, Ministry of Housing, SAMA (Central Bank)
  - Stock Exchange: Tadawul
  - Research: CBRE, JLL, Savills, Colliers
  - News: Al Arabiya, Saudi Gazette, Argaam, Arab News
- Data collection strategy by source priority
- Integration roadmap for platform
- Access/contact information for each source

**`scripts/README.md`** (Installation, usage, troubleshooting)
- Complete guide to all collection and monitoring scripts
- Installation instructions
- Usage examples and options
- Cron automation examples
- Performance and scaling considerations
- Troubleshooting guide

**`data/README.md`** (Data directory guide)
- Overview of data subdirectories and their purpose
- Field definitions for each CSV template
- Data quality standards and confidence scoring
- Workflow: collection → cleaning → analysis
- Data privacy and security guidelines

### 6. LLM Prompts & Templates ✅

**`prompts/chatgpt_transaction_extraction.md`**
- Ready-to-use ChatGPT prompt for extracting transaction data from raw text
- JSON output format with all required valuation fields
- Example inputs and expected outputs
- Extraction rules and Saudi real estate context
- Integration notes for platform

**`prompts/aqar_data_request_email.md`**
- Professional bilingual (English + Arabic) email template
- For requesting data access/API partnership from Aqar.fm
- Includes customization checklist
- Alternative approaches if email doesn't work
- Professional qualifications and commercial terms discussion

---

## Quick Start

### 1. Install Dependencies
```bash
cd /path/to/saudi-realestate-platform
pip install -r scripts/requirements.txt
```

### 2. Test Collection Script
```bash
# Extract a single Aqar.fm listing (example URL)
python scripts/collection/aqar_collector.py "https://aqar.fm/property/example" \
  --output data/raw

# Check output
cat data/raw/aqar_*.json
```

### 3. Test Monitoring Script
```bash
# Monitor all Saudi sources
python scripts/monitoring/monitor_sources.py --output data/monitoring

# Monitor specific source
python scripts/monitoring/monitor_sources.py --source aqar

# List available sources
python scripts/monitoring/monitor_sources.py --list
```

### 4. Review Documentation
- Start with `docs/SOURCE_MAP.md` to understand available data sources
- Check `scripts/README.md` for script details and examples
- See `data/README.md` for data organization and standards

---

## Next Steps (Integration with Platform)

### Phase 1: Import Sample Data (Week 1)
1. ✅ Create CSV templates
2. Add sample data from scripts to database models
3. Create import endpoint (POST /api/v1/cases/{id}/sources/url)
4. Test extraction pipeline with sample data

### Phase 2: Automate Daily Monitoring (Week 2)
1. Schedule `monitor_sources.py` via cron (daily 6 AM)
2. Parse monitoring output and create alerts
3. Surface new high-relevance items in dashboard
4. Log monitoring results for audit trail

### Phase 3: Build Collection Workflow (Week 3)
1. Add more collector scripts (Bayut, PropertyFinder, Wafi)
2. Batch collection for multiple URLs
3. Deduplicate listings across sources
4. Implement data quality scoring and validation

### Phase 4: Advanced Analytics (Month 2)
1. Implement market indices calculation
2. Build price trend analysis
3. Create comparable ranking algorithm
4. Generate automated CMA reports

---

## Data Sources: Priority Tiers

### Tier 1 (Start Immediately)
- **Aqar.fm**: Primary marketplace, largest dataset
  - Scripts ready: `aqar_collector.py`
  - Manual: Paste URLs or implement batch scraping

- **Monitoring**: Daily source monitoring
  - Scripts ready: `monitor_sources.py`
  - Automation: Add to cron

- **Market Research**: CBRE/JLL reports
  - Manual: Download and store
  - Potential: Subscribe for feeds

### Tier 2 (Next 2-4 Weeks)
- **Ejar Transactions**: Apply for official access
  - Manual: Email ejar-support@moh.gov.sa
  - Template ready: See SOURCE_MAP.md

- **Bayut & PropertyFinder**: Secondary marketplaces
  - Scripts: In progress (templates available)
  - Data: Similar to Aqar, good for validation

- **News Monitoring**: Al Arabiya, Saudi Gazette
  - Scripts: Basic monitoring active
  - Potential: RSS feed aggregation

### Tier 3 (Month 2+)
- **Tadawul**: Corporate transaction announcements
  - Scripts: In development
  - Data: High reliability for institutional deals

- **SAMA Economic Data**: Interest rates, economic context
  - Manual: Download from website
  - Potential: API integration

- **Smaller Marketplaces**: Wafi, Aqarsas, Paseetah
  - Scripts: Aqar template can adapt
  - Data: Lower volume, validation use

---

## Database Integration Points

### Table: `sources`
```sql
INSERT INTO sources (case_id, source_type, url, file_path, status, created_at)
VALUES (..., 'url', 'https://aqar.fm/property/12345', NULL, 'pending', NOW());
```

### Table: `extraction_jobs`
```sql
INSERT INTO extraction_jobs (source_id, status, extractor_version, started_at)
VALUES (..., 'running', '1.0', NOW());
```

### Table: `extracted_fields`
```sql
INSERT INTO extracted_fields (extraction_job_id, comparable_id, field_name, raw_value, normalized_value, confidence, citation)
VALUES (..., NULL, 'price_sar', '2500000', '2500000', 0.95, '{...citation_json...}');
```

---

## Automation Examples

### Daily Monitoring with Cron
```bash
# Add to crontab
crontab -e

# Insert this line (6 AM daily)
0 6 * * * cd /srv/muqayyim && python scripts/monitoring/monitor_sources.py \
  --output data/monitoring 2>&1 | tee logs/monitor_$(date +\%Y-\%m-\%d).log
```

### Batch Collection
```bash
#!/bin/bash
# Collect multiple Aqar listings
URLS=(
  "https://aqar.fm/property/1"
  "https://aqar.fm/property/2"
  "https://aqar.fm/property/3"
)

for url in "${URLS[@]}"; do
  python scripts/collection/aqar_collector.py "$url" --output data/raw
  sleep 5  # Rate limiting
done
```

---

## File Locations Summary

| File | Purpose | Status | Usage |
|------|---------|--------|-------|
| `scripts/collection/aqar_collector.py` | Aqar listing extraction | ✅ Ready | `python aqar_collector.py <URL>` |
| `scripts/monitoring/monitor_sources.py` | Source monitoring | ✅ Ready | `python monitor_sources.py` |
| `data/clean/transactions_scaffold.csv` | Transaction template | ✅ Ready | Import/append transactions |
| `data/clean/listings_scaffold.csv` | Listing template | ✅ Ready | Import/append listings |
| `data/clean/source_registry.csv` | Source registry | ✅ Ready | Reference during collection |
| `docs/SOURCE_MAP.md` | Comprehensive source guide | ✅ Ready | Planning data strategy |
| `scripts/README.md` | Scripts documentation | ✅ Ready | Script usage and automation |
| `data/README.md` | Data directory guide | ✅ Ready | Understanding data org |
| `prompts/chatgpt_transaction_extraction.md` | LLM extraction prompt | ✅ Ready | Paste into ChatGPT |
| `prompts/aqar_data_request_email.md` | Aqar partnership email | ✅ Ready | Customize and send |
| `scripts/requirements.txt` | Python dependencies | ✅ Ready | `pip install -r` |

---

## Common Tasks

### Add a New Data Source

1. Add row to `data/clean/source_registry.csv`
2. Create collector script in `scripts/collection/[source]_collector.py`
3. Add to `monitor_sources.py` SOURCES list
4. Test with sample URL
5. Document in `docs/SOURCE_MAP.md`

### Import Listings to Database

1. Collect data: `python aqar_collector.py <URL>`
2. Validate JSON: `python -m json.tool data/raw/aqar_*.json`
3. Convert to CSV using provided template
4. Import via API: `POST /api/v1/cases/{id}/sources/url`
5. Trigger extraction: `POST /api/v1/sources/{id}/extract`

### Request Ejar Access

1. Review `docs/SOURCE_MAP.md` section 2.1 (Ejar)
2. Prepare professional credentials (RICS/valuation license)
3. Email: ejar-support@moh.gov.sa
4. Request: API access or authorized user accounts
5. Budget: Premium service with subscription fees

### Export Data for Analysis

1. Query cleaned data from `data/clean/` CSVs
2. Use `scripts/utility/export_data.py` to convert formats
3. Export to: CSV, Excel (XLSX), JSON, or PDF
4. Store in `data/exports/` with timestamp

---

## Support & Troubleshooting

### Script Won't Run
```bash
# Install dependencies
pip install -r scripts/requirements.txt

# Make scripts executable
chmod +x scripts/collection/*.py
chmod +x scripts/monitoring/*.py

# Check Python version (requires 3.8+)
python --version
```

### Scraping Blocked by robots.txt
- Check `docs/SOURCE_MAP.md` for alternative access methods
- Request API access or data partnership
- Use template: `prompts/aqar_data_request_email.md`

### Data Quality Issues
- Review confidence scores (< 0.75 = flag for review)
- Check extraction patterns in script
- Update regex patterns for HTML changes
- Run deduplication script

---

## Key Contacts

| Organization | Email | Purpose |
|---|---|---|
| Aqar.fm | sales@aqar.fm | Data partnership, API access |
| Ejar | ejar-support@moh.gov.sa | Transaction registry access |
| SAMA | sama.gov.sa | Economic data, interest rates |
| CBRE Saudi | saudi-arabia@cbre.com | Market research subscription |
| JLL Saudi | jll.com/en/contact | Market analysis subscription |
| Bayut | hello@bayut.com | API partnership |

---

## Version Information

- **Platform**: Muqayyim (مقيم) v1.0.0
- **Stage**: 1 (Comparable Ingestor MVP)
- **Data Setup**: March 24, 2026
- **Scripts Version**: 1.0.0
- **Python**: 3.8+
- **Dependencies**: See `scripts/requirements.txt`

---

## Next Team Onboarding

When adding team members:

1. Share this document (`DATA_COLLECTION_SETUP.md`)
2. Point to `docs/SOURCE_MAP.md` for data source reference
3. Run through script examples in `scripts/README.md`
4. Review data organization in `data/README.md`
5. Set up local development environment with dependencies

---

**Created**: March 24, 2026
**Maintained By**: Data Engineering Team
**Status**: Active, Ready for Integration
