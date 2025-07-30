import sqlite3
from datetime import datetime, timedelta

# Connect to the correct database
conn = sqlite3.connect('data/geopolitical_intel.db')
cursor = conn.cursor()

# Check total articles
cursor.execute("SELECT COUNT(*) FROM articles")
total = cursor.fetchone()[0]
print(f"Total articles: {total}")

# Check articles from last hour
cursor.execute("""
    SELECT COUNT(*) FROM articles 
    WHERE created_at > datetime('now', '-1 hour')
""")
recent = cursor.fetchone()[0]
print(f"Articles added in last hour: {recent}")

# Show latest 5 articles
cursor.execute("""
    SELECT id, title, source, language, created_at 
    FROM articles 
    ORDER BY created_at DESC 
    LIMIT 5
""")
print("\nLatest 5 articles:")
for row in cursor.fetchall():
    print(f"  ID: {row[0]}, Source: {row[2]}, Lang: {row[3]}, Created: {row[4]}")
    print(f"     Title: {row[1][:80] if row[1] else 'None'}...")

conn.close()