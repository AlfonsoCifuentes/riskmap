#!/usr/bin/env python3
"""
Sistema de extracción de imágenes de artículos usando IA
Extrae imágenes de artículos de noticias usando técnicas de web scraping inteligente.
"""

import sqlite3
import requests
from bs4 import BeautifulSoup
import logging
from pathlib import Path
import time
import hashlib
import os
from urllib.parse import urljoin, urlparse
import json
from PIL import Image
import io

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constante para el parser HTML
HTML_PARSER = 'html.parser'

class ImageExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Directorio para guardar imágenes
        self.images_dir = Path('data/images')
        self.images_dir.mkdir(exist_ok=True)
        
    def extract_images_from_url(self, url, article_title=""):
        """
        Extrae imágenes de una URL usando múltiples métodos
        """
        try:
            logger.info(f"Extrayendo imágenes de: {url}")
            
            # Método 1: Buscar imágenes en HTML usando BeautifulSoup
            images = self._extract_from_html(url)
            
            if images:
                logger.info(f"Método HTML encontró {len(images)} imágenes")
                return self._select_best_image(images, article_title)
            
            # Método 2: Buscar meta tags Open Graph
            og_image = self._extract_og_image(url)
            if og_image:
                logger.info("Método OpenGraph encontró imagen")
                return og_image
            
            # Método 3: Usar análisis con IA del contenido
            ai_image = self._extract_with_ai_analysis(url, article_title)
            if ai_image:
                logger.info("Método IA encontró imagen")
                return ai_image
            
            logger.warning(f"No se pudo extraer imagen de: {url}")
            return None
            
        except Exception as e:
            logger.error(f"Error extrayendo imagen de {url}: {e}")
            return None
    
    def _extract_from_html(self, url):
        """Extrae imágenes del HTML de la página"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, HTML_PARSER)
            images = []
            
            # Buscar imágenes en diferentes selectores
            selectors = [
                'article img',
                '.article-content img',
                '.news-content img',
                '.story-content img',
                '.post-content img',
                'main img',
                '[class*="image"] img',
                '[class*="photo"] img',
                'img[class*="featured"]',
                'img[class*="hero"]',
                'img[class*="main"]'
            ]
            
            for selector in selectors:
                found_images = soup.select(selector)
                for img in found_images:
                    src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                    if src:
                        full_url = urljoin(url, src)
                        alt_text = img.get('alt', '')
                        
                        # Filtrar imágenes pequeñas o de navegación
                        if self._is_content_image(src, alt_text):
                            images.append({
                                'url': full_url,
                                'alt': alt_text,
                                'selector': selector
                            })
            
            return images
            
        except Exception as e:
            logger.error(f"Error en extracción HTML: {e}")
            return []
    
    def _extract_og_image(self, url):
        """Extrae imagen de meta tags Open Graph"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, HTML_PARSER)
            
            # Buscar meta tags de imagen
            og_image = soup.find('meta', property='og:image')
            if og_image:
                content = og_image.get('content')
                if content:
                    return urljoin(url, content)
            
            # Buscar Twitter card image
            twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
            if twitter_image:
                content = twitter_image.get('content')
                if content:
                    return urljoin(url, content)
            
            return None
            
        except Exception as e:
            logger.error(f"Error en extracción OG: {e}")
            return None
    
    def _extract_with_ai_analysis(self, url, article_title):
        """
        Usa IA para analizar el contenido y encontrar la imagen más relevante
        """
        try:
            # Obtener contenido de la página
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, HTML_PARSER)
            
            # Extraer texto del artículo
            article_text = ""
            for selector in ['article', '.article-content', '.news-content', '.story-content']:
                content = soup.select_one(selector)
                if content:
                    article_text = content.get_text()[:500]  # Primeros 500 caracteres
                    break
            
            # Buscar todas las imágenes
            images = soup.find_all('img')
            
            best_image = None
            best_score = 0
            
            for img in images:
                src = img.get('src') or img.get('data-src')
                if not src:
                    continue
                    
                full_url = urljoin(url, src)
                alt_text = img.get('alt', '')
                
                # Calcular puntuación basada en relevancia
                score = self._calculate_image_relevance(
                    full_url, alt_text, article_title
                )
                
                if score > best_score:
                    best_score = score
                    best_image = full_url
            
            return best_image if best_score > 0.3 else None
            
        except Exception as e:
            logger.error(f"Error en análisis IA: {e}")
            return None
    
    def _calculate_image_relevance(self, image_url, alt_text, title):
        """Calcula la relevancia de una imagen usando análisis de texto"""
        score = 0.0
        
        # Puntuación base por URL
        url_lower = image_url.lower()
        if any(keyword in url_lower for keyword in ['main', 'featured', 'hero', 'article', 'news']):
            score += 0.3
        
        # Puntuación por alt text
        if alt_text:
            alt_lower = alt_text.lower()
            title_words = set(title.lower().split())
            alt_words = set(alt_lower.split())
            
            # Palabras en común
            common_words = title_words.intersection(alt_words)
            if common_words:
                score += len(common_words) * 0.1
        
        # Penalizar imágenes pequeñas o de navegación
        if any(keyword in image_url.lower() for keyword in ['logo', 'icon', 'avatar', 'thumb']):
            score -= 0.2
        
        # Penalizar dimensiones en URL que indican imágenes pequeñas
        if any(size in image_url for size in ['150x', '100x', '50x', 'thumb']):
            score -= 0.1
        
        return max(0.0, score)
    
    def _is_content_image(self, src, alt_text):
        """Determina si una imagen es de contenido (no navegación)"""
        src_lower = src.lower()
        alt_lower = alt_text.lower()
        
        # Filtrar imágenes de navegación
        nav_keywords = ['logo', 'icon', 'avatar', 'menu', 'button', 'arrow', 'banner', 'ad']
        if any(keyword in src_lower or keyword in alt_lower for keyword in nav_keywords):
            return False
        
        # Filtrar imágenes muy pequeñas por URL
        if any(size in src_lower for size in ['1x1', '16x16', '32x32', '50x50']):
            return False
        
        return True
    
    def _select_best_image(self, images, article_title):
        """Selecciona la mejor imagen de una lista"""
        if not images:
            return None
        
        # Si solo hay una imagen, devolverla
        if len(images) == 1:
            return images[0]['url']
        
        # Calcular puntuaciones
        scored_images = []
        for img in images:
            score = self._calculate_image_relevance(
                img['url'], img['alt'], article_title
            )
            scored_images.append((img['url'], score))
        
        # Ordenar por puntuación
        scored_images.sort(key=lambda x: x[1], reverse=True)
        
        return scored_images[0][0] if scored_images else None
    
    def download_and_save_image(self, image_url, article_id):
        """Descarga y guarda una imagen localmente"""
        try:
            response = self.session.get(image_url, timeout=10)
            response.raise_for_status()
            
            # Verificar que es una imagen válida
            image = Image.open(io.BytesIO(response.content))
            
            # Crear nombre de archivo único
            file_extension = image_url.split('.')[-1].split('?')[0]
            if file_extension.lower() not in ['jpg', 'jpeg', 'png', 'webp']:
                file_extension = 'jpg'
            
            filename = f"article_{article_id}_{hashlib.md5(image_url.encode()).hexdigest()[:8]}.{file_extension}"
            file_path = self.images_dir / filename
            
            # Guardar imagen
            image.save(file_path)
            
            # Retornar URL local
            return f"/static/images/{filename}"
            
        except Exception as e:
            logger.error(f"Error descargando imagen {image_url}: {e}")
            return None

def update_article_images():
    """Actualiza las imágenes de artículos en la base de datos"""
    extractor = ImageExtractor()
    
    # Conectar a la base de datos
    conn = sqlite3.connect('data/geopolitical_intel.db')
    cursor = conn.cursor()
    
    # Obtener artículos sin imagen
    cursor.execute('''
        SELECT id, title, url FROM articles 
        WHERE (image_url IS NULL OR image_url = "") 
        AND url IS NOT NULL 
        LIMIT 10
    ''')
    
    articles_without_images = cursor.fetchall()
    
    logger.info(f"Procesando {len(articles_without_images)} artículos sin imagen")
    
    updated_count = 0
    for article_id, title, url in articles_without_images:
        try:
            logger.info(f"Procesando artículo {article_id}: {title[:50]}...")
            
            # Extraer imagen
            image_url = extractor.extract_images_from_url(url, title)
            
            if image_url:
                # Actualizar base de datos
                cursor.execute('''
                    UPDATE articles 
                    SET image_url = ? 
                    WHERE id = ?
                ''', (image_url, article_id))
                
                updated_count += 1
                logger.info(f"✅ Imagen actualizada para artículo {article_id}")
            else:
                logger.warning(f"❌ No se pudo extraer imagen para artículo {article_id}")
            
            # Pausa para evitar sobrecargar servidores
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Error procesando artículo {article_id}: {e}")
    
    # Guardar cambios
    conn.commit()
    conn.close()
    
    logger.info(f"Proceso completado: {updated_count} imágenes actualizadas")
    return updated_count

if __name__ == "__main__":
    # Ejecutar actualización de imágenes
    updated = update_article_images()
    print(f"Se actualizaron {updated} artículos con nuevas imágenes")
