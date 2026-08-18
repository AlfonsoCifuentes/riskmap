"""
GET /api/images
Query params: event_id, aoi_id, source_type, limit
Returns image metadata (no binary). Use /api/image/[id] for the actual image.

source_type supports FAMILIES so the frontend can ask for a category without
knowing every sensor name:
  satellite -> sentinel2, sentinel1, gibs_modis, gibs_viirs
  camera    -> camera, webcam, cctv
Anything else is matched exactly.
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from api._db import error_from_exc, json_response, neon_sql, send_response

_FAMILIES = {
    'satellite': ('sentinel2', 'sentinel1', 'gibs_modis', 'gibs_viirs'),
    'camera': ('camera', 'webcam', 'cctv'),
    'video': ('camera', 'webcam', 'cctv'),
}

_COLS = ("id, source_type, source_url, latitude, longitude, captured_at, "
         "stored_at, image_format, image_width, image_height, image_size_kb, "
         "cloud_cover, resolution_m, aoi_id, event_id")


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            qs = parse_qs(urlparse(self.path).query)
            limit = min(int(qs.get('limit', ['20'])[0]), 200)
            event_id = qs.get('event_id', [None])[0]
            aoi_id = qs.get('aoi_id', [None])[0]
            source_type = qs.get('source_type', [None])[0]

            where = ["is_latest = 1"]
            params = []
            if event_id:
                where.append("event_id = %s")
                params.append(event_id)
            if aoi_id:
                where.append("aoi_id = %s")
                params.append(aoi_id)
            if source_type:
                fam = _FAMILIES.get(source_type.lower())
                if fam:
                    where.append("source_type IN (%s)" % ','.join(['%s'] * len(fam)))
                    params.extend(fam)
                else:
                    where.append("source_type = %s")
                    params.append(source_type)
            params.append(limit)

            sql = (f"SELECT {_COLS} FROM images WHERE {' AND '.join(where)} "
                   f"ORDER BY captured_at DESC NULLS LAST LIMIT %s")
            images = neon_sql(sql, params)
            send_response(self, json_response({'images': images, 'count': len(images)}))
        except Exception as e:
            send_response(self, error_from_exc(e))
