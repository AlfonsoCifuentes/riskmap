"""
RiskMap Schema Initializer
============================
Creates all tables in the target database (Neon Postgres or SQLite).
Safe to run repeatedly — all CREATE TABLE use IF NOT EXISTS.

Usage:
    python -m src.database.schema_init          # auto-detect from DATABASE_URL
    python -m src.database.schema_init --check  # dry-run: show which tables exist
"""

import os
import sys
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.connection import get_db, _detect_backend
from src.database.schema import POSTGRES_SCHEMA, SQLITE_SCHEMA

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")
logger = logging.getLogger(__name__)


def init_schema(check_only: bool = False):
    """Create all tables in the current backend."""
    backend = _detect_backend()
    db = get_db()

    logger.info(f"Backend: {backend}")

    if check_only:
        _check_tables(db, backend)
        return

    if backend == 'postgres':
        logger.info("Applying Postgres schema…")
        db.execute_script(POSTGRES_SCHEMA)
        logger.info("✅ Postgres schema applied")
        # Add event_id to unified_articles if missing
        _add_column_if_missing_pg(db, 'unified_articles', 'event_id', 'INTEGER')
    else:
        logger.info("Applying SQLite schema…")
        db.execute_script(SQLITE_SCHEMA)
        logger.info("✅ SQLite schema applied")
        # Add event_id to unified_articles if missing
        _add_column_if_missing_sqlite(db, 'unified_articles', 'event_id', 'INTEGER')

    _check_tables(db, backend)


def _add_column_if_missing_sqlite(db, table, column, col_type):
    """Add a column to an existing SQLite table if it doesn't exist."""
    try:
        rows = db.execute(f"PRAGMA table_info({table})", fetch=True)
        existing = {r['name'] for r in rows}
        if column not in existing:
            db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
            logger.info(f"  + Added column {column} to {table}")
        else:
            logger.info(f"  ✓ Column {column} already exists in {table}")
    except Exception as e:
        logger.warning(f"  ⚠ Could not check/add column {column} on {table}: {e}")


def _add_column_if_missing_pg(db, table, column, col_type):
    """Add a column to an existing Postgres table if it doesn't exist."""
    try:
        sql = (
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = %s AND column_name = %s"
        )
        rows = db.execute(sql, (table, column), fetch=True)
        if not rows:
            db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
            logger.info(f"  + Added column {column} to {table}")
        else:
            logger.info(f"  ✓ Column {column} already exists in {table}")
    except Exception as e:
        logger.warning(f"  ⚠ Could not check/add column {column} on {table}: {e}")


def _check_tables(db, backend):
    """List all tables in the database."""
    if backend == 'postgres':
        sql = (
            "SELECT tablename FROM pg_catalog.pg_tables "
            "WHERE schemaname = 'public' ORDER BY tablename"
        )
    else:
        sql = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"

    rows = db.execute(sql, fetch=True)
    names = [list(r.values())[0] for r in rows]
    logger.info(f"Tables ({len(names)}): {', '.join(names)}")

    expected = {
        'unified_articles', 'events', 'event_locations',
        'aois', 'images', 'detections', 'signals',
        'alerts', 'conflict_zones', 'enrichment_log', 'gpr_index',
    }
    missing = expected - set(names)
    if missing:
        logger.warning(f"⚠ Missing tables: {', '.join(sorted(missing))}")
    else:
        logger.info("✅ All expected tables present")


if __name__ == '__main__':
    check_only = '--check' in sys.argv
    init_schema(check_only=check_only)
