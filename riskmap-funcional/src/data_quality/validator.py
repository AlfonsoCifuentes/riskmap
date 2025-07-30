"""
Data validation and quality assurance module for the OSINT system.
Ensures data integrity, validates sources, and maintains quality standards.
"""

import re
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json
from urllib.parse import urlparse
import unicodedata

from utils.config import config, logger


class DataValidator:
    """Comprehensive data validation and quality assurance."""

    def __init__(self):
        self.db_path = config.database.path
        self.min_article_length = 100
        self.max_article_length = 50000
        self.trusted_domains = {
            'bbc.com', 'reuters.com', 'cnn.com', 'ap.org', 'dw.com',
            'aljazeera.com', 'elpais.com', 'lemonde.fr', 'spiegel.de',
            'guardian.com', 'washingtonpost.com', 'nytimes.com',
            'ft.com', 'economist.com', 'bloomberg.com'
        }
        self.suspicious_patterns = [
            r'click here', r'amazing deal', r'you won\'t believe',
            r'doctors hate', r'this weird trick', r'shocking truth'
        ]

    def validate_article(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive article validation."""
        validation_result = {
            'is_valid': True,
            'quality_score': 100,
            'issues': [],
            'warnings': [],
            'metadata': {}
        }

        try:
            # Basic field validation
            validation_result = self._validate_required_fields(
                article_data, validation_result)

            # Content quality checks
            validation_result = self._validate_content_quality(
                article_data, validation_result)

            # Source credibility check
            validation_result = self._validate_source_credibility(
                article_data, validation_result)

            # Language and encoding validation
            validation_result = self._validate_language_encoding(
                article_data, validation_result)

            # Duplicate detection
            validation_result = self._check_for_duplicates(
                article_data, validation_result)

            # Spam and low-quality content detection
            validation_result = self._detect_spam_content(
                article_data, validation_result)

            # Calculate final quality score
            validation_result['quality_score'] = max(
                0, validation_result['quality_score'])
            validation_result['is_valid'] = validation_result['quality_score'] >= 60

            # Add validation timestamp
            validation_result['validated_at'] = datetime.now().isoformat()

        except Exception as e:
            logger.error(f"Error during article validation: {e}")
            validation_result.update({
                'is_valid': False,
                'quality_score': 0,
                'issues': [f"Validation error: {str(e)}"]
            })

        return validation_result

    def _validate_required_fields(
            self, article: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate required fields are present and non-empty."""
        required_fields = ['title', 'content', 'url', 'published_at', 'source']

        for field in required_fields:
            if field not in article or not article[field]:
                result['issues'].append(
                    f"Missing or empty required field: {field}")
                result['quality_score'] -= 20

        # Validate URL format
        if 'url' in article and article['url']:
            try:
                parsed = urlparse(article['url'])
                if not parsed.scheme or not parsed.netloc:
                    result['issues'].append("Invalid URL format")
                    result['quality_score'] -= 10
            except Exception:
                result['issues'].append("Malformed URL")
                result['quality_score'] -= 10

        # Validate date format
        if 'published_at' in article and article['published_at']:
            try:
                if isinstance(article['published_at'], str):
                    datetime.fromisoformat(
                        article['published_at'].replace(
                            'Z', '+00:00'))
            except Exception:
                result['warnings'].append("Invalid date format")
                result['quality_score'] -= 5

        return result

    def _validate_content_quality(
            self, article: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate content length and quality indicators."""
        content = article.get('content', '')
        title = article.get('title', '')

        # Content length validation
        if len(content) < self.min_article_length:
            result['issues'].append(
                f"Content too short: {len(content)} characters")
            result['quality_score'] -= 15
        elif len(content) > self.max_article_length:
            result['warnings'].append(
                f"Very long content: {len(content)} characters")
            result['quality_score'] -= 5

        # Title length validation
        if len(title) < 10:
            result['issues'].append("Title too short")
            result['quality_score'] -= 10
        elif len(title) > 200:
            result['warnings'].append("Very long title")
            result['quality_score'] -= 5

        # Content-to-title ratio
        if content and title:
            ratio = len(content) / len(title)
            if ratio < 5:
                result['warnings'].append("Low content-to-title ratio")
                result['quality_score'] -= 5

        # Check for proper sentence structure
        if content:
            sentences = content.split('.')
            avg_sentence_length = sum(
                len(s.split()) for s in sentences) / len(sentences) if sentences else 0

            if avg_sentence_length < 5:
                result['warnings'].append("Very short sentences detected")
                result['quality_score'] -= 5
            elif avg_sentence_length > 50:
                result['warnings'].append("Very long sentences detected")
                result['quality_score'] -= 3

        # Store content metrics
        result['metadata'].update({
            'content_length': len(content),
            'title_length': len(title),
            'word_count': len(content.split()) if content else 0,
            'sentence_count': len(content.split('.')) if content else 0
        })

        return result

    def _validate_source_credibility(
            self, article: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate source credibility and trustworthiness."""
        url = article.get('url', '')
        source = article.get('source', {})

        if url:
            try:
                domain = urlparse(url).netloc.lower()
                # Remove 'www.' prefix for comparison
                domain = domain.replace('www.', '')

                # Check against trusted domains
                is_trusted = any(
                    trusted in domain for trusted in self.trusted_domains)

                if is_trusted:
                    result['quality_score'] += 10
                    result['metadata']['source_trusted'] = True
                else:
                    result['metadata']['source_trusted'] = False

                # Check for suspicious TLDs
                suspicious_tlds = ['.tk', '.ml', '.ga', '.cf']
                if any(domain.endswith(tld) for tld in suspicious_tlds):
                    result['warnings'].append("Suspicious domain extension")
                    result['quality_score'] -= 10

                result['metadata']['domain'] = domain

            except Exception:
                result['warnings'].append("Could not parse source domain")

        # Validate source information
        if isinstance(source, dict):
            if not source.get('name'):
                result['warnings'].append("Missing source name")
                result['quality_score'] -= 5

        return result

    def _validate_language_encoding(
            self, article: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate text encoding and language consistency."""
        content = article.get('content', '')
        title = article.get('title', '')

        # Check for encoding issues
        for text_field, field_name in [(content, 'content'), (title, 'title')]:
            if text_field:
                try:
                    # Check for mojibake (encoding issues)
                    normalized = unicodedata.normalize('NFKD', text_field)
                    if len(normalized) != len(text_field):
                        result['warnings'].append(
                            f"Potential encoding issues in {field_name}")
                        result['quality_score'] -= 3

                    # Check for excessive special characters
                    special_char_ratio = sum(
                        1 for c in text_field if not c.isalnum() and not c.isspace()) / len(text_field)
                    if special_char_ratio > 0.1:
                        result['warnings'].append(
                            f"High special character ratio in {field_name}")
                        result['quality_score'] -= 5

                except Exception:
                    result['warnings'].append(
                        f"Text encoding validation failed for {field_name}")

        return result

    def _check_for_duplicates(
            self, article: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Check for duplicate articles in the database."""
        try:
            content = article.get('content', '')
            title = article.get('title', '')
            url = article.get('url', '')

            if not content or not title:
                return result

            # Create content hash for duplicate detection
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            title_hash = hashlib.md5(title.encode('utf-8')).hexdigest()

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check for exact content match
            cursor.execute("""
                SELECT id, url FROM articles
                WHERE content_hash = ? OR title_hash = ? OR url = ?
                LIMIT 1
            """, (content_hash, title_hash, url))

            duplicate = cursor.fetchone()
            conn.close()

            if duplicate:
                result['issues'].append(
                    f"Duplicate content detected (ID: {duplicate[0]})")
                result['quality_score'] -= 30
                result['metadata']['duplicate_of'] = duplicate[0]
                result['metadata']['duplicate_url'] = duplicate[1]
            else:
                # Store hashes for future duplicate detection
                result['metadata']['content_hash'] = content_hash
                result['metadata']['title_hash'] = title_hash

        except Exception as e:
            logger.error(f"Error checking for duplicates: {e}")
            result['warnings'].append("Could not check for duplicates")

        return result

    def _detect_spam_content(
            self, article: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Detect spam and low-quality content patterns."""
        content = article.get('content', '').lower()
        title = article.get('title', '').lower()

        # Check for suspicious patterns
        suspicious_found = []
        for pattern in self.suspicious_patterns:
            if re.search(pattern, content) or re.search(pattern, title):
                suspicious_found.append(pattern)

        if suspicious_found:
            result['warnings'].append(
                f"Suspicious patterns detected: {suspicious_found}")
            result['quality_score'] -= len(suspicious_found) * 5

        # Check for excessive capitalization
        if content:
            caps_ratio = sum(1 for c in content if c.isupper()) / len(content)
            if caps_ratio > 0.1:
                result['warnings'].append("Excessive capitalization detected")
                result['quality_score'] -= 10

        # Check for excessive punctuation
        if content:
            punct_ratio = sum(
                1 for c in content if c in '!?.,;:') / len(content)
            if punct_ratio > 0.05:
                result['warnings'].append("Excessive punctuation detected")
                result['quality_score'] -= 5

        # Check for repeated phrases
        if content:
            words = content.split()
            if len(words) > 20:
                # Check for phrases repeated more than 3 times
                phrases = [' '.join(words[i:i + 3])
                           for i in range(len(words) - 2)]
                phrase_counts = {}
                for phrase in phrases:
                    phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1

                repeated_phrases = [
                    p for p, count in phrase_counts.items() if count > 3]
                if repeated_phrases:
                    result['warnings'].append("Repeated phrases detected")
                    result['quality_score'] -= min(10,
                                                   len(repeated_phrases) * 2)

        return result

    def validate_batch(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate a batch of articles and return summary statistics."""
        if not articles:
            return {
                'total_articles': 0,
                'valid_articles': 0,
                'invalid_articles': 0,
                'avg_quality_score': 0,
                'validation_summary': {}
            }

        results = []
        for article in articles:
            validation_result = self.validate_article(article)
            results.append(validation_result)

        # Calculate summary statistics
        valid_count = sum(1 for r in results if r['is_valid'])
        invalid_count = len(results) - valid_count
        avg_quality = sum(r['quality_score'] for r in results) / len(results)

        # Collect common issues
        all_issues = []
        all_warnings = []
        for r in results:
            all_issues.extend(r.get('issues', []))
            all_warnings.extend(r.get('warnings', []))

        # Count issue frequencies
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1

        warning_counts = {}
        for warning in all_warnings:
            warning_counts[warning] = warning_counts.get(warning, 0) + 1

        return {
            'total_articles': len(articles),
            'valid_articles': valid_count,
            'invalid_articles': invalid_count,
            'validation_rate': round(
                (valid_count / len(articles)) * 100,
                2),
            'avg_quality_score': round(
                avg_quality,
                2),
            'common_issues': dict(
                sorted(
                    issue_counts.items(),
                    key=lambda x: x[1],
                    reverse=True)[
                        :10]),
            'common_warnings': dict(
                sorted(
                    warning_counts.items(),
                    key=lambda x: x[1],
                    reverse=True)[
                    :10]),
            'validation_summary': {
                'timestamp': datetime.now().isoformat(),
                'detailed_results': results}}

    def get_quality_report(self, days: int = 7) -> Dict[str, Any]:
        """Generate a quality report for articles in the specified time period."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get articles from the specified period
            cursor.execute("""
                SELECT
                    quality_score, validation_result, created_at,
                    CASE WHEN quality_score >= 60 THEN 1 ELSE 0 END as is_valid
                FROM articles
                WHERE created_at > datetime('now', '-{} days')
                AND validation_result IS NOT NULL
            """.format(days))

            articles = cursor.fetchall()
            conn.close()

            if not articles:
                return {
                    'period_days': days,
                    'total_articles': 0,
                    'message': 'No validated articles found in the specified period'}

            # Calculate statistics
            quality_scores = [a[0] for a in articles if a[0] is not None]
            valid_count = sum(a[3] for a in articles)

            # Quality distribution
            quality_ranges = {
                'excellent (90-100)': sum(1 for s in quality_scores if s >= 90),
                'good (80-89)': sum(1 for s in quality_scores if 80 <= s < 90),
                'fair (70-79)': sum(1 for s in quality_scores if 70 <= s < 80),
                'poor (60-69)': sum(1 for s in quality_scores if 60 <= s < 70),
                'invalid (<60)': sum(1 for s in quality_scores if s < 60)
            }

            return {
                'period_days': days,
                'total_articles': len(articles),
                'valid_articles': valid_count,
                'invalid_articles': len(articles) - valid_count,
                'validation_rate': round(
                    (valid_count / len(articles)) * 100,
                    2),
                'avg_quality_score': round(
                    sum(quality_scores) / len(quality_scores),
                    2) if quality_scores else 0,
                'quality_distribution': quality_ranges,
                'generated_at': datetime.now().isoformat()}

        except Exception as e:
            logger.error(f"Error generating quality report: {e}")
            return {
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }

    def cleanup_invalid_articles(self, min_quality_score: int = 30) -> int:
        """Remove articles with very low quality scores from the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Count articles to be deleted
            cursor.execute("""
                SELECT COUNT(*) FROM articles
                WHERE quality_score < ? AND quality_score IS NOT NULL
            """, (min_quality_score,))

            count_to_delete = cursor.fetchone()[0]

            if count_to_delete > 0:
                # Delete low-quality articles
                cursor.execute("""
                    DELETE FROM articles
                    WHERE quality_score < ? AND quality_score IS NOT NULL
                """, (min_quality_score,))

                # Also delete related analysis results
                cursor.execute("""
                    DELETE FROM analysis_results
                    WHERE article_id NOT IN (SELECT id FROM articles)
                """)

                conn.commit()
                logger.info(
                    f"Cleaned up {count_to_delete} low-quality articles")

            conn.close()
            return count_to_delete

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return 0


# Singleton instance
data_validator = DataValidator()
