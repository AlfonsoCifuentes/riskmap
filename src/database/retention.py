"""
RiskMap Image Retention Policy
================================
Keeps only the latest image per AOI+source_type.
Deletes expired images.  Designed to run via GitHub Actions cron.

Usage:
    python -m src.database.retention
"""

import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.connection import get_db, _detect_backend

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")
logger = logging.getLogger(__name__)


def enforce_latest_only():
    """Mark older images as not-latest; only keep newest per (aoi_id, source_type)."""
    db = get_db()
    backend = _detect_backend()

    if backend == 'postgres':
        # Subquery: for each (aoi_id, source_type), find max id
        sql = """
        UPDATE images SET is_latest = 0
        WHERE is_latest = 1
          AND id NOT IN (
            SELECT MAX(id)
            FROM images
            GROUP BY COALESCE(aoi_id, -1), COALESCE(event_id, -1), source_type
          )
        """
    else:
        sql = """
        UPDATE images SET is_latest = 0
        WHERE is_latest = 1
          AND id NOT IN (
            SELECT MAX(id)
            FROM images
            GROUP BY COALESCE(aoi_id, -1), COALESCE(event_id, -1), source_type
          )
        """

    db.execute(sql)
    logger.info("✅ Marked older images as not-latest")


def delete_expired():
    """Remove images past their expires_at timestamp."""
    db = get_db()
    backend = _detect_backend()

    if backend == 'postgres':
        sql = "DELETE FROM images WHERE expires_at IS NOT NULL AND expires_at < NOW()"
    else:
        sql = "DELETE FROM images WHERE expires_at IS NOT NULL AND expires_at < datetime('now')"

    db.execute(sql)
    logger.info("✅ Deleted expired images")


def delete_non_latest():
    """Remove images that are no longer the latest (free space)."""
    db = get_db()
    # First delete detections referencing those images
    db.execute("DELETE FROM detections WHERE image_id IN (SELECT id FROM images WHERE is_latest = 0)")
    db.execute("DELETE FROM images WHERE is_latest = 0")
    logger.info("✅ Deleted non-latest images and their detections")


def stats():
    """Print image storage stats."""
    db = get_db()
    rows = db.execute(
        "SELECT source_type, COUNT(*) as cnt, "
        "COALESCE(SUM(image_size_kb), 0) as total_kb "
        "FROM images GROUP BY source_type ORDER BY total_kb DESC",
        fetch=True,
    )
    logger.info("Image storage stats:")
    for r in rows:
        logger.info(f"  {r['source_type']}: {r['cnt']} images, {r['total_kb']:.0f} KB")

    total = db.execute("SELECT COUNT(*) as cnt FROM images", fetch=True)
    logger.info(f"Total images: {total[0]['cnt']}")


def run_retention():
    """Full retention cycle."""
    logger.info("Running retention policy…")
    enforce_latest_only()
    delete_expired()
    delete_non_latest()
    stats()
    logger.info("Retention complete")


if __name__ == '__main__':
    run_retention()
