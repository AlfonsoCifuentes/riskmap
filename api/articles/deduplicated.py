"""
GET /api/articles/deduplicated
Returns deduplicated geopolitical articles for the mosaic view.
Query params: hours (default 24), limit (default 20)
Deduplication: selects the latest article per (source, country) combination.
"""

from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from api._db import neon_get, json_response, error_response, send_response, clean_articles, error_from_exc
from api._og_image import enrich_articles_with_images


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            qs = parse_qs(urlparse(self.path).query)
            limit = min(int(qs.get('limit', ['20'])[0]), 50)
            lang = qs.get('lang', [None])[0]
            # hours param accepted but we just fetch recent articles ordered by date
            # True dedup would need DISTINCT ON which PostgREST doesn't support,
            # so we fetch more and deduplicate in Python.

            # Only fetch articles WITH images for the mosaic
            params = {
                'geopolitical_relevance': 'eq.1',
                'image_url': 'not.is.null',
            }
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
                limit=100,  # Fetch more to allow dedup
            )

            # Deduplicate: keep first (most recent) article per title similarity
            seen_titles = set()
            mosaic = []
            for article in articles:
                # Simple dedup key: first 60 chars of title lowercased
                title = (article.get('title') or '').strip().lower()[:60]
                if title and title in seen_titles:
                    continue
                if title:
                    seen_titles.add(title)
                mosaic.append(article)
                if len(mosaic) >= limit:
                    break

            # Enrich articles missing images with og:image from source
            enrich_articles_with_images(mosaic)

            # Strip HTML from text fields
            clean_articles(mosaic)

            resp = json_response({
                'success': True,
                'mosaic': mosaic,
                'articles': mosaic,  # Alias for fallback compatibility
                'count': len(mosaic),
            })
            send_response(self, resp)

        except Exception as e:
            send_response(self, error_from_exc(e))
