#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('data/geopolitical_intel.db')
cursor = conn.cursor()

# Check articles with images
print("🔍 ANALYZING IMAGE AVAILABILITY IN GEOPOLITICAL ARTICLES")
print("="*60)

# 1. Total geopolitical articles
cursor.execute("SELECT COUNT(*) FROM articles WHERE geopolitical_relevance = 1")
total_geo = cursor.fetchone()[0]
print(f"Total geopolitical articles: {total_geo}")

# 2. With original_image_url
cursor.execute("""
    SELECT COUNT(*) FROM articles 
    WHERE geopolitical_relevance = 1 AND 
    original_image_url IS NOT NULL AND original_image_url != '' AND original_image_url LIKE 'https://%'
""")
with_original = cursor.fetchone()[0]
print(f"With original_image_url: {with_original}")

# 3. With image_url (not placeholder)
cursor.execute("""
    SELECT COUNT(*) FROM articles 
    WHERE geopolitical_relevance = 1 AND 
    image_url IS NOT NULL AND image_url != '' AND 
    image_url LIKE 'https://%' AND 
    image_url NOT LIKE '%placeholder%' AND 
    image_url NOT LIKE '%via.placeholder%'
""")
with_image = cursor.fetchone()[0]
print(f"With valid image_url: {with_image}")

# 4. With any image (original OR image_url)
cursor.execute("""
    SELECT COUNT(*) FROM articles 
    WHERE geopolitical_relevance = 1 AND 
    (
        (original_image_url IS NOT NULL AND original_image_url != '' AND original_image_url LIKE 'https://%') OR
        (image_url IS NOT NULL AND image_url != '' AND 
         image_url LIKE 'https://%' AND 
         image_url NOT LIKE '%placeholder%' AND 
         image_url NOT LIKE '%via.placeholder%')
    )
""")
with_any_image = cursor.fetchone()[0]
print(f"With any valid image: {with_any_image}")

print("\n🔍 SAMPLE ARTICLES WITH IMAGES:")
print("="*60)

# Show a few examples
cursor.execute("""
    SELECT id, title, 
    CASE 
        WHEN original_image_url IS NOT NULL AND original_image_url != '' AND original_image_url LIKE 'https://%'
        THEN original_image_url
        ELSE image_url
    END as final_image
    FROM articles 
    WHERE geopolitical_relevance = 1 AND 
    (
        (original_image_url IS NOT NULL AND original_image_url != '' AND original_image_url LIKE 'https://%') OR
        (image_url IS NOT NULL AND image_url != '' AND 
         image_url LIKE 'https://%' AND 
         image_url NOT LIKE '%placeholder%' AND 
         image_url NOT LIKE '%via.placeholder%')
    )
    LIMIT 5
""")

results = cursor.fetchall()
if results:
    for i, (article_id, title, image_url) in enumerate(results, 1):
        print(f"{i}. ID {article_id}: {title[:50]}...")
        print(f"   Image: {image_url[:80]}...")
        print()
else:
    print("❌ No articles with images found!")

conn.close()