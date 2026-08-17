"""
GET /api/articles
Query params: limit (default 20), offset (default 0), country, risk_level
"""

from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from api._db import (
    clean_articles,
    error_from_exc,
    json_response,
    neon_get,
    send_response,
)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            qs = parse_qs(urlparse(self.path).query)
            limit = min(int(qs.get('limit', ['20'])[0]), 100)
            offset = int(qs.get('offset', ['0'])[0])
            country = qs.get('country', [None])[0]
            risk = qs.get('risk_level', [None])[0]
            lang = qs.get('lang', [None])[0]

            # PostgREST filter params
            params = {'geopolitical_relevance': 'eq.1'}
            if country:
                params['country'] = f'eq.{country}'
            if risk:
                params['risk_level'] = f'eq.{risk}'
            if lang and lang in ('es', 'en'):
                params['language'] = f'eq.{lang}'

            articles = neon_get(
                'unified_articles',
                params=params,
                select='id,title,summary,url,source,published_at,'
                       'country,region,risk_level,risk_score,'
                       'conflict_type,conflict_intensity,'
                       'image_url,original_image_url,has_image,'
                       'latitude,longitude,'
                       'ai_sentiment,sentiment_score,language',
                order='published_at.desc',
                limit=limit,
                offset=offset,
            )

            # NOTE: og:image extraction happens in the ingest worker (SSRF-safe),
            # never in the request path. The API returns the stored image_url only.

            # Strip HTML from text fields
            clean_articles(articles)

            resp = json_response({
                'success': True,
                'articles': articles,
                'count': len(articles),
                'limit': limit,
                'offset': offset,
            })
            send_response(self, resp)

        except Exception as e:
            send_response(self, error_from_exc(e))
