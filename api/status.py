"""
GET /api/status
System status / health endpoint for Vercel deployment.
Returns fields that the dashboard JS expects:
  total_articles, critical_alerts, regions_in_conflict, active_sources
"""

from http.server import BaseHTTPRequestHandler
from api._db import neon_sql, json_response, error_response, send_response, error_from_exc
from datetime import datetime


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            rows = neon_sql("""
                SELECT
                    COUNT(*) FILTER (WHERE geopolitical_relevance = 1) AS total_articles,
                    COUNT(*) FILTER (WHERE risk_level IN ('high','critical')) AS critical_alerts,
                    COUNT(DISTINCT country) FILTER (WHERE country IS NOT NULL AND country != '') AS regions_in_conflict,
                    COUNT(DISTINCT source) FILTER (WHERE source IS NOT NULL AND source != '') AS active_sources
                FROM unified_articles
            """)

            stats = rows[0] if rows else {}

            resp = json_response({
                'success': True,
                'status': 'ok',
                'timestamp': datetime.utcnow().isoformat(),
                'total_articles': stats.get('total_articles', 0),
                'critical_alerts': stats.get('critical_alerts', 0),
                'regions_in_conflict': stats.get('regions_in_conflict', 0),
                'active_sources': stats.get('active_sources', 0),
            })
            send_response(self, resp)

        except Exception as e:
            send_response(self, error_from_exc(e))
