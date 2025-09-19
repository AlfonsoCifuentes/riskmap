#!/usr/bin/env python3
"""
Test filtros paso a paso
"""

import sqlite3

def test_filters():
    """Test each filter step by step."""
    conn = sqlite3.connect('./data/geopolitical_intel.db')
    
    print("🔍 ANÁLISIS DE FILTROS PASO A PASO")
    print("="*60)
    
    # Total articles
    total = conn.execute('SELECT COUNT(*) FROM articles').fetchone()[0]
    print(f"📰 Total articles: {total}")
    
    # Articles with geopolitical_relevance = 1
    geo_relevant = conn.execute('SELECT COUNT(*) FROM articles WHERE geopolitical_relevance = 1').fetchone()[0]
    print(f"🌍 With geopolitical_relevance = 1: {geo_relevant}")
    
    # Articles with title
    with_title = conn.execute('SELECT COUNT(*) FROM articles WHERE geopolitical_relevance = 1 AND title IS NOT NULL AND title != ""').fetchone()[0]
    print(f"📋 With title: {with_title}")
    
    # Articles with content OR summary
    with_content = conn.execute('''SELECT COUNT(*) FROM articles 
        WHERE geopolitical_relevance = 1 
        AND title IS NOT NULL AND title != "" 
        AND ((content IS NOT NULL AND content != "") OR (summary IS NOT NULL AND summary != ""))
    ''').fetchone()[0]
    print(f"📝 With content OR summary: {with_content}")
    
    # Articles with image
    with_image = conn.execute('''SELECT COUNT(*) FROM articles 
        WHERE geopolitical_relevance = 1 
        AND title IS NOT NULL AND title != "" 
        AND ((content IS NOT NULL AND content != "") OR (summary IS NOT NULL AND summary != ""))
        AND (
            (original_image_url IS NOT NULL AND original_image_url != "") OR
            (image_url IS NOT NULL AND image_url != "" AND 
             image_url NOT LIKE "%placeholder%" AND 
             image_url NOT LIKE "%via.placeholder%" AND
             image_url NOT LIKE "%default%")
        )
    ''').fetchone()[0]
    print(f"🖼️  With image: {with_image}")
    
    # Articles that pass basic keyword filters (simplified version)
    with_basic_keywords = conn.execute('''SELECT COUNT(*) FROM articles 
        WHERE geopolitical_relevance = 1 
        AND title IS NOT NULL AND title != "" 
        AND ((content IS NOT NULL AND content != "") OR (summary IS NOT NULL AND summary != ""))
        AND (
            (original_image_url IS NOT NULL AND original_image_url != "") OR
            (image_url IS NOT NULL AND image_url != "" AND 
             image_url NOT LIKE "%placeholder%" AND 
             image_url NOT LIKE "%via.placeholder%" AND
             image_url NOT LIKE "%default%")
        ) AND (
            LOWER(title) LIKE "%war%" OR LOWER(title) LIKE "%conflict%" OR
            LOWER(title) LIKE "%military%" OR LOWER(title) LIKE "%politics%" OR
            LOWER(title) LIKE "%government%" OR LOWER(title) LIKE "%security%" OR
            LOWER(title) LIKE "%diplomacy%" OR LOWER(title) LIKE "%election%" OR
            LOWER(title) LIKE "%russia%" OR LOWER(title) LIKE "%ukraine%" OR
            LOWER(title) LIKE "%china%" OR LOWER(title) LIKE "%israel%" OR
            LOWER(title) LIKE "%international%" OR LOWER(title) LIKE "%crisis%"
        )
    ''').fetchone()[0]
    print(f"🎯 With basic geopolitical keywords: {with_basic_keywords}")
    
    # Sample titles that pass all basic filters
    print("\n📋 SAMPLE TITLES PASSING BASIC FILTERS:")
    print("-"*60)
    
    sample_query = '''SELECT title, region, risk_level 
        FROM articles 
        WHERE geopolitical_relevance = 1 
        AND title IS NOT NULL AND title != "" 
        AND ((content IS NOT NULL AND content != "") OR (summary IS NOT NULL AND summary != ""))
        AND (
            (original_image_url IS NOT NULL AND original_image_url != "") OR
            (image_url IS NOT NULL AND image_url != "" AND 
             image_url NOT LIKE "%placeholder%" AND 
             image_url NOT LIKE "%via.placeholder%" AND
             image_url NOT LIKE "%default%")
        )
        ORDER BY id DESC
        LIMIT 10
    '''
    
    rows = conn.execute(sample_query).fetchall()
    for i, (title, region, risk) in enumerate(rows, 1):
        print(f"{i:2}. {title[:55]}...")
        print(f"    Region: {region or 'Unknown'} | Risk: {risk or 'unknown'}")
        print()
    
    conn.close()

if __name__ == "__main__":
    test_filters()