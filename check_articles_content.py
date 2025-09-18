#!/usr/bin/env python3
"""
Verificar el contenido de los artículos ingresados
"""

import sqlite3

def check_articles_content():
    """Verificar qué contenido tienen los artículos."""
    conn = sqlite3.connect('./data/geopolitical_intel.db')
    
    print("📊 ANÁLISIS DE CONTENIDO DE ARTÍCULOS")
    print("="*50)
    
    # Total articles
    total = conn.execute('SELECT COUNT(*) FROM articles').fetchone()[0]
    print(f"📰 Total artículos: {total}")
    
    # Articles with content
    with_content = conn.execute('SELECT COUNT(*) FROM articles WHERE content IS NOT NULL AND content != ""').fetchone()[0]
    print(f"📝 Con content: {with_content}")
    
    # Articles with summary
    with_summary = conn.execute('SELECT COUNT(*) FROM articles WHERE summary IS NOT NULL AND summary != ""').fetchone()[0]
    print(f"📋 Con summary: {with_summary}")
    
    # Articles with image_url
    with_image = conn.execute('SELECT COUNT(*) FROM articles WHERE image_url IS NOT NULL AND image_url != ""').fetchone()[0]
    print(f"🖼️  Con image_url: {with_image}")
    
    # Articles that pass the ultra-strict filter
    ultra_strict_query = """
        SELECT COUNT(*) FROM articles 
        WHERE 
            title IS NOT NULL AND title != '' AND
            content IS NOT NULL AND content != '' AND
            (
                (original_image_url IS NOT NULL AND original_image_url != '') OR
                (image_url IS NOT NULL AND image_url != '' AND 
                 image_url NOT LIKE '%placeholder%' AND 
                 image_url NOT LIKE '%via.placeholder%' AND
                 image_url NOT LIKE '%default%')
            )
    """
    ultra_strict = conn.execute(ultra_strict_query).fetchone()[0]
    print(f"🚨 Que pasan filtro ultra-estricto: {ultra_strict}")
    
    # Articles with geopolitical_relevance = 1
    geopolitical = conn.execute('SELECT COUNT(*) FROM articles WHERE geopolitical_relevance = 1').fetchone()[0]
    print(f"🌍 Marcados como geopolíticos: {geopolitical}")
    
    # Sample titles to check content
    print("\n📋 MUESTRA DE ARTÍCULOS:")
    print("-"*50)
    
    sample_query = """
        SELECT title, 
               CASE WHEN content IS NOT NULL AND content != '' THEN 'SÍ' ELSE 'NO' END as has_content,
               CASE WHEN summary IS NOT NULL AND summary != '' THEN 'SÍ' ELSE 'NO' END as has_summary,
               CASE WHEN image_url IS NOT NULL AND image_url != '' THEN 'SÍ' ELSE 'NO' END as has_image,
               geopolitical_relevance
        FROM articles 
        ORDER BY id 
        LIMIT 10
    """
    
    rows = conn.execute(sample_query).fetchall()
    for row in rows:
        title, has_content, has_summary, has_image, geo = row
        print(f"🔸 {title[:50]}...")
        print(f"   Content: {has_content} | Summary: {has_summary} | Image: {has_image} | Geo: {geo}")
        print()
    
    conn.close()

if __name__ == "__main__":
    check_articles_content()