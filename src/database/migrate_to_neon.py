"""
RiskMap SQLite → Neon Postgres Migration
==========================================
Reads unified_articles + supporting tables from the local SQLite DB and
inserts them into Neon Postgres.  Safe to run multiple times (uses UPSERT on url).

Prereqs:
  - Set DATABASE_URL in .env to your Neon connection string
  - pip install psycopg2-binary
  - Run schema_init.py first to create tables in Neon

Usage:
    python -m src.database.migrate_to_neon
    python -m src.database.migrate_to_neon --dry-run    # count only
    python -m src.database.migrate_to_neon --limit 100  # migrate first 100
"""

import os
import sys
import sqlite3
import logging
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")
logger = logging.getLogger(__name__)

# Columns to migrate (intersection of SQLite and Postgres schemas)
ARTICLE_COLUMNS = [
    'title', 'content', 'summary', 'url', 'source',
    'published_at', 'created_at',
    'language', 'original_language', 'is_translated',
    'geopolitical_relevance', 'risk_level', 'risk_score',
    'conflict_type', 'conflict_intensity',
    'country', 'region', 'latitude', 'longitude',
    'location_extracted', 'coordinates_source',
    'image_url', 'original_image_url', 'cv_analysis',
    'satellite_image_url', 'has_image',
    'ai_importance', 'ai_summary', 'auto_generated_summary',
    'ai_sentiment', 'ai_tags', 'enrichment_status',
    'entities_json', 'extracted_entities_json',
    'countries_involved', 'politicians_involved',
    'sentiment_score', 'quality_score',
    'processing_confidence', 'enrichment_confidence',
    'source_country', 'source_bias', 'source_credibility',
    'metadata_json', 'processing_notes',
]


def get_sqlite_conn():
    """Connect to local SQLite DB."""
    path = os.getenv('SQLITE_PATH', './data/geopolitical_intel.db')
    if not os.path.exists(path):
        raise FileNotFoundError(f"SQLite DB not found: {path}")
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def get_neon_conn():
    """Connect to Neon Postgres."""
    import psycopg2
    from psycopg2.extras import RealDictCursor
    dsn = os.getenv('DATABASE_URL', '')
    if not dsn.startswith('postgres'):
        raise ValueError("DATABASE_URL must be a Postgres connection string")
    conn = psycopg2.connect(dsn, cursor_factory=RealDictCursor, sslmode='require')
    return conn


def discover_columns(sqlite_conn, table):
    """Get actual columns in the SQLite table."""
    cur = sqlite_conn.execute(f"PRAGMA table_info({table})")
    return {row['name'] for row in cur.fetchall()}


def migrate_articles(dry_run=False, limit=None):
    """Migrate unified_articles from SQLite → Neon."""
    sqlite_conn = get_sqlite_conn()
    actual_cols = discover_columns(sqlite_conn, 'unified_articles')
    
    # Only use columns that actually exist in SQLite
    cols = [c for c in ARTICLE_COLUMNS if c in actual_cols]
    logger.info(f"Migrating {len(cols)} columns (of {len(ARTICLE_COLUMNS)} requested)")
    
    # Count
    count_row = sqlite_conn.execute("SELECT COUNT(*) as cnt FROM unified_articles").fetchone()
    total = count_row['cnt']
    logger.info(f"Total articles in SQLite: {total}")
    
    if dry_run:
        logger.info("Dry run — no data written")
        sqlite_conn.close()
        return
    
    # Read from SQLite
    sql_select = f"SELECT {', '.join(cols)} FROM unified_articles ORDER BY id"
    if limit:
        sql_select += f" LIMIT {limit}"
    
    rows = sqlite_conn.execute(sql_select).fetchall()
    logger.info(f"Read {len(rows)} articles from SQLite")
    
    if not rows:
        logger.info("Nothing to migrate")
        sqlite_conn.close()
        return
    
    # Write to Neon
    neon_conn = get_neon_conn()
    cur = neon_conn.cursor()
    
    placeholders = ', '.join(['%s'] * len(cols))
    col_list = ', '.join(cols)
    
    # UPSERT: on conflict(url) do update
    update_set = ', '.join([f"{c} = EXCLUDED.{c}" for c in cols if c != 'url'])
    
    insert_sql = (
        f"INSERT INTO unified_articles ({col_list}) VALUES ({placeholders}) "
        f"ON CONFLICT (url) DO UPDATE SET {update_set}"
    )
    
    # First ensure unique constraint on url exists
    try:
        cur.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_ua_url_unique ON unified_articles (url)"
        )
        neon_conn.commit()
    except Exception as e:
        logger.warning(f"Could not create unique index on url: {e}")
        neon_conn.rollback()
    
    batch_size = 50
    inserted = 0
    
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        for row in batch:
            values = tuple(row[c] for c in cols)
            try:
                cur.execute(insert_sql, values)
                inserted += 1
            except Exception as e:
                logger.warning(f"Row error: {e}")
                neon_conn.rollback()
                # Try individual insert without UPSERT
                try:
                    simple_sql = f"INSERT INTO unified_articles ({col_list}) VALUES ({placeholders})"
                    cur.execute(simple_sql, values)
                    inserted += 1
                except Exception:
                    pass
        
        neon_conn.commit()
        logger.info(f"  Migrated {min(i + batch_size, len(rows))}/{len(rows)}")
    
    logger.info(f"✅ Migrated {inserted} articles to Neon")
    
    cur.close()
    neon_conn.close()
    sqlite_conn.close()


def migrate_supporting_tables(dry_run=False):
    """Migrate alerts, conflict_zones, gpr_index."""
    if dry_run:
        logger.info("Dry run — skipping supporting tables")
        return

    sqlite_conn = get_sqlite_conn()
    neon_conn = get_neon_conn()
    cur = neon_conn.cursor()

    for table in ['alerts', 'conflict_zones', 'enrichment_log', 'gpr_index']:
        try:
            actual_cols = discover_columns(sqlite_conn, table)
            if not actual_cols:
                logger.info(f"  Skipping {table} (not found in SQLite)")
                continue

            cols = sorted(actual_cols - {'id'})  # skip auto-increment id
            rows = sqlite_conn.execute(
                f"SELECT {', '.join(cols)} FROM {table}"
            ).fetchall()

            if not rows:
                logger.info(f"  {table}: 0 rows")
                continue

            placeholders = ', '.join(['%s'] * len(cols))
            col_list = ', '.join(cols)
            insert_sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"

            for row in rows:
                values = tuple(row[c] for c in cols)
                try:
                    cur.execute(insert_sql, values)
                except Exception:
                    neon_conn.rollback()

            neon_conn.commit()
            logger.info(f"  {table}: {len(rows)} rows migrated")
        except Exception as e:
            logger.warning(f"  {table}: error — {e}")
            neon_conn.rollback()

    cur.close()
    neon_conn.close()
    sqlite_conn.close()


def main():
    parser = argparse.ArgumentParser(description="Migrate SQLite → Neon Postgres")
    parser.add_argument('--dry-run', action='store_true', help="Count only, don't write")
    parser.add_argument('--limit', type=int, help="Max articles to migrate")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("RiskMap SQLite → Neon Migration")
    logger.info("=" * 60)

    migrate_articles(dry_run=args.dry_run, limit=args.limit)
    migrate_supporting_tables(dry_run=args.dry_run)

    logger.info("Done!")


if __name__ == '__main__':
    main()
