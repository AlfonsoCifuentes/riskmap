#!/usr/bin/env python3
"""
Script para verificar ejemplos específicos de análisis CV de imágenes locales
"""

import sqlite3
import os
import json
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def get_database_path():
    """Obtener ruta de la base de datos desde variables de entorno"""
    database_url = os.getenv('DATABASE_URL', 'sqlite:///data/geopolitical_intel.db')
    if database_url.startswith('sqlite:///'):
        return database_url.replace('sqlite:///', '')
    return database_url

def check_local_analysis_examples():
    """Verificar ejemplos específicos de análisis CV de imágenes locales"""
    db_path = get_database_path()
    print(f'🔗 Base de datos: {db_path}')
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        print('\n🔍 EJEMPLOS DE ANÁLISIS CV DE IMÁGENES LOCALES:')
        print('=' * 80)
        
        # Obtener ejemplos recientes de imágenes locales con análisis
        cursor.execute("""
            SELECT id, title, image_url, visual_analysis_json, visual_risk_score, 
                   visual_analysis_timestamp
            FROM articles 
            WHERE image_url IS NOT NULL 
            AND image_url NOT LIKE 'http%'
            AND visual_analysis_json IS NOT NULL 
            AND visual_analysis_json != ''
            ORDER BY visual_analysis_timestamp DESC
            LIMIT 5
        """)
        
        examples = cursor.fetchall()
        
        for i, (article_id, title, image_url, visual_json, risk_score, timestamp) in enumerate(examples, 1):
            print(f'\n📰 EJEMPLO {i}:')
            print(f'   ID: {article_id}')
            print(f'   Título: {title[:60]}...')
            print(f'   Imagen: {image_url}')
            print(f'   Risk Score: {risk_score}')
            print(f'   Timestamp: {timestamp}')
            
            if visual_json:
                try:
                    analysis = json.loads(visual_json)
                    
                    # Información básica
                    print(f'   📊 Dimensiones: {analysis.get("dimensions", {})}')
                    print(f'   🎯 Calidad: {analysis.get("quality_score", 0):.2f}')
                    
                    # Áreas de interés
                    interest_areas = analysis.get('interest_areas', [])
                    print(f'   👁️ Áreas de interés: {len(interest_areas)}')
                    
                    if interest_areas:
                        for j, area in enumerate(interest_areas[:3]):  # Mostrar solo las primeras 3
                            area_type = area.get('type', 'unknown')
                            confidence = area.get('confidence', 0)
                            importance = area.get('importance', 0)
                            print(f'      {j+1}. {area_type} (conf: {confidence:.2f}, imp: {importance:.2f})')
                    
                    # Posicionamiento
                    positioning = analysis.get('positioning_recommendation', {})
                    mosaic_position = positioning.get('mosaic_position', 'N/A')
                    focal_point = positioning.get('focal_point', {})
                    print(f'   🎪 Posición mosaico: {mosaic_position}')
                    print(f'   📍 Punto focal: x={focal_point.get("x", "N/A")}, y={focal_point.get("y", "N/A")}')
                    
                    # Composición
                    composition = analysis.get('composition_analysis', {})
                    contrast = composition.get('contrast_level', 'N/A')
                    brightness = composition.get('brightness_level', 'N/A')
                    print(f'   🎨 Contraste: {contrast}, Brillo: {brightness}')
                    
                    # Objetos detectados
                    detected_objects = analysis.get('detected_objects', [])
                    if detected_objects:
                        print(f'   🎯 Objetos detectados: {", ".join(detected_objects[:5])}')
                    
                except json.JSONDecodeError:
                    print(f'   ❌ Error: JSON de análisis inválido')
            
            print('-' * 80)
        
        # Estadísticas de calidad
        print(f'\n📈 ESTADÍSTICAS DE CALIDAD:')
        cursor.execute("""
            SELECT 
                AVG(visual_risk_score) as avg_risk,
                MIN(visual_risk_score) as min_risk,
                MAX(visual_risk_score) as max_risk,
                COUNT(*) as total_analyzed
            FROM articles 
            WHERE image_url NOT LIKE 'http%'
            AND visual_analysis_json IS NOT NULL 
            AND visual_analysis_json != ''
        """)
        
        stats = cursor.fetchone()
        if stats:
            avg_risk, min_risk, max_risk, total = stats
            print(f'   Total analizadas: {total}')
            print(f'   Risk Score promedio: {avg_risk:.3f}')
            print(f'   Risk Score mínimo: {min_risk:.3f}')
            print(f'   Risk Score máximo: {max_risk:.3f}')
        
        # Distribución de calidad
        cursor.execute("""
            SELECT visual_analysis_json
            FROM articles 
            WHERE image_url NOT LIKE 'http%'
            AND visual_analysis_json IS NOT NULL 
            AND visual_analysis_json != ''
        """)
        
        quality_scores = []
        interest_area_counts = []
        mosaic_positions = []
        
        for (visual_json,) in cursor.fetchall():
            try:
                analysis = json.loads(visual_json)
                quality_scores.append(analysis.get('quality_score', 0))
                interest_area_counts.append(len(analysis.get('interest_areas', [])))
                positioning = analysis.get('positioning_recommendation', {})
                mosaic_pos = positioning.get('mosaic_position', 'unknown')
                mosaic_positions.append(mosaic_pos)
            except:
                continue
        
        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            avg_interest_areas = sum(interest_area_counts) / len(interest_area_counts)
            print(f'   Calidad promedio: {avg_quality:.3f}')
            print(f'   Áreas de interés promedio: {avg_interest_areas:.1f}')
            
            # Distribución de posiciones de mosaico
            from collections import Counter
            position_counts = Counter(mosaic_positions)
            print(f'   Posiciones mosaico:')
            for position, count in position_counts.most_common(5):
                print(f'      {position}: {count}')

if __name__ == "__main__":
    check_local_analysis_examples()
