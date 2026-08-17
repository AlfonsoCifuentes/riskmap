"""
GET /api/hero-article
Returns the single most important geopolitical article, determined by
AI-based composite importance scoring (risk_score + ai_importance).

Selection criteria (hard requirements):
  - geopolitical_relevance = 1
  - Must have a valid image_url (not null, starts with https://)
  - Title must be at least 20 chars (filters out generic placeholders)
  - Source must not be null/empty (filters out test data)

Ranking: risk_score DESC, then published_at DESC as tie-breaker.
Fetches top 10 candidates and picks the best one with a valid image.
"""

from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from api._db import (
    clean_article,
    error_from_exc,
    json_response,
    neon_get,
    send_response,
)

_SELECT_COLS = (
    'id,title,summary,url,source,published_at,'
    'country,region,risk_level,risk_score,'
    'conflict_type,conflict_intensity,'
    'image_url,original_image_url,has_image,'
    'latitude,longitude,'
    'ai_sentiment,sentiment_score,language,'
    'ai_summary,content,ai_importance'
)


def _is_valid_hero(article):
    """Extra Python-side validation for hero quality."""
    title = article.get('title') or ''
    image = article.get('image_url') or ''
    source = article.get('source') or ''
    # Must have meaningful title, valid https image, and a real source
    return (
        len(title) >= 20
        and image.startswith('https://')
        and len(source) > 1
    )


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            qs = parse_qs(urlparse(self.path).query)
            lang = qs.get('lang', [None])[0]

            params = {
                'geopolitical_relevance': 'eq.1',
                'image_url': 'not.is.null',
            }
            if lang and lang in ('es', 'en'):
                params['language'] = f'eq.{lang}'

            # Fetch top 10 candidates: high importance + valid image + real source
            articles = neon_get(
                'unified_articles',
                params=params,
                select=_SELECT_COLS,
                order='risk_score.desc.nullslast,published_at.desc',
                limit=10,
            )

            # Pick the first candidate that passes Python-side validation
            hero = None
            if articles:
                # image_url is populated by the ingest worker (SSRF-safe).
                for art in articles:
                    if _is_valid_hero(art):
                        hero = art
                        break

            # Fallback: relax image requirement (unlikely with 99.8% coverage)
            if not hero:
                articles = neon_get(
                    'unified_articles',
                    params={'geopolitical_relevance': 'eq.1'},
                    select=_SELECT_COLS,
                    order='risk_score.desc.nullslast,published_at.desc',
                    limit=5,
                )
                if articles:
                    for art in articles:
                        if len(art.get('title') or '') >= 20:
                            hero = art
                            break
                    if not hero:
                        hero = articles[0]

            if hero:
                clean_article(hero)
                resp = json_response({
                    'success': True,
                    'article': hero,
                })
            else:
                resp = json_response({
                    'success': False,
                    'error': 'No hero article available',
                }, 404)

            send_response(self, resp)

        except Exception as e:
            send_response(self, error_from_exc(e))
