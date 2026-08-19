"""
GET /api/status
System health endpoint. Returns the fields the dashboard expects PLUS honest
freshness + deployment provenance (audit addendum B4, spec §1.2 / §92).

Key principle: HTTP 200 != HEALTHY. This endpoint reports how OLD the data is
and derives a freshness level, so stale data can never masquerade as live.
"""

import os
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler

from api._db import (
    error_from_exc,
    json_response,
    neon_sql,
    send_response,
)

# Freshness SLA thresholds (seconds). Spec §1.2.
_HEALTHY = 3 * 3600      # < 3h
_WARNING = 8 * 3600      # 3-8h
_DEGRADED = 24 * 3600    # 8-24h
# > 24h => stale; no data / error => offline


def _freshness(age_seconds):
    if age_seconds is None:
        return "offline"
    if age_seconds < _HEALTHY:
        return "healthy"
    if age_seconds < _WARNING:
        return "warning"
    if age_seconds < _DEGRADED:
        return "degraded"
    return "stale"


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            rows = neon_sql("""
                SELECT
                    COUNT(*)                                            AS total_ingested,
                    COUNT(*) FILTER (WHERE geopolitical_relevance = 1) AS total_articles,
                    -- "Critical" means critical: risk_score >= 70 (risk_level
                    -- 'critical'). Counting 'high' too inflated the headline.
                    COUNT(*) FILTER (WHERE geopolitical_relevance = 1
                        AND (risk_level = 'critical' OR COALESCE(risk_score,0) >= 70)
                    ) AS critical_alerts,
                    COUNT(*) FILTER (WHERE geopolitical_relevance = 1
                        AND (risk_level IN ('high','critical') OR COALESCE(risk_score,0) >= 50)
                    ) AS high_risk_alerts,
                    COUNT(DISTINCT country) FILTER (
                        WHERE country IS NOT NULL AND country <> ''
                    ) AS regions_in_conflict,
                    -- A source is "active" only if it produced data recently,
                    -- not merely because it appears somewhere in history (§197).
                    COUNT(DISTINCT source) FILTER (
                        WHERE source IS NOT NULL AND source <> ''
                          AND published_at >= NOW() - INTERVAL '48 hours'
                    ) AS active_sources,
                    COUNT(DISTINCT source) FILTER (
                        WHERE source IS NOT NULL AND source <> ''
                    ) AS known_sources,
                    -- Pipeline-stage aggregates (honest counts over the dataset,
                    -- not a page-limited slice) for the homepage flow.
                    COUNT(*) FILTER (
                        WHERE geopolitical_relevance = 1
                          AND ai_summary IS NOT NULL AND TRIM(ai_summary) <> ''
                    ) AS ai_summarized,
                    MAX(published_at) AS latest_published_at,
                    MAX(created_at)   AS latest_ingested_at
                FROM unified_articles
            """)
            try:
                ev = neon_sql("SELECT COUNT(*) AS n FROM events")
                events_total = (ev[0].get("n") if ev else 0) or 0
            except Exception:
                events_total = 0
            s = rows[0] if rows else {}

            latest_pub = s.get("latest_published_at")
            latest_ing = s.get("latest_ingested_at")

            # Data age is measured from the most recent thing we ingested.
            reference = latest_ing or latest_pub
            age_seconds = None
            if reference is not None:
                if reference.tzinfo is None:
                    reference = reference.replace(tzinfo=UTC)
                age_seconds = max(
                    0, int((datetime.now(UTC) - reference).total_seconds()))

            level = _freshness(age_seconds)

            resp = json_response({
                "success": True,
                # 'status' reflects freshness, not just "the endpoint replied".
                "status": "ok" if level in ("healthy", "warning") else level,
                "timestamp": datetime.now(UTC).isoformat(),
                "total_articles": s.get("total_articles", 0),
                "total_ingested": s.get("total_ingested", 0),
                "critical_alerts": s.get("critical_alerts", 0),
                "high_risk_alerts": s.get("high_risk_alerts", 0),
                "ai_summarized": s.get("ai_summarized", 0),
                "events_total": events_total,
                "regions_in_conflict": s.get("regions_in_conflict", 0),
                "active_sources": s.get("active_sources", 0),
                "known_sources": s.get("known_sources", 0),
                "freshness": {
                    "level": level,
                    "data_age_seconds": age_seconds,
                    "latest_published_at": latest_pub.isoformat() if latest_pub else None,
                    "latest_ingested_at": latest_ing.isoformat() if latest_ing else None,
                },
                "deployment": {
                    "git_sha": os.getenv("VERCEL_GIT_COMMIT_SHA", "")[:12] or None,
                    "branch": os.getenv("VERCEL_GIT_COMMIT_REF") or None,
                    "environment": os.getenv("VERCEL_ENV") or "development",
                },
            })
            send_response(self, resp)

        except Exception as e:
            send_response(self, error_from_exc(e))
