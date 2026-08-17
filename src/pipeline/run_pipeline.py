"""
Riskmap A.I. — Complete Pipeline Orchestrator
=============================================
Chains all pipeline stages in order:
  1. ingest.py   – Fetch news from RSS + NewsAPI
  2. enrich.py   – Classify, geolocate (AI), risk-score, translate
  3. acquire_images.py  – Acquire satellite/GIBS/FIRMS imagery for events
  4. detect.py   – Run YOLO + AI-vision on acquired images

Usage (standalone):
    python -m src.pipeline.run_pipeline            # full pipeline
    python -m src.pipeline.run_pipeline --stages ingest enrich  # subset

Designed to be called:
  - From a cron / scheduler every 1-2 hours
  - From RISKMAP.py background thread
  - Manually for testing
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime

# Ensure project root is on path
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [PIPELINE] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Stage runners — each returns (articles_affected: int, elapsed_s: float)
# ---------------------------------------------------------------------------

def run_ingest() -> tuple:
    """Stage 1 — Ingest news from RSS feeds + NewsAPI."""
    t0 = time.time()
    try:
        from src.pipeline.ingest import main as ingest_main
        count = ingest_main()
        elapsed = time.time() - t0
        logger.info(f"  Stage 1 INGEST    ✅  {count} articles  ({elapsed:.1f}s)")
        return count, elapsed
    except Exception as exc:
        elapsed = time.time() - t0
        logger.error(f"  Stage 1 INGEST    ❌  {exc}  ({elapsed:.1f}s)")
        return 0, elapsed


def run_enrich() -> tuple:
    """Stage 2 — Geopolitical scoring, AI location extraction, translation."""
    t0 = time.time()
    try:
        from src.pipeline.enrich import enrich_articles, translate_articles
        enriched = enrich_articles()
        translated = translate_articles()
        elapsed = time.time() - t0
        logger.info(
            f"  Stage 2 ENRICH    ✅  {enriched} enriched, {translated} translated  ({elapsed:.1f}s)"
        )
        return enriched, elapsed
    except Exception as exc:
        elapsed = time.time() - t0
        logger.error(f"  Stage 2 ENRICH    ❌  {exc}  ({elapsed:.1f}s)")
        return 0, elapsed


def run_acquire() -> tuple:
    """Stage 3 — Acquire satellite imagery for active AOIs / event locations."""
    t0 = time.time()
    try:
        from src.pipeline.acquire_images import main as acquire_main
        acquire_main()
        elapsed = time.time() - t0
        logger.info(f"  Stage 3 ACQUIRE   ✅  imagery acquired  ({elapsed:.1f}s)")
        return 1, elapsed
    except Exception as exc:
        elapsed = time.time() - t0
        logger.error(f"  Stage 3 ACQUIRE   ❌  {exc}  ({elapsed:.1f}s)")
        return 0, elapsed


def run_detect() -> tuple:
    """Stage 4 — YOLO + AI-vision detection on unprocessed images."""
    t0 = time.time()
    try:
        from src.pipeline.detect import process_undetected_images
        count = process_undetected_images()
        elapsed = time.time() - t0
        logger.info(f"  Stage 4 DETECT    ✅  {count} images processed  ({elapsed:.1f}s)")
        return count, elapsed
    except Exception as exc:
        elapsed = time.time() - t0
        logger.error(f"  Stage 4 DETECT    ❌  {exc}  ({elapsed:.1f}s)")
        return 0, elapsed


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

STAGE_MAP = {
    'ingest': run_ingest,
    'enrich': run_enrich,
    'acquire': run_acquire,
    'detect': run_detect,
}

ALL_STAGES = ['ingest', 'enrich', 'acquire', 'detect']


def run_pipeline(stages=None):
    """Run the complete (or partial) pipeline. Returns summary dict."""
    stages = stages or ALL_STAGES

    started = datetime.utcnow().isoformat()
    logger.info("=" * 60)
    logger.info("🌍 Riskmap A.I. — Pipeline started")
    logger.info(f"   Stages: {', '.join(stages)}")
    logger.info("=" * 60)

    results = {}
    total_start = time.time()

    for stage_name in stages:
        fn = STAGE_MAP.get(stage_name)
        if fn is None:
            logger.warning(f"Unknown stage: {stage_name}")
            continue
        count, elapsed = fn()
        results[stage_name] = {'count': count, 'elapsed_s': round(elapsed, 2)}

    total_elapsed = time.time() - total_start
    summary = {
        'started_at': started,
        'finished_at': datetime.utcnow().isoformat(),
        'total_elapsed_s': round(total_elapsed, 2),
        'stages': results,
    }

    logger.info("=" * 60)
    logger.info(f"✅ Pipeline finished in {total_elapsed:.1f}s")
    logger.info("=" * 60)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Riskmap pipeline runner')
    parser.add_argument(
        '--stages',
        nargs='+',
        choices=ALL_STAGES,
        default=ALL_STAGES,
        help='Pipeline stages to run (default: all)',
    )
    args = parser.parse_args()
    result = run_pipeline(args.stages)
    import json
    print(json.dumps(result, indent=2))
