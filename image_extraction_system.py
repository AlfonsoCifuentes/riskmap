"""
Sistema completo de extracción de imágenes para artículos
Este script extrae imágenes de las URLs originales de los artículos
y las guarda en la base de datos.
"""

import sqlite3
import requests
import os
import time
import hashlib
from urllib.parse import urljoin, urlparse
from pathlib import Path
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import base64
from PIL import Image
import io

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImageExtractionSystem:
    def __init__(self, db_path="geopolitical_intel.db", images_dir="static/images/articles"):
        self.db_path = db_path
        self.images_dir = Path(images_dir)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar Selenium para capturas de pantalla
        self.setup_selenium()
        
        # Headers para requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def setup_selenium(self):
        """Configurar Selenium WebDriver para capturas de pantalla"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-software-rasterizer')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Selenium WebDriver configurado correctamente")
        except Exception as e:
            logger.error(f"Error configurando Selenium: {e}")
            self.driver = None
    
    def get_articles_without_images(self):
        """Obtener artículos que no tienen imagen"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, title, url, source
                    FROM articles 
                    WHERE (image_url IS NULL OR image_url = '' OR image_url LIKE '%placeholder%' OR image_url LIKE '%picsum%')
                    AND url IS NOT NULL 
                    AND url != ''
                    ORDER BY id DESC
                    LIMIT 100
                """)
                articles = cursor.fetchall()
                logger.info(f"Encontrados {len(articles)} artículos sin imagen")
                return articles
        except Exception as e:
            logger.error(f"Error obteniendo artículos sin imagen: {e}")
            return []
    
    def extract_image_from_url(self, url, article_id, title):
        """Extraer imagen de la URL del artículo"""
        try:
            logger.info(f"Procesando artículo {article_id}: {title[:50]}...")
            
            # Método 1: Buscar imagen usando BeautifulSoup
            image_url = self.scrape_article_image(url)
            
            if image_url:
                # Descargar y guardar imagen
                image_path = self.download_and_save_image(image_url, article_id, "scraped")
                if image_path:
                    return image_path
            
            # Método 2: Captura de pantalla si no se encuentra imagen
            if self.driver:
                image_path = self.take_screenshot(url, article_id)
                if image_path:
                    return image_path
            
            logger.warning(f"No se pudo extraer imagen para artículo {article_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error extrayendo imagen del artículo {article_id}: {e}")
            return None
    
    def scrape_article_image(self, url):
        """Buscar imagen principal del artículo usando web scraping"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Selectores comunes para imágenes de artículos
            image_selectors = [
                'meta[property="og:image"]',
                'meta[name="twitter:image"]',
                'article img',
                '.article-image img',
                '.post-thumbnail img',
                '.featured-image img',
                '.hero-image img',
                '.main-image img',
                'figure img',
                '.content img',
                'img[class*="article"]',
                'img[class*="featured"]',
                'img[class*="main"]'
            ]
            
            for selector in image_selectors:
                elements = soup.select(selector)
                for element in elements:
                    if selector.startswith('meta'):
                        image_url = element.get('content')
                    else:
                        image_url = element.get('src') or element.get('data-src')
                    
                    if image_url:
                        # Convertir URL relativa a absoluta
                        image_url = urljoin(url, image_url)
                        
                        # Verificar que la imagen sea válida
                        if self.is_valid_image_url(image_url):
                            logger.info(f"Imagen encontrada: {image_url}")
                            return image_url
            
            return None
            
        except Exception as e:
            logger.error(f"Error en scraping de imagen para {url}: {e}")
            return None
    
    def is_valid_image_url(self, url):
        """Verificar si la URL de imagen es válida"""
        try:
            # Verificar extensión
            parsed = urlparse(url)
            path = parsed.path.lower()
            valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
            
            if any(path.endswith(ext) for ext in valid_extensions):
                return True
            
            # Verificar content-type si no hay extensión clara
            try:
                response = requests.head(url, headers=self.headers, timeout=5)
                content_type = response.headers.get('Content-Type', '')
                if content_type.startswith('image/'):
                    return True
            except:
                pass
            
            return False
            
        except Exception as e:
            logger.error(f"Error verificando URL de imagen: {e}")
            return False
    
    def download_and_save_image(self, image_url, article_id, source_type):
        """Descargar y guardar imagen"""
        try:
            response = requests.get(image_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            # Verificar que es una imagen
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                logger.warning(f"URL no es una imagen: {content_type}")
                return None
            
            # Determinar extensión
            if 'jpeg' in content_type or 'jpg' in content_type:
                ext = '.jpg'
            elif 'png' in content_type:
                ext = '.png'
            elif 'webp' in content_type:
                ext = '.webp'
            elif 'gif' in content_type:
                ext = '.gif'
            else:
                ext = '.jpg'
            
            # Generar nombre de archivo único
            filename = f"article_{article_id}_{source_type}_{int(time.time())}{ext}"
            file_path = self.images_dir / filename
            
            # Guardar imagen
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            # Verificar que la imagen se guardó correctamente
            if file_path.exists() and file_path.stat().st_size > 1000:  # Al menos 1KB
                relative_path = f"static/images/articles/{filename}"
                logger.info(f"Imagen guardada: {relative_path}")
                return relative_path
            else:
                if file_path.exists():
                    file_path.unlink()
                return None
                
        except Exception as e:
            logger.error(f"Error descargando imagen {image_url}: {e}")
            return None
    
    def take_screenshot(self, url, article_id):
        """Tomar captura de pantalla de la página"""
        try:
            if not self.driver:
                return None
                
            self.driver.get(url)
            
            # Esperar a que la página cargue
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Scroll para cargar imágenes lazy-load
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
            time.sleep(2)
            
            # Tomar captura de pantalla
            screenshot = self.driver.get_screenshot_as_png()
            
            # Procesar imagen (recortar la parte superior)
            image = Image.open(io.BytesIO(screenshot))
            
            # Recortar para quedarse con la parte superior (donde suele estar el contenido principal)
            width, height = image.size
            cropped_image = image.crop((0, 0, width, min(height, 800)))
            
            # Guardar imagen
            filename = f"article_{article_id}_screenshot_{int(time.time())}.jpg"
            file_path = self.images_dir / filename
            
            cropped_image.save(file_path, 'JPEG', quality=85)
            
            if file_path.exists() and file_path.stat().st_size > 1000:
                relative_path = f"static/images/articles/{filename}"
                logger.info(f"Captura de pantalla guardada: {relative_path}")
                return relative_path
            
            return None
            
        except Exception as e:
            logger.error(f"Error tomando captura de pantalla para {url}: {e}")
            return None
    
    def update_article_image(self, article_id, image_path):
        """Actualizar la imagen del artículo en la base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE articles 
                    SET image_url = ? 
                    WHERE id = ?
                """, (image_path, article_id))
                
                conn.commit()
                logger.info(f"Imagen actualizada en BD para artículo {article_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error actualizando imagen en BD para artículo {article_id}: {e}")
            return False
    
    def process_all_articles(self):
        """Procesar todos los artículos sin imagen"""
        articles = self.get_articles_without_images()
        
        if not articles:
            logger.info("No hay artículos sin imagen para procesar")
            return
        
        processed = 0
        errors = 0
        
        for article_id, title, url, source in articles:
            try:
                logger.info(f"Procesando artículo {article_id}/{len(articles)}")
                
                image_path = self.extract_image_from_url(url, article_id, title)
                
                if image_path:
                    if self.update_article_image(article_id, image_path):
                        processed += 1
                        logger.info(f"✅ Procesado: {title[:50]}...")
                    else:
                        errors += 1
                else:
                    errors += 1
                    logger.warning(f"❌ No se pudo procesar: {title[:50]}...")
                
                # Pausa para no sobrecargar los servidores
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error procesando artículo {article_id}: {e}")
                errors += 1
        
        logger.info(f"Procesamiento completado: {processed} exitosos, {errors} errores")
        
        if self.driver:
            self.driver.quit()
    
    def __del__(self):
        """Cleanup"""
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
            except:
                pass

def main():
    """Función principal"""
    print("🖼️  SISTEMA DE EXTRACCIÓN DE IMÁGENES PARA ARTÍCULOS")
    print("=" * 60)
    
    extractor = ImageExtractionSystem()
    
    try:
        extractor.process_all_articles()
    except KeyboardInterrupt:
        print("\n⚠️  Proceso interrumpido por el usuario")
    except Exception as e:
        print(f"❌ Error en el proceso: {e}")
    finally:
        if hasattr(extractor, 'driver') and extractor.driver:
            extractor.driver.quit()

if __name__ == "__main__":
    main()
