"""
Prediction CLI for Mizan valuation model.

Usage:
    python -m mizan_cli.predict --input data/raw/subject_properties.csv [--output results]
"""

import json
import logging
import sys
from pathlib import Path

import click
import pandas as pd

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mizan_data import load_subjects
from mizan_features.builder import FeatureBuilder
from mizan_models.anchor_bands import AnchorBandBuilder
from mizan_models.estimator import MizanEstimator
from mizan_models.predictor import MizanPredictor
import joblib

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--input",
    "input_path",
    required=True,
    type=click.Path(exists=True),
    help="Path to subject_properties.csv file",
)
@click.option(
    "--model-dir",
    type=click.Path(exists=True),
    default="models",
    help="Directory containing trained model artifacts",
)
@click.option(
    "--output",
    type=str,
    default="results",
    help="Output filename prefix (will create .csv and .json)",
)
@click.option(
    "--output-dir",
    type=click.Path(),
    default="reports",
    help="Output directory for results",
)
def predict(
    input_path: str,
    model_dir: str,
    output: str,
    output_dir: str,
):
    """Predict valuations for subject properties."""
    model_path = Path(model_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load model artifacts
    logger.info("Loading model artifacts...")

    model_file = model_path / "model.joblib"
    anchor_file = model_path / "anchor_bands.parquet"
    feature_file = model_path / "feature_builder.joblib"

    if not model_file.exists():
        logger.error(f"Model file not found: {model_file}")
        sys.exit(1)

    if not anchor_file.exists():
        logger.error(f"Anchor bands file not found: {anchor_file}")
        sys.exit(1)

    if not feature_file.exists():
        logger.error(f"Feature builder file not found: {feature_file}")
        sys.exit(1)

    model = MizanEstimator.load(str(model_file))
    anchor_bands = AnchorBandBuilder.load(str(anchor_file))
    feature_builder = FeatureBuilder()
    feature_builder.load_state(joblib.load(feature_file))

    logger.info("Model artifacts loaded successfully")

    # Load subject properties
    logger.info(f"Loading subject properties from {input_path}")
    subjects, invalid = load_subjects(input_path, validate=True, skip_invalid=True)

    if len(invalid) > 0:
        logger.warning(f"Skipped {len(invalid)} invalid records")

    if len(subjects) == 0:
        logger.error("No valid subject properties to predict")
        sys.exit(1)

    logger.info(f"Loaded {len(subjects)} subject properties")

    # Create predictor and run predictions
    logger.info("Running predictions...")
    predictor = MizanPredictor(
        model=model,
        feature_builder=feature_builder,
        anchor_bands=anchor_bands,
    )
    results = predictor.predict(subjects)

    # Convert to output formats
    results_list = [r.to_dict() for r in results]

    # Save JSON
    json_path = output_path / f"{output}.json"
    with open(json_path, "w") as f:
        json.dump(results_list, f, indent=2)
    logger.info(f"Saved results to {json_path}")

    # Save CSV (flattened)
    csv_records = []
    for r in results:
        csv_records.append({
            "property_id": r.property_id,
            "estimated_value_sar_low": int(r.estimated_value_sar_low),
            "estimated_value_sar_mid": int(r.estimated_value_sar_mid),
            "estimated_value_sar_high": int(r.estimated_value_sar_high),
            "estimated_price_per_sqm_low": int(r.estimated_price_per_sqm_low),
            "estimated_price_per_sqm_mid": int(r.estimated_price_per_sqm_mid),
            "estimated_price_per_sqm_high": int(r.estimated_price_per_sqm_high),
            "confidence_score": r.confidence_score,
            "data_completeness_score": r.data_completeness_score,
            "segment_used": r.explanation.get("segment", {}).get("key", ""),
            "segment_level": r.explanation.get("segment", {}).get("level", ""),
            "clamp_applied": r.explanation.get("clamping", {}).get("applied", False),
        })

    csv_df = pd.DataFrame(csv_records)
    csv_path = output_path / f"{output}.csv"
    csv_df.to_csv(csv_path, index=False)
    logger.info(f"Saved results to {csv_path}")

    # Print summary
    logger.info("=" * 60)
    logger.info("PREDICTION SUMMARY")
    logger.info("=" * 60)
    for r in results:
        logger.info(f"Property: {r.property_id}")
        logger.info(f"  Value Range: {r.estimated_value_sar_low:,.0f} - "
                   f"{r.estimated_value_sar_mid:,.0f} - "
                   f"{r.estimated_value_sar_high:,.0f} SAR")
        logger.info(f"  Price/sqm:   {r.estimated_price_per_sqm_low:,.0f} - "
                   f"{r.estimated_price_per_sqm_mid:,.0f} - "
                   f"{r.estimated_price_per_sqm_high:,.0f} SAR/sqm")
        logger.info(f"  Confidence:  {r.confidence_score}/100")
        logger.info(f"  Completeness: {r.data_completeness_score}/100")
        logger.info("-" * 60)

    logger.info("Prediction complete!")


if __name__ == "__main__":
    predict()
