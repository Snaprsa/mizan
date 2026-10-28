"""
Tests for deterministic outputs.
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
from mizan_models.estimator import MizanEstimator
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


def create_test_subject() -> SubjectProperty:
    """Helper to create test subject properties."""
    return SubjectProperty(
        property_id="TEST_001",
        city="Riyadh",
        district="Al Olaya",
        property_type=PropertyType.APARTMENT,
        area_sqm=150,
        bedrooms=3,
        bathrooms=2,
        year_built=2020,
    )


class TestDeterminism:
    """Tests for reproducibility and determinism."""

    def test_same_seed_same_output(self):
        """Test that same seed produces identical outputs."""
        prices = list(range(10000, 25000, 500))
        comps = [create_test_comp(price_per_sqm=p) for p in prices]

        # First run
        np.random.seed(42)
        fb1 = FeatureBuilder()
        fb1.fit(comps)
        X1, y1 = fb1.transform_comps(comps)

        model1 = MizanEstimator(model_type="ridge", random_state=42)
        model1.fit(X1, y1)

        anchor1 = AnchorBandBuilder()
        anchor1.fit(comps)

        predictor1 = MizanPredictor(model1, fb1, anchor1)
        results1 = predictor1.predict([create_test_subject()])

        # Second run with same seed
        np.random.seed(42)
        fb2 = FeatureBuilder()
        fb2.fit(comps)
        X2, y2 = fb2.transform_comps(comps)

        model2 = MizanEstimator(model_type="ridge", random_state=42)
        model2.fit(X2, y2)

        anchor2 = AnchorBandBuilder()
        anchor2.fit(comps)

        predictor2 = MizanPredictor(model2, fb2, anchor2)
        results2 = predictor2.predict([create_test_subject()])

        # Compare outputs
        assert results1[0].estimated_value_sar_mid == results2[0].estimated_value_sar_mid
        assert results1[0].confidence_score == results2[0].confidence_score

    def test_multiple_predictions_same_results(self):
        """Test that predicting the same property multiple times gives same results."""
        prices = list(range(10000, 25000, 500))
        comps = [create_test_comp(price_per_sqm=p) for p in prices]

        np.random.seed(42)
        fb = FeatureBuilder()
        fb.fit(comps)
        X, y = fb.transform_comps(comps)

        model = MizanEstimator(model_type="ridge", random_state=42)
        model.fit(X, y)

        anchor = AnchorBandBuilder()
        anchor.fit(comps)

        predictor = MizanPredictor(model, fb, anchor)
        subject = create_test_subject()

        results_a = predictor.predict([subject])
        results_b = predictor.predict([subject])
        results_c = predictor.predict([subject])

        assert results_a[0].estimated_value_sar_mid == results_b[0].estimated_value_sar_mid
        assert results_b[0].estimated_value_sar_mid == results_c[0].estimated_value_sar_mid

    def test_hgb_determinism(self):
        """Test that HistGradientBoosting is also deterministic."""
        prices = list(range(10000, 25000, 500))
        comps = [create_test_comp(price_per_sqm=p) for p in prices]

        np.random.seed(42)
        fb = FeatureBuilder()
        fb.fit(comps)
        X, y = fb.transform_comps(comps)

        # First run
        model1 = MizanEstimator(model_type="hgb", random_state=42)
        model1.fit(X, y)
        preds1 = model1.predict(X)

        # Second run
        model2 = MizanEstimator(model_type="hgb", random_state=42)
        model2.fit(X, y)
        preds2 = model2.predict(X)

        # Compare
        for p1, p2 in zip(preds1, preds2):
            assert p1.log_price_per_sqm_mid == pytest.approx(p2.log_price_per_sqm_mid)
