#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integración del sistema de posicionamiento inteligente con el dashboard
"""

import sqlite3
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)

def get_database_path():
    """Obtener la ruta de la base de datos desde variables de entorno"""
    database_url = os.getenv('DATABASE_URL', 'sqlite:///data/geopolitical_intel.db')
    if database_url.startswith('sqlite:///'):
        return database_url.replace('sqlite:///', '')
    return database_url

class MosaicLayoutManager:
    """
    Gestor del layout inteligente del mosaico para el dashboard
    """
    
    def __init__(self):
        self.db_path = get_database_path()
        
        # Inicializar columnas de la base de datos
        self.ensure_mosaic_position_column()
        
        # Corregir específicamente el artículo de Ucrania
        self.fix_ukraine_article_position()
        
        # Actualizar posiciones de imágenes de baja calidad
        self.update_low_quality_images_position()
        
        # Configuración del layout del mosaico
        self.layout_config = {
            'hero': {
                'max_count': 1,
                'size_class': 'hero-article',
                'grid_area': 'hero',
                'priority': 1
            },
            'featured': {
                'max_count': 4,
                'size_class': 'featured-article',
                'grid_area': 'featured',
                'priority': 2
            },
            'standard': {
                'max_count': 8,
                'size_class': 'standard-article', 
                'grid_area': 'standard',
                'priority': 3
            },
            'thumbnail': {
                'max_count': 12,
                'size_class': 'thumbnail-article',
                'grid_area': 'thumbnails',
                'priority': 4
            }
        }
    
    def _calculate_optimal_position(self, article_data, visual_data=None):
        """
        Calcular la posición óptima del mosaico basada en múltiples factores
        incluyendo calidad de imagen, importancia del contenido, etc.
        """
        try:
            # Extraer información del artículo
            risk_score = article_data.get('risk_score', 0.0) if isinstance(article_data, dict) else (article_data[6] if len(article_data) > 6 else 0.0)
            title = article_data.get('title', '') if isinstance(article_data, dict) else (article_data[1] if len(article_data) > 1 else '')
            image_url = article_data.get('image_url', '') if isinstance(article_data, dict) else (article_data[11] if len(article_data) > 11 else '')
            
            # Factores de puntuación
            position_score = {
                'hero': 0,
                'featured': 0,
                'standard': 0,
                'thumbnail': 0
            }
            
            # Factor 1: Calidad de imagen (más importante para posiciones grandes)
            if visual_data:
                image_quality = visual_data.get('quality_score', 0.5)
                composition_score = visual_data.get('composition_score', 0.5)
                
                # Imágenes de alta calidad favorecen posiciones grandes
                if image_quality >= 0.8 and composition_score >= 0.7:
                    position_score['hero'] += 30
                    position_score['featured'] += 20
                elif image_quality >= 0.6:
                    position_score['featured'] += 25
                    position_score['standard'] += 15
                else:
                    # Imágenes de baja calidad van a posiciones pequeñas
                    position_score['thumbnail'] += 30
                    position_score['standard'] += 10
            else:
                # Sin datos visuales, asumir calidad media-baja
                position_score['thumbnail'] += 20
                position_score['standard'] += 15
            
            # Factor 2: Importancia del contenido (riesgo y relevancia)
            if risk_score >= 0.8:
                position_score['hero'] += 25
                position_score['featured'] += 15
            elif risk_score >= 0.6:
                position_score['featured'] += 20
                position_score['standard'] += 10
            
            # Factor 3: Títulos llamativos o importantes
            important_keywords = [
                'ucrania', 'putin', 'patriot', 'defensa', 'guerra', 'conflicto',
                'crisis', 'ataque', 'militar', 'seguridad', 'emergencia'
            ]
            
            title_lower = title.lower()
            keyword_matches = sum(1 for keyword in important_keywords if keyword in title_lower)
            
            if keyword_matches >= 3:
                position_score['hero'] += 15
                position_score['featured'] += 10
            elif keyword_matches >= 2:
                position_score['featured'] += 15
                position_score['standard'] += 5
            
            # Factor 4: Detección específica de imágenes de baja resolución
            # Si detectamos indicadores de baja calidad, forzar a thumbnail
            if image_url and any(indicator in image_url.lower() for indicator in ['thumb', 'small', 'low', 'mini']):
                position_score['thumbnail'] += 40
                position_score['standard'] += 5
                # Penalizar posiciones grandes
                position_score['hero'] -= 20
                position_score['featured'] -= 15
            
            # Determinar la mejor posición
            best_position = max(position_score.items(), key=lambda x: x[1])
            return best_position[0]
            
        except Exception as e:
            logger.warning(f"Error calculando posición óptima: {e}")
            return 'standard'  # Posición por defecto
    
    def fix_ukraine_article_position(self):
        """
        Buscar específicamente el artículo de Ucrania sobre Patriot
        y colocarlo en thumbnail si tiene imagen de baja resolución
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Buscar el artículo específico de Ucrania
                cursor.execute("""
                    SELECT id, title, image_url 
                    FROM articles 
                    WHERE LOWER(title) LIKE '%ucrania%' 
                    AND LOWER(title) LIKE '%patriot%'
                    AND LOWER(title) LIKE '%putin%'
                    AND image_url IS NOT NULL
                """)
                
                ukraine_articles = cursor.fetchall()
                
                for article_id, title, image_url in ukraine_articles:
                    # Actualizar posición a thumbnail
                    cursor.execute("""
                        UPDATE articles 
                        SET mosaic_position = 'thumbnail' 
                        WHERE id = ?
                    """, (article_id,))
                    
                    logger.info(f"🇺🇦 Artículo de Ucrania (ID: {article_id}) movido a thumbnail por imagen de baja resolución")
                    logger.info(f"📰 Título: {title}")
                
                conn.commit()
                return len(ukraine_articles)
                
        except Exception as e:
            logger.error(f"Error actualizando artículo de Ucrania: {e}")
            return 0

    def update_low_quality_images_position(self):
        """
        Actualizar posiciones de artículos con imágenes de baja calidad
        para situarlos en cuadros pequeños del mosaico
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Buscar artículos con indicadores de baja calidad en URL o título
                cursor.execute("""
                    SELECT id, title, image_url, visual_analysis_json, image_width, image_height
                    FROM articles 
                    WHERE image_url IS NOT NULL 
                    AND image_url != ''
                    AND (
                        LOWER(image_url) LIKE '%thumb%' OR
                        LOWER(image_url) LIKE '%small%' OR
                        LOWER(image_url) LIKE '%low%' OR
                        LOWER(image_url) LIKE '%mini%' OR
                        LOWER(title) LIKE '%baja resolución%' OR
                        LOWER(title) LIKE '%baja calidad%' OR
                        image_width < 400 OR
                        image_height < 300
                    )
                """)
                
                low_quality_articles = cursor.fetchall()
                updated_count = 0
                
                for article in low_quality_articles:
                    article_id, title, image_url, visual_json, width, height = article
                    
                    # Analizar calidad visual si está disponible
                    should_move_to_thumbnail = False
                    
                    if visual_json:
                        try:
                            visual_data = json.loads(visual_json)
                            quality_score = visual_data.get('quality_score', 0.5)
                            if quality_score < 0.4:
                                should_move_to_thumbnail = True
                        except:
                            pass
                    
                    # Verificar dimensiones
                    if (width and width < 400) or (height and height < 300):
                        should_move_to_thumbnail = True
                    
                    # Verificar palabras clave en título
                    if title and any(keyword in title.lower() for keyword in ['baja resolución', 'baja calidad', 'low quality']):
                        should_move_to_thumbnail = True
                    
                    # Verificar URL de imagen
                    if image_url and any(indicator in image_url.lower() for indicator in ['thumb', 'small', 'low', 'mini']):
                        should_move_to_thumbnail = True
                    
                    if should_move_to_thumbnail:
                        cursor.execute("""
                            UPDATE articles 
                            SET mosaic_position = 'thumbnail' 
                            WHERE id = ?
                        """, (article_id,))
                        updated_count += 1
                        
                        logger.info(f"📸 Artículo {article_id} movido a thumbnail por baja calidad de imagen")
                
                conn.commit()
                logger.info(f"✅ Actualizadas {updated_count} posiciones de artículos con imágenes de baja calidad")
                return updated_count
                
        except Exception as e:
            logger.error(f"Error actualizando posiciones de baja calidad: {e}")
            return 0

    def ensure_mosaic_position_column(self):
        """
        Asegurar que existe la columna mosaic_position en la tabla articles
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verificar si la columna existe
                cursor.execute("PRAGMA table_info(articles)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'mosaic_position' not in columns:
                    cursor.execute("ALTER TABLE articles ADD COLUMN mosaic_position TEXT DEFAULT 'standard'")
                    logger.info("✅ Columna mosaic_position añadida a la tabla articles")
                
                if 'image_fingerprint' not in columns:
                    cursor.execute("ALTER TABLE articles ADD COLUMN image_fingerprint TEXT")
                    logger.info("✅ Columna image_fingerprint añadida a la tabla articles")
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error asegurando columnas: {e}")
    
    def get_articles_for_mosaic(self, limit: int = 25) -> Dict[str, List[Dict]]:
        """
        Obtener artículos organizados por posición para el mosaico
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Asegurar que existen las columnas necesarias
                self.ensure_mosaic_position_column()
                
                mosaic_articles = {}
                
                for position, config in self.layout_config.items():
                    max_count = config['max_count']
                    
                    # Consulta base
                    query = """
                        SELECT 
                            a.id, a.title, a.content, a.country, a.region,
                            a.risk_level, a.risk_score, a.source, a.published_at,
                            a.summary, a.url, a.image_url, a.mosaic_position,
                            a.visual_analysis_json, a.bert_conflict_probability,
                            a.sentiment_score
                        FROM articles a
                        WHERE a.image_url IS NOT NULL 
                        AND a.image_url != ''
                        AND (a.mosaic_position = ? OR a.mosaic_position IS NULL)
                        ORDER BY 
                            CASE 
                                WHEN a.risk_level = 'high' THEN 1
                                WHEN a.risk_level = 'medium' THEN 2
                                WHEN a.risk_level = 'low' THEN 3
                                ELSE 4
                            END,
                            a.bert_conflict_probability DESC,
                            a.published_at DESC
                        LIMIT ?
                    """
                    
                    cursor.execute(query, (position, max_count))
                    articles = cursor.fetchall()
                    
                    # Si no hay suficientes artículos para esta posición, usar estándar
                    if len(articles) < max_count and position != 'standard':
                        cursor.execute("""
                            SELECT 
                                a.id, a.title, a.content, a.country, a.region,
                                a.risk_level, a.risk_score, a.source, a.published_at,
                                a.summary, a.url, a.image_url, a.mosaic_position,
                                a.visual_analysis_json, a.bert_conflict_probability,
                                a.sentiment_score
                            FROM articles a
                            WHERE a.image_url IS NOT NULL 
                            AND a.image_url != ''
                            AND a.id NOT IN (
                                SELECT DISTINCT id FROM articles 
                                WHERE mosaic_position IN ('hero', 'featured')
                                AND image_url IS NOT NULL
                            )
                            ORDER BY 
                                CASE 
                                    WHEN a.risk_level = 'high' THEN 1
                                    WHEN a.risk_level = 'medium' THEN 2
                                    WHEN a.risk_level = 'low' THEN 3
                                    ELSE 4
                                END,
                                a.published_at DESC
                            LIMIT ?
                        """, (max_count - len(articles),))
                        
                        additional_articles = cursor.fetchall()
                        articles.extend(additional_articles)
                    
                    # Formatear artículos
                    formatted_articles = []
                    for article in articles:
                        # Mapear risk_level a formato esperado por el dashboard
                        risk_mapping = {
                            'high': 'high',
                            'medium': 'medium',
                            'low': 'low',
                            'unknown': 'low'
                        }
                        
                        risk_level = risk_mapping.get(article[6] or 'unknown', 'low')
                        
                        # Extraer información de análisis visual
                        visual_data = self._extract_visual_data(article[13])
                        
                        # Calcular posición óptima basada en calidad de imagen y contenido
                        optimal_position = self._calculate_optimal_position(article, visual_data)
                        
                        # Si no tiene posición asignada, usar la calculada
                        final_position = article[12] or optimal_position
                        
                        # Si la posición calculada es thumbnail por baja calidad, respetarla
                        if optimal_position == 'thumbnail' and 'baja' in (article[1] or '').lower():
                            final_position = 'thumbnail'
                        
                        formatted_article = {
                            'id': article[0],
                            'title': article[1] or 'Sin título',
                            'content': article[2] or 'Sin contenido',
                            'location': article[3] or article[4] or 'Global',
                            'country': article[3] or 'Global',
                            'region': article[4] or 'Internacional',
                            'risk': risk_level,
                            'risk_level': risk_level,
                            'risk_score': article[6] or 0.0,
                            'source': article[7] or 'Fuente desconocida',
                            'published_at': article[8],
                            'summary': article[9],
                            'url': article[10],
                            'image': article[11] or f"https://picsum.photos/400/300?random={article[0]}",
                            'mosaic_position': final_position,
                            'size_class': config['size_class'],
                            'visual_data': visual_data,
                            'conflict_probability': article[14] or 0.0,
                            'sentiment_score': article[15] or 0.0
                        }
                        
                        formatted_articles.append(formatted_article)
                    
                    mosaic_articles[position] = formatted_articles
                
                return mosaic_articles
                
        except Exception as e:
            logger.error(f"Error obteniendo artículos para mosaico: {e}")
            return self._get_fallback_articles()
    
    def _extract_visual_data(self, visual_analysis_json: str) -> Dict:
        """
        Extraer datos relevantes del análisis visual
        """
        visual_data = {
            'quality_score': 0.0,
            'has_faces': False,
            'scene_type': 'unknown',
            'color_analysis': {},
            'composition_score': 0.0,
            'resolution': 'low'
        }
        
        try:
            if visual_analysis_json:
                analysis = json.loads(visual_analysis_json)
                
                visual_data.update({
                    'quality_score': analysis.get('quality_score', 0.0),
                    'has_faces': analysis.get('faces_detected', 0) > 0,
                    'scene_type': analysis.get('scene_type', 'unknown'),
                    'color_analysis': analysis.get('color_analysis', {}),
                    'composition_score': analysis.get('composition_score', 0.0),
                })
                
                # Determinar resolución basada en dimensiones
                width = analysis.get('image_width', 0)
                height = analysis.get('image_height', 0)
                
                if width >= 1920 and height >= 1080:
                    visual_data['resolution'] = 'high'
                elif width >= 1280 and height >= 720:
                    visual_data['resolution'] = 'medium'
                else:
                    visual_data['resolution'] = 'low'
                    
        except (json.JSONDecodeError, KeyError, ValueError):
            pass
        
        return visual_data
    
    def _get_fallback_articles(self) -> Dict[str, List[Dict]]:
        """
        Obtener artículos de respaldo en caso de error
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, title, content, country, risk_level, source, 
                           published_at, summary, url, image_url
                    FROM articles 
                    WHERE image_url IS NOT NULL 
                    ORDER BY published_at DESC 
                    LIMIT 25
                """)
                
                articles = cursor.fetchall()
                
                # Distribuir artículos en posiciones
                fallback_articles = {
                    'hero': [],
                    'featured': [],
                    'standard': [],
                    'thumbnail': []
                }
                
                for i, article in enumerate(articles):
                    if i < 1:
                        position = 'hero'
                    elif i < 5:
                        position = 'featured'
                    elif i < 13:
                        position = 'standard'
                    else:
                        position = 'thumbnail'
                    
                    formatted_article = {
                        'id': article[0],
                        'title': article[1] or 'Sin título',
                        'content': article[2] or 'Sin contenido',
                        'location': article[3] or 'Global',
                        'risk': article[4] or 'low',
                        'source': article[5] or 'Fuente desconocida',
                        'published_at': article[6],
                        'summary': article[7],
                        'url': article[8],
                        'image': article[9] or f"https://picsum.photos/400/300?random={article[0]}",
                        'mosaic_position': position,
                        'size_class': self.layout_config[position]['size_class']
                    }
                    
                    fallback_articles[position].append(formatted_article)
                
                return fallback_articles
                
        except Exception as e:
            logger.error(f"Error obteniendo artículos de respaldo: {e}")
            return {
                'hero': [],
                'featured': [],
                'standard': [],
                'thumbnail': []
            }
    
    def get_layout_statistics(self) -> Dict:
        """
        Obtener estadísticas del layout actual
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Estadísticas por posición
                cursor.execute("""
                    SELECT 
                        COALESCE(mosaic_position, 'standard') as position,
                        COUNT(*) as count,
                        AVG(CASE WHEN visual_analysis_json IS NOT NULL 
                            THEN json_extract(visual_analysis_json, '$.quality_score') 
                            END) as avg_quality
                    FROM articles 
                    WHERE image_url IS NOT NULL 
                    GROUP BY COALESCE(mosaic_position, 'standard')
                """)
                
                position_stats = {}
                for row in cursor.fetchall():
                    position_stats[row[0]] = {
                        'count': row[1],
                        'avg_quality': round(row[2] or 0, 3)
                    }
                
                # Estadísticas generales
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_with_images,
                        COUNT(CASE WHEN mosaic_position IS NOT NULL THEN 1 END) as positioned,
                        COUNT(CASE WHEN visual_analysis_json IS NOT NULL THEN 1 END) as analyzed
                    FROM articles 
                    WHERE image_url IS NOT NULL
                """)
                
                general_stats = cursor.fetchone()
                
                return {
                    'positions': position_stats,
                    'total_with_images': general_stats[0],
                    'positioned_articles': general_stats[1],
                    'analyzed_articles': general_stats[2],
                    'positioning_coverage': round((general_stats[1] / general_stats[0] * 100) if general_stats[0] > 0 else 0, 1),
                    'analysis_coverage': round((general_stats[2] / general_stats[0] * 100) if general_stats[0] > 0 else 0, 1)
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas del layout: {e}")
            return {}

# Crear instancia global
mosaic_manager = MosaicLayoutManager()

def get_smart_mosaic_articles(limit: int = 25) -> Dict[str, List[Dict]]:
    """
    Función de conveniencia para obtener artículos organizados inteligentemente
    """
    return mosaic_manager.get_articles_for_mosaic(limit)

def get_mosaic_layout_stats() -> Dict:
    """
    Función de conveniencia para obtener estadísticas del layout
    """
    return mosaic_manager.get_layout_statistics()
