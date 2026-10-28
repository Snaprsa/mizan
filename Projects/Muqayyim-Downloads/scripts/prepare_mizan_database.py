"""Prepare a backed-up local runtime DB, preserving the relocated historical DB.

Run from this project root with the workspace Python environment. No demo seeding.
"""
import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def prepare():
    storage = ROOT / 'storage'
    storage.mkdir(exist_ok=True)
    target = storage / 'mizan.db'
    legacy = ROOT / 'muqayyim_dev.db'
    if not target.exists() and legacy.exists():
        # Recover any historical rollback journal on a temporary clone only.
        with tempfile.TemporaryDirectory() as temp:
            cloned = Path(temp) / 'legacy.db'
            shutil.copy2(legacy, cloned)
            journal = Path(str(legacy) + '-journal')
            if journal.exists():
                shutil.copy2(journal, str(cloned) + '-journal')
            with sqlite3.connect(cloned) as source, sqlite3.connect(target) as destination:
                source.backup(destination)
    if target.exists():
        backups = storage / 'database-backups'
        backups.mkdir(exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        with sqlite3.connect(target) as source, sqlite3.connect(backups / f'mizan-{stamp}.db') as destination:
            source.backup(destination)
    os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///' + str(target)
    os.environ['DATABASE_URL_SYNC'] = 'sqlite:///' + str(target)
    os.environ['ENV'] = 'development'
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, inspect
    config = Config(str(ROOT / 'api/alembic.ini'))
    config.set_main_option('script_location', str(ROOT / 'api/alembic'))
    engine = create_engine(os.environ['DATABASE_URL_SYNC'])
    tables = set(inspect(engine).get_table_names())
    if tables and 'alembic_version' not in tables:
        expected = {'organizations', 'users', 'cases', 'sources', 'extraction_jobs', 'extracted_fields',
                    'comparables', 'overrides', 'audit_log', 'subject_properties', 'adjustments',
                    'valuation_runs', 'report_artifacts', 'market_reference_data'}
        if not expected.issubset(tables):
            raise RuntimeError('Unrecognized legacy schema. Stop and inspect before applying migrations.')
        command.stamp(config, '74b32156b97d')
    command.upgrade(config, 'head')
    engine.dispose()
    print(f'Mizan database ready: {target}')


if __name__ == '__main__':
    prepare()
