#!/usr/bin/env python3
"""
Diagnosticar qué artículos se están mostrando actualmente en el mosaico
y por qué algunos no son geopolíticos o no tienen imágenes
"""

import sqlite3
import os

def diagnose_current_articles():
    """Diagnosticar el estado actual de los artículos que se mostrarían"""
    
    db_path = r"e:\Proyectos\VisualStudio\Upgrade_Data_AI\riskmap\data\geopolitical_intel.db"
    
    print("🔍 DIAGNÓSTICO DEL ESTADO ACTUAL DE ARTÍCULOS")
    print("=" * 60)
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            print("\n📊 1. ESTADÍSTICAS GENERALES:")
            cursor.execute("SELECT COUNT(*) FROM articles")
            total_articles = cursor.fetchone()[0]
            print(f"   Total artículos en BD: {total_articles:,}")
            
            cursor.execute("SELECT COUNT(*) FROM articles WHERE image_url LIKE '%placeholder%'")
            placeholder_count = cursor.fetchone()[0]
            print(f"   Artículos con placeholder: {placeholder_count:,}")
            
            cursor.execute("SELECT COUNT(*) FROM articles WHERE original_image_url IS NOT NULL AND original_image_url != ''")
            real_image_count = cursor.fetchone()[0]
            print(f"   Artículos con imagen real: {real_image_count:,}")
            
            print(f"   Cobertura de imágenes: {(real_image_count/total_articles*100):.1f}%")
            
            print("\n📊 2. ANALIZAR SQL ACTUAL (simulando get_top_articles_from_db):")
            
            # Este es el SQL que debería estar en app_BUENA.py
            current_sql = """
            SELECT 
                id,
                title,
                content,
                url,
                source,
                published_at,
                CASE 
                    WHEN original_image_url IS NOT NULL AND original_image_url != '' 
                    THEN '/static/images/news/' || SUBSTR(original_image_url, INSTR(original_image_url, 'news_') + 5)
                    ELSE image_url 
                END as image_url,
                risk_score,
                country,
                region
            FROM articles 
            WHERE (
                -- Incluir contenido geopolítico
                (LOWER(title || ' ' || COALESCE(content, '')) LIKE '%war%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%conflict%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%military%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%politics%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%government%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%security%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%nato%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%russia%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%china%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%israel%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%gaza%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%iran%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%guerra%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%militar%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%política%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%gobierno%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%seguridad%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%otan%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%rusia%' OR
                 LOWER(title || ' ' || COALESCE(content, '')) LIKE '%irán%')
            ) AND (
                -- Excluir contenido no geopolítico
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%sport%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%game%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%match%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%team%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%player%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%goal%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%football%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%soccer%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%basketball%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%emmy%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%oscar%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%movie%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%actor%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%hollywood%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%music%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%celebrity%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%iphone%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%apple%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%anime%' AND
                LOWER(title || ' ' || COALESCE(content, '')) NOT LIKE '%tv show%'
            )
            AND original_image_url IS NOT NULL AND original_image_url != ''
            ORDER BY published_at DESC 
            LIMIT 20
            """
            
            cursor.execute(current_sql)
            filtered_results = cursor.fetchall()
            
            print(f"   Artículos después del filtro: {len(filtered_results)}")
            
            if len(filtered_results) == 0:
                print("   ⚠️  NO HAY ARTÍCULOS que pasen el filtro completo!")
                print("   Esto puede ser porque el filtro es demasiado estricto.")
                
                # Probar sin el filtro de imagen
                cursor.execute(current_sql.replace("AND original_image_url IS NOT NULL AND original_image_url != ''", ""))
                results_without_image_filter = cursor.fetchall()
                print(f"   Sin filtro de imagen: {len(results_without_image_filter)} artículos")
                
                if len(results_without_image_filter) > 0:
                    print("   🔍 Ejemplos sin filtro de imagen:")
                    for i, row in enumerate(results_without_image_filter[:5], 1):
                        article_id, title, content, url, source, published_at, image_url, risk_score, country, region = row
                        title_short = title[:50] + "..." if len(title) > 50 else title
                        image_status = "📸" if image_url and 'placeholder' not in image_url else "❌"
                        print(f"      {i}. {image_status} [{source}] {title_short}")
            else:
                print("   ✅ Artículos encontrados con filtro completo:")
                for i, row in enumerate(filtered_results[:10], 1):
                    article_id, title, content, url, source, published_at, image_url, risk_score, country, region = row
                    title_short = title[:50] + "..." if len(title) > 50 else title
                    print(f"      {i}. 📸 [{source}] {title_short}")
                    
            print("\n📊 3. BUSCAR ARTÍCULOS PROBLEMÁTICOS:")
            
            # Buscar artículos que podrían no ser geopolíticos
            problematic_patterns = ['sport', 'game', 'emmy', 'oscar', 'movie', 'music', 'iphone', 'apple']
            
            for pattern in problematic_patterns:
                cursor.execute(f"""
                    SELECT COUNT(*) FROM articles 
                    WHERE LOWER(title) LIKE '%{pattern}%'
                """)
                count = cursor.fetchone()[0]
                if count > 0:
                    print(f"   ⚠️  {count} artículos contienen '{pattern}'")
                    
                    # Mostrar ejemplos
                    cursor.execute(f"""
                        SELECT title, source FROM articles 
                        WHERE LOWER(title) LIKE '%{pattern}%'
                        LIMIT 3
                    """)
                    examples = cursor.fetchall()
                    for title, source in examples:
                        title_short = title[:60] + "..." if len(title) > 60 else title
                        print(f"      - [{source}] {title_short}")
                        
            print("\n📊 4. ANÁLISIS DE IMÁGENES:")
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN image_url LIKE '%placeholder%' THEN 1 ELSE 0 END) as placeholders,
                    SUM(CASE WHEN original_image_url IS NOT NULL AND original_image_url != '' THEN 1 ELSE 0 END) as with_original
                FROM articles
            """)
            
            total, placeholders, with_original = cursor.fetchone()
            print(f"   Total: {total}, Con placeholder: {placeholders}, Con imagen original: {with_original}")
            
            # Verificar qué artículos tienen placeholder pero no imagen original
            cursor.execute("""
                SELECT id, title, source, image_url, original_image_url
                FROM articles 
                WHERE image_url LIKE '%placeholder%' 
                AND (original_image_url IS NULL OR original_image_url = '')
                LIMIT 10
            """)
            
            placeholder_articles = cursor.fetchall()
            if placeholder_articles:
                print(f"\n   📋 Artículos que necesitan procesamiento de imagen:")
                for article_id, title, source, image_url, original_image_url in placeholder_articles:
                    title_short = title[:50] + "..." if len(title) > 50 else title
                    print(f"      ID {article_id}: [{source}] {title_short}")
                    
    except Exception as e:
        print(f"❌ Error en diagnóstico: {e}")

if __name__ == "__main__":
    diagnose_current_articles()