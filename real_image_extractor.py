#!/usr/bin/env python3
"""
Extractor REAL de imágenes originales desde las fuentes
Obtiene las imágenes ORIGINALES de cada URL de artículo usando web scraping
"""
import sqlite3
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import time
from datetime import datetime
import json

class RealImageExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
    def extract_image_from_url(self, url, title=""):
        """Extrae la imagen ORIGINAL desde la URL del artículo"""
        
        try:
            print(f"🔍 Extrayendo imagen de: {url}")
            
            # Realizar request con timeout
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Estrategias múltiples para encontrar imagen principal
            image_candidates = []
            
            # 1. Open Graph image
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                image_candidates.append(('og:image', og_image.get('content')))
            
            # 2. Twitter Card image
            twitter_image = soup.find('meta', name='twitter:image')
            if twitter_image and twitter_image.get('content'):
                image_candidates.append(('twitter:image', twitter_image.get('content')))
                
            # 3. Schema.org image
            schema_image = soup.find('meta', attrs={'itemprop': 'image'})
            if schema_image and schema_image.get('content'):
                image_candidates.append(('schema:image', schema_image.get('content')))
            
            # 4. Buscar imágenes en el artículo principal
            article_images = []
            
            # CNN específico
            if 'cnn.com' in url:
                cnn_images = soup.find_all('img', class_=re.compile(r'image|photo|media'))
                for img in cnn_images[:3]:
                    if img.get('src'):
                        article_images.append(('cnn-article', img.get('src')))
            
            # BBC específico
            elif 'bbc.com' in url:
                bbc_images = soup.find_all('img', class_=re.compile(r'gel-|media'))
                for img in bbc_images[:3]:
                    if img.get('src'):
                        article_images.append(('bbc-article', img.get('src')))
            
            # Reuters específico
            elif 'reuters.com' in url:
                reuters_images = soup.find_all('img', class_=re.compile(r'Image|image'))
                for img in reuters_images[:3]:
                    if img.get('src'):
                        article_images.append(('reuters-article', img.get('src')))
            
            # Al Jazeera específico
            elif 'aljazeera.com' in url:
                aj_images = soup.find_all('img', class_=re.compile(r'responsive|article'))
                for img in aj_images[:3]:
                    if img.get('src'):
                        article_images.append(('aljazeera-article', img.get('src')))
            
            # Genérico: buscar imágenes principales
            else:
                main_images = soup.find_all('img', class_=re.compile(r'main|hero|featured|lead|primary'))
                for img in main_images[:2]:
                    if img.get('src'):
                        article_images.append(('generic-main', img.get('src')))
                        
                # También buscar en figure/picture tags
                figures = soup.find_all(['figure', 'picture'])
                for fig in figures[:2]:
                    img = fig.find('img')
                    if img and img.get('src'):
                        article_images.append(('generic-figure', img.get('src')))
            
            # Combinar todos los candidatos
            all_candidates = image_candidates + article_images
            
            # Filtrar y validar candidatos
            for source, img_url in all_candidates:
                
                # Convertir URL relativa a absoluta
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif img_url.startswith('/'):
                    img_url = urljoin(url, img_url)
                
                # Filtrar URLs no válidas
                if not img_url.startswith(('http://', 'https://')):
                    continue
                    
                # Evitar imágenes muy pequeñas o logos
                if any(skip in img_url.lower() for skip in ['logo', 'icon', 'avatar', 'thumbnail']):
                    continue
                
                # Verificar que la imagen sea accesible
                if self.verify_image_url(img_url):
                    print(f"   ✅ Imagen encontrada ({source}): {img_url[:60]}...")
                    return img_url
                    
            print(f"   ❌ No se encontró imagen válida")
            return None
            
        except Exception as e:
            print(f"   ❌ Error extrayendo imagen: {e}")
            return None
    
    def verify_image_url(self, img_url):
        """Verifica que una URL de imagen sea accesible"""
        try:
            # HEAD request para verificar sin descargar
            response = self.session.head(img_url, timeout=10, allow_redirects=True)
            
            # Verificar código de estado
            if response.status_code not in [200, 301, 302]:
                return False
                
            # Verificar tipo de contenido
            content_type = response.headers.get('content-type', '').lower()
            if not content_type.startswith('image/'):
                # Algunos sitios no ponen content-type correcto en HEAD
                # Probar GET pequeño
                try:
                    get_response = self.session.get(img_url, timeout=5, stream=True)
                    chunk = next(iter(get_response.iter_content(1024)), b'')
                    
                    # Verificar magic bytes de imagen
                    if chunk.startswith(b'\xff\xd8\xff') or chunk.startswith(b'\x89PNG') or chunk.startswith(b'GIF8'):
                        return True
                except:
                    pass
                return False
            
            return True
            
        except Exception:
            return False

def extract_all_original_images():
    """Extrae las imágenes originales de todos los artículos geopolíticos"""
    
    print("🎯 EXTRAYENDO IMÁGENES ORIGINALES DE TODAS LAS NOTICIAS")
    print("=" * 65)
    print(f"🕒 {datetime.now().strftime('%H:%M:%S')}")
    
    extractor = RealImageExtractor()
    
    try:
        db_path = "./data/geopolitical_intel.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Obtener todos los artículos geopolíticos sin imagen o con imagen incorrecta
        cursor.execute("""
            SELECT id, title, url, source 
            FROM articles 
            WHERE (image_url IS NULL OR image_url = '' OR 
                   image_url LIKE '%placeholder%' OR
                   image_url LIKE '%default%')
            ORDER BY created_at DESC
        """)
        
        articles = cursor.fetchall()
        
        if not articles:
            print("ℹ️ Todos los artículos ya tienen imágenes. Verificando calidad...")
            
            # Verificar artículos existentes
            cursor.execute("""
                SELECT id, title, url, source, image_url
                FROM articles 
                ORDER BY created_at DESC
                LIMIT 20
            """)
            articles = cursor.fetchall()
            
            print(f"🔍 Verificando {len(articles)} artículos existentes...")
            
            updated_count = 0
            
            for id, title, url, source, current_img in articles:
                print(f"\n📰 [{id}] {title[:50]}...")
                print(f"    🔗 {url}")
                print(f"    📸 Actual: {current_img[:60] if current_img else 'Sin imagen'}...")
                
                # Extraer imagen original
                original_img = extractor.extract_image_from_url(url, title)
                
                if original_img and original_img != current_img:
                    # Actualizar con imagen original
                    cursor.execute("""
                        UPDATE articles 
                        SET image_url = ?, original_image_url = ?
                        WHERE id = ?
                    """, (original_img, original_img, id))
                    
                    print(f"    ✅ ACTUALIZADA: {original_img[:60]}...")
                    updated_count += 1
                    
                elif original_img:
                    print(f"    ✅ IMAGEN YA CORRECTA")
                else:
                    print(f"    ⚠️ NO SE PUDO EXTRAER IMAGEN")
                
                # Pausa para no sobrecargar
                time.sleep(1)
        
        else:
            print(f"🔍 Procesando {len(articles)} artículos sin imagen...")
            
            updated_count = 0
            
            for id, title, url, source in articles:
                print(f"\n📰 [{id}] {title[:50]}...")
                print(f"    🔗 {url}")
                
                # Extraer imagen original
                original_img = extractor.extract_image_from_url(url, title)
                
                if original_img:
                    # Actualizar con imagen original
                    cursor.execute("""
                        UPDATE articles 
                        SET image_url = ?, original_image_url = ?
                        WHERE id = ?
                    """, (original_img, original_img, id))
                    
                    print(f"    ✅ IMAGEN EXTRAÍDA: {original_img[:60]}...")
                    updated_count += 1
                    
                else:
                    print(f"    ❌ NO SE PUDO EXTRAER IMAGEN")
                
                # Pausa para no sobrecargar los sitios
                time.sleep(1.5)
        
        conn.commit()
        conn.close()
        
        print(f"\n📊 RESULTADOS FINALES:")
        print(f"   Artículos procesados: {len(articles)}")
        print(f"   Imágenes extraídas: {updated_count}")
        print(f"   Tasa de éxito: {(updated_count/len(articles)*100):.1f}%" if articles else "100%")
        
        return updated_count > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def verify_final_results():
    """Verifica que TODAS las noticias geopolíticas tengan imagen"""
    
    print(f"\n🔍 VERIFICACIÓN FINAL")
    print("-" * 40)
    
    try:
        # Verificar vía API
        response = requests.get("http://localhost:5001/api/articles?limit=10", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            
            print(f"📊 Estado actual del mosaico:")
            
            with_image = 0
            without_image = 0
            
            for i, article in enumerate(articles[:10], 1):
                title = article.get('title', '')[:40]
                img_url = article.get('image_url', '')
                
                if img_url and img_url.startswith('http'):
                    status = "✅"
                    with_image += 1
                else:
                    status = "❌"
                    without_image += 1
                
                print(f"   {i}. {status} {title}...")
                
            print(f"\n📈 ESTADÍSTICAS:")
            print(f"   ✅ Con imagen: {with_image}")
            print(f"   ❌ Sin imagen: {without_image}")
            print(f"   📊 Porcentaje con imagen: {(with_image/(with_image+without_image)*100):.1f}%")
            
            return with_image, without_image
            
    except Exception as e:
        print(f"❌ Error verificando: {e}")
        return 0, 0

def main():
    """Función principal"""
    
    print("🚀 EXTRACTOR DE IMÁGENES ORIGINALES REALES")
    print("=" * 65)
    
    # Extraer imágenes originales de todas las fuentes
    success = extract_all_original_images()
    
    if success:
        print("\n✅ EXTRACCIÓN COMPLETADA")
        
        # Verificar resultados
        with_img, without_img = verify_final_results()
        
        print(f"\n🎯 RESULTADO:")
        if without_img == 0:
            print("   🎉 ¡PERFECTO! TODAS las noticias tienen su imagen original")
            print("   🚀 RECARGA LA PÁGINA para ver el resultado")
        else:
            print(f"   ⚠️ Quedan {without_img} noticias sin imagen")
            print("   💡 Se necesita otra pasada de extracción")
    else:
        print("❌ Error en la extracción")

if __name__ == "__main__":
    main()