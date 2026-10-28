"""
Shared test fixtures.
"""

import os
import pytest

# Set test environment — use SQLite in-memory so tests run without a Postgres server.
# Individual test files can override these if they need a specific DB.
os.environ["ENV"] = "development"  # dev mode = auth bypass
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")
os.environ.setdefault("DATABASE_URL_SYNC", "sqlite://")


@pytest.fixture
def sample_html():
    """Sample HTML content for testing extraction."""
    return """
    <html>
    <head>
        <title>فيلا للبيع في حي النخيل - الرياض</title>
        <meta property="og:title" content="فيلا للبيع في حي النخيل" />
    </head>
    <body>
        <h1>فيلا للبيع في حي النخيل</h1>
        <div class="price">3,500,000 ريال</div>
        <div class="area">450 متر مربع</div>
        <div class="location">الرياض - حي النخيل</div>
        <div class="date">2025-01-15</div>
    </body>
    </html>
    """


@pytest.fixture
def sample_comparable_data():
    """Sample comparable for testing."""
    return {
        "property_title": "Villa in Al Nakheel",
        "city": "Riyadh",
        "district": "Al Nakheel",
        "property_type": "villa",
        "evidence_type": "listing_asking",
        "asking_price": 3500000,
        "currency": "SAR",
        "primary_area_sqm": 450,
        "price_per_sqm": 7777.78,
    }
