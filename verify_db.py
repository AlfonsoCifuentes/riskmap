#!/usr/bin/env python3
import sqlite3
import os

def check_database(db_path):
    if not os.path.exists(db_path):
        print(f"{db_path}: Not found")
        return
        
    print(f"=== {db_path} ===")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Tables: {[t[0] for t in tables]}")
    
    for table_name in [t[0] for t in tables]:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  {table_name}: {count} rows")
        
        # If this is articles table, show more details
        if table_name == 'articles':
            cursor.execute("PRAGMA table_info(articles)")
            columns = cursor.fetchall()
            print(f"    Columns: {[col[1] for col in columns]}")
            
            # Show language distribution
            try:
                cursor.execute("SELECT language, COUNT(*) FROM articles GROUP BY language ORDER BY COUNT(*) DESC")
                lang_dist = cursor.fetchall()
                print("    Languages:")
                for lang, cnt in lang_dist:
                    print(f"      {lang}: {cnt}")
            except:
                pass
                
    conn.close()
    print()

# Check all databases
db_files = [
    'data/articles.db',
    'data/geopolitical_intel.db', 
    'data/geopolitical_intelligence.db',
    'data/news_database.db',
    'data/osint_data.db'
]

for db_file in db_files:
    check_database(db_file)
