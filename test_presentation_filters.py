#!/usr/bin/env python3
"""
Script de prueba rápida para verificar filtros ultra estrictos.
Solo muestra artículos con imágenes de fuentes originales de noticias.
"""

import sqlite3
import os

def test_ultra_strict_filters():
    """Probar filtros ultra estrictos para presentación"""
    
    db_path = 'data/geopolitical_intel.db'
    if not os.path.exists(db_path):
        print("❌ Base de datos no encontrada")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # FILTROS ULTRA ESTRICTOS: igual que en la app
    base_filters = """
        WHERE (is_excluded IS NULL OR is_excluded != 1)
        AND (image_url IS NOT NULL AND image_url != '' 
             AND image_url NOT LIKE '%placeholder%'
             AND image_url NOT LIKE '%default%'
             AND image_url NOT LIKE '%noimage%'
             AND image_url NOT LIKE '%unsplash.com%'
             AND image_url NOT LIKE '%pexels.com%'
             AND image_url NOT LIKE '%pixabay.com%'
             AND image_url NOT LIKE '%fallback%'
             AND image_url NOT LIKE '%stock%'
             AND image_url NOT LIKE '%generic%'
             AND image_url NOT LIKE 'data:image%'
             AND (image_url LIKE '%reuters.com%' 
                  OR image_url LIKE '%bbc.co.uk%'
                  OR image_url LIKE '%cnn.com%'
                  OR image_url LIKE '%apnews.com%'
                  OR image_url LIKE '%france24.com%'
                  OR image_url LIKE '%aljazeera.com%'
                  OR image_url LIKE '%bloomberg.com%'
                  OR image_url LIKE '%theguardian.com%'
                  OR image_url LIKE '%washingtonpost.com%'
                  OR image_url LIKE '%nytimes.com%'
                  OR image_url LIKE '%ft.com%'
                  OR image_url LIKE '%wsj.com%'
                  OR image_url LIKE '%elmundo.es%'
                  OR image_url LIKE '%elpais.com%'
                  OR image_url LIKE '%lavanguardia.com%'
                  OR image_url LIKE '%abc.es%'
                  OR image_url LIKE '%marca.com%'
                  OR image_url LIKE '%expansion.com%'))
        AND (language = 'es' OR 
             (is_translated = 1 AND original_language IS NOT NULL))
    """
    
    print("🔥 FILTROS ULTRA ESTRICTOS PARA PRESENTACIÓN")
    print("=" * 60)
    print("✅ Solo imágenes de fuentes de noticias reales")
    print("✅ Solo en español")
    print("✅ Sin duplicados en mosaico")
    print("-" * 60)
    
    # Test HERO
    print("\n1️⃣ ARTÍCULO HERO:")
    hero_query = f"""
        SELECT id, title, image_url, source, risk_level
        FROM articles 
        {base_filters}
        AND risk_level = 'high'
        ORDER BY datetime(published_at) DESC
        LIMIT 1
    """
    
    cursor.execute(hero_query)
    hero_result = cursor.fetchone()
    
    if hero_result:
        print(f"✅ HERO: ID {hero_result[0]} | {hero_result[1][:40]}...")
        print(f"   Fuente: {hero_result[3]}")
        print(f"   Riesgo: {hero_result[4]}")
        print(f"   Imagen: {hero_result[2]}")
    else:
        print("❌ No hay artículo HERO que cumpla criterios")
    
    # Test MOSAICO
    print("\n2️⃣ MOSAICO (sin duplicados):")
    mosaico_query = f"""
        SELECT id, title, image_url, source, risk_level
        FROM articles 
        {base_filters}
        GROUP BY image_url
        HAVING COUNT(*) = 1
        ORDER BY 
            CASE 
                WHEN risk_level = 'high' THEN 1
                WHEN risk_level = 'medium' THEN 2
                WHEN risk_level = 'low' THEN 3
                ELSE 4
            END,
            datetime(published_at) DESC
        LIMIT 10
    """
    
    cursor.execute(mosaico_query)
    mosaico_results = cursor.fetchall()
    
    if mosaico_results:
        print(f"✅ {len(mosaico_results)} artículos para mosaico:")
        for i, article in enumerate(mosaico_results, 1):
            print(f"   {i}. ID: {article[0]} | {article[1][:30]}... | {article[4]} | {article[3]}")
    else:
        print("❌ No hay artículos para mosaico")
    
    # Estadísticas finales
    print(f"\n3️⃣ ESTADÍSTICAS:")
    cursor.execute(f"SELECT COUNT(*) FROM articles {base_filters}")
    total_valid = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM articles WHERE (is_excluded IS NULL OR is_excluded != 1)")
    total_articles = cursor.fetchone()[0]
    
    print(f"📊 Total artículos válidos: {total_articles}")
    print(f"📊 Artículos que pasan filtros ultra estrictos: {total_valid}")
    print(f"📊 Porcentaje: {(total_valid/total_articles*100):.1f}%")
    
    if total_valid >= 15:
        print(f"\n🎉 PERFECTO para presentación: {total_valid} artículos disponibles")
    elif total_valid >= 5:
        print(f"\n⚠️ ACEPTABLE para presentación: {total_valid} artículos disponibles")
    else:
        print(f"\n❌ PROBLEMAS: Solo {total_valid} artículos disponibles")
    
    conn.close()

if __name__ == "__main__":
    test_ultra_strict_filters()
