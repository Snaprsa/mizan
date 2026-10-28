# Scripts — Data Collection & Monitoring for Muqayyim Platform

## Overview

This directory contains command-line scripts for:
- **Data collection**: Ingesting data from Saudi real estate sources
- **Source monitoring**: Tracking new listings and market changes
- **Data processing**: Cleaning and standardizing raw data
- **Reporting**: Generating analysis outputs

All scripts are designed to:
- Run standalone (no complex dependencies)
- Support cron scheduling for automation
- Provide clear logging and error handling
- Output machine-readable formats (JSON, CSV)

---

## Directory Structure

```
scripts/
├── README.md                    # This file
├── monitoring/                  # Source monitoring scripts
│   ├── monitor_sources.py      # Monitor all Saudi real estate sources
│   ├── market_alerts.py        # Detect significant price/activity changes
│   └── rss_aggregator.py       # Aggregate RSS feeds (future)
│
├── collection/                  # Data collection scripts
│   ├── aqar_collector.py       # Extract Aqar.fm listings
│   ├── bayut_collector.py      # Extract Bayut listings (future)
│   ├── ejar_sync.py            # Sync Ejar transactions (future - requires access)
│   └── news_scraper.py         # Scrape real estate news (future)
│
├── processing/                  # Data cleaning and processing
│   ├── normalize_locations.py   # Standardize Saudi location names
│   ├── clean_prices.py          # Normalize prices and calculate metrics
│   └── deduplicate.py           # Remove duplicate records
│
├── utility/                      # Utility scripts
│   ├── source_health_check.py   # Check source availability
│   ├── export_data.py           # Export data to CSV/XLSX/JSON
│   └── generate_report.py       # Generate analysis reports
│
└── requirements.txt             # Python dependencies
```

---

## Installation

### Prerequisites
- Python 3.8+
- pip or conda

### Setup

```bash
# Clone the repository (if not already done)
git clone <repo_url>
cd saudi-realestate-platform

# Install dependencies
pip install -r scripts/requirements.txt

# Make scripts executable
chmod +x scripts/collection/*.py
chmod +x scripts/monitoring/*.py
```

### Python Dependencies

Core requirements (minimal, standard library focused):
```
requests>=2.28.0        # HTTP requests
beautifulsoup4>=4.11.0  # HTML/XML parsing
pdfplumber>=0.9.0       # PDF extraction (optional)
schedule>=1.1.0         # Task scheduling (optional)
```

Optional for full feature set:
```
pandas>=1.3.0           # Data processing
sqlalchemy>=1.4.0       # Database ORM
openpyxl>=3.8.0         # Excel export
```

Install with:
```bash
pip install -r scripts/requirements.txt
```

---

## Collection Scripts

### `collection/aqar_collector.py`

Extract property listing data from Aqar.fm.

**Usage**:
```bash
# Basic usage
python scripts/collection/aqar_collector.py "https://aqar.fm/property/12345678"

# Custom output directory
python scripts/collection/aqar_collector.py "https://aqar.fm/property/12345678" \
  --output ./data/raw

# Verbose logging
python scripts/collection/aqar_collector.py "https://aqar.fm/property/12345678" \
  --verbose

# Show help
python scripts/collection/aqar_collector.py --help
```

**What it does**:
1. Validates URL (ensures it's from aqar.fm)
2. Checks robots.txt for scraping permission
3. Fetches page content
4. Extracts: price, area, location, property type, bedrooms, bathrooms, tenure, description
5. Saves extracted data as JSON with metadata

**Output**:
```json
{
  "metadata": {
    "source": "aqar.fm",
    "url": "https://aqar.fm/property/...",
    "extracted_at": "2026-03-24T14:30:00Z",
    "extraction_version": "1.0"
  },
  "data": {
    "price_sar": 2500000,
    "area_sqm": 800,
    "price_per_sqm": 3125,
    "city": "Riyadh",
    "district": "Al-Noor",
    "property_type": "villa",
    "bedrooms": 5,
    ...
  }
}
```

**Error Handling**:
- Invalid URL → Exit with error
- robots.txt blocks → Log warning, exit
- Network timeout → Log error, exit
- Parsing failure → Continue with available fields
- File write error → Log error, exit with non-zero status

**Limitations**:
- Single URL at a time (for batch, see monitoring scripts)
- Depends on page HTML structure (may break if Aqar redesigns)
- No JavaScript execution (static content only)
- Rate limiting: Respects site rate limits (10-15 second delays)

---

### `collection/bayut_collector.py` (Future)

Extract from Bayut Saudi marketplace (template available, not yet implemented).

---

## Monitoring Scripts

### `monitoring/monitor_sources.py`

Monitor multiple Saudi real estate sources for new content and market changes.

**Usage**:
```bash
# Monitor all sources
python scripts/monitoring/monitor_sources.py

# Monitor specific source
python scripts/monitoring/monitor_sources.py --source aqar

# Custom output directory
python scripts/monitoring/monitor_sources.py --output ./custom/path

# List available sources
python scripts/monitoring/monitor_sources.py --list

# Show help
python scripts/monitoring/monitor_sources.py --help
```

**What it does**:
1. Loads registry of sources to monitor (10+ Saudi real estate sources)
2. Checks each source for new content
3. Fetches page content and analyzes for relevance
4. Classifies as: high, medium, or low relevance
5. Saves results to JSON with source status

**Output**:
```json
{
  "timestamp": "2026-03-24T14:30:00Z",
  "date": "2026-03-24",
  "sources_monitored": 10,
  "items_found": 10,
  "high_relevance": 3,
  "medium_relevance": 4,
  "low_relevance": 3,
  "errors": 0,
  "sources": [
    {
      "name": "Aqar.fm",
      "url": "https://aqar.fm",
      "status": "success",
      "relevance": "high",
      "metadata": {
        "length_chars": 250000,
        "contains_sar": true,
        "contains_sqm": true,
        "language": "mixed"
      }
    },
    ...
  ]
}
```

**Relevance Keywords**:
- **High**: عقار, بيع, صفقة, قيمة, تثمين, transaction, valuation, sale, SAR, million
- **Medium**: سوق, عقاري, استثمار, market, price, location, investment
- **Low**: Everything else

**Available Sources**:
- Aqar.fm
- Tadawul (stock exchange)
- Al Arabiya Property
- Saudi Gazette
- Bayut Saudi
- Property Finder
- Wafi
- Aqarsas
- Paseetah
- Argaam

**Error Handling**:
- Source timeout → Marked as "fetch_failed"
- robots.txt blocks → Marked as "blocked"
- Invalid JSON → Logged as error, continues with next source
- All errors logged but script completes with summary

**Automation with Cron**:
```bash
# Add to crontab for daily monitoring at 6 AM
0 6 * * * cd /path/to/platform && python scripts/monitoring/monitor_sources.py

# Hourly monitoring
0 * * * * cd /path/to/platform && python scripts/monitoring/monitor_sources.py
```

---

## Processing Scripts

### `processing/normalize_locations.py` (Recommended)

Standardize Saudi Arabia location names and administrative divisions.

```bash
python scripts/processing/normalize_locations.py --input data/clean/listings_clean.csv \
  --output data/clean/listings_normalized.csv
```

**What it does**:
- Maps common location aliases to official names
- Validates Saudi cities (Riyadh, Jeddah, Dammam, etc.)
- Standardizes district spellings
- Adds missing subdistrict data where possible
- Preserves original values in "location_raw" field

---

### `processing/clean_prices.py` (Recommended)

Normalize prices and calculate derived metrics.

```bash
python scripts/processing/clean_prices.py --input data/raw/aqar_*.json \
  --output data/clean/listings_clean.csv
```

**What it does**:
- Converts all prices to SAR
- Validates price ranges (reject outliers)
- Calculates price_per_sqm
- Flags suspicious prices for review
- Adds currency and conversion notes

---

## Utility Scripts

### `utility/source_health_check.py`

Test connectivity and availability of all monitored sources.

```bash
python scripts/utility/source_health_check.py

# Output:
# Aqar.fm                    ✓ Accessible (200)
# Tadawul                    ✓ Accessible (200)
# Al Arabiya Property        ✓ Accessible (200)
# Saudi Gazette              ✓ Accessible (200)
# (etc.)
```

---

### `utility/export_data.py`

Export cleaned data to various formats.

```bash
# Export to CSV
python scripts/utility/export_data.py data/clean/listings_clean.csv \
  --format csv --output exports/listings.csv

# Export to Excel
python scripts/utility/export_data.py data/clean/listings_clean.csv \
  --format xlsx --output exports/listings.xlsx

# Export to JSON
python scripts/utility/export_data.py data/clean/listings_clean.csv \
  --format json --output exports/listings.json
```

---

## Automation with Cron

### Example Cron Jobs

```bash
# Daily monitoring at 6 AM
0 6 * * * cd /srv/muqayyim && python scripts/monitoring/monitor_sources.py

# Hourly Aqar monitoring (sample top listings)
0 * * * * cd /srv/muqayyim && python scripts/monitoring/monitor_sources.py --source aqar

# Weekly health check (Sunday 8 AM)
0 8 * * 0 cd /srv/muqayyim && python scripts/utility/source_health_check.py

# Monthly data export (1st of month, 9 AM)
0 9 1 * * cd /srv/muqayyim && python scripts/utility/export_data.py \
  data/clean/listings_clean.csv --format xlsx --output exports/monthly_export.xlsx
```

### Setup Cron (Ubuntu/Linux)

```bash
# Edit crontab
crontab -e

# Add jobs to crontab, save and exit
# View installed cron jobs
crontab -l
```

---

## Logging

All scripts produce detailed logs to console and files.

**Log Locations**:
```
logs/
├── monitor_sources_2026-03-24.log
├── aqar_collector_2026-03-24.log
└── errors_2026-03-24.log
```

**Log Levels**:
- **DEBUG**: Detailed diagnostic information (--verbose flag)
- **INFO**: General information, script progress
- **WARNING**: Potential issues (robots.txt blocked, timeouts)
- **ERROR**: Errors that prevent completion (missing field, file write failure)

**View Recent Logs**:
```bash
tail -f logs/monitor_sources_*.log
```

---

## Testing

### Unit Tests

```bash
cd scripts/
python -m pytest tests/ -v
```

### Manual Testing

```bash
# Test Aqar collector with known listing
python scripts/collection/aqar_collector.py \
  "https://aqar.fm/property/123456" \
  --verbose

# Test monitoring with verbose output
python scripts/monitoring/monitor_sources.py \
  --source aqar \
  --output ./test_output
```

### Validation

```bash
# Check output JSON is valid
python -m json.tool data/raw/aqar_*.json > /dev/null && echo "Valid JSON"

# Check CSV format
python scripts/utility/validate_csv.py data/clean/*.csv
```

---

## Troubleshooting

### Script Won't Run

```bash
# Issue: ModuleNotFoundError: No module named 'requests'
# Solution: Install dependencies
pip install -r scripts/requirements.txt

# Issue: Permission denied
# Solution: Make scripts executable
chmod +x scripts/collection/*.py
chmod +x scripts/monitoring/*.py
```

### Scraping Failures

```bash
# Issue: robots.txt blocks access
# Solution: Check SOURCE_MAP.md for alternative access methods
# Or request data partnership from source

# Issue: Network timeout
# Solution: Increase timeout in script config
# Or run during off-peak hours (weekends, late night)
```

### Data Quality Issues

```bash
# Issue: Missing or null values
# Root cause: Extraction patterns don't match updated HTML
# Solution: Review source HTML; update regex patterns in script

# Issue: Duplicate records
# Solution: Run deduplicate.py script
python scripts/processing/deduplicate.py \
  --input data/clean/listings_clean.csv \
  --output data/clean/listings_deduplicated.csv
```

---

## Contributing New Scripts

### Template for New Collection Script

```python
#!/usr/bin/env python3
"""
Collect property data from [SOURCE_NAME].

Usage:
    python [source]_collector.py <URL>
    python [source]_collector.py <URL> --output ./data/raw
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class [SourceName]Collector:
    """Collect property data from [source]."""

    def __init__(self, url: str):
        self.url = url
        self.extracted_data = {}

    def validate_url(self) -> bool:
        """Validate URL."""
        return True

    def fetch_content(self) -> bool:
        """Fetch page content."""
        return True

    def extract(self) -> bool:
        """Extract property data."""
        return True

    def save(self, output_dir: str = "./data/raw") -> Optional[str]:
        """Save extracted data."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        filename = f"[source]_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = output_path / filename

        output_data = {
            "metadata": {
                "source": "[source_name]",
                "url": self.url,
                "extracted_at": datetime.utcnow().isoformat(),
            },
            "data": self.extracted_data,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        return str(filepath)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="URL to collect")
    parser.add_argument("--output", default="./data/raw", help="Output directory")
    args = parser.parse_args()

    collector = [SourceName]Collector(args.url)
    if collector.extract():
        collector.save(args.output)
        return 0
    return 1

if __name__ == "__main__":
    sys.exit(main())
```

---

## Performance & Scaling

### Single-Thread Performance
- Aqar single listing: ~2-3 seconds
- Monitor all sources: ~30-60 seconds
- Export 1,000 listings: ~5-10 seconds

### Scaling Considerations
For processing large volumes:
1. Use `--parallel` flag (when implemented)
2. Batch URLs into chunks
3. Distribute across multiple workers
4. Use message queue for async processing (future)

### Resource Usage
- Memory: ~100-200 MB per script
- CPU: Light (mostly I/O bound)
- Network: Respects rate limiting (5-10 requests/min per source)

---

## Version Control

All scripts are version controlled in git:
```bash
git add scripts/
git commit -m "Add/update collection scripts"
git push
```

Data files (`data/raw/`, `data/clean/`) are NOT version controlled (store separately).

---

## Documentation

- **Full source mapping**: See `docs/SOURCE_MAP.md`
- **Data model**: See `docs/DATA_MODEL.md`
- **Architecture**: See `docs/ARCHITECTURE.md`

---

## Support & Contact

For script-related issues:
- **Data collection**: Check `docs/SOURCE_MAP.md` for source accessibility
- **Script errors**: Review logs in `logs/` directory
- **Feature requests**: Create issue in repository

---

**Last Updated**: March 24, 2026
**Maintained By**: Data Engineering Team
