"""
GET /api/hero-article
Returns the single most important geopolitical article (highest risk_score).
"""

from http.server import BaseHTTPRequestHandler
from api._db import neon_get, json_response, error_response, send_response
from api._og_image import enrich_articles_with_images


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            articles = neon_get(
                'unified_articles',
                params={'geopolitical_relevance': 'eq.1'},
                select='id,title,summary,url,source,published_at,'
                       'country,region,risk_level,risk_score,'
                       'conflict_type,conflict_intensity,'
                       'image_url,original_image_url,has_image,'
                       'latitude,longitude,'
                       'ai_sentiment,sentiment_score,language,'
                       'ai_summary,content',
                order='risk_score.desc.nullslast,published_at.desc',
                limit=1,
            )

            if articles:
                # Enrich hero if missing image
                enrich_articles_with_images(articles)
                article = articles[0]
                resp = json_response({
                    'success': True,
                    'article': article,
                })
            else:
                resp = json_response({
                    'success': False,
                    'error': 'No hero article available',
                }, 404)

            send_response(self, resp)

        except Exception as e:
            send_response(self, error_response(str(e)))
