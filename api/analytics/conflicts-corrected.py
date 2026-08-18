"""
GET /api/analytics/conflicts-corrected
Vercel serverless function — analytics endpoint for the dashboard.
Returns conflict zones + comprehensive statistics from unified_articles.
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
            timeframe = qs.get('timeframe', ['all'])[0]

            # ------------------------------------------------------------------
            # 1. Conflict zones — group by country/region from ALL geo articles
            #    Use risk_score thresholds (not risk_level strings which are mostly null)
            # ------------------------------------------------------------------
            # Zones are REAL PLACES the news is about — derived from the
            # geolocated coordinates, never the media outlet. Articles without
            # real coordinates (or that only carry a 2-letter source/country
            # code with no location) are excluded so outlets like
            # "www.theguardian.com" never appear as a "zone".
            zones = neon_sql("""
                SELECT
                    COALESCE(NULLIF(TRIM(country), ''),
                             NULLIF(TRIM(region), '')) AS location,
                    AVG(latitude)                         AS avg_lat,
                    AVG(longitude)                        AS avg_lon,
                    COUNT(*)                              AS article_count,
                    AVG(COALESCE(risk_score, 20))          AS avg_risk_score,
                    MAX(COALESCE(risk_score, 0))           AS max_risk_score,
                    string_agg(DISTINCT conflict_type, ',' ORDER BY conflict_type)
                        FILTER (WHERE conflict_type IS NOT NULL) AS conflict_types,
                    string_agg(DISTINCT source, ',' ORDER BY source)  AS sources
                FROM unified_articles
                WHERE geopolitical_relevance = 1
                  AND latitude IS NOT NULL AND longitude IS NOT NULL
                  AND latitude BETWEEN -89.9 AND 89.9
                  AND longitude BETWEEN -179.9 AND 179.9
                  AND NOT (ABS(latitude) < 0.5 AND ABS(longitude) < 0.5)
                  AND COALESCE(NULLIF(TRIM(country), ''),
                               NULLIF(TRIM(region), '')) IS NOT NULL
                  AND LENGTH(COALESCE(NULLIF(TRIM(country), ''),
                               NULLIF(TRIM(region), ''))) > 2
                GROUP BY COALESCE(NULLIF(TRIM(country), ''),
                                  NULLIF(TRIM(region), ''))
                HAVING COUNT(*) >= 1
                ORDER BY AVG(COALESCE(risk_score, 20)) DESC, COUNT(*) DESC
                LIMIT 60
            """)

            conflict_zones = []
            for row in zones:
                score = float(row['avg_risk_score'] or 0)
                risk_level = (
                    'high' if score >= 40
                    else 'medium' if score >= 25
                    else 'low'
                )
                conflict_zones.append({
                    'location': row['location'],
                    'latitude': float(row['avg_lat']) if row.get('avg_lat') else 0.0,
                    'longitude': float(row['avg_lon']) if row.get('avg_lon') else 0.0,
                    'article_count': row['article_count'] or 0,
                    'avg_risk_score': round(score, 2),
                    'max_risk_score': round(float(row['max_risk_score'] or 0), 2),
                    'risk_level': risk_level,
                    'conflict_types': (row['conflict_types'] or '').split(',') if row.get('conflict_types') else [],
                    'countries': [row['location']],
                    'category': _infer_category(row.get('conflict_types') or ''),
                })

            # ------------------------------------------------------------------
            # 2. Comprehensive statistics using risk_score thresholds
            # ------------------------------------------------------------------
            stats_rows = neon_sql("""
                SELECT
                    COUNT(*)                                           AS total_articles,
                    COUNT(DISTINCT source)                             AS total_sources,
                    COUNT(DISTINCT source) FILTER (
                        WHERE published_at >= NOW() - INTERVAL '90 days'
                    )                                                  AS active_sources,
                    COUNT(*) FILTER (WHERE COALESCE(risk_score, 0) >= 40)
                                                                       AS critical_alerts,
                    COUNT(DISTINCT COALESCE(country, region)) FILTER (
                        WHERE COALESCE(country, region) IS NOT NULL
                          AND COALESCE(risk_score, 0) >= 40
                    )                                                  AS high_risk_regions,
                    COUNT(DISTINCT COALESCE(country, region)) FILTER (
                        WHERE COALESCE(country, region) IS NOT NULL
                          AND COALESCE(risk_score, 0) >= 25
                          AND COALESCE(risk_score, 0) < 40
                    )                                                  AS medium_risk_regions,
                    COUNT(*) FILTER (
                        WHERE title IS NOT NULL
                          AND (content IS NOT NULL OR summary IS NOT NULL)
                    )                                                  AS articles_with_data,
                    AVG(COALESCE(risk_score, 0))                       AS avg_risk_score,
                    COUNT(*) FILTER (WHERE COALESCE(risk_score, 0) >= 40)  AS count_high,
                    COUNT(*) FILTER (WHERE COALESCE(risk_score, 0) >= 25
                                      AND COALESCE(risk_score, 0) < 40)   AS count_medium,
                    COUNT(*) FILTER (WHERE COALESCE(risk_score, 0) < 25)   AS count_low
                FROM unified_articles
                WHERE geopolitical_relevance = 1
            """)
            s = stats_rows[0] if stats_rows else {}

            total = s.get('total_articles') or 0
            with_data = s.get('articles_with_data') or 0
            total_sources = s.get('total_sources') or 0
            active_sources = s.get('active_sources') or 0
            if active_sources == 0 and total_sources > 0:
                active_sources = total_sources
            reliability = int(with_data / total * 100) if total > 0 else 0

            # ------------------------------------------------------------------
            # 3. Category breakdown for the bar chart
            # ------------------------------------------------------------------
            cat_rows = neon_sql("""
                SELECT
                    COALESCE(conflict_type, 'Otros') AS category,
                    COUNT(*) AS count
                FROM unified_articles
                WHERE geopolitical_relevance = 1
                GROUP BY COALESCE(conflict_type, 'Otros')
                ORDER BY count DESC
                LIMIT 10
            """)
            categories = [{'name': _friendly_category(r['category']),
                           'count': r['count']} for r in cat_rows]

            # ------------------------------------------------------------------
            # 4. Top sources breakdown for the pie chart
            # ------------------------------------------------------------------
            src_rows = neon_sql("""
                SELECT source, COUNT(*) AS count
                FROM unified_articles
                WHERE geopolitical_relevance = 1 AND source IS NOT NULL
                GROUP BY source
                ORDER BY count DESC
                LIMIT 8
            """)
            top_sources = [{'name': _short_source(r['source']),
                            'count': r['count']} for r in src_rows]

            resp = json_response({
                'success': True,
                'conflicts': conflict_zones,
                'statistics': {
                    'total_zones': len(conflict_zones),
                    'total_articles': total,
                    'total_sources': total_sources,
                    'active_sources': active_sources,
                    'reliability_score': reliability,
                    'critical_alerts': s.get('critical_alerts') or 0,
                    'regions_in_conflict': s.get('high_risk_regions') or 0,
                    'medium_risk_regions': s.get('medium_risk_regions') or 0,
                    'avg_risk_score': round(float(s.get('avg_risk_score') or 0), 1),
                    'risk_distribution': {
                        'high': s.get('count_high') or 0,
                        'medium': s.get('count_medium') or 0,
                        'low': s.get('count_low') or 0,
                    },
                    'timeframe': timeframe,
                    'data_source': 'neon_postgres',
                },
                'categories': categories,
                'top_sources': top_sources,
                'message': f'Analytics from {total} geopolitical articles',
            })
            send_response(self, resp)

        except Exception as exc:
            send_response(self, error_from_exc(exc))

    def log_message(self, fmt, *args):
        pass


def _infer_category(conflict_types_str: str) -> str:
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


def _friendly_category(raw: str) -> str:
    if not raw or raw == 'Otros':
        return 'Otros'
    mapping = {
        'territorial': 'Territorial',
        'economic': 'Económico',
        'political': 'Político',
        'religious': 'Religioso',
        'ethnic': 'Étnico',
        'military': 'Militar',
        'conflict': 'Conflicto',
        'diplomacy': 'Diplomático',
        'humanitarian': 'Humanitario',
    }
    lower = raw.lower().strip()
    for key, label in mapping.items():
        if key in lower:
            return label
    return raw.title()


def _short_source(source: str) -> str:
    if not source:
        return 'Unknown'
    s = source.replace('www.', '').replace('feeds.', '')
    s = s.split('/')[0]
    for ext in ('.com', '.org', '.net', '.co.uk', '.uk'):
        s = s.replace(ext, '')
    return s.title() if len(s) < 20 else s[:18] + '…'
