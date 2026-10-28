"""
LLM Fallback Extractor — uses Claude to extract structured fields
from text that deterministic parsers couldn't resolve.

RULES:
- LLM is a PARSER, not a DATA SOURCE
- It extracts from provided text only
- It must NEVER invent values
- If unsure, return null with low confidence
- Only used after deterministic extraction fails
"""

import json
import os
from uuid import UUID

from extractors.citation import build_citation


EXTRACTION_PROMPT = """You are a structured data extractor for Saudi Arabian real estate listings.

Extract the following fields from the provided text. For each field, return:
- "value": the extracted value (or null if not found)
- "raw_text": the exact text you found it in
- "confidence": 0.0-1.0 how confident you are

Fields to extract:
- property_title: Title or name of the property
- city: City name (Arabic or English)
- district: District/neighborhood name
- property_type: One of: villa, apartment, land, office, retail, warehouse, compound, other
- deal_type: One of: sale, lease, rent
- evidence_type: One of: listing_asking, transaction_achieved, unknown
- asking_price: Asking price (number only, no currency symbol)
- transacted_price: Transaction price if mentioned (number only)
- currency: SAR, USD, AED, or other
- area_value: Primary area value (number)
- area_unit: sqm or sqft
- area_type: land_area, bua, gla, total_area, unknown
- listing_date: Date in any format
- transaction_date: Transaction date if mentioned
- tenure: freehold, leasehold, or unknown
- latitude: If coordinates present
- longitude: If coordinates present

CRITICAL RULES:
- Only extract what is explicitly stated in the text
- If a field is not mentioned, set value to null
- Do NOT guess or infer values not present in the text
- Return valid JSON only, no markdown

Return a JSON object with field names as keys, each containing {value, raw_text, confidence}."""


async def extract_with_llm(
    text: str,
    source_id: UUID,
    source_type: str,
    source_url_or_name: str,
) -> list[dict]:
    """
    Use Claude to extract structured fields from unresolved text.

    Returns a list of field dicts ready for database insertion.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return []  # No API key, skip LLM extraction

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": f"{EXTRACTION_PROMPT}\n\n--- TEXT TO EXTRACT FROM ---\n{text[:8000]}"
                }
            ],
        )

        response_text = message.content[0].text
        # Strip markdown fences if present
        response_text = response_text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("\n", 1)[1]
        if response_text.endswith("```"):
            response_text = response_text.rsplit("```", 1)[0]

        extracted = json.loads(response_text)

    except Exception:
        # LLM extraction failed — return empty (deterministic results still apply)
        return []

    # Convert to field dicts with citations
    fields = []
    for field_name, data in extracted.items():
        if not isinstance(data, dict) or data.get("value") is None:
            continue

        fields.append({
            "field_name": field_name,
            "raw_value": data.get("raw_text", str(data["value"])),
            "normalized_value": str(data["value"]),
            "display_value": str(data["value"]),
            "confidence": min(data.get("confidence", 0.5), 0.85),  # Cap LLM confidence at 0.85
            "classification": "fact",
            "value_type": "string",
            "citation": build_citation(
                source_id=source_id,
                source_type=source_type,
                source_url_or_name=source_url_or_name,
                locator="llm_extraction",
                snippet=data.get("raw_text", "")[:500],
                extractor_name="llm_fallback",
                extractor_version="1.0.0",
                parse_confidence=0.0,  # No deterministic parse
                llm_confidence=min(data.get("confidence", 0.5), 0.85),
                normalization_notes="Extracted by LLM — requires human verification",
            ),
        })

    return fields
