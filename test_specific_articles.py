#!/usr/bin/env python3
"""
Quick test to see if the NLP processing is working on problematic articles
"""

import sqlite3
import sys
from pathlib import Path
import json
import logging
from datetime import datetime

# Add src directory to path
sys.path.append(str(Path(__file__).parent / 'src'))

from nlp_processing.advanced_analyzer import AdvancedNLPAnalyzer
from src.utils.bert_risk_analyzer import BERTRiskAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_problematic_articles():
    """Test the articles that were causing errors"""
    
    print("🧪 Testing Problematic Articles")
    print("=" * 50)
    
    # Connect to database
    db_path = 'data/geopolitical_intel.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Initialize analyzers
    try:
        nlp_analyzer = AdvancedNLPAnalyzer()
        bert_analyzer = BERTRiskAnalyzer()
        print("✅ Analyzers initialized")
    except Exception as e:
        print(f"❌ Error initializing analyzers: {e}")
        return
    
    # Test specific problematic articles
    problematic_ids = [857, 856, 855, 854]
    
    for article_id in problematic_ids:
        print(f"\n🔍 Testing Article {article_id}")
        
        # Get article data
        cursor.execute('''
            SELECT title, content, country 
            FROM articles 
            WHERE id = ?
        ''', (article_id,))
        
        result = cursor.fetchone()
        if not result:
            print(f"   ❌ Article {article_id} not found")
            continue
            
        title, content, country = result
        print(f"   📰 Title: {title[:50]}...")
        
        # Test NLP analysis
        try:
            article_data = {
                'title': title or '',
                'content': content or '',
                'description': ''
            }
            
            print(f"   🧠 Testing NLP analysis...")
            nlp_results = nlp_analyzer.analyze_article_comprehensive(article_data)
            
            if nlp_results is None:
                print(f"   ⚠️  NLP returned None")
                nlp_results = {}
            else:
                print(f"   ✅ NLP successful")
                print(f"       - Entities: {len(nlp_results.get('entities', []) or [])}")
                print(f"       - Key Persons: {len(nlp_results.get('key_persons', []) or [])}")
                print(f"       - Key Locations: {len(nlp_results.get('key_locations', []) or [])}")
            
            print(f"   🤖 Testing BERT analysis...")
            bert_results = bert_analyzer.analyze_risk(
                title=title or '',
                content=content or '',
                country=country
            )
            
            if bert_results is None:
                print(f"   ⚠️  BERT returned None")
                bert_results = {}
            else:
                print(f"   ✅ BERT successful")
                print(f"       - Risk Level: {bert_results.get('level', 'UNKNOWN')}")
                print(f"       - Risk Score: {bert_results.get('score', 0.0):.3f}")
            
            # Test safe combining
            combined_analysis = {
                'nlp_entities': nlp_results.get('entities', []) or [],
                'sentiment_analysis': nlp_results.get('sentiment', {}) or {},
                'key_persons': nlp_results.get('key_persons', []) or [],
                'key_locations': nlp_results.get('key_locations', []) or [],
                'bert_risk_level': bert_results.get('level', 'MEDIUM') or 'MEDIUM',
                'bert_risk_score': bert_results.get('score', 0.0) or 0.0,
            }
            
            print(f"   ✅ Combined analysis successful")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            logger.error(f"Error testing article {article_id}: {e}", exc_info=True)
    
    conn.close()
    print("\n🎯 Test completed")

if __name__ == "__main__":
    test_problematic_articles()