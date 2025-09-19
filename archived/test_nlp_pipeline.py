#!/usr/bin/env python3
"""
Test script to verify the NLP pipeline is working without NoneType errors
"""

import sys
import os
import sqlite3
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_nlp_pipeline():
    """Test the NLP pipeline on a few articles to ensure no NoneType errors"""
    try:
        # Import after path setup
        from src.nlp_processing.advanced_analyzer import AdvancedNLPAnalyzer
        from src.ai.bert_risk_analyzer import BERTRiskAnalyzer
        
        print("🧪 Testing NLP Pipeline")
        print("=" * 60)
        
        # Initialize analyzers directly
        nlp_analyzer = AdvancedNLPAnalyzer()
        bert_analyzer = BERTRiskAnalyzer()
        
        # Get some articles from database to test
        db_path = './data/geopolitical_intel.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get first 5 articles without advanced NLP processing
        cursor.execute('''
            SELECT a.id, a.title, a.content 
            FROM articles a
            LEFT JOIN processed_data p ON a.id = p.article_id
            WHERE a.content IS NOT NULL 
            AND a.content != ''
            AND (p.advanced_nlp IS NULL OR p.advanced_nlp = '')
            LIMIT 5
        ''')
        
        test_articles = cursor.fetchall()
        conn.close()
        
        if not test_articles:
            print("❌ No articles found for testing")
            return False
            
        print(f"📄 Found {len(test_articles)} articles for testing")
        print()
        
        success_count = 0
        error_count = 0
        
        for article_id, title, content in test_articles:
            try:
                print(f"🔍 Testing Article {article_id}: {title[:50]}...")
                
                # Test advanced NLP processing
                nlp_results = nlp_analyzer.analyze_text(content)
                
                print(f"   ✅ NLP Analysis completed")
                print(f"   📊 Entities: {len(nlp_results.get('entities', []) or [])}")
                print(f"   👤 Key Persons: {len(nlp_results.get('key_persons', []) or [])}")
                print(f"   📍 Key Locations: {len(nlp_results.get('key_locations', []) or [])}")
                
                sentiment = nlp_results.get('sentiment', {})
                if sentiment:
                    print(f"   😊 Sentiment: {sentiment.get('label', 'neutral')} ({sentiment.get('score', 0.0):.3f})")
                else:
                    print(f"   😊 Sentiment: neutral (0.000)")
                
                # Test BERT risk analysis
                bert_results = bert_analyzer.analyze_geopolitical_risk(content)
                
                print(f"   🎯 BERT Analysis completed")
                print(f"   ⚠️  Risk Score: {bert_results.get('risk_score', 0.0):.3f}")
                print(f"   🏷️  Category: {bert_results.get('category', 'unknown')}")
                
                success_count += 1
                print(f"   ✅ Article {article_id} processed successfully")
                
            except Exception as e:
                error_count += 1
                print(f"   ❌ Error processing article {article_id}: {str(e)}")
                logger.error(f"Error processing article {article_id}: {str(e)}", exc_info=True)
            
            print()
        
        print("=" * 60)
        print(f"📊 Test Results:")
        print(f"   ✅ Successful: {success_count}")
        print(f"   ❌ Errors: {error_count}")
        print(f"   📈 Success Rate: {(success_count / len(test_articles) * 100):.1f}%")
        
        if error_count == 0:
            print("🎉 All tests passed! NLP pipeline is working correctly.")
            return True
        else:
            print("⚠️  Some tests failed. Check the errors above.")
            return False
            
    except Exception as e:
        print(f"❌ Critical error in test setup: {str(e)}")
        logger.error(f"Critical error in test setup: {str(e)}", exc_info=True)
        return False

def check_database_status():
    """Check the current status of the database"""
    try:
        db_path = './data/geopolitical_intel.db'
        if not os.path.exists(db_path):
            print(f"❌ Database not found at {db_path}")
            return False
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check articles table
        cursor.execute('SELECT COUNT(*) FROM articles')
        total_articles = cursor.fetchone()[0]
        
        # Check articles with content
        cursor.execute('SELECT COUNT(*) FROM articles WHERE content IS NOT NULL AND content != ""')
        articles_with_content = cursor.fetchone()[0]
        
        # Check processed data
        cursor.execute('SELECT COUNT(*) FROM processed_data WHERE advanced_nlp IS NOT NULL AND advanced_nlp != ""')
        processed_articles = cursor.fetchone()[0]
        
        conn.close()
        
        print("📊 Database Status:")
        print(f"   📄 Total Articles: {total_articles}")
        print(f"   📝 Articles with Content: {articles_with_content}")
        print(f"   🧠 Processed Articles: {processed_articles}")
        print(f"   ⏳ Pending Processing: {articles_with_content - processed_articles}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking database status: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔬 RiskMap NLP Pipeline Test")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check database status first
    if not check_database_status():
        sys.exit(1)
    
    # Test NLP pipeline
    success = test_nlp_pipeline()
    
    print()
    print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success:
        print("🎉 Test completed successfully!")
        sys.exit(0)
    else:
        print("❌ Test failed!")
        sys.exit(1)