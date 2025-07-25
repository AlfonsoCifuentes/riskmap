"""WHO Disease Outbreak News (DON) ingestion.

Parses the official WHO RSS feed of Disease Outbreak News and converts items into
normalized event dictionaries compatible with Riskmap (title, description, url,
date, source, location, type).

Feed: https://www.who.int/feeds/entity/csr/don/en/rss.xml
"""

from datetime import datetime
from typing import List, Dict, Any
import json
import sqlite3

import feedparser
import requests

from utils.config import logger, config
from utils.geo import extract_event_location
from data_ingestion.real_sources import store_events  # reuse DB helper

WHO_RSS = "https://www.who.int/feeds/entity/csr/don/en/rss.xml"


def fetch_who_outbreaks(limit: int = 100) -> List[Dict[str, Any]]:
    """Download and parse WHO Disease Outbreak News RSS feed."""
    try:
        # Sometimes WHO HTTPS handshake fails with feedparser directly; fetch manually
        resp = requests.get(WHO_RSS, timeout=20)
        resp.raise_for_status()
        parsed = feedparser.parse(resp.content)
        events: List[Dict[str, Any]] = []
        for entry in parsed.entries[:limit]:
            title = entry.get("title", "WHO Outbreak")
            description = entry.get("summary", "")
            link = entry.get("link", "")
            published = entry.get("published", "")
            # Attempt location extraction from title/summary
            loc = extract_event_location(title) or extract_event_location(description)
            events.append({
                "title": title,
                "content": description,
                "url": link,
                "published_at": published or datetime.utcnow().isoformat(),
                "source": "WHO DON",
                "location": loc,
                "type": "disease_outbreak"
            })
        return events
    except Exception as exc:
        logger.error(f"[WHO] Error fetching Disease Outbreak News: {exc}")
        return []


if __name__ == "__main__":
    data = fetch_who_outbreaks()
    store_events(data, table="events")
    logger.info(f"[WHO] Stored {len(data)} disease outbreak events.")
