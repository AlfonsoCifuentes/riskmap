#!/usr/bin/env python3
"""
Script to verify the current NLP processing optimization status
"""
import sqlite3
import json

# Database path
db_path = "./data/geopolitical_intel.db"

try:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=== ANALYZING NLP PROCESSING STATUS ===\n")
    
    # Check articles table processed status
    cursor.execute("SELECT processed, COUNT(*) as count FROM articles GROUP BY processed")
    processed_stats = cursor.fetchall()
    
    print("📊 ARTICLES TABLE - processed flag status:")
    for row in processed_stats:
        status_text = "Unprocessed" if row['processed'] == 0 else "Processed" if row['processed'] == 1 else "Error"
        print(f"   {status_text} (processed={row['processed']}): {row['count']} articles")
    
    # Check processed_data table status
    cursor.execute("SELECT COUNT(*) as total FROM processed_data")
    processed_data_count = cursor.fetchone()['total']
    print(f"\n📊 PROCESSED_DATA TABLE: {processed_data_count} records")
    
    # Check for advanced_nlp data
    cursor.execute("SELECT COUNT(*) as count FROM processed_data WHERE advanced_nlp IS NOT NULL AND advanced_nlp != ''")
    advanced_nlp_count = cursor.fetchone()['count']
    print(f"📊 ADVANCED NLP DATA: {advanced_nlp_count} records")
    
    # Check articles without corresponding processed_data
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM articles a 
        LEFT JOIN processed_data pd ON a.id = pd.article_id 
        WHERE pd.article_id IS NULL
    """)
    unmatched_count = cursor.fetchone()['count']
    print(f"📊 ARTICLES WITHOUT PROCESSED_DATA: {unmatched_count} articles")
    
    # Check articles with processed_data but processed=0
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM articles a 
        INNER JOIN processed_data pd ON a.id = pd.article_id 
        WHERE a.processed = 0
    """)
    inconsistent_count = cursor.fetchone()['count']
    print(f"📊 PROCESSED_DATA EXISTS BUT processed=0: {inconsistent_count} articles")
    
    # Sample some articles to check their NLP status
    cursor.execute("""
        SELECT a.id, a.title, a.processed, 
               CASE WHEN pd.advanced_nlp IS NOT NULL THEN 'YES' ELSE 'NO' END as has_advanced_nlp
        FROM articles a 
        LEFT JOIN processed_data pd ON a.id = pd.article_id 
        ORDER BY a.created_at DESC 
        LIMIT 10
    """)
    sample_articles = cursor.fetchall()
    
    print("\n🔍 SAMPLE ARTICLES STATUS:")
    for article in sample_articles:
        print(f"   ID {article['id']}: processed={article['processed']}, has_advanced_nlp={article['has_advanced_nlp']}")
        print(f"      Title: {article['title'][:60]}...")
    
    print("\n=== OPTIMIZATION RECOMMENDATIONS ===")
    if inconsistent_count > 0:
        print(f"⚠️  INCONSISTENCY: {inconsistent_count} articles have processed_data but processed=0")
        print("   Recommendation: Update articles.processed=1 where processed_data exists")
    
    if unmatched_count > 0:
        print(f"⚠️  MISSING DATA: {unmatched_count} articles lack processed_data")
        print("   Recommendation: Process these articles with NLP")
    
    if advanced_nlp_count < processed_data_count:
        missing_advanced = processed_data_count - advanced_nlp_count
        print(f"⚠️  INCOMPLETE ADVANCED NLP: {missing_advanced} records lack advanced_nlp data")
        print("   Recommendation: Run advanced NLP on these records")
    
    conn.close()
    print("\n✅ Analysis complete!")

except Exception as e:
    print(f"❌ Error analyzing database: {e}")
    import traceback
    traceback.print_exc()