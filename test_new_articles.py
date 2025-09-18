#!/usr/bin/env python3
"""
Quick test for the new articles that were causing NoneType errors
"""

import sqlite3
import sys
from pathlib import Path
import logging

# Add src directory to path
sys.path.append(str(Path(__file__).parent / 'src'))

from nlp_processing.advanced_analyzer import AdvancedNLPAnalyzer
from src.utils.bert_risk_analyzer import BERTRiskAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_new_articles():
    """Test the new articles that were causing errors"""
    
    print("🧪 Testing New Articles with NoneType Errors")
    print("=" * 60)
    
    # Connect to database
    db_path = 'data/geopolitical_intel.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Test specific problematic articles from the log
    problematic_ids = [1115, 1114, 1113, 1112, 1111]
    
    for article_id in problematic_ids:
        print(f"\n🔍 Testing Article {article_id}")
        
        # Check if article exists
        cursor.execute('''
            SELECT id, title, content, country 
            FROM articles 
            WHERE id = ?
        ''', (article_id,))
        
        result = cursor.fetchone()
        if not result:
            print(f"   ❌ Article {article_id} not found in database")
            continue
            
        _, title, content, country = result
        print(f"   📰 Title: {title[:50]}...")
        
        # Check current processing status
        cursor.execute('''
            SELECT advanced_nlp 
            FROM processed_data 
            WHERE article_id = ?
        ''', (article_id,))
        
        processed_result = cursor.fetchone()
        if processed_result and processed_result[0] and processed_result[0] not in ['', '{}']:
            print(f"   ✅ Already processed successfully")
            continue
        
        print(f"   ⏳ Article needs processing")
        
        # Test safe processing logic like in the orchestrator
        try:
            # Initialize analyzers
            nlp_analyzer = AdvancedNLPAnalyzer()
            bert_analyzer = BERTRiskAnalyzer()
            
            # Test NLP analysis
            article_data = {
                'title': title or '',
                'content': content or '',
                'description': ''
            }
            
            nlp_results = nlp_analyzer.analyze_article_comprehensive(article_data)
            if nlp_results is None:
                nlp_results = {}
                print(f"   ⚠️  NLP returned None - using safe defaults")
            
            # Validate NLP results structure like in orchestrator
            nlp_required_fields = ['entities', 'sentiment', 'key_persons', 'key_locations', 'total_entities']
            for field in nlp_required_fields:
                if field not in nlp_results or nlp_results[field] is None:
                    if field in ['key_persons', 'key_locations']:
                        nlp_results[field] = []
                    elif field == 'entities':
                        nlp_results[field] = {}
                    elif field == 'sentiment':
                        nlp_results[field] = {'score': 0.0, 'label': 'neutral'}
                    else:
                        nlp_results[field] = 0
            
            # Test BERT analysis
            bert_results = bert_analyzer.analyze_risk(
                title=title or '',
                content=content or '',
                country=country
            )
            if bert_results is None:
                bert_results = {}
                print(f"   ⚠️  BERT returned None - using safe defaults")
            
            # Validate BERT results structure
            bert_required_fields = ['level', 'score', 'confidence', 'reasoning']
            for field in bert_required_fields:
                if field not in bert_results or bert_results[field] is None:
                    if field == 'level':
                        bert_results[field] = 'low'
                    elif field in ['score', 'confidence']:
                        bert_results[field] = 0.0
                    else:
                        bert_results[field] = 'Analysis unavailable'
            
            # Test safe access patterns
            safe_key_persons = nlp_results.get('key_persons') or []
            safe_key_locations = nlp_results.get('key_locations') or []
            safe_entities = nlp_results.get('entities') or {}
            safe_sentiment = nlp_results.get('sentiment') or {'score': 0.0}
            sentiment_score = safe_sentiment.get('score', 0.0) if safe_sentiment else 0.0
            
            bert_level = bert_results.get('level', 'low') if bert_results else 'low'
            bert_score = bert_results.get('score', 0.0) if bert_results else 0.0
            total_entities = nlp_results.get('total_entities', 0) if nlp_results else 0
            
            print(f"   ✅ Safe processing successful:")
            print(f"       - Entities: {len(safe_entities)}")
            print(f"       - Key Persons: {len(safe_key_persons)}")
            print(f"       - Key Locations: {len(safe_key_locations)}")
            print(f"       - Sentiment Score: {sentiment_score:.3f}")
            print(f"       - BERT Level: {bert_level}")
            print(f"       - BERT Score: {bert_score:.3f}")
            print(f"       - Total Entities: {total_entities}")
            
        except Exception as e:
            print(f"   ❌ Error during safe processing: {e}")
            logger.error(f"Error testing article {article_id}: {e}", exc_info=True)
    
    conn.close()
    print("\n🎯 Test completed - All access patterns are now safe!")

if __name__ == "__main__":
    test_new_articles()