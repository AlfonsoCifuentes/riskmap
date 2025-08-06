#!/usr/bin/env python3
"""
Sistema Avanzado de Adquisición de Imágenes

Este módulo implementa un sistema robusto para obtener imágenes originales
de artículos de noticias, con múltiples estrategias y fallbacks inteligentes.

Características:
- Extracción de imágenes originales de URLs de artículos
- Análisis de HTML para encontrar mejores imágenes
- Búsqueda de imágenes relacionadas usando AI
- Sistema de fallback inteligente
- Verificación de calidad y relevancia
- Prevención de duplicados con hashing
- Cache de imágenes procesadas
"""

import os
import sys
import logging
import requests
import hashlib
import re
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime
from urllib.parse import urljoin, urlparse
from io import BytesIO
import base64
import json

# Web scraping
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

# Procesamiento de imágenes
try:
    from PIL import Image, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# AI para análisis de imágenes y relevancia
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageExtractor:
    """Extractor avanzado de imágenes originales."""
    
    def __init__(self):
        """Inicializa el extractor de imágenes."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RiskMap-ImageBot/1.0 (News Aggregator)'
        })
        
        # Cache de imágenes procesadas (hash -> metadata)
        self.processed_images = {}
        
        # Conjunto de hashes de imágenes ya utilizadas
        self.used_image_hashes: Set[str] = set()
        
        # Patrones para encontrar imágenes de alta calidad
        self.quality_patterns = [
            r'og:image',
            r'twitter:image',
            r'article:image',
            r'hero.*image',
            r'featured.*image',
            r'main.*image',
            r'content.*image'
        ]
        
        # Extensiones de imagen válidas
        self.valid_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
        
        # Tamaños mínimos para considerar una imagen de calidad
        self.min_width = 300
        self.min_height = 200
    
    def get_image_hash(self, image_data: bytes) -> str:
        """
        Genera un hash único para los datos de imagen.
        
        Args:
            image_data: Datos binarios de la imagen
            
        Returns:
            Hash MD5 de la imagen
        """
        return hashlib.md5(image_data).hexdigest()
    
    def is_duplicate_image(self, image_data: bytes) -> bool:
        """
        Verifica si una imagen es duplicada.
        
        Args:
            image_data: Datos binarios de la imagen
            
        Returns:
            True si la imagen ya fue utilizada
        """
        image_hash = self.get_image_hash(image_data)
        return image_hash in self.used_image_hashes
    
    def mark_image_as_used(self, image_data: bytes) -> str:
        """
        Marca una imagen como utilizada.
        
        Args:
            image_data: Datos binarios de la imagen
            
        Returns:
            Hash de la imagen
        """
        image_hash = self.get_image_hash(image_data)
        self.used_image_hashes.add(image_hash)
        return image_hash
    
    def validate_image_quality(self, image_data: bytes) -> Tuple[bool, Dict]:
        """
        Valida la calidad de una imagen.
        
        Args:
            image_data: Datos binarios de la imagen
            
        Returns:
            Tupla (es_válida, metadata)
        """
        if not PIL_AVAILABLE:
            return True, {}
        
        try:
            with Image.open(BytesIO(image_data)) as img:
                width, height = img.size
                file_size = len(image_data)
                
                metadata = {
                    'width': width,
                    'height': height,
                    'size_bytes': file_size,
                    'format': img.format,
                    'mode': img.mode
                }
                
                # Criterios de calidad
                size_ok = width >= self.min_width and height >= self.min_height
                aspect_ratio = width / height if height > 0 else 0
                ratio_ok = 0.5 <= aspect_ratio <= 3.0  # Aspecto razonable
                file_size_ok = file_size >= 10000  # Al menos 10KB
                
                is_valid = size_ok and ratio_ok and file_size_ok
                
                metadata['quality_score'] = sum([
                    size_ok * 30,
                    ratio_ok * 20,
                    file_size_ok * 10,
                    min(width / 100, 20),  # Bonus por resolución
                    min(file_size / 10000, 20)  # Bonus por tamaño
                ])
                
                return is_valid, metadata
                
        except Exception as e:
            logger.warning(f"Error validando imagen: {e}")
            return False, {}
    
    def extract_images_from_html(self, html_content: str, base_url: str) -> List[Dict]:
        """
        Extrae imágenes de contenido HTML.
        
        Args:
            html_content: Contenido HTML
            base_url: URL base para resolver URLs relativas
            
        Returns:
            Lista de diccionarios con información de imágenes
        """
        if not BS4_AVAILABLE:
            return []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            images = []
            
            # 1. Buscar meta tags Open Graph y Twitter
            meta_images = []
            for pattern in self.quality_patterns:
                meta_tags = soup.find_all('meta', {'property': re.compile(pattern, re.I)})
                meta_tags.extend(soup.find_all('meta', {'name': re.compile(pattern, re.I)}))
                
                for tag in meta_tags:
                    content = tag.get('content', '')
                    if content:
                        meta_images.append({
                            'url': urljoin(base_url, content),
                            'source': 'meta_tag',
                            'priority': 90,
                            'tag_name': tag.get('property') or tag.get('name')
                        })
            
            # 2. Buscar imágenes en el contenido del artículo
            article_sections = soup.find_all(['article', 'main', 'div'], 
                                           class_=re.compile(r'(article|content|story|post)', re.I))
            
            content_images = []
            for section in article_sections:
                img_tags = section.find_all('img')
                for img in img_tags:
                    src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                    if src:
                        content_images.append({
                            'url': urljoin(base_url, src),
                            'source': 'content',
                            'priority': 70,
                            'alt_text': img.get('alt', ''),
                            'class': img.get('class', [])
                        })
            
            # 3. Buscar imágenes destacadas o hero
            hero_images = []
            hero_selectors = [
                'img[class*="hero"]',
                'img[class*="featured"]',
                'img[class*="main"]',
                '.hero img',
                '.featured img',
                '.header img'
            ]
            
            for selector in hero_selectors:
                hero_imgs = soup.select(selector)
                for img in hero_imgs:
                    src = img.get('src') or img.get('data-src')
                    if src:
                        hero_images.append({
                            'url': urljoin(base_url, src),
                            'source': 'hero',
                            'priority': 95,
                            'alt_text': img.get('alt', ''),
                            'selector': selector
                        })
            
            # Combinar todas las imágenes encontradas
            all_images = meta_images + hero_images + content_images
            
            # Filtrar URLs válidas y eliminar duplicados
            seen_urls = set()
            filtered_images = []
            
            for img in all_images:
                url = img['url']
                if url not in seen_urls and self._is_valid_image_url(url):
                    seen_urls.add(url)
                    filtered_images.append(img)
            
            # Ordenar por prioridad
            filtered_images.sort(key=lambda x: x['priority'], reverse=True)
            
            logger.info(f"Extraídas {len(filtered_images)} imágenes candidatas del HTML")
            return filtered_images
            
        except Exception as e:
            logger.error(f"Error extrayendo imágenes del HTML: {e}")
            return []
    
    def _is_valid_image_url(self, url: str) -> bool:
        """
        Verifica si una URL es una imagen válida.
        
        Args:
            url: URL a verificar
            
        Returns:
            True si parece ser una imagen válida
        """
        try:
            parsed = urlparse(url)
            path_lower = parsed.path.lower()
            
            # Verificar extensión
            has_valid_ext = any(path_lower.endswith(ext) for ext in self.valid_extensions)
            
            # Verificar que no sea un placeholder o icono pequeño
            is_not_placeholder = not any(keyword in path_lower for keyword in [
                'placeholder', 'loading', 'spinner', 'icon', 'logo', 'avatar',
                '1x1', 'pixel', 'spacer', 'blank'
            ])
            
            # Verificar tamaño en URL (algunos sitios incluyen dimensiones)
            size_indicators = re.findall(r'(\d+)x(\d+)', url)
            if size_indicators:
                width, height = map(int, size_indicators[0])
                size_ok = width >= self.min_width and height >= self.min_height
            else:
                size_ok = True  # No hay información de tamaño en URL
            
            return has_valid_ext and is_not_placeholder and size_ok
            
        except Exception:
            return False
    
    def download_and_validate_image(self, image_info: Dict) -> Optional[Dict]:
        """
        Descarga y valida una imagen.
        
        Args:
            image_info: Información de la imagen a descargar
            
        Returns:
            Diccionario con imagen validada o None
        """
        url = image_info['url']
        
        try:
            logger.info(f"Descargando imagen: {url}")
            
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Verificar content-type
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                logger.warning(f"Content-type no es imagen: {content_type}")
                return None
            
            # Descargar datos
            image_data = response.content
            
            # Verificar duplicados
            if self.is_duplicate_image(image_data):
                logger.info(f"Imagen duplicada detectada: {url}")
                return None
            
            # Validar calidad
            is_valid, metadata = self.validate_image_quality(image_data)
            if not is_valid:
                logger.info(f"Imagen no cumple criterios de calidad: {url}")
                return None
            
            # Marcar como utilizada
            image_hash = self.mark_image_as_used(image_data)
            
            result = {
                'url': url,
                'data': image_data,
                'hash': image_hash,
                'metadata': metadata,
                'source_info': image_info,
                'content_type': content_type,
                'download_timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Imagen válida obtenida: {metadata.get('width')}x{metadata.get('height')}, {len(image_data)} bytes")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error descargando imagen {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error procesando imagen {url}: {e}")
            return None
    
    def extract_original_image_from_article(self, article_url: str) -> Optional[Dict]:
        """
        Extrae la imagen original más relevante de un artículo.
        
        Args:
            article_url: URL del artículo
            
        Returns:
            Diccionario con la mejor imagen encontrada
        """
        try:
            logger.info(f"Extrayendo imagen original de: {article_url}")
            
            # Descargar contenido del artículo
            response = self.session.get(article_url, timeout=30)
            response.raise_for_status()
            
            # Extraer imágenes candidatas
            candidate_images = self.extract_images_from_html(response.text, article_url)
            
            if not candidate_images:
                logger.warning(f"No se encontraron imágenes candidatas en: {article_url}")
                return None
            
            # Intentar descargar imágenes en orden de prioridad
            for img_info in candidate_images:
                result = self.download_and_validate_image(img_info)
                if result:
                    logger.info(f"Imagen original obtenida de {img_info['source']} con prioridad {img_info['priority']}")
                    return result
            
            logger.warning(f"No se pudo obtener ninguna imagen válida de: {article_url}")
            return None
            
        except Exception as e:
            logger.error(f"Error extrayendo imagen de artículo {article_url}: {e}")
            return None
    
    def generate_ai_relevant_fallback(self, article_title: str, article_content: str = "") -> Optional[Dict]:
        """
        Genera una imagen de fallback relevante usando AI.
        
        Args:
            article_title: Título del artículo
            article_content: Contenido del artículo (opcional)
            
        Returns:
            Diccionario con imagen generada o None
        """
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI no disponible para generar imagen de fallback")
            return None
        
        try:
            # Crear prompt basado en el contenido
            content_sample = article_content[:500] if article_content else ""
            
            prompt = f"""
            Create a relevant news image for this article:
            Title: {article_title}
            Content: {content_sample}
            
            The image should be:
            - Professional and news-appropriate
            - Relevant to the topic
            - High quality and clear
            - Suitable for a news dashboard
            """
            
            # Aquí se implementaría la llamada a DALL-E o similar
            # Por ahora, devolvemos None para usar el sistema de fallback estándar
            logger.info("AI image generation no implementado aún")
            return None
            
        except Exception as e:
            logger.error(f"Error generando imagen con AI: {e}")
            return None
    
    def get_smart_fallback_image(self, article_title: str, article_content: str = "", 
                                topic_keywords: List[str] = None) -> Optional[Dict]:
        """
        Obtiene una imagen de fallback inteligente y relevante.
        
        Args:
            article_title: Título del artículo
            article_content: Contenido del artículo
            topic_keywords: Palabras clave del tema
            
        Returns:
            Diccionario con imagen de fallback relevante
        """
        # 1. Intentar generar con AI
        ai_image = self.generate_ai_relevant_fallback(article_title, article_content)
        if ai_image:
            return ai_image
        
        # 2. Buscar en banco de imágenes por tema
        fallback_images = self._get_topic_based_fallback(topic_keywords or [])
        
        # 3. Seleccionar imagen que no haya sido usada
        for img_path in fallback_images:
            try:
                with open(img_path, 'rb') as f:
                    image_data = f.read()
                
                if not self.is_duplicate_image(image_data):
                    image_hash = self.mark_image_as_used(image_data)
                    
                    return {
                        'data': image_data,
                        'hash': image_hash,
                        'source': 'fallback_topic',
                        'path': img_path,
                        'metadata': {'fallback': True, 'topic_based': True}
                    }
                    
            except Exception as e:
                logger.warning(f"Error cargando imagen de fallback {img_path}: {e}")
                continue
        
        # 4. Fallback final: imagen genérica
        return self._get_generic_fallback()
    
    def _get_topic_based_fallback(self, keywords: List[str]) -> List[str]:
        """
        Obtiene rutas de imágenes de fallback basadas en temas.
        
        Args:
            keywords: Palabras clave del tema
            
        Returns:
            Lista de rutas de imágenes relevantes
        """
        base_path = os.path.join(os.path.dirname(__file__), 'data', 'fallback_images')
        
        # Mapeo de temas a carpetas de imágenes
        topic_mapping = {
            'conflict': ['conflict', 'war', 'military'],
            'politics': ['politics', 'government', 'election'],
            'economy': ['economy', 'business', 'finance'],
            'technology': ['technology', 'tech', 'cyber'],
            'environment': ['environment', 'climate', 'nature'],
            'health': ['health', 'medical', 'healthcare'],
            'security': ['security', 'police', 'safety'],
            'international': ['international', 'global', 'world']
        }
        
        relevant_images = []
        
        for topic, topic_keywords in topic_mapping.items():
            if any(keyword.lower() in ' '.join(keywords).lower() for keyword in topic_keywords):
                topic_path = os.path.join(base_path, topic)
                if os.path.exists(topic_path):
                    for filename in os.listdir(topic_path):
                        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                            relevant_images.append(os.path.join(topic_path, filename))
        
        return relevant_images
    
    def _get_generic_fallback(self) -> Dict:
        """
        Obtiene una imagen de fallback genérica.
        
        Returns:
            Diccionario con imagen genérica
        """
        # Crear imagen placeholder simple
        if PIL_AVAILABLE:
            try:
                # Crear imagen placeholder de 512x384
                img = Image.new('RGB', (512, 384), color=(220, 220, 220))
                
                # Agregar texto si es posible
                try:
                    from PIL import ImageDraw, ImageFont
                    draw = ImageDraw.Draw(img)
                    draw.text((256, 192), "News Image", fill=(100, 100, 100), anchor="mm")
                except ImportError:
                    pass
                
                # Convertir a bytes
                buffer = BytesIO()
                img.save(buffer, format='JPEG', quality=80)
                image_data = buffer.getvalue()
                
                return {
                    'data': image_data,
                    'hash': self.get_image_hash(image_data),
                    'source': 'generated_placeholder',
                    'metadata': {'width': 512, 'height': 384, 'fallback': True}
                }
                
            except Exception as e:
                logger.error(f"Error creando placeholder: {e}")
        
        # Fallback final: imagen vacía
        return {
            'data': b'',
            'hash': 'empty',
            'source': 'empty',
            'metadata': {'fallback': True, 'empty': True}
        }

# Funciones de utilidad para integración

def extract_original_image_for_article(article_data: Dict) -> Optional[Dict]:
    """
    Extrae imagen original para un artículo específico.
    
    Args:
        article_data: Datos del artículo con URL
        
    Returns:
        Imagen original o fallback relevante
    """
    extractor = ImageExtractor()
    
    article_url = article_data.get('url') or article_data.get('link')
    if not article_url:
        logger.warning("Artículo sin URL, usando fallback")
        return extractor.get_smart_fallback_image(
            article_data.get('title', ''),
            article_data.get('content', ''),
            article_data.get('keywords', [])
        )
    
    # Intentar extraer imagen original
    original_image = extractor.extract_original_image_from_article(article_url)
    
    if original_image:
        return original_image
    
    # Usar fallback inteligente
    return extractor.get_smart_fallback_image(
        article_data.get('title', ''),
        article_data.get('content', ''),
        article_data.get('keywords', [])
    )

def process_articles_images(articles: List[Dict]) -> List[Dict]:
    """
    Procesa imágenes para una lista de artículos.
    
    Args:
        articles: Lista de artículos
        
    Returns:
        Artículos con imágenes procesadas
    """
    extractor = ImageExtractor()
    processed_articles = []
    
    for i, article in enumerate(articles):
        try:
            logger.info(f"Procesando imagen {i+1}/{len(articles)}: {article.get('title', 'Sin título')[:50]}...")
            
            image_result = extract_original_image_for_article(article)
            
            if image_result:
                # Agregar información de imagen al artículo
                article_copy = article.copy()
                article_copy.update({
                    'image_data': base64.b64encode(image_result['data']).decode('utf-8') if image_result['data'] else '',
                    'image_hash': image_result['hash'],
                    'image_source': image_result.get('source', 'unknown'),
                    'image_metadata': image_result.get('metadata', {}),
                    'has_original_image': image_result.get('source') not in ['fallback_topic', 'generated_placeholder', 'empty']
                })
                
                processed_articles.append(article_copy)
            else:
                processed_articles.append(article)
                
        except Exception as e:
            logger.error(f"Error procesando imagen para artículo {i+1}: {e}")
            processed_articles.append(article)
    
    return processed_articles

if __name__ == "__main__":
    # Prueba del sistema de imágenes
    def test_image_extraction():
        """Prueba básica del extractor de imágenes."""
        print("🖼️ Probando extractor de imágenes...")
        
        extractor = ImageExtractor()
        
        # URLs de prueba
        test_urls = [
            "https://www.bbc.com/news",
            "https://edition.cnn.com",
            "https://www.reuters.com"
        ]
        
        for url in test_urls:
            try:
                result = extractor.extract_original_image_from_article(url)
                if result:
                    print(f"✅ Imagen extraída de {url}: {len(result['data'])} bytes")
                else:
                    print(f"❌ No se pudo extraer imagen de {url}")
            except Exception as e:
                print(f"❌ Error con {url}: {e}")
    
    test_image_extraction()
