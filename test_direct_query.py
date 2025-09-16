#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test directo de la función get_top_articles_from_db del código actualizado
"""

import sqlite3
import sys
import os

def test_updated_query():
    """Test la query actualizada directamente en la BD"""
    try:
        # Conectar a la base de datos
        db_path = './data/geopolitical_intel.db'
        if not os.path.exists(db_path):
            print(f"❌ Base de datos no encontrada: {db_path}")
            return False
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Query actualizada (sin GROUP BY/HAVING problemático)
        query = """
        SELECT 
            id, title, 
            CASE 
                WHEN summary IS NOT NULL AND summary != '' THEN summary
                WHEN auto_generated_summary IS NOT NULL AND auto_generated_summary != '' THEN auto_generated_summary
                ELSE SUBSTR(content, 1, 200) || '...'
            END as summary,
            url, 
            CASE 
                WHEN image_url IS NOT NULL AND image_url != '' THEN image_url
                ELSE 'https://via.placeholder.com/400x200?text=Artículo+de+Noticias'
            END as image_url,
            risk_score, language, source, 
            published_at, ai_importance
        FROM articles 
        WHERE 
            -- Campos básicos requeridos
            title IS NOT NULL AND title != '' AND
            content IS NOT NULL AND content != '' AND
            
            -- Riesgo válido
            risk_score >= 0.0 AND
            
            -- Excluir artículos HERO (solo para mosaic)
            (content NOT LIKE '%HERO ARTICLE%' OR content IS NULL) AND
            (title NOT LIKE '%HERO%' OR title IS NULL)
        
        ORDER BY 
            -- Priorizar por riesgo (high->medium->low)
            CASE WHEN risk_score >= 0.6 THEN 3
                 WHEN risk_score >= 0.4 THEN 2  
                 ELSE 1 END DESC,
            ai_importance DESC,
            published_at DESC
        LIMIT 20
        """
        
        print("🔍 Ejecutando query actualizada...")
        cursor.execute(query)
        articles = cursor.fetchall()
        
        print(f"📊 Resultados encontrados: {len(articles)}")
        
        if articles:
            print(f"\n✅ SUCCESS: Query devuelve {len(articles)} artículos")
            print(f"\n🎯 Primeros 3 artículos:")
            
            for i, article in enumerate(articles[:3]):
                print(f"  {i+1}. ID: {article[0]}")
                print(f"     Título: {article[1][:80]}...")
                print(f"     Riesgo: {article[5]}")
                print(f"     Imagen: {article[4][:50]}...")
                print()
            
            conn.close()
            return True
        else:
            print("❌ FAIL: Query no devuelve resultados")
            
            # Debug: verificar qué hay en la tabla
            print("\n🔍 Debug - verificando contenido de la tabla:")
            cursor.execute("SELECT COUNT(*) FROM articles")
            total = cursor.fetchone()[0]
            print(f"  Total artículos: {total}")
            
            cursor.execute("SELECT COUNT(*) FROM articles WHERE title IS NOT NULL AND title != ''")
            with_title = cursor.fetchone()[0]
            print(f"  Con título: {with_title}")
            
            cursor.execute("SELECT COUNT(*) FROM articles WHERE summary IS NOT NULL AND summary != ''")
            with_summary = cursor.fetchone()[0]
            print(f"  Con summary: {with_summary}")
            
            cursor.execute("SELECT COUNT(*) FROM articles WHERE image_url IS NOT NULL AND image_url != ''")
            with_image = cursor.fetchone()[0]
            print(f"  Con imagen: {with_image}")
            
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing query actualizada directamente...")
    success = test_updated_query()
    sys.exit(0 if success else 1)