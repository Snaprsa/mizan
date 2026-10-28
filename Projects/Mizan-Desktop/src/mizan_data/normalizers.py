"""
String normalization functions for city and district names.

Handles common variations, Arabic/English mappings, and standardization
for consistent segment key generation.
"""

import re
from typing import Optional

# Riyadh district name mappings (common variations -> canonical)
DISTRICT_ALIASES = {
    # Al Olaya variations
    "olaya": "Al Olaya",
    "al-olaya": "Al Olaya",
    "العليا": "Al Olaya",
    # Al Malqa variations
    "malqa": "Al Malqa",
    "al-malqa": "Al Malqa",
    "malga": "Al Malqa",
    "المالقة": "Al Malqa",
    # Al Nakheel variations
    "nakheel": "Al Nakheel",
    "al-nakheel": "Al Nakheel",
    "النخيل": "Al Nakheel",
    # Al Yasmin variations
    "yasmin": "Al Yasmin",
    "al-yasmin": "Al Yasmin",
    "yasmeen": "Al Yasmin",
    "الياسمين": "Al Yasmin",
    # Al Sahafa variations
    "sahafa": "Al Sahafa",
    "al-sahafa": "Al Sahafa",
    "الصحافة": "Al Sahafa",
    # Al Muruj variations
    "muruj": "Al Muruj",
    "al-muruj": "Al Muruj",
    "المروج": "Al Muruj",
    # Al Rabwah variations
    "rabwah": "Al Rabwah",
    "al-rabwah": "Al Rabwah",
    "الربوة": "Al Rabwah",
    # Al Shifa variations
    "shifa": "Al Shifa",
    "al-shifa": "Al Shifa",
    "الشفا": "Al Shifa",
    # Al Rawdah variations
    "rawdah": "Al Rawdah",
    "al-rawdah": "Al Rawdah",
    "الروضة": "Al Rawdah",
    # Al Sulaimaniyah variations
    "sulaimaniyah": "Al Sulaimaniyah",
    "al-sulaimaniyah": "Al Sulaimaniyah",
    "السليمانية": "Al Sulaimaniyah",
    # Hittin variations
    "hittin": "Hittin",
    "حطين": "Hittin",
    # Al Narjis variations
    "narjis": "Al Narjis",
    "al-narjis": "Al Narjis",
    "النرجس": "Al Narjis",
    # Al Qirawan variations
    "qirawan": "Al Qirawan",
    "al-qirawan": "Al Qirawan",
    "القيروان": "Al Qirawan",
    # Al Mohammadiyah variations
    "mohammadiyah": "Al Mohammadiyah",
    "al-mohammadiyah": "Al Mohammadiyah",
    "المحمدية": "Al Mohammadiyah",
    # Al Woroud variations
    "woroud": "Al Woroud",
    "al-woroud": "Al Woroud",
    "الورود": "Al Woroud",
}

# City name mappings
CITY_ALIASES = {
    "riyadh": "Riyadh",
    "الرياض": "Riyadh",
    "riyad": "Riyadh",
}


def normalize_city(city: str) -> str:
    """
    Normalize city name to canonical form.

    Args:
        city: Raw city name string

    Returns:
        Normalized city name

    Examples:
        >>> normalize_city("riyadh")
        'Riyadh'
        >>> normalize_city("الرياض")
        'Riyadh'
    """
    if not city:
        return city

    # Clean and lowercase for lookup
    cleaned = city.strip().lower()

    # Check aliases
    if cleaned in CITY_ALIASES:
        return CITY_ALIASES[cleaned]

    # Check raw Arabic
    if city.strip() in CITY_ALIASES:
        return CITY_ALIASES[city.strip()]

    # Title case the original if no alias found
    return _title_case_city(city.strip())


def normalize_district(district: str) -> str:
    """
    Normalize district name to canonical form.

    Args:
        district: Raw district name string

    Returns:
        Normalized district name

    Examples:
        >>> normalize_district("al-olaya")
        'Al Olaya'
        >>> normalize_district("العليا")
        'Al Olaya'
    """
    if not district:
        return district

    # Clean and lowercase for lookup
    cleaned = district.strip().lower()
    cleaned = re.sub(r"[-_]+", "-", cleaned)  # Normalize separators

    # Check aliases
    if cleaned in DISTRICT_ALIASES:
        return DISTRICT_ALIASES[cleaned]

    # Check raw Arabic
    if district.strip() in DISTRICT_ALIASES:
        return DISTRICT_ALIASES[district.strip()]

    # Title case and clean up the original if no alias found
    return _title_case_district(district.strip())


def _title_case_city(name: str) -> str:
    """Title case a city name, handling edge cases."""
    return name.title()


def _title_case_district(name: str) -> str:
    """
    Title case a district name, handling 'Al' prefix properly.

    Examples:
        >>> _title_case_district("al wadi")
        'Al Wadi'
    """
    words = name.replace("-", " ").replace("_", " ").split()
    result = []
    for i, word in enumerate(words):
        if i == 0 and word.lower() == "al":
            result.append("Al")
        else:
            result.append(word.capitalize())
    return " ".join(result)


def create_segment_key(
    city: str,
    district: str,
    property_type: str,
    size_bucket: Optional[str] = None,
) -> str:
    """
    Create a canonical segment key for grouping properties.

    Args:
        city: Normalized city name
        district: Normalized district name
        property_type: Property type ('apartment' or 'villa')
        size_bucket: Optional size category

    Returns:
        Canonical segment key string

    Examples:
        >>> create_segment_key("Riyadh", "Al Olaya", "apartment")
        'Riyadh|Al Olaya|apartment'
    """
    parts = [
        normalize_city(city),
        normalize_district(district),
        property_type.lower(),
    ]
    if size_bucket:
        parts.append(size_bucket)
    return "|".join(parts)


def get_size_bucket(area_sqm: float, property_type: str) -> str:
    """
    Categorize property into size bucket.

    Args:
        area_sqm: Property area in square meters
        property_type: 'apartment' or 'villa'

    Returns:
        Size bucket string: 'small', 'medium', 'large', or 'xlarge'
    """
    if property_type.lower() == "apartment":
        # Apartment size buckets
        if area_sqm < 100:
            return "small"
        elif area_sqm < 180:
            return "medium"
        elif area_sqm < 280:
            return "large"
        else:
            return "xlarge"
    else:
        # Villa size buckets
        if area_sqm < 250:
            return "small"
        elif area_sqm < 400:
            return "medium"
        elif area_sqm < 600:
            return "large"
        else:
            return "xlarge"
