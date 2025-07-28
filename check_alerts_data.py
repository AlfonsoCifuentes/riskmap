import sqlite3
import json
from pathlib import Path

conn = sqlite3.connect('data/geopolitical_intel.db')
cursor = conn.cursor()

print('--- Recent high-risk articles with entities ---')
cursor.execute('''
    SELECT a.title, a.country, a.created_at, a.entities_json, a.key_persons, a.key_locations, pd.entities
    FROM articles a
    LEFT JOIN processed_data pd ON a.id = pd.article_id
    WHERE a.risk_level = 'high'
    AND a.created_at > datetime('now', '-48 hours')
    ORDER BY a.created_at DESC
    LIMIT 10
''')
articles = cursor.fetchall()

for i, article in enumerate(articles):
    print(f'\n=== ARTICLE {i+1} ===')
    title = article[0][:120] if article[0] else 'No title'
    country = article[1] if article[1] else 'Unknown'
    print(f'Title: {title}')
    print(f'Country: {country}')
    print(f'Date: {article[2]}')
    
    # Try to parse entities
    entities_found = False
    if article[3]:  # entities_json
        try:
            entities = json.loads(article[3])
            if entities:
                print(f'Entities (JSON): {entities}')
                entities_found = True
        except:
            pass
    
    if article[4]:  # key_persons
        print(f'Key Persons: {article[4]}')
        entities_found = True
    
    if article[5]:  # key_locations
        print(f'Key Locations: {article[5]}')
        entities_found = True
    
    if article[6]:  # processed_data entities
        content = article[6][:200] if article[6] and len(article[6]) > 200 else article[6]
        print(f'Processed Entities: {content}')
        entities_found = True
    
    if not entities_found:
        print('No entities found')

print('\n--- Countries with recent high-risk events ---')
cursor.execute('''
    SELECT country, COUNT(*) as count, MAX(created_at) as latest
    FROM articles
    WHERE risk_level = 'high'
    AND created_at > datetime('now', '-7 days')
    AND country IS NOT NULL
    GROUP BY country
    ORDER BY count DESC
''')
countries = cursor.fetchall()
for country in countries:
    print(f'{country[0]}: {country[1]} events, latest: {country[2]}')

print('\n--- Sample content for context ---')
cursor.execute('''
    SELECT title, content, country
    FROM articles
    WHERE risk_level = 'high'
    AND created_at > datetime('now', '-24 hours')
    AND content IS NOT NULL
    ORDER BY created_at DESC
    LIMIT 3
''')
content_samples = cursor.fetchall()
for sample in content_samples:
    print(f'\nTitle: {sample[0][:100]}')
    print(f'Country: {sample[2]}')
    print(f'Content: {sample[1][:300]}...')

conn.close()