import sqlite3

# Connect to the correct database
conn = sqlite3.connect('data/geopolitical_intel.db')
cursor = conn.cursor()

# Check processed_data
cursor.execute("SELECT COUNT(*) FROM processed_data")
processed_count = cursor.fetchone()[0]
print(f"Total entries in processed_data: {processed_count}")

# Check articles with updated risk_level
cursor.execute("SELECT COUNT(*) FROM articles WHERE risk_level IS NOT NULL")
with_risk = cursor.fetchone()[0]
print(f"Articles with risk_level: {with_risk}")

# Show some processed data
cursor.execute("""
    SELECT pd.article_id, pd.category, pd.sentiment, a.title
    FROM processed_data pd
    JOIN articles a ON pd.article_id = a.id
    ORDER BY pd.id DESC
    LIMIT 5
""")
print("\nLatest processed articles:")
for row in cursor.fetchall():
    print(f"  Article {row[0]}: Category={row[1]}, Sentiment={row[2]:.2f}, Title={row[3][:50]}...")

conn.close()