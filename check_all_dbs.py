#!/usr/bin/env python3
import sqlite3
import os

def check_db_schema(db_path):
    print(f"Checking database: {db_path}")
    if not os.path.exists(db_path):
        print(f"Database {db_path} does not exist!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("Tables:", [t[0] for t in tables])
        
        # Get articles table schema if it exists
        if any('articles' in table for table in tables):
            cursor.execute("PRAGMA table_info(articles)")
            columns = cursor.fetchall()
            print("Articles columns:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
        else:
            print("No articles table found!")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

# Check both possible databases
check_db_schema('data/geopolitical_intel.db')
print()
check_db_schema('data/news_intelligence.db')
print()
check_db_schema('data/riskmap.db')
