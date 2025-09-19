#!/usr/bin/env python3
"""Debug del filtro HERO para ver qué está pasando"""
import sqlite3
import os

def debug_hero_filter():
    print("🔍 DEBUG DEL FILTRO HERO...")
    
    db_path = "./data/geopolitical_intel.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Verificar total de artículos con filtro básico
    cursor.execute("""
        SELECT COUNT(*) FROM articles 
        WHERE (is_excluded IS NULL OR is_excluded != 1)
        AND (image_url IS NOT NULL AND image_url != '' 
             AND image_url NOT LIKE 'data:image%')
        AND (language = 'es' OR 
             (is_translated = 1 AND original_language IS NOT NULL))
    """)
    basic_count = cursor.fetchone()[0]
    print(f"✅ Artículos con filtro básico: {basic_count}")
    
    # 2. Simular get_top_articles_from_db para héroe (limit=1)
    cursor.execute("""
        SELECT id FROM articles 
        WHERE (is_excluded IS NULL OR is_excluded != 1)
        AND (image_url IS NOT NULL AND image_url != '' 
             AND image_url NOT LIKE 'data:image%')
        AND (language = 'es' OR 
             (is_translated = 1 AND original_language IS NOT NULL))
        ORDER BY CASE 
            WHEN risk_level = 'high' THEN 1
            WHEN risk_level = 'medium' THEN 2
            WHEN risk_level = 'low' THEN 3
            ELSE 4
        END, published_at DESC
        LIMIT 1
    """)
    hero_result = cursor.fetchone()
    hero_id = hero_result[0] if hero_result else None
    print(f"🎯 Hero ID encontrado: {hero_id}")
    
    # 3. Simular filtro del mosaico (excluyendo hero)
    if hero_id:
        cursor.execute(f"""
            SELECT COUNT(*) FROM articles 
            WHERE (is_excluded IS NULL OR is_excluded != 1)
            AND (image_url IS NOT NULL AND image_url != '' 
                 AND image_url NOT LIKE 'data:image%')
            AND (language = 'es' OR 
                 (is_translated = 1 AND original_language IS NOT NULL))
            AND id != {hero_id}
        """)
        mosaic_count = cursor.fetchone()[0]
        print(f"📰 Artículos para mosaico (sin héroe {hero_id}): {mosaic_count}")
        
        # 4. Mostrar detalles del artículo héroe
        cursor.execute(f"SELECT id, title, risk_level, language FROM articles WHERE id = {hero_id}")
        hero_details = cursor.fetchone()
        print(f"\n🎯 DETALLES DEL HÉROE:")
        print(f"   ID: {hero_details[0]}")
        print(f"   Título: {hero_details[1][:60]}...")
        print(f"   Riesgo: {hero_details[2]}")
        print(f"   Idioma: {hero_details[3]}")
        
        # 5. Mostrar artículos disponibles para mosaico
        cursor.execute(f"""
            SELECT id, title, risk_level FROM articles 
            WHERE (is_excluded IS NULL OR is_excluded != 1)
            AND (image_url IS NOT NULL AND image_url != '' 
                 AND image_url NOT LIKE 'data:image%')
            AND (language = 'es' OR 
                 (is_translated = 1 AND original_language IS NOT NULL))
            AND id != {hero_id}
            LIMIT 5
        """)
        mosaic_articles = cursor.fetchall()
        
        if mosaic_articles:
            print(f"\n📰 ARTÍCULOS DISPONIBLES PARA MOSAICO:")
            for article in mosaic_articles:
                print(f"   ID {article[0]}: {article[1][:50]}... | Riesgo: {article[2]}")
        else:
            print(f"\n❌ PROBLEMA: NO HAY ARTÍCULOS PARA MOSAICO después de excluir héroe")
    else:
        print("❌ No se encontró artículo HERO")
    
    conn.close()
    
    if basic_count >= 5 and (not hero_id or mosaic_count >= 1):
        print(f"\n🎯 ✅ DIAGNÓSTICO: Deberían haber artículos disponibles")
    else:
        print(f"\n🎯 ❌ PROBLEMA: La lógica del héroe está eliminando todos los artículos del mosaico")

if __name__ == "__main__":
    debug_hero_filter()