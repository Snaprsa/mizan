"""Additive migration round trip on fresh and populated disposable databases."""
import importlib.util
import sqlite3
from pathlib import Path
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text


def migration():
    p = Path(__file__).parents[1] / 'alembic/versions/20261025_mizan_foundation.py'
    spec = importlib.util.spec_from_file_location('foundation_migration', p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_populated_legacy_database_preserved(tmp_path):
    # SQLite backup reads a consistent snapshot without changing the original schema.
    original = Path(__file__).parents[2] / 'muqayyim_dev.db'
    target = tmp_path / 'migration.db'
    # Private DBs are intentionally absent from portable source handoffs.
    # When present, recover only a disposable copy of the historical snapshot.
    import shutil
    if original.exists():
        shutil.copy2(original, target)
        journal = Path(str(original)+'-journal')
        if journal.exists():
            shutil.copy2(journal, str(target)+'-journal')
    engine = create_engine('sqlite:///'+str(target))
    if not original.exists():
        # Build a populated, explicitly synthetic legacy fixture in tmp_path.
        # This is never the application's runtime DB and is never auto-seeded.
        initial_path = Path(__file__).parents[1] / 'alembic/versions/74b32156b97d_initial.py'
        spec = importlib.util.spec_from_file_location('portable_legacy_migration', initial_path)
        initial = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(initial)
        with engine.begin() as conn:
            with Operations.context(MigrationContext.configure(conn)):
                initial.upgrade()
            uid, cid, sid, compid = ('00000000-0000-0000-0000-00000000000'+str(i) for i in range(1,5))
            conn.execute(text('INSERT INTO users (id,email,name) VALUES (:id,:email,:name)'),
                         {'id':uid,'email':'migration-fixture@example.invalid','name':'Portable test fixture'})
            conn.execute(text('INSERT INTO cases (id,title,created_by) VALUES (:id,:title,:owner)'),
                         {'id':cid,'title':'TEST FIXTURE - not market evidence','owner':uid})
            conn.execute(text('INSERT INTO sources (id,case_id,source_type) VALUES (:id,:case_id,:kind)'),
                         {'id':sid,'case_id':cid,'kind':'manual'})
            conn.execute(text('INSERT INTO comparables (id,case_id,source_id,property_title,status) '
                              'VALUES (:id,:case_id,:source_id,:title,:status)'),
                         {'id':compid,'case_id':cid,'source_id':sid,'title':'TEST FIXTURE - not market evidence','status':'draft'})
    m = migration()
    with engine.begin() as conn:
        before = {table: conn.execute(text('SELECT COUNT(*) FROM "'+table+'"')).scalar()
                  for table in inspect(conn).get_table_names()}
        with Operations.context(MigrationContext.configure(conn)):
            m.upgrade()
        for table, count in before.items():
            assert conn.execute(text('SELECT COUNT(*) FROM "'+table+'"')).scalar() == count
        assert {'properties', 'property_revisions', 'property_assumptions', 'data_sources', 'market_observations'} <= set(inspect(conn).get_table_names())
        with Operations.context(MigrationContext.configure(conn)):
            m.downgrade()
        assert set(inspect(conn).get_table_names()) == set(before)
    engine.dispose()


def test_full_migration_chain_empty_database(tmp_path):
    from alembic import command
    from alembic.config import Config
    api = Path(__file__).parents[1]
    config = Config(str(api/'alembic.ini'))
    config.set_main_option('script_location', str(api/'alembic'))
    engine = create_engine('sqlite:///'+str(tmp_path/'empty.db'))
    # env.py honors DATABASE_URL_SYNC; provide it for the isolated chain.
    import os
    previous = os.environ.get('DATABASE_URL_SYNC')
    os.environ['DATABASE_URL_SYNC'] = str(engine.url)
    try:
        command.upgrade(config, 'head')
        assert 'properties' in inspect(engine).get_table_names()
        command.downgrade(config, 'base')
        assert set(inspect(engine).get_table_names()) <= {'alembic_version'}
    finally:
        if previous is None: os.environ.pop('DATABASE_URL_SYNC', None)
        else: os.environ['DATABASE_URL_SYNC'] = previous
        engine.dispose()
