#!/usr/bin/env python3
"""
Test RSS Fetching System
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from data_ingestion.rss_fetcher import RSSFetcher
from utils.config import logger

def test_rss_system():
    """Test the RSS fetching system."""
    print("🚀 Testing RSS Fetching System")
    print("=" * 50)
    
    # Database path
    BASE_DIR = Path(__file__).resolve().parent
    DB_PATH = str(BASE_DIR / 'data' / 'geopolitical_intel.db')
    
    try:
        # Create RSS fetcher
        fetcher = RSSFetcher(DB_PATH)
        print("✓ RSS Fetcher initialized")
        
        # Test with a few high-priority sources
        print("\\n📡 Testing RSS fetch from selected sources...")
        
        # Fetch from all sources (limited for testing)
        results = fetcher.fetch_all_sources(target_language='es')
        
        print(f"\\n📊 Results:")
        print(f"   Total sources: {results['total_sources']}")
        print(f"   Processed sources: {results['processed_sources']}")
        print(f"   Total articles found: {results['total_articles']}")
        print(f"   New articles saved: {results['new_articles']}")
        print(f"   Filtered articles: {results['filtered_articles']}")
        print(f"   Errors: {results['errors']}")
        
        if results['new_articles'] > 0:
            print(f"\\n✅ Successfully fetched and processed {results['new_articles']} new articles!")
        else:
            print(f"\\n⚠️ No new articles were added (may be duplicates or filtered)")
        
        return True
        
    except Exception as e:
        print(f"\\n❌ Error testing RSS system: {e}")
        return False

def show_recent_articles():
    """Show recently added articles."""
    import sqlite3
    
    BASE_DIR = Path(__file__).resolve().parent
    DB_PATH = str(BASE_DIR / 'data' / 'geopolitical_intel.db')
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT title, source, risk_level, country, created_at, url
            FROM articles 
            ORDER BY created_at DESC 
            LIMIT 10
        ''')
        
        articles = cursor.fetchall()
        
        print(f"\\n📰 Recent Articles ({len(articles)}):")
        print("-" * 80)
        
        for i, (title, source, risk_level, country, created_at, url) in enumerate(articles, 1):
            print(f"{i}. [{risk_level.upper()}] {title[:60]}...")
            print(f"   Source: {source} | Country: {country or 'N/A'}")
            print(f"   URL: {url[:60]}...")
            print(f"   Date: {created_at}")
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error showing articles: {e}")

if __name__ == "__main__":
    success = test_rss_system()
    
    if success:
        show_recent_articles()
        print("\\n🎉 RSS system test completed!")
    else:
        print("\\n💥 RSS system test failed!")