"""
Tests for clamping behavior.
"""

import pytest
import numpy as np
from datetime import date

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mizan_data.schemas import CompRecord, SubjectProperty, PropertyType
from mizan_features.builder import FeatureBuilder
from mizan_models.anchor_bands import AnchorBandBuilder
from mizan_models.estimator import MizanEstimator, PredictionResult
from mizan_models.predictor import MizanPredictor


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


def create_test_subject(
    district: str = "Al Olaya",
    property_type: str = "apartment",
    area: float = 150,
) -> SubjectProperty:
    """Helper to create test subject properties."""
    return SubjectProperty(
        property_id="TEST_001",
        city="Riyadh",
        district=district,
        property_type=PropertyType(property_type),
        area_sqm=area,
        bedrooms=3,
        bathrooms=2,
        year_built=2020,
    )


class TestClampBehavior:
    """Tests for prediction clamping to anchor bounds."""

    def test_prediction_clamped_to_bounds(self):
        """Test that predictions are clamped to anchor band bounds."""
        # Create training data with known price range
        prices = [12000, 13000, 14000, 15000, 16000, 17000, 18000, 19000, 20000, 21000,
                  12500, 13500, 14500, 15500, 16500, 17500, 18500, 19500, 20500, 21500]
        comps = [
            create_test_comp(price_per_sqm=p)
            for p in prices
        ]

        # Build components
        feature_builder = FeatureBuilder()
        feature_builder.fit(comps)

        anchor_bands = AnchorBandBuilder()
        anchor_bands.fit(comps)

        model = MizanEstimator(model_type="ridge", random_state=42)
        X, y = feature_builder.transform_comps(comps)
        model.fit(X, y)

        # Create predictor
        predictor = MizanPredictor(model, feature_builder, anchor_bands)

        # Predict
        subject = create_test_subject()
        results = predictor.predict([subject])

        assert len(results) == 1
        result = results[0]

        # Get anchor bounds
        bounds, _ = anchor_bands.get_bounds("Riyadh", "Al Olaya", "apartment")

        # Verify clamping: low >= p10, high <= p90
        assert result.estimated_price_per_sqm_low >= bounds.p10
        assert result.estimated_price_per_sqm_high <= bounds.p90
        # Verify ordering
        assert result.estimated_price_per_sqm_low <= result.estimated_price_per_sqm_mid
        assert result.estimated_price_per_sqm_mid <= result.estimated_price_per_sqm_high

    def test_clamp_applied_flag(self):
        """Test that clamp_applied flag is set correctly."""
        prices = list(range(10000, 25000, 500))
        comps = [create_test_comp(price_per_sqm=p) for p in prices]

        feature_builder = FeatureBuilder()
        feature_builder.fit(comps)

        anchor_bands = AnchorBandBuilder()
        anchor_bands.fit(comps)

        model = MizanEstimator(model_type="ridge", random_state=42)
        X, y = feature_builder.transform_comps(comps)
        model.fit(X, y)

        predictor = MizanPredictor(model, feature_builder, anchor_bands)
        results = predictor.predict([create_test_subject()])

        # Check explanation contains clamp info
        assert "clamping" in results[0].explanation
        assert "applied" in results[0].explanation["clamping"]
