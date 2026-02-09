"""
GET /api/events
Query params: type (conflict|disaster), limit, severity_min
"""

from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from api._db import neon_get, neon_sql, json_response, error_response, send_response


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            qs = parse_qs(urlparse(self.path).query)
            limit = min(int(qs.get('limit', ['50'])[0]), 200)
            event_type = qs.get('type', [None])[0]
            severity_min = qs.get('severity_min', ['0'])[0]

            # PostgREST filter params
            params = {'severity': f'gte.{severity_min}'}
            if event_type:
                params['event_type'] = f'eq.{event_type}'

            events = neon_get(
                'events',
                params=params,
                select='id,event_type,subtype,title,severity,'
                       'started_at,ended_at,explanation',
                order='last_updated.desc',
                limit=limit,
            )

            # Fetch locations for each event
            if events:
                event_ids = [e['id'] for e in events]
                for ev in events:
                    locs = neon_get(
                        'event_locations',
                        params={'event_id': f'eq.{ev["id"]}'},
                        select='latitude,longitude,name,precision_km',
                    )
                    ev['locations'] = locs

            resp = json_response({'success': True, 'events': events, 'count': len(events)})
            send_response(self, resp)

        except Exception as e:
            send_response(self, error_response(str(e)))
