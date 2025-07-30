#!/usr/bin/env python3
"""
Run full RSS ingestion with BERT risk analysis
"""
import os
import warnings

# Suppress TensorFlow warnings BEFORE any imports
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)

import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / 'src'))

from src.data_ingestion.rss_fetcher import RSSFetcher

def run_full_ingestion():
    """Run complete RSS ingestion with BERT analysis."""
    
    print("🚀 Starting FULL RSS ingestion with BERT risk analysis...")
    print("=" * 60)
    
    # Database path
    BASE_DIR = Path(__file__).resolve().parent
    DB_PATH = str(BASE_DIR / 'data' / 'geopolitical_intel.db')
    
    # Create fetcher (now uses BERTRiskAnalyzer)
    fetcher = RSSFetcher(DB_PATH)
    
    # Fetch all sources
    print("📡 Fetching from all RSS sources...")
    results = fetcher.fetch_all_sources(target_language='es')
    
    print(f"\n🎯 RSS INGESTION RESULTS:")
    print(f"  Total sources: {results['total_sources']}")
    print(f"  Processed sources: {results['processed_sources']}")
    print(f"  Total articles found: {results['total_articles']}")
    print(f"  New articles saved: {results['new_articles']}")
    print(f"  Filtered articles: {results['filtered_articles']}")
    print(f"  Errors: {results['errors']}")
    
    if results['new_articles'] > 0:
        print(f"\n✅ SUCCESS: {results['new_articles']} new articles processed with BERT!")
        
        # Check the risk distribution of new articles
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                risk_level,
                COUNT(*) as count
            FROM articles 
            WHERE created_at > datetime('now', '-1 hour')
            GROUP BY risk_level
            ORDER BY 
                CASE risk_level 
                    WHEN 'high' THEN 1 
                    WHEN 'medium' THEN 2 
                    WHEN 'low' THEN 3 
                    ELSE 4 
                END
        """)
        
        print(f"\n📊 RISK DISTRIBUTION (last hour):")
        for row in cursor.fetchall():
            risk_level, count = row
            print(f"  {risk_level or 'NULL':>8}: {count:>4} articles")
        
        conn.close()
    else:
        print(f"\nℹ️  No new articles found (all articles may already exist)")

if __name__ == "__main__":
    run_full_ingestion()