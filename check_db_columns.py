#!/usr/bin/env python3
"""
Verificar el estado de las columnas de la base de datos
"""

import sqlite3
from pathlib import Path

def check_database_status():
    """Verificar estado de las columnas en la base de datos"""
    
    db_path = Path('data/geopolitical_intel.db')
    if not db_path.exists():
        print("❌ Base de datos no encontrada")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print("📊 ESTADO DE LA BASE DE DATOS")
    print("=" * 50)
    
    # Total de artículos
    cursor.execute('SELECT COUNT(*) FROM articles')
    total_articles = cursor.fetchone()[0]
    print(f"📰 Total de artículos: {total_articles}")
    
    # Artículos con imágenes
    cursor.execute('SELECT COUNT(*) FROM articles WHERE image_url IS NOT NULL AND image_url != ""')
    with_images = cursor.fetchone()[0]
    print(f"🖼️ Artículos con imagen: {with_images}")
    
    # Columnas críticas de análisis visual
    columns_to_check = [
        ('quality_score', 'Puntuación de calidad'),
        ('mosaic_position', 'Posición en mosaico'), 
        ('cv_quality_score', 'Puntuación CV'),
        ('positioning_score', 'Puntuación de posicionamiento'),
        ('image_width', 'Ancho de imagen'),
        ('image_height', 'Alto de imagen'),
        ('dominant_colors', 'Colores dominantes'),
        ('has_faces', 'Detección de caras'),
        ('detected_objects', 'Objetos detectados'),
        ('visual_analysis_json', 'Análisis visual JSON'),
        ('visual_risk_score', 'Puntuación de riesgo visual')
    ]
    
    print("\n🔍 ESTADO DE COLUMNAS DE ANÁLISIS VISUAL:")
    print("-" * 50)
    
    for column, description in columns_to_check:
        cursor.execute(f'SELECT COUNT(*) FROM articles WHERE {column} IS NULL')
        null_count = cursor.fetchone()[0]
        filled_count = total_articles - null_count
        percentage = (filled_count / total_articles * 100) if total_articles > 0 else 0
        
        status = "✅" if percentage > 80 else "⚠️" if percentage > 20 else "❌"
        print(f"{status} {description}: {filled_count}/{total_articles} ({percentage:.1f}%)")
    
    # Los 150 artículos más recientes
    print("\n📅 ANÁLISIS DE LOS 150 ARTÍCULOS MÁS RECIENTES:")
    print("-" * 50)
    
    cursor.execute('''
        SELECT COUNT(*) FROM (
            SELECT * FROM articles 
            ORDER BY created_at DESC 
            LIMIT 150
        ) WHERE image_url IS NOT NULL AND image_url != ""
    ''')
    recent_with_images = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COUNT(*) FROM (
            SELECT * FROM articles 
            ORDER BY created_at DESC 
            LIMIT 150
        ) WHERE quality_score IS NOT NULL
    ''')
    recent_with_quality = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COUNT(*) FROM (
            SELECT * FROM articles 
            ORDER BY created_at DESC 
            LIMIT 150
        ) WHERE cv_quality_score IS NOT NULL
    ''')
    recent_with_cv = cursor.fetchone()[0]
    
    print(f"🖼️ Con imagen: {recent_with_images}/150 ({recent_with_images/150*100:.1f}%)")
    print(f"⭐ Con quality_score: {recent_with_quality}/150 ({recent_with_quality/150*100:.1f}%)")
    print(f"🤖 Con cv_quality_score: {recent_with_cv}/150 ({recent_with_cv/150*100:.1f}%)")
    
    # Obtener algunos ejemplos de artículos recientes sin procesar
    cursor.execute('''
        SELECT id, title, image_url, quality_score, cv_quality_score, mosaic_position
        FROM articles 
        ORDER BY created_at DESC 
        LIMIT 10
    ''')
    
    print("\n📋 MUESTRA DE LOS 10 ARTÍCULOS MÁS RECIENTES:")
    print("-" * 50)
    
    for row in cursor.fetchall():
        article_id, title, image_url, quality_score, cv_quality_score, mosaic_position = row
        has_image = "✅" if image_url else "❌"
        has_quality = "✅" if quality_score else "❌"
        has_cv = "✅" if cv_quality_score else "❌"
        has_position = "✅" if mosaic_position else "❌"
        
        print(f"ID {article_id}: {title[:40]}...")
        print(f"  Imagen: {has_image}  Quality: {has_quality}  CV: {has_cv}  Position: {has_position}")
    
    conn.close()

if __name__ == '__main__':
    check_database_status()
