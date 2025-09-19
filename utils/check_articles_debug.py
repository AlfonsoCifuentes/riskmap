#!/usr/bin/env python3
"""
Debug script to check which articles exist in the database
and their image analysis status
"""

import sqlite3
import sys
import os

def get_database_path():
    """Get database path from environment or use default"""
    return os.getenv('DATABASE_PATH', 'riskmap_analysis.db')

def check_articles(article_ids=None):
    """Check article existence and analysis status"""
    try:
        db_path = get_database_path()
        print(f"Checking database: {db_path}")
        
        if not os.path.exists(db_path):
            print(f"❌ Database file does not exist: {db_path}")
            return
            
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if articles table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='articles'
            """)
            
            if not cursor.fetchone():
                print("❌ Articles table does not exist")
                return
            
            # Check if image_analysis table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='image_analysis'
            """)
            
            has_analysis_table = bool(cursor.fetchone())
            print(f"📊 Image analysis table exists: {has_analysis_table}")
            
            if article_ids:
                # Check specific articles
                for article_id in article_ids:
                    cursor.execute("""
                        SELECT id, title, image_url, published_date
                        FROM articles WHERE id = ?
                    """, (article_id,))
                    
                    result = cursor.fetchone()
                    
                    if result:
                        id, title, image_url, published_date = result
                        print(f"\n✅ Article {article_id} found:")
                        print(f"   Title: {title[:60]}...")
                        print(f"   Image URL: {image_url[:80] if image_url else 'None'}")
                        print(f"   Published: {published_date}")
                        
                        # Check image analysis
                        if has_analysis_table:
                            cursor.execute("""
                                SELECT COUNT(*) FROM image_analysis WHERE article_id = ?
                            """, (article_id,))
                            
                            analysis_count = cursor.fetchone()[0]
                            print(f"   Image analysis: {'✅ Yes' if analysis_count > 0 else '❌ No'}")
                        
                    else:
                        print(f"\n❌ Article {article_id} NOT FOUND")
            
            else:
                # Show general stats
                cursor.execute("SELECT COUNT(*) FROM articles")
                total_articles = cursor.fetchone()[0]
                print(f"\n📈 Total articles in database: {total_articles}")
                
                cursor.execute("""
                    SELECT COUNT(*) FROM articles 
                    WHERE image_url IS NOT NULL AND image_url != ''
                """)
                articles_with_images = cursor.fetchone()[0]
                print(f"🖼️  Articles with images: {articles_with_images}")
                
                if has_analysis_table:
                    cursor.execute("SELECT COUNT(*) FROM image_analysis")
                    total_analysis = cursor.fetchone()[0]
                    print(f"🔍 Image analyses: {total_analysis}")
                
                # Show latest articles
                cursor.execute("""
                    SELECT id, title, image_url 
                    FROM articles 
                    ORDER BY id DESC 
                    LIMIT 10
                """)
                
                latest = cursor.fetchall()
                print(f"\n📋 Latest 10 articles:")
                for id, title, image_url in latest:
                    has_image = "🖼️" if image_url else "❌"
                    print(f"   {id}: {has_image} {title[:50]}...")
                    
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Check specific article IDs
        article_ids = [int(x) for x in sys.argv[1:]]
        print(f"Checking specific articles: {article_ids}")
        check_articles(article_ids)
    else:
        # General check
        print("Checking database status...")
        check_articles()
