"""
Comprehensive test suite for the Geopolitical Intelligence System.
Includes unit tests, integration tests, and system validation.
"""

import unittest
import sys
import sqlite3
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from utils.config import Config, DatabaseManager
from data_ingestion.news_collector import NewsAPICollector, RSSCollector
from nlp_processing.text_analyzer import TranslationService, TextClassifier, SentimentAnalyzer
from monitoring.system_monitor import SystemMonitor
from data_quality.validator import DataValidator


class TestConfig(unittest.TestCase):
    """Test configuration management."""
    
    def setUp(self):
        """Set up test environment."""
        self.config = Config()
    
    def test_config_loading(self):
        """Test configuration loading."""
        self.assertIsInstance(self.config.get_supported_languages(), list)
        self.assertIn('en', self.config.get_supported_languages())
    
    def test_database_manager(self):
        """Test database manager initialization."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        
        try:
            # Create a test config with temp database
            test_config = {'database': {'path': temp_db_path}}
            db = DatabaseManager(test_config)
            self.assertIsNotNone(db)
            
            # Test connection
            conn = db.get_connection()
            self.assertIsNotNone(conn)
            conn.close()
            
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Test required API keys
        required_keys = ['newsapi', 'openai']
        for key in required_keys:
            self.assertIn(key, self.config.config)


class TestDataIngestion(unittest.TestCase):
    """Test data ingestion components."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_config = {
            'newsapi': {'api_key': 'test_key'},
            'rss': {'feeds': ['http://example.com/feed.xml']}
        }
    
    def test_newsapi_collector_init(self):
        """Test NewsAPI collector initialization."""
        collector = NewsAPICollector()
        self.assertIsNotNone(collector)
    
    def test_rss_collector_init(self):
        """Test RSS collector initialization."""
        collector = RSSCollector()
        self.assertIsNotNone(collector)
    
    @patch('requests.get')
    def test_newsapi_fetch_articles(self, mock_get):
        """Test NewsAPI article fetching."""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'ok',
            'articles': [
                {
                    'title': 'Test Article',
                    'description': 'Test description',
                    'url': 'http://example.com/article',
                    'publishedAt': '2024-01-01T00:00:00Z',
                    'source': {'name': 'Test Source'},
                    'content': 'Test content'
                }
            ]
        }
        mock_get.return_value = mock_response
        
        collector = NewsAPICollector()
        articles = collector.fetch_articles_by_topic('geopolitics')
        
        self.assertIsInstance(articles, list)
        mock_get.assert_called_once()
    
    def test_article_validation(self):
        """Test article data validation."""
        valid_article = {
            'title': 'Test Article',
            'content': 'This is a test article with sufficient content length.',
            'url': 'http://example.com/article',
            'published_at': '2024-01-01T00:00:00Z',
            'source': {'name': 'Test Source'}
        }
        
        validator = DataValidator()
        result = validator.validate_article(valid_article)
        
        self.assertIsInstance(result, dict)
        self.assertIn('is_valid', result)
        self.assertIn('quality_score', result)


class TestNLPProcessing(unittest.TestCase):
    """Test NLP processing components."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_text = "This is a test article about international relations and geopolitics."
    
    def test_translation_service_init(self):
        """Test translation service initialization."""
        service = TranslationService()
        self.assertIsNotNone(service)
    
    def test_text_classifier_init(self):
        """Test text classifier initialization."""
        classifier = TextClassifier()
        self.assertIsNotNone(classifier)
    
    def test_sentiment_analyzer_init(self):
        """Test sentiment analyzer initialization."""
        analyzer = SentimentAnalyzer()
        self.assertIsNotNone(analyzer)
    
    @patch('openai.ChatCompletion.create')
    def test_sentiment_analysis(self, mock_openai):
        """Test sentiment analysis."""
        # Mock OpenAI response
        mock_openai.return_value = {
            'choices': [
                {
                    'message': {
                        'content': json.dumps({
                            'sentiment': 'neutral',
                            'confidence': 0.8,
                            'reasoning': 'Test reasoning'
                        })
                    }
                }
            ]
        }
        
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze_sentiment(self.test_text)
        
        self.assertIsInstance(result, dict)
        self.assertIn('sentiment', result)
        self.assertIn('confidence', result)
    
    def test_text_classification(self):
        """Test text classification for geopolitical content."""
        classifier = TextClassifier()
        
        # Test geopolitical keywords detection
        geopolitical_text = "The diplomatic tensions between countries are escalating."
        result = classifier.classify_geopolitical_relevance(geopolitical_text)
        
        self.assertIsInstance(result, dict)
        self.assertIn('is_geopolitical', result)
        self.assertIn('confidence', result)


class TestSystemMonitoring(unittest.TestCase):
    """Test system monitoring and health checks."""
    
    def setUp(self):
        """Set up test environment."""
        self.monitor = SystemMonitor()
    
    def test_monitor_init(self):
        """Test system monitor initialization."""
        self.assertIsNotNone(self.monitor)
    
    def test_system_resources_check(self):
        """Test system resources monitoring."""
        result = self.monitor._check_system_resources()
        
        self.assertIsInstance(result, dict)
        self.assertIn('status', result)
        self.assertIn('cpu_percent', result)
        self.assertIn('memory_percent', result)
        self.assertIn('disk_percent', result)
    
    def test_database_health_check(self):
        """Test database health monitoring."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        
        try:
            # Create a test database
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE articles (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()
            
            # Update monitor to use test database
            self.monitor.db_path = temp_db_path
            
            result = self.monitor._check_database_health()
            
            self.assertIsInstance(result, dict)
            self.assertIn('status', result)
            self.assertIn('tables_found', result)
            
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)
    
    def test_health_check_comprehensive(self):
        """Test comprehensive health check."""
        health_status = self.monitor.check_system_health()
        
        self.assertIsInstance(health_status, dict)
        self.assertIn('overall_status', health_status)
        self.assertIn('timestamp', health_status)
        self.assertIn('checks', health_status)


class TestDataQuality(unittest.TestCase):
    """Test data quality validation."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = DataValidator()
    
    def test_validator_init(self):
        """Test data validator initialization."""
        self.assertIsNotNone(self.validator)
    
    def test_article_validation_valid(self):
        """Test validation of valid article."""
        valid_article = {
            'title': 'Test Article Title',
            'content': 'This is a test article with sufficient content length to pass validation checks. ' * 5,
            'url': 'https://example.com/article',
            'published_at': '2024-01-01T00:00:00Z',
            'source': {'name': 'Test Source'}
        }
        
        result = self.validator.validate_article(valid_article)
        
        self.assertIsInstance(result, dict)
        self.assertIn('is_valid', result)
        self.assertIn('quality_score', result)
        self.assertTrue(result['quality_score'] > 60)
    
    def test_article_validation_invalid(self):
        """Test validation of invalid article."""
        invalid_article = {
            'title': 'Short',
            'content': 'Too short',
            'url': 'invalid-url',
            'published_at': 'invalid-date',
            'source': {}
        }
        
        result = self.validator.validate_article(invalid_article)
        
        self.assertIsInstance(result, dict)
        self.assertIn('is_valid', result)
        self.assertIn('quality_score', result)
        self.assertFalse(result['is_valid'])
        self.assertTrue(len(result.get('issues', [])) > 0)
    
    def test_duplicate_detection(self):
        """Test duplicate article detection."""
        article1 = {
            'title': 'Unique Test Article',
            'content': 'This is a unique test article for duplicate detection.',
            'url': 'https://example.com/unique-article',
            'published_at': '2024-01-01T00:00:00Z',
            'source': {'name': 'Test Source'}
        }
        
        article2 = {
            'title': 'Unique Test Article',  # Same title
            'content': 'This is a unique test article for duplicate detection.',  # Same content
            'url': 'https://example.com/different-url',
            'published_at': '2024-01-01T00:00:00Z',
            'source': {'name': 'Test Source'}
        }
        
        result1 = self.validator.validate_article(article1)
        result2 = self.validator.validate_article(article2)
        
        # Second article should detect similarity (though not exact duplicate without DB)
        self.assertIsInstance(result1, dict)
        self.assertIsInstance(result2, dict)
    
    def test_spam_detection(self):
        """Test spam content detection."""
        spam_article = {
            'title': 'AMAZING DEAL - CLICK HERE NOW!!!',
            'content': 'You won\'t believe this amazing deal! Click here now to see this weird trick that doctors hate!',
            'url': 'https://spam-site.com/deal',
            'published_at': '2024-01-01T00:00:00Z',
            'source': {'name': 'Spam Source'}
        }
        
        result = self.validator.validate_article(spam_article)
        
        self.assertIsInstance(result, dict)
        self.assertTrue(len(result.get('warnings', [])) > 0)
        self.assertTrue(result['quality_score'] < 80)  # Should be penalized for spam patterns


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db_path = self.temp_db.name
        self.temp_db.close()
        
        # Create test database schema
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                published_at TIMESTAMP,
                source TEXT,
                language TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed BOOLEAN DEFAULT FALSE,
                quality_score REAL,
                content_hash TEXT,
                title_hash TEXT,
                validation_result TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER,
                sentiment TEXT,
                risk_level TEXT,
                summary TEXT,
                entities TEXT,
                key_topics TEXT,
                confidence_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES articles (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def tearDown(self):
        """Clean up integration test environment."""
        if os.path.exists(self.temp_db_path):
            os.unlink(self.temp_db_path)
    
    def test_end_to_end_pipeline(self):
        """Test complete end-to-end pipeline."""
        # Test data insertion
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        
        test_article = (
            'Test Geopolitical Article',
            'This is a test article about international relations and diplomatic tensions.',
            'https://example.com/test-article',
            '2024-01-01 00:00:00',
            'Test Source',
            'en'
        )
        
        cursor.execute('''
            INSERT INTO articles (title, content, url, published_at, source, language)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', test_article)
        
        article_id = cursor.lastrowid
        conn.commit()
        
        # Test analysis result insertion
        analysis_result = (
            article_id,
            'neutral',
            'medium',
            'Test summary of the article',
            '[]',
            '["geopolitics", "diplomacy"]',
            0.85
        )
        
        cursor.execute('''
            INSERT INTO analysis_results 
            (article_id, sentiment, risk_level, summary, entities, key_topics, confidence_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', analysis_result)
        
        conn.commit()
        
        # Test data retrieval
        cursor.execute('''
            SELECT a.*, ar.sentiment, ar.risk_level 
            FROM articles a 
            LEFT JOIN analysis_results ar ON a.id = ar.article_id
            WHERE a.id = ?
        ''', (article_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[1], 'Test Geopolitical Article')  # title
        self.assertEqual(result[8], 'neutral')  # sentiment
    
    def test_data_quality_integration(self):
        """Test data quality validation integration."""
        # Update validator to use test database
        validator = DataValidator()
        validator.db_path = self.temp_db_path
        
        # Test quality report with empty database
        quality_report = validator.get_quality_report(days=7)
        
        self.assertIsInstance(quality_report, dict)
        self.assertEqual(quality_report.get('total_articles', 0), 0)
    
    def test_monitoring_integration(self):
        """Test system monitoring integration."""
        # Update monitor to use test database
        monitor = SystemMonitor()
        monitor.db_path = self.temp_db_path
        
        # Test health check
        health_status = monitor.check_system_health()
        
        self.assertIsInstance(health_status, dict)
        self.assertIn('overall_status', health_status)
        
        # Test performance metrics
        metrics = monitor.get_performance_metrics(hours=24)
        
        self.assertIsInstance(metrics, dict)
        self.assertIn('total_articles', metrics)


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases."""
    
    def test_invalid_database_path(self):
        """Test handling of invalid database path."""
        monitor = SystemMonitor()
        monitor.db_path = '/invalid/path/database.db'
        
        result = monitor._check_database_health()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('status'), 'error')
    
    def test_malformed_article_data(self):
        """Test handling of malformed article data."""
        validator = DataValidator()
        
        malformed_data = {
            'title': None,
            'content': 123,  # Wrong type
            'url': 'not-a-url',
            'published_at': 'invalid-date'
        }
        
        result = validator.validate_article(malformed_data)
        
        self.assertIsInstance(result, dict)
        self.assertFalse(result.get('is_valid', True))
        self.assertTrue(len(result.get('issues', [])) > 0)
    
    def test_empty_content_handling(self):
        """Test handling of empty or minimal content."""
        validator = DataValidator()
        
        empty_article = {
            'title': '',
            'content': '',
            'url': '',
            'published_at': '',
            'source': {}
        }
        
        result = validator.validate_article(empty_article)
        
        self.assertIsInstance(result, dict)
        self.assertFalse(result.get('is_valid', True))


def run_tests():
    """Run all tests."""
    print("Running Geopolitical Intelligence System Test Suite...")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestConfig,
        TestDataIngestion,
        TestNLPProcessing,
        TestSystemMonitoring,
        TestDataQuality,
        TestIntegration,
        TestErrorHandling
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFailures ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print(f"\nErrors ({len(result.errors)}):")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
