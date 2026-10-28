"""
Alembic environment configuration.
Uses sync driver for migrations.
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add project root to path so we can import our models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from api.app.database import Base
import api.app.models.foundation  # Register Mizan metadata
from api.app.models import (  # noqa: F401 — import all models so Base.metadata is populated
    Organization, User, Case, Source, ExtractionJob, ExtractedField,
    Comparable, Override, AuditLog,
    SubjectProperty, Adjustment, ValuationRun, ReportArtifact, MarketReferenceData,
)

config = context.config

# Override URL from environment if available
database_url = os.environ.get("DATABASE_URL_SYNC")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
