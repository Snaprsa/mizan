# Saudi Real Estate Data Sources — Comprehensive Mapping

## Overview

This document maps all publicly available and semi-public Saudi real estate data sources, classified by type, accessibility, and extractable fields. It serves as a reference for data collection strategy and integration planning.

**Last Updated**: March 24, 2026
**Scope**: Saudi Arabia (KSA)
**Focus**: Valuation research, comparable analysis, market intelligence

---

## Source Categories

Sources are categorized by:
- **Type**: Web marketplace, government registry, news/media, research/analyst reports, stock exchange, economic data
- **Accessibility**: Public (no login), Semi-public (registration/login), Manual (contact required), Restricted (official access only)
- **Data Quality**: High (authenticated source), Medium (professional listing), Low (user-generated)
- **Update Frequency**: Real-time, Daily, Weekly, Monthly, Quarterly, Ad-hoc

---

## 1. Web Marketplaces (Real-Time Listings)

### 1.1 Aqar.fm
- **URL**: https://aqar.fm
- **Type**: Web Marketplace (Saudi-specific)
- **Accessibility**: Public
- **Update Frequency**: Real-time
- **Data Types**: Residential listings, commercial listings, land, villas, apartments, price, location, description
- **Extractable Fields**:
  - Price (SAR)
  - Area (sqm)
  - Location (city, district, subdistrict)
  - Property type (villa, apartment, townhouse, etc.)
  - Bedrooms/bathrooms
  - Tenure (freehold, usufruct)
  - Contact information
  - Listing date
  - Images (count and URLs)
  - Description (Arabic)
  - Amenities
  - Contact agent name
  - Agency name
- **Limitations**:
  - User-generated data (confidence varies)
  - No verified transaction history
  - Listings may be stale (expired not always immediately removed)
  - Some fields optional at listing creation
- **Recommended Collection**: Web scraping with rate limiting, or contact Aqar for API/data partnership
- **API Access**: Undocumented; contact sales@aqar.fm for partnership inquiries
- **Notes**: Largest Saudi real estate marketplace; critical for comparable research

### 1.2 Bayut Saudi
- **URL**: https://bayut.com.sa
- **Type**: Web Marketplace (Gulf-wide, strong Saudi presence)
- **Accessibility**: Public
- **Update Frequency**: Real-time
- **Data Types**: Residential, commercial, land, price, location, specifications
- **Extractable Fields**:
  - Price (SAR)
  - Area (sqm)
  - Location (city, district)
  - Property type
  - Bedrooms/bathrooms
  - Amenities list
  - Agent/agency info
  - Listing date
  - Images
  - Description (EN/AR)
- **Limitations**:
  - Gulf-wide platform (mixed quality)
  - Limited historical data
  - Some listings cross-listed from Aqar
- **Recommended Collection**: Web scraping or direct inquiry
- **Notes**: Secondary marketplace; useful for cross-validation

### 1.3 Property Finder Saudi
- **URL**: https://propertyfinder.sa
- **Type**: Web Marketplace (Gulf-wide)
- **Accessibility**: Public
- **Update Frequency**: Real-time
- **Data Types**: Residential, commercial, land, detailed specifications
- **Extractable Fields**:
  - Price (SAR)
  - Area (sqm)
  - Location (coordinates, city, district)
  - Property type
  - Bedrooms/bathrooms
  - Furnished status
  - Amenities
  - Agent info
  - Listing date
  - Images
- **Limitations**:
  - International platform (data standardization varies)
  - Significant overlap with other sources
- **Recommended Collection**: Web scraping (documented in data collection scripts)
- **Notes**: Useful for API exploration and data standardization study

### 1.4 Wafi Platform
- **URL**: https://wafi.com.sa
- **Type**: Web Marketplace (Services + real estate)
- **Accessibility**: Public
- **Update Frequency**: Real-time
- **Data Types**: Residential, some commercial, prices, locations
- **Extractable Fields**:
  - Price (SAR)
  - Area (sqm)
  - Location
  - Property type
  - Bedrooms/bathrooms
  - Contact info
  - Listing date
- **Limitations**:
  - Mixed marketplace (real estate is secondary feature)
  - Lower listing quality than Aqar
  - Sparse descriptions
- **Recommended Collection**: Web scraping for supplementary data
- **Notes**: Includes rental listings; useful for lease valuation research

### 1.5 Aqarsas
- **URL**: https://www.aqarsas.com
- **Type**: Web Marketplace
- **Accessibility**: Public
- **Update Frequency**: Real-time
- **Data Types**: Residential, commercial, land
- **Extractable Fields**:
  - Price (SAR)
  - Area (sqm)
  - Location
  - Property type
  - Bedrooms/bathrooms
  - Utilities included (for rentals)
  - Agent info
  - Listing date
- **Limitations**:
  - Newer platform with lower volume
  - Some data quality issues
- **Recommended Collection**: Monitor for emerging trends; lower priority
- **Notes**: Secondary source for validation

### 1.6 Paseetah
- **URL**: https://www.paseetah.com
- **Type**: Web Marketplace
- **Accessibility**: Public
- **Update Frequency**: Real-time
- **Data Types**: Residential primary, some commercial
- **Extractable Fields**:
  - Price (SAR)
  - Area (sqm)
  - Location (city, district)
  - Property type
  - Bedrooms/bathrooms
  - Contact info
  - Listing date
  - Images
- **Limitations**:
  - Smallest marketplace by volume
  - Lower data quality
- **Recommended Collection**: Lower priority; use for market validation
- **Notes**: Include if building comprehensive dataset

---

## 2. Government & Official Registries

### 2.1 Ejar (Ministry of Housing)
- **URL**: https://ejar.moh.gov.sa
- **Type**: Government Registry (Official transactions)
- **Accessibility**: Restricted (requires official credentials)
- **Update Frequency**: Daily (transactions updated same day)
- **Data Types**: Authenticated transactions, contracts, property registration
- **Extractable Fields**:
  - Transaction price (SAR) — **AUTHENTICATED**
  - Property area (sqm)
  - Location (exact address, coordinates available)
  - Property type (precise classification)
  - Transaction date
  - Transaction type (sale, lease, gift)
  - Parties (names may be anonymized for privacy)
  - Transaction reference ID
  - Property ID
  - Property status (registered, mortgaged)
  - Insurance and title status
- **Limitations**:
  - Access restricted to authorized valuation firms, government agencies, and licensed professionals
  - Expensive subscription fees
  - Personal information redacted
  - Significant lag for some data categories
- **Recommended Collection**:
  - Register as authorized valuation professional
  - Contact: ejar-support@moh.gov.sa
  - Costs: Premium service, negotiate volume discounts
- **Reliability Score**: 5/5 (authenticated government source)
- **Notes**: HIGHEST RELIABILITY for transaction data; essential for valuation work. Apply for official access credentials.

### 2.2 Ministry of Housing Statistics
- **URL**: https://www.housing.gov.sa
- **Type**: Government Statistics (Public reporting)
- **Accessibility**: Public
- **Update Frequency**: Quarterly
- **Data Types**: Market statistics, region-wide aggregates, policy data
- **Extractable Fields**:
  - Regional transaction volumes
  - Average prices by region/property type
  - Market trends
  - Housing program data
  - Regional breakdowns
- **Limitations**:
  - Aggregated only (no individual transaction data)
  - Quarterly lag
  - Limited detail on property specifications
- **Recommended Collection**: Web scraping (Python script template provided)
- **Reliability Score**: 5/5 (official government data)
- **Notes**: Critical for market context and trend validation

### 2.3 SAMA (Saudi Central Bank)
- **URL**: https://www.sama.gov.sa
- **Type**: Central Bank (Economic data)
- **Accessibility**: Public
- **Update Frequency**: Monthly
- **Data Types**: Interest rates, mortgage rates, exchange rates, economic indicators
- **Extractable Fields**:
  - Policy interest rates
  - Average mortgage rates (by bank)
  - Exchange rates (SAR vs USD, EUR, etc.)
  - Inflation rates
  - M1/M2 money supply
  - Credit growth
  - Property finance volumes
- **Limitations**:
  - Macro data only
  - Published with 2-4 week lag
- **Recommended Collection**: Automated API calls (SAMA provides REST API)
- **Reliability Score**: 5/5 (central bank official)
- **Notes**: Essential context for valuation assumptions; use for financing scenarios

---

## 3. Stock Exchange & Corporate Disclosures

### 3.1 Tadawul (Saudi Stock Exchange)
- **URL**: https://www.tadawul.com.sa
- **Type**: Securities Exchange (Corporate disclosures)
- **Accessibility**: Public
- **Update Frequency**: Real-time (during trading)
- **Data Types**: Listed company announcements, property acquisitions, acquisitions involving real estate
- **Extractable Fields**:
  - Transaction announcements
  - Deal value (SAR)
  - Property description
  - Company announcements (property acquisitions)
  - Disclosure documents (PDFs)
  - Date of disclosure
  - Company identifiers
  - Board approval dates
- **Limitations**:
  - Only covers listed companies
  - Announcement may occur before or after transaction completion
  - Property details often vague in public disclosures
  - May require access to full disclosure documents
- **Recommended Collection**:
  - Web scraping (RSS/news feed available)
  - Contact investor relations departments for details
- **Reliability Score**: 4/5 (audited corporate disclosure)
- **Notes**: Excellent for institutional/corporate deals; use for market context

---

## 4. Professional Market Research & Analyst Reports

### 4.1 CBRE Saudi Arabia
- **URL**: https://www.cbre.com/en/markets/emea/saudi-arabia
- **Type**: Market Research (Professional reports)
- **Accessibility**: Public (reports); Semi-public (detailed data)
- **Update Frequency**: Monthly/Quarterly
- **Data Types**: Market analysis, price indices, market trends, sector analysis
- **Extractable Fields**:
  - Market trend analysis
  - Comparable price ranges (by region, type)
  - Rental yield analysis
  - Occupancy rates
  - Market forecasts
  - Sector insights
  - Development pipeline data
- **Limitations**:
  - High-level analysis (not individual properties)
  - Published with 4-6 week lag
  - Premium reports require subscription
- **Recommended Collection**:
  - Download public reports
  - Subscribe for premium intelligence
  - Contact: saudi-arabia@cbre.com
- **Reliability Score**: 4/5 (professional firm, but market aggregated)
- **Notes**: Essential for market calibration and comparable ranges

### 4.2 Jones Lang LaSalle (JLL) Saudi Arabia
- **URL**: https://www.jll.com/en/services/markets/saudi-arabia
- **Type**: Market Research (Professional reports)
- **Accessibility**: Public/Semi-public
- **Update Frequency**: Quarterly
- **Data Types**: Market reports, sector analysis, investment insights
- **Extractable Fields**:
  - Market overview
  - Price trends
  - Rental market analysis
  - Development projects
  - Investment opportunities
  - Regional breakdowns
- **Limitations**:
  - Aggregated market data
  - Premium reports require contact
- **Recommended Collection**: Download public reports; contact for detailed data
- **Reliability Score**: 4/5 (professional firm)
- **Notes**: Residential market analysis highly useful

### 4.3 Savills Saudi Arabia
- **URL**: https://www.savills.com
- **Type**: Market Research (Professional reports)
- **Accessibility**: Public/Semi-public
- **Update Frequency**: Quarterly
- **Data Types**: Market trends, price analysis, investment reports
- **Extractable Fields**:
  - Market trends
  - Price benchmarks
  - Rental analysis
  - Sector forecasts
- **Limitations**:
  - Limited Saudi-specific data (international firm focus)
- **Recommended Collection**: Monitor for major market moves
- **Notes**: Secondary source for cross-validation

### 4.4 Colliers Saudi Arabia
- **URL**: https://www.colliers.com
- **Type**: Market Research (Professional reports)
- **Accessibility**: Public/Semi-public
- **Update Frequency**: Quarterly
- **Data Types**: Commercial and industrial market analysis
- **Extractable Fields**:
  - Commercial property trends
  - Industrial market data
  - Investment trends
- **Limitations**:
  - Commercial-focused (limited residential)
- **Recommended Collection**: For commercial valuation research
- **Notes**: Primary source for commercial/industrial comparables

---

## 5. News & Market Intelligence

### 5.1 Al Arabiya Property
- **URL**: https://www.alarabiya.net/autos-and-property
- **Type**: News Media (Market news)
- **Accessibility**: Public
- **Update Frequency**: Daily
- **Data Types**: Market news, deals, company announcements, trends
- **Extractable Fields**:
  - News headlines
  - Deal announcements
  - Market commentary
  - Company news
  - Article dates
  - Quotes and context
- **Limitations**:
  - News summaries (not detailed data)
  - May contain editorial opinions
  - Arabic language (English translation available)
- **Recommended Collection**:
  - RSS feed monitoring (monitor_sources.py script)
  - Keyword-based filtering for relevance
- **Reliability Score**: 2/5 (news, not primary source)
- **Notes**: Good for market pulse and major announcements

### 5.2 Saudi Gazette Property
- **URL**: https://saudigazette.com.sa
- **Type**: News Media (English newspaper)
- **Accessibility**: Public
- **Update Frequency**: Daily
- **Data Types**: Property news, market analysis, company announcements
- **Extractable Fields**:
  - News articles
  - Property announcements
  - Market commentary
  - Interview quotes
  - Deal summaries
- **Limitations**:
  - English-language (secondary source for many topics)
  - Summarized news (not raw data)
- **Recommended Collection**: RSS feed monitoring
- **Reliability Score**: 2/5 (news media)
- **Notes**: Useful for English-speaking audience context

### 5.3 Argaam (Arabiya Financial News)
- **URL**: https://www.argaam.com/en/category/real-estate
- **Type**: Financial News (Arabic markets focus)
- **Accessibility**: Public
- **Update Frequency**: Daily
- **Data Types**: Real estate company news, deals, market analysis
- **Extractable Fields**:
  - Company announcements
  - Deal reports
  - Market analysis
  - Stock-related real estate news
  - Deal valuations
- **Limitations**:
  - Focus on listed companies and major deals
  - Arabic language primary
- **Recommended Collection**: RSS feed monitoring
- **Reliability Score**: 2/5 (news media, but financial focus)
- **Notes**: Good for tracking institutional activity

### 5.4 Arab News
- **URL**: https://www.arabnews.com
- **Type**: News Media (International focus)
- **Accessibility**: Public
- **Update Frequency**: Continuous
- **Data Types**: Major market developments, regional trends
- **Extractable Fields**:
  - Major announcements
  - Market trends
  - Policy changes
  - International context
- **Limitations**:
  - International focus (Saudi coverage secondary)
  - High-level summary news
- **Recommended Collection**: Selective monitoring for major stories
- **Reliability Score**: 2/5 (news media)
- **Notes**: Useful for international context and major policy changes

---

## 6. Secondary Data Sources & Services

### 6.1 Zawya (Bloomberg/Reuters alternative for MENA)
- **URL**: https://www.zawya.com
- **Type**: Financial Data & News
- **Accessibility**: Public/Premium
- **Update Frequency**: Real-time/Daily
- **Data Types**: Company data, market news, financial data
- **Extractable Fields**:
  - Company profiles
  - Transaction announcements
  - Market data
  - News articles
- **Limitations**:
  - Limited Saudi real estate depth
  - Primarily financial market focused
- **Recommended Collection**: Supplementary monitoring
- **Notes**: Useful for institutional investor activity

### 6.2 Bloomberg & Reuters (Limited MENA Coverage)
- **URL**: https://www.bloomberg.com, https://www.reuters.com
- **Type**: Financial Data (International)
- **Accessibility**: Subscription required
- **Update Frequency**: Real-time
- **Data Types**: Major deal announcements, market context
- **Extractable Fields**:
  - Major transaction announcements
  - Market commentary
  - International context
- **Limitations**:
  - Very limited Saudi real estate coverage
  - Expensive subscription
- **Recommended Collection**: Institutional subscriptions only
- **Notes**: For contextual market intelligence only

---

## Data Collection Strategy by Source Type

### Real-Time Priority Sources (Monitor Continuously)
1. **Aqar.fm** — Primary marketplace data
2. **Ejar** — Authenticated transaction register (if access obtained)
3. **SAMA** — Economic indicators (monthly automated)
4. **Ministry of Housing** — Market statistics (quarterly automated)
5. **Al Arabiya Property** — Market pulse (daily monitoring)

### Secondary Priority Sources (Monitor Weekly/Monthly)
1. **Bayut Saudi** — Cross-validation
2. **Property Finder** — Price benchmarking
3. **CBRE Saudi** — Market trend calibration
4. **JLL Saudi** — Sector analysis
5. **Tadawul** — Corporate transaction data

### Supplementary Sources (Monitor As-Needed)
1. **Wafi Platform** — Rental market insights
2. **Savills/Colliers** — Sector-specific analysis
3. **News sources** — Market pulse and announcements
4. **Zawya** — Institutional activity tracking

---

## Access & Integration Roadmap

### Phase 1: Public Data (Immediate)
- Aqar.fm marketplace scraping
- Property Finder scraping
- News/RSS monitoring
- Ministry of Housing reports
- SAMA economic data
- Market research report collection

### Phase 2: Semi-Public Data (Weeks 2-4)
- Bayut/Wafi marketplace expansion
- CBRE/JLL premium report subscriptions
- Tadawul disclosure automation
- Contact agency partnerships

### Phase 3: Restricted Data (Months 2-3)
- Ejar official access application
- Government registry integration
- Potential APIs with major platforms
- Data partnership negotiations

### Phase 4: Advanced Analytics (Months 3-6)
- Time-series analysis across all sources
- Price index construction
- Comparative market analysis (CMA) automation
- Predictive market modeling

---

## Integration Points with Muqayyim Platform

### Immediate (Stage 1)
- Web scraping connectors for Aqar.fm, Bayut
- Manual PDF/URL source ingestion
- News monitoring integration

### Short-term (Stage 2)
- Ejar transaction lookup (if access obtained)
- Market research database
- Historical comparable linking

### Medium-term (Stage 3)
- Automated daily/weekly data ingestion
- Market index calculations
- Trend analysis and alerting

### Long-term (Stage 4)
- Predictive pricing models
- Automated valuation models (AVMs)
- Market-wide analytics dashboard

---

## Data Quality & Confidence Scoring

### Source Reliability Tiers

**Tier 1 (Reliability Score 5)**: Authenticated government/official data
- Ejar transactions
- Ministry statistics
- SAMA economic data

**Tier 2 (Reliability Score 4)**: Professional/corporate disclosure
- Tadawul disclosures
- CBRE/JLL reports
- Agency published data

**Tier 3 (Reliability Score 3)**: Professional marketplace listings
- Aqar.fm (agent-listed)
- Bayut (agent-listed)
- Property Finder (professional listings)

**Tier 4 (Reliability Score 2)**: User marketplace listings
- Aqar.fm (private owner listings)
- Wafi/Aqarsas/Paseetah listings
- News articles

**Tier 5 (Reliability Score 1)**: Unverified or limited source
- Social media
- Hearsay/local information
- Single news report without verification

---

## Recommended Data Enrichment

For maximum valuation accuracy, cross-reference comparable data across:
1. **Marketplace listings** (for asking prices and specifications)
2. **Transaction data** (for actual transaction prices)
3. **Market research** (for market calibration)
4. **Economic indicators** (for financing assumptions)
5. **News/market intelligence** (for local context and recent changes)

---

## Contact Information for Data Access

| Source | Contact | Email | Notes |
|--------|---------|-------|-------|
| Ejar | Ministry of Housing | ejar-support@moh.gov.sa | Official access credentials required |
| SAMA | Saudi Central Bank | sama.gov.sa contact form | API documentation available |
| Aqar.fm | Sales Team | sales@aqar.fm | Data partnership inquiries |
| Bayut | Sales/API | hello@bayut.com | Potential API access for partners |
| CBRE Saudi | Office | saudi-arabia@cbre.com | Report subscriptions |
| JLL Saudi Arabia | Office | jll.com/en/contact | Market research subscriptions |
| Tadawul | Investor Relations | ir-info@tadawul.com.sa | Historical disclosures database |

---

## Legal & Ethical Considerations

- **Web Scraping**: Respect robots.txt and terms of service; use rate limiting
- **Personal Data**: Ensure compliance with PDPA (Saudi Personal Data Protection Act)
- **Confidentiality**: Non-public transaction data (Ejar) restricted to authorized professionals
- **Attribution**: Always cite sources in valuation reports
- **Data Retention**: Follow KSA regulations for data retention (typically 5-7 years for valuation files)

---

## Updates & Maintenance

This document should be reviewed and updated:
- **Quarterly**: For new sources or source changes
- **Annually**: For comprehensive validation and strategy review
- **Ad-hoc**: When major market changes or new data providers emerge

Last reviewed: March 24, 2026
