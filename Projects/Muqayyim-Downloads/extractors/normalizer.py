"""
Saudi-specific value normalization.

Handles:
- Currency normalization (SAR default)
- Area conversion (sqft → sqm)
- Date normalization (Hijri → Gregorian, multiple formats)
- Location normalization (Arabic/English, city/district split)
- Arabic numeral conversion
- Price per sqm computation
"""

import re
from typing import Optional

# Arabic-Eastern numeral mapping
ARABIC_NUMERALS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

# Known city name mappings (Arabic → English)
CITY_MAP = {
    "الرياض": "Riyadh",
    "جده": "Jeddah",   # alternate spelling (ha)
    "جدة": "Jeddah",   # canonical spelling (ta marbuta) — must come last for reverse map
    "مكة": "Makkah",
    "مكة المكرمة": "Makkah",
    "المدينة": "Madinah",
    "المدينة المنورة": "Madinah",
    "الدمام": "Dammam",
    "الخبر": "Khobar",
    "الظهران": "Dhahran",
    "تبوك": "Tabuk",
    "أبها": "Abha",
    "الطائف": "Taif",
    "القصيم": "Qassim",
    "بريدة": "Buraydah",
    "حائل": "Hail",
    "نجران": "Najran",
    "جازان": "Jazan",
    "ينبع": "Yanbu",
    "الجبيل": "Jubail",
    "الأحساء": "Al Ahsa",
    "الخرج": "Al Kharj",
}

# Reverse mapping
CITY_MAP_REVERSE = {v.lower(): k for k, v in CITY_MAP.items()}

SQFT_TO_SQM = 0.09290304


def normalize_arabic_numerals(text: str) -> str:
    """Convert Arabic-Eastern numerals (٠١٢...) to Western (012...)."""
    return text.translate(ARABIC_NUMERALS)


def extract_number(text: str) -> Optional[float]:
    """Extract a numeric value from text, handling Arabic numerals and commas."""
    if not text:
        return None
    cleaned = normalize_arabic_numerals(str(text))
    cleaned = cleaned.replace(",", "").replace("٬", "").replace("،", "")
    # Remove currency symbols and units
    cleaned = re.sub(r"[ريالSARsarر.س\s]", "", cleaned)
    match = re.search(r"[\d.]+", cleaned)
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None


def normalize_currency(text: str) -> str:
    """Normalize currency to ISO code. Default: SAR."""
    if not text:
        return "SAR"
    upper = text.upper().strip()
    if any(k in upper for k in ["ريال", "SAR", "ر.س"]):
        return "SAR"
    if any(k in upper for k in ["USD", "دولار", "$"]):
        return "USD"
    if any(k in upper for k in ["AED", "درهم"]):
        return "AED"
    return "SAR"  # Default for KSA context


def normalize_area(value: float, from_unit: str) -> tuple[float, str]:
    """
    Normalize area to sqm.
    Returns (normalized_value, "sqm").
    """
    unit_lower = from_unit.lower().strip() if from_unit else ""
    if unit_lower in ("sqft", "sq ft", "square feet", "قدم مربع", "قدم"):
        return round(value * SQFT_TO_SQM, 2), "sqm"
    # Already sqm or unknown
    return value, "sqm"


def sqm_to_sqft(sqm: float) -> float:
    """Convert sqm to sqft."""
    return round(sqm / SQFT_TO_SQM, 2)


def normalize_city(raw: str) -> tuple[Optional[str], Optional[str]]:
    """
    Normalize a city name to (English, Arabic).
    Returns (english_name, arabic_name) or (raw, None) if unknown.
    """
    if not raw:
        return None, None
    stripped = raw.strip()

    # Check Arabic → English
    if stripped in CITY_MAP:
        return CITY_MAP[stripped], stripped

    # Check English → Arabic
    lower = stripped.lower()
    if lower in CITY_MAP_REVERSE:
        return stripped, CITY_MAP_REVERSE[lower]

    # Unknown city — return as-is
    return stripped, None


def normalize_date(raw: str) -> Optional[str]:
    """
    Attempt to normalize a date string to ISO format (YYYY-MM-DD).
    Handles common Saudi date formats.
    Returns None if unparseable.
    """
    if not raw:
        return None

    from dateutil import parser as dateutil_parser

    cleaned = normalize_arabic_numerals(raw.strip())

    try:
        dt = dateutil_parser.parse(cleaned, dayfirst=True)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, OverflowError):
        pass

    return None


def hijri_to_gregorian(hijri_date: str) -> Optional[str]:
    """
    Convert Hijri date to Gregorian ISO format.
    Expects format like "1446-06-15" or "15/06/1446".
    """
    if not hijri_date:
        return None

    try:
        from hijri_converter import Hijri

        cleaned = normalize_arabic_numerals(hijri_date.strip())
        # Try YYYY-MM-DD
        match = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})", cleaned)
        if match:
            y, m, d = int(match.group(1)), int(match.group(2)), int(match.group(3))
            greg = Hijri(y, m, d).to_gregorian()
            return greg.strftime("%Y-%m-%d")

        # Try DD/MM/YYYY
        match = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", cleaned)
        if match:
            d, m, y = int(match.group(1)), int(match.group(2)), int(match.group(3))
            if y > 1400:  # Likely Hijri year
                greg = Hijri(y, m, d).to_gregorian()
                return greg.strftime("%Y-%m-%d")
    except Exception:
        pass

    return None


def detect_area_unit(text: str) -> str:
    """Detect area unit from text."""
    if not text:
        return "sqm"
    lower = text.lower()
    if any(k in lower for k in ["sqft", "sq ft", "square feet", "قدم"]):
        return "sqft"
    return "sqm"


def compute_price_per_sqm(price: Optional[float], area_sqm: Optional[float]) -> Optional[float]:
    """Compute price per sqm, returning None if inputs are invalid."""
    if price and area_sqm and area_sqm > 0:
        return round(price / area_sqm, 2)
    return None
