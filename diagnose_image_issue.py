#!/usr/bin/env python3
"""
DIAGNÓSTICO DE IMÁGENES - INVESTIGACIÓN PROFUNDA
===============================================

Analizar por qué el filtro dice que no hay imágenes reales
cuando la BD dice que hay 366 artículos con imágenes.

Autor: GitHub Copilot
Fecha: 2025
"""

import os
import sqlite3
from datetime import datetime

def analyze_image_issue():
    """Analizar el problema de imágenes en detalle"""
    print("🔍 DIAGNÓSTICO PROFUNDO DE IMÁGENES")
    print("=" * 80)
    
    db_path = "data/geopolitical_intel.db"
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Estadísticas generales
    print("📊 ESTADÍSTICAS GENERALES:")
    
    cursor.execute("SELECT COUNT(*) FROM unified_articles")
    total = cursor.fetchone()[0]
    print(f"   Total artículos: {total}")
    
    cursor.execute("SELECT COUNT(*) FROM unified_articles WHERE geopolitical_relevance = 1")
    geopolitical = cursor.fetchone()[0]
    print(f"   Geopolíticos: {geopolitical}")
    
    # 2. Análisis de imágenes detallado
    print(f"\n🖼️ ANÁLISIS DETALLADO DE IMÁGENES:")
    
    # Artículos con imagen_url
    cursor.execute("SELECT COUNT(*) FROM unified_articles WHERE image_url IS NOT NULL AND image_url != ''")
    with_image_url = cursor.fetchone()[0]
    print(f"   Con image_url: {with_image_url}")
    
    # Artículos con original_image_url
    cursor.execute("SELECT COUNT(*) FROM unified_articles WHERE original_image_url IS NOT NULL AND original_image_url != ''")
    with_original_image_url = cursor.fetchone()[0]
    print(f"   Con original_image_url: {with_original_image_url}")
    
    # Artículos con cualquiera de las dos
    cursor.execute("""
        SELECT COUNT(*) FROM unified_articles 
        WHERE (image_url IS NOT NULL AND image_url != '') 
           OR (original_image_url IS NOT NULL AND original_image_url != '')
    """)
    with_any_image = cursor.fetchone()[0]
    print(f"   Con cualquier imagen: {with_any_image}")
    
    # 3. Análisis de URLs de imágenes
    print(f"\n🔗 ANÁLISIS DE URLs DE IMÁGENES:")
    
    # URLs que empiezan con https://
    cursor.execute("""
        SELECT COUNT(*) FROM unified_articles 
        WHERE (image_url LIKE 'https://%' OR original_image_url LIKE 'https://%')
    """)
    https_images = cursor.fetchone()[0]
    print(f"   URLs HTTPS: {https_images}")
    
    # URLs que contienen placeholder
    cursor.execute("""
        SELECT COUNT(*) FROM unified_articles 
        WHERE (image_url LIKE '%placeholder%' OR original_image_url LIKE '%placeholder%')
    """)
    placeholder_images = cursor.fetchone()[0]
    print(f"   URLs con placeholder: {placeholder_images}")
    
    # URLs que contienen via.placeholder
    cursor.execute("""
        SELECT COUNT(*) FROM unified_articles 
        WHERE (image_url LIKE '%via.placeholder%' OR original_image_url LIKE '%via.placeholder%')
    """)
    via_placeholder_images = cursor.fetchone()[0]
    print(f"   URLs con via.placeholder: {via_placeholder_images}")
    
    # 4. Muestra de URLs reales
    print(f"\n📋 MUESTRA DE URLs DE IMÁGENES:")
    
    cursor.execute("""
        SELECT id, title, image_url, original_image_url
        FROM unified_articles 
        WHERE geopolitical_relevance = 1 
          AND ((image_url IS NOT NULL AND image_url != '') 
               OR (original_image_url IS NOT NULL AND original_image_url != ''))
        LIMIT 10
    """)
    samples = cursor.fetchall()
    
    for i, (id, title, image_url, original_image_url) in enumerate(samples, 1):
        print(f"   {i}. ID: {id}")
        print(f"      Título: {title[:60]}...")
        print(f"      image_url: {image_url[:80] if image_url else 'None'}{'...' if image_url and len(image_url) > 80 else ''}")
        print(f"      original_image_url: {original_image_url[:80] if original_image_url else 'None'}{'...' if original_image_url and len(original_image_url) > 80 else ''}")
        print()
    
    # 5. Análisis específico del filtro usado en get_top_articles_from_db
    print(f"🎯 ANÁLISIS DEL FILTRO ESPECÍFICO:")
    
    # Query exacta del filtro actual
    query_filter = """
        SELECT COUNT(*) FROM unified_articles 
        WHERE 
            geopolitical_relevance = 1 AND
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
            )
    """
    
    cursor.execute(query_filter)
    filter_result = cursor.fetchone()[0]
    print(f"   Artículos que pasan el filtro completo: {filter_result}")
    
    # Desglosar el filtro paso a paso
    print(f"\n🔬 DESGLOSE PASO A PASO DEL FILTRO:")
    
    # Paso 1: Solo geopolitical_relevance = 1
    cursor.execute("SELECT COUNT(*) FROM unified_articles WHERE geopolitical_relevance = 1")
    step1 = cursor.fetchone()[0]
    print(f"   1. geopolitical_relevance = 1: {step1}")
    
    # Paso 2: + title no vacío
    cursor.execute("""
        SELECT COUNT(*) FROM unified_articles 
        WHERE geopolitical_relevance = 1 AND title IS NOT NULL AND title != ''
    """)
    step2 = cursor.fetchone()[0]
    print(f"   2. + title válido: {step2}")
    
    # Paso 3: + content o summary
    cursor.execute("""
        SELECT COUNT(*) FROM unified_articles 
        WHERE geopolitical_relevance = 1 AND title IS NOT NULL AND title != ''
          AND ((content IS NOT NULL AND content != '') OR (summary IS NOT NULL AND summary != ''))
    """)
    step3 = cursor.fetchone()[0]
    print(f"   3. + contenido válido: {step3}")
    
    # Paso 4: + condiciones de imagen
    cursor.execute(query_filter)
    step4 = cursor.fetchone()[0]
    print(f"   4. + imagen válida: {step4}")
    
    # 6. Investigar por qué se rechaza las imágenes
    print(f"\n🔍 INVESTIGACIÓN DE RECHAZO DE IMÁGENES:")
    
    # Artículos geopolíticos sin imagen válida
    cursor.execute("""
        SELECT COUNT(*) FROM unified_articles 
        WHERE geopolitical_relevance = 1 
          AND title IS NOT NULL AND title != ''
          AND ((content IS NOT NULL AND content != '') OR (summary IS NOT NULL AND summary != ''))
          AND NOT (
                (original_image_url IS NOT NULL AND original_image_url != '') OR
                (image_url IS NOT NULL AND image_url != '' AND 
                 image_url NOT LIKE '%placeholder%' AND 
                 image_url NOT LIKE '%via.placeholder%' AND
                 image_url NOT LIKE '%default%')
          )
    """)
    rejected_by_image = cursor.fetchone()[0]
    print(f"   Artículos rechazados por imagen: {rejected_by_image}")
    
    # Muestra de los rechazados por imagen
    cursor.execute("""
        SELECT id, title, image_url, original_image_url
        FROM unified_articles 
        WHERE geopolitical_relevance = 1 
          AND title IS NOT NULL AND title != ''
          AND ((content IS NOT NULL AND content != '') OR (summary IS NOT NULL AND summary != ''))
          AND NOT (
                (original_image_url IS NOT NULL AND original_image_url != '') OR
                (image_url IS NOT NULL AND image_url != '' AND 
                 image_url NOT LIKE '%placeholder%' AND 
                 image_url NOT LIKE '%via.placeholder%' AND
                 image_url NOT LIKE '%default%')
          )
        LIMIT 5
    """)
    rejected_samples = cursor.fetchall()
    
    print(f"   Muestra de rechazados:")
    for i, (id, title, image_url, original_image_url) in enumerate(rejected_samples, 1):
        print(f"      {i}. ID: {id} - {title[:40]}...")
        print(f"         image_url: '{image_url}'")
        print(f"         original_image_url: '{original_image_url}'")
    
    conn.close()
    
    # 7. Resumen y recomendaciones
    print(f"\n🎯 RESUMEN Y DIAGNÓSTICO:")
    print(f"   Total artículos: {total}")
    print(f"   Geopolíticos: {geopolitical}")
    print(f"   Con cualquier imagen: {with_any_image}")
    print(f"   Pasan filtro completo: {filter_result}")
    print(f"   Rechazados por imagen: {rejected_by_image}")
    
    if filter_result == 0:
        print(f"\n❌ PROBLEMA IDENTIFICADO:")
        print(f"   El filtro de imágenes es demasiado estricto")
        print(f"   Está rechazando {with_any_image} artículos que SÍ tienen imágenes")
        
        print(f"\n💡 POSIBLES CAUSAS:")
        if placeholder_images > 0:
            print(f"   - {placeholder_images} artículos tienen URLs con 'placeholder'")
        if via_placeholder_images > 0:
            print(f"   - {via_placeholder_images} artículos tienen URLs con 'via.placeholder'")
        
        print(f"\n🔧 RECOMENDACIÓN:")
        print(f"   Revisar y ajustar el filtro de imágenes para ser menos restrictivo")
        print(f"   pero manteniendo la calidad")

if __name__ == "__main__":
    analyze_image_issue()