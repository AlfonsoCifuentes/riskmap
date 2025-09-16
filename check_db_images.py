#!/usr/bin/env python3
"""
Verificar el estado de las imágenes en la base de datos
"""
import sqlite3

def check_images_in_db():
    """Verificar qué tipos de URLs de imagen tenemos en la DB"""
    print("🔍 Verificando URLs de imagen en la base de datos...")
    
    try:
        db_path = "./data/geopolitical_intel.db"
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Total de artículos
            cursor.execute("SELECT COUNT(*) FROM articles")
            total = cursor.fetchone()[0]
            print(f"📊 Total artículos: {total}")
            
            # Artículos con imagen
            cursor.execute("SELECT COUNT(*) FROM articles WHERE image_url IS NOT NULL AND image_url != ''")
            with_images = cursor.fetchone()[0]
            print(f"📊 Artículos con alguna imagen: {with_images}")
            
            # Tipos de imágenes
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN image_url LIKE '%placeholder%' THEN 'placeholder'
                        WHEN image_url LIKE '%picsum.photos%' THEN 'picsum'
                        WHEN image_url LIKE '%via.placeholder%' THEN 'via.placeholder'
                        WHEN image_url IS NULL OR image_url = '' THEN 'null/empty'
                        ELSE 'real'
                    END as image_type,
                    COUNT(*) as count
                FROM articles 
                WHERE image_url IS NOT NULL AND image_url != ''
                GROUP BY 
                    CASE 
                        WHEN image_url LIKE '%placeholder%' THEN 'placeholder'
                        WHEN image_url LIKE '%picsum.photos%' THEN 'picsum'
                        WHEN image_url LIKE '%via.placeholder%' THEN 'via.placeholder'
                        WHEN image_url IS NULL OR image_url = '' THEN 'null/empty'
                        ELSE 'real'
                    END
                ORDER BY count DESC
            """)
            
            types = cursor.fetchall()
            print("\n📸 Tipos de imágenes:")
            for img_type, count in types:
                print(f"- {img_type}: {count} artículos")
            
            # Mostrar algunas URLs reales como ejemplo
            cursor.execute("""
                SELECT image_url, title
                FROM articles 
                WHERE image_url IS NOT NULL 
                AND image_url != ''
                AND image_url NOT LIKE '%placeholder%'
                AND image_url NOT LIKE '%picsum%'
                AND image_url NOT LIKE '%via.placeholder%'
                LIMIT 5
            """)
            
            real_images = cursor.fetchall()
            print(f"\n🖼️  URLs de imágenes reales (primeras 5):")
            for url, title in real_images:
                print(f"- {url}")
                print(f"  📰 {title[:80]}...")
                print()
            
            # Si no hay imágenes reales, relajar filtros para debug
            if not real_images:
                print("⚠️  No hay imágenes reales. Revisando todas las imágenes...")
                cursor.execute("""
                    SELECT image_url, title, id
                    FROM articles 
                    WHERE image_url IS NOT NULL AND image_url != ''
                    ORDER BY id DESC
                    LIMIT 10
                """)
                
                all_images = cursor.fetchall()
                print("\n📸 Últimas 10 imágenes (cualquier tipo):")
                for url, title, art_id in all_images:
                    print(f"- ID {art_id}: {url}")
                    print(f"  📰 {title[:60]}...")
                    print()
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_images_in_db()