"""
GET /api/pipeline-status
Operational counters for end-to-end data pipeline stages.
"""

from http.server import BaseHTTPRequestHandler

from api._db import (
    error_from_exc,
    json_response,
    neon_sql,
    send_response,
)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            rows = neon_sql(
                """
                SELECT
                  COUNT(*) FILTER (WHERE geopolitical_relevance = 1) AS ingest_total,
                  COUNT(*) FILTER (WHERE geopolitical_relevance = 1) AS filtered_total,
                  COUNT(DISTINCT COALESCE(NULLIF(TRIM(url), ''), id::text))
                    FILTER (WHERE geopolitical_relevance = 1) AS curated_total,
                  COUNT(*) FILTER (
                    WHERE geopolitical_relevance = 1
                      AND COALESCE(ai_summary, '') <> ''
                  ) AS rewritten_total,
                  COUNT(*) FILTER (
                    WHERE geopolitical_relevance = 1
                      AND latitude IS NOT NULL
                      AND longitude IS NOT NULL
                  ) AS mapped_total,
                  COUNT(*) FILTER (
                    WHERE geopolitical_relevance = 1
                      AND (
                        COALESCE(source, '') ILIKE '%gdelt%'
                        OR COALESCE(url, '') ILIKE '%gdelt%'
                        OR COALESCE(content, '') ILIKE '%gdelt%'
                        OR COALESCE(summary, '') ILIKE '%gdelt%'
                      )
                  ) AS gdelt_total
                FROM unified_articles
                """
            )
            stage = rows[0] if rows else {}

            rows2 = neon_sql(
                """
                SELECT
                  (SELECT COUNT(*) FROM events) AS events_total,
                  (SELECT COUNT(*) FROM signals) AS signals_total,
                  (SELECT COUNT(*) FROM images) AS images_total,
                  (SELECT COUNT(*) FROM event_locations) AS event_locations_total
                """
            )
            extra = rows2[0] if rows2 else {}

            payload = {
                "success": True,
                "pipeline": {
                    "ingest_total": stage.get("ingest_total", 0),
                    "filtered_total": stage.get("filtered_total", 0),
                    "curated_total": stage.get("curated_total", 0),
                    "rewritten_total": stage.get("rewritten_total", 0),
                    "mapped_total": stage.get("mapped_total", 0),
                    "gdelt_total": stage.get("gdelt_total", 0),
                    "events_total": extra.get("events_total", 0),
                    "signals_total": extra.get("signals_total", 0),
                    "images_total": extra.get("images_total", 0),
                    "event_locations_total": extra.get("event_locations_total", 0),
                },
            }
            send_response(self, json_response(payload))
        except Exception as exc:
            send_response(self, error_from_exc(exc))
