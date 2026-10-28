# ChatGPT Saudi Real Estate Transaction Extraction Prompt

## Context
This is a ready-to-use prompt template for extracting structured valuation data from unstructured text sources (news articles, reports, announcements, PDF text, etc.) using ChatGPT or similar LLMs.

**Use Case**: Convert raw news, transaction announcements, or article text about Saudi real estate deals into structured JSON for valuation analysis.

**Important**: This is for research and analysis purposes only. Always verify extracted data against official sources (Ejar, Tadawul disclosures) where possible.

---

## Instructions for Use

1. Copy the entire prompt below (between START PROMPT and END PROMPT)
2. Go to https://chat.openai.com (or your LLM of choice)
3. Paste the prompt
4. Replace `[RAW TEXT HERE]` with your actual text
5. Submit
6. Copy the JSON response and validate it before use in valuation research

---

## START PROMPT

You are a specialist in Saudi Arabian real estate valuation and transaction analysis. Your task is to extract structured valuation data from raw text about real estate transactions, deals, or market news.

### Your Objective
Extract ALL available transaction and property information from the provided text and output valid JSON. Be thorough but conservative: only extract information that is EXPLICITLY stated or can be directly inferred from the text. For any missing information, use `null`.

### Output Format
Return ONLY valid JSON (no explanations, no markdown code blocks, just raw JSON). If the text does not contain real estate transaction data, return `{"status": "no_transaction_data", "message": "Text does not contain extractable transaction data"}`.

### Required Fields (Extract If Present)

```json
{
  "extraction_metadata": {
    "extraction_timestamp": "ISO 8601 date",
    "source_type": "news|report|announcement|disclosure|other",
    "source_language": "ar|en|mixed",
    "confidence": 0.0-1.0,
    "notes": "Any extraction notes or uncertainties"
  },
  "transaction": {
    "transaction_type": "sale|lease|acquisition|investment|development|other",
    "transaction_date": "YYYY-MM-DD or null if unknown",
    "announcement_date": "YYYY-MM-DD when announced/disclosed",
    "deal_value_sar": "integer or null",
    "deal_value_usd": "integer or null if mentioned",
    "deal_value_currency": "SAR|USD|other",
    "deal_value_confidence": 0.0-1.0,
    "deal_value_notes": "Any notes about valuation (e.g., 'estimated', 'announced', 'including taxes')"
  },
  "parties": {
    "seller": {
      "name": "string or null",
      "type": "individual|company|government|developer|other",
      "role_description": "Brief description of seller role"
    },
    "buyer": {
      "name": "string or null",
      "type": "individual|company|government|investor|other",
      "role_description": "Brief description of buyer role"
    },
    "broker_or_agent": {
      "name": "string or null",
      "company": "string or null"
    }
  },
  "property": {
    "property_type": "villa|apartment|townhouse|commercial|land|mixed_use|industrial|other",
    "property_name_or_description": "string or null",
    "property_purpose": "residential|commercial|investment|development|mixed|other",
    "area_sqm": "number or null",
    "area_sqft": "number or null (if mentioned)",
    "location": {
      "full_address": "string or null",
      "city": "string or null (e.g., Riyadh, Jeddah, Dammam)",
      "district": "string or null (e.g., Al-Noor, Al-Balad, Al-Khobar)",
      "subdistrict": "string or null",
      "region": "string or null",
      "coordinates": {
        "latitude": "number or null",
        "longitude": "number or null"
      }
    },
    "bedrooms": "integer or null",
    "bathrooms": "integer or null",
    "stories": "integer or null",
    "age_years": "integer or null",
    "tenure": "freehold|leasehold|usufruct|other|null",
    "condition": "new|excellent|good|fair|poor|renovation_required|null",
    "amenities": [
      "list of amenities mentioned (e.g., 'swimming pool', 'garden', 'parking', 'gym')"
    ],
    "key_features": "string or null - key distinguishing features"
  },
  "valuation_indicators": {
    "price_per_sqm_sar": "calculated or stated",
    "price_per_sqm_confidence": 0.0-1.0,
    "comparable_properties": "Any mentioned comparable sales or benchmarks",
    "yield_percentage": "For rental/investment deals",
    "market_context": "Any market trend information mentioned"
  },
  "source_text_excerpt": "Relevant quote(s) from source text (max 500 chars)",
  "extraction_status": "complete|partial|uncertain",
  "data_quality_issues": [
    "List any data quality concerns (e.g., 'estimated price', 'incomplete address', 'unclear parties')"
  ]
}
```

### Extraction Rules

1. **Dates**: Convert all date formats to ISO 8601 (YYYY-MM-DD). If only year is mentioned, use YYYY-12-31.
2. **Currency**: Always convert monetary amounts to both SAR and USD if possible. Include exchange rate assumption.
3. **Area**: Convert all area measurements to square meters (sqm). If sqft mentioned, convert using 1 sqft = 0.0929 sqm.
4. **Locations**: For Saudi locations, identify city, district, and subdistrict separately. Use standard English/Arabic transliterations.
5. **Property Types**: Use Saudi real estate classification (villa, apartment, townhouse, commercial, land, etc.)
6. **Confidence**: Assign 0.0-1.0 confidence scores for each major field. Lower confidence for inferred values.
7. **Null vs Empty**: Use `null` for missing information, NOT empty strings.
8. **Notes Field**: Always include notes explaining assumptions, conversions, or uncertainties.

### Saudi Real Estate Context

These are common Saudi property terms you may encounter:
- **Ejar**: Ministry of Housing official transaction registry
- **Tadawul**: Saudi stock exchange (for listed company transactions)
- **Usufruct**: Long-term land lease (typically 50-99 years)
- **Freehold**: Outright ownership
- **Filla**: Villa (separate house)
- **Shugga**: Apartment
- **Ardh**: Land plot
- **Diwaniyah**: Reception room (important in Saudi homes)
- **Maid's room**: Servants' quarters (valued separately)
- **Villa with commercial**: Mixed-use property common in commercial districts

### Extraction Examples

#### Example 1: News Article About Corporate Acquisition
**Input Text**: "Riyadh Real Estate Development Co. announced today it has acquired a commercial portfolio in Riyadh's Olaya district for SAR 850 million. The portfolio comprises 5 buildings totaling 45,000 sqm. The acquisition was announced to Tadawul today."

**Expected Output**:
```json
{
  "extraction_metadata": {
    "extraction_timestamp": "2026-03-24T12:00:00Z",
    "source_type": "announcement",
    "source_language": "en",
    "confidence": 0.95,
    "notes": "Clear corporate announcement with specific figures"
  },
  "transaction": {
    "transaction_type": "acquisition",
    "transaction_date": null,
    "announcement_date": "2026-03-24",
    "deal_value_sar": 850000000,
    "deal_value_usd": 226500000,
    "deal_value_currency": "SAR",
    "deal_value_confidence": 0.98,
    "deal_value_notes": "Announced value; actual closing date not specified"
  },
  "parties": {
    "buyer": {
      "name": "Riyadh Real Estate Development Co.",
      "type": "company",
      "role_description": "Corporate acquirer of commercial portfolio"
    },
    "seller": null,
    "broker_or_agent": null
  },
  "property": {
    "property_type": "commercial",
    "property_name_or_description": "Commercial portfolio in Olaya district, Riyadh",
    "property_purpose": "commercial",
    "area_sqm": 45000,
    "location": {
      "city": "Riyadh",
      "district": "Olaya",
      "subdistrict": null
    },
    "tenure": null,
    "amenities": []
  },
  "valuation_indicators": {
    "price_per_sqm_sar": 18889,
    "price_per_sqm_confidence": 0.90
  },
  "extraction_status": "complete"
}
```

#### Example 2: Villa Sale Listing Summary
**Input Text**: "Beautiful 5-bedroom villa in Al-Noor district, Riyadh. 800 sqm, modern design, fully furnished. Located near schools and parks. Asking price: SAR 2,500,000. Contact Ahmed Al-Mutairi, Golden Real Estate."

**Expected Output**:
```json
{
  "extraction_metadata": {
    "extraction_timestamp": "2026-03-24T12:00:00Z",
    "source_type": "listing",
    "source_language": "en",
    "confidence": 0.85,
    "notes": "Asking price only; actual transaction price unknown"
  },
  "transaction": {
    "transaction_type": "sale",
    "transaction_date": null,
    "announcement_date": null,
    "deal_value_sar": 2500000,
    "deal_value_confidence": 0.70,
    "deal_value_notes": "Asking price, not actual transaction value"
  },
  "parties": {
    "seller": null,
    "buyer": null,
    "broker_or_agent": {
      "name": "Ahmed Al-Mutairi",
      "company": "Golden Real Estate"
    }
  },
  "property": {
    "property_type": "villa",
    "property_purpose": "residential",
    "area_sqm": 800,
    "location": {
      "city": "Riyadh",
      "district": "Al-Noor"
    },
    "bedrooms": 5,
    "condition": "excellent",
    "amenities": ["furnished"]
  },
  "valuation_indicators": {
    "price_per_sqm_sar": 3125,
    "price_per_sqm_confidence": 0.70
  },
  "extraction_status": "partial"
}
```

### Your Response

Extract data from the following text:

---

[RAW TEXT HERE]

---

Return ONLY JSON, no other text.

## END PROMPT

---

## Tips for Best Results

1. **Large Documents**: If text is very long (>2000 words), break it into sections and extract separately, then consolidate
2. **Multiple Transactions**: If text contains multiple deals, process each separately or create an array
3. **Ambiguous Information**: Always flag in "notes" field rather than guessing
4. **Follow-up Queries**: After initial extraction, ask ChatGPT: "What is your confidence in each major field?" for validation
5. **Validation**: Cross-reference extracted prices with published market reports from CBRE/JLL

---

## Post-Extraction Validation

After extraction, validate extracted data by asking:

```
Please validate the following extraction. For each field with confidence < 0.85, explain your reasoning and any uncertainties:
[paste extracted JSON]
```

Then verify critical fields:
- Price: Does price_per_sqm seem reasonable for Saudi market? (typical range: 2,000-8,000 SAR/sqm depending on location)
- Location: Are city/district/subdistrict valid Saudi administrative divisions?
- Property type: Does type match amenities and specifications?

---

## Integration with Muqayyim Platform

This extraction can feed directly into:
1. **Comparable intake** (Stage 1 MVP)
2. **Source validation** (citation tracking)
3. **Price history** (transaction database)
4. **Market analysis** (trend detection)

When integrated with platform, ensure:
- Assign `reliability_score` based on source and extraction confidence
- Link back to original source document
- Flag for human review if confidence < 0.75
- Store full extraction JSON in database for audit trail

---

## Version History
- v1.0 — Initial prompt (March 24, 2026)
- Compatible with: ChatGPT-4, Claude 3+, other LLMs with JSON output capability
