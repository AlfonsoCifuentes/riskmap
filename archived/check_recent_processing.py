import sqlite3
import json

# Connect to database
conn = sqlite3.connect('data/geopolitical_intel.db')
cursor = conn.cursor()

# Check recently processed articles (those with categories other than 'unknown')
cursor.execute("""
    SELECT pd.*, a.title, a.content
    FROM processed_data pd
    JOIN articles a ON pd.article_id = a.id
    WHERE pd.category != 'unknown'
    ORDER BY pd.id DESC
    LIMIT 10
""")

columns = [desc[0] for desc in cursor.description]
print("Recently processed articles with real analysis:")
print("=" * 60)

for row in cursor.fetchall():
    data = dict(zip(columns, row))
    print(f"\nArticle ID: {data['article_id']}")
    print(f"Title: {data['title'][:60]}...")
    print(f"Category: {data['category']}")
    print(f"Sentiment: {data['sentiment']}")
    
    # Check entities
    if data['entities']:
        try:
            entities = json.loads(data['entities'])
            if entities.get('GPE') or entities.get('ORG'):
                print(f"Countries: {', '.join(entities.get('GPE', []))}")
                print(f"Organizations: {', '.join(entities.get('ORG', []))}")
        except:
            pass
    
    # Check keywords
    if data['keywords']:
        try:
            keywords = json.loads(data['keywords'])
            if keywords:
                print(f"Keywords: {', '.join(keywords[:5])}")
        except:
            pass
    
    print("-" * 60)

# Show category distribution for recent processing
cursor.execute("""
    SELECT category, COUNT(*) 
    FROM processed_data 
    WHERE id > (SELECT MAX(id) - 20 FROM processed_data)
    GROUP BY category
""")
print("\nCategory distribution for last 20 processed:")
for cat, count in cursor.fetchall():
    print(f"  {cat}: {count}")

conn.close()