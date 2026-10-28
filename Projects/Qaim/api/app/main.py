"""Qaim API — FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .core.database import init_db
from .routes import cases_router, sources_router, extraction_router, export_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    await init_db()
    yield


app = FastAPI(
    title="Qaim — Saudi Real Estate Valuation API",
    description="Stage 1: Comparable Link Ingestor",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
prefix = settings.API_PREFIX
app.include_router(cases_router, prefix=prefix)
app.include_router(sources_router, prefix=prefix)
app.include_router(extraction_router, prefix=prefix)
app.include_router(export_router, prefix=prefix)


@app.get("/")
async def root():
    return {
        "name": "Qaim",
        "version": "0.1.0",
        "stage": "Stage 1 — Comparable Link Ingestor",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
