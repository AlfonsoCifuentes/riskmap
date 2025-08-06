#!/usr/bin/env python3
"""
Asignador de imágenes para artículos del mosaico - Asegura que todos tengan imagen
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
import random

# Configurar logging sin emojis para evitar problemas de encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'assign_mosaic_images_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

class MosaicImageAssigner:
    """Asignador de imágenes para el mosaico - garantiza que todos los artículos tengan imagen"""
    
    def __init__(self):
        self.db_path = Path('data/geopolitical_intel.db')
        self.images_dir = Path('data/images')
        self.images_dir.mkdir(exist_ok=True)
        
        # Headers para requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Imágenes de alta calidad por categoría geopolítica
        self.stock_images = {
            'conflict': [
                'https://images.unsplash.com/photo-1541644387-0fce5b9c8224?w=800&h=600&fit=crop',  # Guerra abstracta
                'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop',  # Protestas
                'https://images.unsplash.com/photo-1473177027534-53d906e9abcb?w=800&h=600&fit=crop',  # Tensión internacional
            ],
            'politics': [
                'https://images.unsplash.com/photo-1574087449240-b3e4b56eb81c?w=800&h=600&fit=crop',  # Política internacional
                'https://images.unsplash.com/photo-1591789612395-50e7e7e65cb8?w=800&h=600&fit=crop',  # Diplomacia
                'https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=800&h=600&fit=crop',  # Gobierno
            ],
            'economy': [
                'https://images.unsplash.com/photo-1611224923853-80b023f02d71?w=800&h=600&fit=crop',  # Economía global
                'https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?w=800&h=600&fit=crop',  # Mercados
                'https://images.unsplash.com/photo-1543872084-c7e4c0d6d026?w=800&h=600&fit=crop',  # Comercio
            ],
            'technology': [
                'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=800&h=600&fit=crop',  # Tecnología
                'https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&h=600&fit=crop',  # Ciberseguridad
                'https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=800&h=600&fit=crop',  # Tech global
            ],
            'international': [
                'https://images.unsplash.com/photo-1589578527966-fdac0f44566c?w=800&h=600&fit=crop',  # Mundo
                'https://images.unsplash.com/photo-1579952363873-27d3bfad9c0d?w=800&h=600&fit=crop',  # Global
                'https://images.unsplash.com/photo-1569098644584-210bcd375b59?w=800&h=600&fit=crop',  # Internacional
            ],
            'energy': [
                'https://images.unsplash.com/photo-1497440001374-f26997328c1b?w=800&h=600&fit=crop',  # Energía
                'https://images.unsplash.com/photo-1513475382585-d06e58bcb0e0?w=800&h=600&fit=crop',  # Petróleo
                'https://images.unsplash.com/photo-1569163139394-de4e5f43e4e3?w=800&h=600&fit=crop',  # Poder energético
            ]
        }
    
    def categorize_article(self, title: str, content: str = "") -> str:
        """Categorizar artículo para asignar imagen apropiada"""
        text = f"{title} {content}".lower()
        
        # Palabras clave por categoría
        categories = {
            'conflict': ['guerra', 'war', 'conflict', 'violence', 'attack', 'bomb', 'militar', 'army', 'fight', 'batalla', 'israel', 'gaza', 'ukraine', 'russia'],
            'politics': ['president', 'gobierno', 'government', 'politics', 'election', 'vote', 'congress', 'senate', 'minister', 'trump', 'biden', 'political'],
            'economy': ['economy', 'economic', 'trade', 'market', 'tariff', 'inflation', 'gdp', 'comercio', 'mercado', 'economia', 'arancel'],
            'technology': ['technology', 'tech', 'cyber', 'digital', 'internet', 'ai', 'artificial', 'computer', 'tecnologia', 'ciberseguridad'],
            'energy': ['energy', 'oil', 'gas', 'nuclear', 'power', 'electricity', 'energia', 'petroleo', 'nucleares', 'poder']
        }
        
        # Contar matches por categoría
        scores = {}
        for category, keywords in categories.items():
            scores[category] = sum(1 for keyword in keywords if keyword in text)
        
        # Retornar categoría con más matches o 'international' por defecto
        if any(scores.values()):
            return max(scores, key=scores.get)
        return 'international'
    
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
                    logger.info(f"Imagen descargada exitosamente: {filename}")
                    return str(filepath)
                else:
                    filepath.unlink(missing_ok=True)
                    
        except Exception as e:
            logger.warning(f"Error descargando imagen {image_url}: {e}")
        
        return None
    
    def extract_image_from_article(self, url: str, article_id: int) -> Optional[str]:
        """Extraer imagen principal del artículo"""
        try:
            logger.info(f"Extrayendo imagen de: {url}")
            response = requests.get(url, headers=self.headers, timeout=20)
            if response.status_code != 200:
                logger.warning(f"Error HTTP {response.status_code} para {url}")
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
                            logger.info(f"Imagen encontrada con estrategia '{strategy_name}': {image_url}")
                            downloaded_path = self.download_image_from_url(image_url, article_id)
                            if downloaded_path:
                                return downloaded_path
                
                except Exception as e:
                    logger.debug(f"Error en estrategia '{strategy_name}': {e}")
                    continue
            
            logger.warning(f"No se pudo encontrar imagen válida en {url}")
            return None
            
        except Exception as e:
            logger.error(f"Error extrayendo imagen de {url}: {e}")
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
    
    def assign_stock_image(self, article_id: int, title: str, content: str = "") -> Optional[str]:
        """Asignar imagen de stock apropiada según categoría del artículo"""
        category = self.categorize_article(title, content)
        images = self.stock_images.get(category, self.stock_images['international'])
        
        # Seleccionar imagen aleatoria de la categoría
        selected_image = random.choice(images)
        
        logger.info(f"Asignando imagen de stock categoría '{category}': {selected_image}")
        
        # Descargar imagen de stock
        downloaded_path = self.download_image_from_url(selected_image, article_id)
        return downloaded_path
    
    def check_and_assign_mosaic_images(self):
        """Verificar y asignar imágenes a artículos del mosaico que no las tienen"""
        
        if not self.db_path.exists():
            print("ERROR: Base de datos no encontrada")
            return
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        print("ASIGNADOR DE IMAGENES PARA MOSAICO")
        print("=" * 50)
        
        # Obtener artículos que aparecen en el mosaico sin imagen
        # Estos son los artículos de riesgo medio/alto más recientes que no tienen imagen
        cursor.execute('''
            SELECT id, title, url, risk_level, summary
            FROM articles 
            WHERE risk_level IN ('medium', 'high')
            AND (image_url IS NULL OR image_url = "" OR image_url LIKE "%placeholder%" OR image_url LIKE "%picsum%")
            ORDER BY created_at DESC 
            LIMIT 50
        ''')
        
        articles_without_images = cursor.fetchall()
        total_articles = len(articles_without_images)
        
        print(f"Articulos de mosaico sin imagen: {total_articles}")
        
        if total_articles == 0:
            print("EXITO: Todos los articulos del mosaico ya tienen imagen")
            conn.close()
            return
        
        print(f"Procesando {total_articles} articulos...")
        print("-" * 50)
        
        success_count = 0
        stock_count = 0
        start_time = time.time()
        
        for i, (article_id, title, url, risk_level, summary) in enumerate(articles_without_images, 1):
            print(f"[{i}/{total_articles}] ID {article_id} [{risk_level.upper()}]")
            print(f"Titulo: {title[:60]}...")
            
            image_path = None
            
            # 1. Intentar extraer imagen original si hay URL
            if url and url.strip():
                image_path = self.extract_image_from_article(url, article_id)
                
                if image_path:
                    print(f"  EXITO: Imagen extraida de fuente original")
                else:
                    print(f"  AVISO: No se pudo extraer imagen original")
            
            # 2. Si no se pudo obtener imagen original, asignar stock image
            if not image_path:
                content = summary or ""
                image_path = self.assign_stock_image(article_id, title, content)
                
                if image_path:
                    print(f"  EXITO: Imagen de stock asignada")
                    stock_count += 1
                else:
                    print(f"  ERROR: No se pudo asignar imagen")
                    continue
            
            # 3. Actualizar base de datos
            try:
                cursor.execute(
                    'UPDATE articles SET image_url = ? WHERE id = ?',
                    (image_path, article_id)
                )
                conn.commit()
                success_count += 1
                logger.info(f"Imagen asignada exitosamente al articulo {article_id}")
            except Exception as e:
                logger.error(f"Error actualizando BD para articulo {article_id}: {e}")
            
            # Pausa para no sobrecargar servidores
            time.sleep(1)
            
            # Progreso cada 10 artículos
            if i % 10 == 0:
                elapsed = time.time() - start_time
                rate = i / elapsed * 60  # artículos por minuto
                print(f"Progreso: {i}/{total_articles} ({success_count} exitosos) - {rate:.1f} art/min")
                print()
        
        conn.close()
        
        # Reporte final
        elapsed_total = time.time() - start_time
        success_rate = (success_count / total_articles * 100) if total_articles > 0 else 0
        original_count = success_count - stock_count
        
        print("=" * 50)
        print("ASIGNACION DE IMAGENES COMPLETADA:")
        print(f"  Total procesados: {total_articles}")
        print(f"  Exitosos: {success_count} ({success_rate:.1f}%)")
        print(f"  Imagenes originales: {original_count}")
        print(f"  Imagenes de stock: {stock_count}")
        print(f"  Tiempo total: {elapsed_total/60:.1f} minutos")
        if total_articles > 0:
            print(f"  Velocidad promedio: {total_articles/(elapsed_total/60):.1f} articulos/minuto")
        print("=" * 50)
        
        return success_count, total_articles, stock_count
    
    def verify_mosaic_coverage(self):
        """Verificar que todos los artículos del mosaico tienen imagen"""
        
        if not self.db_path.exists():
            print("ERROR: Base de datos no encontrada")
            return
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        print("VERIFICACION DE COBERTURA DE IMAGENES EN MOSAICO")
        print("=" * 55)
        
        # Los 150 artículos de riesgo medio/alto más recientes (mosaico típico)
        cursor.execute('''
            SELECT COUNT(*) FROM (
                SELECT * FROM articles 
                WHERE risk_level IN ('medium', 'high')
                ORDER BY created_at DESC 
                LIMIT 150
            )
        ''')
        total_mosaic = cursor.fetchone()[0]
        
        # Los que tienen imagen
        cursor.execute('''
            SELECT COUNT(*) FROM (
                SELECT * FROM articles 
                WHERE risk_level IN ('medium', 'high')
                ORDER BY created_at DESC 
                LIMIT 150
            ) WHERE image_url IS NOT NULL AND image_url != "" 
            AND image_url NOT LIKE "%placeholder%" AND image_url NOT LIKE "%picsum%"
        ''')
        with_images = cursor.fetchone()[0]
        
        without_images = total_mosaic - with_images
        coverage = (with_images / total_mosaic * 100) if total_mosaic > 0 else 0
        
        print(f"Articulos en mosaico (150 mas recientes medio/alto): {total_mosaic}")
        print(f"Con imagen asignada: {with_images}")
        print(f"Sin imagen: {without_images}")
        print(f"Cobertura: {coverage:.1f}%")
        
        if coverage >= 100:
            print("EXCELENTE: Cobertura completa del mosaico!")
        elif coverage >= 90:
            print("MUY BIEN: Cobertura casi completa")
        elif coverage >= 75:
            print("BIEN: Buena cobertura")
        else:
            print("ATENCION: Cobertura insuficiente")
        
        # Mostrar algunos ejemplos sin imagen
        if without_images > 0:
            print(f"\nEjemplos de articulos sin imagen:")
            print("-" * 40)
            
            cursor.execute('''
                SELECT id, title, risk_level
                FROM articles 
                WHERE risk_level IN ('medium', 'high')
                AND (image_url IS NULL OR image_url = "" OR image_url LIKE "%placeholder%" OR image_url LIKE "%picsum%")
                ORDER BY created_at DESC 
                LIMIT 10
            ''')
            
            examples = cursor.fetchall()
            for article_id, title, risk_level in examples:
                print(f"  ID {article_id} [{risk_level.upper()}]: {title[:50]}...")
        
        conn.close()
        
        return coverage, with_images, without_images

def main():
    """Función principal"""
    assigner = MosaicImageAssigner()
    
    print("ASIGNADOR DE IMAGENES PARA MOSAICO GEOPOLITICO")
    print("=" * 60)
    
    # 1. Verificar estado actual
    coverage, with_images, without_images = assigner.verify_mosaic_coverage()
    
    if coverage >= 100:
        print("\nTodos los articulos del mosaico ya tienen imagen asignada!")
        return
    
    # 2. Confirmar procesamiento
    print(f"\nAsignar imagenes a {without_images} articulos del mosaico? (y/N): ", end="")
    try:
        confirm = input().lower().strip()
        if confirm != 'y':
            print("Procesamiento cancelado")
            return
    except KeyboardInterrupt:
        print("\nProcesamiento cancelado por el usuario")
        return
    
    # 3. Asignar imágenes
    success, total, stock = assigner.check_and_assign_mosaic_images()
    
    # 4. Verificar resultado final
    print("\nVerificando resultado final...")
    final_coverage, final_with, final_without = assigner.verify_mosaic_coverage()
    
    print(f"\nRESULTADO FINAL:")
    print(f"  Cobertura inicial: {coverage:.1f}%")
    print(f"  Cobertura final: {final_coverage:.1f}%")
    print(f"  Mejora: +{final_coverage - coverage:.1f}%")
    
    if final_coverage >= 100:
        print("  EXITO: Cobertura completa del mosaico alcanzada!")
    else:
        print(f"  PENDIENTE: {final_without} articulos aun sin imagen")

if __name__ == '__main__':
    main()
