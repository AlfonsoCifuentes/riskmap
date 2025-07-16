#!/usr/bin/env python3
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('data/geopolitical_intel.db')
cursor = conn.cursor()

# Check table structure
cursor.execute('PRAGMA table_info(articles)')
print('Columns in articles table:')
for row in cursor.fetchall():
    print(f'  {row[1]} ({row[2]})')

# Check total articles
cursor.execute('SELECT COUNT(*) FROM articles')
total = cursor.fetchone()[0]
print(f'\nTotal articles: {total}')

# Check recent articles
cursor.execute('SELECT title, created_at, risk_level, conflict_type FROM articles ORDER BY created_at DESC LIMIT 5')
print('\nRecent articles:')
for row in cursor.fetchall():
    print(f"  {row[0][:50]}... | {row[1]} | Risk: {row[2]} | Type: {row[3]}")

conn.close()
