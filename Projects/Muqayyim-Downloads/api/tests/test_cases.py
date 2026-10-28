"""
Tests for Case API endpoints — create, list, get detail.
Uses httpx AsyncClient against the real FastAPI app with an in-memory SQLite DB.
"""

import os
import sys
import uuid
import pytest

# Ensure project root is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# Override database URL to use in-memory SQLite for tests
os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ["DATABASE_URL_SYNC"] = "sqlite://"
os.environ["ENV"] = "development"


@pytest.fixture
async def async_client():
    """Create a test client with a fresh in-memory database."""
    # Import after env vars are set
    from api.app.database import engine, Base
    import api.app.models  # noqa: F401 — register models

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from httpx import ASGITransport, AsyncClient
    from api.app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


class TestCases:
    """Tests for /api/v1/cases endpoints."""

    @pytest.mark.asyncio
    async def test_list_cases_empty(self, async_client):
        """Should return empty list when no cases exist."""
        resp = await async_client.get("/api/v1/cases")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_create_case(self, async_client):
        """Should create a case and return it with 201."""
        payload = {"title": "Test Case — Riyadh Villas", "description": "Test description"}
        resp = await async_client.post("/api/v1/cases", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == payload["title"]
        assert data["description"] == payload["description"]
        assert data["status"] == "draft"
        assert data["source_count"] == 0
        assert data["comparable_count"] == 0
        # ID should be a valid UUID
        uuid.UUID(data["id"])

    @pytest.mark.asyncio
    async def test_create_case_title_required(self, async_client):
        """Should reject case creation without title."""
        resp = await async_client.post("/api/v1/cases", json={"description": "no title"})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_list_cases_after_create(self, async_client):
        """Should list all created cases."""
        # Create two cases
        await async_client.post("/api/v1/cases", json={"title": "Case A"})
        await async_client.post("/api/v1/cases", json={"title": "Case B"})

        resp = await async_client.get("/api/v1/cases")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        titles = [c["title"] for c in data["data"]]
        assert "Case A" in titles
        assert "Case B" in titles

    @pytest.mark.asyncio
    async def test_get_case_detail(self, async_client):
        """Should retrieve a specific case by ID."""
        create_resp = await async_client.post("/api/v1/cases", json={"title": "Detail Test"})
        case_id = create_resp.json()["id"]

        resp = await async_client.get(f"/api/v1/cases/{case_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == case_id
        assert data["title"] == "Detail Test"

    @pytest.mark.asyncio
    async def test_get_case_not_found(self, async_client):
        """Should return 404 for non-existent case ID."""
        fake_id = str(uuid.uuid4())
        resp = await async_client.get(f"/api/v1/cases/{fake_id}")
        assert resp.status_code == 404


class TestSources:
    """Tests for source management endpoints."""

    @pytest.mark.asyncio
    async def test_add_url_source(self, async_client):
        """Should add a URL source to a case."""
        # Create case first
        case_resp = await async_client.post("/api/v1/cases", json={"title": "URL Test"})
        case_id = case_resp.json()["id"]

        resp = await async_client.post(
            f"/api/v1/cases/{case_id}/sources/url",
            json={"url": "https://aqar.fm/listing/12345"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["source_type"] == "url"
        assert data["url"] == "https://aqar.fm/listing/12345"
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_list_sources(self, async_client):
        """Should list all sources for a case."""
        case_resp = await async_client.post("/api/v1/cases", json={"title": "Sources Test"})
        case_id = case_resp.json()["id"]

        # Add two sources
        await async_client.post(f"/api/v1/cases/{case_id}/sources/url", json={"url": "https://example.com/1"})
        await async_client.post(f"/api/v1/cases/{case_id}/sources/url", json={"url": "https://example.com/2"})

        resp = await async_client.get(f"/api/v1/cases/{case_id}/sources")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_add_source_to_nonexistent_case(self, async_client):
        """Should return 404 when adding source to non-existent case."""
        fake_id = str(uuid.uuid4())
        resp = await async_client.post(
            f"/api/v1/cases/{fake_id}/sources/url",
            json={"url": "https://example.com"},
        )
        assert resp.status_code == 404
