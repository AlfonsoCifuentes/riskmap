import sqlite3

# Check the correct database
conn = sqlite3.connect('data/geopolitical_intel.db')
cursor = conn.cursor()

# Check total articles
cursor.execute("SELECT COUNT(*) FROM articles")
total = cursor.fetchone()[0]
print(f"Total articles in geopolitical_intel.db: {total}")

# Check articles without processed_data
cursor.execute("""
    SELECT COUNT(*) 
    FROM articles a
    LEFT JOIN processed_data pd ON a.id = pd.article_id
    WHERE pd.article_id IS NULL
""")
unprocessed = cursor.fetchone()[0]
print(f"Unprocessed articles: {unprocessed}")

# Check articles with risk_level NULL
cursor.execute("""
    SELECT COUNT(*) 
    FROM articles 
    WHERE risk_level IS NULL
""")
no_risk = cursor.fetchone()[0]
print(f"Articles without risk_level: {no_risk}")

# Check articles that meet both conditions
cursor.execute("""
    SELECT COUNT(*)
    FROM articles a
    LEFT JOIN processed_data pd ON a.id = pd.article_id
    WHERE pd.article_id IS NULL AND a.risk_level IS NULL
""")
to_process = cursor.fetchone()[0]
print(f"Articles to process (no processed_data AND no risk_level): {to_process}")

# Show sample of articles
cursor.execute("""
    SELECT id, title, language, risk_level, created_at
    FROM articles
    ORDER BY created_at DESC
    LIMIT 5
""")
print("\nLatest 5 articles:")
for row in cursor.fetchall():
    print(f"  ID: {row[0]}, Title: {row[1][:50] if row[1] else 'None'}..., Lang: {row[2]}, Risk: {row[3]}, Created: {row[4]}")

# Check if processed_data table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='processed_data'")
if cursor.fetchone():
    print("\nTable 'processed_data' exists")
    cursor.execute("SELECT COUNT(*) FROM processed_data")
    processed_count = cursor.fetchone()[0]
    print(f"Total processed entries: {processed_count}")
else:
    print("\nTable 'processed_data' does NOT exist")

conn.close()