"""Qaim API — Core configuration."""
import os
from pydantic_settings import BaseSettings

# Determine project root (qaim/)
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_default_db = f"sqlite+aiosqlite:///{os.path.join(_project_root, 'qaim_dev.db')}"


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Qaim"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"

    # Database — defaults to SQLite for zero-config local dev
    # For production: postgresql+asyncpg://qaim:qaim_dev@localhost:5432/qaim
    DATABASE_URL: str = os.getenv("DATABASE_URL", _default_db)

    # Redis (optional for MVP — extraction runs inline)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # File Storage
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", os.path.join(_project_root, "uploads"))
    EXPORT_DIR: str = os.getenv("EXPORT_DIR", os.path.join(_project_root, "exports"))

    # Auth (MVP: simple token)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "qaim-dev-secret-change-in-prod")
    DEFAULT_ADMIN_USER: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "admin123"  # MVP only

    # Defaults
    DEFAULT_CURRENCY: str = "SAR"
    DEFAULT_AREA_UNIT: str = "sqm"

    class Config:
        env_file = ".env"


settings = Settings()

