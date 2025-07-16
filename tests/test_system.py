"""
Test suite for the Geopolitical Intelligence System.
"""

import unittest
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from utils.config import Config, DatabaseManager
from data_ingestion.news_collector import NewsAPICollector, RSSCollector
from nlp_processing.text_analyzer import TranslationService, TextClassifier, SentimentAnalyzer


class TestConfig(unittest.TestCase):
    """Test configuration management."""
    
    def test_config_loading(self):
        """Test configuration loading."""
        config = Config()
        self.assertIsInstance(config.get_supported_languages(), list)
        self.assertIn('en', config.get_supported_languages())
    
    def test_database_manager(self):
        """Test database manager initialization."""
        config = Config()
        db = DatabaseManager(config)
        self.assertIsNotNone(db)


class TestDataIngestion(unittest.TestCase):
    """Test data ingestion components."""
    
    def test_newsapi_collector_init(self):
        """Test NewsAPI collector initialization."""
        collector = NewsAPICollector()
        self.assertIsNotNone(collector)
    
    def test_rss_collector_init(self):
        """Test RSS collector initialization."""
        collector = RSSCollector()
        self.assertIsNotNone(collector)


class TestNLPProcessing(unittest.TestCase):
    """Test NLP processing components."""
    
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
    
    def test_rule_based_classification(self):
        """Test rule-based classification fallback."""
        classifier = TextClassifier()
        
        # Test military conflict
        text = "Military forces launched an attack on the border region"
        category, confidence = classifier._rule_based_classification(text)
        self.assertEqual(category, 'military_conflict')
        self.assertGreater(confidence, 0)
        
        # Test protest
        text = "Thousands of protesters gathered in the capital demanding change"
        category, confidence = classifier._rule_based_classification(text)
        self.assertEqual(category, 'protest')
        self.assertGreater(confidence, 0)
        
        # Test neutral
        text = "The weather was pleasant today with sunny skies"
        category, confidence = classifier._rule_based_classification(text)
        self.assertEqual(category, 'neutral')


class TestIntegration(unittest.TestCase):
    """Integration tests."""
    
    def test_full_pipeline_components(self):
        """Test that all main components can be initialized together."""
        try:
            from utils.config import config
            from data_ingestion.news_collector import GeopoliticalNewsCollector
            from nlp_processing.text_analyzer import GeopoliticalTextAnalyzer
            from reporting.report_generator import ReportGenerator
            
            collector = GeopoliticalNewsCollector()
            analyzer = GeopoliticalTextAnalyzer()
            reporter = ReportGenerator()
            
            self.assertIsNotNone(collector)
            self.assertIsNotNone(analyzer)
            self.assertIsNotNone(reporter)
            
        except ImportError as e:
            self.fail(f"Failed to import components: {e}")


def run_tests():
    """Run all tests."""
    print("🧪 Running Geopolitical Intelligence System Tests")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestDataIngestion))
    suite.addTests(loader.loadTestsFromTestCase(TestNLPProcessing))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All tests passed!")
    else:
        print(f"❌ {len(result.failures)} failures, {len(result.errors)} errors")
        
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
