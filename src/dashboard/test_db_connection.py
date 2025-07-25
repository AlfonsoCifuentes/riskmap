import sqlite3
import os

# Test database connection
db_paths = [
    '../../data/geopolitical_intel.db',
    '../data/geopolitical_intel.db',
    'data/geopolitical_intel.db',
    '../../data/riskmap.db'
]

print("Testing database connections...")
print("Current directory:", os.getcwd())

for db_path in db_paths:
    print(f"\nTrying: {db_path}")
    if os.path.exists(db_path):
        print(f"✓ File exists")
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT COUNT(*) FROM articles")
            count = cursor.fetchone()[0]
            print(f"✓ Connection successful - {count} articles found")
            
            # Test recent articles
            cursor.execute("SELECT COUNT(*) FROM articles WHERE created_at > datetime('now', '-7 days')")
            recent = cursor.fetchone()[0]
            print(f"✓ Recent articles (7 days): {recent}")
            
            # Test high risk
            cursor.execute("SELECT COUNT(*) FROM articles WHERE risk_level = 'high'")
            high_risk = cursor.fetchone()[0]
            print(f"✓ High risk articles: {high_risk}")
            
            conn.close()
            print(f"✓ Using this database: {db_path}")
            break
            
        except Exception as e:
            print(f"✗ Connection failed: {e}")
    else:
        print(f"✗ File not found")

print("\nTest completed")