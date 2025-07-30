import sqlite3

# Connect to database
conn = sqlite3.connect('data/geopolitical_intel.db')
cursor = conn.cursor()

# Clear processed_data for a sample of articles
cursor.execute("""
    DELETE FROM processed_data 
    WHERE article_id IN (
        SELECT id FROM articles 
        WHERE content IS NOT NULL AND length(content) > 100
        ORDER BY id DESC 
        LIMIT 20
    )
""")
deleted = cursor.rowcount

# Reset risk_level for these articles
cursor.execute("""
    UPDATE articles 
    SET risk_level = NULL 
    WHERE id IN (
        SELECT id FROM articles 
        WHERE content IS NOT NULL AND length(content) > 100
        ORDER BY id DESC 
        LIMIT 20
    )
""")
updated = cursor.rowcount

conn.commit()
conn.close()

print(f"Cleared {deleted} processed entries")
print(f"Reset risk_level for {updated} articles")
print("Ready to reprocess with improved NLP analyzer")