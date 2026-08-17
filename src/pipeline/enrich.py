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

# Comprehensive country → coords mapping for location inference
# Ordered by geopolitical relevance (conflict zones first for faster matching)
COUNTRY_COORDS = {
    # ── Active conflict zones (highest priority) ──────────────────────────
    'ukraine': (48.38, 31.17), 'russia': (55.75, 37.62),
    'israel': (31.77, 35.21), 'palestine': (31.95, 35.20), 'gaza': (31.50, 34.47),
    'west bank': (31.97, 35.30),
    'iran': (35.69, 51.39), 'iraq': (33.31, 44.37), 'syria': (33.51, 36.29),
    'yemen': (15.37, 44.19), 'lebanon': (33.89, 35.50),
    'north korea': (39.02, 125.75), 'south korea': (37.57, 127.00),
    'taiwan': (25.03, 121.57),
    'afghanistan': (34.53, 69.17), 'pakistan': (33.69, 73.04),
    'myanmar': (19.76, 96.07), 'sudan': (15.50, 32.56),
    'south sudan': (4.85, 31.60), 'ethiopia': (9.02, 38.75),
    'somalia': (2.05, 45.32), 'libya': (32.90, 13.18),
    'mali': (12.64, -8.00), 'niger': (13.51, 2.13),
    'burkina faso': (12.37, -1.53),
    'nigeria': (9.06, 7.49), 'cameroon': (3.85, 11.52),
    'central african republic': (4.36, 18.56),
    'democratic republic of congo': (-4.32, 15.31),
    'drc': (-4.32, 15.31), 'congo': (-4.32, 15.31),
    'mozambique': (-25.97, 32.57), 'chad': (12.11, 15.04),
    'haiti': (18.54, -72.34), 'venezuela': (10.49, -66.88),
    'colombia': (4.71, -74.07), 'mexico': (19.43, -99.13),
    'el salvador': (13.69, -89.22), 'honduras': (14.08, -87.21),
    'guatemala': (14.64, -90.51),
    # ── Major geopolitical actors ──────────────────────────────────────────
    'china': (39.90, 116.40), 'united states': (38.90, -77.04),
    'usa': (38.90, -77.04), 'us ': (38.90, -77.04),
    'russia': (55.75, 37.62), 'india': (28.61, 77.21),
    'turkey': (39.93, 32.86), 'saudi arabia': (24.69, 46.72),
    'egypt': (30.06, 31.25), 'brazil': (-15.78, -47.93),
    'united kingdom': (51.51, -0.13), 'uk ': (51.51, -0.13),
    'france': (48.86, 2.35), 'germany': (52.52, 13.41),
    'japan': (35.68, 139.69), 'south africa': (-25.75, 28.19),
    # ── Middle East & Gulf ─────────────────────────────────────────────────
    'jordan': (31.95, 35.93), 'kuwait': (29.37, 47.98),
    'bahrain': (26.22, 50.59), 'qatar': (25.29, 51.53),
    'uae': (24.47, 54.37), 'united arab emirates': (24.47, 54.37),
    'oman': (23.61, 58.59), 'tunisia': (36.82, 10.17),
    'algeria': (36.74, 3.06), 'morocco': (34.02, -6.85),
    # ── Caucasus & Central Asia ────────────────────────────────────────────
    'azerbaijan': (40.41, 49.87), 'armenia': (40.18, 44.51),
    'georgia': (41.69, 44.83), 'kazakhstan': (51.18, 71.45),
    'uzbekistan': (41.30, 69.28), 'tajikistan': (38.54, 68.77),
    'kyrgyzstan': (42.87, 74.59), 'turkmenistan': (37.95, 58.38),
    # ── South & Southeast Asia ────────────────────────────────────────────
    'bangladesh': (23.72, 90.41), 'sri lanka': (6.93, 79.86),
    'nepal': (27.71, 85.32), 'thailand': (13.75, 100.52),
    'indonesia': (-6.21, 106.85), 'philippines': (14.60, 120.98),
    'malaysia': (3.15, 101.70), 'vietnam': (21.03, 105.85),
    'cambodia': (11.56, 104.92),
    # ── Africa (expanded) ─────────────────────────────────────────────────
    'kenya': (-1.29, 36.82), 'tanzania': (-6.37, 34.89),
    'uganda': (0.32, 32.58), 'rwanda': (-1.95, 30.06),
    'burundi': (-3.39, 29.36), 'zimbabwe': (-17.83, 31.05),
    'zambia': (-13.13, 27.85), 'angola': (-8.84, 13.23),
    'guinea': (9.54, -13.68), 'sierra leone': (8.49, -13.23),
    'liberia': (6.30, -10.80), 'ivory coast': (5.35, -4.01),
    'ghana': (5.60, -0.19), 'senegal': (14.69, -17.44),
    'togo': (6.14, 1.22), 'benin': (6.37, 2.33),
    'mauritania': (18.08, -15.97),
    # ── Europe (conflict-relevant) ────────────────────────────────────────
    'belarus': (53.91, 27.55), 'moldova': (47.00, 28.86),
    'serbia': (44.80, 20.46), 'kosovo': (42.67, 21.17),
    'bosnia': (43.85, 18.36), 'albania': (41.33, 19.83),
    'north macedonia': (41.99, 21.43),
    # ── Americas (conflict-relevant) ──────────────────────────────────────
    'peru': (-12.05, -77.05), 'bolivia': (-16.50, -68.15),
    'ecuador': (-0.23, -78.52), 'argentina': (-34.62, -58.44),
    'chile': (-33.46, -70.65), 'cuba': (23.12, -82.38),
    'nicaragua': (12.13, -86.29), 'costa rica': (9.93, -84.08),
    'dominican republic': (18.47, -69.90),
}

# High-confidence city/location → coords for precise event location
CITY_COORDS = {
    # Ukraine conflict
    'kyiv': (50.45, 30.52), 'mariupol': (47.10, 37.56),
    'kharkiv': (49.99, 36.23), 'bakhmut': (48.60, 37.99),
    'zaporizhzhia': (47.84, 35.12), 'kherson': (46.64, 32.62),
    'odessa': (46.47, 30.73), 'dnipro': (48.46, 35.05),
    'donetsk': (48.02, 37.80), 'luhansk': (48.57, 39.31),
    # Middle East
    'rafah': (31.28, 34.24), 'khan yunis': (31.35, 34.30),
    'ramallah': (31.90, 35.21), 'jenin': (32.47, 35.30),
    'nablus': (32.22, 35.26), 'hebron': (31.53, 35.10),
    'beirut': (33.89, 35.50), 'aleppo': (36.20, 37.16),
    'mosul': (36.34, 43.14), 'fallujah': (33.35, 43.79),
    'erbil': (36.19, 44.01), 'raqqa': (35.95, 39.02),
    'kabul': (34.52, 69.18), 'kandahar': (31.61, 65.71),
    # Africa
    'khartoum': (15.55, 32.53), 'addis ababa': (9.02, 38.75),
    'mogadishu': (2.05, 45.34), 'tripoli': (32.90, 13.18),
    'bamako': (12.65, -8.00), 'niamey': (13.51, 2.11),
    'ouagadougou': (12.37, -1.53), 'bangui': (4.36, 18.56),
    'kinshasa': (-4.32, 15.32), 'goma': (-1.68, 29.22),
    # Asia
    'pyongyang': (39.02, 125.75), 'taipei': (25.03, 121.57),
    'yangon': (16.87, 96.19), 'naypyidaw': (19.75, 96.13),
    'islamabad': (33.72, 73.04), 'karachi': (24.86, 67.01),
    'peshawar': (34.01, 71.57),
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
    """Infer EVENT location from article text using frequency scoring.

    Strategy:
    1. Check city-level coordinates first (most precise).
    2. Score each country by number of mentions (not first-match).
    3. Penalise 'United States'/'US' because it is often the NEWS SOURCE,
       not the event location – keep it only if it scores clearly highest.

    Returns (name, lat, lon) for the most likely event location.
    """
    text_lower = text.lower()

    # 1. City-level match (highest precision)
    city_scores: Dict[str, int] = {}
    for city in CITY_COORDS:
        count = text_lower.count(city)
        if count:
            city_scores[city] = count
    if city_scores:
        best_city = max(city_scores, key=lambda c: city_scores[c])
        lat, lon = CITY_COORDS[best_city]
        return best_city.title(), lat, lon

    # 2. Country-level frequency scoring
    scores: Dict[str, Tuple[int, Tuple[float, float]]] = {}
    for country, coords in COUNTRY_COORDS.items():
        count = text_lower.count(country)
        if count:
            scores[country] = (count, coords)

    if not scores:
        return None, None, None

    # 3. If USA/UK appear but score is not decisively higher than other countries,
    #    prefer the other country (usually the event location).
    western_sources = {'united states', 'usa', 'us ', 'united kingdom', 'uk ', 'france',
                       'germany', 'united nations', 'nato'}
    non_source = {k: v for k, v in scores.items() if k not in western_sources}
    if non_source:
        best = max(non_source, key=lambda c: non_source[c][0])
        lat, lon = non_source[best][1]
        return best.title(), lat, lon

    # Fallback: use the most-mentioned country regardless
    best = max(scores, key=lambda c: scores[c][0])
    lat, lon = scores[best][1]
    return best.title(), lat, lon


def extract_event_location_ai(title: str, content: str) -> Dict:
    """Use Groq to extract WHERE the event happened (not where news comes from).

    Returns dict with keys: country, city, latitude, longitude, confidence (0-1).
    Returns empty dict on failure or if Groq unavailable.
    """
    api_key = os.getenv('GROQ_API_KEY', '')
    if not api_key:
        return {}

    text = f"Title: {title}\n\n{content[:1500]}" if content else f"Title: {title}"

    try:
        import requests
        resp = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'llama-3.1-8b-instant',
                'messages': [
                    {
                        'role': 'system',
                        'content': (
                            'You are a geopolitical expert. Given a news article, identify '
                            'the PRIMARY GEOGRAPHIC LOCATION WHERE THE EVENT TOOK PLACE — '
                            'not where the news agency is from, not where the author is, '
                            'but where the military operation / conflict / disaster / crisis '
                            'is PHYSICALLY happening.\n\n'
                            'Reply with ONLY this JSON (no extra text):\n'
                            '{"country":"<country name>","city":"<city or region, or null>","latitude":<decimal>,"longitude":<decimal>,"confidence":<0.0-1.0>}'
                        ),
                    },
                    {'role': 'user', 'content': text},
                ],
                'max_tokens': 80,
                'temperature': 0.1,
                'response_format': {'type': 'json_object'},
            },
            timeout=10,
        )
        content_str = resp.json()['choices'][0]['message']['content'].strip()
        data = json.loads(content_str)
        # Validate required fields
        if 'country' in data and 'latitude' in data and 'longitude' in data:
            return {
                'country': str(data.get('country', '')),
                'city': str(data.get('city', '')) if data.get('city') else None,
                'latitude': float(data['latitude']),
                'longitude': float(data['longitude']),
                'confidence': float(data.get('confidence', 0.5)),
            }
    except Exception as e:
        logger.debug(f"AI location extraction failed: {e}")
    return {}


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

        # Location inference: for geopolitical articles, try AI first
        country, lat, lon = None, None, None
        ai_location_used = False
        if is_geo and ai_count < 20:
            loc_data = extract_event_location_ai(
                row.get('title', ''), row.get('content', '') or row.get('summary', '')
            )
            if loc_data and loc_data.get('confidence', 0) >= 0.5:
                city_name = loc_data.get('city') or loc_data.get('country', '')
                country = city_name or loc_data.get('country')
                lat = loc_data['latitude']
                lon = loc_data['longitude']
                ai_location_used = True
                ai_count += 1

        # Fallback to improved frequency-based location
        if not country:
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

        # AI summary (rate-limited) — only if Groq wasn't already used for location
        ai_summary = None
        if is_geo and not ai_location_used and ai_count < 20:
            ai_summary = enrich_with_ai(row.get('title', ''), row.get('content', ''))
            if ai_summary:
                ai_count += 1

        # Update article
        coords_src = 'ai_groq' if ai_location_used else ('regex' if country else None)
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
                coordinates_source = COALESCE(coordinates_source, {ph}),
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
                coords_src,
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
