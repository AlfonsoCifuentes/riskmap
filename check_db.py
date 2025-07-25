import sqlite3

conn = sqlite3.connect('data/riskmap.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables in database:")
for table in tables:
    print(f"  - {table[0]}")

# Check if processed_data table exists
if ('processed_data',) not in tables:
    print("\nTable 'processed_data' does not exist. Creating it...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            category TEXT,
            sentiment REAL,
            entities TEXT,
            summary TEXT,
            keywords TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (article_id) REFERENCES articles (id)
        )
    """)
    conn.commit()
    print("Table 'processed_data' created successfully.")

conn.close()