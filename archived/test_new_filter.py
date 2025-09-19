#!/usr/bin/env python3
"""Test del nuevo filtro permisivo"""
import sqlite3
import os

def test_new_filter():
    print("🔍 TESTING NUEVO FILTRO PERMISIVO...")
    
    db_path = "./data/geopolitical_intel.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Probar el nuevo filtro permisivo
    cursor.execute("""
        SELECT COUNT(*) FROM articles 
        WHERE (is_excluded IS NULL OR is_excluded != 1)
        AND (image_url IS NOT NULL AND image_url != '' 
             AND image_url NOT LIKE 'data:image%')
        AND (language = 'es' OR 
             (is_translated = 1 AND original_language IS NOT NULL))
        AND (title NOT LIKE '%meteor%' 
             AND title NOT LIKE '%asteroid%'
             AND title NOT LIKE '%space%'
             AND title NOT LIKE '%sports%'
             AND title NOT LIKE '%deporte%'
             AND title NOT LIKE '%football%'
             AND title NOT LIKE '%soccer%'
             AND title NOT LIKE '%tennis%'
             AND title NOT LIKE '%basketball%'
             AND title NOT LIKE '%olympic%'
             AND title NOT LIKE '%celebrity%'
             AND title NOT LIKE '%entertainment%')
    """)
    new_filter_count = cursor.fetchone()[0]
    print(f"✅ Artículos que pasan el NUEVO filtro permisivo: {new_filter_count}")
    
    # Mostrar algunos ejemplos
    cursor.execute("""
        SELECT id, title, image_url, language, risk_level
        FROM articles 
        WHERE (is_excluded IS NULL OR is_excluded != 1)
        AND (image_url IS NOT NULL AND image_url != '' 
             AND image_url NOT LIKE 'data:image%')
        AND (language = 'es' OR 
             (is_translated = 1 AND original_language IS NOT NULL))
        AND (title NOT LIKE '%meteor%' 
             AND title NOT LIKE '%asteroid%'
             AND title NOT LIKE '%space%'
             AND title NOT LIKE '%sports%'
             AND title NOT LIKE '%deporte%'
             AND title NOT LIKE '%football%'
             AND title NOT LIKE '%soccer%'
             AND title NOT LIKE '%tennis%'
             AND title NOT LIKE '%basketball%'
             AND title NOT LIKE '%olympic%'
             AND title NOT LIKE '%celebrity%'
             AND title NOT LIKE '%entertainment%')
        ORDER BY CASE 
            WHEN risk_level = 'high' THEN 1
            WHEN risk_level = 'medium' THEN 2
            WHEN risk_level = 'low' THEN 3
            ELSE 4
        END, published_at DESC
        LIMIT 10
    """)
    examples = cursor.fetchall()
    
    print(f"\n📰 Artículos disponibles para el mosaico:")
    for article in examples:
        risk_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(article[4], "⚪")
        print(f"   {risk_emoji} ID {article[0]}: {article[1][:60]}...")
        print(f"      🖼️  {article[2][:80]}...")
        print(f"      🌍 {article[3]} | Risk: {article[4]}")
        print()
    
    conn.close()
    
    if new_filter_count >= 5:
        print(f"🎯 ✅ ÉXITO: {new_filter_count} artículos disponibles para el mosaico")
        print("   El endpoint /api/articles ahora debería funcionar!")
    else:
        print(f"🎯 ⚠️  ADVERTENCIA: Solo {new_filter_count} artículos disponibles")

if __name__ == "__main__":
    test_new_filter()