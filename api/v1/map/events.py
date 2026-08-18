"""
GET /api/v1/map/events
Event-centric GeoJSON for the map (spec §4.10 / §36). Returns a FeatureCollection
of events that have a resolved location, with risk, confidence and uncertainty
so the UI can draw circles sized to geo_precision — never a false-precision pin.

Query params:
    category         filter by event_type (validated)
    min_risk         0..100 (default 0)
    min_confidence   0..100 (default 0)
    hours            only events updated within N hours
    limit            max features (default 500, cap 2000)
"""
import re
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from api._db import BadRequest, error_from_exc, json_response, neon_sql, send_response

_IDENT = re.compile(r"^[a-z_][a-z0-9_]*$")


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            qs = parse_qs(urlparse(self.path).query)
            category = qs.get("category", [None])[0]
            if category is not None and not _IDENT.match(category):
                raise BadRequest("invalid category")
            min_risk = float(qs.get("min_risk", ["0"])[0])
            min_conf = float(qs.get("min_confidence", ["0"])[0])
            hours = qs.get("hours", [None])[0]
            limit = min(int(qs.get("limit", ["500"])[0]), 2000)

            where = [
                "COALESCE(e.risk_score, e.severity_normalized, e.severity*100, 0) >= %s",
                "COALESCE(e.confidence_score, e.event_confidence, 0) >= %s",
            ]
            params = [min_risk, min_conf]
            if category:
                where.append("e.event_type = %s")
                params.append(category)
            if hours:
                where.append("e.last_updated >= NOW() - (%s || ' hours')::interval")
                params.append(str(int(float(hours))))
            params.append(limit)

            sql = f"""
                SELECT e.id, e.event_type, e.subtype, e.title,
                       e.severity, e.risk_score, e.risk_level,
                       e.confidence_score, e.event_confidence,
                       e.geo_precision, e.geo_precision_m, e.geo_is_fallback,
                       e.source_count, e.independent_source_count,
                       e.started_at, e.last_updated,
                       el.latitude, el.longitude, el.name, el.precision_km
                FROM events e
                JOIN LATERAL (
                    SELECT latitude, longitude, name, precision_km
                    FROM event_locations
                    WHERE event_id = e.id
                    ORDER BY id LIMIT 1
                ) el ON TRUE
                WHERE {' AND '.join(where)}
                ORDER BY e.last_updated DESC NULLS LAST
                LIMIT %s
            """
            rows = neon_sql(sql, params)

            features = []
            for r in rows:
                risk = r.get("risk_score")
                if risk is None:
                    sev = r.get("severity_normalized") or (
                        (r.get("severity") or 0) * 100)
                    risk = round(float(sev or 0), 1)
                conf = r.get("confidence_score") or r.get("event_confidence")
                radius_m = r.get("geo_precision_m")
                if radius_m is None and r.get("precision_km"):
                    radius_m = float(r["precision_km"]) * 1000
                features.append({
                    "type": "Feature",
                    "id": f"evt_{r['id']}",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [r["longitude"], r["latitude"]],
                    },
                    "properties": {
                        "name": r.get("name") or r.get("title"),
                        "category": r.get("event_type"),
                        "subtype": r.get("subtype"),
                        "risk_score": risk,
                        "risk_level": r.get("risk_level"),
                        "confidence": conf,
                        "geo_precision": r.get("geo_precision"),
                        "uncertainty_radius_m": radius_m,
                        "geo_is_fallback": r.get("geo_is_fallback"),
                        "source_count": r.get("source_count"),
                        "independent_source_count": r.get("independent_source_count"),
                        "updated_at": (r["last_updated"].isoformat()
                                       if r.get("last_updated") else None),
                    },
                })

            resp = json_response({
                "type": "FeatureCollection",
                "features": features,
                "generated_at": datetime.now(UTC).isoformat(),
                "count": len(features),
            })
            send_response(self, resp)
        except Exception as e:
            send_response(self, error_from_exc(e))
