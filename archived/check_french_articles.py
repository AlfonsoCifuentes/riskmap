#!/usr/bin/env python3

import sqlite3

conn = sqlite3.connect('data/geopolitical_intel.db')
cursor = conn.cursor()

# Check for French articles
cursor.execute("""
    SELECT title 
    FROM articles 
    WHERE geopolitical_relevance = 1 
    AND (title LIKE '%français%' OR title LIKE 'Le %' OR title LIKE 'les %' OR title LIKE 'La %' OR title LIKE 'sur %' OR title LIKE 'dans %' OR title LIKE 'avec %' OR title LIKE 'pour %')
    LIMIT 10
""")

rows = cursor.fetchall()
print("French articles found:")
for row in rows:
    print(f"- {row[0]}")

# Check total article count
cursor.execute("SELECT COUNT(*) FROM articles WHERE geopolitical_relevance = 1")
total_count = cursor.fetchone()[0]
print(f"\nTotal geopolitical articles: {total_count}")

conn.close()