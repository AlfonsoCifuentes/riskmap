#!/usr/bin/env python3
"""
Script de extracción masiva de imágenes para artículos
Procesa todos los artículos que no tienen imagen real
"""
import sqlite3
import os
import requests
import re
from urllib.parse import urljoin, urlparse
import time
import hashlib
from PIL import Image
from io import BytesIO
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MassImageExtractor:
    def __init__(self):
        self.db_path = "./data/geopolitical_intel.db"
        self.static_dir = "src/web/static/images/news/"
        os.makedirs(self.static_dir, exist_ok=True)
        
    def extract_images_from_url(self, url):
        """Extrae imágenes de una URL de artículo"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            content = response.text
            
            # Buscar imágenes en el HTML
            img_patterns = [
                r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>',
                r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\'][^>]*>',
                r'"image":\s*"([^"]+)"',
                r'"thumbnail":\s*"([^"]+)"'
            ]
            
            image_urls = []
            for pattern in img_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    img_url = urljoin(url, match)
                    if self.is_valid_image_url(img_url):
                        image_urls.append(img_url)
            
            return list(set(image_urls))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error extrayendo imágenes de {url}: {e}")
            return []
    
    def is_valid_image_url(self, url):
        """Verifica si una URL parece ser una imagen válida"""
        if not url or len(url) < 10:
            return False
            
        # Filtrar URLs no deseadas
        bad_patterns = [
            'placeholder', 'default', 'avatar', 'logo', 'icon',
            'data:', 'blob:', 'advertisement', 'ads', 'tracking'
        ]
        
        url_lower = url.lower()
        if any(pattern in url_lower for pattern in bad_patterns):
            return False
        
        # Verificar extensiones de imagen
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        if any(ext in url_lower for ext in image_extensions):
            return True
        
        # Verificar dominios de imágenes conocidos
        image_domains = ['images.', 'img.', 'media.', 'photo.', 'pic.', 'cdn.']
        if any(domain in url_lower for domain in image_domains):
            return True
        
        return False
    
    def download_and_save_image(self, image_url, article_id):
        """Descarga y guarda una imagen"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(image_url, headers=headers, timeout=15, stream=True)
            response.raise_for_status()
            
            # Verificar que es realmente una imagen
            if not response.headers.get('content-type', '').startswith('image/'):
                return None
            
            # Generar nombre único
            url_hash = hashlib.md5(image_url.encode()).hexdigest()[:8]
            extension = '.jpg'  # Usar JPG por defecto
            filename = f"news_{article_id}_{url_hash}{extension}"
            filepath = os.path.join(self.static_dir, filename)
            
            # Descargar imagen
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Verificar que se guardó correctamente
            if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:  # Min 1KB
                # Intentar optimizar imagen
                try:
                    with Image.open(filepath) as img:
                        # Redimensionar si es muy grande
                        if img.width > 800 or img.height > 600:
                            img.thumbnail((800, 600), Image.Resampling.LANCZOS)
                            img.save(filepath, 'JPEG', quality=85, optimize=True)
                    
                    return filename
                except Exception as e:
                    logger.warning(f"Error optimizando imagen {filename}: {e}")
                    return filename  # Devolver sin optimizar
            else:
                # Eliminar archivo inválido
                if os.path.exists(filepath):
                    os.remove(filepath)
                return None
                
        except Exception as e:
            logger.error(f"Error descargando imagen {image_url}: {e}")
            return None
    
    def update_article_image(self, article_id, image_filename):
        """Actualiza la imagen de un artículo en la BD"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE articles 
                SET original_image_url = ?, 
                    image_source = ?,
                    has_image = 1
                WHERE id = ?
            """, (image_filename, 'extracted', article_id))
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Artículo {article_id} actualizado con imagen {image_filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando artículo {article_id}: {e}")
            return False
    
    def process_articles_without_images(self, max_articles=50):
        """Procesa artículos sin imágenes"""
        logger.info("🚀 Iniciando extracción masiva de imágenes")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Obtener artículos sin imagen
            cursor.execute("""
                SELECT id, title, url 
                FROM articles 
                WHERE (original_image_url IS NULL OR original_image_url = '') 
                AND (image_url IS NULL OR image_url = '' OR image_url LIKE '%placeholder%')
                AND url IS NOT NULL AND url != ''
                AND created_at >= datetime('now', '-7 days')
                ORDER BY created_at DESC
                LIMIT ?
            """, (max_articles,))
            
            articles = cursor.fetchall()
            conn.close()
            
            logger.info(f"📊 Encontrados {len(articles)} artículos para procesar")
            
            processed = 0
            success_count = 0
            
            for article_id, title, url in articles:
                try:
                    logger.info(f"🔍 Procesando: {title[:60]}...")
                    
                    # Extraer imágenes de la URL
                    image_urls = self.extract_images_from_url(url)
                    
                    if not image_urls:
                        logger.warning(f"❌ No se encontraron imágenes para artículo {article_id}")
                        processed += 1
                        continue
                    
                    # Intentar descargar la primera imagen válida
                    image_saved = False
                    for img_url in image_urls[:3]:  # Intentar hasta 3 imágenes
                        filename = self.download_and_save_image(img_url, article_id)
                        if filename:
                            if self.update_article_image(article_id, filename):
                                success_count += 1
                                image_saved = True
                                logger.info(f"✅ Imagen guardada para artículo {article_id}: {filename}")
                                break
                        
                        # Pausa entre descargas
                        time.sleep(0.5)
                    
                    if not image_saved:
                        logger.warning(f"❌ No se pudo guardar imagen para artículo {article_id}")
                    
                    processed += 1
                    
                    # Pausa entre artículos
                    if processed % 5 == 0:
                        logger.info(f"📈 Progreso: {processed}/{len(articles)} ({success_count} exitosos)")
                        time.sleep(2)  # Pausa más larga cada 5 artículos
                    else:
                        time.sleep(1)
                
                except Exception as e:
                    logger.error(f"Error procesando artículo {article_id}: {e}")
                    processed += 1
                    continue
            
            logger.info(f"🏁 COMPLETADO: {processed} procesados, {success_count} exitosos")
            return success_count
            
        except Exception as e:
            logger.error(f"Error en proceso masivo: {e}")
            return 0

def main():
    extractor = MassImageExtractor()
    
    # Procesar hasta 50 artículos sin imagen
    success_count = extractor.process_articles_without_images(50)
    
    print(f"\n🎯 RESUMEN FINAL:")
    print(f"   ✅ Imágenes extraídas exitosamente: {success_count}")
    print(f"   📁 Directorio de imágenes: {extractor.static_dir}")
    print(f"   🔄 Reinicia la aplicación para ver los cambios")

if __name__ == "__main__":
    main()