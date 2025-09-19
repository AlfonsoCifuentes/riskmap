#!/usr/bin/env python3
"""Test del endpoint /api/articles para debugging del mosaico"""
import sqlite3
import os

def test_articles_endpoint():
    print("🔍 TESTING /api/articles ENDPOINT...")
    
    # Conectar a la base de datos
    db_path = "./data/geopolitical_intel.db"
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada: {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Verificar artículos totales
    cursor.execute("SELECT COUNT(*) FROM articles")
    total_articles = cursor.fetchone()[0]
    print(f"📊 Total artículos en DB: {total_articles}")
    
    # 2. Verificar artículos con imágenes
    cursor.execute("SELECT COUNT(*) FROM articles WHERE image_url IS NOT NULL AND image_url != ''")
    articles_with_images = cursor.fetchone()[0]
    print(f"🖼️ Artículos con imágenes: {articles_with_images}")
    
    # 3. Verificar tipos de imágenes
    cursor.execute("""
        SELECT image_url, COUNT(*) as count 
        FROM articles 
        WHERE image_url IS NOT NULL AND image_url != ''
        GROUP BY CASE 
            WHEN image_url LIKE '%placeholder%' THEN 'placeholder'
            WHEN image_url LIKE '%reuters%' THEN 'reuters'
            WHEN image_url LIKE '%bbc%' THEN 'bbc'
            WHEN image_url LIKE '%cnn%' THEN 'cnn'
            ELSE 'other'
        END
        LIMIT 5
    """)
    image_types = cursor.fetchall()
    print("\n📸 Tipos de imágenes:")
    for img_url, count in image_types:
        print(f"   {img_url}: {count}")
    
    # 4. Simular el filtro ultra restrictivo actual
    cursor.execute("""
        SELECT COUNT(*) FROM articles 
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
    """)
    filtered_articles = cursor.fetchone()[0]
    print(f"\n❌ Artículos que pasan el filtro restrictivo: {filtered_articles}")
    
    # 5. Probar un filtro más permisivo
    cursor.execute("""
        SELECT COUNT(*) FROM articles 
        WHERE (is_excluded IS NULL OR is_excluded != 1)
        AND (image_url IS NOT NULL AND image_url != '')
        AND language = 'es'
        LIMIT 20
    """)
    permissive_articles = cursor.fetchone()[0]
    print(f"✅ Artículos con filtro permisivo (solo imagen + español): {permissive_articles}")
    
    # 6. Mostrar algunos ejemplos
    cursor.execute("""
        SELECT id, title, image_url, language, source
        FROM articles 
        WHERE (image_url IS NOT NULL AND image_url != '')
        AND language = 'es'
        LIMIT 5
    """)
    examples = cursor.fetchall()
    print("\n📰 Ejemplos de artículos disponibles:")
    for article in examples:
        print(f"   ID {article[0]}: {article[1][:50]}... | {article[3]} | {article[4]}")
    
    conn.close()
    
    print(f"\n🎯 DIAGNÓSTICO:")
    print(f"   ❌ PROBLEMA: Filtro demasiado restrictivo elimina TODAS las imágenes placeholder")
    print(f"   ✅ SOLUCIÓN: Usar filtro más permisivo o agregar imágenes reales")

if __name__ == "__main__":
    test_articles_endpoint()