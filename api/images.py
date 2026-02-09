"""
GET /api/images
Query params: event_id, aoi_id, source_type, limit
Returns metadata only (no binary data). Use /api/image/[id] for actual image.
"""

from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from api._db import neon_get, json_response, error_response, send_response


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            qs = parse_qs(urlparse(self.path).query)
            limit = min(int(qs.get('limit', ['20'])[0]), 100)
            event_id = qs.get('event_id', [None])[0]
            aoi_id = qs.get('aoi_id', [None])[0]
            source_type = qs.get('source_type', [None])[0]

            # PostgREST filter params
            params = {'is_latest': 'eq.1'}
            if event_id:
                params['event_id'] = f'eq.{event_id}'
            if aoi_id:
                params['aoi_id'] = f'eq.{aoi_id}'
            if source_type:
                params['source_type'] = f'eq.{source_type}'

            images = neon_get(
                'images',
                params=params,
                select='id,source_type,source_url,'
                       'latitude,longitude,captured_at,stored_at,'
                       'image_format,image_width,image_height,'
                       'image_size_kb,cloud_cover,resolution_m,'
                       'aoi_id,event_id',
                order='captured_at.desc',
                limit=limit,
            )

            resp = json_response({'images': images, 'count': len(images)})
            send_response(self, resp)

        except Exception as e:
            send_response(self, error_response(str(e)))
