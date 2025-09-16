#!/usr/bin/env python3
"""
Verificar noticias sin imagen y extraer imágenes de sus fuentes originales
"""

import sqlite3
import json
import requests
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import re
import os
from urllib.parse import urlparse, urljoin
import hashlib
from bs4 import BeautifulSoup

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'image_extraction_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

class ImageExtractor:
    """Extractor de imágenes para artículos sin imagen"""
    
    def __init__(self):
        self.db_path = Path('data/geopolitical_intel.db')
        self.images_dir = Path('data/images')
        self.images_dir.mkdir(exist_ok=True)
        
        # Headers para requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def check_articles_without_images(self):
        """Verificar artículos sin imagen en la base de datos"""
        
        if not self.db_path.exists():
            print("❌ Base de datos no encontrada")
            return
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        print("🔍 ANÁLISIS DE ARTÍCULOS SIN IMAGEN")
        print("=" * 60)
        
        # Total de artículos
        cursor.execute('SELECT COUNT(*) FROM articles')
        total_articles = cursor.fetchone()[0]
        
        # Artículos sin imagen
        cursor.execute('''
            SELECT COUNT(*) FROM articles 
            WHERE image_url IS NULL OR image_url = "" OR image_url LIKE "%placeholder%" OR image_url LIKE "%picsum%"
        ''')
        no_image = cursor.fetchone()[0]
        
        print(f"📊 Total de artículos: {total_articles}")
        print(f"❌ Sin imagen: {no_image} ({no_image/total_articles*100:.1f}%)")
        print(f"✅ Con imagen: {total_articles - no_image} ({(total_articles-no_image)/total_articles*100:.1f}%)")
        
        # Artículos de riesgo medio/alto sin imagen
        cursor.execute('''
            SELECT COUNT(*) FROM articles 
            WHERE risk_level IN ('medium', 'high')
            AND (image_url IS NULL OR image_url = "" OR image_url LIKE "%placeholder%" OR image_url LIKE "%picsum%")
        ''')
        high_risk_no_image = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM articles WHERE risk_level IN ("medium", "high")')
        total_high_risk = cursor.fetchone()[0]
        
        print(f"\n🎯 ARTÍCULOS DE RIESGO MEDIO/ALTO:")
        print(f"📊 Total: {total_high_risk}")
        print(f"❌ Sin imagen: {high_risk_no_image} ({high_risk_no_image/total_high_risk*100:.1f}%)")
        
        # Los 150 más recientes de riesgo medio/alto sin imagen
        cursor.execute('''
            SELECT COUNT(*) FROM (
                SELECT * FROM articles 
                WHERE risk_level IN ('medium', 'high')
                ORDER BY created_at DESC 
                LIMIT 150
            ) WHERE image_url IS NULL OR image_url = "" OR image_url LIKE "%placeholder%" OR image_url LIKE "%picsum%"
        ''')
        recent_no_image = cursor.fetchone()[0]
        
        print(f"\n📅 150 MÁS RECIENTES DE RIESGO MEDIO/ALTO:")
        print(f"❌ Sin imagen: {recent_no_image}/150 ({recent_no_image/150*100:.1f}%)")
        
        # Muestra de artículos sin imagen que tienen URL
        print(f"\n📋 ARTÍCULOS SIN IMAGEN CON URL DISPONIBLE:")
        print("-" * 60)
        
        cursor.execute('''
            SELECT id, title, url, risk_level
            FROM articles 
            WHERE (image_url IS NULL OR image_url = "" OR image_url LIKE "%placeholder%" OR image_url LIKE "%picsum%")
            AND url IS NOT NULL AND url != ""
            ORDER BY 
                CASE 
                    WHEN risk_level = 'high' THEN 1
                    WHEN risk_level = 'medium' THEN 2
                    WHEN risk_level = 'low' THEN 3
                    ELSE 4
                END,
                created_at DESC
            LIMIT 20
        ''')
        
        articles_with_url = cursor.fetchall()
        
        for i, (article_id, title, url, risk_level) in enumerate(articles_with_url, 1):
            print(f"{i:2d}. ID {article_id} [{risk_level.upper()}]: {title[:50]}...")
            print(f"    URL: {url[:70]}...")
            print()
        
        conn.close()
        
        return len(articles_with_url)
    
    def download_image_from_url(self, image_url: str, article_id: int) -> Optional[str]:
        """Descargar imagen desde URL"""
        try:
            response = requests.get(image_url, headers=self.headers, timeout=15, stream=True)
            if response.status_code == 200:
                # Generar nombre único
                url_hash = hashlib.md5(image_url.encode()).hexdigest()[:8]
                extension = '.jpg'
                
                content_type = response.headers.get('content-type', '')
                if 'png' in content_type:
                    extension = '.png'
                elif 'gif' in content_type:
                    extension = '.gif'
                elif 'webp' in content_type:
                    extension = '.webp'
                
                filename = f"article_{article_id}_{url_hash}{extension}"
                filepath = self.images_dir / filename
                
                # Descargar imagen
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Verificar que se descargó correctamente
                if filepath.exists() and filepath.stat().st_size > 1000:  # Al menos 1KB
                    logger.info(f"✅ Imagen descargada: {filename}")
                    return str(filepath)
                else:
                    filepath.unlink(missing_ok=True)
                    
        except Exception as e:
            logger.warning(f"⚠️ Error descargando imagen {image_url}: {e}")
        
        return None
    
    def extract_image_from_article(self, url: str, article_id: int) -> Optional[str]:
        """Extraer imagen principal del artículo"""
        try:
            logger.info(f"🔍 Extrayendo imagen de: {url}")
            response = requests.get(url, headers=self.headers, timeout=20)
            if response.status_code != 200:
                logger.warning(f"⚠️ Error HTTP {response.status_code} para {url}")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Lista de estrategias para encontrar imágenes, en orden de prioridad
            strategies = [
                # Meta tags de redes sociales
                ('og:image', lambda: soup.find('meta', property='og:image')),
                ('twitter:image', lambda: soup.find('meta', attrs={'name': 'twitter:image'})),
                ('twitter:image:src', lambda: soup.find('meta', attrs={'name': 'twitter:image:src'})),
                
                # Imágenes destacadas comunes
                ('featured-image', lambda: soup.select_one('img[class*="featured"]')),
                ('hero-image', lambda: soup.select_one('img[class*="hero"]')),
                ('main-image', lambda: soup.select_one('img[class*="main"]')),
                ('lead-image', lambda: soup.select_one('img[class*="lead"]')),
                
                # Selectores específicos por estructura
                ('article-img', lambda: soup.select_one('article img')),
                ('content-img', lambda: soup.select_one('.content img, .article-content img')),
                ('post-img', lambda: soup.select_one('.post img, .post-content img')),
                
                # Selectores genéricos de contenido
                ('main-content', lambda: soup.select_one('main img, .main img')),
                ('first-img', lambda: soup.select_one('img[src]')),
            ]
            
            for strategy_name, strategy_func in strategies:
                try:
                    result = strategy_func()
                    if result:
                        if strategy_name.startswith(('og:', 'twitter:')):
                            # Meta tags
                            image_url = result.get('content')
                        else:
                            # IMG elements
                            image_url = result.get('src') or result.get('data-src') or result.get('data-lazy-src')
                        
                        if image_url and self.is_valid_image_url(image_url, url):
                            logger.info(f"📷 Imagen encontrada con estrategia '{strategy_name}': {image_url}")
                            downloaded_path = self.download_image_from_url(image_url, article_id)
                            if downloaded_path:
                                return downloaded_path
                
                except Exception as e:
                    logger.debug(f"Error en estrategia '{strategy_name}': {e}")
                    continue
            
            logger.warning(f"⚠️ No se pudo encontrar imagen válida en {url}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo imagen de {url}: {e}")
            return None
    
    def is_valid_image_url(self, image_url: str, base_url: str) -> bool:
        """Validar y normalizar URL de imagen"""
        if not image_url:
            return False
            
        # Normalizar URL relativas
        if image_url.startswith('//'):
            image_url = 'https:' + image_url
        elif image_url.startswith('/'):
            base_netloc = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"
            image_url = urljoin(base_netloc, image_url)
        elif not image_url.startswith('http'):
            image_url = urljoin(base_url, image_url)
        
        # Verificar que sea una URL válida de imagen
        if not image_url.startswith('http'):
            return False
        
        # Verificar extensión o tipo
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        url_lower = image_url.lower()
        
        # Excluir imágenes obviamente inválidas
        invalid_patterns = ['logo', 'avatar', 'icon', 'button', 'spacer', '1x1', 'pixel']
        if any(pattern in url_lower for pattern in invalid_patterns):
            # Pero permitir si tiene extensión válida y tamaño razonable
            if not any(ext in url_lower for ext in valid_extensions):
                return False
        
        return any(ext in url_lower for ext in valid_extensions) or 'image' in url_lower or '/img/' in url_lower
    
    def extract_images_for_articles_without_images(self, limit: int = 50):
        """Extraer imágenes para artículos que no tienen imagen"""
        
        if not self.db_path.exists():
            print("❌ Base de datos no encontrada")
            return
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        print(f"🚀 EXTRAYENDO IMÁGENES PARA ARTÍCULOS SIN IMAGEN (LÍMITE: {limit})")
        print("=" * 70)
        
        # Obtener artículos sin imagen, priorizando alto riesgo
        cursor.execute('''
            SELECT id, title, url, risk_level
            FROM articles 
            WHERE (image_url IS NULL OR image_url = "" OR image_url LIKE "%placeholder%" OR image_url LIKE "%picsum%")
            AND url IS NOT NULL AND url != ""
            ORDER BY 
                CASE 
                    WHEN risk_level = 'high' THEN 1
                    WHEN risk_level = 'medium' THEN 2
                    WHEN risk_level = 'low' THEN 3
                    ELSE 4
                END,
                created_at DESC
            LIMIT ?
        ''', (limit,))
        
        articles = cursor.fetchall()
        total_articles = len(articles)
        
        print(f"📊 Artículos a procesar: {total_articles}")
        
        if total_articles == 0:
            print("✅ No hay artículos sin imagen para procesar")
            conn.close()
            return
        
        success_count = 0
        start_time = time.time()
        
        for i, (article_id, title, url, risk_level) in enumerate(articles, 1):
            print(f"\n📝 [{i}/{total_articles}] ID {article_id} [{risk_level.upper()}]")
            print(f"📰 {title[:60]}...")
            
            # Extraer imagen
            image_path = self.extract_image_from_article(url, article_id)
            
            if image_path:
                # Actualizar base de datos
                try:
                    cursor.execute(
                        'UPDATE articles SET image_url = ? WHERE id = ?',
                        (image_path, article_id)
                    )
                    conn.commit()
                    success_count += 1
                    logger.info(f"✅ Imagen asignada al artículo {article_id}")
                except Exception as e:
                    logger.error(f"❌ Error actualizando BD para artículo {article_id}: {e}")
            else:
                logger.warning(f"❌ No se pudo obtener imagen para artículo {article_id}")
            
            # Pausa para no sobrecargar servidores
            time.sleep(2)
            
            # Progreso cada 10 artículos
            if i % 10 == 0:
                elapsed = time.time() - start_time
                rate = i / elapsed * 60  # artículos por minuto
                print(f"📈 Progreso: {i}/{total_articles} ({success_count} exitosos) - {rate:.1f} art/min")
        
        conn.close()
        
        # Reporte final
        elapsed_total = time.time() - start_time
        success_rate = (success_count / total_articles * 100) if total_articles > 0 else 0
        
        print(f"\n🎯 EXTRACCIÓN DE IMÁGENES COMPLETADA:")
        print(f"   - Exitosos: {success_count}/{total_articles} ({success_rate:.1f}%)")
        print(f"   - Tiempo total: {elapsed_total/60:.1f} minutos")
        if total_articles > 0:
            print(f"   - Velocidad promedio: {total_articles/(elapsed_total/60):.1f} artículos/minuto")
        
        return success_count, total_articles

def main():
    """Función principal"""
    extractor = ImageExtractor()
    
    print("🖼️ EXTRACTOR DE IMÁGENES PARA ARTÍCULOS")
    print("=" * 50)
    
    # 1. Verificar estado actual
    articles_to_process = extractor.check_articles_without_images()
    
    if articles_to_process == 0:
        print("\n✅ Todos los artículos ya tienen imagen asignada")
        return
    
    # 2. Confirmar procesamiento
    print(f"\n¿Procesar {min(articles_to_process, 50)} artículos sin imagen? (y/N): ", end="")
    try:
        confirm = input().lower().strip()
        if confirm != 'y':
            print("❌ Procesamiento cancelado")
            return
    except KeyboardInterrupt:
        print("\n❌ Procesamiento cancelado por el usuario")
        return
    
    # 3. Extraer imágenes
    success, total = extractor.extract_images_for_articles_without_images(50)
    
    print(f"\n{'='*50}")
    print(f"✅ PROCESAMIENTO COMPLETADO:")
    print(f"   - Imágenes extraídas: {success}")
    print(f"   - Total procesados: {total}")
    if total > 0:
        print(f"   - Tasa de éxito: {success/total*100:.1f}%")
    print(f"{'='*50}")

if __name__ == '__main__':
    main()
