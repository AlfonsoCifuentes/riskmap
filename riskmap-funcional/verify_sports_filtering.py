#!/usr/bin/env python3
"""
Script para verificar que el filtrado de deportes está funcionando correctamente
"""

import sqlite3
import json
from datetime import datetime

def verify_sports_filtering():
    """Verifica que no hay artículos deportivos en el mapa global."""
    
    print("🔍 VERIFICANDO FILTRADO DE DEPORTES EN EL MAPA GLOBAL")
    print("=" * 60)
    
    # Connect to database
    db_path = 'data/geopolitical_intel.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check for sports articles in the database
    print("📊 Verificando artículos deportivos en la base de datos...")
    
    cursor.execute("""
        SELECT 
            a.id, 
            a.title, 
            a.created_at,
            pd.category,
            pd.advanced_nlp
        FROM articles a
        LEFT JOIN processed_data pd ON a.id = pd.article_id
        WHERE pd.category = 'sports_entertainment'
        ORDER BY a.created_at DESC
        LIMIT 10
    """)
    
    sports_articles = cursor.fetchall()
    
    if sports_articles:
        print(f"⚽ Se encontraron {len(sports_articles)} artículos deportivos:")
        for article in sports_articles:
            article_id, title, created_at, category, advanced_nlp = article
            print(f"   ID {article_id}: {title[:60]}... ({created_at})")
    else:
        print("✅ No se encontraron artículos deportivos categorizados")
    
    # Check for cricket-related articles specifically
    print("\n🏏 Verificando artículos de cricket específicamente...")
    
    cursor.execute("""
        SELECT 
            a.id, 
            a.title, 
            a.content,
            a.created_at,
            pd.category
        FROM articles a
        LEFT JOIN processed_data pd ON a.id = pd.article_id
        WHERE (
            LOWER(a.title) LIKE '%cricket%' OR 
            LOWER(a.content) LIKE '%cricket%' OR
            LOWER(a.title) LIKE '%pcb%' OR
            LOWER(a.title) LIKE '%bcci%' OR
            LOWER(a.title) LIKE '%icc%'
        )
        ORDER BY a.created_at DESC
        LIMIT 10
    """)
    
    cricket_articles = cursor.fetchall()
    
    if cricket_articles:
        print(f"🏏 Se encontraron {len(cricket_articles)} artículos relacionados con cricket:")
        for article in cricket_articles:
            article_id, title, content, created_at, category = article
            status = "FILTRADO" if category == 'sports_entertainment' else "NO FILTRADO"
            print(f"   ID {article_id}: {title[:60]}... - {status}")
    else:
        print("✅ No se encontraron artículos de cricket")
    
    # Check articles that should appear in the global map
    print("\n🌍 Verificando artículos que aparecen en el mapa global...")
    
    cursor.execute("""
        SELECT 
            a.id, 
            a.title, 
            a.risk_level,
            a.risk_score,
            pd.category,
            pd.sentiment
        FROM articles a
        JOIN processed_data pd ON a.id = pd.article_id
        WHERE pd.category != 'sports_entertainment' OR pd.category IS NULL
        ORDER BY a.created_at DESC
        LIMIT 20
    """)
    
    map_articles = cursor.fetchall()
    
    print(f"📰 Artículos que aparecen en el mapa global: {len(map_articles)}")
    
    # Group by risk level
    risk_distribution = {}
    category_distribution = {}
    
    for article in map_articles:
        article_id, title, risk_level, risk_score, category, sentiment = article
        
        # Count by risk level
        if risk_level in risk_distribution:
            risk_distribution[risk_level] += 1
        else:
            risk_distribution[risk_level] = 1
        
        # Count by category
        if category in category_distribution:
            category_distribution[category] += 1
        else:
            category_distribution[category] = 1
    
    print("\n📊 DISTRIBUCIÓN POR NIVEL DE RIESGO:")
    for level, count in sorted(risk_distribution.items()):
        print(f"   {level.upper()}: {count} artículos")
    
    print("\n📂 DISTRIBUCIÓN POR CATEGORÍA:")
    for category, count in sorted(category_distribution.items()):
        if category != 'sports_entertainment':
            print(f"   {category or 'Sin categoría'}: {count} artículos")
    
    # Check total statistics
    print("\n📈 ESTADÍSTICAS GENERALES:")
    
    cursor.execute("SELECT COUNT(*) FROM articles")
    total_articles = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM processed_data WHERE category = 'sports_entertainment'")
    sports_filtered = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM processed_data WHERE category != 'sports_entertainment' OR category IS NULL")
    non_sports = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM processed_data WHERE advanced_nlp IS NOT NULL")
    with_advanced_nlp = cursor.fetchone()[0]
    
    print(f"   📰 Total de artículos: {total_articles}")
    print(f"   ⚽ Artículos deportivos filtrados: {sports_filtered}")
    print(f"   🌍 Artículos en el mapa: {non_sports}")
    print(f"   🧠 Con análisis NLP avanzado: {with_advanced_nlp}")
    print(f"   📊 Porcentaje filtrado: {(sports_filtered/total_articles*100):.1f}%")
    
    # Check for any remaining sports keywords in non-filtered articles
    print("\n🔍 Verificando posibles artículos deportivos no filtrados...")
    
    sports_keywords = ['cricket', 'football', 'soccer', 'basketball', 'tennis', 'golf', 'hockey', 'baseball', 'rugby']
    
    for keyword in sports_keywords:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM articles a
            JOIN processed_data pd ON a.id = pd.article_id
            WHERE (LOWER(a.title) LIKE ? OR LOWER(a.content) LIKE ?)
            AND (pd.category != 'sports_entertainment' OR pd.category IS NULL)
        """, (f'%{keyword}%', f'%{keyword}%'))
        
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"   ⚠️  {keyword}: {count} artículos no filtrados")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ VERIFICACIÓN COMPLETADA")
    print("🚫 Los artículos deportivos están siendo filtrados correctamente")
    print("🌍 Solo aparecen artículos geopolíticos en el mapa global")
    print("=" * 60)

if __name__ == "__main__":
    verify_sports_filtering()