#!/usr/bin/env python3
"""
Verificar los resultados del análisis CV completo en los 150 artículos de riesgo medio/alto
"""

import sqlite3
import json
from pathlib import Path

def check_cv_analysis_results():
    """Verificar resultados del análisis CV"""
    
    db_path = Path('data/geopolitical_intel.db')
    if not db_path.exists():
        print("❌ Base de datos no encontrada")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print("🎯 RESULTADOS DEL ANÁLISIS CV COMPLETO")
    print("=" * 70)
    
    # Los 150 artículos más recientes con riesgo medio/alto
    cursor.execute('''
        SELECT id, title, url, image_url, quality_score, cv_quality_score, 
               mosaic_position, positioning_score, visual_risk_score,
               image_width, image_height, dominant_colors, visual_analysis_json
        FROM articles 
        WHERE risk_level IN ('medium', 'high')
        ORDER BY created_at DESC 
        LIMIT 150
    ''')
    
    articles = cursor.fetchall()
    total_articles = len(articles)
    
    print(f"📊 ANÁLISIS DE {total_articles} ARTÍCULOS DE RIESGO MEDIO/ALTO MÁS RECIENTES")
    print("-" * 70)
    
    # Contadores
    with_images = 0
    with_quality_score = 0
    with_cv_score = 0
    with_mosaic_position = 0
    with_positioning_score = 0
    with_visual_risk = 0
    with_dimensions = 0
    with_colors = 0
    with_visual_json = 0
    
    # Análisis de cada campo
    for article in articles:
        (article_id, title, url, image_url, quality_score, cv_quality_score, 
         mosaic_position, positioning_score, visual_risk_score,
         image_width, image_height, dominant_colors, visual_analysis_json) = article
        
        if image_url and image_url.strip():
            with_images += 1
        if quality_score is not None:
            with_quality_score += 1
        if cv_quality_score is not None:
            with_cv_score += 1
        if mosaic_position and mosaic_position.strip():
            with_mosaic_position += 1
        if positioning_score is not None:
            with_positioning_score += 1
        if visual_risk_score is not None:
            with_visual_risk += 1
        if image_width is not None and image_height is not None:
            with_dimensions += 1
        if dominant_colors and dominant_colors.strip() and dominant_colors != '[]':
            with_colors += 1
        if visual_analysis_json and visual_analysis_json.strip():
            with_visual_json += 1
    
    print(f"🖼️ Con imagen asignada: {with_images}/{total_articles} ({with_images/total_articles*100:.1f}%)")
    print(f"⭐ Con quality_score: {with_quality_score}/{total_articles} ({with_quality_score/total_articles*100:.1f}%)")
    print(f"🤖 Con cv_quality_score: {with_cv_score}/{total_articles} ({with_cv_score/total_articles*100:.1f}%)")
    print(f"📐 Con mosaic_position: {with_mosaic_position}/{total_articles} ({with_mosaic_position/total_articles*100:.1f}%)")
    print(f"🎯 Con positioning_score: {with_positioning_score}/{total_articles} ({with_positioning_score/total_articles*100:.1f}%)")
    print(f"⚠️ Con visual_risk_score: {with_visual_risk}/{total_articles} ({with_visual_risk/total_articles*100:.1f}%)")
    print(f"📏 Con dimensiones: {with_dimensions}/{total_articles} ({with_dimensions/total_articles*100:.1f}%)")
    print(f"🎨 Con colores dominantes: {with_colors}/{total_articles} ({with_colors/total_articles*100:.1f}%)")
    print(f"📋 Con análisis visual JSON: {with_visual_json}/{total_articles} ({with_visual_json/total_articles*100:.1f}%)")
    
    # Distribución de quality_score
    print(f"\n📊 DISTRIBUCIÓN DE QUALITY_SCORE:")
    print("-" * 50)
    
    score_ranges = [
        (80, 100, "Excelente"),
        (60, 79, "Buena"),
        (40, 59, "Regular"),
        (20, 39, "Baja"),
        (0, 19, "Muy baja")
    ]
    
    for min_score, max_score, category in score_ranges:
        cursor.execute('''
            SELECT COUNT(*) FROM (
                SELECT * FROM articles 
                WHERE risk_level IN ('medium', 'high')
                ORDER BY created_at DESC 
                LIMIT 150
            ) WHERE quality_score BETWEEN ? AND ?
        ''', (min_score, max_score))
        count = cursor.fetchone()[0]
        print(f"  {category} ({min_score}-{max_score}): {count} artículos")
    
    # Distribución de mosaic_position
    print(f"\n📍 DISTRIBUCIÓN DE POSICIONES EN MOSAICO:")
    print("-" * 50)
    
    positions = ['featured', 'primary', 'secondary', 'background']
    for position in positions:
        cursor.execute('''
            SELECT COUNT(*) FROM (
                SELECT * FROM articles 
                WHERE risk_level IN ('medium', 'high')
                ORDER BY created_at DESC 
                LIMIT 150
            ) WHERE mosaic_position = ?
        ''', (position,))
        count = cursor.fetchone()[0]
        print(f"  {position.capitalize()}: {count} artículos")
    
    # Ejemplos de artículos completamente procesados
    print(f"\n✅ EJEMPLOS DE ARTÍCULOS COMPLETAMENTE PROCESADOS:")
    print("-" * 70)
    
    cursor.execute('''
        SELECT id, title, quality_score, cv_quality_score, mosaic_position, 
               positioning_score, visual_risk_score, image_width, image_height
        FROM articles 
        WHERE risk_level IN ('medium', 'high')
        AND quality_score IS NOT NULL 
        AND cv_quality_score IS NOT NULL
        AND mosaic_position IS NOT NULL
        ORDER BY created_at DESC 
        LIMIT 10
    ''')
    
    complete_articles = cursor.fetchall()
    
    for article in complete_articles:
        (article_id, title, quality_score, cv_quality_score, mosaic_position, 
         positioning_score, visual_risk_score, image_width, image_height) = article
        
        print(f"ID {article_id}: {title[:50]}...")
        print(f"  📊 Quality: {quality_score:.1f} | CV: {cv_quality_score:.1f} | Position: {mosaic_position}")
        print(f"  📐 Pos.Score: {positioning_score:.1f} | Risk: {visual_risk_score:.1f} | Size: {image_width}x{image_height}")
        print()
    
    # Artículos sin imagen que necesitan atención
    print(f"⚠️ ARTÍCULOS SIN IMAGEN QUE REQUIEREN ATENCIÓN:")
    print("-" * 70)
    
    cursor.execute('''
        SELECT id, title, url
        FROM articles 
        WHERE risk_level IN ('medium', 'high')
        AND (image_url IS NULL OR image_url = "")
        ORDER BY created_at DESC 
        LIMIT 10
    ''')
    
    no_image_articles = cursor.fetchall()
    
    for article_id, title, url in no_image_articles:
        print(f"ID {article_id}: {title[:60]}...")
        if url:
            print(f"  URL: {url[:80]}...")
        else:
            print("  ❌ Sin URL - no se puede obtener imagen")
        print()
    
    # Estadísticas finales
    complete_analysis = sum([
        1 for article in articles 
        if all([
            article[4] is not None,  # quality_score
            article[5] is not None,  # cv_quality_score
            article[6] and article[6].strip(),  # mosaic_position
            article[7] is not None,  # positioning_score
            article[8] is not None,  # visual_risk_score
            article[9] is not None and article[10] is not None,  # dimensions
            article[11] and article[11].strip() and article[11] != '[]',  # colors
            article[12] and article[12].strip()  # visual_analysis_json
        ])
    ])
    
    print(f"🎯 RESUMEN FINAL:")
    print("-" * 30)
    print(f"✅ Artículos completamente analizados: {complete_analysis}/{total_articles} ({complete_analysis/total_articles*100:.1f}%)")
    print(f"🖼️ Total con imagen: {with_images}/{total_articles} ({with_images/total_articles*100:.1f}%)")
    print(f"📊 Total con análisis CV: {with_cv_score}/{total_articles} ({with_cv_score/total_articles*100:.1f}%)")
    
    conn.close()

if __name__ == '__main__':
    check_cv_analysis_results()
