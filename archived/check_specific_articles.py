#!/usr/bin/env python3
"""
Script para verificar las imágenes en la base de datos directamente
"""

import sqlite3

def check_specific_articles():
    """Verificar artículos específicos en la base de datos"""
    print("🔍 Verificando artículos específicos en la base de datos...")
    
    conn = sqlite3.connect('data/geopolitical_intel.db')
    cursor = conn.cursor()
    
    # 1. Obtener los primeros 5 artículos ordenados por risk_score
    print("\n1. Primeros 5 artículos por risk_score:")
    cursor.execute('''
        SELECT id, title, image_url, risk_level, risk_score, country 
        FROM articles 
        ORDER BY risk_score DESC 
        LIMIT 5
    ''')
    
    articles = cursor.fetchall()
    for i, (article_id, title, image_url, risk_level, risk_score, country) in enumerate(articles):
        has_image = "Sí" if image_url and image_url.strip() else "No"
        print(f"   {i+1}. ID:{article_id} | {title[:50]}...")
        print(f"      🖼️  Imagen: {has_image} | {image_url if image_url else 'N/A'}")
        print(f"      ⚠️  Riesgo: {risk_level} ({risk_score}) | País: {country}")
        print()
    
    # 2. Obtener artículos QUE SÍ tienen imagen
    print("2. Artículos CON imagen (primeros 5):")
    cursor.execute('''
        SELECT id, title, image_url, risk_level, country 
        FROM articles 
        WHERE image_url IS NOT NULL AND image_url != ""
        ORDER BY risk_score DESC 
        LIMIT 5
    ''')
    
    articles_with_images = cursor.fetchall()
    if articles_with_images:
        for i, (article_id, title, image_url, risk_level, country) in enumerate(articles_with_images):
            print(f"   {i+1}. ID:{article_id} | {title[:50]}...")
            print(f"      🖼️  Imagen: {image_url}")
            print(f"      ⚠️  Riesgo: {risk_level} | País: {country}")
            print()
    else:
        print("   ❌ No se encontraron artículos con imagen")
    
    # 3. Obtener estadísticas generales
    print("3. Estadísticas generales:")
    cursor.execute('SELECT COUNT(*) FROM articles')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM articles WHERE image_url IS NOT NULL AND image_url != ""')
    with_images = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM articles WHERE risk_score IS NOT NULL')
    with_risk = cursor.fetchone()[0]
    
    print(f"   📊 Total artículos: {total}")
    print(f"   🖼️  Con imagen: {with_images}")
    print(f"   ❌ Sin imagen: {total - with_images}")
    print(f"   ⚠️  Con risk_score: {with_risk}")
    print(f"   📈 Cobertura imágenes: {(with_images/total)*100:.1f}%")
    
    conn.close()

if __name__ == "__main__":
    check_specific_articles()
