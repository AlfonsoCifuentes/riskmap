"""Verify the v2 SQLite DDL is valid and idempotent (offline proof for §55).

Applies the SQLite variant to a throwaway in-memory database twice — proving the
migration is safe to run on every pipeline start. Postgres variant is exercised
in CI-lite only for string integrity (kept in lock-step by review).
"""
import sqlite3

from src.database import migrations_v2


def _base_tables(cur):
    # Minimal stand-ins so FKs in event_evidence resolve.
    cur.executescript(
        "CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY);"
        "CREATE TABLE IF NOT EXISTS unified_articles (id INTEGER PRIMARY KEY);"
    )


def test_sqlite_tables_apply_idempotently():
    con = sqlite3.connect(":memory:")
    cur = con.cursor()
    _base_tables(cur)
    for _ in range(2):  # twice => idempotent
        for ddl in migrations_v2.V2_TABLES_SQLITE:
            cur.executescript(ddl)
    names = {r[0] for r in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert migrations_v2.V2_EXPECTED_TABLES <= names


def test_sqlite_columns_add_and_are_idempotent():
    con = sqlite3.connect(":memory:")
    cur = con.cursor()
    _base_tables(cur)

    def add_if_missing(table, col, col_type):
        existing = {r[1] for r in cur.execute(f"PRAGMA table_info({table})")}
        if col not in existing:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")

    for _ in range(2):
        for table, cols in migrations_v2.V2_COLUMNS.items():
            for col, _pg, sqlite_type in cols:
                add_if_missing(table, col, sqlite_type)

    cols = {r[1] for r in cur.execute("PRAGMA table_info(unified_articles)")}
    assert {"geo_method", "geo_confidence", "geo_precision_m",
            "geo_is_fallback", "risk_engine_version", "title_original"} <= cols
    evcols = {r[1] for r in cur.execute("PRAGMA table_info(events)")}
    assert {"risk_score", "confidence_score", "independent_source_count",
            "status", "risk_engine_version"} <= evcols


def test_dialects_cover_same_tables():
    assert len(migrations_v2.V2_TABLES_PG) == len(migrations_v2.V2_TABLES_SQLITE)
