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
    if "forecast" in p:
        return "forecast"
    if "report" in p:
        return "report"
    if "history" in p:
        return "history"
    if "cameras" in p:
        return "cameras"
    if "/image" in p:
        return "image"
    return ""


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            qs = parse_qs(parsed.query)
            route = _route_from(parsed.path, qs)

            # Binary image bytes (served directly, not JSON).
            if route == "image":
                self._serve_image(qs)
                return

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
            elif route == "forecast":
                payload = _forecast(qs)
            elif route == "report":
                payload = _report()
            elif route == "history":
                payload = _history(qs)
            elif route == "cameras":
                from src.core import cameras
                payload = {"data_kind": "EXPERIMENTAL",
                           "note": "Visual Intelligence is experimental; a camera "
                                   "alone never confirms an event.",
                           "allowed_detections": sorted(cameras.ALLOWED_DETECTIONS),
                           "cameras": cameras.load_registry()}
            else:
                send_response(self, json_response(
                    {"error": "unknown route", "hint": "use ?route=..."}, 404))
                return

            send_response(self, json_response(payload))
        except Exception as e:
            send_response(self, error_from_exc(e))

    def _serve_image(self, qs):
        """Serve the stored WebP bytes for an image id, or 404."""
        try:
            img_id = int(qs.get("id", ["0"])[0])
        except (ValueError, TypeError):
            img_id = 0
        if img_id <= 0:
            self.send_response(400)
            self.end_headers()
            return
        try:
            rows = neon_sql(
                "SELECT image_data, image_format FROM images WHERE id = %s LIMIT 1",
                [img_id])
            data = rows[0].get("image_data") if rows else None
            if not data:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"not found")
                return
            blob = bytes(data)  # psycopg2 returns memoryview for bytea
            fmt = (rows[0].get("image_format") or "webp").lower()
            ctype = {"webp": "image/webp", "png": "image/png",
                     "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(fmt, "image/webp")
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "public, max-age=3600, immutable")
            self.send_header("Content-Length", str(len(blob)))
            self.end_headers()
            self.wfile.write(blob)
        except Exception:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"error")


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


def _report():
    """Evidence-driven executive report from reproducible aggregates (spec §20).

    No LLM fabrication: every figure comes from a query, with a data cutoff so
    the report is reproducible. A narrative layer can be added on top later.
    """
    kpis = neon_sql("""
        SELECT
          COUNT(*) FILTER (WHERE geopolitical_relevance = 1) AS total_events_articles,
          COUNT(*) FILTER (WHERE geopolitical_relevance = 1
                             AND published_at >= NOW() - INTERVAL '24 hours') AS new_24h,
          COUNT(*) FILTER (WHERE geopolitical_relevance = 1
                             AND COALESCE(risk_score,0) >= 0.6) AS high_risk
        FROM unified_articles
    """)
    k = kpis[0] if kpis else {}
    top = neon_sql("""
        SELECT e.id, e.title, e.event_type, e.risk_score, e.risk_level,
               e.confidence_score, e.source_count, e.independent_source_count,
               e.last_updated
        FROM events e
        ORDER BY COALESCE(e.risk_score, e.severity*100, 0) DESC NULLS LAST,
                 e.last_updated DESC NULLS LAST
        LIMIT 10
    """)
    cats = neon_sql("""
        SELECT COALESCE(conflict_type,'other') AS category, COUNT(*) AS n
        FROM unified_articles WHERE geopolitical_relevance = 1
        GROUP BY COALESCE(conflict_type,'other') ORDER BY n DESC LIMIT 8
    """)
    return {
        "success": True,
        "generated_at": datetime.now(UTC).isoformat(),
        "data_cutoff": datetime.now(UTC).isoformat(),
        "kpis": k,
        "top_events": [{
            "id": t.get("id"), "title": t.get("title"),
            "category": t.get("event_type"),
            "risk_score": t.get("risk_score"), "risk_level": t.get("risk_level"),
            "confidence": t.get("confidence_score"),
            "source_count": t.get("source_count"),
            "independent_source_count": t.get("independent_source_count"),
            "updated_at": (t["last_updated"].isoformat()
                           if t.get("last_updated") else None),
        } for t in top],
        "category_breakdown": [{"category": c["category"], "count": c["n"]} for c in cats],
        "methodology": ("Figures are reproducible aggregates over unified_articles "
                        "and events at the data cutoff. Risk and confidence are "
                        "reported separately (Risk Engine v2)."),
    }


def _history(qs):
    """Historical coverage analytics over the full dataset (spec §13).

    Reproducible aggregates: daily article volume, category mix, top REAL
    countries (never media outlets), risk-band distribution, and events by type.
    Recent-heavy because raw articles have limited retention — honestly labelled.
    """
    try:
        days = min(int(qs.get("days", ["90"])[0]), 365)
    except (ValueError, TypeError):
        days = 90

    daily = neon_sql(
        """
        SELECT to_char(date_trunc('day', published_at), 'YYYY-MM-DD') AS day,
               COUNT(*) AS n,
               COUNT(*) FILTER (WHERE COALESCE(risk_score,0) >= 50
                                  OR risk_level IN ('high','critical')) AS high
        FROM unified_articles
        WHERE geopolitical_relevance = 1 AND published_at IS NOT NULL
          AND published_at >= NOW() - (%s || ' days')::interval
        GROUP BY 1 ORDER BY 1
        """, [str(days)])

    # Monthly series over the FULL real span (articles + events), so the
    # long-range time-series is never empty even when raw-article retention is
    # short. Honest: this is the real coverage window, not synthetic backfill.
    monthly = neon_sql(
        """
        WITH pts AS (
            SELECT date_trunc('month', published_at) AS m, risk_score AS rs
            FROM unified_articles
            WHERE geopolitical_relevance = 1 AND published_at IS NOT NULL
            UNION ALL
            SELECT date_trunc('month', COALESCE(started_at, last_updated)) AS m,
                   COALESCE(risk_score, severity_normalized, severity*100, 0) AS rs
            FROM events
            WHERE COALESCE(started_at, last_updated) IS NOT NULL
        )
        SELECT to_char(m, 'YYYY-MM') AS month,
               COUNT(*) AS n,
               COUNT(*) FILTER (WHERE COALESCE(rs,0) >= 50) AS high
        FROM pts
        WHERE m >= date_trunc('month', NOW()) - INTERVAL '23 months'
        GROUP BY m ORDER BY m
        """)

    span = neon_sql(
        """
        SELECT to_char(MIN(published_at), 'YYYY-MM-DD') AS first_day,
               to_char(MAX(published_at), 'YYYY-MM-DD') AS last_day
        FROM unified_articles WHERE geopolitical_relevance = 1
        """)

    categories = neon_sql(
        """
        SELECT COALESCE(NULLIF(TRIM(conflict_type),''),'other') AS category,
               COUNT(*) AS n
        FROM unified_articles WHERE geopolitical_relevance = 1
        GROUP BY 1 ORDER BY n DESC LIMIT 10
        """)

    # Top REAL places — same discipline as the zones endpoint (no outlets).
    countries = neon_sql(
        """
        SELECT COALESCE(NULLIF(TRIM(country),''), NULLIF(TRIM(region),'')) AS place,
               COUNT(*) AS n,
               ROUND(AVG(COALESCE(risk_score,0))::numeric, 1) AS avg_risk
        FROM unified_articles
        WHERE geopolitical_relevance = 1
          AND latitude IS NOT NULL AND longitude IS NOT NULL
          AND NOT (ABS(latitude) < 0.5 AND ABS(longitude) < 0.5)
          AND LENGTH(COALESCE(NULLIF(TRIM(country),''),NULLIF(TRIM(region),''))) > 2
        GROUP BY 1 ORDER BY n DESC LIMIT 12
        """)

    risk_bands = neon_sql(
        """
        SELECT
          COUNT(*) FILTER (WHERE COALESCE(risk_score,0) < 30) AS low,
          COUNT(*) FILTER (WHERE COALESCE(risk_score,0) >= 30 AND COALESCE(risk_score,0) < 50) AS medium,
          COUNT(*) FILTER (WHERE COALESCE(risk_score,0) >= 50 AND COALESCE(risk_score,0) < 70) AS high,
          COUNT(*) FILTER (WHERE COALESCE(risk_score,0) >= 70) AS critical
        FROM unified_articles WHERE geopolitical_relevance = 1
        """)

    events_by_type = neon_sql(
        """
        SELECT COALESCE(NULLIF(TRIM(event_type),''),'other') AS type, COUNT(*) AS n
        FROM events GROUP BY 1 ORDER BY n DESC LIMIT 8
        """)

    return {
        "success": True,
        "window_days": days,
        "daily": [{"day": r["day"], "count": r["n"], "high": r["high"]} for r in daily],
        "monthly": [{"month": r["month"], "count": r["n"], "high": r["high"]} for r in monthly],
        "coverage": (span[0] if span else {}),
        "categories": [{"category": r["category"], "count": r["n"]} for r in categories],
        "countries": [{"place": r["place"], "count": r["n"],
                       "avg_risk": float(r["avg_risk"] or 0)} for r in countries],
        "risk_bands": (risk_bands[0] if risk_bands else {}),
        "events_by_type": [{"type": r["type"], "count": r["n"]} for r in events_by_type],
        "generated_at": datetime.now(UTC).isoformat(),
    }


def _forecast(qs):
    """Escalation forecast for a region/category from real recent-event features
    (spec §16). Honest: returns probability WITH its baseline + uncertainty."""
    from src.core import forecasting
    category = qs.get("category", [None])[0]
    if category is not None and not _IDENT.match(category):
        raise BadRequest("invalid category")
    cat_filter = "AND event_type = %s" if category else ""
    params = [category] if category else []
    try:
        rows = neon_sql(f"""
            SELECT
              COUNT(*) FILTER (WHERE last_updated >= NOW() - INTERVAL '7 days') AS last7,
              COUNT(*) FILTER (WHERE last_updated >= NOW() - INTERVAL '14 days'
                                 AND last_updated < NOW() - INTERVAL '7 days') AS prev7,
              AVG(COALESCE(confidence_score, 0)) AS mean_conf,
              AVG(COALESCE(independent_source_count, 1)) AS mean_indep
            FROM events WHERE TRUE {cat_filter}
        """, params)
        s = rows[0] if rows else {}
    except Exception:
        s = {}
    last7 = float(s.get("last7") or 0)
    prev7 = float(s.get("prev7") or 0)
    rate = last7 / 7.0
    slope = 0.0
    if prev7 > 0:
        slope = max(-1.0, min(1.0, (last7 - prev7) / prev7))
    features = {
        "recent_event_rate": rate,
        "risk_slope": slope,
        "source_corroboration": float(s.get("mean_indep") or 1),
        "official_alert": False,
        "horizon_hours": 168,
    }
    result = forecasting.escalation_probability(features)
    result["category"] = category or "all"
    result["window"] = {"last_7d_events": int(last7), "prev_7d_events": int(prev7)}
    return result


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
