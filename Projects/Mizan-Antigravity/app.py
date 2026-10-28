"""
Mizan Web Application - Real Estate Valuation UI

Flask server providing:
- Main HTML page at /
- Prediction API at /api/predict
"""

import logging
import sys
from pathlib import Path

from flask import Flask, render_template, request, jsonify
import joblib
import pandas as pd

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mizan_data.schemas import SubjectProperty, PropertyType
from mizan_features.builder import FeatureBuilder
from mizan_models.anchor_bands import AnchorBandBuilder
from mizan_models.estimator import MizanEstimator
from mizan_models.predictor import MizanPredictor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global predictor instance (loaded on startup)
predictor = None


def load_model():
    """Load model artifacts on startup."""
    global predictor
    
    model_path = Path(__file__).parent / "models"
    
    model_file = model_path / "model.joblib"
    anchor_file = model_path / "anchor_bands.parquet"
    feature_file = model_path / "feature_builder.joblib"
    
    if not all(f.exists() for f in [model_file, anchor_file, feature_file]):
        logger.error("Model files not found. Run training first: make train")
        return False
    
    model = MizanEstimator.load(str(model_file))
    anchor_bands = AnchorBandBuilder.load(str(anchor_file))
    feature_builder = FeatureBuilder()
    feature_builder.load_state(joblib.load(feature_file))
    
    predictor = MizanPredictor(
        model=model,
        feature_builder=feature_builder,
        anchor_bands=anchor_bands,
    )
    
    logger.info("Model loaded successfully")
    return True


# Load comps data for district lookup
comps_data = None

def load_comps():
    """Load comps data for district lookups."""
    global comps_data
    import pandas as pd
    comps_path = Path(__file__).parent / "data" / "raw" / "comps_saudi_full.csv"
    if comps_path.exists():
        comps_data = pd.read_csv(comps_path)
        logger.info(f"Loaded {len(comps_data)} comps for district lookup")
    else:
        logger.warning("Comps file not found for district lookup")


@app.route("/")
def index():
    """Serve main page."""
    return render_template("index.html")


@app.route("/api/districts/<city>")
def get_districts(city):
    """Get districts for a city with price ranges."""
    global comps_data
    
    if comps_data is None:
        load_comps()
    
    if comps_data is None:
        return jsonify({"error": "Data not loaded", "districts": []})
    
    # Map Arabic city names
    city_map = {
        "الرياض": "Riyadh",
        "الدمام": "Dammam",
        "Riyadh": "Riyadh",
        "Dammam": "Dammam",
    }
    city_normalized = city_map.get(city, city)
    
    # Filter by city
    city_data = comps_data[comps_data['city'] == city_normalized]
    
    if len(city_data) == 0:
        return jsonify({"city": city, "districts": []})
    
    # Group by district and calculate stats
    districts = []
    for district, group in city_data.groupby('district'):
        price_per_sqm = group['total_price_sar'] / group['area_sqm']
        districts.append({
            "name": district,
            "count": len(group),
            "avg_price_sqm": int(price_per_sqm.mean()),
            "min_price_sqm": int(price_per_sqm.min()),
            "max_price_sqm": int(price_per_sqm.max()),
        })
    
    # Sort by number of transactions
    districts.sort(key=lambda x: x['count'], reverse=True)
    
    return jsonify({
        "city": city,
        "district_count": len(districts),
        "districts": districts
    })


@app.route("/api/predict", methods=["POST"])
def predict():
    """Run prediction on submitted property data."""
    global predictor
    
    if predictor is None:
        return jsonify({"error": "Model not loaded"}), 500
    
    try:
        data = request.json
        
        # Map Arabic property types to English
        property_type_map = {
            "شقة": "apartment",
            "فيلا": "villa",
            "apartment": "apartment",
            "villa": "villa",
        }
        
        # Map Arabic city names to English (for model compatibility)
        city_map = {
            "الرياض": "Riyadh",
            "جدة": "Jeddah",
            "مكة": "Mecca",
            "المدينة": "Medina",
            "الدمام": "Dammam",
            "شرورة": "Sharurah",
            "Riyadh": "Riyadh",
            "Jeddah": "Jeddah",
            "Mecca": "Mecca",
            "Medina": "Medina",
            "Dammam": "Dammam",
            "Sharurah": "Sharurah",
        }
        
        # Build SubjectProperty from form data
        property_type_ar = data.get("property_type", "شقة")
        property_type = property_type_map.get(property_type_ar, "apartment")
        
        city_ar = data.get("city", "الرياض")
        city = city_map.get(city_ar, city_ar)
        
        subject_data = {
            "property_id": "WEB_001",
            "city": city,
            "district": data.get("district", "Unknown"),
            "property_type": PropertyType(property_type),
            "area_sqm": float(data.get("area_sqm", 150)),
        }
        
        # Add optional fields if provided
        optional_fields = [
            ("bedrooms", int),
            ("bathrooms", int),
            ("parking_count", int),
            ("floor_level", int),
            ("year_built", int),
            ("finish_tier", int),
            ("condition_tier", int),
            ("elevator", int),
            ("central_ac", int),
            ("maid_room", int),
            ("garden", int),
            ("private_entrance", int),
        ]
        
        for field, dtype in optional_fields:
            value = data.get(field)
            if value is not None and value != "" and value != "null":
                try:
                    subject_data[field] = dtype(value)
                except (ValueError, TypeError):
                    pass
        
        # Create subject and predict
        subject = SubjectProperty(**subject_data)
        results = predictor.predict([subject])
        
        if not results:
            return jsonify({"error": "Prediction failed"}), 500
        
        result = results[0]
        
        # Fetch comparable deals for transparency
        comparable_deals = []
        if comps_data is not None:
            # Filter by city and property type
            city_comps = comps_data[
                (comps_data['city'] == city) & 
                (comps_data['property_type'] == property_type)
            ].copy()
            
            # Calculate price per sqm
            city_comps['price_per_sqm'] = city_comps['total_price_sar'] / city_comps['area_sqm']
            
            # Filter by similar area (±50%)
            area = float(data.get("area_sqm", 100))
            area_min, area_max = area * 0.5, area * 1.5
            similar_comps = city_comps[
                (city_comps['area_sqm'] >= area_min) & 
                (city_comps['area_sqm'] <= area_max)
            ]
            
            # Prioritize same district, then nearby
            same_district = similar_comps[similar_comps['district'] == data.get("district", "")]
            other_comps = similar_comps[similar_comps['district'] != data.get("district", "")]
            
            # Take up to 5 comps: prefer same district
            selected = pd.concat([same_district.head(3), other_comps.head(2)])
            
            for _, comp in selected.head(5).iterrows():
                comparable_deals.append({
                    "district": comp['district'],
                    "area_sqm": int(comp['area_sqm']),
                    "total_price": int(comp['total_price_sar']),
                    "price_per_sqm": int(comp['price_per_sqm']),
                    "trans_date": comp.get('trans_date', '2024'),
                    "same_district": comp['district'] == data.get("district", "")
                })
        
        return jsonify({
            "success": True,
            "property_id": result.property_id,
            "estimated_value_sar_low": int(result.estimated_value_sar_low),
            "estimated_value_sar_mid": int(result.estimated_value_sar_mid),
            "estimated_value_sar_high": int(result.estimated_value_sar_high),
            "estimated_price_per_sqm_low": int(result.estimated_price_per_sqm_low),
            "estimated_price_per_sqm_mid": int(result.estimated_price_per_sqm_mid),
            "estimated_price_per_sqm_high": int(result.estimated_price_per_sqm_high),
            "confidence_score": result.confidence_score,
            "data_completeness_score": result.data_completeness_score,
            "explanation": result.explanation,
            "comparable_deals": comparable_deals,
            "comps_count": len(comparable_deals),
        })
        
    except Exception as e:
        logger.exception("Prediction error")
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    if load_model():
        app.run(debug=True, port=5001)
    else:
        print("Failed to load model. Please run 'make train' first.")
        sys.exit(1)
