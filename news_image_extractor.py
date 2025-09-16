#!/usr/bin/env python3
"""
Sistema completo de extracción, descarga y almacenamiento de imágenes para noticias
"""
import os
import requests
import sqlite3
import hashlib
import mimetypes
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsImageExtractor:
    def __init__(self, images_dir="./static/images/news"):
        """
        Inicializar el extractor de imágenes
        
        Args:
            images_dir (str): Directorio donde guardar las imágenes
        """
        self.images_dir = Path(images_dir)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        # Headers para simular un navegador real
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }
        
        # Selectores CSS para encontrar imágenes principales
        self.image_selectors = [
            # Meta tags de redes sociales (más confiables)
            ('meta[property="og:image"]', 'content'),
            ('meta[name="twitter:image"]', 'content'),
            ('meta[name="twitter:image:src"]', 'content'),
            
            # Imágenes destacadas en artículos
            ('img[class*="featured"]', 'src'),
            ('img[class*="hero"]', 'src'),
            ('img[class*="main"]', 'src'),
            ('img[class*="lead"]', 'src'),
            ('.featured-image img', 'src'),
            ('.hero-image img', 'src'),
            
            # Imágenes dentro de artículos
            ('article img', 'src'),
            ('.article img', 'src'),
            ('.content img', 'src'),
            ('.story-body img', 'src'),
            
            # Data attributes (lazy loading)
            ('img[data-src]', 'data-src'),
            ('img[data-lazy]', 'data-lazy'),
        ]
    
    def extract_image_from_url(self, url, max_retries=2):
        """
        Extraer la imagen principal de una URL de noticia
        
        Args:
            url (str): URL del artículo
            max_retries (int): Número máximo de reintentos
            
        Returns:
            str: URL de la imagen extraída o None
        """
        if not url or not url.startswith('http'):
            return None
            
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"Extrayendo imagen de: {url} (intento {attempt + 1})")
                
                response = requests.get(url, headers=self.headers, timeout=15)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Intentar con cada selector
                for selector, attr in self.image_selectors:
                    elements = soup.select(selector)
                    for element in elements:
                        img_url = element.get(attr)
                        if img_url:
                            # Normalizar URL
                            img_url = self._normalize_image_url(img_url, url)
                            
                            # Validar que es una imagen
                            if self._is_valid_image_url(img_url):
                                logger.info(f"✅ Imagen encontrada: {img_url}")
                                return img_url
                
                logger.warning(f"No se encontraron imágenes válidas en {url}")
                return None
                
            except requests.RequestException as e:
                logger.warning(f"Error al acceder {url} (intento {attempt + 1}): {e}")
                if attempt < max_retries:
                    time.sleep(2 ** attempt)  # Backoff exponencial
                continue
            except Exception as e:
                logger.error(f"Error inesperado extrayendo imagen de {url}: {e}")
                return None
        
        return None
    
    def _normalize_image_url(self, img_url, base_url):
        """Normalizar y completar URLs de imagen"""
        if not img_url:
            return None
            
        # URLs que empiezan con //
        if img_url.startswith('//'):
            return 'https:' + img_url
        
        # URLs relativas
        elif img_url.startswith('/'):
            return urljoin(base_url, img_url)
        
        # URLs ya completas
        elif img_url.startswith('http'):
            return img_url
        
        # URLs relativas sin /
        else:
            return urljoin(base_url, img_url)
    
    def _is_valid_image_url(self, img_url, min_size=1000):
        """
        Verificar si una URL es una imagen válida
        
        Args:
            img_url (str): URL de la imagen
            min_size (int): Tamaño mínimo en bytes
            
        Returns:
            bool: True si es válida
        """
        try:
            # Hacer HEAD request para verificar
            response = requests.head(img_url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                return False
                
            content_type = response.headers.get('content-type', '').lower()
            if not content_type.startswith('image/'):
                return False
            
            # Verificar tamaño mínimo
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) < min_size:
                return False
                
            return True
            
        except:
            return False
    
    def download_image(self, img_url, filename=None):
        """
        Descargar imagen y guardarla localmente
        
        Args:
            img_url (str): URL de la imagen
            filename (str): Nombre del archivo (opcional)
            
        Returns:
            str: Ruta relativa del archivo guardado o None
        """
        try:
            logger.info(f"Descargando imagen: {img_url}")
            
            response = requests.get(img_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            # Generar nombre de archivo si no se proporciona
            if not filename:
                # Usar hash del URL + extensión
                url_hash = hashlib.md5(img_url.encode()).hexdigest()[:12]
                
                # Detectar extensión
                content_type = response.headers.get('content-type', '')
                extension = mimetypes.guess_extension(content_type) or '.jpg'
                
                filename = f"news_{url_hash}{extension}"
            
            # Ruta completa
            file_path = self.images_dir / filename
            
            # Guardar imagen
            with open(file_path, 'wb') as f:
                f.write(response.content)
                
            # Retornar ruta relativa para la base de datos
            relative_path = f"/static/images/news/{filename}"
            logger.info(f"✅ Imagen guardada: {relative_path}")
            return relative_path
            
        except Exception as e:
            logger.error(f"Error descargando imagen {img_url}: {e}")
            return None
    
    def process_article(self, article_id, article_url):
        """
        Procesar un artículo: extraer imagen, descargarla y actualizar BD
        
        Args:
            article_id (int): ID del artículo
            article_url (str): URL del artículo
            
        Returns:
            str: Ruta de la imagen guardada o None
        """
        try:
            # Extraer URL de imagen
            img_url = self.extract_image_from_url(article_url)
            if not img_url:
                return None
            
            # Descargar imagen
            local_path = self.download_image(img_url)
            if not local_path:
                return None
            
            # Actualizar base de datos
            self._update_article_image(article_id, local_path, img_url)
            
            return local_path
            
        except Exception as e:
            logger.error(f"Error procesando artículo {article_id}: {e}")
            return None
    
    def _update_article_image(self, article_id, local_path, original_url):
        """Actualizar la imagen del artículo en la base de datos"""
        try:
            db_path = "./data/geopolitical_intel.db"
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE articles 
                    SET image_url = ?, original_image_url = ?
                    WHERE id = ?
                """, (local_path, original_url, article_id))
                conn.commit()
                
            logger.info(f"✅ BD actualizada para artículo {article_id}")
            
        except Exception as e:
            logger.error(f"Error actualizando BD para artículo {article_id}: {e}")
    
    def process_all_articles(self, limit=None, skip_existing=True):
        """
        Procesar todos los artículos de la base de datos
        
        Args:
            limit (int): Límite de artículos a procesar
            skip_existing (bool): Saltar artículos que ya tienen imagen local
        """
        try:
            db_path = "./data/geopolitical_intel.db"
            
            # Agregar columna para URL original si no existe
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("ALTER TABLE articles ADD COLUMN original_image_url TEXT")
                except sqlite3.OperationalError:
                    pass  # Columna ya existe
            
            # Obtener artículos a procesar
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                where_clause = "WHERE url IS NOT NULL AND url != ''"
                if skip_existing:
                    where_clause += " AND (image_url IS NULL OR image_url = '' OR image_url LIKE '%placeholder%')"
                
                query = f"""
                    SELECT id, title, url 
                    FROM articles 
                    {where_clause}
                    ORDER BY id DESC
                """
                
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor.execute(query)
                articles = cursor.fetchall()
            
            logger.info(f"🔄 Procesando {len(articles)} artículos...")
            
            success_count = 0
            error_count = 0
            
            for i, article in enumerate(articles):
                print(f"\n📰 [{i+1}/{len(articles)}] ID {article['id']}: {article['title'][:60]}...")
                
                result = self.process_article(article['id'], article['url'])
                
                if result:
                    success_count += 1
                    print(f"   ✅ Imagen guardada: {result}")
                else:
                    error_count += 1
                    print(f"   ❌ No se pudo extraer imagen")
                
                # Pausa para no sobrecargar los servidores
                time.sleep(1)
            
            print(f"\n📊 RESUMEN:")
            print(f"- Procesados: {len(articles)}")
            print(f"- Exitosos: {success_count}")
            print(f"- Errores: {error_count}")
            print(f"- Tasa de éxito: {(success_count/len(articles)*100):.1f}%")
            
        except Exception as e:
            logger.error(f"Error procesando artículos: {e}")

def main():
    """Función principal para usar como script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extraer imágenes de noticias')
    parser.add_argument('--limit', type=int, help='Límite de artículos a procesar')
    parser.add_argument('--force', action='store_true', help='Procesar todos, incluso los que ya tienen imagen')
    
    args = parser.parse_args()
    
    extractor = NewsImageExtractor()
    extractor.process_all_articles(
        limit=args.limit, 
        skip_existing=not args.force
    )

if __name__ == "__main__":
    main()