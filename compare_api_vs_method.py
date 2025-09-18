#!/usr/bin/env python3
"""
Compare API response vs our method to find differences
"""
import requests
import sqlite3
import os

def compare_api_vs_method():
    print("🔍 COMPARING API RESPONSE VS OUR METHOD")
    print("="*60)
    
    # Test 1: Get API response
    print("Step 1: Getting API response...")
    try:
        response = requests.get('http://localhost:5001/api/articles')
        api_data = response.json()
        api_articles = api_data.get('articles', [])
        print(f"API returned {len(api_articles)} articles")
        
        if api_articles:
            print("API article IDs:", [art['id'] for art in api_articles[:5]])
            api_with_images = [art for art in api_articles if art.get('image')]
            print(f"API articles with images: {len(api_with_images)}")
    except Exception as e:
        print(f"❌ API failed: {e}")
        api_articles = []
    
    # Test 2: Get our method response
    print(f"\nStep 2: Getting our method response...")
    try:
        from src.utils.config import get_database_path
        db_path = get_database_path()
    except ImportError:
        db_path = "data/geopolitical_intel.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get hero first
    cursor.execute("""
        SELECT id, title FROM articles 
        WHERE geopolitical_relevance = 1 AND
        title IS NOT NULL AND title != '' AND
        (
            (content IS NOT NULL AND content != '') OR 
            (summary IS NOT NULL AND summary != '')
        ) AND
        (
            (original_image_url IS NOT NULL AND original_image_url != '') OR
            (image_url IS NOT NULL AND image_url != '' AND 
             image_url NOT LIKE '%placeholder%' AND 
             image_url NOT LIKE '%via.placeholder%' AND
             image_url NOT LIKE '%default%')
        ) AND
        (
            LOWER(title) NOT LIKE '%sport%' AND LOWER(title) NOT LIKE '%sports%' AND
            LOWER(title) NOT LIKE '%game%' AND LOWER(title) NOT LIKE '%games%'
        ) AND
        source NOT LIKE '%Yahoo Entertainment%' AND
        created_at >= datetime('now', '-30 days')
        ORDER BY 
        COALESCE(ai_importance, 0) DESC,
        COALESCE(risk_score, 0) DESC,
        created_at DESC
        LIMIT 1
    """)
    
    hero_result = cursor.fetchone()
    hero_id = hero_result[0] if hero_result else None
    print(f"Our method hero ID: {hero_id}")
    
    # Get regular articles excluding hero
    cursor.execute("""
        SELECT id, title,
        CASE 
            WHEN original_image_url IS NOT NULL AND original_image_url != '' AND original_image_url LIKE 'https://%'
            THEN original_image_url
            WHEN image_url IS NOT NULL AND image_url != '' AND image_url LIKE 'https://%' AND image_url NOT LIKE '%via.placeholder%' THEN 
                image_url
            ELSE 
                NULL
        END as image_url
        FROM articles 
        WHERE geopolitical_relevance = 1 AND
        title IS NOT NULL AND title != '' AND
        (
            (content IS NOT NULL AND content != '') OR 
            (summary IS NOT NULL AND summary != '')
        ) AND
        (
            (original_image_url IS NOT NULL AND original_image_url != '') OR
            (image_url IS NOT NULL AND image_url != '' AND 
             image_url NOT LIKE '%placeholder%' AND 
             image_url NOT LIKE '%via.placeholder%' AND
             image_url NOT LIKE '%default%')
        ) AND
        (
            LOWER(title) NOT LIKE '%sport%' AND LOWER(title) NOT LIKE '%sports%' AND
            LOWER(title) NOT LIKE '%game%' AND LOWER(title) NOT LIKE '%games%'
        ) AND
        source NOT LIKE '%Yahoo Entertainment%' AND
        id != ? AND
        created_at >= datetime('now', '-30 days')
        ORDER BY 
        COALESCE(ai_importance, 0) DESC,
        COALESCE(risk_score, 0) DESC,
        created_at DESC
        LIMIT 20
    """, (hero_id,))
    
    method_results = cursor.fetchall()
    conn.close()
    
    print(f"Our method returned {len(method_results)} articles")
    print("Our method article IDs:", [row[0] for row in method_results[:5]])
    method_with_images = [row for row in method_results if row[2]]
    print(f"Our method articles with images: {len(method_with_images)}")
    
    # Compare
    print(f"\n🔍 COMPARISON:")
    print(f"API articles count: {len(api_articles)}")
    print(f"Our method count: {len(method_results)}")
    
    if api_articles and method_results:
        api_ids = set(art['id'] for art in api_articles[:5])
        method_ids = set(row[0] for row in method_results[:5])
        
        print(f"Common IDs: {api_ids.intersection(method_ids)}")
        print(f"API-only IDs: {api_ids - method_ids}")
        print(f"Method-only IDs: {method_ids - api_ids}")

if __name__ == "__main__":
    compare_api_vs_method()