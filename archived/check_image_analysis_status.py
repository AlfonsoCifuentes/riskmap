#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar y reportar el estado de las imágenes
Especialmente enfocado en detectar imágenes de baja calidad y duplicadas
"""

import sqlite3
import json
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Añadir el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

# Cargar variables de entorno
load_dotenv()

def get_database_path():
    """Obtener la ruta de la base de datos desde variables de entorno"""
    database_url = os.getenv('DATABASE_URL', 'sqlite:///data/geopolitical_intel.db')
    if database_url.startswith('sqlite:///'):
        return database_url.replace('sqlite:///', '')
    return database_url

def check_image_quality():
    """
    Verificar la calidad de las imágenes en la base de datos
    """
    print("🔍 ANÁLISIS DE CALIDAD DE IMÁGENES")
    print("=" * 50)
    
    db_path = get_database_path()
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Verificar artículos con análisis visual
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_with_images,
                    COUNT(CASE WHEN visual_analysis_json IS NOT NULL THEN 1 END) as with_analysis,
                    AVG(CASE WHEN visual_analysis_json IS NOT NULL 
                        THEN json_extract(visual_analysis_json, '$.quality_score') 
                        END) as avg_quality
                FROM articles 
                WHERE image_url IS NOT NULL AND image_url != ''
            """)
            
            stats = cursor.fetchone()
            total_with_images, with_analysis, avg_quality = stats
            
            print(f"📊 Total artículos con imágenes: {total_with_images}")
            print(f"📈 Con análisis visual: {with_analysis}")
            print(f"🎯 Calidad promedio: {avg_quality:.3f if avg_quality else 0}")
            print(f"📋 Cobertura de análisis: {(with_analysis/total_with_images*100):.1f}%" if total_with_images > 0 else "0%")
            
            # Identificar imágenes de baja calidad
            cursor.execute("""
                SELECT id, title, image_url, 
                       json_extract(visual_analysis_json, '$.quality_score') as quality,
                       json_extract(visual_analysis_json, '$.image_width') as width,
                       json_extract(visual_analysis_json, '$.image_height') as height
                FROM articles 
                WHERE image_url IS NOT NULL 
                AND visual_analysis_json IS NOT NULL
                AND json_extract(visual_analysis_json, '$.quality_score') < 0.6
                ORDER BY json_extract(visual_analysis_json, '$.quality_score') ASC
                LIMIT 10
            """)
            
            low_quality = cursor.fetchall()
            
            print(f"\n🔻 IMÁGENES DE BAJA CALIDAD (< 0.6)")
            print("-" * 50)
            
            if low_quality:
                for article in low_quality:
                    article_id, title, image_url, quality, width, height = article
                    resolution = f"{width}x{height}" if width and height else "N/A"
                    print(f"ID: {article_id}")
                    print(f"   Título: {title[:60]}...")
                    print(f"   Calidad: {quality:.3f}")
                    print(f"   Resolución: {resolution}")
                    print(f"   URL: {image_url[:80]}...")
                    print()
            else:
                print("✅ No se encontraron imágenes de baja calidad")
            
            # Verificar imágenes de muy baja resolución
            cursor.execute("""
                SELECT id, title, image_url,
                       json_extract(visual_analysis_json, '$.image_width') as width,
                       json_extract(visual_analysis_json, '$.image_height') as height,
                       json_extract(visual_analysis_json, '$.quality_score') as quality
                FROM articles 
                WHERE image_url IS NOT NULL 
                AND visual_analysis_json IS NOT NULL
                AND (
                    json_extract(visual_analysis_json, '$.image_width') < 400 
                    OR json_extract(visual_analysis_json, '$.image_height') < 300
                )
                ORDER BY (json_extract(visual_analysis_json, '$.image_width') * 
                         json_extract(visual_analysis_json, '$.image_height')) ASC
                LIMIT 5
            """)
            
            low_res = cursor.fetchall()
            
            print(f"\n📱 IMÁGENES DE BAJA RESOLUCIÓN")
            print("-" * 50)
            
            if low_res:
                for article in low_res:
                    article_id, title, image_url, width, height, quality = article
                    print(f"ID: {article_id}")
                    print(f"   Título: {title[:60]}...")
                    print(f"   Resolución: {width}x{height}")
                    print(f"   Calidad: {quality:.3f if quality else 'N/A'}")
                    print(f"   URL: {image_url[:80]}...")
                    print()
            else:
                print("✅ No se encontraron imágenes de muy baja resolución")
                
    except Exception as e:
        print(f"❌ Error verificando calidad de imágenes: {e}")

def check_duplicate_candidates():
    """
    Verificar candidatos a imágenes duplicadas basándose en URLs similares
    """
    print("\n🔄 ANÁLISIS DE POSIBLES DUPLICADOS")
    print("=" * 50)
    
    db_path = get_database_path()
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Buscar URLs similares (mismo dominio)
            cursor.execute("""
                SELECT 
                    SUBSTR(image_url, 1, INSTR(image_url, '/', 9)) as domain_path,
                    COUNT(*) as count,
                    GROUP_CONCAT(id, ', ') as article_ids
                FROM articles 
                WHERE image_url IS NOT NULL 
                AND image_url != ''
                AND image_url NOT LIKE '%picsum%'
                AND image_url NOT LIKE '%placeholder%'
                GROUP BY SUBSTR(image_url, 1, INSTR(image_url, '/', 9))
                HAVING COUNT(*) > 1
                ORDER BY COUNT(*) DESC
                LIMIT 10
            """)
            
            similar_domains = cursor.fetchall()
            
            if similar_domains:
                print("🌐 Artículos con imágenes del mismo dominio:")
                for domain, count, ids in similar_domains:
                    print(f"   {domain}: {count} artículos (IDs: {ids})")
            else:
                print("✅ No se encontraron dominios con múltiples imágenes")
            
            # Buscar imágenes con fingerprints
            cursor.execute("""
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN image_fingerprint IS NOT NULL THEN 1 END) as with_fingerprint
                FROM articles 
                WHERE image_url IS NOT NULL AND image_url != ''
            """)
            
            fingerprint_stats = cursor.fetchone()
            total, with_fingerprint = fingerprint_stats
            
            print(f"\n🔐 Estado de fingerprints:")
            print(f"   Total imágenes: {total}")
            print(f"   Con fingerprint: {with_fingerprint}")
            print(f"   Cobertura: {(with_fingerprint/total*100):.1f}%" if total > 0 else "0%")
            
    except Exception as e:
        print(f"❌ Error verificando duplicados: {e}")

def check_mosaic_positioning():
    """
    Verificar el estado del posicionamiento en el mosaico
    """
    print("\n📍 ANÁLISIS DE POSICIONAMIENTO EN MOSAICO")
    print("=" * 50)
    
    db_path = get_database_path()
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Verificar si existe la columna mosaic_position
            cursor.execute("PRAGMA table_info(articles)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'mosaic_position' not in columns:
                print("⚠️ La columna 'mosaic_position' no existe en la tabla articles")
                return
            
            # Estadísticas de posicionamiento
            cursor.execute("""
                SELECT 
                    COALESCE(mosaic_position, 'sin_asignar') as position,
                    COUNT(*) as count,
                    AVG(CASE WHEN visual_analysis_json IS NOT NULL 
                        THEN json_extract(visual_analysis_json, '$.quality_score') 
                        END) as avg_quality
                FROM articles 
                WHERE image_url IS NOT NULL 
                GROUP BY COALESCE(mosaic_position, 'sin_asignar')
                ORDER BY 
                    CASE COALESCE(mosaic_position, 'sin_asignar')
                        WHEN 'hero' THEN 1
                        WHEN 'featured' THEN 2
                        WHEN 'standard' THEN 3
                        WHEN 'thumbnail' THEN 4
                        ELSE 5
                    END
            """)
            
            positions = cursor.fetchall()
            
            print("📊 Distribución por posición:")
            total_positioned = sum(count for pos, count, qual in positions)
            
            for position, count, avg_quality in positions:
                percentage = (count / total_positioned * 100) if total_positioned > 0 else 0
                quality_str = f"{avg_quality:.3f}" if avg_quality else "N/A"
                print(f"   {position}: {count} artículos ({percentage:.1f}%) - Calidad promedio: {quality_str}")
            
            # Ejemplos de cada posición
            print(f"\n🔍 Ejemplos por posición:")
            for position in ['hero', 'featured', 'standard', 'thumbnail']:
                cursor.execute("""
                    SELECT id, title, 
                           json_extract(visual_analysis_json, '$.quality_score') as quality
                    FROM articles 
                    WHERE mosaic_position = ? 
                    AND image_url IS NOT NULL
                    ORDER BY json_extract(visual_analysis_json, '$.quality_score') DESC
                    LIMIT 1
                """, (position,))
                
                example = cursor.fetchone()
                if example:
                    article_id, title, quality = example
                    quality_str = f"{quality:.3f}" if quality else "N/A"
                    print(f"   {position}: ID {article_id} - {title[:50]}... (Q: {quality_str})")
                else:
                    print(f"   {position}: Sin artículos asignados")
                    
    except Exception as e:
        print(f"❌ Error verificando posicionamiento: {e}")

def generate_recommendations():
    """
    Generar recomendaciones basadas en el análisis
    """
    print("\n💡 RECOMENDACIONES")
    print("=" * 50)
    
    db_path = get_database_path()
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            recommendations = []
            
            # Verificar cobertura de análisis visual
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN visual_analysis_json IS NOT NULL THEN 1 END) as analyzed
                FROM articles 
                WHERE image_url IS NOT NULL
            """)
            
            total, analyzed = cursor.fetchone()
            coverage = (analyzed / total * 100) if total > 0 else 0
            
            if coverage < 95:
                recommendations.append(f"🔍 Ejecutar análisis visual para {total - analyzed} imágenes restantes")
            
            # Verificar calidad promedio
            cursor.execute("""
                SELECT AVG(json_extract(visual_analysis_json, '$.quality_score'))
                FROM articles 
                WHERE visual_analysis_json IS NOT NULL
            """)
            
            avg_quality = cursor.fetchone()[0]
            if avg_quality and avg_quality < 0.7:
                recommendations.append(f"🎨 Mejorar calidad de imágenes (promedio actual: {avg_quality:.3f})")
            
            # Verificar fingerprints
            cursor.execute("""
                SELECT COUNT(CASE WHEN image_fingerprint IS NULL THEN 1 END)
                FROM articles 
                WHERE image_url IS NOT NULL
            """)
            
            missing_fingerprints = cursor.fetchone()[0]
            if missing_fingerprints > 0:
                recommendations.append(f"🔐 Generar fingerprints para {missing_fingerprints} imágenes")
            
            # Verificar posicionamiento
            cursor.execute("PRAGMA table_info(articles)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'mosaic_position' not in columns:
                recommendations.append("📍 Ejecutar sistema de posicionamiento inteligente")
            else:
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM articles 
                    WHERE image_url IS NOT NULL 
                    AND (mosaic_position IS NULL OR mosaic_position = '')
                """)
                
                unpositioned = cursor.fetchone()[0]
                if unpositioned > 0:
                    recommendations.append(f"📍 Asignar posiciones a {unpositioned} artículos")
            
            if recommendations:
                for i, rec in enumerate(recommendations, 1):
                    print(f"{i}. {rec}")
            else:
                print("✅ Todo el sistema está optimizado correctamente")
                
    except Exception as e:
        print(f"❌ Error generando recomendaciones: {e}")

def main():
    """Función principal"""
    print("🎯 SISTEMA DE ANÁLISIS DE IMÁGENES - REPORTE COMPLETO")
    print("=" * 60)
    print(f"📅 Fecha: {os.popen('date /t').read().strip()}")
    print(f"🕒 Hora: {os.popen('time /t').read().strip()}")
    print()
    
    # Ejecutar análisis
    check_image_quality()
    check_duplicate_candidates()
    check_mosaic_positioning()
    generate_recommendations()
    
    print("\n" + "=" * 60)
    print("📋 ANÁLISIS COMPLETADO")
    print("💡 Ejecute 'python optimize_image_positioning.py' para aplicar optimizaciones")
    print("=" * 60)

if __name__ == "__main__":
    main()
