"""
GET /api/gdelt-events
Returns recent articles/events likely sourced from GDELT for contrast checks.
Query params: limit (default 25)
"""

from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from api._db import (
    error_from_exc,
    json_response,
    neon_sql,
    send_response,
)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            qs = parse_qs(urlparse(self.path).query)
            limit = min(max(int(qs.get("limit", ["25"])[0]), 1), 100)

            rows = neon_sql(
                """
                SELECT
                    id,
                    title,
                    summary,
                    source,
                    published_at AS created_at,
                    url,
                    country,
                    region,
                    risk_level,
                    risk_score,
                    'article' AS record_type
                FROM unified_articles
                WHERE geopolitical_relevance = 1
                  AND (
                    COALESCE(source, '') ILIKE '%%gdelt%%'
                    OR COALESCE(url, '') ILIKE '%%gdelt%%'
                    OR COALESCE(content, '') ILIKE '%%gdelt%%'
                    OR COALESCE(summary, '') ILIKE '%%gdelt%%'
                  )
                ORDER BY published_at DESC
                LIMIT %s
                """,
                [limit],
            )

            # Fallback: if no explicit GDELT tag was stored, return the latest
            # high-relevance events so frontend can still contrast sources.
            if not rows:
                rows = neon_sql(
                    """
                    SELECT
                        e.id,
                        e.title,
                        e.explanation AS summary,
                        'events_table' AS source,
                        e.started_at AS created_at,
                        NULL::text AS url,
                        NULL::text AS country,
                        NULL::text AS region,
                        CASE
                          WHEN e.severity >= 0.75 THEN 'high'
                          WHEN e.severity >= 0.45 THEN 'medium'
                          ELSE 'low'
                        END AS risk_level,
                        ROUND((e.severity * 100)::numeric, 2) AS risk_score,
                        'event' AS record_type
                    FROM events e
                    ORDER BY e.started_at DESC NULLS LAST
                    LIMIT %s
                    """,
                    [limit],
                )

            resp = json_response(
                {
                    "success": True,
                    "count": len(rows),
                    "events": rows,
                }
            )
            send_response(self, resp)
        except Exception as exc:
            send_response(self, error_from_exc(exc))
