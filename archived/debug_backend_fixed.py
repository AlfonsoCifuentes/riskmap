#!/usr/bin/env python3
"""
Test the exact backend logic from app_BUENA.py
"""
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

def test_backend_articles_query():
    print("🔍 SIMULATING EXACT BACKEND LOGIC (UPDATED)")
    print("="*60)
    
    # Get database path
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/geopolitical_intel.db')
    db_path = DATABASE_URL.replace('sqlite:///', '')
    print(f"✅ Got database path from config: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    print(f"✅ Database exists: {db_path}")
    
    # Test without hero exclusion first
    exclude_hero_id = None
    limit = 5
    
    print(f"🔄 Testing query with exclude_hero_id: {exclude_hero_id}")
    exclude_clause = "id != ?" if exclude_hero_id else "1=1"
    print(f"   Exclude clause: {exclude_clause}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # EXACT COPY from app_BUENA.py (FIXED VERSION)
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
                source NOT LIKE '%Yahoo Entertainment%' AND
                
                -- Excluir HERO si se especifica
                {exclude_clause} AND
                
                -- Solo artículos recientes (últimos 30 días para más cobertura)
                created_at >= datetime('now', '-30 days')
            ORDER BY 
                -- Prioridad: importancia AI > riesgo > fecha
                COALESCE(ai_importance, 0) DESC,
                COALESCE(risk_score, 0) DESC,
                created_at DESC
            LIMIT ?
        """
        
        query = base_query.format(exclude_clause=exclude_clause)
        
        if exclude_hero_id:
            cursor.execute(query, (exclude_hero_id, limit))
        else:
            cursor.execute(query, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        print(f"✅ Main query successful: {len(rows)} results")
        if rows:
            print("📋 Results:")
            for i, row in enumerate(rows):
                # Mapping: id, title, summary, url, source, published_at, country, region, risk_level,
                # conflict_type, sentiment_score, risk_score, image_url, ai_importance  
                article_id = row[0]
                title = row[1]
                image_url = row[12]  # image_url is column 12
                
                print(f"   {i+1}. ID {article_id}: {title[:50]}...")
                print(f"      Image: {image_url or 'NULL'}")
        else:
            print("❌ No results returned")
    
    except Exception as e:
        print(f"❌ Main query failed: {str(e)}")
        print("   Backend would use _get_real_articles_from_db() fallback")

if __name__ == "__main__":
    test_backend_articles_query()