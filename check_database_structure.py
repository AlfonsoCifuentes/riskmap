import sqlite3
import os

# Possible database paths
possible_paths = [
    'data/geopolitical_intel.db',
    'data/riskmap.db',
    'src/dashboard/data/geopolitical_intel.db',
    '../data/geopolitical_intel.db'
]

print("Checking for database files...")
db_path = None

for path in possible_paths:
    if os.path.exists(path):
        print(f"✓ Found database at: {path}")
        db_path = path
        break
    else:
        print(f"✗ Not found: {path}")

if not db_path:
    print("No database found! Please check the database location.")
    exit(1)

print(f"\nConnecting to database: {db_path}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables
print("\n" + "="*50)
print("TABLES IN DATABASE:")
print("="*50)
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

if not tables:
    print("No tables found in database!")
else:
    for table in tables:
        print(f"  - {table[0]}")

# Check each table structure
for table in tables:
    table_name = table[0]
    print(f"\n" + "-"*30)
    print(f"TABLE: {table_name}")
    print("-"*30)
    
    # Get table info
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    print("Columns:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'} {'PRIMARY KEY' if col[5] else ''}")
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"Row count: {count}")
    
    # Show sample data if exists
    if count > 0:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
        sample_rows = cursor.fetchall()
        print("Sample data:")
        for i, row in enumerate(sample_rows):
            print(f"  Row {i+1}: {dict(zip([col[1] for col in columns], row))}")

# Check for articles table specifically
print(f"\n" + "="*50)
print("ARTICLES TABLE ANALYSIS:")
print("="*50)

if ('articles',) in tables:
    # Check risk levels
    cursor.execute("SELECT risk_level, COUNT(*) FROM articles GROUP BY risk_level")
    risk_levels = cursor.fetchall()
    print("Risk levels distribution:")
    for level, count in risk_levels:
        print(f"  - {level}: {count}")
    
    # Check countries
    cursor.execute("SELECT country, COUNT(*) FROM articles WHERE country IS NOT NULL GROUP BY country ORDER BY COUNT(*) DESC LIMIT 10")
    countries = cursor.fetchall()
    print("\nTop 10 countries:")
    for country, count in countries:
        print(f"  - {country}: {count}")
    
    # Check recent articles
    cursor.execute("SELECT COUNT(*) FROM articles WHERE created_at > datetime('now', '-7 days')")
    recent_count = cursor.fetchone()[0]
    print(f"\nArticles from last 7 days: {recent_count}")
    
    # Check if there are any high risk articles
    cursor.execute("SELECT COUNT(*) FROM articles WHERE risk_level = 'high'")
    high_risk_count = cursor.fetchone()[0]
    print(f"High risk articles: {high_risk_count}")

conn.close()
print(f"\n" + "="*50)
print("DATABASE ANALYSIS COMPLETE")
print("="*50)