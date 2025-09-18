#!/usr/bin/env python3
"""
Debug SQL query en backend
"""

import sqlite3
import os
import sys

def debug_backend_query():
    """Debug the exact SQL query used by backend."""
    db_path = "./data/geopolitical_intel.db"
    
    if not os.path.exists(db_path):
        print("❌ Database not found")
        return
    
    conn = sqlite3.connect(db_path)
    
    # Exact same query as backend
    base_query = """
        SELECT 
            id, title, 
            CASE 
                WHEN summary IS NOT NULL AND summary != '' AND summary NOT LIKE '%<think>%' THEN 
                    summary
                WHEN auto_generated_summary IS NOT NULL AND auto_generated_summary != '' AND auto_generated_summary NOT LIKE '%<think>%' THEN 
                    auto_generated_summary
                WHEN content IS NOT NULL AND content != '' AND content NOT LIKE '%<think>%' THEN 
                    SUBSTR(content, 1, 300) || '...'
                ELSE 
                    'Análisis de contenido geopolítico disponible para revisión.'
            END as summary,
            url, source, published_at, country, region, risk_level, 
            conflict_type, sentiment_score, risk_score,
            CASE 
                WHEN original_image_url IS NOT NULL AND original_image_url != '' AND original_image_url LIKE 'https://%'
                THEN original_image_url
                WHEN image_url IS NOT NULL AND image_url != '' AND image_url LIKE 'https://%' AND image_url NOT LIKE '%via.placeholder%' THEN 
                    image_url
                ELSE 
                    NULL
            END as image_url,
            ai_importance
        FROM articles 
        WHERE 
            -- Solo artículos marcados como geopolíticos por el sistema inteligente
            geopolitical_relevance = 1 AND
            
            -- Campos básicos requeridos 
            title IS NOT NULL AND title != '' AND
            (
                (content IS NOT NULL AND content != '') OR 
                (summary IS NOT NULL AND summary != '')
            ) AND
            
            -- Solo artículos con imagen real (no placeholder)
            (
                (original_image_url IS NOT NULL AND original_image_url != '') OR
                (image_url IS NOT NULL AND image_url != '' AND 
                 image_url NOT LIKE '%placeholder%' AND 
                 image_url NOT LIKE '%via.placeholder%' AND
                 image_url NOT LIKE '%default%')
            ) AND
            
            -- Exclusiones mínimas para casos extremos
            (
                LOWER(title) NOT LIKE '%sport%' AND LOWER(title) NOT LIKE '%sports%' AND
                LOWER(title) NOT LIKE '%game%' AND LOWER(title) NOT LIKE '%games%' AND
                LOWER(title) NOT LIKE '%football%' AND LOWER(title) NOT LIKE '%soccer%' AND
                LOWER(title) NOT LIKE '%basketball%' AND LOWER(title) NOT LIKE '%baseball%' AND
                LOWER(title) NOT LIKE '%emmy%' AND LOWER(title) NOT LIKE '%oscar%' AND
                LOWER(title) NOT LIKE '%movie%' AND LOWER(title) NOT LIKE '%actor%' AND
                LOWER(title) NOT LIKE '%hollywood%' AND LOWER(title) NOT LIKE '%singer%' AND
                LOWER(title) NOT LIKE '%music%' AND LOWER(title) NOT LIKE '%celebrity%' AND
                LOWER(title) NOT LIKE '%netflix%' AND
                LOWER(title) NOT LIKE '%iphone%' AND LOWER(title) NOT LIKE '%nintendo%' AND
                LOWER(title) NOT LIKE '%deporte%' AND LOWER(title) NOT LIKE '%deportes%' AND
                LOWER(title) NOT LIKE '%fútbol%' AND LOWER(title) NOT LIKE '%música%'
            ) AND
            
            -- Solo artículos recientes (últimos 30 días para más cobertura)
            created_at >= datetime('now', '-30 days')
        ORDER BY 
            -- Prioridad: importancia AI > riesgo > fecha
            COALESCE(ai_importance, 0) DESC,
            COALESCE(risk_score, 0) DESC,
            created_at DESC
        LIMIT 5
    """
    
    print("🔍 TESTING BACKEND SQL QUERY")
    print("="*60)
    
    try:
        cursor = conn.cursor()
        cursor.execute(base_query)
        rows = cursor.fetchall()
        
        print(f"📊 Query returned: {len(rows)} articles")
        print()
        
        for i, row in enumerate(rows, 1):
            print(f"{i}. Article ID: {row[0]}")
            print(f"   Title: {row[1][:50]}...")
            print(f"   Summary: {'YES' if row[2] else 'NO'}")
            print(f"   URL: {'YES' if row[3] else 'NO'}")
            print(f"   Source: {row[4]}")
            print(f"   Image URL: {row[12][:60]}..." if row[12] else "   Image URL: NULL")
            print(f"   AI Importance: {row[13]}")
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Query error: {e}")
        conn.close()

if __name__ == "__main__":
    debug_backend_query()