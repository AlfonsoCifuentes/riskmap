"""
Enhanced data quality validator for global news collection.
Validates content quality, language detection, bias indicators, and source credibility.
"""

from utils.config import config, DatabaseManager
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
import sys
import re
from collections import Counter, defaultdict
import hashlib

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))


logger = logging.getLogger(__name__)


class GlobalDataQualityValidator:
    """Enhanced data quality validator for global news collection."""

    def __init__(self):
        self.db = DatabaseManager(config)
        self.quality_thresholds = {
            'min_article_length': 50,
            'max_article_length': 50000,
            'min_title_length': 10,
            'max_title_length': 200,
            'duplicate_similarity_threshold': 0.85,
            'spam_keyword_threshold': 3,
            'min_credible_sources_per_language': 2
        }

        # Spam and low-quality indicators
        self.spam_keywords = [
            'click here', 'buy now', 'free download', 'get rich quick',
            'lose weight fast', 'miracle cure', 'limited time offer',
            'act now', 'call now', 'subscribe now', 'sign up now'
        ]

        # Language detection patterns (basic)
        self.language_patterns = {
            'en': [r'\b(the|and|or|but|in|on|at|to|for|of|with|by)\b'],
            'es': [r'\b(el|la|los|las|y|o|pero|en|con|de|para|por)\b'],
            'fr': [r'\b(le|la|les|et|ou|mais|dans|avec|de|pour|par)\b'],
            'de': [r'\b(der|die|das|und|oder|aber|in|mit|von|für|bei)\b'],
            'ru': [r'[а-яё]+'],
            'zh': [r'[\u4e00-\u9fff]+'],
            'ar': [r'[\u0600-\u06ff]+'],
            'ja': [r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]+']
        }

    def validate_article_batch(
            self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate a batch of articles and return quality metrics."""
        validation_results = {
            'total_articles': len(articles),
            'valid_articles': 0,
            'quality_issues': defaultdict(int),
            'language_distribution': Counter(),
            'source_credibility': defaultdict(list),
            'duplicate_groups': [],
            'overall_quality_score': 0.0,
            'recommendations': []
        }

        if not articles:
            return validation_results

        # Track duplicates
        content_hashes = defaultdict(list)
        title_words = defaultdict(list)

        for i, article in enumerate(articles):
            article_id = article.get('id', i)
            issues = []

            # Basic validation
            title = article.get('title', '').strip()
            content = article.get('content', '').strip()
            source = article.get('source', '').strip()
            language = article.get('language', 'unknown')
            url = article.get('url', '')

            # Length validation
            if len(content) < self.quality_thresholds['min_article_length']:
                issues.append('content_too_short')
            elif len(content) > self.quality_thresholds['max_article_length']:
                issues.append('content_too_long')

            if len(title) < self.quality_thresholds['min_title_length']:
                issues.append('title_too_short')
            elif len(title) > self.quality_thresholds['max_title_length']:
                issues.append('title_too_long')

            # Content quality checks
            if self._detect_spam_content(content, title):
                issues.append('spam_indicators')

            if self._check_content_completeness(content):
                issues.append('incomplete_content')

            # Language validation
            detected_language = self._detect_language(content)
            if detected_language != language and language != 'unknown':
                issues.append('language_mismatch')

            # URL validation
            if not self._validate_url(url):
                issues.append('invalid_url')

            # Source credibility
            credibility = self._assess_source_credibility(source)
            validation_results['source_credibility'][credibility].append(
                source)

            # Track for duplicate detection
            content_hash = hashlib.md5(content.encode()).hexdigest()
            content_hashes[content_hash].append(article_id)

            # Title similarity for duplicate detection
            title_signature = ' '.join(sorted(title.lower().split()[:10]))
            title_words[title_signature].append(article_id)

            # Update counters
            validation_results['language_distribution'][language] += 1
            for issue in issues:
                validation_results['quality_issues'][issue] += 1

            # Count as valid if no critical issues
            critical_issues = [
                'content_too_short',
                'spam_indicators',
                'invalid_url']
            if not any(issue in critical_issues for issue in issues):
                validation_results['valid_articles'] += 1

        # Identify duplicates
        for content_hash, article_ids in content_hashes.items():
            if len(article_ids) > 1:
                validation_results['duplicate_groups'].append({
                    'type': 'content_duplicate',
                    'article_ids': article_ids,
                    'count': len(article_ids)
                })

        for title_sig, article_ids in title_words.items():
            if len(article_ids) > 1:
                validation_results['duplicate_groups'].append({
                    'type': 'title_similar',
                    'article_ids': article_ids,
                    'count': len(article_ids)
                })

        # Calculate overall quality score
        quality_score = self._calculate_quality_score(validation_results)
        validation_results['overall_quality_score'] = quality_score

        # Generate recommendations
        validation_results['recommendations'] = self._generate_quality_recommendations(
            validation_results)

        return validation_results

    def validate_collection_diversity(self, days: int = 7) -> Dict[str, Any]:
        """Validate the diversity and coverage of collected news."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            since_time = (datetime.now() - timedelta(days=days)).isoformat()

            # Language diversity
            cursor.execute('''
                SELECT language, COUNT(*) as count, COUNT(DISTINCT source) as unique_sources
                FROM articles
                WHERE published_at > ?
                GROUP BY language
                ORDER BY count DESC
            ''', (since_time,))

            language_diversity = []
            total_articles = 0
            for row in cursor.fetchall():
                language_diversity.append({
                    'language': row[0],
                    'article_count': row[1],
                    'unique_sources': row[2]
                })
                total_articles += row[1]

            # Source diversity
            cursor.execute('''
                SELECT source, COUNT(*) as count, language
                FROM articles
                WHERE published_at > ?
                GROUP BY source, language
                ORDER BY count DESC
            ''', (since_time,))

            source_diversity = []
            source_counts = defaultdict(int)
            for row in cursor.fetchall():
                source_diversity.append({
                    'source': row[0],
                    'article_count': row[1],
                    'language': row[2]
                })
                source_counts[row[0]] += row[1]

            # Geographic diversity (from processed articles)
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
                LIMIT 30
            ''', (since_time,))

            geographic_coverage = {}
            for row in cursor.fetchall():
                try:
                    countries = json.loads(row[0]) if row[0] else []
                    for country in countries:
                        geographic_coverage[country] = geographic_coverage.get(
                            country, 0) + row[1]
                except (json.JSONDecodeError, TypeError):
                    continue

            # Calculate diversity scores
            language_count = len(language_diversity)
            source_count = len(source_diversity)
            geographic_count = len(geographic_coverage)

            # Gini coefficient for source distribution (concentration measure)
            source_distribution = list(source_counts.values())
            gini_coefficient = self._calculate_gini_coefficient(
                source_distribution)

            # Coverage balance score
            expected_languages = config.get(
                'data_sources.global_coverage.priority_languages', [])
            coverage_balance = min(
                language_count / len(expected_languages),
                1.0) if expected_languages else 1.0

            conn.close()

            return {
                'analysis_period_days': days,
                'total_articles': total_articles,
                'diversity_metrics': {
                    'language_diversity': language_count,
                    'source_diversity': source_count,
                    'geographic_diversity': geographic_count,
                    'source_concentration_gini': round(gini_coefficient, 3),
                    'coverage_balance_score': round(coverage_balance, 3)
                },
                'language_distribution': language_diversity,
                'top_sources': source_diversity[:20],
                'geographic_coverage': dict(sorted(geographic_coverage.items(),
                                                   key=lambda x: x[1], reverse=True)[:20]),
                'quality_assessment': self._assess_diversity_quality(
                    language_count, source_count, geographic_count, gini_coefficient
                )
            }

        except Exception as e:
            logger.error(f"Error validating collection diversity: {e}")
            return {}

    def validate_temporal_consistency(self, days: int = 30) -> Dict[str, Any]:
        """Validate temporal consistency of news collection."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            since_time = (datetime.now() - timedelta(days=days)).isoformat()

            # Daily collection volumes
            cursor.execute('''
                SELECT
                    DATE(published_at) as collection_date,
                    COUNT(*) as article_count,
                    COUNT(DISTINCT source) as unique_sources,
                    COUNT(DISTINCT language) as unique_languages
                FROM articles
                WHERE published_at > ?
                GROUP BY DATE(published_at)
                ORDER BY collection_date DESC
            ''', (since_time,))

            daily_stats = []
            for row in cursor.fetchall():
                daily_stats.append({
                    'date': row[0],
                    'articles': row[1],
                    'sources': row[2],
                    'languages': row[3]
                })

            # Calculate consistency metrics
            article_counts = [stat['articles'] for stat in daily_stats]
            avg_daily_articles = sum(article_counts) / \
                len(article_counts) if article_counts else 0
            consistency_score = self._calculate_consistency_score(
                article_counts)

            # Identify gaps and anomalies
            gaps = []
            anomalies = []

            for i, stat in enumerate(daily_stats):
                if stat['articles'] == 0:
                    gaps.append(stat['date'])
                elif stat['articles'] > avg_daily_articles * 3:  # 3x average
                    anomalies.append({
                        'date': stat['date'],
                        'articles': stat['articles'],
                        'type': 'high_volume'
                    })
                elif stat['articles'] < avg_daily_articles * 0.3:  # 30% of average
                    anomalies.append({
                        'date': stat['date'],
                        'articles': stat['articles'],
                        'type': 'low_volume'
                    })

            conn.close()

            return {
                'analysis_period_days': days,
                'temporal_metrics': {
                    'avg_daily_articles': round(avg_daily_articles, 1),
                    'consistency_score': round(consistency_score, 3),
                    'collection_gaps': len(gaps),
                    'volume_anomalies': len(anomalies)
                },
                'daily_statistics': daily_stats,
                'gaps': gaps,
                'anomalies': anomalies,
                'recommendations': self._generate_temporal_recommendations(
                    consistency_score, gaps, anomalies
                )
            }

        except Exception as e:
            logger.error(f"Error validating temporal consistency: {e}")
            return {}

    def _detect_spam_content(self, content: str, title: str) -> bool:
        """Detect spam indicators in content."""
        text = (content + ' ' + title).lower()
        spam_count = sum(
            1 for keyword in self.spam_keywords if keyword in text)
        return spam_count >= self.quality_thresholds['spam_keyword_threshold']

    def _check_content_completeness(self, content: str) -> bool:
        """Check if content appears incomplete."""
        # Basic completeness checks
        if content.endswith('...') or content.endswith('[...]'):
            return True
        if len(content.split()) < 20:  # Very short content
            return True
        if content.count('.') < 2:  # No sentence structure
            return True
        return False

    def _detect_language(self, text: str) -> str:
        """Basic language detection using patterns."""
        text_sample = text.lower()[:500]  # Use first 500 characters

        language_scores = {}
        for lang, patterns in self.language_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_sample))
                score += matches

            if score > 0:
                language_scores[lang] = score / len(text_sample)

        if language_scores:
            return max(language_scores, key=language_scores.get)
        return 'unknown'

    def _validate_url(self, url: str) -> bool:
        """Basic URL validation."""
        if not url:
            return False

        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            # domain...
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        return bool(url_pattern.match(url))

    def _assess_source_credibility(self, source: str) -> str:
        """Assess source credibility based on known indicators."""
        source_lower = source.lower()

        # High credibility sources
        high_credibility = [
            'reuters',
            'bbc',
            'associated press',
            'ap news',
            'guardian',
            'financial times',
            'new york times',
            'washington post']

        # Medium credibility sources
        medium_credibility = [
            'cnn',
            'fox news',
            'france24',
            'deutsche welle',
            'npr']

        # State-funded sources (medium-low credibility)
        state_funded = ['rt', 'sputnik', 'xinhua', 'tass', 'presstv']

        for source_name in high_credibility:
            if source_name in source_lower:
                return 'high'

        for source_name in medium_credibility:
            if source_name in source_lower:
                return 'medium'

        for source_name in state_funded:
            if source_name in source_lower:
                return 'medium-low'

        return 'unknown'

    def _calculate_quality_score(
            self, validation_results: Dict[str, Any]) -> float:
        """Calculate overall quality score for a batch of articles."""
        total_articles = validation_results['total_articles']
        if total_articles == 0:
            return 0.0

        valid_ratio = validation_results['valid_articles'] / total_articles

        # Penalty for quality issues
        issue_penalties = {
            'spam_indicators': 0.3,
            'content_too_short': 0.2,
            'language_mismatch': 0.1,
            'invalid_url': 0.15,
            'incomplete_content': 0.1
        }

        penalty_score = 0.0
        for issue, count in validation_results['quality_issues'].items():
            penalty = issue_penalties.get(issue, 0.05)
            penalty_score += (count / total_articles) * penalty

        # Penalty for duplicates
        duplicate_penalty = len(
            validation_results['duplicate_groups']) / total_articles * 0.2

        quality_score = max(
            0.0,
            valid_ratio -
            penalty_score -
            duplicate_penalty)
        return min(1.0, quality_score)

    def _calculate_gini_coefficient(self, values: List[int]) -> float:
        """Calculate Gini coefficient for distribution inequality."""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        n = len(sorted_values)
        cumulative_sum = sum(sorted_values)

        if cumulative_sum == 0:
            return 0.0

        gini_sum = sum(
            (2 * i - n - 1) * value for i,
            value in enumerate(
                sorted_values,
                1))
        return gini_sum / (n * cumulative_sum)

    def _calculate_consistency_score(self, values: List[int]) -> float:
        """Calculate consistency score based on variance."""
        if not values or len(values) < 2:
            return 1.0

        mean_val = sum(values) / len(values)
        variance = sum((x - mean_val) ** 2 for x in values) / len(values)
        coefficient_of_variation = (
            variance ** 0.5) / mean_val if mean_val > 0 else float('inf')

        # Convert to score (0-1, where 1 is most consistent)
        consistency_score = 1.0 / (1.0 + coefficient_of_variation)
        return min(1.0, consistency_score)

    def _generate_quality_recommendations(
            self, validation_results: Dict[str, Any]) -> List[str]:
        """Generate quality improvement recommendations."""
        recommendations = []

        total_articles = validation_results['total_articles']
        if total_articles == 0:
            return recommendations

        # Check for high spam rate
        spam_count = validation_results['quality_issues'].get(
            'spam_indicators', 0)
        if spam_count / total_articles > 0.1:
            recommendations.append(
                f"High spam rate detected ({spam_count} articles). Review source quality.")

        # Check for language issues
        lang_mismatch = validation_results['quality_issues'].get(
            'language_mismatch', 0)
        if lang_mismatch / total_articles > 0.05:
            recommendations.append(
                f"Language detection issues ({lang_mismatch} articles). Improve language validation.")

        # Check for duplicate content
        if len(validation_results['duplicate_groups']) > 0:
            recommendations.append(
                f"Found {len(validation_results['duplicate_groups'])} duplicate groups. Improve deduplication.")

        # Check source credibility distribution
        credibility_dist = validation_results['source_credibility']
        high_cred_count = len(credibility_dist.get('high', []))
        total_sources = sum(len(sources)
                            for sources in credibility_dist.values())

        if total_sources > 0 and high_cred_count / total_sources < 0.3:
            recommendations.append(
                "Low proportion of high-credibility sources. Consider adding more reliable sources.")

        return recommendations

    def _assess_diversity_quality(self,
                                  lang_count: int,
                                  source_count: int,
                                  geo_count: int,
                                  gini: float) -> Dict[str,
                                                       str]:
        """Assess the quality of diversity metrics."""
        assessment = {}

        # Language diversity assessment
        if lang_count >= 8:
            assessment['language_diversity'] = 'excellent'
        elif lang_count >= 5:
            assessment['language_diversity'] = 'good'
        elif lang_count >= 3:
            assessment['language_diversity'] = 'fair'
        else:
            assessment['language_diversity'] = 'poor'

        # Source diversity assessment
        if source_count >= 50:
            assessment['source_diversity'] = 'excellent'
        elif source_count >= 25:
            assessment['source_diversity'] = 'good'
        elif source_count >= 10:
            assessment['source_diversity'] = 'fair'
        else:
            assessment['source_diversity'] = 'poor'

        # Geographic coverage assessment
        if geo_count >= 30:
            assessment['geographic_coverage'] = 'excellent'
        elif geo_count >= 15:
            assessment['geographic_coverage'] = 'good'
        elif geo_count >= 8:
            assessment['geographic_coverage'] = 'fair'
        else:
            assessment['geographic_coverage'] = 'poor'

        # Source concentration assessment (lower Gini is better)
        if gini <= 0.3:
            assessment['source_distribution'] = 'well_balanced'
        elif gini <= 0.5:
            assessment['source_distribution'] = 'moderately_balanced'
        elif gini <= 0.7:
            assessment['source_distribution'] = 'somewhat_concentrated'
        else:
            assessment['source_distribution'] = 'highly_concentrated'

        return assessment

    def _generate_temporal_recommendations(
            self,
            consistency_score: float,
            gaps: List[str],
            anomalies: List[Dict]) -> List[str]:
        """Generate temporal consistency recommendations."""
        recommendations = []

        if consistency_score < 0.5:
            recommendations.append(
                "Collection volume is highly inconsistent. Review collection scheduling.")

        if len(gaps) > 0:
            recommendations.append(
                f"Found {len(gaps)} days with no collection. Check system reliability.")

        high_volume_anomalies = [
            a for a in anomalies if a['type'] == 'high_volume']
        if len(high_volume_anomalies) > 3:
            recommendations.append(
                "Multiple high-volume anomalies detected. Check for duplicate collection.")

        low_volume_anomalies = [
            a for a in anomalies if a['type'] == 'low_volume']
        if len(low_volume_anomalies) > 5:
            recommendations.append(
                "Frequent low-volume days detected. Check source availability.")

        return recommendations


# Initialize global validator instance
global_data_validator = GlobalDataQualityValidator()
