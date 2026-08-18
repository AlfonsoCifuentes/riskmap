"""
GET /api/data-quality
Data Quality Scorecard (spec §15 / §105). Computes completeness, validity,
uniqueness, timeliness, provenance and geo-precision metrics over
unified_articles, in one query. Every number is derived from a reproducible
aggregate — no invented figures.
"""
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler

from api._db import error_from_exc, json_response, neon_sql, send_response


def _pct(numerator, denominator):
    if not denominator:
        return None
    return round(100.0 * (numerator or 0) / denominator, 1)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            rows = neon_sql("""
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE title IS NOT NULL AND title <> '') AS has_title,
                    COUNT(*) FILTER (WHERE published_at IS NOT NULL) AS has_date,
                    COUNT(*) FILTER (WHERE source IS NOT NULL AND source <> '') AS has_source,
                    COUNT(*) FILTER (WHERE latitude IS NOT NULL AND longitude IS NOT NULL) AS has_coords,
                    COUNT(*) FILTER (
                        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
                          AND (latitude BETWEEN -90 AND 90)
                          AND (longitude BETWEEN -180 AND 180)
                    ) AS valid_coords,
                    COUNT(*) FILTER (WHERE url IS NOT NULL AND url <> '') AS has_url,
                    COUNT(DISTINCT url) FILTER (WHERE url IS NOT NULL AND url <> '') AS distinct_urls,
                    COUNT(*) FILTER (WHERE geo_is_fallback = TRUE) AS country_only_geo,
                    COUNT(*) FILTER (WHERE geo_precision IS NOT NULL) AS has_geo_precision,
                    COUNT(*) FILTER (WHERE published_at >= NOW() - INTERVAL '24 hours') AS fresh_24h,
                    COUNT(*) FILTER (WHERE risk_engine_version IS NOT NULL) AS risk_versioned,
                    MAX(published_at) AS latest_published_at
                FROM unified_articles
                WHERE geopolitical_relevance = 1
            """)
            s = rows[0] if rows else {}
            total = s.get("total") or 0
            has_url = s.get("has_url") or 0
            distinct_urls = s.get("distinct_urls") or 0

            dims = {
                "completeness": {
                    "title": _pct(s.get("has_title"), total),
                    "publication_date": _pct(s.get("has_date"), total),
                    "source": _pct(s.get("has_source"), total),
                    "coordinates": _pct(s.get("has_coords"), total),
                },
                "validity": {
                    "valid_coordinates": _pct(s.get("valid_coords"), s.get("has_coords")),
                },
                "uniqueness": {
                    "url_uniqueness": _pct(distinct_urls, has_url),
                    "duplicate_rate": (round(100 - _pct(distinct_urls, has_url), 1)
                                       if has_url else None),
                },
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
            }

            send_response(self, json_response({
                "success": True,
                "total_records": total,
                "dimensions": dims,
                "generated_at": datetime.now(UTC).isoformat(),
            }))
        except Exception as e:
            send_response(self, error_from_exc(e))
