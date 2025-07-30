"""
Enhanced monitoring module for global news collection system.
Tracks collection performance, source reliability, and coverage metrics.
"""

from utils.config import config, DatabaseManager
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys
import requests
from collections import defaultdict, Counter
import time

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))


logger = logging.getLogger(__name__)


class GlobalCollectionMonitor:
    """Monitor for global news collection performance and coverage."""

    def __init__(self):
        self.db = DatabaseManager(config)
        self.monitoring_enabled = config.get(
            'monitoring.collection_monitoring.enabled', True)

    def track_collection_performance(self,
                                     collection_type: str,
                                     source_info: Dict[str,
                                                       Any],
                                     articles_collected: int,
                                     duration_seconds: float,
                                     errors: List[str] = None) -> None:
        """Track collection performance metrics."""
        if not self.monitoring_enabled:
            return

        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Insert collection performance record
            cursor.execute('''
                INSERT INTO collection_performance
                (timestamp, collection_type, source_name, source_url, language, region,
                 articles_collected, duration_seconds, success_rate, errors)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                collection_type,
                source_info.get('name', 'unknown'),
                source_info.get('url', ''),
                source_info.get('language', 'unknown'),
                source_info.get('region', 'unknown'),
                articles_collected,
                duration_seconds,
                1.0 if articles_collected > 0 and not errors else 0.0,
                json.dumps(errors or [])
            ))

            conn.commit()
            conn.close()

            logger.debug(
                f"Tracked collection performance: {collection_type} - {articles_collected} articles")

        except Exception as e:
            logger.error(f"Error tracking collection performance: {e}")

    def get_collection_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get collection statistics for the specified time period."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            since_time = (datetime.now() - timedelta(hours=hours)).isoformat()

            # Overall statistics
            cursor.execute('''
                SELECT
                    COUNT(*) as total_collections,
                    SUM(articles_collected) as total_articles,
                    AVG(articles_collected) as avg_articles_per_collection,
                    AVG(duration_seconds) as avg_duration,
                    AVG(success_rate) as overall_success_rate
                FROM collection_performance
                WHERE timestamp > ?
            ''', (since_time,))

            overall_stats = cursor.fetchone()

            # Statistics by collection type
            cursor.execute('''
                SELECT
                    collection_type,
                    COUNT(*) as collections,
                    SUM(articles_collected) as articles,
                    AVG(duration_seconds) as avg_duration,
                    AVG(success_rate) as success_rate
                FROM collection_performance
                WHERE timestamp > ?
                GROUP BY collection_type
                ORDER BY articles DESC
            ''', (since_time,))

            type_stats = []
            for row in cursor.fetchall():
                type_stats.append({
                    'type': row[0],
                    'collections': row[1],
                    'articles': row[2],
                    'avg_duration': round(row[3], 2),
                    'success_rate': round(row[4], 3)
                })

            # Statistics by language
            cursor.execute('''
                SELECT
                    language,
                    COUNT(*) as collections,
                    SUM(articles_collected) as articles,
                    AVG(success_rate) as success_rate
                FROM collection_performance
                WHERE timestamp > ?
                GROUP BY language
                ORDER BY articles DESC
            ''', (since_time,))

            language_stats = []
            for row in cursor.fetchall():
                language_stats.append({
                    'language': row[0],
                    'collections': row[1],
                    'articles': row[2],
                    'success_rate': round(row[3], 3)
                })

            # Top performing sources
            cursor.execute('''
                SELECT
                    source_name,
                    COUNT(*) as collections,
                    SUM(articles_collected) as total_articles,
                    AVG(articles_collected) as avg_articles,
                    AVG(success_rate) as success_rate
                FROM collection_performance
                WHERE timestamp > ?
                GROUP BY source_name
                ORDER BY total_articles DESC
                LIMIT 20
            ''', (since_time,))

            top_sources = []
            for row in cursor.fetchall():
                top_sources.append({
                    'source': row[0],
                    'collections': row[1],
                    'total_articles': row[2],
                    'avg_articles': round(row[3], 1),
                    'success_rate': round(row[4], 3)
                })

            conn.close()

            return {
                'time_period_hours': hours,
                'overall': {
                    'total_collections': overall_stats[0] or 0,
                    'total_articles': overall_stats[1] or 0,
                    'avg_articles_per_collection': round(
                        overall_stats[2] or 0,
                        1),
                    'avg_duration_seconds': round(
                        overall_stats[3] or 0,
                        2),
                    'overall_success_rate': round(
                        overall_stats[4] or 0,
                        3)},
                'by_type': type_stats,
                'by_language': language_stats,
                'top_sources': top_sources}

        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}

    def get_source_reliability_report(self, days: int = 7) -> Dict[str, Any]:
        """Generate source reliability report."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            since_time = (datetime.now() - timedelta(days=days)).isoformat()

            # Source reliability metrics
            cursor.execute('''
                SELECT
                    source_name,
                    source_url,
                    language,
                    COUNT(*) as attempts,
                    SUM(articles_collected) as total_articles,
                    AVG(articles_collected) as avg_articles,
                    AVG(success_rate) as success_rate,
                    AVG(duration_seconds) as avg_duration,
                    COUNT(CASE WHEN success_rate = 0 THEN 1 END) as failures
                FROM collection_performance
                WHERE timestamp > ?
                GROUP BY source_name, source_url, language
                ORDER BY success_rate DESC, total_articles DESC
            ''', (since_time,))

            source_reliability = []
            for row in cursor.fetchall():
                failure_rate = row[8] / row[3] if row[3] > 0 else 0
                # Success rate adjusted for failures
                reliability_score = row[6] * (1 - failure_rate)

                source_reliability.append({
                    'source_name': row[0],
                    'source_url': row[1],
                    'language': row[2],
                    'attempts': row[3],
                    'total_articles': row[4],
                    'avg_articles': round(row[5], 1),
                    'success_rate': round(row[6], 3),
                    'avg_duration': round(row[7], 2),
                    'failures': row[8],
                    'failure_rate': round(failure_rate, 3),
                    'reliability_score': round(reliability_score, 3)
                })

            # Categorize sources by reliability
            high_reliability = [
                s for s in source_reliability if s['reliability_score'] >= 0.8]
            medium_reliability = [
                s for s in source_reliability if 0.5 <= s['reliability_score'] < 0.8]
            low_reliability = [
                s for s in source_reliability if s['reliability_score'] < 0.5]

            conn.close()

            return {
                'report_period_days': days,
                'total_sources_tested': len(source_reliability),
                'high_reliability': high_reliability,
                'medium_reliability': medium_reliability,
                'low_reliability': low_reliability,
                'recommendations': self._generate_reliability_recommendations(source_reliability)}

        except Exception as e:
            logger.error(f"Error generating source reliability report: {e}")
            return {}

    def get_coverage_analysis(self, days: int = 7) -> Dict[str, Any]:
        """Analyze geographic and linguistic coverage."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            since_time = (datetime.now() - timedelta(days=days)).isoformat()

            # Language coverage
            cursor.execute('''
                SELECT language, SUM(articles_collected) as articles
                FROM collection_performance
                WHERE timestamp > ?
                GROUP BY language
                ORDER BY articles DESC
            ''', (since_time,))

            language_coverage = {row[0]: row[1] for row in cursor.fetchall()}

            # Regional coverage (from processed articles)
            cursor.execute('''
                SELECT
                    json_extract(p.entities, '$.GPE') as countries,
                    COUNT(*) as mentions
                FROM processed_data p
                JOIN articles a ON p.article_id = a.id
                WHERE a.published_at > ?
                    AND json_extract(p.entities, '$.GPE') IS NOT NULL
                GROUP BY countries
                ORDER BY mentions DESC
                LIMIT 50
            ''', (since_time,))

            regional_coverage = {}
            for row in cursor.fetchall():
                try:
                    countries = json.loads(row[0]) if row[0] else []
                    for country in countries:
                        regional_coverage[country] = regional_coverage.get(
                            country, 0) + row[1]
                except (json.JSONDecodeError, TypeError):
                    continue

            # Coverage gaps analysis
            expected_languages = config.get(
                'data_sources.global_coverage.priority_languages', [])
            missing_languages = [
                lang for lang in expected_languages if lang not in language_coverage]

            # Calculate coverage scores
            total_articles = sum(language_coverage.values())
            language_diversity = len(language_coverage)
            regional_diversity = len(regional_coverage)

            coverage_score = min(
                language_diversity /
                len(expected_languages) if expected_languages else 1.0,
                1.0)

            conn.close()

            return {
                'analysis_period_days': days,
                'total_articles_analyzed': total_articles,
                'language_coverage': language_coverage,
                'regional_coverage': dict(
                    sorted(
                        regional_coverage.items(),
                        key=lambda x: x[1],
                        reverse=True)[
                        :20]),
                'coverage_metrics': {
                    'language_diversity': language_diversity,
                    'regional_diversity': regional_diversity,
                    'coverage_score': round(
                        coverage_score,
                        3),
                    'missing_languages': missing_languages}}

        except Exception as e:
            logger.error(f"Error generating coverage analysis: {e}")
            return {}

    def _generate_reliability_recommendations(
            self, source_reliability: List[Dict]) -> List[str]:
        """Generate recommendations based on source reliability analysis."""
        recommendations = []

        # Check for sources with high failure rates
        high_failure_sources = [
            s for s in source_reliability if s['failure_rate'] > 0.3]
        if high_failure_sources:
            recommendations.append(
                f"Consider removing or fixing {len(high_failure_sources)} sources with >30% failure rate"
            )

        # Check for sources with low article counts
        low_yield_sources = [
            s for s in source_reliability if s['avg_articles'] < 1.0 and s['attempts'] > 5]
        if low_yield_sources:
            recommendations.append(
                f"Review {len(low_yield_sources)} sources with consistently low article yields"
            )

        # Check for sources with very slow response times
        slow_sources = [
            s for s in source_reliability if s['avg_duration'] > 30.0]
        if slow_sources:
            recommendations.append(
                f"Optimize or replace {len(slow_sources)} sources with >30s average response time"
            )

        # Recommend adding more sources for underrepresented languages
        language_counts = Counter(s['language'] for s in source_reliability)
        underrepresented = [
            lang for lang,
            count in language_counts.items() if count < 3]
        if underrepresented:
            recommendations.append(
                f"Consider adding more sources for underrepresented languages: {', '.join(underrepresented)}"
            )

        return recommendations

    def create_monitoring_tables(self):
        """Create database tables for collection monitoring."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS collection_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    collection_type TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    source_url TEXT,
                    language TEXT,
                    region TEXT,
                    articles_collected INTEGER DEFAULT 0,
                    duration_seconds REAL DEFAULT 0.0,
                    success_rate REAL DEFAULT 0.0,
                    errors TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create indexes for better query performance
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_collection_timestamp ON collection_performance(timestamp)')
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_collection_type ON collection_performance(collection_type)')
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_collection_source ON collection_performance(source_name)')
            cursor.execute(
                'CREATE INDEX IF NOT EXISTS idx_collection_language ON collection_performance(language)')

            conn.commit()
            conn.close()

            logger.info("Collection monitoring tables created/verified")

        except Exception as e:
            logger.error(f"Error creating monitoring tables: {e}")


class SourceHealthChecker:
    """Health checker for news sources."""

    def __init__(self):
        self.timeout = 30
        self.user_agent = "Mozilla/5.0 (compatible; GeopoliticalIntelligenceBot/1.0)"

    def check_source_health(
            self, source_info: Dict[str, Any]) -> Dict[str, Any]:
        """Check the health of a news source."""
        health_report = {
            'source_name': source_info.get('name', 'unknown'),
            'url': source_info.get('rss', ''),
            'status': 'unknown',
            'response_time': None,
            'accessible': False,
            'valid_rss': False,
            'recent_content': False,
            'error_message': None
        }

        try:
            start_time = time.time()

            # Check URL accessibility
            headers = {'User-Agent': self.user_agent}
            response = requests.get(source_info.get('rss', ''),
                                    headers=headers, timeout=self.timeout)

            health_report['response_time'] = round(time.time() - start_time, 2)
            health_report['accessible'] = response.status_code == 200

            if response.status_code == 200:
                # Basic RSS validation
                content = response.text.lower()
                health_report['valid_rss'] = '<rss' in content or '<feed' in content

                # Check for recent content (basic check)
                current_year = str(datetime.now().year)
                health_report['recent_content'] = current_year in response.text

                if health_report['valid_rss'] and health_report['recent_content']:
                    health_report['status'] = 'healthy'
                elif health_report['valid_rss']:
                    health_report['status'] = 'degraded'
                else:
                    health_report['status'] = 'unhealthy'
            else:
                health_report['status'] = 'unhealthy'
                health_report['error_message'] = f"HTTP {response.status_code}"

        except requests.RequestException as e:
            health_report['status'] = 'unhealthy'
            health_report['error_message'] = str(e)
        except Exception as e:
            health_report['status'] = 'error'
            health_report['error_message'] = str(e)

        return health_report

    def batch_health_check(
            self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Perform health checks on multiple sources."""
        results = []

        for source in sources:
            try:
                health_report = self.check_source_health(source)
                results.append(health_report)

                # Add small delay to avoid overwhelming servers
                time.sleep(0.5)

            except Exception as e:
                logger.error(
                    f"Error checking source {source.get('name', 'unknown')}: {e}")
                results.append({
                    'source_name': source.get('name', 'unknown'),
                    'url': source.get('rss', ''),
                    'status': 'error',
                    'error_message': str(e)
                })

        return results


# Initialize global monitor instance
collection_monitor = GlobalCollectionMonitor()
source_health_checker = SourceHealthChecker()
