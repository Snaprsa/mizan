import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "web"))

from app import app, load_model  # noqa: E402


@pytest.fixture(scope="module")
def client():
    assert load_model() is True
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client


def test_cities_endpoint(client):
    response = client.get("/api/cities")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert "Riyadh" in data


def test_valuation_endpoint(client):
    payload = {
        "property_id": "TEST_WEB_001",
        "city": "Riyadh",
        "district": "Al Olaya",
        "property_type": "apartment",
        "area_sqm": 220,
        "bedrooms": 4,
        "bathrooms": 3,
        "parking_count": 2,
        "floor_level": 15,
        "year_built": 2024,
        "finish_tier": 5,
        "condition_tier": 5,
        "elevator": 1,
        "central_ac": 1,
        "maid_room": 1,
        "garden": 0,
        "private_entrance": 0,
        "include_roi": True,
    }
    response = client.post("/api/valuate", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["valuation"]["estimated_value_sar_mid"] > 0
    assert "roi_analysis" in data
    assert data["roi_analysis"]["investment_grade"] in {"Strong Buy", "Buy", "Hold", "Caution", "Avoid"}


def test_comparables_endpoint(client):
    payload = {
        "property_type": "apartment",
        "area_sqm": 150,
        "district": "Al Malqa",
        "limit": 3,
    }
    response = client.post("/api/comparables", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["count"] <= 3
    assert isinstance(data["comparables"], list)
