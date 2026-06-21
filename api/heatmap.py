"""
GET /api/heatmap
Returns lat/lon/weight points for the risk heatmap overlay.
"""

from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from api._db import neon_get, json_response, error_response, send_response


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

            event_locs = []
            try:
                event_locs = neon_get(
                    'event_locations',
                    select='latitude,longitude,event_id',
                    limit=200,
                )
            except Exception:
                pass

            signals = []
            try:
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
            except Exception:
                pass

            points = []
            for a in articles:
                points.append({
                    'lat': a['latitude'], 'lon': a['longitude'],
                    'weight': a.get('risk_score', 0.5), 'source': 'article',
                })
            for el in event_locs:
                points.append({
                    'lat': el['latitude'], 'lon': el['longitude'],
                    'weight': 0.7, 'source': 'event',
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
            send_response(self, error_response(str(e)))
