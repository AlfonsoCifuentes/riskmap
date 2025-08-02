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
                            a.id, a.title, a.content, a.location, a.country, a.region,
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
                                a.id, a.title, a.content, a.location, a.country, a.region,
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
                        visual_data = self._extract_visual_data(article[14])
                        
                        formatted_article = {
                            'id': article[0],
                            'title': article[1] or 'Sin título',
                            'content': article[2] or 'Sin contenido',
                            'location': article[3] or article[4] or article[5] or 'Global',
                            'country': article[4] or 'Global',
                            'region': article[5] or 'Internacional',
                            'risk': risk_level,
                            'risk_level': risk_level,
                            'risk_score': article[7] or 0.0,
                            'source': article[8] or 'Fuente desconocida',
                            'published_at': article[9],
                            'summary': article[10],
                            'url': article[11],
                            'image': article[12] or f"https://picsum.photos/400/300?random={article[0]}",
                            'mosaic_position': article[13] or position,
                            'size_class': config['size_class'],
                            'visual_data': visual_data,
                            'conflict_probability': article[15] or 0.0,
                            'sentiment_score': article[16] or 0.0
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
                    SELECT id, title, content, location, risk_level, source, 
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
