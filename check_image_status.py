#!/usr/bin/env python3
"""
Script para verificar el estado actual de las imágenes en la base de datos
y el mosaico de noticias geopolíticas
"""
import sqlite3
import os
from datetime import datetime

def check_database_images():
    """Verifica el estado de las imágenes en la base de datos"""
    
    db_path = "./data/geopolitical_intel.db"
    
    if not os.path.exists(db_path):
        print("❌ Base de datos no encontrada:", db_path)
        return
    
    print("📊 VERIFICACIÓN DE IMÁGENES EN BASE DE DATOS")
    print("=" * 60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Total de artículos
    cursor.execute("SELECT COUNT(*) FROM articles")
    total_articles = cursor.fetchone()[0]
    print(f"📰 Total de artículos: {total_articles:,}")
    
    # Artículos con imágenes
    cursor.execute("""
        SELECT COUNT(*) FROM articles 
        WHERE (image_url IS NOT NULL AND image_url != '') OR 
              (original_image_url IS NOT NULL AND original_image_url != '')
    """)
    articles_with_images = cursor.fetchone()[0]
    print(f"🖼️  Artículos con alguna imagen: {articles_with_images:,}")
    
    # Artículos con imágenes reales (no placeholder)
    cursor.execute("""
        SELECT COUNT(*) FROM articles 
        WHERE (
            (image_url IS NOT NULL AND image_url != '' AND 
             image_url NOT LIKE '%placeholder%' AND 
             image_url NOT LIKE '%via.placeholder%') OR
            (original_image_url IS NOT NULL AND original_image_url != '')
        )
    """)
    real_images = cursor.fetchone()[0]
    print(f"✅ Artículos con imágenes reales: {real_images:,}")
    
    # Artículos geopolíticos con imágenes reales
    cursor.execute("""
        SELECT COUNT(*) FROM articles 
        WHERE (
            (image_url IS NOT NULL AND image_url != '' AND 
             image_url NOT LIKE '%placeholder%' AND 
             image_url NOT LIKE '%via.placeholder%') OR
            (original_image_url IS NOT NULL AND original_image_url != '')
        ) AND (
            LOWER(title) LIKE '%war%' OR LOWER(title) LIKE '%conflict%' OR
            LOWER(title) LIKE '%military%' OR LOWER(title) LIKE '%politics%' OR
            LOWER(title) LIKE '%russia%' OR LOWER(title) LIKE '%ukraine%' OR
            LOWER(title) LIKE '%china%' OR LOWER(title) LIKE '%iran%' OR
            LOWER(title) LIKE '%israel%' OR LOWER(title) LIKE '%gaza%' OR
            LOWER(title) LIKE '%security%' OR LOWER(title) LIKE '%diplomat%' OR
            LOWER(title) LIKE '%government%' OR LOWER(title) LIKE '%president%' OR
            LOWER(title) LIKE '%minister%' OR LOWER(title) LIKE '%trump%' OR
            LOWER(title) LIKE '%biden%' OR LOWER(title) LIKE '%putin%' OR
            LOWER(title) LIKE '%nuclear%' OR LOWER(title) LIKE '%nato%'
        )
    """)
    geopolitical_with_images = cursor.fetchone()[0]
    print(f"🎯 Geopolíticos con imágenes reales: {geopolitical_with_images:,}")
    
    # Artículos recientes (últimos 14 días)
    cursor.execute("""
        SELECT COUNT(*) FROM articles 
        WHERE created_at >= datetime('now', '-14 days')
    """)
    recent_articles = cursor.fetchone()[0]
    print(f"📅 Artículos recientes (14 días): {recent_articles:,}")
    
    # Artículos geopolíticos recientes con imágenes
    cursor.execute("""
        SELECT COUNT(*) FROM articles 
        WHERE created_at >= datetime('now', '-14 days') AND (
            (image_url IS NOT NULL AND image_url != '' AND 
             image_url NOT LIKE '%placeholder%' AND 
             image_url NOT LIKE '%via.placeholder%') OR
            (original_image_url IS NOT NULL AND original_image_url != '')
        ) AND (
            LOWER(title) LIKE '%war%' OR LOWER(title) LIKE '%conflict%' OR
            LOWER(title) LIKE '%military%' OR LOWER(title) LIKE '%politics%' OR
            LOWER(title) LIKE '%russia%' OR LOWER(title) LIKE '%ukraine%' OR
            LOWER(title) LIKE '%china%' OR LOWER(title) LIKE '%iran%' OR
            LOWER(title) LIKE '%israel%' OR LOWER(title) LIKE '%gaza%' OR
            LOWER(title) LIKE '%security%' OR LOWER(title) LIKE '%diplomat%' OR
            LOWER(title) LIKE '%government%' OR LOWER(title) LIKE '%president%' OR
            LOWER(title) LIKE '%minister%' OR LOWER(title) LIKE '%trump%' OR
            LOWER(title) LIKE '%biden%' OR LOWER(title) LIKE '%putin%' OR
            LOWER(title) LIKE '%nuclear%' OR LOWER(title) LIKE '%nato%'
        )
    """)
    target_articles = cursor.fetchone()[0]
    print(f"🔥 OBJETIVO (recientes + geopolíticos + imágenes): {target_articles:,}")
    
    print("\n" + "=" * 60)
    
    if target_articles > 0:
        print(f"✅ ÉXITO: {target_articles} artículos cumplen todos los criterios")
        
        # Mostrar algunos ejemplos
        print("\n🎯 EJEMPLOS DE ARTÍCULOS VÁLIDOS:")
        cursor.execute("""
            SELECT id, title, 
                   CASE 
                       WHEN original_image_url IS NOT NULL AND original_image_url != '' 
                       THEN original_image_url
                       ELSE image_url
                   END as image,
                   created_at
            FROM articles 
            WHERE created_at >= datetime('now', '-14 days') AND (
                (image_url IS NOT NULL AND image_url != '' AND 
                 image_url NOT LIKE '%placeholder%' AND 
                 image_url NOT LIKE '%via.placeholder%') OR
                (original_image_url IS NOT NULL AND original_image_url != '')
            ) AND (
                LOWER(title) LIKE '%war%' OR LOWER(title) LIKE '%conflict%' OR
                LOWER(title) LIKE '%military%' OR LOWER(title) LIKE '%politics%' OR
                LOWER(title) LIKE '%russia%' OR LOWER(title) LIKE '%ukraine%' OR
                LOWER(title) LIKE '%china%' OR LOWER(title) LIKE '%iran%' OR
                LOWER(title) LIKE '%israel%' OR LOWER(title) LIKE '%gaza%' OR
                LOWER(title) LIKE '%security%' OR LOWER(title) LIKE '%diplomat%' OR
                LOWER(title) LIKE '%government%' OR LOWER(title) LIKE '%president%' OR
                LOWER(title) LIKE '%minister%' OR LOWER(title) LIKE '%trump%' OR
                LOWER(title) LIKE '%biden%' OR LOWER(title) LIKE '%putin%' OR
                LOWER(title) LIKE '%nuclear%' OR LOWER(title) LIKE '%nato%'
            )
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        examples = cursor.fetchall()
        for i, (id, title, image, created) in enumerate(examples, 1):
            print(f"   {i}. ID {id}: {title[:60]}...")
            print(f"      📸 Imagen: {image[:80]}...")
            print(f"      📅 Fecha: {created}")
            print()
    else:
        print("❌ NO HAY ARTÍCULOS que cumplan todos los criterios")
        print("   🔧 Necesario usar RSS feeds o métodos alternativos")
    
    # Verificar directorio de imágenes locales
    print("\n📁 VERIFICACIÓN DE IMÁGENES LOCALES:")
    image_dir = "src/web/static/images/news/"
    if os.path.exists(image_dir):
        local_images = [f for f in os.listdir(image_dir) if f.endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif'))]
        print(f"🖼️  Imágenes locales guardadas: {len(local_images)}")
        
        if len(local_images) > 0:
            print("   Ejemplos:")
            for img in local_images[:5]:
                print(f"     - {img}")
    else:
        print("❌ Directorio de imágenes no existe")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("🎯 CONCLUSIÓN:")
    if target_articles > 0:
        print("   ✅ El mosaico debería mostrar contenido válido")
        print("   ✅ El filtro SQL funciona correctamente")
    else:
        print("   ⚠️  El mosaico podría estar vacío")
        print("   🔧 Necesario implementar alternativas de imagen")

def check_recent_rss_images():
    """Verifica qué imágenes RSS están disponibles"""
    print("\n📡 VERIFICACIÓN DE IMÁGENES RSS:")
    print("=" * 40)
    
    db_path = "./data/geopolitical_intel.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Artículos recientes con URLs RSS que pueden tener imágenes
    cursor.execute("""
        SELECT id, title, url, image_url, source
        FROM articles 
        WHERE created_at >= datetime('now', '-7 days')
        AND url IS NOT NULL AND url != ''
        AND (image_url IS NULL OR image_url = '' OR image_url LIKE '%placeholder%')
        AND (
            LOWER(title) LIKE '%war%' OR LOWER(title) LIKE '%conflict%' OR
            LOWER(title) LIKE '%military%' OR LOWER(title) LIKE '%politics%' OR
            LOWER(title) LIKE '%russia%' OR LOWER(title) LIKE '%ukraine%' OR
            LOWER(title) LIKE '%china%' OR LOWER(title) LIKE '%iran%' OR
            LOWER(title) LIKE '%security%' OR LOWER(title) LIKE '%diplomat%'
        )
        ORDER BY created_at DESC
        LIMIT 10
    """)
    
    candidates = cursor.fetchall()
    print(f"🎯 Artículos geopolíticos sin imagen (candidatos): {len(candidates)}")
    
    for id, title, url, image_url, source in candidates:
        print(f"\n   📰 ID {id}: {title[:50]}...")
        print(f"   🔗 URL: {url}")
        print(f"   🏢 Fuente: {source}")
        print(f"   🖼️  Imagen actual: {image_url or 'Ninguna'}")
    
    conn.close()

if __name__ == "__main__":
    check_database_images()
    check_recent_rss_images()