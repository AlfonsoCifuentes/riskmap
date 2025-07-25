import sqlite3

# Connect to the correct database
conn = sqlite3.connect('data/geopolitical_intel.db')
cursor = conn.cursor()

# Reset risk_level for ALL articles to allow processing
cursor.execute("UPDATE articles SET risk_level = NULL")
affected = cursor.rowcount
conn.commit()

print(f"Reset risk_level for {affected} articles")

# Clear processed_data table to start fresh
cursor.execute("DELETE FROM processed_data")
deleted = cursor.rowcount
conn.commit()
print(f"Cleared {deleted} entries from processed_data")

# Verify
cursor.execute("""
    SELECT COUNT(*)
    FROM articles a
    LEFT JOIN processed_data pd ON a.id = pd.article_id
    WHERE pd.article_id IS NULL AND a.risk_level IS NULL
""")
to_process = cursor.fetchone()[0]
print(f"Articles ready to process: {to_process}")

conn.close()