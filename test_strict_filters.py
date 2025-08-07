#!/usr/bin/env python3
"""
Script para probar que los filtros estrictos funcionan correctamente.
Solo debe mostrar artículos con imagen original y en español.
"""

import sqlite3
import os
import sys

def test_strict_filters():
    """Probar filtros estrictos para hero y mosaico"""
    
    # Conectar a la base de datos
    db_path = 'data/geopolitical_intel.db'
    if not os.path.exists(db_path):
        print("❌ Base de datos no encontrada")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # FILTROS ESTRICTOS: igual que en la app
    base_filters = """
        WHERE (is_excluded IS NULL OR is_excluded != 1)
        AND (image_url IS NOT NULL AND image_url != '' 
             AND image_url NOT LIKE '%placeholder%'
             AND image_url NOT LIKE '%default%'
             AND image_url NOT LIKE '%noimage%')
        AND (language = 'es' OR 
             (is_translated = 1 AND original_language IS NOT NULL))
    """
    
    print("🔍 PROBANDO FILTROS ESTRICTOS...")
    print("Criterios: imagen original + idioma español")
    print("-" * 50)
    
    # Test 1: Artículo HERO (alto riesgo)
    print("\n1️⃣ TEST ARTÍCULO HERO (alto riesgo)")
    hero_query = f"""
        SELECT id, title, image_url, language, original_language, is_translated, risk_level
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
        print(f"✅ HERO encontrado:")
        print(f"   ID: {hero_result[0]}")
        print(f"   Título: {hero_result[1][:60]}...")
        print(f"   Imagen: {hero_result[2][:60]}...")
        print(f"   Idioma: {hero_result[3]}")
        print(f"   Idioma original: {hero_result[4]}")
        print(f"   Traducido: {hero_result[5]}")
        print(f"   Riesgo: {hero_result[6]}")
    else:
        print("❌ No se encontró artículo HERO con alto riesgo")
        
        # Probar con medium
        print("\n🔄 Probando con riesgo medium...")
        hero_query_medium = f"""
            SELECT id, title, image_url, language, original_language, is_translated, risk_level
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
            print(f"✅ HERO (medium) encontrado:")
            print(f"   ID: {hero_result[0]}")
            print(f"   Título: {hero_result[1][:60]}...")
            print(f"   Riesgo: {hero_result[6]}")
        else:
            print("❌ No se encontró artículo HERO con medium riesgo")
    
    # Test 2: Artículos MOSAICO (múltiples)
    print("\n\n2️⃣ TEST ARTÍCULOS MOSAICO (múltiples)")
    mosaico_query = f"""
        SELECT id, title, language, original_language, is_translated, risk_level
        FROM articles 
        {base_filters}
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
    
    cursor.execute(mosaico_query)
    mosaico_results = cursor.fetchall()
    
    if mosaico_results:
        print(f"✅ {len(mosaico_results)} artículos MOSAICO encontrados:")
        for i, article in enumerate(mosaico_results, 1):
            print(f"   {i}. ID: {article[0]} | Idioma: {article[2]} | Traducido: {article[4]} | Riesgo: {article[5]}")
    else:
        print("❌ No se encontraron artículos MOSAICO")
    
    # Test 3: Estadísticas generales
    print("\n\n3️⃣ ESTADÍSTICAS GENERALES")
    
    # Total de artículos que cumplen criterios
    cursor.execute(f"SELECT COUNT(*) FROM articles {base_filters}")
    total_filtered = cursor.fetchone()[0]
    
    # Total de artículos en la BD
    cursor.execute("SELECT COUNT(*) FROM articles WHERE (is_excluded IS NULL OR is_excluded != 1)")
    total_articles = cursor.fetchone()[0]
    
    # Artículos con imagen
    cursor.execute("""
        SELECT COUNT(*) FROM articles 
        WHERE (is_excluded IS NULL OR is_excluded != 1)
        AND (image_url IS NOT NULL AND image_url != '' 
             AND image_url NOT LIKE '%placeholder%'
             AND image_url NOT LIKE '%default%'
             AND image_url NOT LIKE '%noimage%')
    """)
    with_image = cursor.fetchone()[0]
    
    # Artículos en español
    cursor.execute("""
        SELECT COUNT(*) FROM articles 
        WHERE (is_excluded IS NULL OR is_excluded != 1)
        AND (language = 'es' OR 
             (is_translated = 1 AND original_language IS NOT NULL))
    """)
    in_spanish = cursor.fetchone()[0]
    
    print(f"📊 Total artículos (no excluidos): {total_articles}")
    print(f"📊 Con imagen original: {with_image}")
    print(f"📊 En español: {in_spanish}")
    print(f"📊 QUE CUMPLEN AMBOS CRITERIOS: {total_filtered}")
    print(f"📊 Porcentaje de cumplimiento: {(total_filtered/total_articles*100):.1f}%")
    
    conn.close()
    
    if total_filtered == 0:
        print("\n⚠️ WARNING: No hay artículos que cumplan ambos criterios!")
        print("   Necesitamos revisar traducción o filtros de imagen")
    else:
        print(f"\n✅ SUCCESS: {total_filtered} artículos cumplen criterios estrictos")

if __name__ == "__main__":
    test_strict_filters()
