#!/usr/bin/env python3
"""
Script para corregir la lógica de filtrado de imágenes
Analiza y optimiza la selección de artículos con imágenes válidas
"""

import os
import sqlite3
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def analyze_image_filtering():
    """Analiza en detalle el problema del filtrado de imágenes"""
    
    print("🔍 ANÁLISIS DETALLADO DE FILTRADO DE IMÁGENES")
    print("=" * 80)
    
    try:
        db_path = "./data/geopolitical_intel.db"
        if not os.path.exists(db_path):
            print(f"❌ Base de datos no encontrada: {db_path}")
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Estadísticas generales
        print("\n📊 ESTADÍSTICAS GENERALES:")
        cursor.execute("SELECT COUNT(*) FROM unified_articles")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM unified_articles WHERE geopolitical_relevance = 1")
        geopolitical = cursor.fetchone()[0]
        
        print(f"   Total artículos: {total}")
        print(f"   Geopolíticos: {geopolitical}")
        
        # 2. Análisis de imágenes
        print("\n🖼️ ANÁLISIS DE IMÁGENES:")
        
        # Artículos con original_image_url válida
        cursor.execute("""
            SELECT COUNT(*) FROM unified_articles 
            WHERE geopolitical_relevance = 1 
            AND original_image_url IS NOT NULL 
            AND original_image_url != '' 
            AND original_image_url LIKE 'https://%'
        """)
        with_original_image = cursor.fetchone()[0]
        
        # Artículos con image_url válida
        cursor.execute("""
            SELECT COUNT(*) FROM unified_articles 
            WHERE geopolitical_relevance = 1 
            AND image_url IS NOT NULL 
            AND image_url != '' 
            AND image_url LIKE 'https://%'
            AND image_url NOT LIKE '%placeholder%'
        """)
        with_image_url = cursor.fetchone()[0]
        
        # Artículos con CUALQUIER imagen válida (UNION)
        cursor.execute("""
            SELECT COUNT(*) FROM unified_articles 
            WHERE geopolitical_relevance = 1 
            AND (
                (original_image_url IS NOT NULL AND original_image_url != '' AND original_image_url LIKE 'https://%') OR
                (image_url IS NOT NULL AND image_url != '' AND image_url LIKE 'https://%' AND image_url NOT LIKE '%placeholder%')
            )
        """)
        with_any_image = cursor.fetchone()[0]
        
        print(f"   Con original_image_url válida: {with_original_image}")
        print(f"   Con image_url válida: {with_image_url}")  
        print(f"   Con CUALQUIER imagen válida: {with_any_image}")
        
        # 3. Test de la nueva lógica CASE WHEN
        print("\n🧪 TEST DE NUEVA LÓGICA CASE WHEN:")
        
        test_query = """
            SELECT 
                id, title, 
                original_image_url, 
                image_url,
                CASE 
                    WHEN original_image_url IS NOT NULL AND original_image_url != '' AND original_image_url LIKE 'https://%'
                    THEN original_image_url
                    WHEN image_url IS NOT NULL AND image_url != '' AND image_url LIKE 'https://%' AND image_url NOT LIKE '%placeholder%'
                    THEN image_url
                    ELSE NULL
                END as selected_image
            FROM unified_articles 
            WHERE geopolitical_relevance = 1 
            AND title IS NOT NULL AND title != ''
            AND (
                (original_image_url IS NOT NULL AND original_image_url != '' AND original_image_url LIKE 'https://%') OR
                (image_url IS NOT NULL AND image_url != '' AND image_url LIKE 'https://%' AND image_url NOT LIKE '%placeholder%')
            )
            ORDER BY created_at DESC 
            LIMIT 20
        """
        
        cursor.execute(test_query)
        test_results = cursor.fetchall()
        
        print(f"   Artículos que pasarían el filtro mejorado: {len(test_results)}")
        
        # Mostrar muestra
        print("\n📋 MUESTRA DE ARTÍCULOS CON NUEVA LÓGICA:")
        for i, row in enumerate(test_results[:10]):
            id_art, title, orig_img, img_url, selected = row
            print(f"   {i+1}. ID: {id_art}")
            print(f"      Título: {title[:60]}...")
            print(f"      Original: {orig_img[:50] if orig_img else 'None'}...")
            print(f"      Image: {img_url[:50] if img_url else 'None'}...")
            print(f"      ✅ Seleccionada: {selected[:50] if selected else 'None'}...")
            print()
        
        # 4. Problemas detectados
        print("\n⚠️ PROBLEMAS DETECTADOS:")
        
        # Artículos con image_url vacía pero con original_image_url
        cursor.execute("""
            SELECT COUNT(*) FROM unified_articles 
            WHERE geopolitical_relevance = 1 
            AND (image_url = '' OR image_url IS NULL)
            AND original_image_url IS NOT NULL 
            AND original_image_url != '' 
            AND original_image_url LIKE 'https://%'
        """)
        empty_but_has_original = cursor.fetchone()[0]
        
        print(f"   Artículos con image_url vacía pero original_image_url válida: {empty_but_has_original}")
        
        # URLs con placeholder
        cursor.execute("""
            SELECT COUNT(*) FROM unified_articles 
            WHERE geopolitical_relevance = 1 
            AND (
                image_url LIKE '%placeholder%' OR 
                image_url LIKE '%via.placeholder%' OR
                original_image_url LIKE '%placeholder%'
            )
        """)
        with_placeholders = cursor.fetchone()[0]
        
        print(f"   Artículos con URLs placeholder: {with_placeholders}")
        
        conn.close()
        
        print("\n🎯 RECOMENDACIONES:")
        print("   1. ✅ Usar lógica CASE WHEN para priorizar original_image_url")
        print("   2. ✅ Filtrar placeholders más agresivamente")
        print("   3. ✅ Considerar artículos con image_url vacía si tienen original_image_url")
        print(f"   4. ✅ Esto debería incrementar artículos válidos a ~{with_any_image}")
        
    except Exception as e:
        logger.error(f"Error en análisis: {e}")
        
def test_optimized_query():
    """Prueba la consulta optimizada"""
    
    print("\n🚀 PRUEBA DE CONSULTA OPTIMIZADA")
    print("=" * 50)
    
    try:
        db_path = "./data/geopolitical_intel.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Consulta optimizada
        optimized_query = """
            SELECT 
                id, title, 
                CASE 
                    WHEN original_image_url IS NOT NULL AND original_image_url != '' AND original_image_url LIKE 'https://%'
                    THEN original_image_url
                    WHEN image_url IS NOT NULL AND image_url != '' AND image_url LIKE 'https://%' 
                         AND image_url NOT LIKE '%placeholder%' 
                         AND image_url NOT LIKE '%via.placeholder%'
                         AND image_url NOT LIKE '%default%'
                    THEN image_url
                    ELSE NULL
                END as image_url,
                risk_level
            FROM unified_articles 
            WHERE 
                geopolitical_relevance = 1 AND
                title IS NOT NULL AND title != '' AND
                (
                    (content IS NOT NULL AND content != '') OR 
                    (summary IS NOT NULL AND summary != '')
                ) AND
                (
                    (original_image_url IS NOT NULL AND original_image_url != '' AND original_image_url LIKE 'https://%') OR
                    (image_url IS NOT NULL AND image_url != '' AND image_url LIKE 'https://%' 
                     AND image_url NOT LIKE '%placeholder%' 
                     AND image_url NOT LIKE '%via.placeholder%'
                     AND image_url NOT LIKE '%default%')
                ) AND
                created_at >= datetime('now', '-30 days')
            ORDER BY 
                COALESCE(ai_importance, 0) DESC,
                COALESCE(risk_score, 0) DESC,
                created_at DESC
            LIMIT 30
        """
        
        cursor.execute(optimized_query)
        results = cursor.fetchall()
        
        print(f"✅ Artículos que pasarían el filtro optimizado: {len(results)}")
        print("\n📋 PRIMEROS 15 RESULTADOS:")
        
        for i, row in enumerate(results[:15]):
            id_art, title, img_url, risk = row
            print(f"   {i+1}. ID: {id_art} | Risk: {risk}")
            print(f"      {title[:70]}...")
            print(f"      🖼️  {img_url[:60] if img_url else 'Sin imagen'}...")
            print()
        
        conn.close()
        
        return len(results)
        
    except Exception as e:
        logger.error(f"Error en prueba optimizada: {e}")
        return 0

if __name__ == "__main__":
    print("🛠️ HERRAMIENTA DE CORRECCIÓN DE FILTRADO DE IMÁGENES")
    print("=" * 80)
    
    analyze_image_filtering()
    optimized_count = test_optimized_query()
    
    print(f"\n🎯 RESUMEN:")
    print(f"   Artículos disponibles con filtro optimizado: {optimized_count}")
    print(f"   Esto debería resolver el problema de artículos rechazados")
    print(f"   La nueva lógica priorizará original_image_url sobre image_url")
    
    print(f"\n✅ SIGUIENTE PASO: Aplicar esta lógica en RISKMAP.py")