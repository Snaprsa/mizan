"""
Tests for extraction pipeline components.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from extractors.normalizer import (
    extract_number, normalize_arabic_numerals, normalize_currency,
    normalize_city, normalize_date, normalize_area, compute_price_per_sqm,
)
from extractors.confidence import score_confidence, classify_confidence


class TestNormalizer:
    def test_arabic_numerals(self):
        assert normalize_arabic_numerals("٣٥٠٠٠٠٠") == "3500000"
        assert normalize_arabic_numerals("١٢٣.٤٥") == "123.45"

    def test_extract_number_simple(self):
        assert extract_number("3,500,000") == 3500000
        assert extract_number("450") == 450

    def test_extract_number_arabic(self):
        assert extract_number("٣٬٥٠٠٬٠٠٠ ريال") == 3500000

    def test_extract_number_with_currency(self):
        assert extract_number("3,500,000 SAR") == 3500000
        assert extract_number("SAR 1,250,000") == 1250000

    def test_extract_number_none(self):
        assert extract_number("") is None
        assert extract_number("no numbers here") is None

    def test_normalize_currency(self):
        assert normalize_currency("ريال") == "SAR"
        assert normalize_currency("SAR") == "SAR"
        assert normalize_currency("ر.س") == "SAR"
        assert normalize_currency("USD") == "USD"
        assert normalize_currency("") == "SAR"  # Default

    def test_normalize_area_sqft_to_sqm(self):
        val, unit = normalize_area(1000, "sqft")
        assert unit == "sqm"
        assert 92 < val < 94  # ~92.9

    def test_normalize_area_sqm_passthrough(self):
        val, unit = normalize_area(450, "sqm")
        assert val == 450
        assert unit == "sqm"

    def test_normalize_city_arabic(self):
        en, ar = normalize_city("الرياض")
        assert en == "Riyadh"
        assert ar == "الرياض"

    def test_normalize_city_english(self):
        en, ar = normalize_city("Jeddah")
        assert en == "Jeddah"
        assert ar == "جدة"

    def test_normalize_city_unknown(self):
        en, ar = normalize_city("SomeNewCity")
        assert en == "SomeNewCity"
        assert ar is None

    def test_normalize_date_iso(self):
        assert normalize_date("2025-01-15") == "2025-01-15"

    def test_normalize_date_slash(self):
        result = normalize_date("15/01/2025")
        assert result == "2025-01-15"

    def test_normalize_date_invalid(self):
        assert normalize_date("not a date") is None

    def test_compute_price_per_sqm(self):
        assert compute_price_per_sqm(3500000, 450) == pytest.approx(7777.78, rel=0.01)

    def test_compute_price_per_sqm_none(self):
        assert compute_price_per_sqm(None, 450) is None
        assert compute_price_per_sqm(3500000, 0) is None
        assert compute_price_per_sqm(3500000, None) is None


class TestConfidence:
    def test_high_confidence(self):
        score = score_confidence(0.95, source_reliability=5)
        assert score >= 0.9

    def test_low_reliability_reduces_confidence(self):
        high = score_confidence(0.9, source_reliability=5)
        low = score_confidence(0.9, source_reliability=1)
        assert high > low

    def test_llm_blending(self):
        without_llm = score_confidence(0.8, source_reliability=3)
        with_llm = score_confidence(0.8, source_reliability=3, llm_confidence=0.9)
        # LLM should slightly change the score
        assert without_llm != with_llm

    def test_crosscheck_boost(self):
        base = score_confidence(0.7, source_reliability=3)
        boosted = score_confidence(0.7, source_reliability=3, crosscheck_confidence=0.9)
        assert boosted > base

    def test_clamped_to_range(self):
        score = score_confidence(1.0, source_reliability=5, crosscheck_confidence=1.0)
        assert 0.0 <= score <= 1.0

    def test_classify_high(self):
        assert classify_confidence(0.85) == "high"

    def test_classify_medium(self):
        assert classify_confidence(0.6) == "medium"

    def test_classify_low(self):
        assert classify_confidence(0.3) == "low"
