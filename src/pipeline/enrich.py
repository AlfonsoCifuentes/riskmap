"""
Riskmap A.I. NLP Enrichment Pipeline
==================================
Enriches raw articles with: geopolitical relevance scoring, sentiment,
conflict-type classification, location inference, AI summaries.

Designed to run after ingest.py as a GitHub Actions step.

Usage:
    python -m src.pipeline.enrich
"""

import os
import sys
import json
import logging
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.connection import get_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [ENRICH] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Geopolitical keyword scoring
# ---------------------------------------------------------------------------

GEO_KEYWORDS = {
    # High-signal conflict terms (weight 3)
    3: [
        'military', 'invasion', 'airstrike', 'missile', 'warplane', 'drone strike',
        'bombing', 'shelling', 'troops', 'soldiers', 'casualties', 'killed',
        'ceasefire', 'sanctions', 'coup', 'rebellion', 'insurgency', 'terrorism',
        'nuclear', 'chemical weapons', 'war crimes', 'genocide', 'ethnic cleansing',
        'humanitarian crisis', 'refugee', 'displacement', 'occupation',
    ],
    # Medium-signal (weight 2)
    2: [
        'conflict', 'tension', 'escalation', 'provocation', 'deployment',
        'defense', 'security', 'intelligence', 'espionage', 'cyber attack',
        'border', 'territorial', 'sovereignty', 'arms', 'weapons',
        'protest', 'unrest', 'riot', 'crackdown', 'opposition',
        'natural disaster', 'earthquake', 'tsunami', 'hurricane', 'typhoon',
        'flood', 'wildfire', 'volcanic', 'landslide', 'cyclone',
    ],
    # Low-signal (weight 1)
    1: [
        'diplomatic', 'negotiations', 'summit', 'treaty', 'alliance',
        'trade war', 'embargo', 'blockade', 'geopolitical', 'strategy',
        'emergency', 'evacuation', 'rescue', 'relief', 'aid',
    ],
}

CONFLICT_TYPES = {
    'armed_conflict': ['military', 'war', 'invasion', 'troops', 'airstrike', 'bombing', 'soldiers'],
    'terrorism': ['terrorism', 'terrorist', 'extremist', 'bombing', 'insurgency', 'militant'],
    'civil_unrest': ['protest', 'riot', 'unrest', 'crackdown', 'demonstration', 'opposition'],
    'cyber': ['cyber attack', 'hacking', 'cyber warfare', 'cyber espionage'],
    'diplomatic': ['sanctions', 'diplomatic', 'negotiations', 'treaty', 'summit'],
    'humanitarian': ['humanitarian', 'refugee', 'displacement', 'famine', 'crisis'],
    'natural_disaster': ['earthquake', 'flood', 'hurricane', 'wildfire', 'tsunami', 'volcanic'],
}

# Rough country → coords mapping for location inference
COUNTRY_COORDS = {
    'ukraine': (48.38, 31.17), 'russia': (55.75, 37.62),
    'israel': (31.77, 35.21), 'palestine': (31.95, 35.20), 'gaza': (31.50, 34.47),
    'iran': (35.69, 51.39), 'iraq': (33.31, 44.37), 'syria': (33.51, 36.29),
    'yemen': (15.37, 44.19), 'lebanon': (33.89, 35.50),
    'china': (39.90, 116.40), 'taiwan': (25.03, 121.57),
    'north korea': (39.02, 125.75), 'south korea': (37.57, 127.00),
    'afghanistan': (34.53, 69.17), 'pakistan': (33.69, 73.04),
    'myanmar': (19.76, 96.07), 'sudan': (15.50, 32.56),
    'ethiopia': (9.02, 38.75), 'somalia': (2.05, 45.32),
    'libya': (32.90, 13.18), 'mali': (12.64, -8.00),
    'niger': (13.51, 2.13), 'nigeria': (9.06, 7.49),
    'congo': (-4.32, 15.31), 'mozambique': (-25.97, 32.57),
    'haiti': (18.54, -72.34), 'venezuela': (10.49, -66.88),
    'mexico': (19.43, -99.13), 'colombia': (4.71, -74.07),
    'turkey': (39.93, 32.86), 'india': (28.61, 77.21),
}


def score_geopolitical(text: str) -> Tuple[float, bool]:
    """Return (score 0-1, is_geopolitical) based on keyword presence."""
    text_lower = text.lower()
    total = 0
    for weight, keywords in GEO_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                total += weight
    # Normalize: 15+ = definitely geopolitical
    score = min(total / 15.0, 1.0)
    return round(score, 3), score >= 0.25


def classify_conflict(text: str) -> Optional[str]:
    """Return the most likely conflict type."""
    text_lower = text.lower()
    best_type = None
    best_count = 0
    for ctype, keywords in CONFLICT_TYPES.items():
        count = sum(1 for kw in keywords if kw in text_lower)
        if count > best_count:
            best_count = count
            best_type = ctype
    return best_type if best_count >= 2 else None


def simple_sentiment(text: str) -> Tuple[str, float]:
    """Very basic sentiment: negative / neutral / positive with score."""
    text_lower = text.lower()
    neg_words = ['killed', 'dead', 'attack', 'destroy', 'crisis', 'war', 'threat',
                 'bomb', 'victims', 'casualties', 'collapse', 'disaster', 'devastat']
    pos_words = ['peace', 'agreement', 'rescue', 'recovery', 'aid', 'ceasefire',
                 'rebuild', 'cooperation', 'progress', 'stability']

    neg = sum(1 for w in neg_words if w in text_lower)
    pos = sum(1 for w in pos_words if w in text_lower)

    score = (pos - neg) / max(pos + neg, 1)
    if score < -0.2:
        return 'negative', round(score, 3)
    elif score > 0.2:
        return 'positive', round(score, 3)
    return 'neutral', round(score, 3)


def infer_location(text: str) -> Tuple[Optional[str], Optional[float], Optional[float]]:
    """Infer country and coordinates from article text."""
    text_lower = text.lower()
    for country, (lat, lon) in COUNTRY_COORDS.items():
        if country in text_lower:
            return country.title(), lat, lon
    return None, None, None


def enrich_with_ai(title: str, content: str) -> Optional[str]:
    """Generate a brief AI summary using Groq (Llama 3.1)."""
    api_key = os.getenv('GROQ_API_KEY', '')
    if not api_key:
        return None

    try:
        import requests
        resp = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'llama-3.1-70b-versatile',
                'messages': [
                    {'role': 'system', 'content': (
                        'You are a geopolitical analyst. Provide a 2-sentence summary '
                        'of the following article, highlighting key actors, locations, '
                        'and geopolitical implications.'
                    )},
                    {'role': 'user', 'content': f"Title: {title}\n\n{content[:2000]}"},
                ],
                'max_tokens': 150,
                'temperature': 0.3,
            },
            timeout=15,
        )
        data = resp.json()
        return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        logger.debug(f"AI summary failed: {e}")
        return None


def enrich_articles():
    """Enrich un-enriched articles in the database."""
    db = get_db()
    ph = db.placeholder

    # Get articles not yet enriched
    rows = db.execute(
        "SELECT id, title, content, summary FROM unified_articles "
        f"WHERE enrichment_status IS NULL OR enrichment_status = '' "
        "ORDER BY id DESC LIMIT 100",
        fetch=True,
    )
    logger.info(f"Found {len(rows)} articles to enrich")

    enriched = 0
    ai_count = 0

    for row in rows:
        article_id = row['id']
        text = f"{row.get('title', '')} {row.get('content', '')} {row.get('summary', '')}"

        # Geopolitical scoring
        risk_score, is_geo = score_geopolitical(text)
        conflict_type = classify_conflict(text)
        sentiment, sentiment_score = simple_sentiment(text)
        country, lat, lon = infer_location(text)

        # Risk level
        if risk_score >= 0.7:
            risk_level = 'critical'
        elif risk_score >= 0.5:
            risk_level = 'high'
        elif risk_score >= 0.3:
            risk_level = 'medium'
        else:
            risk_level = 'low'

        # AI summary (rate-limited)
        ai_summary = None
        if is_geo and ai_count < 20:  # max 20 AI calls per run
            ai_summary = enrich_with_ai(row.get('title', ''), row.get('content', ''))
            if ai_summary:
                ai_count += 1

        # Update article
        db.execute(
            f"""UPDATE unified_articles SET
                geopolitical_relevance = {ph},
                risk_score = {ph},
                risk_level = {ph},
                conflict_type = {ph},
                ai_sentiment = {ph},
                sentiment_score = {ph},
                country = COALESCE(country, {ph}),
                latitude = COALESCE(latitude, {ph}),
                longitude = COALESCE(longitude, {ph}),
                ai_summary = COALESCE(ai_summary, {ph}),
                enrichment_status = 'enriched',
                quality_score = {ph}
            WHERE id = {ph}""",
            (
                1 if is_geo else 0,
                risk_score,
                risk_level,
                conflict_type,
                sentiment,
                sentiment_score,
                country,
                lat,
                lon,
                ai_summary,
                risk_score,  # quality_score = risk_score as baseline
                article_id,
            ),
        )
        enriched += 1

    logger.info(f"✅ Enriched {enriched} articles ({ai_count} with AI summaries)")

    # Create events from high-relevance articles
    _create_events_from_articles(db)

    return enriched


def _create_events_from_articles(db):
    """Group recent high-risk articles into events."""
    ph = db.placeholder

    rows = db.execute(
        "SELECT id, title, conflict_type, country, latitude, longitude, risk_score "
        "FROM unified_articles "
        "WHERE geopolitical_relevance = 1 AND risk_score >= 0.5 "
        "  AND event_id IS NULL "
        "ORDER BY published_at DESC LIMIT 50",
        fetch=True,
    )

    if not rows:
        return

    # Group by country + conflict_type
    groups = {}
    for r in rows:
        key = (r.get('country', 'Unknown'), r.get('conflict_type', 'unknown'))
        groups.setdefault(key, []).append(r)

    created = 0
    for (country, ctype), articles in groups.items():
        if len(articles) < 1:
            continue

        ctype = ctype or 'unknown'
        is_disaster = ctype == 'natural_disaster'
        event_type = 'disaster' if is_disaster else 'conflict'
        avg_score = sum(a.get('risk_score', 0) for a in articles) / len(articles)
        title = f"{ctype.replace('_', ' ').title()} — {country}" if country else ctype

        # Insert event
        cur = db.execute(
            f"""INSERT INTO events (event_type, subtype, title, severity, started_at, explanation)
                VALUES ({ph},{ph},{ph},{ph},{ph},{ph})""",
            (event_type, ctype, title, avg_score,
             datetime.utcnow().isoformat(),
             f"Auto-generated from {len(articles)} articles"),
        )

        # Get the event ID
        if db.backend_name == 'postgres':
            # For Postgres, we need to query the last inserted ID
            event_rows = db.execute(
                "SELECT id FROM events ORDER BY id DESC LIMIT 1", fetch=True
            )
            event_id = event_rows[0]['id'] if event_rows else None
        else:
            event_id = cur.lastrowid

        if event_id:
            # Link articles
            article_ids = [a['id'] for a in articles]
            for aid in article_ids:
                db.execute(
                    f"UPDATE unified_articles SET event_id = {ph} WHERE id = {ph}",
                    (event_id, aid),
                )

            # Create event location
            for a in articles:
                if a.get('latitude') and a.get('longitude'):
                    db.execute(
                        f"""INSERT INTO event_locations
                            (event_id, latitude, longitude, name, source)
                            VALUES ({ph},{ph},{ph},{ph},'article')""",
                        (event_id, a['latitude'], a['longitude'],
                         a.get('country', '')),
                    )
                    break  # one location per event for now

            created += 1

    logger.info(f"✅ Created {created} events from article clusters")


# ---------------------------------------------------------------------------
# Translation: auto-translate non-Spanish articles using Groq
# ---------------------------------------------------------------------------

_SPANISH_STOPS = frozenset([
    'de', 'la', 'el', 'los', 'las', 'en', 'por', 'con', 'que', 'del',
    'para', 'una', 'un', 'es', 'se', 'al', 'como', 'pero', 'su',
    'le', 'ya', 'son', 'fue', 'ser', 'hay', 'muy', 'cada', 'sobre',
])


def _is_likely_spanish(text: str) -> bool:
    """Quick heuristic: check for common Spanish stopwords."""
    words = text.lower().split()
    if len(words) < 3:
        return False
    count = sum(1 for w in words if w in _SPANISH_STOPS)
    return count >= 2 and (count / len(words)) >= 0.12


def _detect_script_lang(text: str) -> str:
    """Detect language from non-Latin character scripts."""
    for ch in text:
        cp = ord(ch)
        if 0x0400 <= cp <= 0x04FF: return 'ru'
        if 0x0600 <= cp <= 0x06FF: return 'ar'
        if 0x4E00 <= cp <= 0x9FFF: return 'zh'
        if 0x0900 <= cp <= 0x097F: return 'hi'
        if 0x0370 <= cp <= 0x03FF: return 'el'
        if 0x3040 <= cp <= 0x30FF: return 'ja'
        if 0xAC00 <= cp <= 0xD7AF: return 'ko'
    return ''


def _translate_via_groq(title: str, summary: str, api_key: str):
    """Translate title + summary to Spanish in one Groq API call.

    Returns (new_title, new_summary, detected_lang) or None on error.
    """
    import requests as _req

    text_block = f"TITLE: {title}"
    has_summary = (summary and summary.strip() != title.strip()
                   and len(summary.strip()) > 15)
    if has_summary:
        text_block += f"\nSUMMARY: {summary[:800]}"

    try:
        resp = _req.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'llama-3.1-8b-instant',
                'messages': [
                    {'role': 'system', 'content': (
                        'You are a professional translator. Translate to Spanish.\n'
                        'RULES:\n'
                        '- If the text is already in Spanish, return it unchanged.\n'
                        '- Preserve proper nouns, acronyms, numbers, and place names.\n'
                        '- Reply ONLY with:\n'
                        'LANG: <ISO 639-1 code of the source language>\n'
                        'TITLE: <Spanish translation of title>\n'
                        'SUMMARY: <Spanish translation of summary>\n'
                        '- If no SUMMARY was given, omit the SUMMARY line.'
                    )},
                    {'role': 'user', 'content': text_block},
                ],
                'max_tokens': 400,
                'temperature': 0.1,
            },
            timeout=20,
        )
        content = resp.json()['choices'][0]['message']['content'].strip()

        lang = ''
        new_title = title
        new_summary = summary

        for line in content.split('\n'):
            stripped = line.strip()
            upper = stripped.upper()
            if upper.startswith('LANG:'):
                lang = stripped.split(':', 1)[1].strip().lower()[:5]
            elif upper.startswith('TITLE:'):
                val = stripped.split(':', 1)[1].strip()
                if val:
                    new_title = val
            elif upper.startswith('SUMMARY:'):
                val = stripped.split(':', 1)[1].strip()
                if val:
                    new_summary = val

        return new_title, new_summary, lang
    except Exception as e:
        logger.debug(f"Translation API error: {e}")
        return None


def translate_articles():
    """Translate non-Spanish articles to Spanish using Groq API."""
    db = get_db()
    ph = db.placeholder
    api_key = os.getenv('GROQ_API_KEY', '')

    if not api_key:
        logger.info('⏭ No GROQ_API_KEY — skipping translation')
        return 0

    rows = db.execute(
        "SELECT id, title, summary, language FROM unified_articles "
        "WHERE (is_translated IS NULL OR is_translated = 0) "
        "ORDER BY id DESC LIMIT 60",
        fetch=True,
    )

    if not rows:
        logger.info('No articles need translation')
        return 0

    logger.info(f"Found {len(rows)} articles to check for translation")

    translated = 0
    skipped_es = 0

    for row in rows:
        title = (row.get('title') or '').strip()
        summary = (row.get('summary') or '').strip()

        if not title:
            continue

        # Skip if already in Spanish
        if _is_likely_spanish(title):
            db.execute(
                f"UPDATE unified_articles SET language = 'es', is_translated = 0 "
                f"WHERE id = {ph}",
                (row['id'],),
            )
            skipped_es += 1
            continue

        # Translate via Groq
        result = _translate_via_groq(title, summary, api_key)
        if result is None:
            continue

        new_title, new_summary, orig_lang = result

        if not orig_lang:
            orig_lang = _detect_script_lang(title) or 'en'

        db.execute(
            f"""UPDATE unified_articles SET
                title = {ph},
                summary = {ph},
                language = 'es',
                original_language = {ph},
                is_translated = 1,
                processing_notes = {ph}
            WHERE id = {ph}""",
            (
                new_title,
                new_summary,
                orig_lang,
                f'Original: {title[:200]}',
                row['id'],
            ),
        )
        translated += 1

        # Rate limit: ~2 seconds between Groq calls
        time.sleep(2)

    logger.info(f"✅ Translated {translated} articles, {skipped_es} already Spanish")
    return translated


def main():
    logger.info("=" * 60)
    logger.info("Riskmap A.I. NLP Enrichment Pipeline")
    logger.info("=" * 60)
    enrich_articles()
    translate_articles()
    logger.info("Enrichment complete")


if __name__ == '__main__':
    main()
