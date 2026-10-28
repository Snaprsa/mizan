"""
Flask web server for Mizan valuation UI.
"""

import json
import logging
import sys
from pathlib import Path

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mizan_data.schemas import SubjectProperty, PropertyType
from mizan_features.builder import FeatureBuilder
from mizan_models.anchor_bands import AnchorBandBuilder
from mizan_models.estimator import MizanEstimator
from mizan_models.predictor import MizanPredictor
from mizan_data.loader import load_comps, comps_to_dataframe
from mizan_roi import ROICalculator, MarketFactorsEngine, RiskAssessor
import joblib
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# Global predictor instance
predictor = None
# Global comps dataframe for comparable deals lookup
comps_df = None
# ROI analysis components
roi_calculator = ROICalculator()
market_factors_engine = MarketFactorsEngine()
risk_assessor = RiskAssessor()


def load_model():
    """Load trained model artifacts."""
    global predictor, comps_df
    
    model_dir = Path(__file__).parent.parent / "models"
    data_dir = Path(__file__).parent.parent / "data" / "raw"
    
    model_file = model_dir / "model.joblib"
    anchor_file = model_dir / "anchor_bands.parquet"
    feature_file = model_dir / "feature_builder.joblib"
    comps_file = data_dir / "comps.csv"
    
    if not all(f.exists() for f in [model_file, anchor_file, feature_file]):
        logger.error("Model files not found. Run training first.")
        return False
    
    model = MizanEstimator.load(str(model_file))
    anchor_bands = AnchorBandBuilder.load(str(anchor_file))
    feature_builder = FeatureBuilder()
    feature_builder.load_state(joblib.load(feature_file))
    
    predictor = MizanPredictor(model, feature_builder, anchor_bands)
    
    # Load comps database for comparable deals lookup
    if comps_file.exists():
        comp_records, _ = load_comps(str(comps_file))
        comps_df = comps_to_dataframe(comp_records)
        logger.info(f"Loaded {len(comps_df)} comparable deals for lookup")
    else:
        logger.warning("Comps file not found. Comparable deals feature disabled.")
        comps_df = pd.DataFrame()
    
    logger.info("Model loaded successfully")
    return True


@app.route("/")
def index():
    """Serve the main UI page."""
    return render_template("index.html")


@app.route("/api/valuate", methods=["POST"])
def valuate():
    """API endpoint for property valuation with ROI analysis."""
    try:
        data = request.json
        include_roi = data.get("include_roi", True)
        
        city = data.get("city", "Riyadh")
        district = data.get("district")
        property_type = data.get("property_type")
        area_sqm = float(data.get("area_sqm"))
        year_built = int(data["year_built"]) if data.get("year_built") else None
        
        # Build subject property
        subject = SubjectProperty(
            property_id=data.get("property_id", "WEB_001"),
            city=city,
            district=district,
            property_type=PropertyType(property_type),
            area_sqm=area_sqm,
            bedrooms=int(data["bedrooms"]) if data.get("bedrooms") else None,
            bathrooms=int(data["bathrooms"]) if data.get("bathrooms") else None,
            parking_count=int(data["parking_count"]) if data.get("parking_count") else None,
            floor_level=int(data["floor_level"]) if data.get("floor_level") else None,
            year_built=year_built,
            finish_tier=int(data["finish_tier"]) if data.get("finish_tier") else None,
            condition_tier=int(data["condition_tier"]) if data.get("condition_tier") else None,
            elevator=int(data["elevator"]) if data.get("elevator") is not None else None,
            central_ac=int(data["central_ac"]) if data.get("central_ac") is not None else None,
            maid_room=int(data["maid_room"]) if data.get("maid_room") is not None else None,
            garden=int(data["garden"]) if data.get("garden") is not None else None,
            private_entrance=int(data["private_entrance"]) if data.get("private_entrance") is not None else None,
        )
        
        # Run prediction
        results = predictor.predict([subject])
        result = results[0]
        valuation_dict = result.to_dict()
        
        response = {
            "success": True,
            "valuation": valuation_dict
        }
        
        # Add ROI analysis if requested
        if include_roi:
            property_value = valuation_dict.get("estimated_value_sar_mid", 0)
            
            # Calculate risk score first
            risk_result = risk_assessor.assess(
                city=city,
                district=district,
                property_type=property_type,
                property_value_sar=property_value,
                area_sqm=area_sqm,
                year_built=year_built,
            )
            
            # Calculate ROI
            roi_result = roi_calculator.calculate(
                property_value_sar=property_value,
                property_type=property_type,
                city=city,
                district=district,
                area_sqm=area_sqm,
                risk_score=risk_result.overall_risk,
            )
            
            # Get market factors
            market_result = market_factors_engine.analyze(
                city=city,
                district=district,
                property_type=property_type,
                area_sqm=area_sqm,
            )
            
            response["roi_analysis"] = roi_result.to_dict()
            response["market_factors"] = market_result.to_dict()
            response["risk_assessment"] = risk_result.to_dict()
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Valuation error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400


@app.route("/api/cities")
def get_cities():
    """Get list of cities from the database."""
    if comps_df is None or comps_df.empty:
        return jsonify(["Riyadh"])  # Fallback
    cities = sorted(comps_df['city'].unique().tolist())
    return jsonify(cities)


@app.route("/api/districts")
def get_districts():
    """Get list of districts, optionally filtered by city."""
    city = request.args.get('city', None)
    
    if comps_df is None or comps_df.empty:
        # Fallback districts for Riyadh
        return jsonify([
            "Al Olaya", "Al Malqa", "Al Nakheel", "Al Yasmin", "Al Sahafa",
            "Al Muruj", "Hittin", "Al Narjis", "Al Qirawan", "Al Rabwah"
        ])
    
    if city:
        filtered = comps_df[comps_df['city'] == city]
        districts = sorted(filtered['district'].unique().tolist())
    else:
        districts = sorted(comps_df['district'].unique().tolist())
    
    return jsonify(districts)


def get_comparable_deals(property_type: str, area_sqm: float, district: str = None, limit: int = 5):
    """
    Find comparable deals from the database based on property type and size.
    
    Args:
        property_type: apartment or villa
        area_sqm: target area in square meters
        district: optional district filter
        limit: max number of deals to return
        
    Returns:
        List of comparable deal dictionaries
    """
    if comps_df is None or comps_df.empty:
        return []
    
    # Filter by property type
    filtered = comps_df[comps_df['property_type'] == property_type].copy()
    
    if filtered.empty:
        return []
    
    # Optionally filter by district (prioritize same district)
    if district:
        same_district = filtered[filtered['district'] == district]
        if len(same_district) >= limit:
            filtered = same_district
    
    # Calculate size difference and sort by closest size
    filtered['size_diff'] = abs(filtered['area_sqm'] - area_sqm)
    filtered = filtered.sort_values('size_diff')
    
    # Take top N closest matches
    top_comps = filtered.head(limit)
    
    # Format results
    deals = []
    for _, row in top_comps.iterrows():
        deals.append({
            "district": row.get('district', 'N/A'),
            "property_type": row['property_type'],
            "area_sqm": int(row['area_sqm']),
            "total_price_sar": int(row['total_price_sar']),
            "price_per_sqm": int(row['price_per_sqm']),
            "bedrooms": int(row['bedrooms']) if pd.notna(row.get('bedrooms')) else None,
            "bathrooms": int(row['bathrooms']) if pd.notna(row.get('bathrooms')) else None,
            "year_built": int(row['year_built']) if pd.notna(row.get('year_built')) else None,
            "trans_date": str(row['trans_date']) if pd.notna(row.get('trans_date')) else None,
        })
    
    return deals


@app.route("/api/comparables", methods=["POST"])
def get_comparables():
    """API endpoint to fetch comparable deals."""
    try:
        data = request.json
        property_type = data.get("property_type", "apartment")
        area_sqm = float(data.get("area_sqm", 150))
        district = data.get("district")
        limit = int(data.get("limit", 5))
        
        deals = get_comparable_deals(property_type, area_sqm, district, limit)
        
        return jsonify({
            "success": True,
            "comparables": deals,
            "count": len(deals)
        })
        
    except Exception as e:
        logger.error(f"Comparables error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400


if __name__ == "__main__":
    if load_model():
        app.run(host="0.0.0.0", port=5050, debug=True)
    else:
        print("Failed to load model. Please run training first.")
        sys.exit(1)
