#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar análisis CV recientes
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def get_database_path():
    """Obtener la ruta de la base de datos desde variables de entorno"""
    database_url = os.getenv('DATABASE_URL', 'sqlite:///data/geopolitical_intel.db')
    if database_url.startswith('sqlite:///'):
        return database_url.replace('sqlite:///', '')
    return database_url

def main():
    db_path = get_database_path()
    print(f'🔗 Base de datos: {db_path}')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Total de artículos
    cursor.execute('SELECT COUNT(*) FROM articles')
    total = cursor.fetchone()[0]
    print(f'📈 Total de artículos: {total}')
    
    # Artículos con visual_analysis_json
    cursor.execute('SELECT COUNT(*) FROM articles WHERE visual_analysis_json IS NOT NULL AND visual_analysis_json != ""')
    visual_count = cursor.fetchone()[0]
    print(f'👁️ Artículos con visual_analysis_json: {visual_count}')
    
    # Análisis creados en las últimas 2 horas
    cutoff_time = (datetime.now() - timedelta(hours=2)).isoformat()
    cursor.execute('''
        SELECT COUNT(*) FROM articles 
        WHERE visual_analysis_timestamp IS NOT NULL 
        AND visual_analysis_timestamp > ?
    ''', (cutoff_time,))
    recent_count = cursor.fetchone()[0]
    print(f'🕒 Análisis creados en las últimas 2 horas: {recent_count}')
    
    # Ejemplos recientes con análisis real
    cursor.execute('''
        SELECT id, title, image_url, visual_analysis_json, visual_analysis_timestamp
        FROM articles 
        WHERE visual_analysis_json IS NOT NULL 
        AND visual_analysis_json != ""
        AND visual_analysis_timestamp > ?
        ORDER BY visual_analysis_timestamp DESC
        LIMIT 5
    ''', (cutoff_time,))
    
    recent_analyses = cursor.fetchall()
    print(f'\n🔍 Análisis recientes (últimas 2 horas):')
    
    for analysis in recent_analyses:
        article_id, title, image_url, visual_json, timestamp = analysis
        print(f'\nID: {article_id}')
        print(f'Título: {title[:60]}...')
        print(f'URL imagen: {image_url[:80]}...')
        print(f'Timestamp: {timestamp}')
        
        if visual_json:
            try:
                visual_data = json.loads(visual_json)
                interest_areas = visual_data.get('interest_areas', [])
                mosaic_position = visual_data.get('mosaic_position', 'N/A')
                quality_score = visual_data.get('quality_score', 0)
                print(f'Áreas de interés: {len(interest_areas)}')
                print(f'Posición mosaico: {mosaic_position}')
                print(f'Calidad: {quality_score}')
            except:
                print(f'JSON inválido')
        print('-' * 60)
    
    # URLs que fallaron (locales)
    cursor.execute('''
        SELECT COUNT(*) FROM articles 
        WHERE image_url LIKE 'static/images/%'
    ''')
    local_images = cursor.fetchone()[0]
    print(f'\n📁 Imágenes con URLs locales: {local_images}')
    
    # URLs externas exitosas
    cursor.execute('''
        SELECT COUNT(*) FROM articles 
        WHERE image_url LIKE 'http%'
        AND visual_analysis_json IS NOT NULL 
        AND visual_analysis_json != ""
    ''')
    external_success = cursor.fetchone()[0]
    print(f'🌐 URLs externas con análisis exitoso: {external_success}')
    
    conn.close()

if __name__ == "__main__":
    main()
