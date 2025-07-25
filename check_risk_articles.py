#!/usr/bin/env python3
"""
Check what high-risk articles we have and their URL status
"""
import sqlite3

def check_risk_articles():
    # Connect to database
    conn = sqlite3.connect('data/geopolitical_intel.db')
    cursor = conn.cursor()
    
    print("=== ANÁLISIS DE ARTÍCULOS POR NIVEL DE RIESGO ===\n")
    
    # Check distribution of risk levels
    cursor.execute("""
        SELECT 
            risk_level,
            COUNT(*) as count,
            COUNT(CASE WHEN url IS NOT NULL AND url != '' AND url != '#' THEN 1 END) as with_url,
            COUNT(CASE WHEN image_url IS NOT NULL AND image_url != '' THEN 1 END) as with_image
        FROM articles 
        WHERE created_at > datetime('now', '-7 days')
        GROUP BY risk_level
        ORDER BY 
            CASE risk_level 
                WHEN 'high' THEN 1 
                WHEN 'medium' THEN 2 
                WHEN 'low' THEN 3 
                ELSE 4 
            END
    """)
    
    print("📊 DISTRIBUCIÓN DE RIESGO (últimos 7 días):")
    print("-" * 60)
    for row in cursor.fetchall():
        risk_level, count, with_url, with_image = row
        print(f"{risk_level or 'NULL':>8}: {count:>4} artículos | {with_url:>3} con URL | {with_image:>3} con imagen")
    
    print("\n" + "="*60)
    
    # Check high-risk articles specifically
    cursor.execute("""
        SELECT id, title, url, image_url, country, created_at, source
        FROM articles 
        WHERE risk_level = 'high'
        AND created_at > datetime('now', '-7 days')
        ORDER BY created_at DESC
        LIMIT 10
    """)
    
    high_risk_articles = cursor.fetchall()
    print(f"\n🔥 ARTÍCULOS DE ALTO RIESGO (últimos 7 días): {len(high_risk_articles)}")
    print("-" * 80)
    
    for i, article in enumerate(high_risk_articles, 1):
        article_id, title, url, image_url, country, created_at, source = article
        print(f"\n{i}. ID: {article_id}")
        print(f"   Título: {title[:70]}...")
        print(f"   País: {country or 'N/A'}")
        print(f"   Fecha: {created_at}")
        print(f"   Fuente: {source or 'N/A'}")
        print(f"   URL: {url or 'SIN URL'}")
        print(f"   Imagen: {image_url or 'SIN IMAGEN'}")
    
    # Check medium-risk articles
    cursor.execute("""
        SELECT id, title, url, image_url, country, created_at, source
        FROM articles 
        WHERE risk_level = 'medium'
        AND created_at > datetime('now', '-7 days')
        ORDER BY created_at DESC
        LIMIT 5
    """)
    
    medium_risk_articles = cursor.fetchall()
    print(f"\n⚠️  ARTÍCULOS DE RIESGO MEDIO (últimos 7 días): {len(medium_risk_articles)}")
    print("-" * 80)
    
    for i, article in enumerate(medium_risk_articles, 1):
        article_id, title, url, image_url, country, created_at, source = article
        print(f"\n{i}. ID: {article_id}")
        print(f"   Título: {title[:70]}...")
        print(f"   País: {country or 'N/A'}")
        print(f"   Fecha: {created_at}")
        print(f"   Fuente: {source or 'N/A'}")
        print(f"   URL: {url or 'SIN URL'}")
        print(f"   Imagen: {image_url or 'SIN IMAGEN'}")
    
    # Check what sources are providing articles
    cursor.execute("""
        SELECT 
            source,
            COUNT(*) as total,
            COUNT(CASE WHEN risk_level = 'high' THEN 1 END) as high_risk,
            COUNT(CASE WHEN risk_level = 'medium' THEN 1 END) as medium_risk,
            COUNT(CASE WHEN url IS NOT NULL AND url != '' AND url != '#' THEN 1 END) as with_url
        FROM articles 
        WHERE created_at > datetime('now', '-7 days')
        GROUP BY source
        ORDER BY total DESC
        LIMIT 10
    """)
    
    print(f"\n📰 FUENTES DE ARTÍCULOS (últimos 7 días):")
    print("-" * 80)
    print(f"{'Fuente':<30} {'Total':<8} {'Alto':<6} {'Medio':<7} {'Con URL':<8}")
    print("-" * 80)
    
    for row in cursor.fetchall():
        source, total, high_risk, medium_risk, with_url = row
        source_name = (source or 'Sin fuente')[:29]
        print(f"{source_name:<30} {total:<8} {high_risk:<6} {medium_risk:<7} {with_url:<8}")
    
    conn.close()

if __name__ == "__main__":
    check_risk_articles()