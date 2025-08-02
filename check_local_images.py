#!/usr/bin/env python3
"""
Script para verificar el estado de las imágenes locales en la base de datos
"""

import sqlite3
import os
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables de entorno
load_dotenv()

def get_database_path():
    """Obtener ruta de la base de datos desde variables de entorno"""
    database_url = os.getenv('DATABASE_URL', 'sqlite:///data/geopolitical_intel.db')
    if database_url.startswith('sqlite:///'):
        return database_url.replace('sqlite:///', '')
    return database_url

def check_local_images_status():
    """Verificar el estado de las imágenes locales"""
    db_path = get_database_path()
    print(f'🔗 Base de datos: {db_path}')
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Total de artículos
        cursor.execute('SELECT COUNT(*) FROM articles')
        total = cursor.fetchone()[0]
        print(f'📈 Total de artículos: {total}')
        
        # Artículos con imágenes locales
        cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE image_url IS NOT NULL 
            AND image_url != '' 
            AND image_url NOT LIKE 'http%'
            AND image_url NOT LIKE '%placeholder%'
            AND image_url NOT LIKE '%picsum%'
        """)
        local_images = cursor.fetchone()[0]
        print(f'📁 Artículos con imágenes locales: {local_images}')
        
        # Imágenes locales sin análisis
        cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE image_url IS NOT NULL 
            AND image_url != '' 
            AND image_url NOT LIKE 'http%'
            AND image_url NOT LIKE '%placeholder%'
            AND image_url NOT LIKE '%picsum%'
            AND (visual_analysis_json IS NULL OR visual_analysis_json = '')
        """)
        local_without_analysis = cursor.fetchone()[0]
        print(f'🔍 Imágenes locales SIN análisis CV: {local_without_analysis}')
        
        # Imágenes locales CON análisis
        local_with_analysis = local_images - local_without_analysis
        print(f'✅ Imágenes locales CON análisis CV: {local_with_analysis}')
        
        # Porcentaje de cobertura local
        if local_images > 0:
            coverage = (local_with_analysis / local_images) * 100
            print(f'📊 Cobertura análisis imágenes locales: {coverage:.1f}%')
        
        # Imágenes externas
        cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE image_url LIKE 'http%'
        """)
        external_images = cursor.fetchone()[0]
        print(f'🌐 Artículos con imágenes externas: {external_images}')
        
        # Imágenes externas con análisis
        cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE image_url LIKE 'http%'
            AND visual_analysis_json IS NOT NULL 
            AND visual_analysis_json != ''
        """)
        external_with_analysis = cursor.fetchone()[0]
        print(f'✅ Imágenes externas CON análisis CV: {external_with_analysis}')
        
        # Ejemplos de rutas locales
        print(f'\n📂 Ejemplos de rutas de imágenes locales:')
        cursor.execute("""
            SELECT image_url FROM articles 
            WHERE image_url IS NOT NULL 
            AND image_url != '' 
            AND image_url NOT LIKE 'http%'
            AND image_url NOT LIKE '%placeholder%'
            AND image_url NOT LIKE '%picsum%'
            LIMIT 5
        """)
        examples = cursor.fetchall()
        for i, (url,) in enumerate(examples, 1):
            print(f'  {i}. {url}')
            
            # Verificar si el archivo existe
            if url.startswith('static/images/'):
                base_path = Path(__file__).parent
                full_path = base_path / url
                exists = "✅" if full_path.exists() else "❌"
                print(f'     {exists} Existe: {full_path}')
        
        print(f'\n🎯 RESUMEN:')
        print(f'   - Total artículos: {total}')
        print(f'   - Imágenes locales pendientes: {local_without_analysis}')
        print(f'   - Imágenes externas con análisis: {external_with_analysis}')
        print(f'   - Total con análisis CV: {local_with_analysis + external_with_analysis}')

if __name__ == "__main__":
    check_local_images_status()
