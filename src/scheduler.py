"""Global scheduler for Riskmap data ingestion.

Runs near-real-time feeds every 10 minutes and historical updates monthly.
Use APScheduler to manage jobs.

Usage:
    python -m scheduler
"""

from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from utils.config import config, logger
from pathlib import Path

# Import ingestion functions
# Ensure src package root in path when executed as script
if __name__ == "__main__" and __package__ is None:
    import importlib.util, sys
    from pathlib import Path
    src_root = Path(__file__).resolve().parent
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))

from .data_ingestion.ingest_all_sources import (
    fetch_gdelt_events, fetch_usgs_earthquakes, fetch_emsc_earthquakes,
    fetch_gdacs_events, store_events
)
from .data_ingestion.social import ingest_social
from .data_ingestion.historical import fetch_ucdp_conflicts, store_historical
from .data_ingestion.who_disease import fetch_who_outbreaks
from .data_ingestion.energy import fetch_oil_production, store_energy
from .data_ingestion.emdat import fetch_emdat_disasters, store_emdat
from .analytics.risk_index import calc_risk

# Import RSS fetcher
from .data_ingestion.rss_fetcher import RSSFetcher


def ingest_realtime():
    """Fetch and store real-time (≤24h) events every 10 minutes."""
    logger.info("[Scheduler] Running real-time ingestion …")
    try:
        # Traditional event sources
        events = []
        events += fetch_gdelt_events(days=1)
        events += fetch_usgs_earthquakes(hours=24)
        events += fetch_emsc_earthquakes()
        events += fetch_gdacs_events()
        ingest_social()
        store_events(events, table="events")
        logger.info(f"[Scheduler] Stored {len(events)} realtime events.")
        
        # RSS News ingestion
        try:
            # Get database path
            BASE_DIR = Path(__file__).resolve().parents[1]
            DB_PATH = str(BASE_DIR / 'data' / 'geopolitical_intel.db')
            
            # Get target language from config (default to Spanish)
            target_language = config.get('dashboard.language', 'es')
            
            # Create RSS fetcher and fetch all sources
            rss_fetcher = RSSFetcher(DB_PATH)
            rss_results = rss_fetcher.fetch_all_sources(target_language=target_language)
            
            logger.info(f"[Scheduler] RSS ingestion completed: {rss_results}")
            
        except Exception as rss_exc:
            logger.error(f"[Scheduler] RSS ingestion error: {rss_exc}")
        
    except Exception as exc:
        logger.error(f"[Scheduler] Realtime ingestion error: {exc}")


def ingest_historical():
    """Fetch and store historical updates once a month (1st day)."""
    logger.info("[Scheduler] Running monthly historical ingestion …")
    try:
        conflicts = fetch_ucdp_conflicts()
        store_historical(conflicts)
        logger.info(f"[Scheduler] Stored {len(conflicts)} historical conflict events.")
    except Exception as exc:
        logger.error(f"[Scheduler] Historical ingestion error: {exc}")


def main():
    scheduler = BlockingScheduler(timezone="UTC")

    # Realtime ingest every 10 minutes
    scheduler.add_job(ingest_realtime, IntervalTrigger(minutes=10), id="realtime_ingest", max_instances=1, replace_existing=True)

    # Historical ingest on the first day of each month at 02:00 UTC
    scheduler.add_job(ingest_historical, CronTrigger(day=1, hour=2, minute=0), id="historical_ingest", max_instances=1, replace_existing=True)

    # Alert evaluation every 10 minutes
    from .alerts.engine import evaluate_rules  # lazy import
    scheduler.add_job(evaluate_rules, IntervalTrigger(minutes=10), id="alert_eval", replace_existing=True)

    # Daily risk index calculation at 03:00 UTC
    scheduler.add_job(calc_risk, CronTrigger(hour=3), id="risk_daily", replace_existing=True)

    logger.info("[Scheduler] Starting scheduler …")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("[Scheduler] Shutdown.")


if __name__ == "__main__":
    main()
