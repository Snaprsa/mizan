# Data Collection & Monitoring Infrastructure Index

**Project**: Muqayyim (مقيم) — Saudi Real Estate Valuation Platform  
**Date**: March 24, 2026  
**Status**: ✅ Complete and Ready for Integration

---

## Quick Navigation

### For New Team Members
**Start here**: [`DATA_COLLECTION_SETUP.md`](DATA_COLLECTION_SETUP.md)
- Overview of what was created
- Quick-start examples
- Next integration steps
- File location reference

### For Using the Scripts
**See**: [`scripts/README.md`](scripts/README.md)
- Installation instructions
- Usage examples for each script
- Cron automation setup
- Troubleshooting guide

### For Understanding Data Sources
**See**: [`docs/SOURCE_MAP.md`](docs/SOURCE_MAP.md)
- Complete mapping of 20+ Saudi sources
- For each source: URL, data types, accessibility, contacts
- Data collection strategy by priority tier
- Integration roadmap

### For Data Organization
**See**: [`data/README.md`](data/README.md)
- Directory structure explanation
- CSV template field definitions
- Data quality standards
- Workflow: collection → cleaning → analysis

---

## What's Available Now

### Runnable Scripts

#### Data Collection
- **`scripts/collection/aqar_collector.py`** — Extract Aqar.fm listings
  ```bash
  python scripts/collection/aqar_collector.py "https://aqar.fm/property/ID"
  ```

#### Monitoring
- **`scripts/monitoring/monitor_sources.py`** — Monitor 10+ Saudi sources
  ```bash
  python scripts/monitoring/monitor_sources.py  # All sources
  python scripts/monitoring/monitor_sources.py --source aqar  # Specific source
  python scripts/monitoring/monitor_sources.py --list  # Show available sources
  ```

### Data Templates

- **`data/clean/transactions_scaffold.csv`** — Transaction data template
- **`data/clean/listings_scaffold.csv`** — Property listings template
- **`data/clean/source_registry.csv`** — Registry of 20+ data sources

### LLM Ready-to-Use Prompts

- **`prompts/chatgpt_transaction_extraction.md`** — ChatGPT prompt for data extraction
- **`prompts/aqar_data_request_email.md`** — Email template for Aqar partnership request

### Documentation

- **`docs/SOURCE_MAP.md`** — Complete source reference (21 KB, 8000+ words)
- **`scripts/README.md`** — Script documentation and examples
- **`data/README.md`** — Data organization and standards
- **`DATA_COLLECTION_SETUP.md`** — Quick-start guide

---

## File Organization

```
/sessions/dazzling-sharp-volta/mnt/saudi-realestate-platform/
│
├── DATA_SETUP_INDEX.md              ← You are here
├── DATA_COLLECTION_SETUP.md         ← Quick-start guide
│
├── data/
│   ├── raw/                         ← Raw ingested data (to be populated)
│   ├── clean/
│   │   ├── transactions_scaffold.csv
│   │   ├── listings_scaffold.csv
│   │   ├── source_registry.csv
│   │   └── README.md
│   ├── monitoring/                  ← Monitoring outputs (to be populated)
│   ├── exports/                     ← Generated reports (to be populated)
│   └── README.md
│
├── scripts/
│   ├── requirements.txt              ← Python dependencies
│   ├── README.md                     ← Script documentation
│   │
│   ├── collection/
│   │   ├── __init__.py
│   │   └── aqar_collector.py        ← Aqar listing extraction (546 lines)
│   │
│   └── monitoring/
│       ├── __init__.py
│       └── monitor_sources.py        ← Source monitoring (469 lines)
│
├── docs/
│   └── SOURCE_MAP.md                ← Complete source reference (8000+ words)
│
├── prompts/
│   ├── chatgpt_transaction_extraction.md    ← ChatGPT prompt
│   └── aqar_data_request_email.md           ← Email template
│
└── (existing project files...)
```

---

## Implementation Checklist

### Immediate (Today)
- [ ] Review `DATA_COLLECTION_SETUP.md`
- [ ] Review `docs/SOURCE_MAP.md` for source strategy
- [ ] Install dependencies: `pip install -r scripts/requirements.txt`

### Week 1: Integration Setup
- [ ] Test scripts: `python scripts/collection/aqar_collector.py <test-url>`
- [ ] Test monitoring: `python scripts/monitoring/monitor_sources.py --list`
- [ ] Import CSV templates into database schema
- [ ] Create API endpoints for source ingestion

### Week 2: Automation
- [ ] Add `monitor_sources.py` to cron (daily 6 AM)
- [ ] Create alert system for high-relevance items
- [ ] Build dashboard integration

### Week 3+: Expansion
- [ ] Add Bayut/PropertyFinder collectors
- [ ] Implement batch collection
- [ ] Add Ejar transaction support (if access granted)
- [ ] Build market analysis features

---

## Key Contacts

| Organization | Email | Purpose |
|---|---|---|
| Aqar.fm | sales@aqar.fm | Data partnership / API access |
| Ejar Ministry | ejar-support@moh.gov.sa | Transaction registry access |
| SAMA | sama.gov.sa | Economic data / interest rates |
| CBRE Saudi | saudi-arabia@cbre.com | Market research subscription |
| JLL Saudi | jll.com/en/contact | Market analysis subscription |

*Full contact list in SOURCE_MAP.md*

---

## Quick Reference Commands

### Setup
```bash
pip install -r scripts/requirements.txt
chmod +x scripts/collection/*.py
chmod +x scripts/monitoring/*.py
```

### Testing
```bash
# Test Aqar collector
python scripts/collection/aqar_collector.py "https://aqar.fm/property/example" --verbose

# Test source monitoring
python scripts/monitoring/monitor_sources.py --source aqar

# List available sources
python scripts/monitoring/monitor_sources.py --list
```

### Daily Automation
```bash
# Add to crontab for daily monitoring
crontab -e
# Insert: 0 6 * * * cd /path/to/project && python scripts/monitoring/monitor_sources.py
```

---

## Frequently Asked Questions

**Q: How do I extract a listing from Aqar?**  
A: Use `aqar_collector.py` script. See `scripts/README.md` for examples.

**Q: How do I monitor sources automatically?**  
A: Use `monitor_sources.py` and schedule it via cron. See `DATA_COLLECTION_SETUP.md` for examples.

**Q: Where are all the Saudi real estate sources documented?**  
A: See `docs/SOURCE_MAP.md` — complete reference for 20+ sources with access information.

**Q: How do I request data from Aqar?**  
A: Use the template in `prompts/aqar_data_request_email.md` and customize for your organization.

**Q: How do I extract transaction data from news articles?**  
A: Use the ChatGPT prompt in `prompts/chatgpt_transaction_extraction.md` and copy/paste into ChatGPT.

**Q: What data quality standards should I follow?**  
A: See `data/README.md` for confidence scoring (0.0-1.0) and reliability tiers (1-5).

---

## Documentation Hierarchy

1. **For Quick Start**: `DATA_COLLECTION_SETUP.md` (5 min read)
2. **For Script Usage**: `scripts/README.md` (10 min read)
3. **For Source Strategy**: `docs/SOURCE_MAP.md` (30 min read)
4. **For Data Organization**: `data/README.md` (10 min read)
5. **For Specific Scripts**: Individual script headers/docstrings

---

## Support Workflow

**Issue**: Script not running  
→ See `scripts/README.md` → Troubleshooting section

**Issue**: Need to add a new data source  
→ See `data/README.md` → Common Tasks section

**Issue**: Don't know which sources to use  
→ See `docs/SOURCE_MAP.md` → Priority Tiers section

**Issue**: Need to request data access  
→ Use template in `prompts/aqar_data_request_email.md`

**Issue**: Need to extract transaction data  
→ Use template in `prompts/chatgpt_transaction_extraction.md`

---

## Version Information

- **Platform**: Muqayyim (مقيم) v1.0.0
- **Stage**: 1 (Comparable Ingestor MVP)
- **Data Infrastructure**: v1.0.0 (March 24, 2026)
- **Python**: 3.8+ required
- **Scripts**: 2 (Aqar collector, Source monitor)
- **Documentation**: 4 comprehensive guides
- **Data Sources Mapped**: 20+

---

## Next Steps

1. ✅ Read `DATA_COLLECTION_SETUP.md` (5 minutes)
2. ✅ Review `docs/SOURCE_MAP.md` for source strategy (20 minutes)
3. ✅ Test scripts with sample data
4. ✅ Set up cron automation
5. ✅ Integrate with platform database
6. ✅ Build monitoring dashboard

---

**Questions?** See the relevant documentation file above.  
**Ready to integrate?** Start with `DATA_COLLECTION_SETUP.md`.  
**Need source info?** Check `docs/SOURCE_MAP.md`.

---

*Created: March 24, 2026*  
*Maintained by: Data Engineering Team*  
*Status: Ready for Production*
