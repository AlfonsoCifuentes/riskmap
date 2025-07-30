"""Initialize the database with all required tables."""

from src.utils.config import DatabaseManager, config

# Initialize database
db = DatabaseManager(config)

# This will create all tables if they don't exist
conn = db.get_connection()
conn.close()

print("Database initialized successfully!")

# Verify tables
import sqlite3
conn = sqlite3.connect('data/riskmap.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("\nTables created:")
for table in tables:
    print(f"  - {table[0]}")
conn.close()