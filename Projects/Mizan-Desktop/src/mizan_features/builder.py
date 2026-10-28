"""
Feature engineering for property valuation.

Builds feature matrices from property records, handles encoding,
imputation, and transformation.
"""

import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

import numpy as np
import pandas as pd

from mizan_data.schemas import CompRecord, SubjectProperty, PropertyType, FIELD_WEIGHTS

logger = logging.getLogger(__name__)


@dataclass
class FeatureConfig:
    """Configuration for feature building."""

    # Imputation defaults by property type
    default_age_years: int = 5
    default_finish_tier: int = 3
    default_condition_tier: int = 3

    # Encoding settings
    encoding_smoothing: float = 10.0  # Smoothing factor for target encoding

    # Feature list for model
    numeric_features: list[str] = field(
        default_factory=lambda: [
            "log_area",
            "age_years",
            "bedrooms",
            "bathrooms",
            "parking_count",
            "floor_level",
            "finish_tier",
            "condition_tier",
        ]
    )

    binary_features: list[str] = field(
        default_factory=lambda: [
            "elevator",
            "central_ac",
            "maid_room",
            "garden",
            "private_entrance",
            "is_villa",
        ]
    )


class FeatureBuilder:
    """
    Builds feature matrices for training and prediction.

    Handles:
    - Log transformation of area
    - Age computation from year_built
    - Target encoding for districts
    - Missing value imputation with tracking
    """

    def __init__(self, config: Optional[FeatureConfig] = None):
        self.config = config or FeatureConfig()
        self.district_encoder: Optional[dict[str, float]] = None
        self.global_mean_log_price: float = 0.0
        self._fitted = False

    def fit(self, comps: list[CompRecord]) -> "FeatureBuilder":
        """
        Fit the feature builder on training data.

        Computes district target encodings and stores global statistics.

        Args:
            comps: List of comparable sale records

        Returns:
            Self for chaining
        """
        df = self._comps_to_df(comps)

        # Compute target encoding for districts
        self.district_encoder = self._compute_target_encoding(
            df, "district", "log_price_per_sqm"
        )

        # Store global mean
        self.global_mean_log_price = df["log_price_per_sqm"].mean()

        self._fitted = True
        logger.info(
            f"Fitted FeatureBuilder on {len(comps)} records, "
            f"{len(self.district_encoder)} districts"
        )
        return self

    def transform_comps(
        self, comps: list[CompRecord]
    ) -> tuple[pd.DataFrame, pd.Series]:
        """
        Transform comparable sales to feature matrix and target.

        Args:
            comps: List of comparable sale records

        Returns:
            Tuple of (feature_matrix, target_series)
            - feature_matrix: DataFrame with all features
            - target_series: log(price_per_sqm) values
        """
        if not self._fitted:
            raise ValueError("FeatureBuilder must be fitted before transform")

        df = self._comps_to_df(comps)
        features = self._build_features(df)
        target = df["log_price_per_sqm"]

        return features, target

    def transform_subjects(
        self, subjects: list[SubjectProperty]
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Transform subject properties to feature matrix with imputation tracking.

        Args:
            subjects: List of subject properties

        Returns:
            Tuple of (feature_matrix, imputation_info)
            - feature_matrix: DataFrame with all features
            - imputation_info: DataFrame tracking which fields were imputed
        """
        if not self._fitted:
            raise ValueError("FeatureBuilder must be fitted before transform")

        df = self._subjects_to_df(subjects)
        features, imputation_info = self._build_features_with_imputation(df)

        return features, imputation_info

    def _comps_to_df(self, comps: list[CompRecord]) -> pd.DataFrame:
        """Convert comp records to DataFrame with computed columns."""
        records = []
        for comp in comps:
            rec = comp.model_dump()
            rec["price_per_sqm"] = comp.price_per_sqm
            rec["computed_age_years"] = comp.computed_age_years
            records.append(rec)

        df = pd.DataFrame(records)
        df["log_price_per_sqm"] = np.log(df["price_per_sqm"])
        df["log_area"] = np.log(df["area_sqm"])
        df["is_villa"] = (df["property_type"] == "villa").astype(int)
        df["age_years"] = df["computed_age_years"]

        return df

    def _subjects_to_df(self, subjects: list[SubjectProperty]) -> pd.DataFrame:
        """Convert subject properties to DataFrame."""
        records = [subj.model_dump() for subj in subjects]
        df = pd.DataFrame(records)
        df["log_area"] = np.log(df["area_sqm"])
        df["is_villa"] = (df["property_type"] == "villa").astype(int)

        return df

    def _compute_target_encoding(
        self,
        df: pd.DataFrame,
        column: str,
        target: str,
    ) -> dict[str, float]:
        """
        Compute smoothed target encoding for a categorical column.

        Uses additive smoothing: (sum_target + m * global_mean) / (count + m)
        where m is the smoothing factor.
        """
        global_mean = df[target].mean()
        m = self.config.encoding_smoothing

        encoding = {}
        for value, group in df.groupby(column):
            count = len(group)
            sum_target = group[target].sum()
            smoothed = (sum_target + m * global_mean) / (count + m)
            encoding[value] = smoothed

        return encoding

    def _build_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Build feature matrix from DataFrame (for comps with complete data)."""
        features = pd.DataFrame(index=df.index)

        # Numeric features
        for feat in self.config.numeric_features:
            if feat in df.columns:
                features[feat] = df[feat].fillna(self._get_default(feat)).infer_objects(copy=False)
            else:
                features[feat] = self._get_default(feat)

        # Binary features
        for feat in self.config.binary_features:
            if feat in df.columns:
                features[feat] = df[feat].fillna(0).astype(int)
            else:
                features[feat] = 0

        # District encoding
        features["district_encoded"] = df["district"].map(self.district_encoder)
        features["district_encoded"] = features["district_encoded"].fillna(
            self.global_mean_log_price
        )

        return features

    def _build_features_with_imputation(
        self, df: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Build features with imputation tracking for subjects."""
        features = pd.DataFrame(index=df.index)
        imputed = pd.DataFrame(index=df.index)

        # Compute age_years from year_built if not provided
        if "age_years" not in df.columns or df["age_years"].isna().any():
            current_year = date.today().year
            df["age_years"] = df.apply(
                lambda row: (
                    row["age_years"]
                    if pd.notna(row.get("age_years"))
                    else (
                        current_year - row["year_built"]
                        if pd.notna(row.get("year_built"))
                        else None
                    )
                ),
                axis=1,
            )

        # Numeric features with imputation tracking
        for feat in self.config.numeric_features:
            if feat in df.columns:
                mask = df[feat].isna()
                features[feat] = df[feat].fillna(self._get_default(feat, df)).infer_objects(copy=False)
                imputed[feat] = mask
            else:
                features[feat] = self._get_default(feat, df)
                imputed[feat] = True

        # Binary features with property-type-aware defaults
        for feat in self.config.binary_features:
            if feat in df.columns:
                mask = df[feat].isna()
                default = self._get_binary_default(feat, df)
                features[feat] = df[feat].fillna(default).infer_objects(copy=False).astype(int)
                imputed[feat] = mask
            else:
                features[feat] = self._get_binary_default(feat, df)
                imputed[feat] = True

        # District encoding
        features["district_encoded"] = df["district"].map(self.district_encoder)
        unknown_districts = features["district_encoded"].isna()
        features["district_encoded"] = features["district_encoded"].fillna(
            self.global_mean_log_price
        )
        imputed["district_encoded"] = unknown_districts

        return features, imputed

    def _get_default(self, feature: str, df: Optional[pd.DataFrame] = None) -> float:
        """Get default value for a numeric feature."""
        defaults = {
            "log_area": np.log(150),  # ~150 sqm default
            "age_years": self.config.default_age_years,
            "bedrooms": 3,
            "bathrooms": 2,
            "parking_count": 1,
            "floor_level": 0,
            "finish_tier": self.config.default_finish_tier,
            "condition_tier": self.config.default_condition_tier,
        }
        return defaults.get(feature, 0)

    def _get_binary_default(
        self, feature: str, df: Optional[pd.DataFrame] = None
    ) -> pd.Series | int:
        """Get property-type-aware default for binary features."""
        if df is None:
            return 0

        is_villa = df.get("is_villa", pd.Series([0] * len(df)))

        # Property-type-aware defaults
        if feature == "elevator":
            # Apartments more likely to have elevators
            return (~is_villa.astype(bool)).astype(int)
        elif feature == "garden":
            # Villas more likely to have gardens
            return is_villa.astype(int)
        elif feature == "private_entrance":
            # Villas more likely to have private entrance
            return is_villa.astype(int)
        elif feature == "central_ac":
            # Most properties have central AC in Riyadh
            return 1
        else:
            return 0

    def get_feature_names(self) -> list[str]:
        """Get list of all feature names in order."""
        return (
            self.config.numeric_features
            + self.config.binary_features
            + ["district_encoded"]
        )

    def save_state(self) -> dict:
        """Save encoder state for persistence."""
        return {
            "district_encoder": self.district_encoder,
            "global_mean_log_price": self.global_mean_log_price,
            "config": {
                "default_age_years": self.config.default_age_years,
                "default_finish_tier": self.config.default_finish_tier,
                "default_condition_tier": self.config.default_condition_tier,
                "encoding_smoothing": self.config.encoding_smoothing,
            },
        }

    def load_state(self, state: dict) -> "FeatureBuilder":
        """Load encoder state from saved dict."""
        self.district_encoder = state["district_encoder"]
        self.global_mean_log_price = state["global_mean_log_price"]
        if "config" in state:
            self.config.default_age_years = state["config"]["default_age_years"]
            self.config.default_finish_tier = state["config"]["default_finish_tier"]
            self.config.default_condition_tier = state["config"]["default_condition_tier"]
            self.config.encoding_smoothing = state["config"]["encoding_smoothing"]
        self._fitted = True
        return self


def build_features(
    comps: list[CompRecord],
    subjects: Optional[list[SubjectProperty]] = None,
) -> tuple[pd.DataFrame, pd.Series, Optional[pd.DataFrame], FeatureBuilder]:
    """
    Convenience function to build features for training and optionally prediction.

    Args:
        comps: List of comparable sales for training
        subjects: Optional list of subject properties for prediction

    Returns:
        Tuple of (X_train, y_train, X_subjects, feature_builder)
    """
    builder = FeatureBuilder()
    builder.fit(comps)

    X_train, y_train = builder.transform_comps(comps)

    X_subjects = None
    if subjects:
        X_subjects, _ = builder.transform_subjects(subjects)

    return X_train, y_train, X_subjects, builder
