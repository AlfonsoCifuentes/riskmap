import sqlite3

# Check what's in our database
conn = sqlite3.connect('data/geopolitical_intel.db')
cursor = conn.cursor()

# Check total articles
cursor.execute("SELECT COUNT(*) FROM articles")
total = cursor.fetchone()[0]
print(f"Total articles in database: {total}")

# Check articles with images
cursor.execute("SELECT COUNT(*) FROM articles WHERE image_url IS NOT NULL AND image_url != ''")
with_images = cursor.fetchone()[0]
print(f"Articles with images: {with_images}")

# Check geopolitical keywords
keywords = ['war', 'conflict', 'military', 'politics', 'government', 'international', 'diplomacy', 'crisis']
geopolitical_count = 0

for keyword in keywords:
    cursor.execute(f"SELECT COUNT(*) FROM articles WHERE title LIKE '%{keyword}%' OR content LIKE '%{keyword}%'")
    count = cursor.fetchone()[0]
    if count > 0:
        geopolitical_count += count
        print(f"Articles with '{keyword}': {count}")

print(f"Total geopolitical matches: {geopolitical_count}")

# Check what our current filter should return
print("\n" + "="*50)
print("TESTING OUR FILTER LOGIC")
print("="*50)

# This should match our SQL filter from app_BUENA.py
filter_query = """
SELECT COUNT(*) FROM articles 
WHERE (
    -- Geopolitical content
    (
        title LIKE '%war%' OR title LIKE '%guerra%' OR title LIKE '%conflict%' OR title LIKE '%conflicto%' OR
        title LIKE '%military%' OR title LIKE '%militar%' OR title LIKE '%politics%' OR title LIKE '%política%' OR
        title LIKE '%government%' OR title LIKE '%gobierno%' OR title LIKE '%international%' OR title LIKE '%internacional%' OR
        title LIKE '%diplomacy%' OR title LIKE '%diplomacia%' OR title LIKE '%security%' OR title LIKE '%seguridad%' OR
        title LIKE '%defense%' OR title LIKE '%defensa%' OR title LIKE '%crisis%' OR 
        content LIKE '%war%' OR content LIKE '%guerra%' OR content LIKE '%conflict%' OR content LIKE '%conflicto%' OR
        content LIKE '%military%' OR content LIKE '%militar%' OR content LIKE '%politics%' OR content LIKE '%política%' OR
        content LIKE '%government%' OR content LIKE '%gobierno%' OR content LIKE '%international%' OR content LIKE '%internacional%' OR
        content LIKE '%diplomacy%' OR content LIKE '%diplomacia%' OR content LIKE '%security%' OR content LIKE '%seguridad%' OR
        content LIKE '%defense%' OR content LIKE '%defensa%' OR content LIKE '%crisis%'
    )
    AND 
    -- Must have real image
    (
        image_url IS NOT NULL AND 
        image_url != '' AND 
        image_url NOT LIKE '%placeholder%' AND 
        image_url NOT LIKE '%default%' AND 
        image_url NOT LIKE '/static/images/placeholder%'
    )
)
"""

cursor.execute(filter_query)
filtered_count = cursor.fetchone()[0]
print(f"Articles matching our filter: {filtered_count}")

# Get sample of filtered articles
sample_query = filter_query.replace("COUNT(*)", "title, image_url").replace("SELECT COUNT(*)", "SELECT title, image_url") + " LIMIT 5"
cursor.execute(sample_query)
samples = cursor.fetchall()

print("\nSample articles that should be returned:")
for i, (title, image_url) in enumerate(samples):
    print(f"{i+1}. {title[:60]}...")
    print(f"   Image: {image_url[:60]}...")

conn.close()