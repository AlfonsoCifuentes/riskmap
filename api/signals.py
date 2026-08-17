"""
GET /api/signals
Query params: type (conflict_indicator|disaster_signal), limit, event_id
"""

from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from api._db import neon_get, json_response, error_response, send_response, error_from_exc


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            qs = parse_qs(urlparse(self.path).query)
            limit = min(int(qs.get('limit', ['50'])[0]), 200)
            signal_type = qs.get('type', [None])[0]
            event_id = qs.get('event_id', [None])[0]

            # PostgREST filter params
            params = {}
            if signal_type:
                params['signal_type'] = f'eq.{signal_type}'
            if event_id:
                params['event_id'] = f'eq.{event_id}'

            signals = neon_get(
                'signals',
                params=params,
                select='id,signal_type,severity,title,'
                       'description,latitude,longitude,created_at,'
                       'event_id,detection_id,image_id',
                order='created_at.desc',
                limit=limit,
            )

            resp = json_response({'signals': signals, 'count': len(signals)})
            send_response(self, resp)

        except Exception as e:
            send_response(self, error_from_exc(e))
