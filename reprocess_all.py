import sqlite3

# Connect to database
conn = sqlite3.connect('data/geopolitical_intel.db')
cursor = conn.cursor()

# Clear ALL processed_data to start fresh with improved analyzer
cursor.execute("DELETE FROM processed_data")
deleted = cursor.rowcount

# Reset ALL risk_levels
cursor.execute("UPDATE articles SET risk_level = NULL")
updated = cursor.rowcount

conn.commit()
conn.close()

print(f"Cleared {deleted} processed entries")
print(f"Reset risk_level for {updated} articles")
print("Ready to reprocess ALL articles with improved NLP analyzer")