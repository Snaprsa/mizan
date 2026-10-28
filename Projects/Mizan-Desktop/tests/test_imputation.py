"""
Tests for missing value imputation.
"""

import pytest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mizan_data.schemas import SubjectProperty, PropertyType
from mizan_models.confidence import (
    compute_completeness_score,
    compute_segment_support_score,
    compute_confidence_score,
)


class TestCompletenessScore:
    """Tests for completeness score computation."""

    def test_complete_property_high_score(self):
        """Test that complete properties get high completeness scores."""
        subject = SubjectProperty(
            property_id="TEST",
            city="Riyadh",
            district="Al Olaya",
            property_type=PropertyType.APARTMENT,
            area_sqm=150,
            bedrooms=3,
            bathrooms=2,
            parking_count=1,
            floor_level=5,
            year_built=2020,
            finish_tier=4,
            condition_tier=4,
            elevator=1,
            central_ac=1,
            maid_room=0,
            garden=0,
            private_entrance=0,
        )

        score = compute_completeness_score(subject)
        assert score >= 90

    def test_minimal_property_low_score(self):
        """Test that minimal properties get lower completeness scores."""
        subject = SubjectProperty(
            property_id="TEST",
            city="Riyadh",
            district="Al Olaya",
            property_type=PropertyType.APARTMENT,
            area_sqm=150,
            # All other fields are None
        )

        score = compute_completeness_score(subject)
        assert score < 70
        assert score > 30  # Should still have base score from required fields

    def test_age_field_counted_once(self):
        """Test that year_built or age_years counts, not both."""
        subject_with_year = SubjectProperty(
            property_id="TEST",
            city="Riyadh",
            district="Al Olaya",
            property_type=PropertyType.APARTMENT,
            area_sqm=150,
            year_built=2020,
        )

        subject_with_age = SubjectProperty(
            property_id="TEST",
            city="Riyadh",
            district="Al Olaya",
            property_type=PropertyType.APARTMENT,
            area_sqm=150,
            age_years=4,
        )

        score1 = compute_completeness_score(subject_with_year)
        score2 = compute_completeness_score(subject_with_age)

        # Both should have similar scores
        assert abs(score1 - score2) < 5


class TestSegmentSupportScore:
    """Tests for segment support score."""

    def test_low_count_low_score(self):
        """Test that low sample counts give low scores."""
        score = compute_segment_support_score(5)
        assert score < 50

    def test_high_count_full_score(self):
        """Test that high sample counts give full score."""
        score = compute_segment_support_score(100)
        assert score == 100

    def test_threshold_behavior(self):
        """Test behavior around N_MIN threshold."""
        from mizan_models.confidence import N_MIN

        score_below = compute_segment_support_score(N_MIN - 1)
        score_at = compute_segment_support_score(N_MIN)
        score_above = compute_segment_support_score(N_MIN + 10)

        assert score_below < 100
        assert score_at == 100
        assert score_above == 100


class TestCombinedConfidence:
    """Tests for combined confidence score."""

    def test_combined_score_range(self):
        """Test that combined score is in valid range."""
        score = compute_confidence_score(
            completeness_score=80,
            segment_support_score=60,
            model_uncertainty=0.2,
        )
        assert 0 <= score <= 100

    def test_uncertainty_impact(self):
        """Test that higher uncertainty lowers score."""
        score_low_uncertainty = compute_confidence_score(
            completeness_score=80,
            segment_support_score=80,
            model_uncertainty=0.1,
        )

        score_high_uncertainty = compute_confidence_score(
            completeness_score=80,
            segment_support_score=80,
            model_uncertainty=0.5,
        )

        assert score_low_uncertainty > score_high_uncertainty
