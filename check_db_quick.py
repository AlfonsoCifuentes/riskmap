#!/usr/bin/env python3
import sqlite3
import os

db_path = 'data/geopolitical_intelligence.db'

try:
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables found: {tables}")
        
        # Check articles table structure if it exists
        if 'articles' in tables:
            cursor.execute("PRAGMA table_info(articles);")
            columns = cursor.fetchall()
            print(f"\nArticles table structure:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            # Count articles
            cursor.execute("SELECT COUNT(*) FROM articles")
            count = cursor.fetchone()[0]
            print(f"\nTotal articles: {count}")
            
            if count > 0:
                # Show sample article
                cursor.execute("SELECT id, title, location, risk_score FROM articles LIMIT 1")
                sample = cursor.fetchone()
                print(f"Sample article: ID={sample[0]}, Title={sample[1][:50]}..., Location={sample[2]}, Risk={sample[3]}")
        
        conn.close()
    else:
        print(f"Database not found at: {db_path}")
        
except Exception as e:
    print(f"Error: {e}")
