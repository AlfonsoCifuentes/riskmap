import sqlite3
from pathlib import Path

# Connect to database
db_path = Path('data/geopolitical_intel.db')
if not db_path.exists():
    print('Database not found')
    exit(1)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Check total articles
cursor.execute('SELECT COUNT(*) FROM articles')
total = cursor.fetchone()[0]
print(f'Total articles: {total}')

# Check high risk
cursor.execute('SELECT COUNT(*) FROM articles WHERE risk_level = "high"')
high_risk = cursor.fetchone()[0]
print(f'High risk articles: {high_risk}')

# Check today
cursor.execute('SELECT COUNT(*) FROM articles WHERE created_at > datetime("now", "-24 hours")')
today = cursor.fetchone()[0]
print(f'Articles last 24h: {today}')

# Check countries
cursor.execute('SELECT COUNT(DISTINCT country) FROM articles WHERE country IS NOT NULL')
countries = cursor.fetchone()[0]
print(f'Countries with articles: {countries}')

# Check recent articles
cursor.execute('SELECT title, country, risk_level, created_at FROM articles ORDER BY created_at DESC LIMIT 5')
recent = cursor.fetchall()
print('\nRecent articles:')
for article in recent:
    print(f'- {article[0][:50]}... | {article[1]} | {article[2]} | {article[3]}')

# Check date range
cursor.execute('SELECT MIN(created_at), MAX(created_at) FROM articles')
date_range = cursor.fetchone()
print(f'\nDate range: {date_range[0]} to {date_range[1]}')

conn.close()