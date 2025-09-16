#!/usr/bin/env python3
"""
Script para buscar artículos geopolíticos con imágenes en un rango más amplio de fechas
"""
import sqlite3
import os

def find_geopolitical_articles_with_images():
    """Busca artículos geopolíticos con imágenes en un rango más amplio"""
    try:
        db_path = "./data/geopolitical_intel.db"
        if not os.path.exists(db_path):
            print(f"❌ Base de datos no encontrada: {db_path}")
            return

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Buscar artículos geopolíticos con imágenes de los últimos 14 días
        cursor.execute("""
            SELECT 
                id, title, source, created_at,
                CASE 
                    WHEN original_image_url IS NOT NULL AND original_image_url != '' THEN 'extracted'
                    WHEN image_url IS NOT NULL AND image_url != '' AND image_url NOT LIKE '%placeholder%' THEN 'original'
                    ELSE 'none'
                END as image_status,
                CASE
                    WHEN (
                        LOWER(title) LIKE '%war%' OR LOWER(title) LIKE '%conflict%' OR
                        LOWER(title) LIKE '%military%' OR LOWER(title) LIKE '%politics%' OR
                        LOWER(title) LIKE '%government%' OR LOWER(title) LIKE '%security%' OR
                        LOWER(title) LIKE '%russia%' OR LOWER(title) LIKE '%ukraine%' OR
                        LOWER(title) LIKE '%china%' OR LOWER(title) LIKE '%iran%' OR
                        LOWER(title) LIKE '%israel%' OR LOWER(title) LIKE '%gaza%' OR
                        LOWER(title) LIKE '%nato%' OR LOWER(title) LIKE '%drone%' OR
                        LOWER(title) LIKE '%trump%' OR LOWER(title) LIKE '%biden%' OR
                        LOWER(title) LIKE '%harris%' OR LOWER(title) LIKE '%rubio%' OR
                        LOWER(title) LIKE '%nuclear%' OR LOWER(title) LIKE '%sanction%' OR
                        LOWER(title) LIKE '%diplomat%' OR LOWER(title) LIKE '%minister%' OR
                        LOWER(title) LIKE '%president%' OR LOWER(title) LIKE '%election%' OR
                        LOWER(title) LIKE '%congress%' OR LOWER(title) LIKE '%senate%' OR
                        LOWER(title) LIKE '%parliament%' OR LOWER(title) LIKE '%intelligence%' OR
                        LOWER(title) LIKE '%terrorism%' OR LOWER(title) LIKE '%crisis%' OR
                        LOWER(title) LIKE '%revolution%' OR LOWER(title) LIKE '%protest%' OR
                        LOWER(title) LIKE '%violence%' OR LOWER(title) LIKE '%border%' OR
                        LOWER(title) LIKE '%refugee%' OR LOWER(title) LIKE '%myanmar%' OR
                        LOWER(title) LIKE '%venezuela%' OR LOWER(title) LIKE '%nepal%' OR
                        LOWER(title) LIKE '%romania%' OR LOWER(title) LIKE '%poland%' OR
                        LOWER(title) LIKE '%syria%' OR LOWER(title) LIKE '%lebanon%' OR
                        LOWER(title) LIKE '%turkey%' OR LOWER(title) LIKE '%afghanistan%' OR
                        LOWER(title) LIKE '%iraq%' OR LOWER(title) LIKE '%yemen%'
                    ) THEN 'YES'
                    ELSE 'NO'
                END as is_geopolitical
            FROM articles 
            WHERE 
                -- Solo artículos con imagen
                (
                    (original_image_url IS NOT NULL AND original_image_url != '') OR
                    (image_url IS NOT NULL AND image_url != '' AND 
                     image_url NOT LIKE '%placeholder%' AND 
                     image_url NOT LIKE '%via.placeholder%')
                ) AND
                
                -- Campos básicos
                title IS NOT NULL AND title != '' AND
                content IS NOT NULL AND content != '' AND
                
                -- Últimos 14 días en lugar de 7
                created_at >= datetime('now', '-14 days') AND
                
                -- Excluir deportes y entretenimiento claramente
                LOWER(title) NOT LIKE '%sport%' AND LOWER(title) NOT LIKE '%sports%' AND
                LOWER(title) NOT LIKE '%emmy%' AND LOWER(title) NOT LIKE '%emmys%' AND
                LOWER(title) NOT LIKE '%demon slayer%' AND LOWER(title) NOT LIKE '%anime%' AND
                LOWER(title) NOT LIKE '%giants%' AND LOWER(title) NOT LIKE '%cowboys%' AND
                LOWER(title) NOT LIKE '%broncos%' AND LOWER(title) NOT LIKE '%colts%' AND
                LOWER(title) NOT LIKE '%football%' AND LOWER(title) NOT LIKE '%nfl%' AND
                LOWER(title) NOT LIKE '%basketball%' AND LOWER(title) NOT LIKE '%nba%' AND
                source NOT LIKE '%Sports%' AND source NOT LIKE '%Entertainment%' AND
                source NOT LIKE '%ESPN%' AND source NOT LIKE '%CBS Sports%' AND
                source NOT LIKE '%NBC Sports%' AND source NOT LIKE '%Giants.com%'
                
            ORDER BY created_at DESC
            LIMIT 30
        """)

        articles = cursor.fetchall()
        conn.close()

        print("🔍 BÚSQUEDA AMPLIADA: Artículos con imágenes (14 días)")
        print("=" * 60)

        geopolitical_with_image = 0
        total_with_image = len(articles)

        for i, (article_id, title, source, created_at, image_status, is_geopolitical) in enumerate(articles, 1):
            geo_icon = "🎯" if is_geopolitical == "YES" else "❌"
            img_icon = "✅" if image_status != "none" else "❌"
            
            print(f"\n🔸 Artículo #{i} (ID: {article_id})")
            print(f"   📰 {title[:70]}...")
            print(f"   🌐 {source}")
            print(f"   📅 {created_at}")
            print(f"   {img_icon} Imagen: {image_status}")
            print(f"   {geo_icon} Geopolítico: {is_geopolitical}")
            
            if is_geopolitical == "YES" and image_status != "none":
                geopolitical_with_image += 1
                print(f"   ✅ VÁLIDO PARA MOSAICO")

        print("\n" + "=" * 60)
        print(f"📊 RESUMEN AMPLIADO:")
        print(f"   📈 Total con imagen (14 días): {total_with_image}")
        print(f"   🎯 Geopolíticos con imagen: {geopolitical_with_image}")
        print(f"   📊 Porcentaje válido: {(geopolitical_with_image/total_with_image*100):.1f}%" if total_with_image > 0 else "   📊 Sin datos")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    find_geopolitical_articles_with_images()