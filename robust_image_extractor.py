#!/usr/bin/env python3
"""
Extractor REAL de imágenes originales - VERSIÓN CORREGIDA
Obtiene las imágenes ORIGINALES de cada URL de artículo usando web scraping robusto
"""
import sqlite3
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import time
from datetime import datetime

class RobustImageExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        })
        
    def extract_image_from_url(self, url, title=""):
        """Extrae la imagen ORIGINAL desde la URL del artículo - MÉTODO ROBUSTO"""
        
        try:
            print(f"🔍 Extrayendo de: {url[:60]}...")
            
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Lista de candidatos a imagen
            image_candidates = []
            
            # 1. Meta Open Graph
            try:
                og_tags = soup.find_all('meta', {'property': 'og:image'})
                for tag in og_tags:
                    if tag.get('content'):
                        image_candidates.append(('og:image', tag.get('content')))
            except:
                pass
            
            # 2. Meta Twitter
            try:
                twitter_tags = soup.find_all('meta', {'name': 'twitter:image'})
                for tag in twitter_tags:
                    if tag.get('content'):
                        image_candidates.append(('twitter:image', tag.get('content')))
            except:
                pass
            
            # 3. Schema.org
            try:
                schema_tags = soup.find_all('meta', {'itemprop': 'image'})
                for tag in schema_tags:
                    if tag.get('content'):
                        image_candidates.append(('schema:image', tag.get('content')))
            except:
                pass
            
            # 4. JSON-LD structured data
            try:
                scripts = soup.find_all('script', {'type': 'application/ld+json'})
                for script in scripts:
                    if script.string:
                        try:
                            import json
                            data = json.loads(script.string)
                            if isinstance(data, dict) and 'image' in data:
                                img = data['image']
                                if isinstance(img, str):
                                    image_candidates.append(('json-ld', img))
                                elif isinstance(img, list) and img:
                                    image_candidates.append(('json-ld', img[0]))
                        except:
                            pass
            except:
                pass
            
            # 5. Sitio específico - CNN
            if 'cnn.com' in url:
                try:
                    # CNN usa clases específicas
                    cnn_imgs = soup.find_all('img')
                    for img in cnn_imgs:
                        src = img.get('src') or img.get('data-src')
                        if src and any(indicator in src for indicator in ['prod', 'stellar', 'dam']):
                            image_candidates.append(('cnn-specific', src))
                            break
                except:
                    pass
            
            # 6. Sitio específico - BBC
            elif 'bbc.com' in url:
                try:
                    # BBC usa ichef
                    bbc_imgs = soup.find_all('img')
                    for img in bbc_imgs:
                        src = img.get('src') or img.get('data-src')
                        if src and 'ichef.bbci.co.uk' in src:
                            image_candidates.append(('bbc-specific', src))
                            break
                except:
                    pass
            
            # 7. Sitio específico - AP News
            elif 'apnews.com' in url:
                try:
                    ap_imgs = soup.find_all('img')
                    for img in ap_imgs:
                        src = img.get('src') or img.get('data-src')
                        if src and 'apnews.com' in src and 'assets' in src:
                            image_candidates.append(('ap-specific', src))
                            break
                except:
                    pass
            
            # 8. Sitio específico - Al Jazeera
            elif 'aljazeera.com' in url:
                try:
                    aj_imgs = soup.find_all('img')
                    for img in aj_imgs:
                        src = img.get('src') or img.get('data-src')
                        if src and ('aljazeera' in src or 'aje.io' in src):
                            image_candidates.append(('aljazeera-specific', src))
                            break
                except:
                    pass
            
            # 9. Búsqueda genérica en figure/picture
            try:
                figures = soup.find_all(['figure', 'picture'])
                for fig in figures:
                    img = fig.find('img')
                    if img:
                        src = img.get('src') or img.get('data-src')
                        if src:
                            image_candidates.append(('figure', src))
            except:
                pass
            
            # 10. Imágenes con clases relevantes
            try:
                relevant_imgs = soup.find_all('img')
                for img in relevant_imgs:
                    img_class = ' '.join(img.get('class', [])).lower()
                    if any(keyword in img_class for keyword in ['hero', 'main', 'featured', 'lead', 'primary', 'article']):
                        src = img.get('src') or img.get('data-src')
                        if src:
                            image_candidates.append(('class-relevant', src))
            except:
                pass
            
            # Procesar candidatos
            print(f"   📸 Encontrados {len(image_candidates)} candidatos")
            
            for source, img_url in image_candidates:
                
                # Limpiar y normalizar URL
                if not img_url:
                    continue
                    
                # Convertir URLs relativas
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif img_url.startswith('/'):
                    img_url = urljoin(url, img_url)
                
                # Verificar formato
                if not img_url.startswith(('http://', 'https://')):
                    continue
                
                # Filtrar URLs obviamente malas
                if any(bad in img_url.lower() for bad in [
                    'logo', 'icon', 'avatar', 'placeholder', 'default', 
                    'loading', 'spinner', 'thumbnail-small', 'widget'
                ]):
                    continue
                
                # Verificar accesibilidad
                if self.verify_image_accessible(img_url):
                    print(f"   ✅ IMAGEN VÁLIDA ({source}): {img_url[:50]}...")
                    return img_url
                else:
                    print(f"   ❌ No accesible ({source}): {img_url[:50]}...")
            
            print(f"   ⚠️ No se encontró imagen válida de {len(image_candidates)} candidatos")
            return None
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}...")
            return None
    
    def verify_image_accessible(self, img_url):
        """Verifica que una imagen sea accesible"""
        try:
            # HEAD request primero
            response = self.session.head(img_url, timeout=8, allow_redirects=True)
            
            if response.status_code in [200, 301, 302]:
                content_type = response.headers.get('content-type', '').lower()
                if content_type.startswith('image/'):
                    return True
                    
            # Si HEAD falla, probar GET pequeño
            response = self.session.get(img_url, timeout=8, stream=True)
            if response.status_code == 200:
                # Leer primeros bytes para verificar
                chunk = next(iter(response.iter_content(1024)), b'')
                # Magic bytes de imagen
                if (chunk.startswith(b'\xff\xd8\xff') or  # JPEG
                    chunk.startswith(b'\x89PNG') or      # PNG  
                    chunk.startswith(b'GIF8') or         # GIF
                    chunk.startswith(b'RIFF')):          # WebP
                    return True
            
            return False
            
        except:
            return False

def extract_real_images():
    """Función principal para extraer imágenes reales"""
    
    print("🎯 EXTRACTOR DE IMÁGENES ORIGINALES - VERSIÓN ROBUSTA")
    print("=" * 70)
    print(f"🕒 {datetime.now().strftime('%H:%M:%S')}")
    
    extractor = RobustImageExtractor()
    
    try:
        db_path = "./data/geopolitical_intel.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Obtener artículos sin imagen válida
        cursor.execute("""
            SELECT id, title, url, source 
            FROM articles 
            WHERE image_url IS NULL OR image_url = '' 
               OR image_url LIKE 'http://localhost%'
               OR image_url LIKE '%placeholder%'
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        articles = cursor.fetchall()
        
        print(f"📰 Procesando {len(articles)} artículos...")
        
        success_count = 0
        
        for i, (id, title, url, source) in enumerate(articles, 1):
            print(f"\n[{i}/{len(articles)}] ID:{id}")
            print(f"📰 {title[:55]}...")
            print(f"🔗 {url[:70]}...")
            
            # Extraer imagen original
            original_image = extractor.extract_image_from_url(url, title)
            
            if original_image:
                # Actualizar base de datos
                cursor.execute("""
                    UPDATE articles 
                    SET image_url = ?, original_image_url = ?
                    WHERE id = ?
                """, (original_image, original_image, id))
                
                success_count += 1
                print(f"   ✅ ACTUALIZADO: {original_image[:50]}...")
                
            else:
                print(f"   ❌ SIN IMAGEN VÁLIDA")
            
            # Pausa entre requests
            time.sleep(2)
        
        conn.commit()
        
        print(f"\n📊 RESULTADOS:")
        print(f"   Artículos procesados: {len(articles)}")
        print(f"   Imágenes extraídas: {success_count}")
        print(f"   Tasa éxito: {(success_count/len(articles)*100):.1f}%" if articles else "N/A")
        
        # Verificar resultado final
        if success_count > 0:
            print(f"\n🔍 VERIFICACIÓN FINAL...")
            
            # Verificar vía API
            try:
                response = requests.get("http://localhost:5001/api/articles?limit=6", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    articles_api = data.get('articles', [])
                    
                    with_image = sum(1 for art in articles_api if art.get('image_url'))
                    total = len(articles_api)
                    
                    print(f"   📊 Mosaico actual: {with_image}/{total} con imagen ({(with_image/total*100):.1f}%)")
                    
                    if with_image == total:
                        print("   🎉 ¡PERFECTO! TODAS las noticias tienen imagen")
                    else:
                        print(f"   ⚠️ Faltan {total - with_image} imágenes")
            except Exception as e:
                print(f"   ❌ Error verificando API: {e}")
        
        conn.close()
        return success_count > 0
        
    except Exception as e:
        print(f"❌ ERROR CRÍTICO: {e}")
        return False

def main():
    """Ejecutar extractor"""
    
    success = extract_real_images()
    
    if success:
        print(f"\n✅ EXTRACCIÓN COMPLETADA CON ÉXITO")
        print(f"🚀 RECARGA LA PÁGINA PARA VER LAS IMÁGENES ORIGINALES")
    else:
        print(f"\n❌ EXTRACCIÓN FALLÓ - REVISAR CONEXIONES")

if __name__ == "__main__":
    main()