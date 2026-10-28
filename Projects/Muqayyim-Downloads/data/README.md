# Data Directory — Muqayyim Valuation Platform

## Overview

This directory contains all data assets for the Muqayyim (مقيم) Saudi Real Estate Valuation Platform, including:
- **Raw data**: Ingested from external sources (PDFs, web scrapes, APIs)
- **Clean data**: Processed and standardized data ready for analysis
- **Monitoring data**: New items detected by source monitoring scripts
- **Exports**: Generated reports and analysis outputs

---

## Directory Structure

```
data/
├── raw/                    # Raw ingested data (original form)
│   ├── aqar_*.json         # Aqar.fm scraped listings (raw)
│   ├── ejar_*.json         # Ejar transaction data (if access obtained)
│   ├── source_*.json       # PDF/document extractions
│   └── (other raw sources)
│
├── clean/                  # Cleaned and standardized data
│   ├── transactions_scaffold.csv    # Transaction template (sample rows)
│   ├── listings_scaffold.csv        # Listings template (sample rows)
│   ├── source_registry.csv          # Registry of all data sources
│   ├── transactions_clean.csv       # Production transaction data
│   ├── listings_clean.csv           # Production listing data
│   ├── comparable_analysis.csv      # Processed comparable properties
│   └── price_indices.csv            # Calculated market indices
│
├── monitoring/             # Monitoring outputs and alerts
│   ├── monitor_run_*.json           # Daily monitoring results
│   ├── new_items_*.json             # New high-relevance items found
│   ├── alerts_*.json                # Significant market movements
│   └── source_status.json           # Last status of each monitored source
│
└── exports/                # Generated reports and outputs
    ├── valuation_reports/          # Completed valuation reports (PDF)
    ├── comparable_analysis/        # CMA exports
    ├── market_analysis/            # Market analysis reports
    └── data_dumps/                 # Periodic data backups
```

---

## Data Files Reference

### Clean Data Templates

#### `transactions_scaffold.csv`
Template for transaction data with headers:
- `source`: Data source (Ejar, Tadawul, Gazette, etc.)
- `date`: Transaction date (YYYY-MM-DD)
- `property_name`: Property identifier/name
- `location`: Full location description
- `city`, `district`: Administrative divisions
- `property_type`: Villa, apartment, commercial, land, etc.
- `deal_type`: Actual Sale, Lease, Acquisition, etc.
- `sale_or_rent`: Sale or Rent
- `announced_value_sar`: Transaction/asking price in SAR
- `area_sqm`: Property area in square meters
- `price_per_sqm`: Calculated price per sqm
- `parties_involved`: Description of buyer/seller/broker
- `listing_status`: Completed, Active, etc.
- `raw_text`: Source text excerpt
- `source_url`: Link to source
- `confidence_score`: 0.0-1.0 extraction confidence
- `notes`: Additional notes
- `usability`: High, Medium, Low
- `reliability_score`: 1-5 (1=user-generated, 5=government verified)
- `extracted_at`: ISO 8601 timestamp

**Usage**:
- Append transaction rows to this file as transactions are collected
- Use as template for manual data entry
- Import into database during processing

#### `listings_scaffold.csv`
Template for property listings with headers:
- `source`: Source platform (Aqar, Bayut, PropertyFinder, etc.)
- `listing_id`: Unique listing ID from source
- `date_listed`: When listing was posted
- `date_scraped`: When data was extracted
- `property_name`: Listing title
- `city`, `district`, `subdistrict`: Location hierarchy
- `property_type`: Villa, apartment, etc.
- `bedrooms`, `bathrooms`: Unit specifications
- `area_sqm`: Property size in square meters
- `asking_price_sar`: Listed price in SAR
- `price_per_sqm`: Calculated price per sqm
- `tenure`: Freehold, leasehold, usufruct
- `listing_url`: Direct link to original listing
- `description_ar`: Arabic description
- `description_en`: English description
- `images_count`: Number of images in listing
- `latitude`, `longitude`: Geographic coordinates
- `confidence_score`: 0.0-1.0 data quality confidence
- `status`: Active, Expired, Sold, etc.
- `notes`: Data quality notes
- `raw_text`: Raw text from extraction
- `extracted_at`: Extraction timestamp

**Usage**:
- Use for marketplace listing comparables
- One row per listing
- Update status over time as listings expire/sell

#### `source_registry.csv`
Master registry of all data sources with columns:
- `source_name`: Human-readable name (Aqar.fm, Ejar, etc.)
- `source_url`: Primary URL
- `source_type`: Web Marketplace, Government Registry, News Media, Research, etc.
- `data_types`: Comma-separated data types available
- `accessibility`: Public, Semi-public, Manual, Restricted
- `update_frequency`: Real-time, Daily, Weekly, Monthly, etc.
- `saudi_specific`: Yes/No
- `notes`: Use case notes, API info, contact details
- `status`: Active, Monitoring, Pending Access, Inactive
- `last_checked`: Date source was last verified

**Usage**:
- Reference before collection activities
- Update status and last_checked regularly
- Use to plan collection priorities and schedules

---

## Data Quality Standards

### Confidence Scoring (0.0 - 1.0)

- **0.9-1.0**: High confidence — authenticated source, complete data
- **0.75-0.89**: Good confidence — professional listing, most fields present
- **0.60-0.74**: Medium confidence — marketplace listing with some uncertainty
- **0.40-0.59**: Lower confidence — user-generated or incomplete data
- **<0.40**: Low confidence — uncertain extraction, significant assumptions

### Reliability Scoring (1-5)

| Score | Type | Examples |
|-------|------|----------|
| 5 | Authenticated government/official | Ejar transactions, SAMA data, official disclosures |
| 4 | Professional corporate disclosure | Tadawul announcements, CBRE/JLL reports, broker listings |
| 3 | Professional marketplace | Aqar.fm agent-listed, Bayut verified |
| 2 | User marketplace/news | Aqar owner listings, marketplace user entries, news articles |
| 1 | Unverified/hearsay | Social media, single news report, informal sources |

### Data Completeness

Track what percentage of expected fields are populated for each record.

---

## Workflow: Data Collection → Clean → Analysis

### Stage 1: Raw Collection
1. Scripts collect raw data from sources (Aqar, news feeds, web pages)
2. Raw data saved to `raw/` with timestamp and source metadata
3. File format: JSON with structure matching source schema

### Stage 2: Cleaning & Standardization
1. Raw data imported and validated
2. Fields mapped to standard schema (transactions_scaffold.csv, listings_scaffold.csv)
3. Location names normalized (city/district/subdistrict standardized)
4. Prices converted to SAR; areas converted to sqm
5. Dates converted to ISO 8601 format
6. Confidence scores assigned
7. Cleaned data exported to `clean/`

### Stage 3: Monitoring & Alerts
1. Daily monitoring scripts run (monitor_sources.py)
2. New high-relevance items flagged
3. Source status tracked and reported
4. Significant market changes trigger alerts

### Stage 4: Analysis & Export
1. Cleaned data analyzed for valuation research
2. Comparable properties identified and ranked
3. Market indices calculated
4. Reports generated and exported to `exports/`

---

## Scripts Integration

### Data Collection Scripts
Located in `/scripts/collection/`

**aqar_collector.py**: Extract individual Aqar.fm listings
```bash
python scripts/collection/aqar_collector.py "https://aqar.fm/property/12345" --output data/raw
```

### Data Monitoring Scripts
Located in `/scripts/monitoring/`

**monitor_sources.py**: Monitor all configured sources daily
```bash
python scripts/monitoring/monitor_sources.py --output data/monitoring
```

---

## Environment Setup

### Directory Permissions
```bash
# Ensure data directory is writable by application and scripts
chmod 755 data/
chmod 755 data/raw data/clean data/monitoring data/exports
```

### Backup Strategy
- **Raw data**: Keep indefinitely (source of truth)
- **Clean data**: Keep production versions; archive old versions
- **Monitoring data**: Keep rolling 90 days
- **Exports**: Keep per valuation case per client retention policy

### Size Estimates
- **Raw data**: Grows ~10-50 MB/month depending on scraping volume
- **Clean data**: ~1-5 MB for 1,000 listings + transactions
- **Monitoring data**: ~5-10 MB/month
- **Total**: Plan for 100-200 GB storage over 5 years

---

## Data Privacy & Security

### Sensitive Data Handling
- **Anonymized transaction parties**: Do not store names of individual transactors
- **Personal information**: Limit PII; store only as aggregate/anonymized
- **Confidential sources**: Mark and restrict access as needed

### Access Control
- Database credentials: `.env` file (never in `data/`)
- Raw data: Accessible to data import/collection processes only
- Exports: Controlled by case/valuation ownership

### Retention Policy
- **Listings**: Keep 2 years (longer if used in active valuations)
- **Transactions**: Keep per regulatory/audit requirements (5-7 years minimum)
- **Raw data**: Keep 1 year backup after cleaning
- **Monitoring**: Archive after 90 days to cold storage

---

## Common Data Tasks

### Adding a New Listing Source

1. Create entry in `data/clean/source_registry.csv`
2. Create collection script in `scripts/collection/` (reference aqar_collector.py)
3. Add source to `monitor_sources.py` SOURCES list
4. Test collection and monitoring
5. Document in `docs/SOURCE_MAP.md`

### Importing Transaction Data

1. Validate data against `transactions_scaffold.csv` schema
2. Assign confidence and reliability scores
3. Add source citations and extraction metadata
4. Import to database with `api/app/services/import_service.py`
5. Flag for human review if confidence < 0.75

### Generating Export

1. Query cleaned data from database
2. Apply business logic filters (reliability > threshold, location filters, date ranges)
3. Format per export requirements (XLSX, CSV, PDF)
4. Save to `exports/` with timestamp and metadata
5. Generate audit trail entry

---

## Tools & Libraries

### For Data Collection
- `requests`: HTTP requests to websites
- `beautifulsoup4`: HTML/XML parsing
- `pdfplumber`: PDF text/table extraction
- `json`: JSON handling
- `csv`: CSV file handling

### For Data Processing
- `pandas`: DataFrame manipulation
- `sqlalchemy`: Database ORM
- `pydantic`: Data validation

### For Monitoring
- `feedparser`: RSS/Atom feed parsing
- `schedule`: Task scheduling
- `logging`: Application logging

---

## Troubleshooting

### Scraping Issues
- **robots.txt blocked**: Check source_registry.csv status; request data partnership instead
- **Parsing failures**: Update extraction patterns; check raw HTML for structure changes
- **Timeout errors**: Increase script timeout; use exponential backoff retry logic

### Data Quality Issues
- **Missing values**: Mark as `null`; do not invent or estimate values
- **Inconsistent units**: Standardize during cleaning phase (SAR, sqm, dates)
- **Duplicate records**: Deduplicate by source + listing_id + date

### Monitoring Alerts
- **No data collected**: Check network connectivity; verify source accessibility
- **High error rate**: Review error logs; contact source support if needed
- **Alert fatigue**: Adjust keyword thresholds in monitor_sources.py

---

## Version Control

- Raw data: Not version controlled (too large); keep local backup
- Scripts: Version controlled in git (`scripts/` directory)
- Schemas/templates: Version controlled in git (`data/clean/` templates)
- Exports: Archive per case; do not store in git

---

## Contact & Support

For data-related questions:
- **Data collection issues**: Review scripts/collection/ documentation
- **Source mapping**: See docs/SOURCE_MAP.md
- **API integration**: Contact source providers (emails in source_registry.csv)
- **Database schema**: See docs/DATA_MODEL.md

---

**Last Updated**: March 24, 2026
**Maintained By**: Data Engineering Team
