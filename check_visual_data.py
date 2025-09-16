#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar datos de análisis visual en la base de datos
"""

import sqlite3
import os
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
    
    # Artículos con detected_objects
    cursor.execute('SELECT COUNT(*) FROM articles WHERE detected_objects IS NOT NULL AND detected_objects != ""')
    objects_count = cursor.fetchone()[0]
    print(f'🔍 Artículos con detected_objects: {objects_count}')
    
    # Ejemplos de visual_analysis_json
    cursor.execute('SELECT id, title, visual_analysis_json FROM articles WHERE visual_analysis_json IS NOT NULL AND visual_analysis_json != "" LIMIT 3')
    examples = cursor.fetchall()
    
    print(f'\n🔍 Ejemplos de análisis visual:')
    for example in examples:
        print(f'\nID: {example[0]}')
        print(f'Título: {example[1][:60]}...')
        print(f'Visual analysis: {example[2][:100]}...')
    
    # Verificar el progreso del script analyze_all_images
    print(f'\n🚀 Estado del análisis CV en progreso:')
    
    # También revisar si hay una columna cv_analysis en otras tablas
    cursor.execute("PRAGMA table_info(articles)")
    columns = cursor.fetchall()
    print(f'\n📋 Columnas disponibles en articles:')
    for col in columns:
        if 'visual' in col[1].lower() or 'cv' in col[1].lower() or 'analysis' in col[1].lower():
            print(f'   - {col[1]} ({col[2]})')
    
    conn.close()

if __name__ == "__main__":
    main()
