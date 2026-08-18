"""
Consolidated v2 API dispatcher.

Vercel Hobby (the project's €0 plan) caps a deployment at 12 Serverless
Functions. To stay within that budget, several logical endpoints share this one
function and are routed by a `route` query param injected via vercel.json
rewrites (with a path fallback):

    /api/v1/map/events   -> route=map-events   (event GeoJSON + filters)
    /api/replay          -> route=replay        (deterministic Replay Mode)
    /api/data-quality    -> route=data-quality  (quality scorecard)
    /api/pipeline-runs   -> route=pipeline-runs (System Observatory feed)
    /api/pipeline-status -> route=pipeline-status (stage counters)

Each handler returns reproducible aggregates; replay is clearly flagged REPLAY.
"""
import os
import re
import sys
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api._db import (  # noqa: E402
    BadRequest,
    error_from_exc,
    json_response,
    neon_sql,
    send_response,
)

_IDENT = re.compile(r"^[a-z_][a-z0-9_]*$")


def _route_from(path: str, qs: dict) -> str:
    if qs.get("route"):
        return qs["route"][0]
    # Fallback: infer from the original path.
    p = path.lower()
    if "map/events" in p:
        return "map-events"
    if "replay" in p:
        return "replay"
    if "data-quality" in p:
        return "data-quality"
    if "pipeline-runs" in p:
        return "pipeline-runs"
    if "pipeline-status" in p:
        return "pipeline-status"
    if "cv-metrics" in p:
        return "cv-metrics"
    return ""


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            qs = parse_qs(parsed.query)
            route = _route_from(parsed.path, qs)

            if route == "map-events":
                payload = _map_events(qs)
            elif route == "replay":
                payload = _replay(qs)
            elif route == "data-quality":
                payload = _data_quality()
            elif route == "pipeline-runs":
                payload = _pipeline_runs(qs)
            elif route == "pipeline-status":
                payload = _pipeline_status()
            elif route == "cv-metrics":
                from src.core import cv_benchmark
                payload = cv_benchmark.load_registry()
            else:
                send_response(self, json_response(
                    {"error": "unknown route", "hint": "use ?route=..."}, 404))
                return

            send_response(self, json_response(payload))
        except Exception as e:
            send_response(self, error_from_exc(e))


# --------------------------------------------------------------------------
# Route handlers
# --------------------------------------------------------------------------

def _map_events(qs):
    category = qs.get("category", [None])[0]
    if category is not None and not _IDENT.match(category):
        raise BadRequest("invalid category")
    min_risk = float(qs.get("min_risk", ["0"])[0])
    min_conf = float(qs.get("min_confidence", ["0"])[0])
    hours = qs.get("hours", [None])[0]
    limit = min(int(qs.get("limit", ["500"])[0]), 2000)

    where = [
        "COALESCE(e.risk_score, e.severity_normalized, e.severity*100, 0) >= %s",
        "COALESCE(e.confidence_score, 0) >= %s",
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
        SELECT e.id, e.event_type, e.subtype, e.title, e.severity,
               e.risk_score, e.risk_level, e.confidence_score,
               e.severity_normalized, e.geo_precision, e.geo_precision_m,
               e.geo_is_fallback, e.source_count, e.independent_source_count,
               e.started_at, e.last_updated,
               el.latitude, el.longitude, el.name, el.precision_km
        FROM events e
        JOIN LATERAL (
            SELECT latitude, longitude, name, precision_km
            FROM event_locations WHERE event_id = e.id ORDER BY id LIMIT 1
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
            risk = round(float(r.get("severity_normalized")
                               or (r.get("severity") or 0) * 100), 1)
        radius_m = r.get("geo_precision_m")
        if radius_m is None and r.get("precision_km"):
            radius_m = float(r["precision_km"]) * 1000
        features.append({
            "type": "Feature",
            "id": f"evt_{r['id']}",
            "geometry": {"type": "Point",
                         "coordinates": [r["longitude"], r["latitude"]]},
            "properties": {
                "name": r.get("name") or r.get("title"),
                "category": r.get("event_type"),
                "subtype": r.get("subtype"),
                "risk_score": risk,
                "risk_level": r.get("risk_level"),
                "confidence": r.get("confidence_score"),
                "geo_precision": r.get("geo_precision"),
                "uncertainty_radius_m": radius_m,
                "geo_is_fallback": r.get("geo_is_fallback"),
                "source_count": r.get("source_count"),
                "independent_source_count": r.get("independent_source_count"),
                "updated_at": (r["last_updated"].isoformat()
                               if r.get("last_updated") else None),
            },
        })
    return {"type": "FeatureCollection", "features": features,
            "count": len(features),
            "generated_at": datetime.now(UTC).isoformat()}


def _replay(qs):
    from src.core import replay
    scenario = qs.get("scenario", [None])[0]
    if not scenario:
        return {"data_kind": "REPLAY", "scenarios": replay.list_scenarios()}
    try:
        return replay.run(scenario)
    except FileNotFoundError:
        return {"error": "unknown scenario",
                "scenarios": [s["id"] for s in replay.list_scenarios()]}


def _pct(n, d):
    return None if not d else round(100.0 * (n or 0) / d, 1)


def _data_quality():
    rows = neon_sql("""
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE title IS NOT NULL AND title <> '') AS has_title,
            COUNT(*) FILTER (WHERE published_at IS NOT NULL) AS has_date,
            COUNT(*) FILTER (WHERE source IS NOT NULL AND source <> '') AS has_source,
            COUNT(*) FILTER (WHERE latitude IS NOT NULL AND longitude IS NOT NULL) AS has_coords,
            COUNT(*) FILTER (
                WHERE latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180
            ) AS valid_coords,
            COUNT(*) FILTER (WHERE url IS NOT NULL AND url <> '') AS has_url,
            COUNT(DISTINCT url) FILTER (WHERE url IS NOT NULL AND url <> '') AS distinct_urls,
            COUNT(*) FILTER (WHERE geo_is_fallback = TRUE) AS country_only_geo,
            COUNT(*) FILTER (WHERE geo_precision IS NOT NULL) AS has_geo_precision,
            COUNT(*) FILTER (WHERE published_at >= NOW() - INTERVAL '24 hours') AS fresh_24h,
            COUNT(*) FILTER (WHERE risk_engine_version IS NOT NULL) AS risk_versioned,
            MAX(published_at) AS latest_published_at
        FROM unified_articles WHERE geopolitical_relevance = 1
    """)
    s = rows[0] if rows else {}
    total = s.get("total") or 0
    has_url = s.get("has_url") or 0
    distinct_urls = s.get("distinct_urls") or 0
    dup = _pct(distinct_urls, has_url)
    return {
        "success": True, "total_records": total,
        "dimensions": {
            "completeness": {
                "title": _pct(s.get("has_title"), total),
                "publication_date": _pct(s.get("has_date"), total),
                "source": _pct(s.get("has_source"), total),
                "coordinates": _pct(s.get("has_coords"), total),
            },
            "validity": {"valid_coordinates": _pct(s.get("valid_coords"), s.get("has_coords"))},
            "uniqueness": {"url_uniqueness": dup,
                           "duplicate_rate": (round(100 - dup, 1) if dup is not None else None)},
            "timeliness": {
                "fresh_24h": _pct(s.get("fresh_24h"), total),
                "latest_published_at": (s["latest_published_at"].isoformat()
                                        if s.get("latest_published_at") else None),
            },
            "provenance": {
                "known_source": _pct(s.get("has_source"), total),
                "risk_engine_versioned": _pct(s.get("risk_versioned"), total),
            },
            "geo_precision": {
                "country_only_rate": _pct(s.get("country_only_geo"), s.get("has_coords")),
                "precision_recorded": _pct(s.get("has_geo_precision"), s.get("has_coords")),
            },
        },
        "generated_at": datetime.now(UTC).isoformat(),
    }


def _pipeline_runs(qs):
    limit = min(int(qs.get("limit", ["30"])[0]), 200)
    try:
        rows = neon_sql(
            """SELECT id, stage, started_at, finished_at, status, items_in,
                      items_out, errors, cost_estimate_eur, git_sha, notes
               FROM pipeline_runs ORDER BY started_at DESC LIMIT %s""",
            [limit])
    except Exception:
        rows = []
    runs = []
    for r in rows:
        st, fi = r.get("started_at"), r.get("finished_at")
        runs.append({
            "id": r.get("id"), "stage": r.get("stage"), "status": r.get("status"),
            "started_at": st.isoformat() if st else None,
            "finished_at": fi.isoformat() if fi else None,
            "duration_seconds": (round((fi - st).total_seconds(), 1)
                                 if st and fi else None),
            "items_in": r.get("items_in"), "items_out": r.get("items_out"),
            "errors": r.get("errors"), "git_sha": (r.get("git_sha") or "")[:12] or None,
            "notes": r.get("notes"),
        })
    return {"runs": runs, "count": len(runs)}


def _pipeline_status():
    rows = neon_sql("""
        SELECT
          COUNT(*) FILTER (WHERE geopolitical_relevance = 1) AS ingest_total,
          COUNT(*) FILTER (WHERE geopolitical_relevance = 1
                             AND latitude IS NOT NULL AND longitude IS NOT NULL) AS mapped_total,
          COUNT(*) FILTER (WHERE geopolitical_relevance = 1
                             AND COALESCE(ai_summary, '') <> '') AS enriched_total
        FROM unified_articles
    """)
    stage = rows[0] if rows else {}
    extra = neon_sql("""
        SELECT (SELECT COUNT(*) FROM events) AS events_total,
               (SELECT COUNT(*) FROM signals) AS signals_total,
               (SELECT COUNT(*) FROM images) AS images_total
    """)
    ex = extra[0] if extra else {}
    return {"success": True, "pipeline": {**stage, **ex}}
