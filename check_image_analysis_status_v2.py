#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar el estado del análisis de imágenes y el sistema de posicionamiento inteligente
"""

import sqlite3
import json
import logging
from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_path():
    """Obtener la ruta de la base de datos desde las variables de entorno"""
    db_path = os.getenv('DATABASE_PATH', 'data/riskmap.db')
    return Path(db_path)

def check_image_quality():
    """Verificar la calidad de las imágenes en la base de datos"""
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
                    COUNT(CASE WHEN cv_quality_score IS NOT NULL THEN 1 END) as with_cv_score,
                    AVG(CASE WHEN cv_quality_score IS NOT NULL 
                        THEN cv_quality_score 
                        END) as avg_quality
                FROM articles 
                WHERE image_url IS NOT NULL AND image_url != ''
            """)
            
            stats = cursor.fetchone()
            total_with_images, with_analysis, with_cv_score, avg_quality = stats
            
            print(f"📊 Total artículos con imágenes: {total_with_images}")
            print(f"📈 Con análisis visual: {with_analysis}")
            print(f"🎯 Con puntuación CV: {with_cv_score}")
            if avg_quality:
                print(f"🔧 Calidad promedio: {avg_quality:.3f}")
            else:
                print("🔧 Calidad promedio: No disponible")
            
            if total_with_images > 0:
                coverage = (with_analysis/total_with_images*100)
                print(f"📋 Cobertura de análisis: {coverage:.1f}%")
            
            # Distribución de calidad
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN cv_quality_score < 0.5 THEN 1 END) as low_quality,
                    COUNT(CASE WHEN cv_quality_score >= 0.5 AND cv_quality_score < 0.7 THEN 1 END) as medium_quality,
                    COUNT(CASE WHEN cv_quality_score >= 0.7 THEN 1 END) as high_quality
                FROM articles 
                WHERE cv_quality_score IS NOT NULL
            """)
            
            quality_dist = cursor.fetchone()
            if quality_dist:
                low, medium, high = quality_dist
                print(f"\n📊 Distribución de calidad:")
                print(f"   🔴 Baja calidad (<0.5): {low}")
                print(f"   🟡 Calidad media (0.5-0.7): {medium}")
                print(f"   🟢 Alta calidad (>0.7): {high}")
            
            # Mostrar algunos ejemplos de baja calidad
            cursor.execute("""
                SELECT id, title, cv_quality_score, image_width, image_height
                FROM articles 
                WHERE cv_quality_score IS NOT NULL 
                AND cv_quality_score < 0.6
                ORDER BY cv_quality_score ASC
                LIMIT 5
            """)
            
            low_quality_examples = cursor.fetchall()
            if low_quality_examples:
                print(f"\n🔻 EJEMPLOS DE BAJA CALIDAD:")
                print("-" * 50)
                for article in low_quality_examples:
                    article_id, title, quality, width, height = article
                    print(f"   ID: {article_id} | Calidad: {quality:.3f} | {width}x{height} | {title[:50]}...")
            
    except Exception as e:
        print(f"❌ Error verificando calidad de imágenes: {e}")

def check_duplicates():
    """Verificar imágenes duplicadas"""
    print("\n🔄 ANÁLISIS DE POSIBLES DUPLICADOS")
    print("=" * 50)
    
    db_path = get_database_path()
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Verificar duplicados usando image_fingerprint
            cursor.execute("""
                SELECT image_fingerprint, COUNT(*) as count,
                       GROUP_CONCAT(id) as article_ids,
                       GROUP_CONCAT(title, ' | ') as titles
                FROM articles 
                WHERE image_fingerprint IS NOT NULL 
                AND image_fingerprint != ''
                GROUP BY image_fingerprint
                HAVING COUNT(*) > 1
                ORDER BY count DESC
                LIMIT 10
            """)
            
            duplicates = cursor.fetchall()
            
            if duplicates:
                print(f"⚠️ Se encontraron {len(duplicates)} grupos de imágenes duplicadas:")
                print("-" * 70)
                
                for dup in duplicates:
                    fingerprint, count, article_ids, titles = dup
                    print(f"🔗 Fingerprint: {fingerprint[:16]}...")
                    print(f"   📊 Artículos afectados: {count}")
                    print(f"   🆔 IDs: {article_ids}")
                    print(f"   📰 Títulos: {titles[:100]}...")
                    print()
            else:
                print("✅ No se encontraron imágenes duplicadas")
                
            # Verificar artículos sin fingerprint
            cursor.execute("""
                SELECT COUNT(*) 
                FROM articles 
                WHERE image_url IS NOT NULL 
                AND image_url != ''
                AND (image_fingerprint IS NULL OR image_fingerprint = '')
            """)
            
            no_fingerprint = cursor.fetchone()[0]
            if no_fingerprint > 0:
                print(f"⚠️ {no_fingerprint} artículos con imagen sin fingerprint")
                
    except Exception as e:
        print(f"❌ Error verificando duplicados: {e}")

def check_mosaic_positioning():
    """Verificar el posicionamiento en mosaico"""
    print("\n📍 ANÁLISIS DE POSICIONAMIENTO EN MOSAICO")
    print("=" * 50)
    
    db_path = get_database_path()
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Verificar distribución de posiciones
            cursor.execute("""
                SELECT 
                    mosaic_position,
                    COUNT(*) as count
                FROM articles 
                WHERE mosaic_position IS NOT NULL 
                AND mosaic_position != ''
                GROUP BY mosaic_position
                ORDER BY count DESC
            """)
            
            positions = cursor.fetchall()
            
            if positions:
                print("📊 Distribución de posiciones del mosaico:")
                print("-" * 40)
                
                total_positioned = sum(pos[1] for pos in positions)
                
                for position, count in positions:
                    percentage = (count / total_positioned * 100) if total_positioned > 0 else 0
                    print(f"   {position:15} | {count:4} artículos ({percentage:.1f}%)")
                
                # Verificar artículos sin posición asignada
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM articles 
                    WHERE image_url IS NOT NULL 
                    AND image_url != ''
                    AND (mosaic_position IS NULL OR mosaic_position = '')
                """)
                
                no_position = cursor.fetchone()[0]
                print(f"\n⚠️ {no_position} artículos con imagen sin posición asignada")
                
                # Mostrar artículos con mejor puntuación para posicionamiento
                cursor.execute("""
                    SELECT id, title, positioning_score, mosaic_position, cv_quality_score
                    FROM articles 
                    WHERE positioning_score IS NOT NULL
                    ORDER BY positioning_score DESC
                    LIMIT 5
                """)
                
                top_positioned = cursor.fetchall()
                if top_positioned:
                    print(f"\n🌟 TOP 5 ARTÍCULOS PARA POSICIONAMIENTO:")
                    print("-" * 60)
                    for article in top_positioned:
                        article_id, title, p_score, position, quality = article
                        print(f"   ID: {article_id} | Score: {p_score:.3f} | Pos: {position} | Q: {quality:.3f}")
                        print(f"       {title[:60]}...")
                        print()
            else:
                print("⚠️ No hay artículos con posiciones de mosaico asignadas")
                
    except Exception as e:
        print(f"❌ Error verificando posicionamiento: {e}")

def generate_recommendations():
    """Generar recomendaciones para optimizar el sistema"""
    print("\n💡 RECOMENDACIONES")
    print("=" * 50)
    
    db_path = get_database_path()
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            recommendations = []
            
            # Verificar artículos sin análisis CV
            cursor.execute("""
                SELECT COUNT(*) 
                FROM articles 
                WHERE image_url IS NOT NULL 
                AND image_url != ''
                AND visual_analysis_json IS NULL
            """)
            
            no_analysis = cursor.fetchone()[0]
            if no_analysis > 0:
                recommendations.append(f"🔍 Analizar {no_analysis} artículos sin análisis CV")
            
            # Verificar artículos sin fingerprint
            cursor.execute("""
                SELECT COUNT(*) 
                FROM articles 
                WHERE image_url IS NOT NULL 
                AND image_url != ''
                AND (image_fingerprint IS NULL OR image_fingerprint = '')
            """)
            
            no_fingerprint = cursor.fetchone()[0]
            if no_fingerprint > 0:
                recommendations.append(f"🔗 Generar fingerprints para {no_fingerprint} imágenes")
            
            # Verificar imágenes de baja calidad
            cursor.execute("""
                SELECT COUNT(*) 
                FROM articles 
                WHERE cv_quality_score IS NOT NULL 
                AND cv_quality_score < 0.5
            """)
            
            low_quality = cursor.fetchone()[0]
            if low_quality > 0:
                recommendations.append(f"📈 Mejorar {low_quality} imágenes de baja calidad")
            
            # Verificar artículos sin posición
            cursor.execute("""
                SELECT COUNT(*) 
                FROM articles 
                WHERE image_url IS NOT NULL 
                AND image_url != ''
                AND (mosaic_position IS NULL OR mosaic_position = '')
            """)
            
            no_position = cursor.fetchone()[0]
            if no_position > 0:
                recommendations.append(f"📍 Asignar posiciones para {no_position} artículos")
            
            if recommendations:
                for i, rec in enumerate(recommendations, 1):
                    print(f"{i}. {rec}")
            else:
                print("✅ El sistema está optimizado. No se requieren acciones adicionales.")
                
    except Exception as e:
        print(f"❌ Error generando recomendaciones: {e}")

def main():
    """Función principal"""
    print("🎯 SISTEMA DE ANÁLISIS DE IMÁGENES - REPORTE COMPLETO")
    print("=" * 60)
    print(f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y')}")
    print(f"🕒 Hora: {datetime.now().strftime('%H:%M')}")
    print()
    
    # Ejecutar análisis
    check_image_quality()
    check_duplicates()
    check_mosaic_positioning()
    generate_recommendations()
    
    print("=" * 60)
    print("📋 ANÁLISIS COMPLETADO")
    print("💡 Ejecute 'python optimize_image_positioning.py' para aplicar optimizaciones")
    print("=" * 60)

if __name__ == "__main__":
    main()
