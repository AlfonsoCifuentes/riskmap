#!/usr/bin/env python3
"""
Reporte final: verificar que todos los artículos de riesgo medio/alto tienen todas las columnas llenadas
"""

import sqlite3
import json
from pathlib import Path

def final_verification_report():
    """Reporte final de verificación"""
    
    db_path = Path('data/geopolitical_intel.db')
    if not db_path.exists():
        print("❌ Base de datos no encontrada")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print("🎯 REPORTE FINAL DE VERIFICACIÓN")
    print("=" * 80)
    
    # 1. Verificar que todos los artículos tienen nivel de riesgo
    cursor.execute('SELECT COUNT(*) FROM articles WHERE risk_level IS NULL OR risk_level = ""')
    no_risk = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM articles')
    total = cursor.fetchone()[0]
    
    print(f"🛡️ NIVELES DE RIESGO GEOPOLÍTICO:")
    print(f"   ✅ Todos los artículos tienen nivel de riesgo asignado: {total - no_risk}/{total}")
    if no_risk > 0:
        print(f"   ⚠️ {no_risk} artículos sin nivel de riesgo")
    
    # 2. Estado de los 150 artículos de riesgo medio/alto más recientes
    print(f"\n📊 ESTADO DE LOS 150 ARTÍCULOS DE RIESGO MEDIO/ALTO MÁS RECIENTES:")
    print("-" * 80)
    
    # Obtener artículos
    cursor.execute('''
        SELECT COUNT(*) FROM (
            SELECT * FROM articles 
            WHERE risk_level IN ('medium', 'high')
            ORDER BY created_at DESC 
            LIMIT 150
        )
    ''')
    target_articles = cursor.fetchone()[0]
    
    # Verificar cada columna crítica
    critical_columns = [
        ('image_url', 'Imagen asignada'),
        ('quality_score', 'Puntuación de calidad'),
        ('cv_quality_score', 'Puntuación CV'),
        ('mosaic_position', 'Posición en mosaico'),
        ('positioning_score', 'Puntuación de posicionamiento'),
        ('visual_risk_score', 'Puntuación de riesgo visual'),
        ('image_width', 'Ancho de imagen'),
        ('image_height', 'Alto de imagen'),
        ('dominant_colors', 'Colores dominantes'),
        ('visual_analysis_json', 'Análisis visual JSON')
    ]
    
    for column, description in critical_columns:
        if column in ['image_url', 'mosaic_position', 'dominant_colors', 'visual_analysis_json']:
            # Columnas de texto
            cursor.execute(f'''
                SELECT COUNT(*) FROM (
                    SELECT * FROM articles 
                    WHERE risk_level IN ('medium', 'high')
                    ORDER BY created_at DESC 
                    LIMIT 150
                ) WHERE {column} IS NOT NULL AND {column} != "" AND {column} != "[]"
            ''')
        else:
            # Columnas numéricas
            cursor.execute(f'''
                SELECT COUNT(*) FROM (
                    SELECT * FROM articles 
                    WHERE risk_level IN ('medium', 'high')
                    ORDER BY created_at DESC 
                    LIMIT 150
                ) WHERE {column} IS NOT NULL
            ''')
        
        filled = cursor.fetchone()[0]
        percentage = (filled / target_articles * 100) if target_articles > 0 else 0
        
        status = "✅" if percentage >= 80 else "⚠️" if percentage >= 50 else "❌"
        print(f"{status} {description}: {filled}/{target_articles} ({percentage:.1f}%)")
    
    # 3. Análisis de calidad de las imágenes
    print(f"\n🎨 ANÁLISIS DE CALIDAD DE IMÁGENES:")
    print("-" * 50)
    
    # Distribución de quality_score
    cursor.execute('''
        SELECT AVG(quality_score) FROM (
            SELECT * FROM articles 
            WHERE risk_level IN ('medium', 'high')
            AND quality_score IS NOT NULL
            ORDER BY created_at DESC 
            LIMIT 150
        )
    ''')
    avg_quality = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT AVG(cv_quality_score) FROM (
            SELECT * FROM articles 
            WHERE risk_level IN ('medium', 'high')
            AND cv_quality_score IS NOT NULL
            ORDER BY created_at DESC 
            LIMIT 150
        )
    ''')
    avg_cv = cursor.fetchone()[0]
    
    if avg_quality:
        print(f"📊 Puntuación promedio de calidad: {avg_quality:.1f}/100")
    if avg_cv:
        print(f"🤖 Puntuación promedio CV: {avg_cv:.1f}/100")
    
    # 4. Distribución de posiciones en mosaico
    print(f"\n📍 DISTRIBUCIÓN DE POSICIONES EN MOSAICO:")
    print("-" * 50)
    
    positions = [
        ('featured', 'Destacada'),
        ('primary', 'Principal'),
        ('secondary', 'Secundaria'),
        ('background', 'Fondo')
    ]
    
    for pos_key, pos_name in positions:
        cursor.execute('''
            SELECT COUNT(*) FROM (
                SELECT * FROM articles 
                WHERE risk_level IN ('medium', 'high')
                ORDER BY created_at DESC 
                LIMIT 150
            ) WHERE mosaic_position = ?
        ''', (pos_key,))
        count = cursor.fetchone()[0]
        print(f"  📌 {pos_name}: {count} artículos")
    
    # 5. Estadísticas de imágenes descargadas
    print(f"\n🖼️ ESTADÍSTICAS DE IMÁGENES:")
    print("-" * 40)
    
    cursor.execute('''
        SELECT COUNT(*) FROM (
            SELECT * FROM articles 
            WHERE risk_level IN ('medium', 'high')
            ORDER BY created_at DESC 
            LIMIT 150
        ) WHERE image_url LIKE '%data/images%'
    ''')
    local_images = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COUNT(*) FROM (
            SELECT * FROM articles 
            WHERE risk_level IN ('medium', 'high')
            ORDER BY created_at DESC 
            LIMIT 150
        ) WHERE image_url IS NOT NULL AND image_url != ""
    ''')
    total_images = cursor.fetchone()[0]
    
    print(f"📥 Imágenes descargadas localmente: {local_images}")
    print(f"🌐 Total con imagen: {total_images}")
    print(f"📊 Porcentaje de éxito en descarga: {(local_images/total_images*100) if total_images > 0 else 0:.1f}%")
    
    # 6. Artículos que necesitan atención
    print(f"\n⚠️ ARTÍCULOS QUE REQUIEREN ATENCIÓN:")
    print("-" * 50)
    
    cursor.execute('''
        SELECT COUNT(*) FROM (
            SELECT * FROM articles 
            WHERE risk_level IN ('medium', 'high')
            ORDER BY created_at DESC 
            LIMIT 150
        ) WHERE image_url IS NULL OR image_url = ""
    ''')
    no_image = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COUNT(*) FROM (
            SELECT * FROM articles 
            WHERE risk_level IN ('medium', 'high')
            ORDER BY created_at DESC 
            LIMIT 150
        ) WHERE quality_score IS NULL
    ''')
    no_analysis = cursor.fetchone()[0]
    
    print(f"🚫 Sin imagen: {no_image} artículos")
    print(f"🚫 Sin análisis CV: {no_analysis} artículos")
    
    # 7. Resumen ejecutivo
    print(f"\n🎯 RESUMEN EJECUTIVO:")
    print("=" * 50)
    
    # Calcular completitud general
    cursor.execute('''
        SELECT COUNT(*) FROM (
            SELECT * FROM articles 
            WHERE risk_level IN ('medium', 'high')
            ORDER BY created_at DESC 
            LIMIT 150
        ) WHERE image_url IS NOT NULL AND image_url != ""
           AND quality_score IS NOT NULL
           AND cv_quality_score IS NOT NULL
           AND mosaic_position IS NOT NULL AND mosaic_position != ""
           AND positioning_score IS NOT NULL
           AND visual_risk_score IS NOT NULL
           AND image_width IS NOT NULL
           AND image_height IS NOT NULL
           AND dominant_colors IS NOT NULL AND dominant_colors != "" AND dominant_colors != "[]"
           AND visual_analysis_json IS NOT NULL AND visual_analysis_json != ""
    ''')
    complete_analysis = cursor.fetchone()[0]
    
    completeness = (complete_analysis / target_articles * 100) if target_articles > 0 else 0
    
    print(f"✅ COMPLETITUD TOTAL: {complete_analysis}/{target_articles} ({completeness:.1f}%)")
    
    if completeness >= 90:
        status = "🟢 EXCELENTE"
    elif completeness >= 70:
        status = "🟡 BUENO"
    elif completeness >= 50:
        status = "🟠 REGULAR"
    else:
        status = "🔴 NECESITA MEJORA"
    
    print(f"📊 ESTADO GENERAL: {status}")
    
    # Recomendaciones
    print(f"\n💡 RECOMENDACIONES:")
    print("-" * 30)
    
    if no_image > 0:
        print(f"• Procesar {no_image} artículos sin imagen")
    if no_analysis > 0:
        print(f"• Completar análisis CV para {no_analysis} artículos")
    if completeness >= 90:
        print("• ✅ Sistema listo para producción")
    else:
        print(f"• Mejorar completitud del {completeness:.1f}% al 90%+")
    
    conn.close()

if __name__ == '__main__':
    final_verification_report()
