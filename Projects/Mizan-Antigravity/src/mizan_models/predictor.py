"""
Prediction pipeline with clamping to anchor bounds.

Combines model predictions with segment bounds to produce
final valuations with explanations.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

from mizan_data.schemas import SubjectProperty
from mizan_features.builder import FeatureBuilder
from .anchor_bands import AnchorBandBuilder, SegmentBounds
from .estimator import MizanEstimator, PredictionResult
from .confidence import (
    compute_completeness_score,
    compute_segment_support_score,
    compute_confidence_score_with_fallback,
)

logger = logging.getLogger(__name__)


@dataclass
class ValuationResult:
    """Complete valuation result for a property."""

    property_id: str

    # Value estimates in SAR
    estimated_value_sar_low: float
    estimated_value_sar_mid: float
    estimated_value_sar_high: float

    # Price per sqm estimates
    estimated_price_per_sqm_low: float
    estimated_price_per_sqm_mid: float
    estimated_price_per_sqm_high: float

    # Scores
    confidence_score: int  # 0-100
    data_completeness_score: int  # 0-100

    # Explanation
    explanation: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        return {
            "property_id": self.property_id,
            "estimated_value_sar_low": int(self.estimated_value_sar_low),
            "estimated_value_sar_mid": int(self.estimated_value_sar_mid),
            "estimated_value_sar_high": int(self.estimated_value_sar_high),
            "estimated_price_per_sqm_low": int(self.estimated_price_per_sqm_low),
            "estimated_price_per_sqm_mid": int(self.estimated_price_per_sqm_mid),
            "estimated_price_per_sqm_high": int(self.estimated_price_per_sqm_high),
            "confidence_score": self.confidence_score,
            "data_completeness_score": self.data_completeness_score,
            "explanation": self.explanation,
        }


class MizanPredictor:
    """
    Main prediction pipeline for property valuation.

    Combines:
    - Feature building with imputation
    - Model prediction
    - Anchor band clamping
    - Confidence scoring
    - Explanation generation
    """

    def __init__(
        self,
        model: MizanEstimator,
        feature_builder: FeatureBuilder,
        anchor_bands: AnchorBandBuilder,
    ):
        """
        Initialize predictor with trained components.

        Args:
            model: Trained MizanEstimator
            feature_builder: Fitted FeatureBuilder
            anchor_bands: Computed AnchorBandBuilder
        """
        self.model = model
        self.feature_builder = feature_builder
        self.anchor_bands = anchor_bands

    def predict(self, subjects: list[SubjectProperty]) -> list[ValuationResult]:
        """
        Predict valuations for subject properties.

        Args:
            subjects: List of SubjectProperty objects

        Returns:
            List of ValuationResult objects
        """
        # Build features with imputation tracking
        features, imputation_info = self.feature_builder.transform_subjects(subjects)

        # Get model predictions
        predictions = self.model.predict(features)

        # Process each subject
        results = []
        for i, (subject, pred) in enumerate(zip(subjects, predictions)):
            result = self._process_prediction(
                subject=subject,
                prediction=pred,
                imputed_fields=imputation_info.iloc[i],
            )
            results.append(result)

        return results

    def _process_prediction(
        self,
        subject: SubjectProperty,
        prediction: PredictionResult,
        imputed_fields: pd.Series,
    ) -> ValuationResult:
        """Process a single prediction with clamping and scoring."""
        # Get anchor bounds
        bounds, fallback_level = self.anchor_bands.get_bounds(
            city=subject.city,
            district=subject.district,
            property_type=subject.property_type.value,
            area_sqm=subject.area_sqm,
        )

        # Convert model predictions to price_per_sqm
        pred_low = prediction.price_per_sqm_low
        pred_mid = prediction.price_per_sqm_mid
        pred_high = prediction.price_per_sqm_high

        # Clamp to anchor bounds
        clamped_low = max(pred_low, bounds.p10)
        clamped_mid = np.clip(pred_mid, bounds.p25, bounds.p75)
        clamped_high = min(pred_high, bounds.p90)

        # Ensure ordering
        clamped_low = min(clamped_low, clamped_mid)
        clamped_high = max(clamped_high, clamped_mid)

        # Track if clamping was applied
        clamp_applied = (
            pred_low != clamped_low
            or pred_mid != clamped_mid
            or pred_high != clamped_high
        )

        # Compute total values
        area = subject.area_sqm
        value_low = clamped_low * area
        value_mid = clamped_mid * area
        value_high = clamped_high * area

        # Compute scores (with fallback penalty for cities without local data)
        completeness = compute_completeness_score(subject)
        segment_support = compute_segment_support_score(bounds.count)
        confidence = compute_confidence_score_with_fallback(
            completeness_score=completeness,
            segment_support_score=segment_support,
            model_uncertainty=prediction.model_uncertainty,
            fallback_level=fallback_level,
        )

        # Build explanation
        explanation = self._build_explanation(
            subject=subject,
            bounds=bounds,
            fallback_level=fallback_level,
            prediction=prediction,
            clamped=(clamped_low, clamped_mid, clamped_high),
            clamp_applied=clamp_applied,
            imputed_fields=imputed_fields,
        )

        return ValuationResult(
            property_id=subject.property_id or "unknown",
            estimated_value_sar_low=value_low,
            estimated_value_sar_mid=value_mid,
            estimated_value_sar_high=value_high,
            estimated_price_per_sqm_low=clamped_low,
            estimated_price_per_sqm_mid=clamped_mid,
            estimated_price_per_sqm_high=clamped_high,
            confidence_score=confidence,
            data_completeness_score=completeness,
            explanation=explanation,
        )

    def _build_explanation(
        self,
        subject: SubjectProperty,
        bounds: SegmentBounds,
        fallback_level: str,
        prediction: PredictionResult,
        clamped: tuple[float, float, float],
        clamp_applied: bool,
        imputed_fields: pd.Series,
    ) -> dict:
        """Build explanation dictionary."""
        imputed_list = [
            field for field, was_imputed in imputed_fields.items() if was_imputed
        ]

        explanation = {
            "segment": {
                "key": bounds.segment_key,
                "level": fallback_level,
                "count": bounds.count,
                "p10": int(bounds.p10),
                "p50": int(bounds.p50),
                "p90": int(bounds.p90),
            },
            "model_prediction": {
                "price_per_sqm_low": int(prediction.price_per_sqm_low),
                "price_per_sqm_mid": int(prediction.price_per_sqm_mid),
                "price_per_sqm_high": int(prediction.price_per_sqm_high),
            },
            "clamping": {
                "applied": bool(clamp_applied),
                "final_low": int(clamped[0]),
                "final_mid": int(clamped[1]),
                "final_high": int(clamped[2]),
            },
            "imputed_fields": imputed_list,
            "top_drivers": self._get_top_drivers(subject),
        }

        return explanation

    def _get_top_drivers(self, subject: SubjectProperty) -> list[str]:
        """Identify top value drivers for this property."""
        drivers = []

        # Size driver
        if subject.area_sqm >= 300:
            drivers.append(f"Large size ({subject.area_sqm:.0f} sqm)")
        elif subject.area_sqm <= 100:
            drivers.append(f"Compact size ({subject.area_sqm:.0f} sqm)")

        # Age driver
        if subject.age_years is not None:
            if subject.age_years <= 2:
                drivers.append("New construction")
            elif subject.age_years >= 15:
                drivers.append(f"Older property ({subject.age_years} years)")

        # Quality drivers
        if subject.finish_tier is not None and subject.finish_tier >= 4:
            drivers.append("High finish quality")
        if subject.condition_tier is not None and subject.condition_tier >= 4:
            drivers.append("Excellent condition")

        # Amenity drivers
        amenities = []
        if subject.elevator:
            amenities.append("elevator")
        if subject.garden:
            amenities.append("garden")
        if subject.maid_room:
            amenities.append("maid room")
        if subject.private_entrance:
            amenities.append("private entrance")
        if amenities:
            drivers.append(f"Amenities: {', '.join(amenities)}")

        # Location
        drivers.append(f"Location: {subject.district}, {subject.city}")

        return drivers[:5]  # Limit to top 5
