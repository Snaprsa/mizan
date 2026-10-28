"""
Training CLI for Mizan valuation model.

Usage:
    python -m mizan_cli.train --comps data/raw/comps.csv [--model-type ridge|hgb]
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

import click
import pandas as pd
import numpy as np

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mizan_data import load_comps
from mizan_features.builder import FeatureBuilder
from mizan_models.anchor_bands import AnchorBandBuilder
from mizan_models.estimator import MizanEstimator
import joblib

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--comps",
    required=True,
    type=click.Path(exists=True),
    help="Path to comps.csv file",
)
@click.option(
    "--model-type",
    type=click.Choice(["ridge", "hgb"]),
    default="ridge",
    help="Model type: ridge (default) or hgb (HistGradientBoosting)",
)
@click.option(
    "--output-dir",
    type=click.Path(),
    default="models",
    help="Output directory for trained artifacts",
)
@click.option(
    "--validation-split",
    type=float,
    default=0.2,
    help="Fraction of data to use for validation (time-based split)",
)
@click.option(
    "--seed",
    type=int,
    default=42,
    help="Random seed for reproducibility",
)
def train(
    comps: str,
    model_type: str,
    output_dir: str,
    validation_split: float,
    seed: int,
):
    """Train the Mizan valuation model."""
    np.random.seed(seed)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load data
    logger.info(f"Loading comps from {comps}")
    comp_records, invalid = load_comps(comps, validate=True, skip_invalid=True)

    if len(invalid) > 0:
        logger.warning(f"Skipped {len(invalid)} invalid records")

    if len(comp_records) < 10:
        logger.error(f"Insufficient data: only {len(comp_records)} valid records")
        sys.exit(1)

    logger.info(f"Loaded {len(comp_records)} valid comparable sales")

    # Time-based train/validation split
    sorted_comps = sorted(comp_records, key=lambda x: x.trans_date)
    split_idx = int(len(sorted_comps) * (1 - validation_split))
    train_comps = sorted_comps[:split_idx]
    val_comps = sorted_comps[split_idx:]

    logger.info(f"Train set: {len(train_comps)}, Validation set: {len(val_comps)}")

    # Build features
    logger.info("Building features...")
    feature_builder = FeatureBuilder()
    feature_builder.fit(train_comps)

    X_train, y_train = feature_builder.transform_comps(train_comps)
    X_val, y_val = feature_builder.transform_comps(val_comps)

    logger.info(f"Feature matrix shape: {X_train.shape}")

    # Build anchor bands
    logger.info("Computing anchor bands...")
    anchor_builder = AnchorBandBuilder(use_size_bucket=False)
    anchor_builder.fit(train_comps)

    # Train model
    logger.info(f"Training {model_type} model...")
    model = MizanEstimator(model_type=model_type, random_state=seed)
    model.fit(X_train, y_train)

    # Evaluate on validation set
    logger.info("Evaluating on validation set...")
    val_preds = model.predict(X_val)

    # Convert predictions to DataFrames for metrics
    y_val_arr = y_val.values
    y_pred_mid = np.array([p.log_price_per_sqm_mid for p in val_preds])

    # Metrics in log space
    mae_log = np.mean(np.abs(y_val_arr - y_pred_mid))
    rmse_log = np.sqrt(np.mean((y_val_arr - y_pred_mid) ** 2))

    # Convert to price space
    y_val_price = np.exp(y_val_arr)
    y_pred_price = np.exp(y_pred_mid)
    mae_price = np.mean(np.abs(y_val_price - y_pred_price))
    mape = np.mean(np.abs(y_val_price - y_pred_price) / y_val_price) * 100

    # Compute total price metrics
    val_areas = np.array([c.area_sqm for c in val_comps])
    val_total_actual = y_val_price * val_areas
    val_total_pred = y_pred_price * val_areas
    mae_total = np.mean(np.abs(val_total_actual - val_total_pred))
    mape_total = np.mean(np.abs(val_total_actual - val_total_pred) / val_total_actual) * 100

    # Print metrics
    metrics = {
        "mae_log_price_per_sqm": float(mae_log),
        "rmse_log_price_per_sqm": float(rmse_log),
        "mae_price_per_sqm": float(mae_price),
        "mape_price_per_sqm": float(mape),
        "mae_total_price": float(mae_total),
        "mape_total_price": float(mape_total),
        "n_train": len(train_comps),
        "n_val": len(val_comps),
        "model_type": model_type,
        "timestamp": datetime.now().isoformat(),
    }

    logger.info("=" * 50)
    logger.info("VALIDATION METRICS")
    logger.info("=" * 50)
    logger.info(f"MAE (log price/sqm):     {mae_log:.4f}")
    logger.info(f"RMSE (log price/sqm):    {rmse_log:.4f}")
    logger.info(f"MAE (price/sqm SAR):     {mae_price:,.0f}")
    logger.info(f"MAPE (price/sqm):        {mape:.2f}%")
    logger.info(f"MAE (total price SAR):   {mae_total:,.0f}")
    logger.info(f"MAPE (total price):      {mape_total:.2f}%")
    logger.info("=" * 50)

    # Save artifacts
    model_path = output_path / "model.joblib"
    anchor_path = output_path / "anchor_bands.parquet"
    feature_state_path = output_path / "feature_builder.joblib"
    metrics_path = output_path / "metrics.json"

    model.save(str(model_path))
    anchor_builder.save(str(anchor_path))
    joblib.dump(feature_builder.save_state(), feature_state_path)

    import json
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Saved model to {model_path}")
    logger.info(f"Saved anchor bands to {anchor_path}")
    logger.info(f"Saved feature builder to {feature_state_path}")
    logger.info(f"Saved metrics to {metrics_path}")
    logger.info("Training complete!")


if __name__ == "__main__":
    train()
