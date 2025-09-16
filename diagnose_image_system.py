#!/usr/bin/env python3
"""
Analizar el estado actual de las imágenes en la base de datos y encontrar el origen del problema
"""
import sqlite3
import requests
from urllib.parse import urljoin, urlparse
import re

def analyze_current_images():
    """Analizar las URLs de imagen actuales en la base de datos"""
    print("🔍 ANALIZANDO IMÁGENES EN LA BASE DE DATOS")
    print("=" * 60)
    
    try:
        db_path = "./data/geopolitical_intel.db"
        
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Obtener estadísticas generales
            cursor.execute("SELECT COUNT(*) as total FROM articles")
            total = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as with_image FROM articles WHERE image_url IS NOT NULL AND image_url != ''")
            with_image = cursor.fetchone()['with_image']
            
            print(f"📊 ESTADÍSTICAS GENERALES:")
            print(f"- Total artículos: {total}")
            print(f"- Con imagen: {with_image}")
            print(f"- Sin imagen: {total - with_image}")
            print(f"- Cobertura: {(with_image/total*100):.1f}%")
            
            # Analizar tipos de URLs
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN image_url LIKE '%via.placeholder%' THEN 'via.placeholder'
                        WHEN image_url LIKE '%placeholder%' THEN 'other_placeholder'
                        WHEN image_url LIKE '%picsum%' THEN 'picsum'
                        WHEN image_url LIKE '%unsplash%' THEN 'unsplash'
                        WHEN image_url LIKE 'http%' THEN 'external_url'
                        WHEN image_url LIKE '/static/%' THEN 'local_file'
                        ELSE 'unknown'
                    END as url_type,
                    COUNT(*) as count
                FROM articles 
                WHERE image_url IS NOT NULL AND image_url != ''
                GROUP BY url_type
                ORDER BY count DESC
            """)
            
            url_types = cursor.fetchall()
            
            print(f"\n🔗 TIPOS DE URLs DE IMAGEN:")
            for row in url_types:
                print(f"- {row['url_type']}: {row['count']} artículos")
            
            # Mostrar ejemplos de URLs reales vs placeholders
            cursor.execute("""
                SELECT id, title, url, image_url, source 
                FROM articles 
                WHERE image_url IS NOT NULL AND image_url != ''
                ORDER BY id DESC 
                LIMIT 10
            """)
            
            examples = cursor.fetchall()
            
            print(f"\n📰 EJEMPLOS DE ARTÍCULOS RECIENTES:")
            for article in examples:
                print(f"\n- ID {article['id']}: {article['title'][:50]}...")
                print(f"  Source: {article['source']}")
                print(f"  URL: {article['url']}")
                print(f"  Image: {article['image_url']}")
                
                # Verificar si la URL del artículo funciona
                if article['url']:
                    try:
                        response = requests.head(article['url'], timeout=5)
                        status = f"✅ {response.status_code}" if response.status_code == 200 else f"❌ {response.status_code}"
                    except:
                        status = "❌ No accesible"
                    print(f"  Status: {status}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

def test_image_extraction_from_url(url):
    """Probar extracción de imagen desde una URL de noticia"""
    print(f"\n🧪 PROBANDO EXTRACCIÓN DE IMAGEN DESDE:")
    print(f"   {url}")
    
    try:
        # Simular lo que haría un extractor de imágenes
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print(f"✅ Página accesible ({len(response.content)} bytes)")
            
            # Buscar imágenes en el HTML
            import re
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar imágenes principales
            img_selectors = [
                'meta[property="og:image"]',
                'meta[name="twitter:image"]', 
                'img[class*="featured"]',
                'img[class*="hero"]',
                'img[class*="main"]',
                'article img',
                '.article img',
                '.content img'
            ]
            
            found_images = []
            for selector in img_selectors:
                if 'meta' in selector:
                    elements = soup.select(selector)
                    for elem in elements:
                        img_url = elem.get('content')
                        if img_url:
                            found_images.append((selector, img_url))
                else:
                    images = soup.select(selector)
                    for img in images[:2]:  # Solo primeras 2 por selector
                        img_url = img.get('src') or img.get('data-src')
                        if img_url:
                            found_images.append((selector, img_url))
            
            if found_images:
                print(f"🖼️  IMÁGENES ENCONTRADAS ({len(found_images)}):")
                for i, (selector, img_url) in enumerate(found_images[:5]):
                    # Convertir URL relativa a absoluta
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    elif img_url.startswith('/'):
                        img_url = urljoin(url, img_url)
                    
                    print(f"   {i+1}. {selector}: {img_url}")
                    
                    # Probar si la imagen carga
                    try:
                        img_response = requests.head(img_url, timeout=3)
                        if img_response.status_code == 200:
                            content_type = img_response.headers.get('content-type', '')
                            if 'image' in content_type:
                                print(f"      ✅ Imagen válida ({content_type})")
                                return img_url  # Retornar la primera imagen válida
                            else:
                                print(f"      ❌ No es imagen ({content_type})")
                        else:
                            print(f"      ❌ Error {img_response.status_code}")
                    except:
                        print(f"      ❌ No accesible")
                        
                return found_images[0][1] if found_images else None
            else:
                print("❌ No se encontraron imágenes")
                return None
        else:
            print(f"❌ Error HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error extrayendo imagen: {e}")
        return None

def main():
    """Función principal de análisis"""
    print("🔍 DIAGNÓSTICO: Sistema de imágenes de noticias")
    print("=" * 70)
    
    # Paso 1: Analizar base de datos actual
    analyze_current_images()
    
    # Paso 2: Probar extracción en una URL real
    print("\n" + "=" * 70)
    print("🧪 PRUEBA DE EXTRACCIÓN DE IMAGEN")
    
    # Obtener una URL de artículo real para probar
    try:
        db_path = "./data/geopolitical_intel.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT url FROM articles 
                WHERE url IS NOT NULL AND url != '' 
                AND url NOT LIKE '%placeholder%'
                ORDER BY id DESC 
                LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                test_url = row[0]
                extracted_image = test_image_extraction_from_url(test_url)
                
                if extracted_image:
                    print(f"\n🎉 IMAGEN EXTRAÍDA EXITOSAMENTE:")
                    print(f"   {extracted_image}")
                    print(f"\n💡 CONCLUSIÓN: Es posible extraer imágenes reales")
                else:
                    print(f"\n⚠️  No se pudo extraer imagen de esta URL")
            else:
                print("❌ No hay URLs de artículos para probar")
                
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
    
    print("\n" + "=" * 70)
    print("📋 RESUMEN DEL DIAGNÓSTICO:")
    print("1. La base de datos actual usa mayormente placeholders")
    print("2. Es técnicamente posible extraer imágenes reales de las URLs")  
    print("3. Se necesita implementar un sistema automático de extracción")
    print("4. Se debe integrar en el proceso de ingesta de noticias")

if __name__ == "__main__":
    main()