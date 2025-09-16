#!/usr/bin/env python3
"""
Sistema mejorado de extracción de imágenes para artículos
Específicamente diseñado para resolver problemas de:
1. Imágenes faltantes en artículos como AP News, Financial Times, Axios
2. Texturas negras o imágenes de fallback de baja calidad
3. Mejor captura desde URLs originales
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
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import base64

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImprovedImageExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Configurar Selenium para casos difíciles
        self.setup_selenium()
        
        # Imágenes fallback específicas por fuente
        self.source_fallbacks = {
            'AP News': 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800&h=600&fit=crop',
            'Financial Times': 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&h=600&fit=crop',
            'Axios': 'https://images.unsplash.com/photo-1495020689067-958852a7e369?w=800&h=600&fit=crop',
            'Reuters': 'https://images.unsplash.com/photo-1557804506-669a67965ba0?w=800&h=600&fit=crop',
            'CNN': 'https://images.unsplash.com/photo-1586953208448-b95a79798f07?w=800&h=600&fit=crop',
            'BBC': 'https://images.unsplash.com/photo-1495020689067-958852a7e369?w=800&h=600&fit=crop',
            'default': 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800&h=600&fit=crop'
        }
        
        # Palabras clave para identificar imágenes de baja calidad que deben evitarse
        self.bad_image_keywords = [
            'texture', 'black', 'negro', 'fallback', 'placeholder', 
            'default', '1x1', 'pixel', 'transparent', 'blank', 'empty',
            'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP', # 1x1 transparent GIF
            'loading', 'spinner', 'icon', 'avatar', 'logo-small'
        ]

    def setup_selenium(self):
        """Configurar Selenium para casos difíciles"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Selenium WebDriver configurado correctamente")
        except Exception as e:
            logger.warning(f"No se pudo configurar Selenium: {e}")
            self.driver = None

    def is_bad_image(self, image_url, alt_text=""):
        """Verifica si una imagen debe evitarse por ser de baja calidad"""
        if not image_url:
            return True
        
        # Verificar palabras clave problemáticas
        combined_text = f"{image_url.lower()} {alt_text.lower()}"
        for keyword in self.bad_image_keywords:
            if keyword in combined_text:
                logger.debug(f"Imagen rechazada por palabra clave '{keyword}': {image_url}")
                return True
        
        # Verificar dimensiones sospechosas en la URL
        if re.search(r'[1-9]\d*x[1-9]\d*', image_url):
            match = re.search(r'(\d+)x(\d+)', image_url)
            if match:
                width, height = int(match.group(1)), int(match.group(2))
                if width < 200 or height < 150:
                    logger.debug(f"Imagen rechazada por dimensiones pequeñas {width}x{height}: {image_url}")
                    return True
        
        return False

    def extract_image_advanced(self, url, title=""):
        """Extractor avanzado de imágenes con múltiples métodos"""
        logger.info(f"🔍 Extrayendo imagen avanzada de: {url}")
        
        try:
            # Método 1: Extracción HTML mejorada
            image_url = self._extract_html_advanced(url, title)
            if image_url and not self.is_bad_image(image_url):
                return image_url
            
            # Método 2: Selenium para sitios con JavaScript
            if self.driver:
                image_url = self._extract_with_selenium(url, title)
                if image_url and not self.is_bad_image(image_url):
                    return image_url
            
            # Método 3: API específica por sitio
            image_url = self._extract_site_specific(url, title)
            if image_url and not self.is_bad_image(image_url):
                return image_url
            
            logger.warning(f"No se pudo extraer imagen válida de: {url}")
            return None
            
        except Exception as e:
            logger.error(f"Error en extracción avanzada: {e}")
            return None

    def _extract_html_advanced(self, url, title=""):
        """Extracción HTML mejorada con selectores específicos por sitio"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Selectores específicos por sitio
            domain = urlparse(url).netloc.lower()
            
            site_selectors = {
                'apnews.com': [
                    'figure.Image img',
                    '.CardHeadline img',
                    '.Component-featured-media img',
                    'img[data-key="image"]',
                    '.RichTextStoryBody img'
                ],
                'ft.com': [
                    '.article__content-image img',
                    '.n-content-image img',
                    '.article-hero__image img',
                    'figure img',
                    '.image-container img'
                ],
                'axios.com': [
                    '.ArticleHeaderHero img',
                    '.gtm-story-image img',
                    '.aspect-ratio-box img',
                    'figure img',
                    '.media-object img'
                ]
            }
            
            # Usar selectores específicos si están disponibles
            selectors = []
            for site_domain in site_selectors:
                if site_domain in domain:
                    selectors.extend(site_selectors[site_domain])
                    break
            
            # Selectores genéricos mejorados
            selectors.extend([
                'meta[property="og:image"]',
                'meta[name="twitter:image"]',
                'meta[property="twitter:image"]',
                'article img',
                '.article-content img',
                '.news-content img',
                '.story-content img',
                '.post-content img',
                'main img',
                '.hero-image img',
                '.featured-image img',
                '.primary-image img',
                '[class*="image"] img',
                '[class*="photo"] img',
                '[class*="media"] img',
                'img[class*="featured"]',
                'img[class*="hero"]',
                'img[class*="main"]',
                'img[class*="primary"]',
                'figure img',
                '.content img'
            ])
            
            for selector in selectors:
                try:
                    if selector.startswith('meta'):
                        elements = soup.select(selector)
                        for element in elements:
                            content = element.get('content')
                            if content:
                                full_url = urljoin(url, content)
                                if self._validate_image_quality(full_url):
                                    logger.info(f"✅ Imagen encontrada (meta): {full_url}")
                                    return full_url
                    else:
                        elements = soup.select(selector)
                        for element in elements:
                            src = element.get('src') or element.get('data-src') or element.get('data-lazy-src')
                            if src:
                                full_url = urljoin(url, src)
                                if self._validate_image_quality(full_url):
                                    logger.info(f"✅ Imagen encontrada (HTML): {full_url}")
                                    return full_url
                except Exception as e:
                    logger.debug(f"Error con selector {selector}: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error en extracción HTML: {e}")
            return None

    def _extract_with_selenium(self, url, title=""):
        """Extracción usando Selenium para sitios con JavaScript"""
        try:
            logger.info(f"🤖 Usando Selenium para: {url}")
            
            self.driver.get(url)
            
            # Esperar a que la página cargue
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Scroll para activar lazy loading
            self.driver.execute_script("window.scrollTo(0, 500);")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 1000);")
            time.sleep(2)
            
            # Buscar imágenes
            img_elements = self.driver.find_elements(By.TAG_NAME, "img")
            
            for img in img_elements:
                try:
                    src = img.get_attribute('src') or img.get_attribute('data-src')
                    if src and not self.is_bad_image(src):
                        full_url = urljoin(url, src)
                        if self._validate_image_quality(full_url):
                            logger.info(f"✅ Imagen encontrada (Selenium): {full_url}")
                            return full_url
                except Exception as e:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error con Selenium: {e}")
            return None

    def _extract_site_specific(self, url, title=""):
        """Métodos específicos para sitios problemáticos"""
        domain = urlparse(url).netloc.lower()
        
        # AP News específico
        if 'apnews.com' in domain:
            return self._extract_ap_news(url)
        
        # Financial Times específico
        if 'ft.com' in domain:
            return self._extract_financial_times(url)
        
        # Axios específico
        if 'axios.com' in domain:
            return self._extract_axios(url)
        
        return None

    def _extract_ap_news(self, url):
        """Extractor específico para AP News"""
        try:
            # AP News a menudo usa un patrón específico en sus URLs de imagen
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar en JSON-LD data
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'image' in data:
                        image_data = data['image']
                        if isinstance(image_data, dict) and 'url' in image_data:
                            return image_data['url']
                        elif isinstance(image_data, list) and len(image_data) > 0:
                            return image_data[0].get('url') if isinstance(image_data[0], dict) else image_data[0]
                        elif isinstance(image_data, str):
                            return image_data
                except:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error en AP News: {e}")
            return None

    def _extract_financial_times(self, url):
        """Extractor específico para Financial Times"""
        try:
            # FT usa patrones específicos
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar imágenes en data attributes específicos
            for img in soup.find_all('img'):
                data_src = img.get('data-src') or img.get('data-original-src')
                if data_src and 'ft.com' in data_src:
                    return data_src
            
            return None
            
        except Exception as e:
            logger.error(f"Error en Financial Times: {e}")
            return None

    def _extract_axios(self, url):
        """Extractor específico para Axios"""
        try:
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Axios usa clases específicas
            for selector in ['.aspect-ratio-box img', '.media-object img', '.gtm-story-image']:
                element = soup.select_one(selector)
                if element:
                    src = element.get('src') or element.get('data-src')
                    if src:
                        return urljoin(url, src)
            
            return None
            
        except Exception as e:
            logger.error(f"Error en Axios: {e}")
            return None

    def _validate_image_quality(self, image_url):
        """Valida que la imagen sea de calidad suficiente"""
        try:
            if self.is_bad_image(image_url):
                return False
            
            # Verificar que la imagen existe y es accesible
            head_response = self.session.head(image_url, timeout=5)
            if head_response.status_code != 200:
                return False
            
            # Verificar content-type
            content_type = head_response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                return False
            
            # Verificar tamaño del archivo (no muy pequeño)
            content_length = head_response.headers.get('Content-Length')
            if content_length and int(content_length) < 1000:  # Menos de 1KB es sospechoso
                return False
            
            return True
            
        except Exception as e:
            logger.debug(f"Error validando imagen {image_url}: {e}")
            return False

    def get_smart_fallback(self, source, title=""):
        """Obtiene una imagen de fallback inteligente basada en el contenido"""
        # Detectar fuente del URL o contenido
        for source_key in self.source_fallbacks:
            if source_key.lower() in source.lower():
                return self.source_fallbacks[source_key]
        
        # Fallback basado en palabras clave del título
        if title:
            title_lower = title.lower()
            if any(word in title_lower for word in ['guerra', 'war', 'conflict', 'fighting']):
                return 'https://images.unsplash.com/photo-1582213782179-e0d53f98f2ca?w=800&h=600&fit=crop'
            elif any(word in title_lower for word in ['economia', 'economy', 'market', 'financial']):
                return 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&h=600&fit=crop'
            elif any(word in title_lower for word in ['politics', 'political', 'gobierno', 'government']):
                return 'https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=800&h=600&fit=crop'
            elif any(word in title_lower for word in ['tech', 'technology', 'digital', 'cyber']):
                return 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=800&h=600&fit=crop'
        
        return self.source_fallbacks['default']

    def clean_bad_images_from_db(self):
        """Limpia imágenes de baja calidad de la base de datos"""
        try:
            conn = sqlite3.connect('data/geopolitical_intel.db')
            cursor = conn.cursor()
            
            # Buscar artículos con imágenes problemáticas
            cursor.execute('''
                SELECT id, title, image_url, source
                FROM articles 
                WHERE image_url IS NOT NULL 
                AND image_url != ''
                ORDER BY created_at DESC
                LIMIT 100
            ''')
            
            articles = cursor.fetchall()
            logger.info(f"Revisando {len(articles)} artículos para limpiar imágenes de baja calidad")
            
            cleaned_count = 0
            for article_id, title, image_url, source in articles:
                if self.is_bad_image(image_url):
                    # Obtener fallback inteligente
                    new_image = self.get_smart_fallback(source or '', title or '')
                    
                    cursor.execute('''
                        UPDATE articles 
                        SET image_url = ? 
                        WHERE id = ?
                    ''', (new_image, article_id))
                    
                    cleaned_count += 1
                    logger.info(f"🧹 Limpiada imagen de baja calidad para artículo {article_id}: {title[:50]}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Limpieza completada: {cleaned_count} imágenes mejoradas")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error en limpieza de base de datos: {e}")
            return 0

    def update_missing_images(self, limit=20):
        """Actualiza imágenes faltantes con el extractor mejorado"""
        try:
            conn = sqlite3.connect('data/geopolitical_intel.db')
            cursor = conn.cursor()
            
            # Buscar artículos sin imagen o con imágenes problemáticas
            cursor.execute('''
                SELECT id, title, url, source
                FROM articles 
                WHERE (
                    image_url IS NULL 
                    OR image_url = '' 
                    OR image_url LIKE '%placeholder%' 
                    OR image_url LIKE '%picsum%'
                    OR image_url LIKE '%fallback%'
                ) 
                AND url IS NOT NULL 
                AND url != ''
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            articles = cursor.fetchall()
            logger.info(f"Procesando {len(articles)} artículos para actualizar imágenes")
            
            updated_count = 0
            for article_id, title, url, source in articles:
                try:
                    logger.info(f"📰 Procesando artículo {article_id}: {title[:50]}...")
                    
                    # Extraer imagen con método avanzado
                    image_url = self.extract_image_advanced(url, title)
                    
                    if not image_url:
                        # Usar fallback inteligente
                        image_url = self.get_smart_fallback(source or '', title or '')
                    
                    # Actualizar base de datos
                    cursor.execute('''
                        UPDATE articles 
                        SET image_url = ? 
                        WHERE id = ?
                    ''', (image_url, article_id))
                    
                    updated_count += 1
                    logger.info(f"✅ Imagen actualizada para artículo {article_id}: {image_url}")
                    
                    # Pausa para evitar sobrecargar servidores
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error procesando artículo {article_id}: {e}")
                    continue
            
            conn.commit()
            conn.close()
            
            logger.info(f"🎉 Actualización completada: {updated_count} imágenes actualizadas")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error en actualización de imágenes: {e}")
            return 0

    def __del__(self):
        """Cleanup del driver de Selenium"""
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
            except:
                pass

def main():
    """Función principal para ejecutar el extractor mejorado"""
    logger.info("🚀 Iniciando extractor mejorado de imágenes...")
    
    extractor = ImprovedImageExtractor()
    
    # Paso 1: Limpiar imágenes de baja calidad existentes
    logger.info("🧹 Limpiando imágenes de baja calidad...")
    cleaned = extractor.clean_bad_images_from_db()
    
    # Paso 2: Actualizar artículos sin imágenes
    logger.info("📸 Actualizando artículos sin imágenes...")
    updated = extractor.update_missing_images(30)  # Procesar 30 artículos
    
    logger.info(f"🎉 Proceso completado: {cleaned} imágenes limpiadas, {updated} imágenes actualizadas")

if __name__ == "__main__":
    main()
