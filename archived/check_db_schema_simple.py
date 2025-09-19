#!/usr/bin/env python3
import sqlite3

try:
    conn = sqlite3.connect('data/news_intelligence.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Tables:", tables)
    
    # Get articles table schema
    cursor.execute("PRAGMA table_info(articles)")
    columns = cursor.fetchall()
    print("Articles columns:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
