#!/usr/bin/env python3
"""
Test directo del guardado de artículos para verificar el problema.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import sqlite3
import logging
from datetime import datetime

from src.utils.config import config, DatabaseManager
from src.data_ingestion.news_collector import NewsAPICollector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_save_directly():
    """Test directo del guardado"""
    logger.info("=== TEST SAVE DIRECTLY ===")
    
    try:
        collector = NewsAPICollector()
        
        # Test collection
        articles = collector.search_everything(
            query="conflict",
            language="en",
            max_articles=3
        )
        
        logger.info(f"Collected {len(articles)} articles")
        
        # Show details of collected articles
        for i, article in enumerate(articles):
            logger.info(f"Article {i+1}:")
            logger.info(f"  Title: {article.get('title', 'No title')}")
            logger.info(f"  Content length: {len(article.get('content', '') or '')}")
            logger.info(f"  URL: {article.get('url', 'No URL')}")
            logger.info(f"  Language: {article.get('language', 'No lang')}")
            logger.info(f"  Source: {article.get('source', 'No source')}")
            
        # Check if articles meet the saving criteria
        valid_articles = []
        for article in articles:
            content = article.get('content', '') or ''
            if len(content) > 50:
                valid_articles.append(article)
            else:
                logger.warning(f"Article filtered out - content too short: {len(content)} chars")
        
        logger.info(f"Valid articles for saving: {len(valid_articles)}")
        
        # Manual save test
        if valid_articles:
            logger.info("Attempting manual save...")
            collector._save_articles(valid_articles)
            logger.info("Save completed")
        
        # Check database after save
        conn = sqlite3.connect(config.get_database_path())
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM articles WHERE language = 'en';")
        en_count = cursor.fetchone()[0]
        logger.info(f"English articles in DB: {en_count}")
        
        cursor.execute("SELECT title, language, created_at FROM articles WHERE language = 'en' ORDER BY created_at DESC LIMIT 3;")
        recent_en = cursor.fetchall()
        logger.info("Recent English articles:")
        for article in recent_en:
            logger.info(f"  - {article[1]}: {article[0][:50]}... ({article[2]})")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_save_directly()
