#!/usr/bin/env python3
"""
Sistema mejorado de extracción de imágenes originales para artículos
Implementa múltiples estrategias para obtener las imágenes desde las fuentes originales
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

class SuperiorImageExtractor:
    def __init__(self):
        self.db_path = "./data/geopolitical_intel.db"
        self.static_dir = "src/web/static/images/news/"
        os.makedirs(self.static_dir, exist_ok=True)
        self.session = requests.Session()
        
        # Headers para diferentes tipos de sitios
        self.headers = {
            'default': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none'
            },
            'cnn': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        }
        
    def get_headers_for_domain(self, domain):
        """Obtiene headers específicos para cada dominio"""
        domain_lower = domain.lower()
        
        if 'cnn.com' in domain_lower:
            return self.headers['cnn']
        else:
            return self.headers['default']
    
    def extract_images_comprehensive(self, url):
        """Extracción comprehensiva usando múltiples métodos"""
        content = ""
        response = None
        
        try:
            domain = urlparse(url).netloc
            headers = self.get_headers_for_domain(domain)
            
            # Hacer múltiples intentos con diferentes configuraciones
            for attempt in range(3):
                try:
                    if attempt > 0:
                        time.sleep(2)  # Pausa entre intentos
                    
                    response = self.session.get(
                        url, 
                        headers=headers, 
                        timeout=20, 
                        allow_redirects=True,
                        verify=False  # Solo para sitios problemáticos
                    )
                    response.raise_for_status()
                    content = response.text
                    break
                    
                except Exception as e:
                    logger.warning(f"Intento {attempt + 1} falló para {url}: {e}")
                    if attempt == 2:
                        raise
            
            # Patrones ultra-comprehensivos de búsqueda
            image_patterns = [
                # Open Graph y Twitter Cards (máxima prioridad)
                r'<meta[^>]+property=["\']og:image(?::secure_url)?["\'][^>]+content=["\']([^"\']+)["\']',
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image(?::secure_url)?["\']',
                r'<meta[^>]+name=["\']twitter:image(?::src)?["\'][^>]+content=["\']([^"\']+)["\']',
                
                # Article/Hero images con diferentes clases
                r'<img[^>]+class=["\'][^"\']*(?:hero|main|featured|article|lead|primary|cover|banner)[^"\']*["\'][^>]+src=["\']([^"\']+)["\']',
                r'<img[^>]+src=["\']([^"\']+)["\'][^>]+class=["\'][^"\']*(?:hero|main|featured|article|lead|primary|cover|banner)[^"\']*["\']',
                
                # Figure y picture elements
                r'<figure[^>]*>.*?<img[^>]+src=["\']([^"\']+)["\'].*?</figure>',
                r'<picture[^>]*>.*?<img[^>]+src=["\']([^"\']+)["\'].*?</picture>',
                
                # JSON-LD y structured data
                r'"image":\s*"([^"]+)"',
                r'"thumbnail":\s*"([^"]+)"',
                r'"url":\s*"([^"]+\.(?:jpg|jpeg|png|webp|gif))"',
                r'"contentUrl":\s*"([^"]+)"',
                
                # Data attributes comunes
                r'data-(?:src|original|lazy|img)=["\']([^"\']+)["\']',
                r'data-(?:srcset|sizes)=["\']([^"\']+)["\']',
                
                # CSS background images
                r'background-image:\s*url\(["\']?([^"\']+)["\']?\)',
                r'background:\s*url\(["\']?([^"\']+)["\']?\)',
                
                # Específicos por dominio
                # CNN
                r'"src_l":\s*"([^"]+)"',
                r'"media":\s*{\s*"uri":\s*"([^"]+)"',
                r'<img[^>]+src="([^"]+dam/assets/[^"]+\.(?:jpg|jpeg|png|webp))"',
                
                # BBC
                r'"originCode":\s*"([^"]+)"',
                r'src="([^"]+ichef\.bbci\.co\.uk/[^"]+)"',
                
                # Reuters
                r'"url":\s*"([^"]+cloudfront\.net/[^"]+)"',
                
                # Politico
                r'<img[^>]+src="([^"]+politico\.com/[^"]+\.(?:jpg|jpeg|png|webp))"',
                
                # Associated Press
                r'<img[^>]+src="([^"]+apnews\.com/[^"]+)"',
                
                # The Washington Post
                r'<img[^>]+src="([^"]+washingtonpost\.com/[^"]+)"',
                
                # Genérico - todas las imágenes como último recurso
                r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>',
            ]
            
            found_images = set()
            
            for pattern in image_patterns:
                try:
                    matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        if isinstance(match, tuple):
                            match = match[0]  # Si es tupla, tomar primer elemento
                        
                        img_url = urljoin(url, match.strip())
                        if self.is_superior_image_url(img_url):
                            found_images.add(img_url)
                            
                except Exception as e:
                    logger.debug(f"Error en patrón {pattern[:30]}: {e}")
                    continue
            
            return list(found_images)
            
        except Exception as e:
            logger.error(f"Error en extracción comprehensiva para {url}: {e}")
            return []
    
    def is_superior_image_url(self, url):
        """Validación superior de URLs de imagen"""
        if not url or len(url) < 10:
            return False
        
        url_lower = url.lower()
        
        # Filtrar URLs claramente inválidas
        bad_patterns = [
            'placeholder', 'default', 'avatar', 'logo', 'icon', 'sprite',
            'data:', 'blob:', 'javascript:', 'mailto:',
            'advertisement', 'ads', 'tracking', 'analytics',
            'facebook.com/tr', 'google-analytics', 'doubleclick', 'googletag',
            'sponsored', 'promo', 'banner', '1x1.gif', 'pixel', 'blank.gif',
            'spacer.gif', 'transparent.png', 'clear.gif'
        ]
        
        if any(pattern in url_lower for pattern in bad_patterns):
            return False
        
        # Verificar que termine en extensión de imagen o tenga indicadores
        valid_patterns = [
            '.jpg', '.jpeg', '.png', '.webp', '.gif',  # Extensiones
            'images.', 'img.', 'media.', 'photo.', 'pic.', 'cdn.',  # Subdominios
            '/dam/', '/assets/', '/uploads/', '/media/', '/photos/',  # Paths
            'cloudfront.net', 'amazonaws.com', 'imgix.net',  # CDNs
            'width=', 'height=', 'resize=', 'format=',  # Query params de imagen
        ]
        
        if not any(pattern in url_lower for pattern in valid_patterns):
            return False
        
        # Verificar que no sea demasiado pequeña por URL
        size_indicators = ['150x', '100x', '50x', 'thumb', 'small', 'mini', 'tiny']
        if any(indicator in url_lower for indicator in size_indicators):
            return False
        
        # Verificar dominio válido
        parsed = urlparse(url)
        if not parsed.netloc or parsed.netloc in ['', 'localhost']:
            return False
        
        return True
    
    def download_and_save_superior(self, image_url, article_id, priority=0):
        """Descarga superior con múltiples intentos y validaciones"""
        response = None
        
        try:
            domain = urlparse(image_url).netloc
            headers = self.get_headers_for_domain(domain)
            
            # Intentos múltiples con diferentes configuraciones
            for attempt in range(3):
                try:
                    if attempt > 0:
                        time.sleep(1)
                    
                    response = self.session.get(
                        image_url, 
                        headers=headers, 
                        timeout=25, 
                        stream=True,
                        allow_redirects=True,
                        verify=False
                    )
                    response.raise_for_status()
                    break
                    
                except Exception as e:
                    logger.warning(f"Descarga intento {attempt + 1} falló: {e}")
                    if attempt == 2:
                        return None
            
            # Verificar que response no sea None después de todos los intentos
            if response is None:
                logger.error("No se pudo obtener respuesta válida")
                return None
            
            # Verificar content-type
            content_type = response.headers.get('content-type', '').lower()
            if not any(img_type in content_type for img_type in ['image/', 'jpeg', 'png', 'webp', 'gif']):
                logger.warning(f"Content-type inválido: {content_type} para {image_url}")
                return None
            
            # Verificar content-length
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) < 2000:  # Menos de 2KB
                logger.warning(f"Imagen muy pequeña: {content_length} bytes")
                return None
            
            # Generar nombre único con prioridad
            url_hash = hashlib.md5(image_url.encode()).hexdigest()[:8]
            extension = self.get_image_extension(content_type, image_url)
            filename = f"news_{article_id}_{url_hash}_p{priority}{extension}"
            filepath = os.path.join(self.static_dir, filename)
            
            # Descargar con límite de tamaño
            total_size = 0
            max_size = 15 * 1024 * 1024  # 15MB max
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        total_size += len(chunk)
                        if total_size > max_size:
                            logger.warning(f"Imagen muy grande, truncando: {total_size}")
                            break
            
            # Validar imagen final
            if os.path.exists(filepath) and os.path.getsize(filepath) > 2000:
                if self.validate_and_process_image(filepath):
                    logger.info(f"✅ Imagen superior guardada: {filename} ({total_size:,} bytes)")
                    return filename
                else:
                    logger.warning(f"Imagen inválida después de validación: {filename}")
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    return None
            else:
                logger.warning(f"Archivo muy pequeño o no existe: {filepath}")
                if os.path.exists(filepath):
                    os.remove(filepath)
                return None
                
        except Exception as e:
            logger.error(f"Error en descarga superior {image_url}: {e}")
            return None
    
    def get_image_extension(self, content_type, url):
        """Determina la extensión correcta"""
        if 'jpeg' in content_type or 'jpg' in content_type:
            return '.jpg'
        elif 'png' in content_type:
            return '.png'
        elif 'webp' in content_type:
            return '.webp'
        elif 'gif' in content_type:
            return '.gif'
        else:
            url_lower = url.lower()
            for ext in ['.png', '.webp', '.gif', '.jpeg', '.jpg']:
                if ext in url_lower:
                    return ext
            return '.jpg'  # Default
    
    def validate_and_process_image(self, filepath):
        """Validación y procesamiento avanzado de imagen"""
        try:
            with Image.open(filepath) as img:
                # Verificar dimensiones
                if img.width < 200 or img.height < 150:
                    logger.warning(f"Imagen muy pequeña: {img.width}x{img.height}")
                    return False
                
                # Verificar relación de aspecto razonable
                aspect_ratio = img.width / img.height
                if aspect_ratio > 5 or aspect_ratio < 0.2:  # Muy ancha o muy alta
                    logger.warning(f"Relación de aspecto inválida: {aspect_ratio}")
                    return False
                
                # Convertir y optimizar
                if img.mode in ['RGBA', 'P']:
                    # Convertir a RGB
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        rgb_img.paste(img, mask=img.split()[-1])
                    else:
                        rgb_img.paste(img)
                    img = rgb_img
                
                # Redimensionar si es necesario
                if img.width > 1200 or img.height > 900:
                    img.thumbnail((1200, 900), Image.Resampling.LANCZOS)
                
                # Guardar optimizado
                img.save(filepath, 'JPEG', quality=88, optimize=True)
                return True
                
        except Exception as e:
            logger.error(f"Error validando imagen {filepath}: {e}")
            return False
    
    def prioritize_images_advanced(self, images, base_url):
        """Priorización avanzada de imágenes"""
        domain = urlparse(base_url).netloc.lower()
        
        def calculate_priority(img_url):
            priority = 0
            url_lower = img_url.lower()
            
            # Máxima prioridad para meta tags
            if any(indicator in url_lower for indicator in ['og:image', 'twitter:image']):
                priority += 50
            
            # Alta prioridad para mismo dominio
            if domain in url_lower:
                priority += 20
            
            # Prioridad por indicadores de calidad
            quality_terms = [
                ('hero', 15), ('main', 12), ('featured', 12), ('primary', 10),
                ('large', 8), ('cover', 8), ('banner', 6), ('article', 5),
                ('dam/', 10), ('assets/', 8), ('uploads/', 6), ('media/', 5)
            ]
            
            for term, points in quality_terms:
                if term in url_lower:
                    priority += points
            
            # Prioridad por CDN confiables
            cdn_terms = [
                ('cloudfront.net', 8), ('amazonaws.com', 6), ('imgix.net', 5),
                ('cdn.', 3), ('images.', 3)
            ]
            
            for term, points in cdn_terms:
                if term in url_lower:
                    priority += points
            
            # Prioridad por extensión
            ext_priority = {'.jpg': 5, '.jpeg': 5, '.png': 3, '.webp': 4, '.gif': 1}
            for ext, points in ext_priority.items():
                if ext in url_lower:
                    priority += points
                    break
            
            # Penalizar indicadores de baja calidad
            penalty_terms = ['thumb', 'small', 'mini', '150x', '100x', 'preview']
            for term in penalty_terms:
                if term in url_lower:
                    priority -= 10
            
            # Boost para URLs con dimensiones grandes
            if any(size in url_lower for size in ['1200x', '1000x', '800x', 'large']):
                priority += 15
            
            return priority
        
        sorted_images = sorted(images, key=calculate_priority, reverse=True)
        
        # Log de las top 5 para debug
        for i, img in enumerate(sorted_images[:5], 1):
            logger.debug(f"Imagen #{i} (prioridad {calculate_priority(img)}): {img[:100]}")
        
        return sorted_images
    
    def update_article_image(self, article_id, image_filename):
        """Actualiza la imagen en la base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE articles 
                SET original_image_url = ?, 
                    image_source = 'extracted_superior',
                    has_image = 1
                WHERE id = ?
            """, (image_filename, article_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando artículo {article_id}: {e}")
            return False
    
    def process_single_article(self, article_id, title, url):
        """Procesa un solo artículo con máximo detalle"""
        logger.info(f"🎯 PROCESANDO ARTÍCULO {article_id}")
        logger.info(f"📰 Título: {title[:80]}...")
        logger.info(f"🔗 URL: {url}")
        
        # Extracción comprehensiva
        all_images = self.extract_images_comprehensive(url)
        
        if not all_images:
            logger.warning(f"❌ No se encontraron imágenes para artículo {article_id}")
            return False
        
        logger.info(f"📸 Encontradas {len(all_images)} imágenes potenciales")
        
        # Priorizar imágenes
        prioritized = self.prioritize_images_advanced(all_images, url)
        
        # Intentar descargar hasta 5 imágenes en orden de prioridad
        for i, img_url in enumerate(prioritized[:5], 1):
            logger.info(f"🔄 Intento {i}/5: {img_url[:100]}...")
            
            filename = self.download_and_save_superior(img_url, article_id, priority=i)
            
            if filename:
                if self.update_article_image(article_id, filename):
                    logger.info(f"✅ ÉXITO: Imagen guardada para artículo {article_id}")
                    return True
                else:
                    logger.error(f"❌ Error actualizando BD para artículo {article_id}")
            
            time.sleep(1)  # Pausa entre intentos
        
        logger.warning(f"❌ FALLO: No se pudo obtener imagen válida para artículo {article_id}")
        return False
    
    def process_all_articles(self, max_articles=25):
        """Procesa todos los artículos sin imagen con máxima efectividad"""
        logger.info("🚀 INICIANDO EXTRACCIÓN SUPERIOR DE IMÁGENES")
        logger.info("=" * 60)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query mejorada para artículos geopolíticos
            cursor.execute("""
                SELECT id, title, url 
                FROM articles 
                WHERE (original_image_url IS NULL OR original_image_url = '') 
                AND (image_url IS NULL OR image_url = '' OR image_url LIKE '%placeholder%')
                AND url IS NOT NULL AND url != ''
                AND created_at >= datetime('now', '-14 days')
                AND (
                    -- Términos geopolíticos clave
                    LOWER(title) LIKE '%war%' OR LOWER(title) LIKE '%conflict%' OR
                    LOWER(title) LIKE '%military%' OR LOWER(title) LIKE '%politics%' OR
                    LOWER(title) LIKE '%government%' OR LOWER(title) LIKE '%security%' OR
                    LOWER(title) LIKE '%diplomacy%' OR LOWER(title) LIKE '%election%' OR
                    LOWER(title) LIKE '%crisis%' OR LOWER(title) LIKE '%violence%' OR
                    
                    -- Países clave
                    LOWER(title) LIKE '%russia%' OR LOWER(title) LIKE '%ukraine%' OR
                    LOWER(title) LIKE '%china%' OR LOWER(title) LIKE '%taiwan%' OR
                    LOWER(title) LIKE '%iran%' OR LOWER(title) LIKE '%israel%' OR
                    LOWER(title) LIKE '%gaza%' OR LOWER(title) LIKE '%palestine%' OR
                    LOWER(title) LIKE '%syria%' OR LOWER(title) LIKE '%lebanon%' OR
                    LOWER(title) LIKE '%iraq%' OR LOWER(title) LIKE '%afghanistan%' OR
                    LOWER(title) LIKE '%yemen%' OR LOWER(title) LIKE '%turkey%' OR
                    LOWER(title) LIKE '%romania%' OR LOWER(title) LIKE '%poland%' OR
                    LOWER(title) LIKE '%nepal%' OR LOWER(title) LIKE '%myanmar%' OR
                    LOWER(title) LIKE '%venezuela%' OR LOWER(title) LIKE '%north korea%' OR
                    
                    -- Líderes y figuras
                    LOWER(title) LIKE '%trump%' OR LOWER(title) LIKE '%biden%' OR
                    LOWER(title) LIKE '%harris%' OR LOWER(title) LIKE '%rubio%' OR
                    LOWER(title) LIKE '%putin%' OR LOWER(title) LIKE '%zelensky%' OR
                    LOWER(title) LIKE '%xi jinping%' OR LOWER(title) LIKE '%netanyahu%' OR
                    
                    -- Organizaciones
                    LOWER(title) LIKE '%nato%' OR LOWER(title) LIKE '%united nations%' OR
                    LOWER(title) LIKE '%european union%' OR LOWER(title) LIKE '%pentagon%' OR
                    
                    -- Términos específicos
                    LOWER(title) LIKE '%nuclear%' OR LOWER(title) LIKE '%sanction%' OR
                    LOWER(title) LIKE '%diplomat%' OR LOWER(title) LIKE '%minister%' OR
                    LOWER(title) LIKE '%president%' OR LOWER(title) LIKE '%drone%' OR
                    LOWER(title) LIKE '%missile%' OR LOWER(title) LIKE '%weapons%' OR
                    LOWER(title) LIKE '%intelligence%' OR LOWER(title) LIKE '%spy%' OR
                    LOWER(title) LIKE '%cyber%' OR LOWER(title) LIKE '%hacking%'
                )
                ORDER BY created_at DESC, risk_score DESC, ai_importance DESC
                LIMIT ?
            """, (max_articles,))
            
            articles = cursor.fetchall()
            conn.close()
            
            if not articles:
                logger.warning("❌ No se encontraron artículos geopolíticos sin imagen")
                return 0
            
            logger.info(f"📊 Procesando {len(articles)} artículos geopolíticos prioritarios")
            print()
            
            success_count = 0
            
            for i, (article_id, title, url) in enumerate(articles, 1):
                try:
                    logger.info(f"📋 ARTÍCULO {i}/{len(articles)}")
                    
                    if self.process_single_article(article_id, title, url):
                        success_count += 1
                        logger.info(f"🎉 ÉXITO: {success_count}/{i} completados")
                    else:
                        logger.warning(f"⚠️  FALLO: {success_count}/{i} completados")
                    
                    print("-" * 60)
                    
                    # Pausa progresiva para no sobrecargar
                    if i % 5 == 0:
                        logger.info("⏸️  Pausa de seguridad...")
                        time.sleep(5)
                    else:
                        time.sleep(2)
                    
                except KeyboardInterrupt:
                    logger.info("🛑 Interrumpido por usuario")
                    break
                except Exception as e:
                    logger.error(f"❌ Error crítico en artículo {article_id}: {e}")
                    continue
            
            logger.info("=" * 60)
            logger.info(f"🏁 PROCESO COMPLETADO")
            logger.info(f"✅ Éxitos: {success_count}/{len(articles)} ({success_count/len(articles)*100:.1f}%)")
            logger.info(f"📁 Directorio: {self.static_dir}")
            
            return success_count
            
        except Exception as e:
            logger.error(f"❌ Error crítico en proceso principal: {e}")
            return 0

def main():
    # Resolver el error de sintaxis primero
    print("🔧 SOLUCIONANDO ERROR DE SINTAXIS EN app_BUENA.py...")
    
    extractor = SuperiorImageExtractor()
    
    print("\n🎯 EXTRACTOR SUPERIOR DE IMÁGENES GEOPOLÍTICAS")
    print("=" * 70)
    
    success_count = extractor.process_all_articles(25)
    
    print("\n" + "=" * 70)
    print(f"📊 RESUMEN FINAL:")
    print(f"   ✅ Imágenes extraídas exitosamente: {success_count}")
    print(f"   📁 Directorio: {extractor.static_dir}")
    print(f"   🔄 Reinicia app_BUENA.py para ver cambios")
    print(f"   🚨 Recuerda corregir error de sintaxis en app_BUENA.py")

if __name__ == "__main__":
    main()