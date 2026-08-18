"""
GET /api/heatmap
Returns lat/lon/weight points for the risk heatmap overlay.
"""

from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from api._db import (
    error_from_exc,
    json_response,
    neon_get,
    neon_sql,
    send_response,
)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            qs = parse_qs(urlparse(self.path).query)
            limit = min(int(qs.get('limit', ['500'])[0]), 2000)

            # Articles with risk scores
            articles = neon_get(
                'unified_articles',
                params={
                    'geopolitical_relevance': 'eq.1',
                    'latitude': 'not.is.null',
                    'longitude': 'not.is.null',
                    'risk_score': 'gt.0',
                },
                select='latitude,longitude,risk_score',
                order='published_at.desc',
                limit=limit,
            )

            # Event locations weighted by the event's REAL risk (not a constant).
            event_locs = neon_sql(
                """
                SELECT el.latitude, el.longitude,
                       COALESCE(e.risk_score/100.0, e.severity, 0.5) AS weight
                FROM event_locations el
                JOIN events e ON e.id = el.event_id
                ORDER BY el.id DESC LIMIT 200
                """
            )

            # Signals
            signals = neon_get(
                'signals',
                params={
                    'latitude': 'not.is.null',
                    'longitude': 'not.is.null',
                },
                select='latitude,longitude,severity,signal_type',
                order='created_at.desc',
                limit=200,
            )

            points = []
            for a in articles:
                points.append({
                    'lat': a['latitude'], 'lon': a['longitude'],
                    'weight': a.get('risk_score', 0.5), 'source': 'article',
                })
            for el in event_locs:
                points.append({
                    'lat': el['latitude'], 'lon': el['longitude'],
                    'weight': min(1.0, float(el.get('weight') or 0.5)),
                    'source': 'event',
                })
            for s in signals:
                points.append({
                    'lat': s['latitude'], 'lon': s['longitude'],
                    'weight': s.get('severity', 0.5), 'source': s.get('signal_type', 'signal'),
                })

            resp = json_response({
                'points': points,
                'count': len(points),
            })
            send_response(self, resp)

        except Exception as e:
            send_response(self, error_from_exc(e))
