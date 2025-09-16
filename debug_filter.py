import sqlite3

conn = sqlite3.connect('data/geopolitical_intel.db')
cursor = conn.cursor()

# Check database schema
cursor.execute("PRAGMA table_info(articles)")
columns = cursor.fetchall()
print("Available columns in articles table:")
for col in columns:
    print(f"  - {col[1]} ({col[2]})")

print("\n" + "="*50)
print("CHECKING IMAGE COLUMNS")
print("="*50)

# Check image_url vs original_image_url
cursor.execute("SELECT COUNT(*) FROM articles WHERE image_url IS NOT NULL AND image_url != ''")
image_url_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM articles WHERE original_image_url IS NOT NULL AND original_image_url != ''")
original_image_url_count = cursor.fetchone()[0]

print(f"Articles with image_url: {image_url_count}")
print(f"Articles with original_image_url: {original_image_url_count}")

# Check samples of each
print("\nSample image_url values:")
cursor.execute("SELECT image_url FROM articles WHERE image_url IS NOT NULL AND image_url != '' LIMIT 3")
for row in cursor.fetchall():
    print(f"  {row[0]}")

print("\nSample original_image_url values:")
cursor.execute("SELECT original_image_url FROM articles WHERE original_image_url IS NOT NULL AND original_image_url != '' LIMIT 3")
for row in cursor.fetchall():
    print(f"  {row[0]}")

# Test what the current Flask filter actually finds
print("\n" + "="*50)
print("TESTING CURRENT FLASK FILTER")
print("="*50)

flask_filter = """
SELECT COUNT(*) FROM articles 
WHERE 
    original_image_url IS NOT NULL AND original_image_url != '' AND
    title IS NOT NULL AND title != '' AND
    content IS NOT NULL AND content != '' AND
    (content NOT LIKE '%HERO ARTICLE%' OR content IS NULL) AND
    (title NOT LIKE '%HERO%' OR title IS NULL) AND
    (
        LOWER(title || ' ' || COALESCE(content, '')) LIKE '%war%' OR
        LOWER(title || ' ' || COALESCE(content, '')) LIKE '%conflict%' OR
        LOWER(title || ' ' || COALESCE(content, '')) LIKE '%military%' OR
        LOWER(title || ' ' || COALESCE(content, '')) LIKE '%politics%'
    )
"""

cursor.execute(flask_filter)
flask_count = cursor.fetchone()[0]
print(f"Current Flask filter matches: {flask_count}")

# Test without original_image_url requirement
fixed_filter = """
SELECT COUNT(*) FROM articles 
WHERE 
    image_url IS NOT NULL AND image_url != '' AND
    title IS NOT NULL AND title != '' AND
    content IS NOT NULL AND content != '' AND
    (content NOT LIKE '%HERO ARTICLE%' OR content IS NULL) AND
    (title NOT LIKE '%HERO%' OR title IS NULL) AND
    (
        LOWER(title || ' ' || COALESCE(content, '')) LIKE '%war%' OR
        LOWER(title || ' ' || COALESCE(content, '')) LIKE '%conflict%' OR
        LOWER(title || ' ' || COALESCE(content, '')) LIKE '%military%' OR
        LOWER(title || ' ' || COALESCE(content, '')) LIKE '%politics%'
    )
"""

cursor.execute(fixed_filter)
fixed_count = cursor.fetchone()[0]
print(f"Fixed filter matches: {fixed_count}")

conn.close()