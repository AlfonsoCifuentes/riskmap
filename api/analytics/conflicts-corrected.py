"""
GET /api/analytics/conflicts-corrected
Vercel serverless function — replicates the analytics endpoint from RISKMAP.py.
Returns conflict zones + statistics from unified_articles in Neon Postgres.
"""

from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from api._db import neon_sql, json_response, error_response, send_response


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            qs = parse_qs(urlparse(self.path).query)
            timeframe = qs.get('timeframe', ['7d'])[0]

            timeframe_days = {
                '24h': 1,
                '7d': 7,
                '30d': 30,
                '90d': 90,
            }.get(timeframe, 7)

            # ------------------------------------------------------------------
            # 1. Conflict zones — aggregate by country from unified_articles
            # ------------------------------------------------------------------
            zones = neon_sql("""
                SELECT
                    COALESCE(country, region, 'Unknown') AS location,
                    AVG(latitude)  AS avg_lat,
                    AVG(longitude) AS avg_lon,
                    COUNT(*)       AS article_count,
                    AVG(CASE
                        WHEN risk_score IS NOT NULL THEN risk_score
                        WHEN risk_level = 'high'   THEN 0.8
                        WHEN risk_level = 'medium'  THEN 0.5
                        WHEN risk_level = 'low'     THEN 0.2
                        ELSE 0.1
                    END)           AS avg_risk_score,
                    string_agg(DISTINCT conflict_type, ',') AS conflict_types
                FROM unified_articles
                WHERE geopolitical_relevance = 1
                  AND country IS NOT NULL
                  AND published_at >= NOW() - make_interval(days => %s)
                GROUP BY COALESCE(country, region, 'Unknown')
                HAVING COUNT(*) >= 1
                ORDER BY avg_risk_score DESC, article_count DESC
                LIMIT 50
            """, [timeframe_days])

            conflict_zones = []
            for row in zones:
                conflict_zones.append({
                    'location': row['location'],
                    'latitude': float(row['avg_lat']) if row.get('avg_lat') else 0.0,
                    'longitude': float(row['avg_lon']) if row.get('avg_lon') else 0.0,
                    'article_count': row['article_count'] or 0,
                    'avg_risk_score': round(float(row['avg_risk_score'] or 0), 3),
                    'risk_level': (
                        'high' if float(row['avg_risk_score'] or 0) >= 0.6
                        else 'medium' if float(row['avg_risk_score'] or 0) >= 0.35
                        else 'low'
                    ),
                    'conflict_types': (row['conflict_types'] or '').split(','),
                    'countries': [row['location']],
                    'category': _infer_category(row.get('conflict_types') or ''),
                })

            # ------------------------------------------------------------------
            # 2. Statistics
            # ------------------------------------------------------------------
            stats_rows = neon_sql("""
                SELECT
                    COUNT(*)                                           AS total_articles,
                    COUNT(DISTINCT source)                             AS total_sources,
                    COUNT(DISTINCT source) FILTER (
                        WHERE created_at >= NOW() - INTERVAL '7 days'
                    )                                                  AS active_sources,
                    COUNT(*) FILTER (WHERE risk_level = 'high')        AS critical_alerts,
                    COUNT(DISTINCT country) FILTER (
                        WHERE country IS NOT NULL AND risk_level = 'high'
                    )                                                  AS high_risk_regions,
                    COUNT(DISTINCT country) FILTER (
                        WHERE country IS NOT NULL AND risk_level = 'medium'
                    )                                                  AS medium_risk_regions,
                    COUNT(*) FILTER (
                        WHERE title IS NOT NULL AND (content IS NOT NULL OR summary IS NOT NULL)
                    )                                                  AS articles_with_data
                FROM unified_articles
                WHERE geopolitical_relevance = 1
            """)
            s = stats_rows[0] if stats_rows else {}

            total = s.get('total_articles') or 0
            with_data = s.get('articles_with_data') or 0
            reliability = int(with_data / total * 100) if total > 0 else 0

            resp = json_response({
                'success': True,
                'conflicts': conflict_zones,
                'statistics': {
                    'total_zones': len(conflict_zones),
                    'total_articles': total,
                    'total_sources': s.get('total_sources') or 0,
                    'active_sources': s.get('active_sources') or 0,
                    'reliability_score': reliability,
                    'critical_alerts': s.get('critical_alerts') or 0,
                    'regions_in_conflict': s.get('high_risk_regions') or 0,
                    'medium_risk_regions': s.get('medium_risk_regions') or 0,
                    'timeframe': timeframe,
                    'timeframe_days': timeframe_days,
                    'data_source': 'neon_postgres',
                },
                'message': f'Conflict zones for {timeframe_days} days',
            })
            send_response(self, resp)

        except Exception as exc:
            send_response(self, error_response(str(exc)))

    def log_message(self, fmt, *args):
        pass  # silence Vercel logs


def _infer_category(conflict_types_str: str) -> str:
    """Map raw conflict_type strings to a dashboard category."""
    ct = conflict_types_str.lower()
    if any(k in ct for k in ('territorial', 'border', 'invasion', 'occupation')):
        return 'Territorial'
    if any(k in ct for k in ('economic', 'trade', 'sanction', 'tariff')):
        return 'Económico'
    if any(k in ct for k in ('politic', 'election', 'government', 'diplomacy', 'coup')):
        return 'Político'
    if any(k in ct for k in ('religio', 'sectarian', 'jihad', 'extremis')):
        return 'Religioso'
    if any(k in ct for k in ('ethnic', 'tribal', 'genocide')):
        return 'Étnico'
    if any(k in ct for k in ('military', 'war', 'armed', 'combat')):
        return 'Militar'
    return 'Otros'
