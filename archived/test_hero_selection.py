#!/usr/bin/env python3
"""
Script para probar la nueva lógica de selección del artículo hero
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

def test_hero_selection():
    """Probar la selección del artículo hero"""
    
    db_path = Path('data/geopolitical_intel.db')
    if not db_path.exists():
        print("❌ Base de datos no encontrada")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print("🎯 PRUEBA DE SELECCIÓN DE ARTÍCULO HERO")
    print("=" * 60)
    
    # 1. Verificar artículos de alto riesgo recientes (últimas 72 horas)
    print("\n📊 ARTÍCULOS DE ALTO RIESGO (ÚLTIMAS 72 HORAS):")
    print("-" * 50)
    
    cursor.execute("""
        SELECT id, title, risk_level, published_at, image_url
        FROM articles 
        WHERE risk_level = 'high'
        AND datetime(published_at) > datetime('now', '-3 days')
        ORDER BY 
            CASE 
                WHEN image_url IS NOT NULL AND image_url != '' 
                     AND image_url NOT LIKE '%placeholder%' 
                     AND image_url NOT LIKE '%picsum%' THEN 0
                ELSE 1
            END ASC,
            published_at DESC
        LIMIT 5
    """)
    
    high_risk_recent = cursor.fetchall()
    
    if high_risk_recent:
        for i, (article_id, title, risk_level, published_at, image_url) in enumerate(high_risk_recent, 1):
            has_image = "✅" if image_url and image_url.strip() and 'placeholder' not in image_url and 'picsum' not in image_url else "❌"
            print(f"{i}. ID {article_id}: {title[:40]}...")
            print(f"   Riesgo: {risk_level} | Fecha: {published_at} | Imagen: {has_image}")
        
        selected = high_risk_recent[0]
        print(f"\n🎯 CANDIDATO HERO: ID {selected[0]} - '{selected[1][:50]}...'")
    else:
        print("❌ No hay artículos de alto riesgo en las últimas 72 horas")
    
    # 2. Si no hay alto riesgo reciente, verificar medio riesgo muy reciente (24 horas)
    if not high_risk_recent:
        print("\n📊 ARTÍCULOS DE RIESGO MEDIO (ÚLTIMAS 24 HORAS):")
        print("-" * 50)
        
        cursor.execute("""
            SELECT id, title, risk_level, published_at, image_url
            FROM articles 
            WHERE risk_level = 'medium'
            AND datetime(published_at) > datetime('now', '-1 day')
            ORDER BY 
                CASE 
                    WHEN image_url IS NOT NULL AND image_url != '' 
                         AND image_url NOT LIKE '%placeholder%' 
                         AND image_url NOT LIKE '%picsum%' THEN 0
                    ELSE 1
                END ASC,
                published_at DESC
            LIMIT 5
        """)
        
        medium_risk_recent = cursor.fetchall()
        
        if medium_risk_recent:
            for i, (article_id, title, risk_level, published_at, image_url) in enumerate(medium_risk_recent, 1):
                has_image = "✅" if image_url and image_url.strip() and 'placeholder' not in image_url and 'picsum' not in image_url else "❌"
                print(f"{i}. ID {article_id}: {title[:40]}...")
                print(f"   Riesgo: {risk_level} | Fecha: {published_at} | Imagen: {has_image}")
            
            selected = medium_risk_recent[0]
            print(f"\n🎯 CANDIDATO HERO: ID {selected[0]} - '{selected[1][:50]}...'")
        else:
            print("❌ No hay artículos de riesgo medio en las últimas 24 horas")
    
    # 3. Fallback: cualquier artículo de alto riesgo
    if not high_risk_recent and (not 'medium_risk_recent' in locals() or not medium_risk_recent):
        print("\n📊 CUALQUIER ARTÍCULO DE ALTO RIESGO:")
        print("-" * 40)
        
        cursor.execute("""
            SELECT id, title, risk_level, published_at, image_url
            FROM articles 
            WHERE risk_level = 'high'
            ORDER BY 
                CASE 
                    WHEN image_url IS NOT NULL AND image_url != '' 
                         AND image_url NOT LIKE '%placeholder%' 
                         AND image_url NOT LIKE '%picsum%' THEN 0
                    ELSE 1
                END ASC,
                published_at DESC
            LIMIT 5
        """)
        
        any_high_risk = cursor.fetchall()
        
        if any_high_risk:
            for i, (article_id, title, risk_level, published_at, image_url) in enumerate(any_high_risk, 1):
                has_image = "✅" if image_url and image_url.strip() and 'placeholder' not in image_url and 'picsum' not in image_url else "❌"
                print(f"{i}. ID {article_id}: {title[:40]}...")
                print(f"   Riesgo: {risk_level} | Fecha: {published_at} | Imagen: {has_image}")
            
            selected = any_high_risk[0]
            print(f"\n🎯 CANDIDATO HERO: ID {selected[0]} - '{selected[1][:50]}...'")
        else:
            print("❌ No hay artículos de alto riesgo en la base de datos")
    
    # 4. Estadísticas generales
    print(f"\n📈 ESTADÍSTICAS GENERALES:")
    print("-" * 30)
    
    # Total por nivel de riesgo
    risk_levels = ['high', 'medium', 'low']
    for level in risk_levels:
        cursor.execute('SELECT COUNT(*) FROM articles WHERE risk_level = ?', (level,))
        count = cursor.fetchone()[0]
        print(f"📊 Riesgo {level}: {count} artículos")
    
    # Artículos con imagen
    cursor.execute("""
        SELECT COUNT(*) FROM articles 
        WHERE image_url IS NOT NULL AND image_url != '' 
        AND image_url NOT LIKE '%placeholder%' 
        AND image_url NOT LIKE '%picsum%'
    """)
    with_real_images = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM articles')
    total = cursor.fetchone()[0]
    
    print(f"🖼️ Con imagen real: {with_real_images}/{total} ({with_real_images/total*100:.1f}%)")
    
    # Artículos recientes por riesgo
    cursor.execute("""
        SELECT 
            risk_level,
            COUNT(*) as count
        FROM articles 
        WHERE datetime(published_at) > datetime('now', '-7 days')
        GROUP BY risk_level
        ORDER BY 
            CASE risk_level
                WHEN 'high' THEN 1
                WHEN 'medium' THEN 2
                WHEN 'low' THEN 3
                ELSE 4
            END
    """)
    
    recent_stats = cursor.fetchall()
    print(f"\n📅 ÚLTIMOS 7 DÍAS:")
    for risk_level, count in recent_stats:
        print(f"   {risk_level}: {count} artículos")
    
    conn.close()
    
    print(f"\n✅ PRUEBA COMPLETADA")

if __name__ == '__main__':
    test_hero_selection()
