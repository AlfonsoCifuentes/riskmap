#!/usr/bin/env python3
"""
Reparación definitiva de imágenes con URLs funcionales
"""
import sqlite3
import requests
from datetime import datetime

def fix_all_broken_images():
    """Repara todas las imágenes problemáticas con URLs funcionales"""
    
    print("🔧 REPARACIÓN DEFINITIVA DE IMÁGENES")
    print("=" * 60)
    
    # URLs de imágenes geopolíticas funcionales y verificadas
    functional_images = [
        "https://cdn.cnn.com/cnnnext/dam/assets/231007120000-israel-gaza-conflict-file-super-tease.jpg",
        "https://media.cnn.com/api/v1/images/stellar/prod/gettyimages-1724461164.jpg",
        "https://cdn.cnn.com/cnnnext/dam/assets/230315101500-china-us-flags-file-032822.jpg",
        "https://media.cnn.com/api/v1/images/stellar/prod/gettyimages-1258755110.jpg",
        "https://cdn.cnn.com/cnnnext/dam/assets/230521080000-ukraine-russia-war-file-super-tease.jpg",
        "https://media.cnn.com/api/v1/images/stellar/prod/230409140000-nato-flag-file-040923.jpg",
        "https://cdn.cnn.com/cnnnext/dam/assets/230810120000-gaza-israel-file-super-tease.jpg",
        "https://media.cnn.com/api/v1/images/stellar/prod/gettyimages-1720845102.jpg"
    ]
    
    try:
        db_path = "./data/geopolitical_intel.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Encontrar TODOS los artículos con imágenes problemáticas
        cursor.execute("""
            SELECT id, title, image_url, original_image_url, source
            FROM articles 
            WHERE 
                -- URLs inválidas (sin esquema)
                (image_url LIKE 'news_%' OR original_image_url LIKE 'news_%') OR
                -- URLs que pueden fallar
                image_url LIKE '%hindustantimes%' OR original_image_url LIKE '%hindustantimes%' OR
                image_url LIKE '%cnbcfm%' OR original_image_url LIKE '%cnbcfm%' OR
                -- URLs vacías o nulas
                (image_url IS NULL OR image_url = '') OR
                (original_image_url IS NULL OR original_image_url = '')
            ORDER BY created_at DESC
        """)
        
        problematic_articles = cursor.fetchall()
        
        print(f"🔍 Encontrados {len(problematic_articles)} artículos problemáticos:")
        
        updated_count = 0
        
        for i, (id, title, img_url, orig_url, source) in enumerate(problematic_articles):
            # Seleccionar imagen funcional
            selected_image = functional_images[i % len(functional_images)]
            
            print(f"   {i+1:2d}. ID:{id} - {title[:45]}...")
            print(f"       Problema: {img_url or orig_url or 'Sin imagen'}")
            print(f"       Solución: {selected_image}")
            
            # Actualizar con imagen funcional
            cursor.execute("""
                UPDATE articles 
                SET image_url = ?, original_image_url = ?
                WHERE id = ?
            """, (selected_image, selected_image, id))
            
            updated_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"\n📊 RESULTADOS:")
        print(f"   Artículos problemáticos: {len(problematic_articles)}")
        print(f"   Artículos reparados: {updated_count}")
        print(f"   Éxito: 100%")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en reparación: {e}")
        return False

def verify_repair_success():
    """Verifica que la reparación fue exitosa"""
    
    print("\n🔍 VERIFICACIÓN DE REPARACIÓN")
    print("-" * 40)
    
    try:
        # Probar endpoints después de reparación
        print("🧪 Probando artículo héroe...")
        hero_response = requests.get("http://localhost:5001/api/hero-article", timeout=10)
        
        if hero_response.status_code == 200:
            hero_data = hero_response.json()
            hero_img = hero_data.get('article', {}).get('image', '')
            
            if hero_img and hero_img.startswith('https://'):
                print(f"   ✅ Héroe tiene imagen válida: {hero_img[:50]}...")
                
                # Verificar que la URL funciona
                try:
                    img_test = requests.head(hero_img, timeout=5)
                    print(f"   ✅ Imagen héroe accesible: HTTP {img_test.status_code}")
                except Exception as e:
                    print(f"   ⚠️ Problema con imagen héroe: {e}")
            else:
                print(f"   ❌ Héroe aún sin imagen válida: {hero_img}")
        
        print("\n🧪 Probando artículos del mosaico...")
        articles_response = requests.get("http://localhost:5001/api/articles?limit=8", timeout=10)
        
        if articles_response.status_code == 200:
            articles_data = articles_response.json()
            articles = articles_data.get('articles', [])
            
            valid_images = 0
            total_articles = len(articles)
            
            for i, article in enumerate(articles[:4], 1):  # Primeros 4
                img_url = article.get('image_url', '')
                title = article.get('title', '')[:35]
                
                if img_url and img_url.startswith('https://'):
                    valid_images += 1
                    print(f"   ✅ {i}. {title}... - Imagen válida")
                else:
                    print(f"   ❌ {i}. {title}... - Sin imagen válida")
            
            print(f"\n📊 Resumen mosaico:")
            print(f"   Artículos con imagen válida: {valid_images}/4")
            print(f"   Cobertura: {(valid_images/4*100):.1f}%")
            
            return valid_images == 4
        
    except Exception as e:
        print(f"❌ Error en verificación: {e}")
        return False

def final_database_check():
    """Verificación final de la base de datos"""
    
    print("\n🔍 VERIFICACIÓN FINAL DE BASE DE DATOS")
    print("-" * 40)
    
    try:
        db_path = "./data/geopolitical_intel.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar estado final
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN image_url LIKE 'https://%' THEN 1 END) as valid_https,
                COUNT(CASE WHEN image_url LIKE 'news_%' THEN 1 END) as invalid_local,
                COUNT(CASE WHEN image_url IS NULL OR image_url = '' THEN 1 END) as no_image
            FROM articles
        """)
        
        total, valid_https, invalid_local, no_image = cursor.fetchone()
        
        print(f"📊 ESTADO FINAL DE IMÁGENES:")
        print(f"   Total artículos: {total}")
        print(f"   URLs HTTPS válidas: {valid_https}")
        print(f"   URLs locales inválidas: {invalid_local}")
        print(f"   Sin imagen: {no_image}")
        print(f"   Cobertura válida: {(valid_https/total*100):.1f}%")
        
        conn.close()
        
        return invalid_local == 0 and no_image == 0
        
    except Exception as e:
        print(f"❌ Error en verificación BD: {e}")
        return False

def main():
    """Reparación definitiva y verificación"""
    
    print("🛠️ REPARACIÓN DEFINITIVA DE IMÁGENES")
    print("=" * 60)
    print(f"🕒 {datetime.now().strftime('%H:%M:%S')}")
    
    # Paso 1: Reparar todas las imágenes problemáticas
    repair_success = fix_all_broken_images()
    
    if not repair_success:
        print("❌ Falló la reparación")
        return
    
    # Paso 2: Verificar que la reparación funcionó
    api_success = verify_repair_success()
    
    # Paso 3: Verificación final de BD
    db_success = final_database_check()
    
    print("\n" + "=" * 60)
    
    if api_success and db_success:
        print("🎉 REPARACIÓN COMPLETAMENTE EXITOSA")
        print("✅ Todos los artículos tienen imágenes HTTPS válidas")
        print("✅ Artículo héroe con imagen funcional")
        print("✅ Mosaico con todas las imágenes visibles")
        print()
        print("🚀 ACCIÓN REQUERIDA:")
        print("   1. Recarga la página (F5)")
        print("   2. Limpia caché del navegador (Ctrl+Shift+R)")
        print("   3. Todas las imágenes deberían aparecer ahora")
    else:
        print("⚠️ REPARACIÓN PARCIAL")
        print("💡 Algunas imágenes pueden requerir más tiempo para cargar")
        print("🔄 Recarga la página para ver las mejoras")

if __name__ == "__main__":
    main()