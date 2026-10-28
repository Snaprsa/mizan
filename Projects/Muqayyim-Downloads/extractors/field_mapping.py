"""
Known field mappings for common Saudi real estate sites.

These patterns help the deterministic extractor before falling back to LLM.
Each mapping includes CSS selectors, regex patterns, and meta tag names
for specific sites.

TODO: Expand as we encounter more sites and learn their structures.
"""

import re
from typing import Optional


# Known site patterns — keyed by domain
SITE_PATTERNS: dict[str, dict] = {
    "sa.aqar.fm": {
        "name": "Aqar",
        "reliability": 2,
        "selectors": {
            "property_title": ["h1", ".listing-title", "[data-testid='listing-title']"],
            "asking_price": [".price", ".listing-price", "[data-testid='price']"],
            "city": [".location-city", ".breadcrumb li:nth-child(3)"],
            "district": [".location-district", ".breadcrumb li:nth-child(5)"],
            "area": [".area", ".listing-area", "[data-testid='area']"],
        },
        "meta_tags": {
            "property_title": ["og:title", "twitter:title"],
            "description": ["og:description", "description"],
        },
        # Aqar embeds listing data as escaped JSON inside Next.js script blocks.
        # These regex patterns extract values from that JSON blob.
        "json_patterns": {
            "asking_price": re.compile(r'"price\\":(\d+)', re.UNICODE),
            "area_sqm": re.compile(r'"space\\":(\d+(?:\.\d+)?)', re.UNICODE),
            "bedrooms": re.compile(r'"beds\\":(\d+)', re.UNICODE),
            "bathrooms": re.compile(r'"wc\\":(\d+)', re.UNICODE),
            "property_type_raw": re.compile(r'"category\\":(\d+)', re.UNICODE),
            "listing_id": re.compile(r'"listing_id\\":(\d+)', re.UNICODE),
            "lat": re.compile(r'"lat\\":([\d.\-]+)', re.UNICODE),
            "lng": re.compile(r'"lng\\":([\d.\-]+)', re.UNICODE),
            "city_raw": re.compile(r'"city_name_ar\\":\\"([^"\\]+)\\"', re.UNICODE),
            "district_raw": re.compile(r'"district_name_ar\\":\\"([^"\\]+)\\"', re.UNICODE),
        },
    },
    "pasteah.com": {
        "name": "Pasteah",
        "reliability": 2,
        "selectors": {
            "property_title": ["h1", ".property-title"],
            "asking_price": [".price", ".property-price"],
        },
        "meta_tags": {
            "property_title": ["og:title"],
        },
    },
    "aqarsas.com": {
        "name": "Aqarsas",
        "reliability": 2,
        "selectors": {
            "property_title": ["h1"],
            "asking_price": [".price"],
        },
        "meta_tags": {},
    },
}


# Common price patterns in Arabic and English
PRICE_PATTERNS = [
    # SAR patterns
    re.compile(r"([\d,٬،]+(?:\.\d+)?)\s*(?:ريال|ر\.س|SAR)", re.UNICODE),
    re.compile(r"(?:SAR|ريال|ر\.س)\s*([\d,٬،]+(?:\.\d+)?)", re.UNICODE),
    # Generic large number that might be a price
    re.compile(r"(?:السعر|Price|price)[\s:]*(\d[\d,٬،]*)", re.UNICODE),
]

# Area patterns
AREA_PATTERNS = [
    re.compile(r"([\d,٬،]+(?:\.\d+)?)\s*(?:متر\s*مربع|م²|sqm|م\.م)", re.UNICODE),
    re.compile(r"([\d,٬،]+(?:\.\d+)?)\s*(?:قدم\s*مربع|sqft|sq\.?\s*ft)", re.UNICODE),
    re.compile(r"(?:المساحة|Area|area|مساحة)[\s:]*(\d[\d,٬،.]*)", re.UNICODE),
]

# Date patterns
DATE_PATTERNS = [
    re.compile(r"(\d{4}-\d{1,2}-\d{1,2})"),
    re.compile(r"(\d{1,2}/\d{1,2}/\d{4})"),
    re.compile(r"(\d{1,2}-\d{1,2}-\d{4})"),
]

# Property type keywords
PROPERTY_TYPE_KEYWORDS = {
    "فيلا": "villa", "villa": "villa",
    "شقة": "apartment", "apartment": "apartment",
    "أرض": "raw_land", "land": "raw_land", "ارض": "raw_land",
    "مكتب": "office", "office": "office",
    "محل": "retail", "retail": "retail", "shop": "retail",
    "مستودع": "warehouse", "warehouse": "warehouse",
    "دوبلكس": "duplex", "duplex": "duplex",
    "تاون هاوس": "townhouse", "townhouse": "townhouse",
    "كمباوند": "compound", "compound": "compound",
}


def get_site_config(url: str) -> Optional[dict]:
    """Get site-specific configuration from URL."""
    for domain, config in SITE_PATTERNS.items():
        if domain in url:
            return config
    return None


def detect_property_type(text: str) -> Optional[str]:
    """Detect property type from text keywords."""
    lower = text.lower()
    for keyword, ptype in PROPERTY_TYPE_KEYWORDS.items():
        if keyword in lower:
            return ptype
    return None
