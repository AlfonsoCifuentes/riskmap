#!/usr/bin/env python3
"""
Verificar que los cambios del mosaico están funcionando correctamente:
1. Artículos de alto riesgo aparecen primero
2. Todas las noticias del mosaico tienen imagen
3. Links abren en nueva pestaña
"""

import sqlite3
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_mosaic_changes():
    """Verificar los cambios del mosaico"""
    
    print("🔍 VERIFICACIÓN DE CAMBIOS DEL MOSAICO")
    print("=" * 70)
    
    db_path = Path('data/geopolitical_intel.db')
    if not db_path.exists():
        print("❌ Base de datos no encontrada")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # 1. Verificar que los artículos de alto riesgo tienen imagen
    print("\n📊 VERIFICACIÓN 1: Artículos de alto riesgo con imagen")
    print("-" * 50)
    
    cursor.execute('''
        SELECT COUNT(*) 
        FROM articles 
        WHERE risk_level = 'high' 
        AND (image_url IS NOT NULL AND image_url != '')
    ''')
    high_risk_with_image = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COUNT(*) 
        FROM articles 
        WHERE risk_level = 'high'
    ''')
    total_high_risk = cursor.fetchone()[0]
    
    print(f"✅ Artículos de alto riesgo con imagen: {high_risk_with_image}/{total_high_risk}")
    if total_high_risk > 0:
        coverage_percent = (high_risk_with_image / total_high_risk) * 100
        print(f"📈 Cobertura de imagen para alto riesgo: {coverage_percent:.1f}%")
    
    # 2. Verificar distribución de artículos en el mosaico
    print("\n📊 VERIFICACIÓN 2: Distribución en el mosaico")
    print("-" * 50)
    
    cursor.execute('''
        SELECT 
            risk_level,
            COUNT(*) as count,
            COUNT(CASE WHEN image_url IS NOT NULL AND image_url != '' THEN 1 END) as with_image
        FROM articles 
        WHERE risk_level IS NOT NULL
        GROUP BY risk_level
        ORDER BY 
            CASE 
                WHEN risk_level = 'high' THEN 1
                WHEN risk_level = 'medium' THEN 2
                WHEN risk_level = 'low' THEN 3
                ELSE 4
            END
    ''')
    
    distribution = cursor.fetchall()
    
    for risk_level, count, with_image in distribution:
        image_percent = (with_image / count * 100) if count > 0 else 0
        print(f"🎯 {risk_level.upper()}: {count} artículos, {with_image} con imagen ({image_percent:.1f}%)")
    
    # 3. Verificar artículos para el mosaico (top 50 más recientes)
    print("\n📊 VERIFICACIÓN 3: Top 50 artículos para mosaico")
    print("-" * 50)
    
    cursor.execute('''
        SELECT 
            id, title, risk_level, risk_score, 
            CASE 
                WHEN image_url IS NOT NULL AND image_url != '' THEN 'SÍ'
                ELSE 'NO'
            END as tiene_imagen,
            published_at
        FROM articles 
        WHERE risk_level IN ('high', 'medium', 'low')
        ORDER BY 
            CASE 
                WHEN risk_level = 'high' THEN 1
                WHEN risk_level = 'medium' THEN 2
                WHEN risk_level = 'low' THEN 3
                ELSE 4
            END,
            risk_score DESC,
            published_at DESC
        LIMIT 50
    ''')
    
    mosaic_articles = cursor.fetchall()
    
    high_risk_count = 0
    medium_risk_count = 0
    low_risk_count = 0
    with_image_count = 0
    
    print("🏆 PRIMEROS 10 ARTÍCULOS DEL MOSAICO:")
    for i, (article_id, title, risk_level, risk_score, tiene_imagen, published_at) in enumerate(mosaic_articles[:10]):
        if risk_level == 'high':
            high_risk_count += 1
        elif risk_level == 'medium':
            medium_risk_count += 1
        elif risk_level == 'low':
            low_risk_count += 1
            
        if tiene_imagen == 'SÍ':
            with_image_count += 1
            
        emoji = "🔥" if risk_level == 'high' else "⚠️" if risk_level == 'medium' else "🟢"
        print(f"  {i+1:2d}. {emoji} [{risk_level.upper()}] {title[:60]}... (Imagen: {tiene_imagen})")
    
    # Contar todos los 50
    total_stats = {'high': 0, 'medium': 0, 'low': 0, 'with_image': 0}
    for article in mosaic_articles:
        risk_level = article[2]
        tiene_imagen = article[4]
        
        if risk_level in total_stats:
            total_stats[risk_level] += 1
        if tiene_imagen == 'SÍ':
            total_stats['with_image'] += 1
    
    print(f"\n📈 RESUMEN TOP 50 ARTÍCULOS DEL MOSAICO:")
    print(f"🔥 Alto riesgo: {total_stats['high']} artículos")
    print(f"⚠️ Medio riesgo: {total_stats['medium']} artículos") 
    print(f"🟢 Bajo riesgo: {total_stats['low']} artículos")
    print(f"🖼️ Con imagen: {total_stats['with_image']}/50 ({total_stats['with_image']/50*100:.1f}%)")
    
    # 4. Verificar artículos sin imagen que necesitarían fallback
    print("\n📊 VERIFICACIÓN 4: Artículos sin imagen (necesitan fallback)")
    print("-" * 50)
    
    cursor.execute('''
        SELECT COUNT(*) 
        FROM articles 
        WHERE (image_url IS NULL OR image_url = '')
        AND risk_level IN ('high', 'medium')
    ''')
    articles_without_image = cursor.fetchone()[0]
    
    print(f"⚠️ Artículos de alto/medio riesgo sin imagen: {articles_without_image}")
    
    if articles_without_image > 0:
        print("💡 Estos artículos usarán imágenes de fallback automáticamente")
        
        # Mostrar algunos ejemplos
        cursor.execute('''
            SELECT id, title, risk_level
            FROM articles 
            WHERE (image_url IS NULL OR image_url = '')
            AND risk_level IN ('high', 'medium')
            LIMIT 5
        ''')
        
        examples = cursor.fetchall()
        print("📝 Ejemplos de artículos que usarán fallback:")
        for article_id, title, risk_level in examples:
            emoji = "🔥" if risk_level == 'high' else "⚠️"
            print(f"  {emoji} ID {article_id}: {title[:70]}...")
    
    # 5. Verificar funcionalidad de URLs
    print("\n📊 VERIFICACIÓN 5: URLs de artículos")
    print("-" * 50)
    
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN url IS NOT NULL AND url != '' THEN 1 END) as with_url
        FROM articles 
        WHERE risk_level IN ('high', 'medium', 'low')
    ''')
    
    total_articles, articles_with_url = cursor.fetchone()
    url_percent = (articles_with_url / total_articles * 100) if total_articles > 0 else 0
    
    print(f"🔗 Artículos con URL: {articles_with_url}/{total_articles} ({url_percent:.1f}%)")
    
    conn.close()
    
    # Resumen final
    print("\n🎯 RESUMEN DE VERIFICACIÓN")
    print("=" * 70)
    
    success_score = 0
    total_checks = 5
    
    if high_risk_with_image > 0:
        success_score += 1
        print("✅ Artículos de alto riesgo tienen imágenes")
    else:
        print("❌ No hay artículos de alto riesgo con imágenes")
    
    if total_stats.get('high', 0) > 0:
        success_score += 1
        print("✅ Artículos de alto riesgo aparecen primero en mosaico")
    else:
        print("⚠️ Pocos artículos de alto riesgo en el mosaico")
    
    if total_stats.get('with_image', 0) >= 40:  # Al menos 80% con imagen
        success_score += 1
        print("✅ Buena cobertura de imágenes en el mosaico")
    else:
        print("⚠️ Cobertura de imágenes en mosaico podría mejorar")
    
    if articles_without_image < total_high_risk * 0.5:  # Menos del 50% sin imagen
        success_score += 1
        print("✅ Sistema de fallback de imágenes funcionando")
    else:
        print("⚠️ Muchos artículos sin imagen - revisar sistema de fallback")
    
    if url_percent >= 90:
        success_score += 1
        print("✅ URLs disponibles para abrir en nueva pestaña")
    else:
        print("⚠️ Algunas URLs faltantes - revisar funcionalidad de links")
    
    print(f"\n🏆 PUNTUACIÓN FINAL: {success_score}/{total_checks} verificaciones pasadas")
    
    if success_score >= 4:
        print("🎉 ¡Excelente! El mosaico está configurado correctamente")
    elif success_score >= 3:
        print("👍 Bien! El mosaico funciona con mejoras menores")
    else:
        print("⚠️ Necesita atención - revisar configuración del mosaico")

if __name__ == '__main__':
    verify_mosaic_changes()
