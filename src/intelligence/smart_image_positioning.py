#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema Inteligente de Posicionamiento de Imágenes
Módulo que implementa lógica avanzada para:
1. Evitar imágenes duplicadas
2. Posicionar inteligentemente en el mosaico basado en análisis CV
3. Buscar imágenes de mejor calidad automáticamente
4. Asignar posiciones optimales según contenido visual
"""

import sqlite3
import json
import hashlib
import requests
import io
import os
import logging
from typing import Dict, List, Tuple, Optional, Union
from PIL import Image
import cv2
import numpy as np
from dotenv import load_dotenv
from pathlib import Path
import imagehash
from urllib.parse import urlparse
import time

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

def get_database_path():
    """Obtener la ruta de la base de datos desde variables de entorno"""
    database_url = os.getenv('DATABASE_URL', 'sqlite:///data/geopolitical_intel.db')
    if database_url.startswith('sqlite:///'):
        return database_url.replace('sqlite:///', '')
    return database_url

class SmartImagePositioning:
    """
    Sistema inteligente para posicionamiento de imágenes en el mosaico
    """
    
    def __init__(self):
        self.db_path = get_database_path()
        
        # Configuraciones del mosaico
        self.mosaic_positions = {
            'hero': {'size': 'large', 'priority': 1, 'quality_threshold': 0.8},
            'featured': {'size': 'medium', 'priority': 2, 'quality_threshold': 0.7},
            'standard': {'size': 'small', 'priority': 3, 'quality_threshold': 0.5},
            'thumbnail': {'size': 'tiny', 'priority': 4, 'quality_threshold': 0.3}
        }
        
        # Configuraciones para detección de similitud
        self.similarity_threshold = 0.85  # Umbral para considerar imágenes similares
        self.hash_size = 16  # Tamaño del hash perceptual
        
        # Configuraciones para búsqueda de mejores imágenes
        self.search_engines = [
            'https://www.google.com/search?q={query}&tbm=isch',
            'https://www.bing.com/images/search?q={query}',
        ]
        
        # Headers para requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        logger.info("🎯 Sistema de posicionamiento inteligente inicializado")
    
    def get_image_fingerprint(self, image_url: str) -> Optional[str]:
        """
        Generar fingerprint único para una imagen usando hash perceptual
        SOLO para imágenes reales (no placeholders)
        """
        try:
            # Validar que NO sea una URL de placeholder
            if not image_url or not isinstance(image_url, str):
                return None
                
            # Excluir explícitamente URLs de placeholder
            placeholder_indicators = [
                'placeholder.com',
                'via.placeholder',
                'picsum.photos',
                '/placeholders/',
                'placeholder_',
                'text=',
                'random='
            ]
            
            url_lower = image_url.lower()
            if any(indicator in url_lower for indicator in placeholder_indicators):
                logger.debug(f"Saltando URL placeholder: {image_url}")
                return None
            
            # Validar que sea una URL válida de imagen
            parsed_url = urlparse(image_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                logger.debug(f"URL inválida: {image_url}")
                return None
            
            # Verificar extensión de imagen
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
            path_lower = parsed_url.path.lower()
            if not any(path_lower.endswith(ext) for ext in valid_extensions):
                # Si no tiene extensión obvia, intentar de todas formas
                pass
            
            # Intentar descargar y procesar la imagen
            response = requests.get(image_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Verificar que la respuesta sea realmente una imagen
            content_type = response.headers.get('content-type', '').lower()
            if not content_type.startswith('image/'):
                logger.debug(f"Contenido no es imagen: {content_type} para {image_url}")
                return None
            
            # Convertir a imagen PIL
            img = Image.open(io.BytesIO(response.content))
            
            # Verificar dimensiones mínimas (evitar imágenes muy pequeñas)
            if img.width < 50 or img.height < 50:
                logger.debug(f"Imagen muy pequeña ({img.width}x{img.height}): {image_url}")
                return None
            
            # Generar hash perceptual
            perceptual_hash = imagehash.phash(img, hash_size=self.hash_size)
            
            logger.debug(f"✅ Fingerprint generado para imagen real: {image_url}")
            return str(perceptual_hash)
            
        except Exception as e:
            logger.warning(f"Error generando fingerprint para {image_url}: {e}")
            return None
    
    def calculate_image_similarity(self, hash1: str, hash2: str) -> float:
        """
        Calcular similitud entre dos hashes perceptuales
        """
        try:
            h1 = imagehash.hex_to_hash(hash1)
            h2 = imagehash.hex_to_hash(hash2)
            
            # Calcular diferencia Hamming
            hamming_distance = h1 - h2
            
            # Convertir a porcentaje de similitud
            max_distance = len(hash1) * 4  # Máxima distancia posible
            similarity = 1.0 - (hamming_distance / max_distance)
            
            return similarity
            
        except Exception as e:
            logger.warning(f"Error calculando similitud: {e}")
            return 0.0
    
    def check_duplicate_images(self) -> List[Dict]:
        """
        Verificar y detectar imágenes duplicadas en la base de datos
        """
        duplicates = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Obtener todas las imágenes REALES con sus hashes (excluir placeholders)
                cursor.execute("""
                    SELECT id, title, image_url, image_fingerprint
                    FROM articles 
                    WHERE image_url IS NOT NULL 
                    AND image_url != ''
                    AND image_url NOT LIKE '%placeholder%'
                    AND image_url NOT LIKE '%via.placeholder%'
                    AND image_url NOT LIKE '%picsum.photos%'
                    AND image_url NOT LIKE '%text=%'
                    AND image_url NOT LIKE '%random=%'
                    AND image_fingerprint IS NOT NULL
                    ORDER BY id DESC
                """)
                
                images = cursor.fetchall()
                
                # Comparar cada imagen con las demás
                for i, img1 in enumerate(images):
                    for j, img2 in enumerate(images[i+1:], i+1):
                        if img1[3] and img2[3]:  # Si ambas tienen fingerprint
                            similarity = self.calculate_image_similarity(img1[3], img2[3])
                            
                            if similarity >= self.similarity_threshold:
                                duplicates.append({
                                    'article1_id': img1[0],
                                    'article1_title': img1[1],
                                    'article1_url': img1[2],
                                    'article2_id': img2[0],
                                    'article2_title': img2[1], 
                                    'article2_url': img2[2],
                                    'similarity': similarity
                                })
                
                logger.info(f"🔍 Detectados {len(duplicates)} pares de imágenes similares")
                return duplicates
                
        except Exception as e:
            logger.error(f"Error verificando duplicados: {e}")
            return []
    
    def resolve_duplicate_images(self, duplicates: List[Dict]) -> Dict:
        """
        Resolver imágenes duplicadas buscando alternativas de mejor calidad
        """
        resolution_results = {
            'resolved': 0,
            'failed': 0,
            'skipped': 0
        }
        
        for duplicate_pair in duplicates:
            try:
                # Determinar cuál imagen mantener (mayor calidad)
                article1_id = duplicate_pair['article1_id']
                article2_id = duplicate_pair['article2_id']
                
                # Obtener calidad de análisis visual de ambas
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        SELECT visual_analysis_json 
                        FROM articles 
                        WHERE id IN (?, ?)
                    """, (article1_id, article2_id))
                    
                    analyses = cursor.fetchall()
                    
                    if len(analyses) == 2:
                        quality1 = self._extract_quality_score(analyses[0][0])
                        quality2 = self._extract_quality_score(analyses[1][0])
                        
                        # Mantener la de mayor calidad, buscar alternativa para la otra
                        if quality1 >= quality2:
                            article_to_replace = article2_id
                            reference_title = duplicate_pair['article2_title']
                        else:
                            article_to_replace = article1_id
                            reference_title = duplicate_pair['article1_title']
                        
                        # Buscar imagen alternativa
                        new_image_url = self.find_alternative_image(reference_title)
                        
                        if new_image_url:
                            # Actualizar en base de datos
                            cursor.execute("""
                                UPDATE articles 
                                SET image_url = ?, image_fingerprint = NULL
                                WHERE id = ?
                            """, (new_image_url, article_to_replace))
                            
                            conn.commit()
                            resolution_results['resolved'] += 1
                            
                            logger.info(f"✅ Resuelto duplicado para artículo {article_to_replace}")
                        else:
                            resolution_results['failed'] += 1
                            logger.warning(f"❌ No se pudo encontrar alternativa para artículo {article_to_replace}")
                    else:
                        resolution_results['skipped'] += 1
                        
            except Exception as e:
                logger.error(f"Error resolviendo duplicado: {e}")
                resolution_results['failed'] += 1
        
        return resolution_results
    
    def _extract_quality_score(self, visual_analysis_json: str) -> float:
        """
        Extraer puntuación de calidad del análisis visual
        """
        try:
            if visual_analysis_json:
                analysis = json.loads(visual_analysis_json)
                return analysis.get('quality_score', 0.0)
        except (json.JSONDecodeError, KeyError):
            pass
        return 0.0
    
    def calculate_optimal_position(self, article_id: int) -> str:
        """
        Calcular la posición óptima en el mosaico basada en análisis CV
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT visual_analysis_json, risk_level, bert_conflict_probability
                    FROM articles 
                    WHERE id = ?
                """, (article_id,))
                
                result = cursor.fetchone()
                if not result:
                    return 'standard'
                
                visual_analysis_json, risk_level, conflict_prob = result
                
                # Analizar datos visuales
                quality_score = 0.0
                has_faces = False
                has_action = False
                resolution_score = 0.0
                
                if visual_analysis_json:
                    try:
                        analysis = json.loads(visual_analysis_json)
                        quality_score = analysis.get('quality_score', 0.0)
                        has_faces = analysis.get('faces_detected', 0) > 0
                        has_action = 'action' in analysis.get('scene_type', '').lower()
                        
                        # Calcular score de resolución basado en dimensiones
                        width = analysis.get('image_width', 0)
                        height = analysis.get('image_height', 0)
                        resolution_score = min(1.0, (width * height) / (1920 * 1080))
                        
                    except (json.JSONDecodeError, KeyError, ValueError):
                        pass
                
                # Calcular score de importancia del contenido
                importance_score = 0.0
                if risk_level == 'high':
                    importance_score = 1.0
                elif risk_level == 'medium':
                    importance_score = 0.7
                elif risk_level == 'low':
                    importance_score = 0.4
                
                if conflict_prob and conflict_prob > 0.7:
                    importance_score = max(importance_score, 0.8)
                
                # Calcular score combinado
                visual_impact_score = (
                    quality_score * 0.3 +
                    resolution_score * 0.3 +
                    importance_score * 0.4
                )
                
                # Bonificaciones
                if has_faces:
                    visual_impact_score += 0.1
                if has_action:
                    visual_impact_score += 0.1
                
                # Determinar posición óptima
                if visual_impact_score >= 0.8 and quality_score >= 0.8:
                    return 'hero'
                elif visual_impact_score >= 0.6 and quality_score >= 0.7:
                    return 'featured'
                elif visual_impact_score >= 0.4 and quality_score >= 0.5:
                    return 'standard'
                else:
                    return 'thumbnail'
                    
        except Exception as e:
            logger.error(f"Error calculando posición óptima para artículo {article_id}: {e}")
            return 'standard'
    
    def find_alternative_image(self, title: str) -> Optional[str]:
        """
        Buscar imagen alternativa de mejor calidad para un artículo
        """
        try:
            # Limpiar título para búsqueda
            search_query = self._clean_title_for_search(title)
            
            # Simular búsqueda de imagen alternativa
            # En implementación real, usaríamos APIs de búsqueda de imágenes
            alternative_sources = [
                f"https://picsum.photos/1200/800?random={hash(search_query) % 1000}",
                f"https://source.unsplash.com/1200x800/?{search_query.replace(' ', ',')}",
                f"https://images.unsplash.com/photo-{abs(hash(search_query)) % 1000000000000}?w=1200&h=800&fit=crop"
            ]
            
            # Probar fuentes alternativas
            for alt_url in alternative_sources:
                try:
                    response = requests.head(alt_url, headers=self.headers, timeout=5)
                    if response.status_code == 200:
                        logger.info(f"🔍 Encontrada imagen alternativa: {alt_url}")
                        return alt_url
                except Exception:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error buscando imagen alternativa: {e}")
            return None
    
    def _clean_title_for_search(self, title: str) -> str:
        """
        Limpiar título para búsqueda de imágenes
        """
        # Remover caracteres especiales y palabras comunes
        import re
        
        # Palabras a remover
        stop_words = ['el', 'la', 'los', 'las', 'de', 'del', 'y', 'o', 'en', 'con', 'por', 'para', 'que', 'se', 'un', 'una']
        
        # Limpiar título
        cleaned = re.sub(r'[^\w\s]', ' ', title.lower())
        words = [word for word in cleaned.split() if word not in stop_words and len(word) > 2]
        
        return ' '.join(words[:5])  # Máximo 5 palabras clave
    
    def update_all_image_fingerprints(self) -> Dict:
        """
        Actualizar fingerprints de todas las imágenes
        """
        results = {
            'processed': 0,
            'updated': 0,
            'failed': 0
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Obtener artículos sin fingerprint o que necesiten actualización
                # EXCLUIR explícitamente URLs de placeholder
                cursor.execute("""
                    SELECT id, image_url 
                    FROM articles 
                    WHERE image_url IS NOT NULL 
                    AND image_url != ''
                    AND image_url NOT LIKE '%placeholder%'
                    AND image_url NOT LIKE '%via.placeholder%'
                    AND image_url NOT LIKE '%picsum.photos%'
                    AND image_url NOT LIKE '%text=%'
                    AND image_url NOT LIKE '%random=%'
                    AND (image_fingerprint IS NULL OR image_fingerprint = '')
                    ORDER BY id DESC
                    LIMIT 100
                """)
                
                articles = cursor.fetchall()
                
                for article_id, image_url in articles:
                    results['processed'] += 1
                    
                    # Generar fingerprint
                    fingerprint = self.get_image_fingerprint(image_url)
                    
                    if fingerprint:
                        # Actualizar en base de datos
                        cursor.execute("""
                            UPDATE articles 
                            SET image_fingerprint = ?
                            WHERE id = ?
                        """, (fingerprint, article_id))
                        
                        results['updated'] += 1
                        logger.info(f"🔐 Fingerprint actualizado para artículo {article_id}")
                    else:
                        results['failed'] += 1
                    
                    # Pequeña pausa para evitar sobrecarga
                    time.sleep(0.1)
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error actualizando fingerprints: {e}")
        
        return results
    
    def assign_mosaic_positions(self) -> Dict:
        """
        Asignar posiciones en el mosaico a todos los artículos basado en análisis CV
        """
        results = {
            'hero': 0,
            'featured': 0,
            'standard': 0,
            'thumbnail': 0,
            'processed': 0
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Obtener todos los artículos con imágenes
                cursor.execute("""
                    SELECT id 
                    FROM articles 
                    WHERE image_url IS NOT NULL 
                    AND image_url != ''
                    ORDER BY id DESC
                """)
                
                article_ids = [row[0] for row in cursor.fetchall()]
                
                for article_id in article_ids:
                    # Calcular posición óptima
                    position = self.calculate_optimal_position(article_id)
                    
                    # Actualizar en base de datos
                    cursor.execute("""
                        UPDATE articles 
                        SET mosaic_position = ?
                        WHERE id = ?
                    """, (position, article_id))
                    
                    results[position] += 1
                    results['processed'] += 1
                    
                    if results['processed'] % 50 == 0:
                        logger.info(f"📍 Procesados {results['processed']} artículos")
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error asignando posiciones del mosaico: {e}")
        
        return results
    
    def get_positioning_statistics(self) -> Dict:
        """
        Obtener estadísticas del posicionamiento actual
        """
        stats = {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Estadísticas de posiciones
                cursor.execute("""
                    SELECT mosaic_position, COUNT(*) 
                    FROM articles 
                    WHERE image_url IS NOT NULL 
                    AND image_url != ''
                    GROUP BY mosaic_position
                """)
                
                position_stats = dict(cursor.fetchall())
                
                # Estadísticas de calidad
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_with_images,
                        COUNT(CASE WHEN image_fingerprint IS NOT NULL THEN 1 END) as with_fingerprints,
                        AVG(CASE WHEN visual_analysis_json IS NOT NULL 
                            THEN json_extract(visual_analysis_json, '$.quality_score') 
                            END) as avg_quality
                    FROM articles 
                    WHERE image_url IS NOT NULL AND image_url != ''
                """)
                
                quality_stats = cursor.fetchone()
                
                stats = {
                    'positions': position_stats,
                    'total_with_images': quality_stats[0] if quality_stats else 0,
                    'with_fingerprints': quality_stats[1] if quality_stats else 0,
                    'average_quality': round(quality_stats[2] or 0, 3),
                    'coverage': {
                        'fingerprints': round((quality_stats[1] / quality_stats[0] * 100) if quality_stats[0] > 0 else 0, 1)
                    }
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            stats = {'error': str(e)}
        
        return stats
    
    def optimize_low_quality_images(self, quality_threshold: float = 0.5) -> Dict:
        """
        Optimizar imágenes de baja calidad buscando alternativas
        """
        results = {
            'identified': 0,
            'improved': 0,
            'failed': 0
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Encontrar imágenes de baja calidad
                cursor.execute("""
                    SELECT id, title, image_url, visual_analysis_json
                    FROM articles 
                    WHERE image_url IS NOT NULL 
                    AND image_url != ''
                    AND visual_analysis_json IS NOT NULL
                    AND json_extract(visual_analysis_json, '$.quality_score') < ?
                    ORDER BY json_extract(visual_analysis_json, '$.quality_score') ASC
                    LIMIT 20
                """, (quality_threshold,))
                
                low_quality_articles = cursor.fetchall()
                results['identified'] = len(low_quality_articles)
                
                for article_id, title, current_url, analysis_json in low_quality_articles:
                    try:
                        # Buscar imagen alternativa
                        alternative_url = self.find_alternative_image(title)
                        
                        if alternative_url and alternative_url != current_url:
                            # Actualizar imagen
                            cursor.execute("""
                                UPDATE articles 
                                SET image_url = ?, 
                                    image_fingerprint = NULL,
                                    visual_analysis_json = NULL
                                WHERE id = ?
                            """, (alternative_url, article_id))
                            
                            results['improved'] += 1
                            logger.info(f"🎨 Mejorada imagen para artículo {article_id}: {title[:50]}...")
                        else:
                            results['failed'] += 1
                            
                    except Exception as e:
                        logger.error(f"Error optimizando imagen para artículo {article_id}: {e}")
                        results['failed'] += 1
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error optimizando imágenes de baja calidad: {e}")
        
        return results

def main():
    """Función principal para pruebas"""
    smart_positioning = SmartImagePositioning()
    
    # Actualizar fingerprints
    logger.info("🔄 Actualizando fingerprints de imágenes...")
    fingerprint_results = smart_positioning.update_all_image_fingerprints()
    logger.info(f"📊 Fingerprints: {fingerprint_results}")
    
    # Verificar duplicados
    logger.info("🔍 Verificando imágenes duplicadas...")
    duplicates = smart_positioning.check_duplicate_images()
    logger.info(f"🔄 Encontrados {len(duplicates)} pares similares")
    
    # Asignar posiciones del mosaico
    logger.info("📍 Asignando posiciones del mosaico...")
    position_results = smart_positioning.assign_mosaic_positions()
    logger.info(f"📊 Posiciones asignadas: {position_results}")
    
    # Obtener estadísticas
    stats = smart_positioning.get_positioning_statistics()
    logger.info(f"📈 Estadísticas: {stats}")

if __name__ == "__main__":
    main()
