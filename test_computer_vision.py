#!/usr/bin/env python3
"""
Script de demostración para el sistema de Computer Vision integrado en RiskMap
Muestra cómo el sistema analiza imágenes y optimiza su posicionamiento en el mosaico
"""

import json
import time
import sqlite3
from pathlib import Path

def get_database_path():
    """Obtener la ruta de la base de datos desde el archivo .env"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    return os.getenv('DATABASE_PATH', 'geopolitical_analysis.db')

def test_computer_vision_integration():
    """Probar la integración completa del sistema de computer vision"""
    print("🔍 SISTEMA DE COMPUTER VISION - RISKMAP")
    print("=" * 50)
    
    try:
        # Verificar instalación de dependencias CV
        import cv2
        import numpy as np
        from PIL import Image
        from sklearn.cluster import KMeans
        print("✅ Dependencias de Computer Vision instaladas correctamente")
        
        # Importar módulo de análisis
        from src.vision.image_analysis import ImageInterestAnalyzer
        analyzer = ImageInterestAnalyzer()
        print("✅ Módulo de análisis de imágenes cargado")
        
    except ImportError as e:
        print(f"❌ Error importando dependencias CV: {e}")
        print("💡 Instale las dependencias con: pip install opencv-python pillow scikit-learn")
        return False
    
    # Verificar base de datos
    db_path = get_database_path()
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM articles WHERE image_url IS NOT NULL")
            articles_with_images = cursor.fetchone()[0]
            print(f"📊 Artículos con imágenes en BD: {articles_with_images}")
            
            # Obtener algunos artículos para demo
            cursor.execute("""
                SELECT id, title, image_url 
                FROM articles 
                WHERE image_url IS NOT NULL 
                LIMIT 5
            """)
            demo_articles = cursor.fetchall()
            
    except Exception as e:
        print(f"❌ Error accediendo a base de datos: {e}")
        return False
    
    if not demo_articles:
        print("⚠️ No hay artículos con imágenes para demostrar")
        return False
    
    print(f"\n🎯 DEMOSTRANDO ANÁLISIS CV EN {len(demo_articles)} ARTÍCULOS")
    print("-" * 50)
    
    # Analizar cada artículo
    for i, (article_id, title, image_url) in enumerate(demo_articles, 1):
        print(f"\n📰 [{i}] {title[:60]}...")
        print(f"🔗 URL: {image_url}")
        
        try:
            # Realizar análisis CV
            print("🔍 Analizando imagen...")
            start_time = time.time()
            
            analysis = analyzer.analyze_image_interest_areas(image_url, title)
            
            analysis_time = time.time() - start_time
            print(f"⏱️ Tiempo de análisis: {analysis_time:.2f}s")
            
            if analysis.get('error'):
                print(f"❌ Error: {analysis['error']}")
                continue
            
            # Mostrar resultados
            quality_score = analysis.get('quality_score', 0)
            positioning = analysis.get('positioning_recommendation', {})
            
            print(f"✨ Calidad de imagen: {quality_score:.2f}/1.0 ({quality_score*100:.0f}%)")
            print(f"📍 Posición recomendada: {positioning.get('position', 'center')}")
            print(f"🎯 Razón: {positioning.get('reason', 'N/A')}")
            
            # Mostrar áreas de interés encontradas
            if 'interest_areas' in analysis:
                areas = analysis['interest_areas']
                print(f"🔍 Áreas de interés detectadas: {len(areas)}")
                for j, area in enumerate(areas[:3], 1):  # Mostrar máximo 3
                    x, y, w, h = area['bbox']
                    conf = area['confidence']
                    print(f"   [{j}] Región ({x},{y}) {w}x{h} - Confianza: {conf:.2f}")
            
        except Exception as e:
            print(f"❌ Error procesando artículo {article_id}: {e}")
    
    # Verificar tabla de análisis
    print(f"\n📊 ESTADO DE LA BASE DE DATOS")
    print("-" * 30)
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Verificar si existe tabla de análisis
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='image_analysis'
            """)
            
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM image_analysis")
                analysis_count = cursor.fetchone()[0]
                print(f"✅ Análisis CV guardados: {analysis_count}")
                
                # Mostrar estadísticas
                cursor.execute("""
                    SELECT 
                        AVG(quality_score) as avg_quality,
                        MIN(quality_score) as min_quality,
                        MAX(quality_score) as max_quality
                    FROM image_analysis
                """)
                stats = cursor.fetchone()
                if stats[0]:
                    print(f"📈 Calidad promedio: {stats[0]:.2f}")
                    print(f"📉 Rango: {stats[1]:.2f} - {stats[2]:.2f}")
            else:
                print("⚠️ Tabla de análisis CV no existe aún")
                
    except Exception as e:
        print(f"❌ Error verificando BD: {e}")
    
    print(f"\n🎉 DEMOSTRACIÓN COMPLETADA")
    print("=" * 50)
    print("💡 El sistema de Computer Vision está integrado y funcionando")
    print("🌐 Las imágenes del mosaico serán optimizadas automáticamente")
    print("📊 Los indicadores de calidad aparecerán en el dashboard")
    
    return True

def show_api_endpoints():
    """Mostrar los endpoints de API disponibles para computer vision"""
    print("\n🚀 ENDPOINTS DE API DISPONIBLES")
    print("=" * 40)
    
    endpoints = [
        {
            "method": "POST",
            "url": "/api/vision/analyze-image",
            "description": "Analizar una imagen específica",
            "params": "image_url, title (opcional)"
        },
        {
            "method": "POST", 
            "url": "/api/vision/analyze-article-images",
            "description": "Analizar imágenes de múltiples artículos",
            "params": "article_ids (lista)"
        },
        {
            "method": "GET",
            "url": "/api/vision/get-analysis/<id>", 
            "description": "Obtener análisis CV de un artículo",
            "params": "id del artículo"
        },
        {
            "method": "GET",
            "url": "/api/vision/mosaic-positioning",
            "description": "Obtener recomendaciones de posicionamiento para mosaico",
            "params": "limit (opcional)"
        }
    ]
    
    for endpoint in endpoints:
        print(f"📡 {endpoint['method']} {endpoint['url']}")
        print(f"   📝 {endpoint['description']}")
        print(f"   📋 Parámetros: {endpoint['params']}")
        print()

if __name__ == "__main__":
    print("🚀 INICIANDO PRUEBA DEL SISTEMA DE COMPUTER VISION")
    print()
    
    success = test_computer_vision_integration()
    
    if success:
        show_api_endpoints()
        print("\n✅ Sistema listo para usar!")
        print("🌐 Abra el dashboard para ver las optimizaciones en acción")
    else:
        print("\n❌ Sistema necesita configuración adicional")
        print("💡 Revise la instalación de dependencias y configuración de BD")
