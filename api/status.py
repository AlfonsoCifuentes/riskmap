"""
GET /api/status
System status / health endpoint for Vercel deployment.
"""

from http.server import BaseHTTPRequestHandler
from api._db import neon_get, json_response, error_response, send_response, NEON_API_URL
from datetime import datetime


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            stats = {}

            # Article counts
            articles = neon_get(
                'unified_articles',
                select='id',
                limit=1,
            )
            geo_articles = neon_get(
                'unified_articles',
                params={'geopolitical_relevance': 'eq.1'},
                select='id',
                limit=1,
            )
            stats['articles'] = {
                'has_data': len(articles) > 0,
                'has_geopolitical': len(geo_articles) > 0,
            }

            # Events
            events = neon_get('events', select='event_type,id', limit=200)
            event_counts = {}
            for e in events:
                t = e.get('event_type', 'unknown')
                event_counts[t] = event_counts.get(t, 0) + 1
            stats['events'] = event_counts

            # Signals
            signals = neon_get('signals', select='signal_type,id', limit=200)
            sig_counts = {}
            for s in signals:
                t = s.get('signal_type', 'unknown')
                sig_counts[t] = sig_counts.get(t, 0) + 1
            stats['signals'] = sig_counts

            resp = json_response({
                'status': 'ok',
                'backend': 'neon-rest-api',
                'api_url': NEON_API_URL[:50] + '…' if len(NEON_API_URL) > 50 else NEON_API_URL,
                'timestamp': datetime.utcnow().isoformat(),
                'stats': stats,
            })
            send_response(self, resp)

        except Exception as e:
            send_response(self, error_response(str(e)))
