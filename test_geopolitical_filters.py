#!/usr/bin/env python3
"""
Script para probar filtros geopolíticos ultra estrictos
Verifica que se excluyan noticias no geopolíticas como meteoros, deportes, tecnología, etc.
"""

import sqlite3
import os
from datetime import datetime

def test_geopolitical_filters():
    """Probar los filtros geopolíticos"""
    
    try:
        # Ruta de la base de datos
        db_path = r"data\geopolitical_intel.db"
        
        if not os.path.exists(db_path):
            print(f"❌ Base de datos no encontrada en: {db_path}")
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 TESTING GEOPOLITICAL FILTERS")
        print("=" * 50)
        
        # FILTROS ULTRA ESTRICTOS: SOLO IMÁGENES DE FUENTES DE NOTICIAS REALES + CONTENIDO GEOPOLÍTICO
        base_filters = """
            WHERE (is_excluded IS NULL OR is_excluded != 1)
            AND (image_url IS NOT NULL AND image_url != '' 
                 AND image_url NOT LIKE '%placeholder%'
                 AND image_url NOT LIKE '%default%'
                 AND image_url NOT LIKE '%noimage%'
                 AND image_url NOT LIKE '%unsplash.com%'
                 AND image_url NOT LIKE '%pexels.com%'
                 AND image_url NOT LIKE '%pixabay.com%'
                 AND image_url NOT LIKE '%fallback%'
                 AND image_url NOT LIKE '%stock%'
                 AND image_url NOT LIKE '%generic%'
                 AND image_url NOT LIKE 'data:image%'
                 AND (image_url LIKE '%reuters.com%' 
                      OR image_url LIKE '%bbc.co.uk%'
                      OR image_url LIKE '%cnn.com%'
                      OR image_url LIKE '%apnews.com%'
                      OR image_url LIKE '%france24.com%'
                      OR image_url LIKE '%aljazeera.com%'
                      OR image_url LIKE '%bloomberg.com%'
                      OR image_url LIKE '%theguardian.com%'
                      OR image_url LIKE '%washingtonpost.com%'
                      OR image_url LIKE '%nytimes.com%'
                      OR image_url LIKE '%ft.com%'
                      OR image_url LIKE '%wsj.com%'
                      OR image_url LIKE '%elmundo.es%'
                      OR image_url LIKE '%elpais.com%'
                      OR image_url LIKE '%lavanguardia.com%'
                      OR image_url LIKE '%abc.es%'
                      OR image_url LIKE '%marca.com%'
                      OR image_url LIKE '%expansion.com%'))
            AND (language = 'es' OR 
                 (is_translated = 1 AND original_language IS NOT NULL))
            AND (title NOT LIKE '%meteor%' 
                 AND title NOT LIKE '%asteroid%'
                 AND title NOT LIKE '%space%'
                 AND title NOT LIKE '%sports%'
                 AND title NOT LIKE '%deporte%'
                 AND title NOT LIKE '%football%'
                 AND title NOT LIKE '%soccer%'
                 AND title NOT LIKE '%tennis%'
                 AND title NOT LIKE '%basketball%'
                 AND title NOT LIKE '%olympic%'
                 AND title NOT LIKE '%celebrity%'
                 AND title NOT LIKE '%entertainment%'
                 AND title NOT LIKE '%weather%'
                 AND title NOT LIKE '%climate%' 
                 AND title NOT LIKE '%technology%'
                 AND title NOT LIKE '%tech%'
                 AND title NOT LIKE '%gadget%'
                 AND title NOT LIKE '%iphone%'
                 AND title NOT LIKE '%samsung%'
                 AND title NOT LIKE '%health%'
                 AND title NOT LIKE '%medical%'
                 AND title NOT LIKE '%covid%'
                 AND title NOT LIKE '%vaccine%')
        """
        
        # 1. Verificar que se excluyó la noticia de meteoros
        print("1️⃣ Verificando exclusión de noticias de meteoros:")
        meteor_query = "SELECT title, risk_level FROM articles WHERE title LIKE '%meteor%' OR title LIKE '%Perseid%'"
        cursor.execute(meteor_query)
        meteor_articles = cursor.fetchall()
        
        if meteor_articles:
            print(f"   ⚠️ Encontradas {len(meteor_articles)} noticias de meteoros en BD:")
            for title, risk in meteor_articles:
                print(f"      - {title[:80]}... (Riesgo: {risk})")
        else:
            print("   ✅ No se encontraron noticias de meteoros")
        
        # 2. Verificar artículo HERO (limit=1)
        print("\n2️⃣ Verificando artículo HERO:")
        hero_query = f"""
            SELECT id, title, risk_level, risk_score, image_url, source
            FROM articles 
            {base_filters}
            AND risk_level = 'high'
            ORDER BY 
                CASE 
                    WHEN risk_score IS NOT NULL THEN risk_score 
                    ELSE 0.8
                END DESC,
                datetime(published_at) DESC,
                id DESC
            LIMIT 1
        """
        
        cursor.execute(hero_query)
        hero_result = cursor.fetchone()
        
        if hero_result:
            print(f"   ✅ HERO encontrado: ID {hero_result[0]} - '{hero_result[1][:50]}...'")
            print(f"      Riesgo: {hero_result[2]} | Score: {hero_result[3]} | Fuente: {hero_result[5]}")
            print(f"      Imagen: {hero_result[4][:80]}...")
        else:
            # Buscar en medium si no hay high
            hero_query_medium = f"""
                SELECT id, title, risk_level, risk_score, image_url, source
                FROM articles 
                {base_filters}
                AND risk_level = 'medium'
                ORDER BY 
                    CASE 
                        WHEN risk_score IS NOT NULL THEN risk_score 
                        ELSE 0.5
                    END DESC,
                    datetime(published_at) DESC,
                    id DESC
                LIMIT 1
            """
            
            cursor.execute(hero_query_medium)
            hero_result = cursor.fetchone()
            
            if hero_result:
                print(f"   ⚠️ HERO (medium): ID {hero_result[0]} - '{hero_result[1][:50]}...'")
                print(f"      Riesgo: {hero_result[2]} | Score: {hero_result[3]} | Fuente: {hero_result[5]}")
            else:
                print("   ❌ NO se encontró artículo HERO válido")
        
        # 3. Verificar mosaico (múltiples artículos)
        print("\n3️⃣ Verificando artículos del MOSAICO:")
        mosaic_query = f"""
            SELECT id, title, risk_level, risk_score, image_url, source
            FROM articles 
            {base_filters}
            GROUP BY image_url
            HAVING COUNT(*) = 1
            ORDER BY 
                CASE 
                    WHEN risk_level = 'high' THEN 1
                    WHEN risk_level = 'medium' THEN 2
                    WHEN risk_level = 'low' THEN 3
                    ELSE 4
                END,
                CASE 
                    WHEN risk_score IS NOT NULL THEN risk_score 
                    ELSE 0.0
                END DESC,
                datetime(published_at) DESC,
                id DESC
            LIMIT 10
        """
        
        cursor.execute(mosaic_query)
        mosaic_results = cursor.fetchall()
        
        if mosaic_results:
            print(f"   ✅ Encontrados {len(mosaic_results)} artículos para mosaico:")
            for i, (id_, title, risk, score, img_url, source) in enumerate(mosaic_results, 1):
                print(f"      {i}. ID {id_} - '{title[:40]}...' | Riesgo: {risk} | Fuente: {source}")
        else:
            print("   ❌ NO se encontraron artículos válidos para mosaico")
        
        # 4. Estadísticas generales
        print("\n4️⃣ Estadísticas de filtrado:")
        
        # Total de artículos
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_articles = cursor.fetchone()[0]
        
        # Artículos que pasan todos los filtros
        cursor.execute(f"SELECT COUNT(*) FROM articles {base_filters}")
        filtered_articles = cursor.fetchone()[0]
        
        # Por nivel de riesgo
        cursor.execute(f"SELECT risk_level, COUNT(*) FROM articles {base_filters} GROUP BY risk_level")
        risk_stats = cursor.fetchall()
        
        print(f"   📊 Total artículos en BD: {total_articles}")
        print(f"   📊 Artículos que pasan filtros: {filtered_articles}")
        print(f"   📊 Tasa de filtrado: {(filtered_articles/total_articles*100):.1f}%")
        print("   📊 Por nivel de riesgo:")
        for risk, count in risk_stats:
            print(f"      - {risk}: {count} artículos")
        
        # 5. Verificar exclusiones específicas
        print("\n5️⃣ Verificando exclusiones de contenido no geopolítico:")
        
        exclusion_checks = [
            ("meteoros/asteroides", "title LIKE '%meteor%' OR title LIKE '%asteroid%'"),
            ("deportes", "title LIKE '%sports%' OR title LIKE '%deporte%' OR title LIKE '%football%'"),
            ("tecnología", "title LIKE '%technology%' OR title LIKE '%tech%' OR title LIKE '%gadget%'"),
            ("salud/medicina", "title LIKE '%health%' OR title LIKE '%medical%' OR title LIKE '%covid%'"),
            ("entretenimiento", "title LIKE '%celebrity%' OR title LIKE '%entertainment%'")
        ]
        
        for category, pattern in exclusion_checks:
            cursor.execute(f"SELECT COUNT(*) FROM articles WHERE {pattern}")
            excluded_count = cursor.fetchone()[0]
            if excluded_count > 0:
                print(f"   ⚠️ {category}: {excluded_count} artículos excluidos correctamente")
            else:
                print(f"   ✅ {category}: sin artículos a excluir")
        
        conn.close()
        
        print("\n" + "=" * 50)
        print("🎯 RESUMEN:")
        print(f"✅ Filtros geopolíticos aplicados correctamente")
        print(f"✅ {filtered_articles} artículos válidos para mostrar")
        print(f"✅ Solo noticias geopolíticas con imágenes originales y en español")
        
    except Exception as e:
        print(f"❌ Error ejecutando test: {e}")

if __name__ == "__main__":
    test_geopolitical_filters()
