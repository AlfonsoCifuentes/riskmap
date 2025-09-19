#!/usr/bin/env python3
"""
Debug backend logs y posibles errores
"""

import sqlite3
import sys
import os

def test_exact_backend_logic():
    """Test the exact backend logic step by step."""
    print("🔍 SIMULATING EXACT BACKEND LOGIC")
    print("="*60)
    
    try:
        # Same logic as backend get_top_articles_from_db
        try:
            from src.utils.config import get_database_path
            db_path = get_database_path()
            print(f"✅ Got database path from config: {db_path}")
        except ImportError:
            db_path = r"data\geopolitical_intel.db"
            print(f"⚠️  Fallback to hardcoded path: {db_path}")
        
        if not os.path.exists(db_path):
            print(f"❌ Database not found: {db_path}")
            print("   Backend would use _get_real_articles_from_db()")
            return
        
        print(f"✅ Database exists: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test the exact query with exclude_hero_id = None
        exclude_hero_id = None
        limit = 5
        
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
                
                {exclude_clause}
                
                -- Solo artículos recientes (últimos 30 días para más cobertura)
                created_at >= datetime('now', '-30 days')
            ORDER BY 
                -- Prioridad: importancia AI > riesgo > fecha
                COALESCE(ai_importance, 0) DESC,
                COALESCE(risk_score, 0) DESC,
                created_at DESC
            LIMIT ?
        """
        
        exclude_clause = "id != ?" if exclude_hero_id else "1=1"
        query = base_query.format(exclude_clause=exclude_clause)
        
        print(f"🔄 Testing query with exclude_hero_id: {exclude_hero_id}")
        print(f"   Exclude clause: {exclude_clause}")
        
        try:
            if exclude_hero_id:
                cursor.execute(query, (exclude_hero_id, limit))
            else:
                cursor.execute(query, (limit,))
            
            rows = cursor.fetchall()
            print(f"✅ Main query successful: {len(rows)} results")
            
            for i, row in enumerate(rows, 1):
                print(f"   {i}. ID {row[0]}: {row[1][:40]}...")
                print(f"      Image: {row[12][:50]}..." if row[12] else "      Image: NULL")
            
        except Exception as query_error:
            print(f"❌ Main query failed: {query_error}")
            print("   Backend would use _get_real_articles_from_db() fallback")
            
            # Test fallback query
            print("\n🔄 Testing fallback query...")
            try:
                cursor.execute("""
                    SELECT 
                        id, title, 
                        CASE 
                            WHEN summary IS NOT NULL AND summary != '' THEN summary
                            WHEN content IS NOT NULL AND content != '' THEN SUBSTR(content, 1, 300) || '...'
                            ELSE 'Resumen no disponible'
                        END as summary,
                        url, source, published_at, country, region, risk_level, 
                        conflict_type, sentiment_score, risk_score, image_url, ai_importance
                    FROM articles 
                    WHERE 
                        title IS NOT NULL AND title != '' AND
                        (
                            LOWER(title) LIKE '%ukraine%' OR LOWER(title) LIKE '%russia%' OR
                            LOWER(title) LIKE '%war%' OR LOWER(title) LIKE '%conflict%' OR
                            LOWER(title) LIKE '%military%' OR LOWER(title) LIKE '%politics%' OR
                            LOWER(title) LIKE '%government%' OR LOWER(title) LIKE '%security%' OR
                            LOWER(title) LIKE '%china%' OR LOWER(title) LIKE '%iran%' OR
                            LOWER(title) LIKE '%israel%' OR LOWER(title) LIKE '%crisis%'
                        ) AND
                        created_at >= datetime('now', '-30 days')
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,))
                
                fallback_rows = cursor.fetchall()
                print(f"✅ Fallback query successful: {len(fallback_rows)} results")
                
                for i, row in enumerate(fallback_rows, 1):
                    print(f"   {i}. ID {row[0]}: {row[1][:40]}...")
                    print(f"      Image: {row[12][:50]}..." if row[12] else "      Image: NULL")
                    
            except Exception as fallback_error:
                print(f"❌ Fallback query also failed: {fallback_error}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ General error: {e}")

if __name__ == "__main__":
    test_exact_backend_logic()