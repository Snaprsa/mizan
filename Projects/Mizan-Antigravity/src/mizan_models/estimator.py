"""
Model estimators for property valuation.

Provides Ridge regression baseline and HistGradientBoosting alternative
for predicting log(price_per_sqm) with uncertainty quantification.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import cross_val_predict
import joblib

logger = logging.getLogger(__name__)


@dataclass
class PredictionResult:
    """Result of a single property prediction."""

    log_price_per_sqm_mid: float
    log_price_per_sqm_low: float
    log_price_per_sqm_high: float
    model_uncertainty: float  # Standard deviation of prediction

    @property
    def price_per_sqm_mid(self) -> float:
        return np.exp(self.log_price_per_sqm_mid)

    @property
    def price_per_sqm_low(self) -> float:
        return np.exp(self.log_price_per_sqm_low)

    @property
    def price_per_sqm_high(self) -> float:
        return np.exp(self.log_price_per_sqm_high)


class BaseEstimator(ABC):
    """Abstract base class for valuation estimators."""

    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series) -> "BaseEstimator":
        """Fit the model on training data."""
        pass

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> list[PredictionResult]:
        """Make predictions with uncertainty."""
        pass

    @abstractmethod
    def save(self, filepath: str) -> None:
        """Save model to file."""
        pass

    @classmethod
    @abstractmethod
    def load(cls, filepath: str) -> "BaseEstimator":
        """Load model from file."""
        pass


class RidgeEstimator(BaseEstimator):
    """
    Ridge regression estimator for property valuation.

    Uses cross-validated residuals to estimate prediction uncertainty.
    """

    def __init__(self, alpha: float = 1.0, random_state: int = 42):
        """
        Initialize Ridge estimator.

        Args:
            alpha: Regularization strength
            random_state: Random seed for reproducibility
        """
        self.alpha = alpha
        self.random_state = random_state
        self.model: Optional[Ridge] = None
        self.residual_std: float = 0.0
        self.feature_names: list[str] = []

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "RidgeEstimator":
        """
        Fit Ridge regression model.

        Args:
            X: Feature matrix
            y: Target values (log_price_per_sqm)

        Returns:
            Self for chaining
        """
        self.feature_names = list(X.columns)

        # Fit main model
        self.model = Ridge(alpha=self.alpha, random_state=self.random_state)
        self.model.fit(X, y)

        # Compute residual std from cross-validation
        cv_preds = cross_val_predict(
            Ridge(alpha=self.alpha, random_state=self.random_state),
            X,
            y,
            cv=5,
        )
        residuals = y - cv_preds
        self.residual_std = float(residuals.std())

        logger.info(
            f"Fitted RidgeEstimator: residual_std={self.residual_std:.4f}, "
            f"n_features={len(self.feature_names)}"
        )
        return self

    def predict(self, X: pd.DataFrame) -> list[PredictionResult]:
        """
        Make predictions with uncertainty intervals.

        Args:
            X: Feature matrix for subjects

        Returns:
            List of PredictionResult objects
        """
        if self.model is None:
            raise ValueError("Model not fitted")

        # Ensure features are in correct order
        X = X[self.feature_names]

        preds = self.model.predict(X)
        results = []

        for pred in preds:
            # Use 1.5 * residual_std for approximate 80% interval
            margin = 1.5 * self.residual_std
            results.append(
                PredictionResult(
                    log_price_per_sqm_mid=float(pred),
                    log_price_per_sqm_low=float(pred - margin),
                    log_price_per_sqm_high=float(pred + margin),
                    model_uncertainty=self.residual_std,
                )
            )

        return results

    def get_feature_importance(self) -> dict[str, float]:
        """Get feature importance from model coefficients."""
        if self.model is None:
            raise ValueError("Model not fitted")
        return dict(zip(self.feature_names, np.abs(self.model.coef_)))

    def save(self, filepath: str) -> None:
        """Save model state to file."""
        state = {
            "model": self.model,
            "residual_std": self.residual_std,
            "feature_names": self.feature_names,
            "alpha": self.alpha,
            "random_state": self.random_state,
            "type": "ridge",
        }
        joblib.dump(state, filepath)
        logger.info(f"Saved RidgeEstimator to {filepath}")

    @classmethod
    def load(cls, filepath: str) -> "RidgeEstimator":
        """Load model from file."""
        state = joblib.load(filepath)
        estimator = cls(alpha=state["alpha"], random_state=state["random_state"])
        estimator.model = state["model"]
        estimator.residual_std = state["residual_std"]
        estimator.feature_names = state["feature_names"]
        logger.info(f"Loaded RidgeEstimator from {filepath}")
        return estimator


class HistGradientBoostingEstimator(BaseEstimator):
    """
    HistGradientBoosting estimator with built-in quantile regression.

    Trains separate models for low, mid, and high quantiles to provide
    native uncertainty intervals.
    """

    def __init__(
        self,
        max_iter: int = 100,
        max_depth: int = 6,
        learning_rate: float = 0.1,
        random_state: int = 42,
    ):
        """
        Initialize HistGradientBoosting estimator.

        Args:
            max_iter: Maximum number of boosting iterations
            max_depth: Maximum tree depth
            learning_rate: Learning rate
            random_state: Random seed for reproducibility
        """
        self.max_iter = max_iter
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.random_state = random_state

        self.model_mid: Optional[HistGradientBoostingRegressor] = None
        self.model_low: Optional[HistGradientBoostingRegressor] = None
        self.model_high: Optional[HistGradientBoostingRegressor] = None
        self.feature_names: list[str] = []

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "HistGradientBoostingEstimator":
        """
        Fit quantile regression models.

        Args:
            X: Feature matrix
            y: Target values (log_price_per_sqm)

        Returns:
            Self for chaining
        """
        self.feature_names = list(X.columns)
        X_arr = X.values
        y_arr = y.values

        # Median (50th percentile)
        self.model_mid = HistGradientBoostingRegressor(
            loss="squared_error",
            max_iter=self.max_iter,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            random_state=self.random_state,
        )
        self.model_mid.fit(X_arr, y_arr)

        # 10th percentile (low)
        self.model_low = HistGradientBoostingRegressor(
            loss="quantile",
            quantile=0.1,
            max_iter=self.max_iter,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            random_state=self.random_state,
        )
        self.model_low.fit(X_arr, y_arr)

        # 90th percentile (high)
        self.model_high = HistGradientBoostingRegressor(
            loss="quantile",
            quantile=0.9,
            max_iter=self.max_iter,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            random_state=self.random_state,
        )
        self.model_high.fit(X_arr, y_arr)

        logger.info(
            f"Fitted HistGradientBoostingEstimator: n_features={len(self.feature_names)}"
        )
        return self

    def predict(self, X: pd.DataFrame) -> list[PredictionResult]:
        """
        Make predictions with quantile-based uncertainty intervals.

        Args:
            X: Feature matrix for subjects

        Returns:
            List of PredictionResult objects
        """
        if self.model_mid is None:
            raise ValueError("Model not fitted")

        # Ensure features are in correct order
        X = X[self.feature_names]
        X_arr = X.values

        preds_mid = self.model_mid.predict(X_arr)
        preds_low = self.model_low.predict(X_arr)
        preds_high = self.model_high.predict(X_arr)

        results = []
        for mid, low, high in zip(preds_mid, preds_low, preds_high):
            # Estimate uncertainty as half the interval width in log space
            uncertainty = (high - low) / 2
            results.append(
                PredictionResult(
                    log_price_per_sqm_mid=float(mid),
                    log_price_per_sqm_low=float(low),
                    log_price_per_sqm_high=float(high),
                    model_uncertainty=float(uncertainty),
                )
            )

        return results

    def save(self, filepath: str) -> None:
        """Save model state to file."""
        state = {
            "model_mid": self.model_mid,
            "model_low": self.model_low,
            "model_high": self.model_high,
            "feature_names": self.feature_names,
            "max_iter": self.max_iter,
            "max_depth": self.max_depth,
            "learning_rate": self.learning_rate,
            "random_state": self.random_state,
            "type": "hgb",
        }
        joblib.dump(state, filepath)
        logger.info(f"Saved HistGradientBoostingEstimator to {filepath}")

    @classmethod
    def load(cls, filepath: str) -> "HistGradientBoostingEstimator":
        """Load model from file."""
        state = joblib.load(filepath)
        estimator = cls(
            max_iter=state["max_iter"],
            max_depth=state["max_depth"],
            learning_rate=state["learning_rate"],
            random_state=state["random_state"],
        )
        estimator.model_mid = state["model_mid"]
        estimator.model_low = state["model_low"]
        estimator.model_high = state["model_high"]
        estimator.feature_names = state["feature_names"]
        logger.info(f"Loaded HistGradientBoostingEstimator from {filepath}")
        return estimator


class MizanEstimator:
    """
    Unified estimator interface that wraps Ridge or HGB models.

    Provides a consistent API regardless of underlying model type.
    """

    def __init__(self, model_type: str = "ridge", **kwargs):
        """
        Initialize Mizan estimator.

        Args:
            model_type: 'ridge' or 'hgb'
            **kwargs: Arguments passed to underlying estimator
        """
        self.model_type = model_type
        if model_type == "ridge":
            self.estimator = RidgeEstimator(**kwargs)
        elif model_type == "hgb":
            self.estimator = HistGradientBoostingEstimator(**kwargs)
        else:
            raise ValueError(f"Unknown model type: {model_type}")

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "MizanEstimator":
        """Fit the underlying estimator."""
        self.estimator.fit(X, y)
        return self

    def predict(self, X: pd.DataFrame) -> list[PredictionResult]:
        """Make predictions with the underlying estimator."""
        return self.estimator.predict(X)

    def save(self, filepath: str) -> None:
        """Save model to file."""
        self.estimator.save(filepath)

    @classmethod
    def load(cls, filepath: str) -> "MizanEstimator":
        """Load model from file."""
        state = joblib.load(filepath)
        model_type = state.get("type", "ridge")

        wrapper = cls.__new__(cls)
        wrapper.model_type = model_type

        if model_type == "ridge":
            wrapper.estimator = RidgeEstimator.load(filepath)
        else:
            wrapper.estimator = HistGradientBoostingEstimator.load(filepath)

        return wrapper
