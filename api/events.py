"""
GET /api/events
Query params: type (conflict|disaster), limit, severity_min
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

            # Fetch ALL locations in ONE query (was N+1: one query per event,
            # which made this endpoint take ~46s for 60 events). Group in Python.
            if events:
                ids = [ev['id'] for ev in events]
                rows = neon_sql(
                    "SELECT event_id, latitude, longitude, name, precision_km "
                    "FROM event_locations WHERE event_id = ANY(%s)",
                    [ids],
                )
                by_event = {}
                for r in rows:
                    by_event.setdefault(r['event_id'], []).append({
                        'latitude': r['latitude'], 'longitude': r['longitude'],
                        'name': r['name'], 'precision_km': r['precision_km'],
                    })
                for ev in events:
                    ev['locations'] = by_event.get(ev['id'], [])

            resp = json_response({'success': True, 'events': events, 'count': len(events)})
            send_response(self, resp)

        except Exception as e:
            send_response(self, error_from_exc(e))
