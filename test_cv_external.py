#!/usr/bin/env python3
"""
Script para probar el análisis de computer vision con artículos específicos
"""

import sys
import os
import sqlite3
import logging
import json
from datetime import datetime

# Añadir el patch de compatibilidad
sys.path.insert(0, os.path.dirname(__file__))

try:
    import ml_dtypes_patch
    print("🔧 Patch ml_dtypes aplicado correctamente")
except ImportError as e:
    print(f"⚠️ No se pudo cargar patch ml_dtypes: {e}")

def test_cv_with_external_images():
    """Probar CV con imágenes externas"""
    try:
        from src.vision.image_analysis import ImageInterestAnalyzer, analyze_article_image
        print("✅ Computer Vision module imported successfully")
        
        # Obtener artículos con URLs externas
        conn = sqlite3.connect('data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, image_url 
            FROM articles 
            WHERE image_url LIKE 'http%' 
            AND visual_analysis_json IS NULL 
            LIMIT 3
        """)
        
        articles = cursor.fetchall()
        
        for article_id, title, image_url in articles:
            print(f"\n🔍 Analizando artículo {article_id}: {title[:50]}...")
            print(f"🖼️ Imagen: {image_url}")
            
            # Realizar análisis
            analysis_result = analyze_article_image(image_url, title)
            
            if analysis_result and 'error' not in analysis_result:
                print(f"✅ Análisis exitoso!")
                
                # Mostrar información clave
                if 'positioning_recommendation' in analysis_result:
                    positioning = analysis_result['positioning_recommendation']
                    print(f"📍 Posicionamiento recomendado: {positioning}")
                
                if 'interest_areas' in analysis_result:
                    areas = analysis_result['interest_areas']
                    print(f"🎯 Áreas de interés encontradas: {len(areas)}")
                    for i, area in enumerate(areas[:3]):  # Mostrar primeras 3
                        print(f"   - Área {i+1}: {area}")
                
                if 'composition_analysis' in analysis_result:
                    composition = analysis_result['composition_analysis']
                    print(f"🎨 Análisis de composición: {composition}")
                
                # Guardar en BD
                cursor.execute("""
                    UPDATE articles 
                    SET visual_risk_score = ?,
                        detected_objects = ?,
                        visual_analysis_json = ?,
                        visual_analysis_timestamp = ?
                    WHERE id = ?
                """, (
                    analysis_result.get('risk_score', 0.0),
                    json.dumps(analysis_result.get('detected_objects', [])),
                    json.dumps(analysis_result),
                    datetime.now().isoformat(),
                    article_id
                ))
                
                conn.commit()
                print(f"💾 Análisis guardado en BD")
                
            else:
                print(f"❌ Error en análisis: {analysis_result}")
        
        conn.close()
        print(f"\n🎉 Prueba completada!")
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")

if __name__ == "__main__":
    test_cv_with_external_images()
