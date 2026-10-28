"""
Tests for anchor band computation.
"""

import pytest
import numpy as np
from datetime import date

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mizan_data.schemas import CompRecord, PropertyType
from mizan_models.anchor_bands import AnchorBandBuilder, SegmentBounds, N_MIN


def create_test_comp(
    district: str = "Al Olaya",
    property_type: str = "apartment",
    price_per_sqm: float = 15000,
    area: float = 150,
) -> CompRecord:
    """Helper to create test comp records."""
    return CompRecord(
        trans_date=date(2024, 1, 1),
        city="Riyadh",
        district=district,
        property_type=PropertyType(property_type),
        total_price_sar=price_per_sqm * area,
        area_sqm=area,
        bedrooms=3,
        bathrooms=2,
        year_built=2020,
    )


class TestAnchorBandBuilder:
    """Tests for AnchorBandBuilder class."""

    def test_fit_computes_quantiles(self):
        """Test that fit computes correct quantiles."""
        # Create 20 comps with known prices
        prices = list(range(10000, 30000, 1000))  # 10k to 29k
        comps = [
            create_test_comp(price_per_sqm=p)
            for p in prices
        ]

        builder = AnchorBandBuilder()
        builder.fit(comps)

        # Check that segment band exists
        key = "Riyadh|Al Olaya|apartment"
        assert key in builder.bands

        bounds = builder.bands[key]
        assert bounds.count == 20
        assert bounds.p50 == pytest.approx(np.median(prices), rel=0.01)

    def test_fallback_to_city_level(self):
        """Test fallback when district has insufficient data."""
        # Create < N_MIN comps for one district, more for another
        comps = [
            create_test_comp(district="Al Olaya", price_per_sqm=15000)
            for _ in range(5)  # Less than N_MIN
        ]
        comps += [
            create_test_comp(district="Al Malqa", price_per_sqm=14000)
            for _ in range(20)
        ]

        builder = AnchorBandBuilder()
        builder.fit(comps)

        # Al Olaya should fallback to city level
        bounds, level = builder.get_bounds("Riyadh", "Al Olaya", "apartment")
        assert level == "city"

        # Al Malqa should use segment level
        bounds2, level2 = builder.get_bounds("Riyadh", "Al Malqa", "apartment")
        assert level2 == "segment"

    def test_segment_bounds_reliable_check(self):
        """Test is_reliable property."""
        bounds_small = SegmentBounds(
            segment_key="test",
            count=5,
            p10=1, p25=2, p50=3, p75=4, p90=5,
            mean=3, std=1,
        )
        assert not bounds_small.is_reliable

        bounds_large = SegmentBounds(
            segment_key="test",
            count=N_MIN + 1,
            p10=1, p25=2, p50=3, p75=4, p90=5,
            mean=3, std=1,
        )
        assert bounds_large.is_reliable

    def test_to_dataframe(self):
        """Test export to DataFrame."""
        comps = [
            create_test_comp(price_per_sqm=15000)
            for _ in range(15)
        ]

        builder = AnchorBandBuilder()
        builder.fit(comps)
        df = builder.to_dataframe()

        assert "segment_key" in df.columns
        assert "p10" in df.columns
        assert "p90" in df.columns
        assert len(df) > 0
