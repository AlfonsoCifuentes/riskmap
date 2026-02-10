"""
RiskMap Data Ingestion Pipeline
=================================
Fetches articles from RSS feeds + NewsAPI, deduplicates, stores in DB.
Designed to run as a GitHub Actions step or standalone.

Usage:
    python -m src.pipeline.ingest
"""

import os
import sys
import json
import hashlib
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests
import feedparser

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.connection import get_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [INGEST] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# RSS Feeds — curated geopolitical intelligence sources
# ---------------------------------------------------------------------------

RSS_FEEDS = [
    # Global conflict / security
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://feeds.reuters.com/reuters/worldNews",
    "https://www.theguardian.com/world/rss",
    # Defense / intelligence
    "https://www.defensenews.com/arc/outboundfeeds/rss/?outputType=xml",
    "https://www.janes.com/feeds/news",
    # Think tanks
    "https://www.crisisgroup.org/rss.xml",
    "https://www.brookings.edu/feed/",
    "https://carnegieendowment.org/rss/solr/?lang=en",
    # Disaster / humanitarian
    "https://reliefweb.int/updates/rss.xml",
    "https://www.gdacs.org/xml/rss.xml",
    # Regional
    "https://www.middleeasteye.net/rss",
    "https://www.scmp.com/rss/91/feed",
]


def _url_hash(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


def fetch_rss() -> List[Dict]:
    """Fetch articles from all RSS feeds."""
    articles = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url, agent="RiskMap/1.0")
            source = feed.feed.get("title", feed_url)[:80]
            for entry in feed.entries[:20]:  # max 20 per feed
                pub = entry.get("published_parsed") or entry.get("updated_parsed")
                published_at = None
                if pub:
                    try:
                        published_at = datetime(*pub[:6]).isoformat()
                    except Exception:
                        pass

                articles.append({
                    'title': entry.get('title', '')[:500],
                    'content': entry.get('summary', entry.get('description', ''))[:5000],
                    'summary': entry.get('summary', '')[:1000],
                    'url': entry.get('link', ''),
                    'source': source,
                    'published_at': published_at or datetime.utcnow().isoformat(),
                    'image_url': _extract_image(entry),
                    'language': 'en',
                })
            logger.info(f"  ✓ {source}: {len(feed.entries)} entries")
        except Exception as e:
            logger.warning(f"  ✗ {feed_url}: {e}")
    return articles


def _extract_image(entry) -> Optional[str]:
    """Try to extract an image URL from an RSS entry."""
    # media:content
    media = entry.get('media_content', [])
    for m in media:
        url = m.get('url', '')
        if url and re.match(r'https?://', url):
            return url
    # media:thumbnail
    thumb = entry.get('media_thumbnail', [])
    for t in thumb:
        url = t.get('url', '')
        if url and re.match(r'https?://', url):
            return url
    # enclosures
    for enc in entry.get('enclosures', []):
        if enc.get('type', '').startswith('image/'):
            return enc.get('href', enc.get('url', ''))
    return None


def fetch_newsapi() -> List[Dict]:
    """Fetch from NewsAPI (free tier: 100 req/day)."""
    api_key = os.getenv('NEWSAPI_KEY', '')
    if not api_key:
        logger.info("  NewsAPI key not set, skipping")
        return []

    articles = []
    queries = [
        'geopolitical conflict',
        'military operation',
        'natural disaster emergency',
        'humanitarian crisis',
    ]

    for q in queries:
        try:
            resp = requests.get(
                'https://newsapi.org/v2/everything',
                params={
                    'q': q,
                    'language': 'en',
                    'sortBy': 'publishedAt',
                    'pageSize': 15,
                    'apiKey': api_key,
                },
                timeout=15,
            )
            data = resp.json()
            for art in data.get('articles', []):
                articles.append({
                    'title': (art.get('title') or '')[:500],
                    'content': (art.get('content') or art.get('description') or '')[:5000],
                    'summary': (art.get('description') or '')[:1000],
                    'url': art.get('url', ''),
                    'source': art.get('source', {}).get('name', 'NewsAPI'),
                    'published_at': art.get('publishedAt', datetime.utcnow().isoformat()),
                    'image_url': art.get('urlToImage'),
                    'language': 'en',
                })
            logger.info(f"  ✓ NewsAPI [{q}]: {len(data.get('articles', []))} articles")
        except Exception as e:
            logger.warning(f"  ✗ NewsAPI [{q}]: {e}")

    return articles


def store_articles(articles: List[Dict]):
    """Deduplicate and insert articles into unified_articles."""
    db = get_db()
    ph = db.placeholder

    # Get existing URLs for dedup
    existing = set()
    try:
        rows = db.execute("SELECT url FROM unified_articles", fetch=True)
        existing = {r['url'] for r in rows if r.get('url')}
    except Exception:
        pass

    inserted = 0
    for art in articles:
        url = art.get('url', '')
        if not url or url in existing:
            continue

        try:
            db.execute(
                f"""INSERT INTO unified_articles
                    (title, content, summary, url, source, published_at,
                     image_url, language, geopolitical_relevance, created_at)
                    VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph}, 0, {ph})""",
                (
                    art['title'], art['content'], art['summary'],
                    url, art['source'], art['published_at'],
                    art.get('image_url'), art.get('language', 'en'),
                    datetime.utcnow().isoformat(),
                ),
            )
            existing.add(url)
            inserted += 1
        except Exception as e:
            logger.debug(f"Insert error: {e}")

    logger.info(f"✅ Inserted {inserted} new articles (of {len(articles)} fetched)")

    # Extract og:image for articles that don't already have one
    if inserted > 0:
        try:
            from api._og_image import extract_og_image
            rows = db.execute(
                "SELECT id, url FROM unified_articles "
                "WHERE (image_url IS NULL OR image_url = '') "
                "AND url IS NOT NULL AND url != '' "
                "ORDER BY id DESC LIMIT 50",
                fetch=True,
            )
            enriched = 0
            for row in rows:
                aid, url = row['id'], row['url']
                img = extract_og_image(url)
                if img:
                    db.execute(
                        f"UPDATE unified_articles SET image_url={ph}, "
                        f"original_image_url={ph}, has_image=1 WHERE id={ph}",
                        (img, img, aid),
                    )
                    enriched += 1
            if enriched:
                logger.info(f"🖼️ Extracted og:image for {enriched}/{len(rows)} articles")
        except Exception as e:
            logger.warning(f"⚠️ og:image extraction failed: {e}")

    # Classify articles as geopolitical or not
    if inserted > 0:
        _classify_geopolitical(db, ph)

    return inserted


# ---------------------------------------------------------------------------
# Geopolitical classification — keyword-based filtering
# ---------------------------------------------------------------------------

# Non-geopolitical keyword patterns (reject if title matches)
_NON_GEO_PATTERNS = [
    # Sports
    r'\bNFL\b', r'\bNBA\b', r'\bMLB\b', r'\bNHL\b', r'\bUEFA\b.*LIVE',
    r'\bSuper Bowl\b', r'\btouchdown\b', r'\bquarterback\b',
    r'\bpower ranking', r'\bfantasy football\b', r'\bearly odds\b',
    r'\bWorld Series\b', r'\bPremier League\b', r'\bChampions League\b.*LIVE',
    r'\bCoachella\b', r'\bSuper Bowl\b',
    # Entertainment
    r'\bEmmy\b', r'\bOscar\b(?!.*war|.*conflict|.*sanction)',
    r'\bGrammy\b', r'\bbox office\b', r'\bNetflix\b(?!.*censor|.*ban)',
    r'\bstreaming service\b', r'\bred carpet\b', r'\balfombra roja\b',
    # Celebrity gossip
    r'\bCardi B\b', r'\bTaylor Swift\b(?!.*politic|.*endorse)',
    r'\bBieber\b', r'\bKardashian\b',
    r'\bembarazo\b(?!.*crisis|.*refugee)', r'\bpregnancy\b(?!.*crisis)',
    # Consumer tech
    r'\biPhone\b.*(?:preorder|review|stock|spec)',
    r'\bSnapdragon\b', r'\bAndroid\b.*(?:update|review|spec)',
    # Local crime (not geopolitical)
    r'found dead in (?:suitcase|trunk|car)',
    r'matar a (?:ex )?novi[oa]', r'flesh-eating.*Vibrio',
    # Pure sports sources articles
    r'\bJoe Burrow\b', r'\bTom Brady\b', r'\bPete Carroll\b',
]

# Sources that are NEVER geopolitical
_NON_GEO_SOURCES = {
    'CBS Sports', 'NBCSports.com', 'ESPN', 'The Ringer', 'Ed.gov',
    'Pff.com', 'Sports Illustrated', 'Bleacher Report',
}


def _classify_geopolitical(db, ph):
    """Classify newly inserted articles (geopolitical_relevance=0) using keywords."""
    rows = db.execute(
        "SELECT id, title, source FROM unified_articles "
        "WHERE geopolitical_relevance = 0 "
        "ORDER BY id DESC LIMIT 200",
        fetch=True,
    )
    if not rows:
        return

    geo_ids = []
    non_geo_ids = []

    for row in rows:
        aid = row['id']
        title = row.get('title') or ''
        source = row.get('source') or ''

        # Reject non-geo sources
        if source in _NON_GEO_SOURCES:
            non_geo_ids.append(aid)
            continue

        # Reject non-geo title patterns
        is_non_geo = False
        for pattern in _NON_GEO_PATTERNS:
            if re.search(pattern, title, re.IGNORECASE):
                is_non_geo = True
                break

        if is_non_geo:
            non_geo_ids.append(aid)
        else:
            geo_ids.append(aid)

    # Mark geopolitical articles
    if geo_ids:
        placeholders = ','.join([ph] * len(geo_ids))
        db.execute(
            f"UPDATE unified_articles SET geopolitical_relevance = 1 "
            f"WHERE id IN ({placeholders})",
            tuple(geo_ids),
        )

    logger.info(
        f"🏷️ Classified: {len(geo_ids)} geopolitical, "
        f"{len(non_geo_ids)} non-geopolitical"
    )


def main():
    logger.info("=" * 60)
    logger.info("RiskMap Data Ingestion Pipeline")
    logger.info("=" * 60)

    logger.info("Fetching RSS feeds…")
    rss_articles = fetch_rss()

    logger.info("Fetching NewsAPI…")
    news_articles = fetch_newsapi()

    all_articles = rss_articles + news_articles
    logger.info(f"Total fetched: {len(all_articles)}")

    inserted = store_articles(all_articles)
    logger.info(f"Pipeline complete — {inserted} new articles stored")


if __name__ == '__main__':
    main()
