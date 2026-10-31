"""
Muqayyim API — Saudi Real Estate Valuation Platform
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.app.config import get_settings
from api.app.routers import cases, sources, extractions, comparables, exports, properties, market, analysis, imagery, evidence, monitor, map as intelligence_map
import api.app.models.foundation  # Register additive Mizan models
import api.app.models.monitor  # noqa: F401

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Path(settings.storage_local_path).mkdir(parents=True, exist_ok=True)
    # Auto-create tables (works for SQLite dev; migrations handle production)
    from api.app.database import engine, Base
    import api.app.models  # noqa: F401 — ensure all models are registered
    if settings.env == "development":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="Mizan API",
    description="Saudi Real Estate Valuation Platform",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Open for dev — tighten in production
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(intelligence_map.router, prefix="/api/v1")
app.include_router(imagery.router, prefix="/api/v1")
app.include_router(evidence.router, prefix="/api/v1")
app.include_router(monitor.router, prefix="/api/v1")
app.include_router(properties.router, prefix="/api/v1")
app.include_router(market.router, prefix="/api/v1")
app.include_router(cases.router, prefix="/api/v1/cases", tags=["Cases"])
app.include_router(sources.router, prefix="/api/v1", tags=["Sources"])
app.include_router(extractions.router, prefix="/api/v1", tags=["Extractions"])
app.include_router(comparables.router, prefix="/api/v1", tags=["Comparables"])
app.include_router(exports.router, prefix="/api/v1", tags=["Exports"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "mizan-api", "version": "0.2.0"}
