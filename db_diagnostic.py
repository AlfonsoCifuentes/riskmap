#!/usr/bin/env python3
"""
Direct Database Diagnostic - Analyze what articles are being served to the mosaic
"""
import sqlite3
import os
from datetime import datetime, timedelta

def analyze_mosaic_articles():
    """Analyze articles that would be shown in the mosaic"""
    db_path = "./data/geopolitical_intel.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    print("🔍 DIAGNOSTIC: Análisis directo de la base de datos")
    print("=" * 60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check what tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"📊 Tablas disponibles: {[t[0] for t in tables]}")
    
    # Get schema info for articles table
    cursor.execute("PRAGMA table_info(articles)")
    columns = cursor.fetchall()
    print(f"\n📋 Columnas en tabla articles:")
    for col in columns:
        print(f"   - {col[1]} ({col[2]})")
    
    # Test what the current Flask query would return
    print("\n🎯 SIMULANDO CONSULTA DEL FLASK:")
    print("-" * 40)
    
    query = """
    SELECT 
        id, title, summary, source, url, image_source,
        datetime(created_at) as created_at,
        (CASE 
            WHEN image_source IS NOT NULL 
            AND image_source != '' 
            AND image_source NOT LIKE '%placeholder%'
            AND image_source NOT LIKE '%default%'
            AND image_source NOT LIKE '%no-image%'
            THEN 1 ELSE 0 
        END) as has_real_image,
        (CASE 
            WHEN LOWER(title) LIKE '%ukraine%' OR LOWER(title) LIKE '%russia%' 
            OR LOWER(title) LIKE '%china%' OR LOWER(title) LIKE '%taiwan%' 
            OR LOWER(title) LIKE '%war%' OR LOWER(title) LIKE '%conflict%'
            OR LOWER(title) LIKE '%military%' OR LOWER(title) LIKE '%defense%'
            OR LOWER(title) LIKE '%security%' OR LOWER(title) LIKE '%diplomat%'
            OR LOWER(title) LIKE '%sanction%' OR LOWER(title) LIKE '%treaty%'
            OR LOWER(title) LIKE '%election%' OR LOWER(title) LIKE '%government%'
            OR LOWER(title) LIKE '%president%' OR LOWER(title) LIKE '%minister%'
            THEN 1 ELSE 0 
        END) as is_geopolitical
    FROM articles 
    WHERE created_at >= datetime('now', '-14 days')
    ORDER BY created_at DESC 
    LIMIT 20
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    print(f"📈 Total artículos encontrados: {len(results)}")
    
    geopolitical_count = 0
    with_real_images = 0
    valid_articles = 0
    
    for i, row in enumerate(results, 1):
        id, title, summary, source, url, image_source, created_at, has_real_image, is_geopolitical = row
        
        print(f"\n🔸 Artículo #{i} (ID: {id})")
        print(f"   📰 Título: {title[:80]}...")
        print(f"   🌐 Fuente: {source}")
        print(f"   📅 Fecha: {created_at}")
        print(f"   🖼️  Imagen: {image_source or 'NO IMAGEN'}")
        print(f"   ✅ Imagen real: {'SÍ' if has_real_image else 'NO'}")
        print(f"   🎯 Geopolítico: {'SÍ' if is_geopolitical else 'NO'}")
        
        if has_real_image:
            with_real_images += 1
        if is_geopolitical:
            geopolitical_count += 1
        if has_real_image and is_geopolitical:
            valid_articles += 1
            print(f"   ✨ VÁLIDO PARA MOSAICO")
        else:
            print(f"   ❌ RECHAZADO - {'Sin imagen' if not has_real_image else ''} {'No geopolítico' if not is_geopolitical else ''}")
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DEL DIAGNÓSTICO:")
    print(f"   📈 Total artículos analizados: {len(results)}")
    print(f"   🖼️  Con imágenes reales: {with_real_images}")
    print(f"   🎯 Contenido geopolítico: {geopolitical_count}")
    print(f"   ✅ Válidos para mosaico: {valid_articles}")
    print(f"   ❌ Rechazados: {len(results) - valid_articles}")
    
    # Check for image issues
    print("\n🖼️  DIAGNÓSTICO DE IMÁGENES:")
    print("-" * 40)
    
    cursor.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN image_source IS NULL OR image_source = '' THEN 1 ELSE 0 END) as sin_imagen,
        SUM(CASE WHEN image_source LIKE '%placeholder%' THEN 1 ELSE 0 END) as placeholders,
        SUM(CASE WHEN image_source LIKE '%default%' THEN 1 ELSE 0 END) as defaults,
        SUM(CASE WHEN image_source LIKE '%no-image%' THEN 1 ELSE 0 END) as no_image
    FROM articles 
    WHERE created_at >= datetime('now', '-14 days')
    """)
    
    img_stats = cursor.fetchone()
    total, sin_imagen, placeholders, defaults, no_image = img_stats
    
    print(f"   📊 Total artículos (14 días): {total}")
    print(f"   ❌ Sin imagen: {sin_imagen}")
    print(f"   🔳 Placeholders: {placeholders}")
    print(f"   🔳 Defaults: {defaults}")
    print(f"   🔳 No-image: {no_image}")
    print(f"   ✅ Con imagen real: {total - sin_imagen - placeholders - defaults - no_image}")
    
    # Check for non-geopolitical content
    print("\n🎯 DIAGNÓSTICO DE CONTENIDO NO GEOPOLÍTICO:")
    print("-" * 50)
    
    non_geo_query = """
    SELECT title, source, 
        CASE 
            WHEN LOWER(title) LIKE '%sport%' OR LOWER(title) LIKE '%football%' OR LOWER(title) LIKE '%soccer%' 
            OR LOWER(title) LIKE '%basketball%' OR LOWER(title) LIKE '%tennis%' THEN 'DEPORTES'
            WHEN LOWER(title) LIKE '%celebrity%' OR LOWER(title) LIKE '%hollywood%' OR LOWER(title) LIKE '%music%' 
            OR LOWER(title) LIKE '%movie%' OR LOWER(title) LIKE '%entertainment%' THEN 'ENTRETENIMIENTO'
            WHEN LOWER(title) LIKE '%iphone%' OR LOWER(title) LIKE '%android%' OR LOWER(title) LIKE '%tech%' 
            OR LOWER(title) LIKE '%apple%' OR LOWER(title) LIKE '%google%' THEN 'TECNOLOGÍA CONSUMO'
            WHEN LOWER(title) LIKE '%health%' OR LOWER(title) LIKE '%covid%' OR LOWER(title) LIKE '%vaccine%' THEN 'SALUD'
            WHEN LOWER(title) LIKE '%weather%' OR LOWER(title) LIKE '%climate%' THEN 'CLIMA'
            ELSE 'OTRO NO GEOPOLÍTICO'
        END as categoria
    FROM articles 
    WHERE created_at >= datetime('now', '-14 days')
    AND NOT (
        LOWER(title) LIKE '%ukraine%' OR LOWER(title) LIKE '%russia%' 
        OR LOWER(title) LIKE '%china%' OR LOWER(title) LIKE '%taiwan%' 
        OR LOWER(title) LIKE '%war%' OR LOWER(title) LIKE '%conflict%'
        OR LOWER(title) LIKE '%military%' OR LOWER(title) LIKE '%defense%'
        OR LOWER(title) LIKE '%security%' OR LOWER(title) LIKE '%diplomat%'
        OR LOWER(title) LIKE '%sanction%' OR LOWER(title) LIKE '%treaty%'
        OR LOWER(title) LIKE '%election%' OR LOWER(title) LIKE '%government%'
        OR LOWER(title) LIKE '%president%' OR LOWER(title) LIKE '%minister%'
    )
    LIMIT 10
    """
    
    cursor.execute(non_geo_query)
    non_geo_results = cursor.fetchall()
    
    if non_geo_results:
        print("❌ EJEMPLOS DE CONTENIDO NO GEOPOLÍTICO DETECTADO:")
        for title, source, categoria in non_geo_results:
            print(f"   🔸 [{categoria}] {title[:60]}... (Fuente: {source})")
    else:
        print("✅ No se detectó contenido obviamente no geopolítico")
    
    conn.close()
    
    return {
        'total_articles': len(results),
        'with_real_images': with_real_images,
        'geopolitical_articles': geopolitical_count,
        'valid_for_mosaic': valid_articles
    }

if __name__ == "__main__":
    stats = analyze_mosaic_articles()
    
    print("\n" + "🎯" * 20)
    print("RECOMENDACIONES:")
    
    if stats['valid_for_mosaic'] < 10:
        print("⚠️  MUY POCOS ARTÍCULOS VÁLIDOS - Se necesita:")
        print("   1. Mejorar extracción de imágenes")
        print("   2. Ampliar criterios geopolíticos")
        print("   3. Revisar fuentes de datos")
    
    if stats['with_real_images'] < stats['total_articles'] / 2:
        print("🖼️  PROBLEMA DE IMÁGENES - Ejecutar procesamiento masivo")
    
    if stats['geopolitical_articles'] < stats['total_articles'] / 2:
        print("🎯 PROBLEMA DE FILTRO GEOPOLÍTICO - Revisar criterios")