#!/usr/bin/env python3
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('data/geopolitical_intel.db')
cursor = conn.cursor()

print("🔍 DEBUGGING WHY ARTICLES WITH IMAGES AREN'T RETURNED")
print("="*60)

# Test the full query step by step
print("Step 1: Basic geopolitical + images")
cursor.execute("""
    SELECT COUNT(*) FROM articles 
    WHERE geopolitical_relevance = 1 AND 
    (
        (original_image_url IS NOT NULL AND original_image_url != '' AND original_image_url LIKE 'https://%') OR
        (image_url IS NOT NULL AND image_url != '' AND 
         image_url LIKE 'https://%' AND 
         image_url NOT LIKE '%placeholder%' AND 
         image_url NOT LIKE '%via.placeholder%' AND
         image_url NOT LIKE '%default%')
    )
""")
count1 = cursor.fetchone()[0]
print(f"Geopolitical + valid images: {count1}")

print("\nStep 2: + Title and content/summary requirements")
cursor.execute("""
    SELECT COUNT(*) FROM articles 
    WHERE geopolitical_relevance = 1 AND 
    title IS NOT NULL AND title != '' AND
    (
        (content IS NOT NULL AND content != '') OR 
        (summary IS NOT NULL AND summary != '')
    ) AND
    (
        (original_image_url IS NOT NULL AND original_image_url != '' AND original_image_url LIKE 'https://%') OR
        (image_url IS NOT NULL AND image_url != '' AND 
         image_url LIKE 'https://%' AND 
         image_url NOT LIKE '%placeholder%' AND 
         image_url NOT LIKE '%via.placeholder%' AND
         image_url NOT LIKE '%default%')
    )
""")
count2 = cursor.fetchone()[0]
print(f"+ title/content requirements: {count2}")

print("\nStep 3: + Exclusion filters")
cursor.execute("""
    SELECT COUNT(*) FROM articles 
    WHERE geopolitical_relevance = 1 AND 
    title IS NOT NULL AND title != '' AND
    (
        (content IS NOT NULL AND content != '') OR 
        (summary IS NOT NULL AND summary != '')
    ) AND
    (
        (original_image_url IS NOT NULL AND original_image_url != '' AND original_image_url LIKE 'https://%') OR
        (image_url IS NOT NULL AND image_url != '' AND 
         image_url LIKE 'https://%' AND 
         image_url NOT LIKE '%placeholder%' AND 
         image_url NOT LIKE '%via.placeholder%' AND
         image_url NOT LIKE '%default%')
    ) AND
    (
        LOWER(title) NOT LIKE '%sport%' AND LOWER(title) NOT LIKE '%sports%' AND
        LOWER(title) NOT LIKE '%game%' AND LOWER(title) NOT LIKE '%games%' AND
        LOWER(title) NOT LIKE '%football%' AND LOWER(title) NOT LIKE '%soccer%' AND
        LOWER(title) NOT LIKE '%basketball%' AND LOWER(title) NOT LIKE '%baseball%' AND
        LOWER(title) NOT LIKE '%emmy%' AND LOWER(title) NOT LIKE '%oscar%' AND
        LOWER(title) NOT LIKE '%movie%' AND LOWER(title) NOT LIKE '%actor%' AND
        LOWER(title) NOT LIKE '%hollywood%' AND LOWER(title) NOT LIKE '%singer%' AND
        LOWER(title) NOT LIKE '%music%' AND LOWER(title) NOT LIKE '%celebrity%' AND
        LOWER(title) NOT LIKE '%netflix%' AND
        LOWER(title) NOT LIKE '%iphone%' AND LOWER(title) NOT LIKE '%nintendo%' AND
        LOWER(title) NOT LIKE '%deporte%' AND LOWER(title) NOT LIKE '%deportes%' AND
        LOWER(title) NOT LIKE '%fútbol%' AND LOWER(title) NOT LIKE '%música%'
    ) AND
    source NOT LIKE '%Yahoo Entertainment%'
""")
count3 = cursor.fetchone()[0]
print(f"+ exclusion filters: {count3}")

print("\nStep 4: + Date filter (last 30 days)")
cursor.execute("""
    SELECT COUNT(*) FROM articles 
    WHERE geopolitical_relevance = 1 AND 
    title IS NOT NULL AND title != '' AND
    (
        (content IS NOT NULL AND content != '') OR 
        (summary IS NOT NULL AND summary != '')
    ) AND
    (
        (original_image_url IS NOT NULL AND original_image_url != '' AND original_image_url LIKE 'https://%') OR
        (image_url IS NOT NULL AND image_url != '' AND 
         image_url LIKE 'https://%' AND 
         image_url NOT LIKE '%placeholder%' AND 
         image_url NOT LIKE '%via.placeholder%' AND
         image_url NOT LIKE '%default%')
    ) AND
    (
        LOWER(title) NOT LIKE '%sport%' AND LOWER(title) NOT LIKE '%sports%' AND
        LOWER(title) NOT LIKE '%game%' AND LOWER(title) NOT LIKE '%games%' AND
        LOWER(title) NOT LIKE '%football%' AND LOWER(title) NOT LIKE '%soccer%' AND
        LOWER(title) NOT LIKE '%basketball%' AND LOWER(title) NOT LIKE '%baseball%' AND
        LOWER(title) NOT LIKE '%emmy%' AND LOWER(title) NOT LIKE '%oscar%' AND
        LOWER(title) NOT LIKE '%movie%' AND LOWER(title) NOT LIKE '%actor%' AND
        LOWER(title) NOT LIKE '%hollywood%' AND LOWER(title) NOT LIKE '%singer%' AND
        LOWER(title) NOT LIKE '%music%' AND LOWER(title) NOT LIKE '%celebrity%' AND
        LOWER(title) NOT LIKE '%netflix%' AND
        LOWER(title) NOT LIKE '%iphone%' AND LOWER(title) NOT LIKE '%nintendo%' AND
        LOWER(title) NOT LIKE '%deporte%' AND LOWER(title) NOT LIKE '%deportes%' AND
        LOWER(title) NOT LIKE '%fútbol%' AND LOWER(title) NOT LIKE '%música%'
    ) AND
    source NOT LIKE '%Yahoo Entertainment%' AND
    created_at >= datetime('now', '-30 days')
""")
count4 = cursor.fetchone()[0]
print(f"+ date filter (30 days): {count4}")

if count4 == 0:
    print("\n🔍 CHECKING DATE RANGE:")
    cursor.execute("SELECT MIN(created_at), MAX(created_at) FROM articles WHERE geopolitical_relevance = 1")
    min_date, max_date = cursor.fetchone()
    print(f"Date range of geopolitical articles: {min_date} to {max_date}")
    
    # Try with 90 days
    cursor.execute("""
        SELECT COUNT(*) FROM articles 
        WHERE geopolitical_relevance = 1 AND 
        title IS NOT NULL AND title != '' AND
        (
            (content IS NOT NULL AND content != '') OR 
            (summary IS NOT NULL AND summary != '')
        ) AND
        (
            (original_image_url IS NOT NULL AND original_image_url != '' AND original_image_url LIKE 'https://%') OR
            (image_url IS NOT NULL AND image_url != '' AND 
             image_url LIKE 'https://%' AND 
             image_url NOT LIKE '%placeholder%' AND 
             image_url NOT LIKE '%via.placeholder%' AND
             image_url NOT LIKE '%default%')
        ) AND
        (
            LOWER(title) NOT LIKE '%sport%' AND LOWER(title) NOT LIKE '%sports%' AND
            LOWER(title) NOT LIKE '%game%' AND LOWER(title) NOT LIKE '%games%' AND
            LOWER(title) NOT LIKE '%football%' AND LOWER(title) NOT LIKE '%soccer%' AND
            LOWER(title) NOT LIKE '%basketball%' AND LOWER(title) NOT LIKE '%baseball%' AND
            LOWER(title) NOT LIKE '%emmy%' AND LOWER(title) NOT LIKE '%oscar%' AND
            LOWER(title) NOT LIKE '%movie%' AND LOWER(title) NOT LIKE '%actor%' AND
            LOWER(title) NOT LIKE '%hollywood%' AND LOWER(title) NOT LIKE '%singer%' AND
            LOWER(title) NOT LIKE '%music%' AND LOWER(title) NOT LIKE '%celebrity%' AND
            LOWER(title) NOT LIKE '%netflix%' AND
            LOWER(title) NOT LIKE '%iphone%' AND LOWER(title) NOT LIKE '%nintendo%' AND
            LOWER(title) NOT LIKE '%deporte%' AND LOWER(title) NOT LIKE '%deportes%' AND
            LOWER(title) NOT LIKE '%fútbol%' AND LOWER(title) NOT LIKE '%música%'
        ) AND
        source NOT LIKE '%Yahoo Entertainment%' AND
        created_at >= datetime('now', '-90 days')
    """)
    count90 = cursor.fetchone()[0]
    print(f"With 90-day filter: {count90}")

# Show some examples with their dates
print(f"\n🔍 SAMPLE ARTICLES WITH IMAGES (showing dates):")
print("="*60)

cursor.execute("""
    SELECT id, title, created_at,
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
    ORDER BY created_at DESC
    LIMIT 5
""")

results = cursor.fetchall()
for i, (article_id, title, created_at, image_url) in enumerate(results, 1):
    print(f"{i}. ID {article_id}: {title[:50]}...")
    print(f"   Date: {created_at}")
    print(f"   Image: {image_url[:60]}...")
    print()

conn.close()