"""Initialize the complete database schema."""

import sqlite3
from pathlib import Path

# Create data directory if it doesn't exist
Path('data').mkdir(exist_ok=True)

# Connect to database
conn = sqlite3.connect('data/riskmap.db')
cursor = conn.cursor()

# Create articles table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT,
        url TEXT UNIQUE,
        source TEXT,
        published_at DATETIME,
        language TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        risk_level TEXT,
        country TEXT,
        region TEXT,
        summary TEXT,
        risk_score REAL,
        sentiment_score REAL,
        sentiment_label TEXT,
        conflict_type TEXT,
        key_persons TEXT,
        key_locations TEXT,
        entities_json TEXT,
        conflict_indicators TEXT,
        visual_risk_score REAL,
        detected_objects TEXT,
        visual_analysis_json TEXT,
        image_url TEXT,
        processed INTEGER DEFAULT 0,
        processing_time REAL,
        quality_score REAL,
        author TEXT,
        description TEXT,
        metadata TEXT
    )
''')

# Create processed_data table
cursor.execute('''
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
''')

# Create indices
cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON articles(created_at)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_published_at ON articles(published_at)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_language ON articles(language)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_risk_level ON articles(risk_level)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_processed_article_id ON processed_data(article_id)')

# Commit changes
conn.commit()

# Verify tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Database initialized successfully!")
print("\nTables created:")
for table in tables:
    print(f"  - {table[0]}")

# Show table schemas
for table_name in ['articles', 'processed_data']:
    print(f"\nSchema for {table_name}:")
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")

conn.close()