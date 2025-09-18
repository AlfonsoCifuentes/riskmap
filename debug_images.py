#!/usr/bin/env python3
"""
Debug imagen URLs
"""

import sqlite3

def debug_images():
    """Debug image URL filtering."""
    conn = sqlite3.connect('./data/geopolitical_intel.db')
    
    print("🖼️  DEBUG IMAGE URL FILTERING")
    print("="*60)
    
    # Articles with image_url by geopolitical_relevance
    with_geo = conn.execute('SELECT COUNT(*) FROM articles WHERE geopolitical_relevance = 1 AND image_url IS NOT NULL AND image_url != ""').fetchone()[0]
    print(f"📸 Geopolitical articles with image_url: {with_geo}")
    
    # Articles that pass strict image filter
    strict_image = conn.execute('''SELECT COUNT(*) FROM articles 
        WHERE geopolitical_relevance = 1 
        AND (
            (original_image_url IS NOT NULL AND original_image_url != '' AND original_image_url LIKE 'https://%') OR
            (image_url IS NOT NULL AND image_url != '' AND image_url LIKE 'https://%' AND image_url NOT LIKE '%via.placeholder%')
        )
    ''').fetchone()[0]
    print(f"🔒 That pass strict image filter: {strict_image}")
    
    # Sample image URLs from geopolitical articles  
    print("\n📋 SAMPLE IMAGE URLs:")
    print("-"*60)
    
    sample_query = '''SELECT title, image_url,
        CASE 
            WHEN original_image_url IS NOT NULL AND original_image_url != '' AND original_image_url LIKE 'https://%'
            THEN 'original_image_url: PASS'
            WHEN image_url IS NOT NULL AND image_url != '' AND image_url LIKE 'https://%' AND image_url NOT LIKE '%via.placeholder%'
            THEN 'image_url: PASS'
            ELSE 'FILTERED OUT'
        END as filter_result
        FROM articles 
        WHERE geopolitical_relevance = 1 
        AND image_url IS NOT NULL 
        AND image_url != ""
        ORDER BY id DESC
        LIMIT 10
    '''
    
    rows = conn.execute(sample_query).fetchall()
    for i, (title, image_url, filter_result) in enumerate(rows, 1):
        print(f"{i:2}. {title[:45]}...")
        print(f"    Image: {image_url[:70]}...")
        print(f"    Filter: {filter_result}")
        print()
    
    conn.close()

if __name__ == "__main__":
    debug_images()