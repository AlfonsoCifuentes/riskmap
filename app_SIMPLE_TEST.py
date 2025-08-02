#!/usr/bin/env python3
"""
SIMPLE Test version - GeopoliticalRisk Dashboard Backend
Versión simplificada para testear los nuevos endpoints de imágenes
"""

import os
import sys
import logging
import sqlite3
import time
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import threading
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
from PIL import Image
import io

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("[WARNING] python-dotenv not installed. Environment variables from .env files won't be loaded.")
    pass

# Database configuration
def get_database_path():
    """Obtener la ruta de la base de datos desde variables de entorno"""
    db_path = os.getenv('DATABASE_PATH', './data/geopolitical_intel.db')
    return db_path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SimpleRiskDashboard:
    def __init__(self):
        self.db_path = get_database_path()
        self.system_state = {
            'image_extraction_task': None,
            'alerts': []
        }
        self.background_tasks = {}
    
    def extract_image_from_url(self, url, article_id=None, title=""):
        """Extraer imagen de la URL del artículo con mejoras de calidad"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar imágenes con diferentes estrategias
            image_candidates = []
            
            # 1. Meta tags de OpenGraph y Twitter
            for meta in soup.find_all('meta', property=['og:image', 'twitter:image']):
                if meta.get('content'):
                    image_candidates.append({
                        'url': meta['content'],
                        'priority': 10,
                        'source': 'meta'
                    })
            
            # 2. Imágenes del contenido principal
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src')
                if src:
                    # Filtrar imágenes obvias de baja calidad
                    if any(skip in src.lower() for skip in ['icon', 'logo', 'button', 'ad', 'banner']):
                        continue
                    
                    # Calcular prioridad basada en tamaño aparente
                    priority = 5
                    if any(indicator in src.lower() for indicator in ['large', 'full', 'main', 'hero']):
                        priority = 8
                    elif any(indicator in src.lower() for indicator in ['thumb', 'small', '150x', '100x']):
                        priority = 2
                    
                    image_candidates.append({
                        'url': src,
                        'priority': priority,
                        'source': 'content'
                    })
            
            if not image_candidates:
                logger.warning(f"No se encontraron imágenes para: {url}")
                return None
            
            # Ordenar por prioridad y seleccionar la mejor
            image_candidates.sort(key=lambda x: x['priority'], reverse=True)
            
            # Validar las mejores imágenes
            for candidate in image_candidates[:3]:  # Revisar solo las 3 mejores
                try:
                    image_url = candidate['url']
                    if not image_url.startswith('http'):
                        image_url = urljoin(url, image_url)
                    
                    # Verificar que la imagen existe y es válida
                    img_response = requests.get(image_url, headers=headers, timeout=5)
                    if img_response.status_code == 200:
                        # Verificar que es realmente una imagen
                        try:
                            img = Image.open(io.BytesIO(img_response.content))
                            width, height = img.size
                            
                            # Preferir imágenes más grandes
                            if width >= 300 and height >= 200:
                                logger.info(f"✅ Imagen de calidad encontrada: {width}x{height} - {image_url}")
                                return image_url
                            elif width >= 150 and height >= 100:
                                logger.info(f"⚠️ Imagen aceptable encontrada: {width}x{height} - {image_url}")
                                # Seguir buscando una mejor, pero guardar esta como backup
                                backup_image = image_url
                        except Exception:
                            continue  # No es una imagen válida
                    
                except Exception as e:
                    logger.debug(f"Error validando imagen {candidate['url']}: {e}")
                    continue
            
            # Si no encontramos una imagen de alta calidad, usar la backup
            if 'backup_image' in locals():
                return backup_image
            
            logger.warning(f"No se pudo extraer imagen válida de: {url}")
            return None
            
        except Exception as e:
            logger.error(f"Error extrayendo imagen de {url}: {e}")
            return None
    
    def get_articles_without_images(self, limit=50):
        """Obtener artículos que no tienen imagen o tienen imágenes de baja calidad"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, title, url, source, image_url
                    FROM articles 
                    WHERE (
                        image_url IS NULL 
                        OR image_url = '' 
                        OR image_url LIKE '%placeholder%' 
                        OR image_url LIKE '%picsum%'
                        OR image_url LIKE '%via.placeholder%'
                        OR image_url LIKE '%300x200%'
                        OR image_url LIKE '%400x300%'
                    )
                    AND url IS NOT NULL 
                    AND url != ''
                    ORDER BY id DESC
                    LIMIT ?
                """, (limit,))
                articles = cursor.fetchall()
                logger.info(f"Encontrados {len(articles)} artículos que necesitan imágenes de mejor calidad")
                return articles
        except Exception as e:
            logger.error(f"Error obteniendo artículos sin imagen: {e}")
            return []
    
    def get_articles_with_low_quality_images(self):
        """Obtener artículos con imágenes de baja calidad"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Buscar artículos con URLs de imagen que podrían ser de baja calidad
                cursor.execute("""
                    SELECT id, title, url, image_url
                    FROM articles 
                    WHERE image_url IS NOT NULL 
                    AND image_url != '' 
                    AND image_url NOT LIKE '%placeholder%'
                    AND image_url NOT LIKE '%via.placeholder%'
                    AND image_url NOT LIKE '%example.com%'
                    AND image_url NOT LIKE '%picsum%'
                    AND (image_url LIKE '%150x%' 
                         OR image_url LIKE '%100x%' 
                         OR image_url LIKE '%small%'
                         OR image_url LIKE '%thumb%'
                         OR image_url LIKE '%icon%'
                         OR image_url LIKE '%64x%'
                         OR image_url LIKE '%48x%'
                         OR LENGTH(image_url) < 30)
                    ORDER BY created_at DESC
                    LIMIT 100
                """)
                
                articles = cursor.fetchall()
                logger.info(f"Encontrados {len(articles)} artículos con posibles imágenes de baja calidad")
                return articles
                
        except Exception as e:
            logger.error(f"Error obteniendo artículos con imágenes de baja calidad: {e}")
            return []
    
    def update_article_image(self, article_id, image_url):
        """Actualizar la imagen de un artículo en la base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE articles 
                    SET image_url = ? 
                    WHERE id = ?
                """, (image_url, article_id))
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"✅ Imagen actualizada para artículo {article_id}: {image_url}")
                    return True
                else:
                    logger.warning(f"⚠️ No se encontró artículo con ID {article_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error actualizando imagen del artículo {article_id}: {e}")
            return False

# Crear instancia de la app
app = Flask(__name__)
CORS(app)
dashboard = SimpleRiskDashboard()

@app.route('/api/images/ensure-all', methods=['POST'])
def ensure_all_images():
    """Endpoint para asegurar que todos los artículos tengan imágenes"""
    try:
        logger.info("🔄 Iniciando proceso para asegurar imágenes en todos los artículos")
        
        # Obtener artículos sin imágenes
        articles_without_images = dashboard.get_articles_without_images(100)
        
        if not articles_without_images:
            return jsonify({
                'success': True,
                'message': 'Todos los artículos ya tienen imágenes',
                'processed': 0,
                'total': 0
            })
        
        # Procesar artículos en background
        def process_images():
            processed = 0
            errors = 0
            
            for article_id, title, url, source, current_image in articles_without_images:
                try:
                    logger.info(f"🔍 Procesando: {title[:50]}...")
                    
                    # Extraer imagen
                    image_url = dashboard.extract_image_from_url(url, article_id, title)
                    
                    if image_url:
                        # Actualizar en la base de datos
                        if dashboard.update_article_image(article_id, image_url):
                            processed += 1
                            logger.info(f"✅ Imagen agregada para: {title[:50]}...")
                        else:
                            errors += 1
                    else:
                        errors += 1
                    
                    # Pausa para no sobrecargar
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error procesando artículo {article_id}: {e}")
                    errors += 1
            
            logger.info(f"🎯 Proceso completado: {processed} imágenes procesadas, {errors} errores")
        
        # Ejecutar en background
        thread = threading.Thread(target=process_images)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Proceso iniciado para {len(articles_without_images)} artículos',
            'total': len(articles_without_images),
            'status': 'processing'
        })
        
    except Exception as e:
        logger.error(f"Error en ensure_all_images: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/images/quality-check', methods=['POST'])
def improve_image_quality():
    """Endpoint para mejorar la calidad de imágenes existentes"""
    try:
        logger.info("🔄 Iniciando mejora de calidad de imágenes")
        
        # Obtener artículos con imágenes de baja calidad
        articles_low_quality = dashboard.get_articles_with_low_quality_images()
        
        if not articles_low_quality:
            return jsonify({
                'success': True,
                'message': 'No se encontraron imágenes de baja calidad',
                'improved': 0,
                'total': 0
            })
        
        # Procesar mejoras en background
        def improve_images():
            improved = 0
            errors = 0
            
            for article_id, title, url, current_image in articles_low_quality:
                try:
                    logger.info(f"🔍 Mejorando imagen para: {title[:50]}...")
                    
                    # Buscar imagen de mejor calidad
                    new_image_url = dashboard.extract_image_from_url(url, article_id, title)
                    
                    if new_image_url and new_image_url != current_image:
                        # Actualizar en la base de datos
                        if dashboard.update_article_image(article_id, new_image_url):
                            improved += 1
                            logger.info(f"✅ Imagen mejorada para: {title[:50]}...")
                        else:
                            errors += 1
                    
                    # Pausa para no sobrecargar
                    time.sleep(3)
                    
                except Exception as e:
                    logger.error(f"Error mejorando imagen para artículo {article_id}: {e}")
                    errors += 1
            
            logger.info(f"🎯 Mejora completada: {improved} imágenes mejoradas, {errors} errores")
        
        # Ejecutar en background
        thread = threading.Thread(target=improve_images)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Proceso de mejora iniciado para {len(articles_low_quality)} imágenes',
            'total': len(articles_low_quality),
            'status': 'improving'
        })
        
    except Exception as e:
        logger.error(f"Error en improve_image_quality: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/images/status', methods=['GET'])
def get_image_status():
    """Obtener estadísticas del estado de las imágenes"""
    try:
        with sqlite3.connect(dashboard.db_path) as conn:
            cursor = conn.cursor()
            
            # Total de artículos
            cursor.execute("SELECT COUNT(*) FROM articles")
            total_articles = cursor.fetchone()[0]
            
            # Artículos con imágenes
            cursor.execute("""
                SELECT COUNT(*) FROM articles 
                WHERE image_url IS NOT NULL 
                AND image_url != '' 
                AND image_url NOT LIKE '%placeholder%'
                AND image_url NOT LIKE '%picsum%'
            """)
            with_images = cursor.fetchone()[0]
            
            # Artículos sin imágenes
            without_images = total_articles - with_images
            
            # Imágenes potencialmente de baja calidad
            cursor.execute("""
                SELECT COUNT(*) FROM articles 
                WHERE image_url IS NOT NULL 
                AND image_url != '' 
                AND image_url NOT LIKE '%placeholder%'
                AND (image_url LIKE '%150x%' 
                     OR image_url LIKE '%100x%' 
                     OR image_url LIKE '%small%'
                     OR image_url LIKE '%thumb%')
            """)
            low_quality = cursor.fetchone()[0]
            
            coverage_percentage = (with_images / total_articles * 100) if total_articles > 0 else 0
            
            return jsonify({
                'total_articles': total_articles,
                'with_images': with_images,
                'without_images': without_images,
                'low_quality_images': low_quality,
                'coverage_percentage': round(coverage_percentage, 2),
                'status': 'healthy' if coverage_percentage > 80 else 'needs_improvement'
            })
            
    except Exception as e:
        logger.error(f"Error obteniendo estado de imágenes: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/articles', methods=['GET'])
def get_articles():
    """Obtener artículos para el dashboard - excluyendo el hero"""
    try:
        with sqlite3.connect(dashboard.db_path) as conn:
            cursor = conn.cursor()
            
            # Obtener el ID del artículo hero primero
            cursor.execute("""
                SELECT id FROM articles 
                WHERE risk_level IN ('HIGH', 'VERY_HIGH', 'CRITICAL')
                ORDER BY risk_score DESC, created_at DESC 
                LIMIT 1
            """)
            hero_result = cursor.fetchone()
            hero_id = hero_result[0] if hero_result else None
            
            # Obtener artículos para el mosaico (excluyendo el hero)
            if hero_id:
                cursor.execute("""
                    SELECT id, title, content, risk_level, risk_score, 
                           source, created_at, image_url, url
                    FROM articles 
                    WHERE id != ?
                    ORDER BY created_at DESC 
                    LIMIT 12
                """, (hero_id,))
            else:
                cursor.execute("""
                    SELECT id, title, content, risk_level, risk_score, 
                           source, created_at, image_url, url
                    FROM articles 
                    ORDER BY created_at DESC 
                    LIMIT 12
                """)
            
            articles = []
            for row in cursor.fetchall():
                article = {
                    'id': row[0],
                    'title': row[1],
                    'content': row[2][:200] + "..." if len(row[2]) > 200 else row[2],
                    'risk_level': row[3],
                    'risk_score': row[4],
                    'source': row[5],
                    'created_at': row[6],
                    'image_url': row[7] if row[7] and 'placeholder' not in row[7] else None,
                    'url': row[8]
                }
                articles.append(article)
            
            return jsonify(articles)
            
    except Exception as e:
        logger.error(f"Error obteniendo artículos: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/hero-article', methods=['GET'])
def get_hero_article():
    """Obtener el artículo principal (hero)"""
    try:
        with sqlite3.connect(dashboard.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, content, risk_level, risk_score, 
                       source, created_at, image_url, url
                FROM articles 
                WHERE risk_level IN ('HIGH', 'VERY_HIGH', 'CRITICAL')
                ORDER BY risk_score DESC, created_at DESC 
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            if row:
                hero_article = {
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'risk_level': row[3],
                    'risk_score': row[4],
                    'source': row[5],
                    'created_at': row[6],
                    'image_url': row[7] if row[7] and 'placeholder' not in row[7] else None,
                    'url': row[8]
                }
                return jsonify(hero_article)
            else:
                return jsonify({'error': 'No hero article found'}), 404
                
    except Exception as e:
        logger.error(f"Error obteniendo artículo hero: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("🚀 Iniciando Simple Test Server para Dashboard de Riesgos Geopolíticos")
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=True)
