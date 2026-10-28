# Mizan - Saudi Real Estate Valuation Tool

Phase 1: Property valuation for Riyadh (apartments and villas).

## Overview

Mizan is a local-first real estate valuation tool that predicts property values in Riyadh, Saudi Arabia. It uses a layered estimator approach combining segment-based anchor bands with machine learning models to produce realistic value ranges.

**Key Features:**
- Estimates value range (low, mid, high) in SAR
- Provides price per sqm estimates
- Confidence scoring (0-100)
- Data completeness tracking
- No external APIs - runs entirely locally

## Quick Start

```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Train model
python -m mizan_cli.train --comps data/raw/comps.csv

# 4. Run predictions
python -m mizan_cli.predict --input data/raw/subject_properties.csv

# 5. Run the web app
python web/app.py
# open http://127.0.0.1:5050
```

Or use the Makefile:
```bash
make setup
make train
make predict
```

## Project Structure

```
mizan/
├── data/
│   ├── raw/              # Input CSVs
│   │   ├── comps.csv
│   │   └── subject_properties.csv
│   ├── processed/        # Processed data
│   └── external/         # Future REGA/GASTAT data
├── models/               # Trained artifacts
│   ├── model.joblib
│   ├── anchor_bands.parquet
│   └── feature_builder.joblib
├── reports/              # Prediction outputs
│   ├── results.csv
│   └── results.json
├── src/
│   ├── mizan_data/       # Data loading & validation
│   ├── mizan_features/   # Feature engineering
│   ├── mizan_models/     # Training & prediction
│   └── mizan_cli/        # CLI commands
├── tests/                # pytest tests
├── requirements.txt
├── Makefile
└── README.md
```

## Data Formats

### comps.csv (Required columns)

| Column | Type | Description |
|--------|------|-------------|
| trans_date | date | Transaction date (YYYY-MM-DD) |
| city | string | City name |
| district | string | District name |
| property_type | string | "apartment" or "villa" |
| total_price_sar | float | Total sale price in SAR |
| area_sqm | float | Total area in square meters |
| bedrooms | int | Number of bedrooms |
| bathrooms | int | Number of bathrooms |
| parking_count | int | Parking spaces (default: 0) |
| floor_level | int | Floor level (apartments only) |
| year_built | int | Year of construction |
| finish_tier | int | Finish quality 1-5 |
| condition_tier | int | Condition 1-5 |
| elevator | int | 0 or 1 |
| central_ac | int | 0 or 1 |
| maid_room | int | 0 or 1 |
| garden | int | 0 or 1 |
| private_entrance | int | 0 or 1 |

Optional: `lat`, `lon`, `source_tag`

### subject_properties.csv

Same columns as comps.csv except:
- `total_price_sar` is not required
- Add `property_id` column for tracking
- Missing fields will be imputed (lowers confidence score)

## CLI Commands

### Training

```bash
python -m mizan_cli.train --comps data/raw/comps.csv [OPTIONS]

Options:
  --model-type [ridge|hgb]  Model type (default: ridge)
  --output-dir PATH         Output directory (default: models)
  --validation-split FLOAT  Validation fraction (default: 0.2)
  --seed INT                Random seed (default: 42)
```

### Prediction

```bash
python -m mizan_cli.predict --input data/raw/subject_properties.csv [OPTIONS]

Options:
  --model-dir PATH    Model artifacts directory (default: models)
  --output STRING     Output filename prefix (default: results)
  --output-dir PATH   Output directory (default: reports)
```

## Output Format

### results.json

```json
[
  {
    "property_id": "SUBJ_001",
    "estimated_value_sar_low": 2500000,
    "estimated_value_sar_mid": 2900000,
    "estimated_value_sar_high": 3300000,
    "estimated_price_per_sqm_low": 13500,
    "estimated_price_per_sqm_mid": 15700,
    "estimated_price_per_sqm_high": 17800,
    "confidence_score": 82,
    "data_completeness_score": 95,
    "explanation": {
      "segment": {"key": "Riyadh|Al Olaya|apartment", ...},
      "model_prediction": {...},
      "clamping": {"applied": false, ...},
      "top_drivers": ["Location: Al Olaya, Riyadh", ...]
    }
  }
]
```

## How It Works

### Layer A: Segment Anchor Bands
Computes price/sqm quantiles (p10, p25, p50, p75, p90) for each market segment:
- Segment key: city | district | property_type
- Provides guardrails for plausible market ranges
- Falls back to broader segments if sample size < 10

### Layer B: Adjustment Model
Predicts log(price_per_sqm) using property features:
- **Ridge regression** (default): Fast, stable, good baseline
- **HistGradientBoosting**: Better with non-linear relationships

Features used:
- log_area, age_years, bedrooms, bathrooms
- parking_count, floor_level, finish_tier, condition_tier
- Binary amenities: elevator, central_ac, maid_room, garden, private_entrance
- Target-encoded district

### Layer C: Clamping & Uncertainty
- Model produces low/mid/high predictions
- Clamps to anchor bounds: low ≥ p10, high ≤ p90
- Ensures predictions stay within plausible market ranges

### Confidence Scoring

```
confidence = 0.3 × completeness + 0.4 × segment_support + 0.3 × model_residual
```

- **Completeness** (0-100): Weighted presence of input fields
- **Segment support** (0-100): Based on comparable count in segment
- **Model residual** (0-100): Based on prediction uncertainty

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## TODO: Phase 1.1 Improvements

1. [ ] Add geospatial features (distance to landmarks)
2. [ ] Implement time-based price adjustments
3. [ ] Add conformal prediction for tighter intervals
4. [ ] Expand to other Saudi cities
5. [ ] Add more property types (land, commercial)
6. [ ] REGA/GASTAT data integration
7. [ ] Web interface for predictions

## Requirements

- Python 3.11+
- See requirements.txt for dependencies

## License

MIT
