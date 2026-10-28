"""
Application configuration from environment variables.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://muqayyim:muqayyim@localhost:5432/muqayyim"
    database_url_sync: str = "postgresql://muqayyim:muqayyim@localhost:5432/muqayyim"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    jwt_secret: str = "dev-secret-change-in-production-immediately"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24

    # LLM
    anthropic_api_key: Optional[str] = None

    # Storage
    storage_backend: str = "local"  # local | s3
    storage_local_path: str = "./storage"
    s3_bucket: Optional[str] = None
    s3_region: str = "me-south-1"

    # App
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_url: str = "http://localhost:3000"
    env: str = "development"
    debug: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
