import sqlite3

# Connect to the correct database
conn = sqlite3.connect('data/geopolitical_intel.db')
cursor = conn.cursor()

# Check current schema
cursor.execute("PRAGMA table_info(processed_data)")
columns = cursor.fetchall()
print("Current columns in processed_data:")
for col in columns:
    print(f"  - {col[1]} ({col[2]})")

# Add keywords column if it doesn't exist
column_names = [col[1] for col in columns]
if 'keywords' not in column_names:
    cursor.execute("ALTER TABLE processed_data ADD COLUMN keywords TEXT")
    conn.commit()
    print("\nAdded 'keywords' column to processed_data table")
else:
    print("\n'keywords' column already exists")

conn.close()