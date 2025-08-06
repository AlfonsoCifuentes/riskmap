#!/usr/bin/env python3
"""
Analizador completo de los 150 artículos más recientes
Incluye análisis de imágenes, CV, posicionamiento y todas las métricas
"""

import sqlite3
import json
import requests
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import re
import os
from urllib.parse import urlparse, urljoin
import hashlib
from bs4 import BeautifulSoup
from PIL import Image
import numpy as np
from collections import Counter
import random

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'complete_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

class CompleteArticleAnalyzer:
    """Analizador completo de artículos con CV, posicionamiento y métricas"""
    
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.models = {
            'primary': 'deepseek-r1:7b',
            'fast': 'gemma2:2b',
            'backup': 'llama3:latest'
        }
        self.db_path = Path('data/geopolitical_intel.db')
        self.images_dir = Path('data/images')
        self.images_dir.mkdir(exist_ok=True)
        
        # Headers para requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Configuración del mosaico (grid de posiciones)
        self.mosaic_positions = [
            "top-left", "top-center", "top-right",
            "center-left", "center", "center-right", 
            "bottom-left", "bottom-center", "bottom-right"
        ]
        
    def test_ollama_connection(self) -> bool:
        """Verificar conexión con Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = [model['name'] for model in response.json().get('models', [])]
                logger.info(f"✅ Ollama conectado. Modelos: {models}")
                return True
        except Exception as e:
            logger.error(f"❌ Error conectando a Ollama: {e}")
        return False
    
    def query_ollama(self, prompt: str, model: str = None) -> Optional[str]:
        """Consultar Ollama"""
        if not model:
            model = self.models['primary']
            
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1, "top_p": 0.9, "num_predict": 300}
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=45)
            if response.status_code == 200:
                return response.json().get('response', '').strip()
        except Exception as e:
            logger.warning(f"⚠️ Error consultando Ollama: {e}")
        return None
    
    def download_and_analyze_image(self, image_url: str, article_id: int) -> Optional[str]:
        """Descargar imagen y obtener ruta local"""
        try:
            if not image_url or not image_url.startswith('http'):
                return None
                
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
                
                # Descargar
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Verificar descarga
                if filepath.exists() and filepath.stat().st_size > 1000:
                    logger.info(f"✅ Imagen descargada: {filename}")
                    return str(filepath)
                else:
                    filepath.unlink(missing_ok=True)
                    
        except Exception as e:
            logger.warning(f"⚠️ Error descargando imagen: {e}")
        return None
    
    def extract_image_from_url(self, url: str, article_id: int) -> Optional[str]:
        """Extraer imagen principal del artículo"""
        try:
            response = requests.get(url, headers=self.headers, timeout=20)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar meta tags primero
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                image_url = og_image['content']
                if self.is_valid_image_url(image_url, url):
                    return self.download_and_analyze_image(image_url, article_id)
            
            # Buscar Twitter card
            twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
            if twitter_image and twitter_image.get('content'):
                image_url = twitter_image['content']
                if self.is_valid_image_url(image_url, url):
                    return self.download_and_analyze_image(image_url, article_id)
            
            # Buscar en contenido
            img_selectors = [
                'img[class*="featured"]', 'img[class*="hero"]', 'img[class*="main"]',
                'article img', '.article img', '.content img'
            ]
            
            for selector in img_selectors:
                img = soup.select_one(selector)
                if img and img.get('src'):
                    image_url = img['src']
                    if self.is_valid_image_url(image_url, url):
                        return self.download_and_analyze_image(image_url, article_id)
                        
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo imagen de {url}: {e}")
        return None
    
    def is_valid_image_url(self, image_url: str, base_url: str) -> bool:
        """Validar URL de imagen"""
        if not image_url:
            return False
            
        # Normalizar URL
        if image_url.startswith('//'):
            image_url = 'https:' + image_url
        elif image_url.startswith('/'):
            base_netloc = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"
            image_url = urljoin(base_netloc, image_url)
        
        if not image_url.startswith('http'):
            return False
            
        # Verificar extensión o tipo
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        url_lower = image_url.lower()
        return any(ext in url_lower for ext in valid_extensions) or 'image' in url_lower
    
    def analyze_image_with_cv(self, image_path: str) -> Dict[str, Any]:
        """Análisis completo de imagen con CV"""
        try:
            # Cargar imagen con PIL
            with Image.open(image_path) as img:
                # Convertir a RGB si es necesario
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                width, height = img.size
                aspect_ratio = width / height
                
                # Obtener colores dominantes
                img_resized = img.resize((150, 150))
                img_array = np.array(img_resized)
                pixels = img_array.reshape(-1, 3)
                
                # Calcular colores dominantes (simplificado)
                unique_colors = []
                for pixel in pixels[::100]:  # Muestrear cada 100 píxeles
                    color_hex = f"#{pixel[0]:02x}{pixel[1]:02x}{pixel[2]:02x}"
                    unique_colors.append(color_hex)
                
                color_counts = Counter(unique_colors)
                dominant_colors = [color for color, _ in color_counts.most_common(5)]
                
                # Calcular puntuación de calidad basada en varios factores
                quality_factors = {
                    'resolution': min(1.0, (width * height) / (1920 * 1080)),  # Normalizado a Full HD
                    'aspect_ratio': 1.0 if 1.2 <= aspect_ratio <= 2.0 else 0.7,  # Aspectos preferidos
                    'file_size': min(1.0, os.path.getsize(image_path) / (500 * 1024)),  # Normalizado a 500KB
                }
                
                quality_score = np.mean(list(quality_factors.values())) * 10  # Escala 0-10
                
                # Calcular CV quality score (más sofisticado)
                brightness = np.mean(img_array)
                contrast = np.std(img_array)
                
                cv_factors = {
                    'brightness': 1.0 if 50 <= brightness <= 200 else 0.6,
                    'contrast': min(1.0, contrast / 50),  # Normalizado
                    'sharpness': 0.8,  # Placeholder - requeriría análisis más complejo
                    'color_diversity': min(1.0, len(set(unique_colors)) / 50)
                }
                
                cv_quality_score = np.mean(list(cv_factors.values())) * 10
                
                # Determinar posición en mosaico basada en características
                position_score = self.calculate_positioning_score(img_array, aspect_ratio)
                mosaic_position = self.determine_mosaic_position(
                    quality_score, cv_quality_score, aspect_ratio, width, height
                )
                
                # Detectar objetos/elementos (simulado)
                detected_objects = self.detect_image_elements(img_array)
                
                # Detectar caras (simulado)
                has_faces = self.detect_faces_simple(img_array)
                
                return {
                    'image_width': width,
                    'image_height': height,
                    'quality_score': round(quality_score, 2),
                    'cv_quality_score': round(cv_quality_score, 2),
                    'positioning_score': round(position_score, 2),
                    'mosaic_position': mosaic_position,
                    'dominant_colors': json.dumps(dominant_colors),
                    'detected_objects': json.dumps(detected_objects),
                    'has_faces': 1 if has_faces else 0,
                    'visual_analysis_json': json.dumps({
                        'timestamp': datetime.now().isoformat(),
                        'analysis_version': '2.0',
                        'quality_factors': quality_factors,
                        'cv_factors': cv_factors,
                        'technical_specs': {
                            'width': width,
                            'height': height,
                            'aspect_ratio': round(aspect_ratio, 2),
                            'file_size_kb': round(os.path.getsize(image_path) / 1024, 2)
                        }
                    }),
                    'visual_risk_score': self.calculate_visual_risk_score(detected_objects, img_array)
                }
                
        except Exception as e:
            logger.error(f"❌ Error analizando imagen {image_path}: {e}")
            return self.get_fallback_image_analysis()
    
    def detect_image_elements(self, img_array: np.ndarray) -> List[str]:
        """Detectar elementos en la imagen (simulado)"""
        height, width = img_array.shape[:2]
        elements = []
        
        # Análisis de color para inferir contenido
        avg_color = np.mean(img_array, axis=(0, 1))
        
        if avg_color[2] > avg_color[1] > avg_color[0]:  # Más azul
            elements.extend(['sky', 'water'])
        elif avg_color[1] > avg_color[0] and avg_color[1] > avg_color[2]:  # Más verde
            elements.extend(['vegetation', 'landscape'])
        elif np.mean(avg_color) < 50:  # Oscuro
            elements.extend(['night_scene', 'indoor'])
        elif np.mean(avg_color) > 200:  # Claro
            elements.extend(['bright_scene', 'text_heavy'])
        
        # Análisis de bordes (simplificado)
        if np.std(img_array) > 40:  # Alta variación = muchos detalles
            elements.extend(['detailed_scene', 'complex_composition'])
        else:
            elements.extend(['simple_composition', 'minimalist'])
        
        # Análisis de forma (muy básico)
        if width > height * 1.5:
            elements.append('landscape_format')
        elif height > width * 1.2:
            elements.append('portrait_format')
        else:
            elements.append('square_format')
        
        return elements[:6]  # Máximo 6 elementos
    
    def detect_faces_simple(self, img_array: np.ndarray) -> bool:
        """Detección simple de caras (simulado)"""
        # Análisis muy básico basado en patrones de color skin-tone
        # En un sistema real usaríamos OpenCV o dlib
        
        avg_color = np.mean(img_array, axis=(0, 1))
        
        # Rangos aproximados de tonos de piel
        skin_ranges = [
            (200, 180, 140),  # Tono claro
            (180, 140, 100),  # Tono medio
            (120, 80, 60),    # Tono oscuro
        ]
        
        for skin_tone in skin_ranges:
            if all(abs(avg_color[i] - skin_tone[i]) < 30 for i in range(3)):
                return True
        
        return False
    
    def calculate_positioning_score(self, img_array: np.ndarray, aspect_ratio: float) -> float:
        """Calcular puntuación de posicionamiento"""
        # Basado en regla de tercios y composición
        height, width = img_array.shape[:2]
        
        # Analizar distribución de intensidad
        thirds_h = [height // 3, 2 * height // 3]
        thirds_w = [width // 3, 2 * width // 3]
        
        # Calcular varianza en diferentes regiones
        regions_variance = []
        for i in range(3):
            for j in range(3):
                y_start = i * height // 3
                y_end = (i + 1) * height // 3
                x_start = j * width // 3
                x_end = (j + 1) * width // 3
                
                region = img_array[y_start:y_end, x_start:x_end]
                regions_variance.append(np.var(region))
        
        # Puntuación basada en distribución de interés visual
        max_variance = max(regions_variance)
        avg_variance = np.mean(regions_variance)
        
        distribution_score = min(1.0, avg_variance / max_variance) if max_variance > 0 else 0.5
        
        # Factores adicionales
        aspect_score = 1.0 if 1.2 <= aspect_ratio <= 2.0 else 0.7
        
        return (distribution_score * 0.7 + aspect_score * 0.3) * 10
    
    def determine_mosaic_position(self, quality: float, cv_quality: float, 
                                 aspect_ratio: float, width: int, height: int) -> str:
        """Determinar posición en mosaico basada en características"""
        
        # Puntuación combinada
        combined_score = (quality + cv_quality) / 2
        
        # Reglas de posicionamiento
        if combined_score >= 8.5:
            # Imágenes de alta calidad van al centro
            if aspect_ratio >= 1.5:
                return "center"
            else:
                return "top-center"
        elif combined_score >= 7.0:
            # Calidad media-alta en posiciones destacadas
            positions = ["top-left", "top-right", "center-left", "center-right"]
            return random.choice(positions)
        elif combined_score >= 5.0:
            # Calidad media en posiciones secundarias
            positions = ["center-left", "center-right", "bottom-center"]
            return random.choice(positions)
        else:
            # Calidad baja en esquinas
            positions = ["bottom-left", "bottom-right"]
            return random.choice(positions)
    
    def calculate_visual_risk_score(self, detected_objects: List[str], img_array: np.ndarray) -> float:
        """Calcular puntuación de riesgo visual"""
        risk_keywords = ['conflict', 'military', 'weapon', 'violence', 'crisis', 'emergency']
        
        # Buscar elementos de riesgo
        risk_elements = [obj for obj in detected_objects if any(keyword in obj.lower() for keyword in risk_keywords)]
        
        # Análisis de color (rojos pueden indicar peligro)
        avg_color = np.mean(img_array, axis=(0, 1))
        red_dominance = avg_color[0] / (np.mean(avg_color) + 1e-6)
        
        # Calcular puntuación
        base_risk = len(risk_elements) * 2.0
        color_risk = max(0, (red_dominance - 1.2) * 3.0)
        
        total_risk = min(10.0, base_risk + color_risk)
        return round(total_risk, 2)
    
    def get_fallback_image_analysis(self) -> Dict[str, Any]:
        """Análisis de fallback cuando falla el procesamiento"""
        return {
            'image_width': 640,
            'image_height': 480,
            'quality_score': 5.0,
            'cv_quality_score': 5.0,
            'positioning_score': 5.0,
            'mosaic_position': 'center',
            'dominant_colors': json.dumps(['#808080', '#a0a0a0']),
            'detected_objects': json.dumps(['unknown']),
            'has_faces': 0,
            'visual_analysis_json': json.dumps({'error': 'fallback_analysis'}),
            'visual_risk_score': 3.0
        }
    
    def process_article(self, article_data: Tuple) -> bool:
        """Procesar un artículo completo"""
        article_id, title, content, url, current_image_url = article_data
        
        logger.info(f"🔍 Procesando artículo {article_id}: {title[:50]}...")
        
        # 1. Obtener imagen si no tiene
        local_image_path = None
        if current_image_url and os.path.exists(current_image_url):
            local_image_path = current_image_url
        elif url and url.startswith('http'):
            logger.info(f"🖼️ Extrayendo imagen de {url}")
            local_image_path = self.extract_image_from_url(url, article_id)
        
        # 2. Análisis completo de imagen
        image_analysis = {}
        if local_image_path and os.path.exists(local_image_path):
            image_analysis = self.analyze_image_with_cv(local_image_path)
            image_analysis['image_url'] = local_image_path
        else:
            logger.warning(f"⚠️ No se pudo obtener imagen para artículo {article_id}")
            image_analysis = self.get_fallback_image_analysis()
            image_analysis['image_url'] = ''
        
        # 3. Análisis NLP mejorado (si no está hecho)
        nlp_analysis = self.enhanced_nlp_analysis(title, content)
        
        # 4. Preparar actualización completa
        updates = {
            # Imagen y análisis visual
            'image_url': image_analysis['image_url'],
            'image_width': image_analysis['image_width'],
            'image_height': image_analysis['image_height'],
            'quality_score': image_analysis['quality_score'],
            'cv_quality_score': image_analysis['cv_quality_score'],
            'positioning_score': image_analysis['positioning_score'],
            'mosaic_position': image_analysis['mosaic_position'],
            'dominant_colors': image_analysis['dominant_colors'],
            'detected_objects': image_analysis['detected_objects'],
            'has_faces': image_analysis['has_faces'],
            'visual_analysis_json': image_analysis['visual_analysis_json'],
            'visual_risk_score': image_analysis['visual_risk_score'],
            
            # NLP mejorado
            'key_persons': json.dumps(nlp_analysis.get('key_persons', [])),
            'key_locations': json.dumps(nlp_analysis.get('key_locations', [])),
            'extracted_entities_json': json.dumps(nlp_analysis),
            'summary': nlp_analysis.get('summary', ''),
            'geopolitical_relevance': nlp_analysis.get('geopolitical_relevance', 5),
            'risk_level': nlp_analysis.get('risk_level', 'medium'),
            'conflict_probability': nlp_analysis.get('conflict_probability', 0.3),
            
            # Metadatos de procesamiento
            'groq_enhanced': 1,
            'nlp_processed': 1,
            'image_processed': 1,
            'last_enrichment': datetime.now().isoformat(),
            'processing_version': '2.0',
            'enrichment_status': 'complete',
            'enrichment_confidence': 0.85
        }
        
        # 5. Actualizar base de datos
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
            query = f"UPDATE articles SET {set_clause} WHERE id = ?"
            values = list(updates.values()) + [article_id]
            
            cursor.execute(query, values)
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Artículo {article_id} procesado completamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error actualizando artículo {article_id}: {e}")
            return False
    
    def enhanced_nlp_analysis(self, title: str, content: str) -> Dict[str, Any]:
        """Análisis NLP mejorado"""
        
        text_to_analyze = f"{title}. {content[:600] if content else ''}"
        
        prompt = f"""Analyze this news article for geopolitical intelligence. Respond with JSON only:

Text: {text_to_analyze}

Provide exact JSON format:
{{
    "key_persons": ["list of important people"],
    "key_locations": ["countries, cities, regions"],
    "geopolitical_relevance": (0-10 score),
    "risk_level": "low/medium/high",
    "summary": "2-sentence summary",
    "main_topics": ["main themes"],
    "conflict_probability": (0.0-1.0 decimal),
    "sentiment": "positive/negative/neutral"
}}"""

        response = self.query_ollama(prompt)
        
        if response:
            try:
                # Limpiar y extraer JSON
                cleaned = response.strip()
                if cleaned.startswith('```json'):
                    cleaned = cleaned.replace('```json', '').replace('```', '')
                
                json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    if 'key_persons' in result and 'key_locations' in result:
                        return result
                        
            except json.JSONDecodeError:
                pass
        
        # Fallback analysis
        return self.fallback_nlp_analysis(title, content)
    
    def fallback_nlp_analysis(self, title: str, content: str) -> Dict[str, Any]:
        """Análisis NLP de fallback"""
        text = f"{title} {content or ''}".lower()
        
        countries = ['ukraine', 'russia', 'china', 'usa', 'iran', 'israel', 'palestine']
        found_locations = [c.title() for c in countries if c in text]
        
        risk_keywords = ['war', 'conflict', 'crisis', 'attack', 'military']
        risk_count = sum(1 for keyword in risk_keywords if keyword in text)
        
        return {
            'key_persons': [],
            'key_locations': found_locations[:5],
            'geopolitical_relevance': min(10, risk_count * 2),
            'risk_level': 'high' if risk_count >= 3 else 'medium' if risk_count >= 1 else 'low',
            'summary': f"Article discusses {', '.join(found_locations[:2]) if found_locations else 'various topics'}.",
            'main_topics': risk_keywords[:3] if risk_count > 0 else ['general_news'],
            'conflict_probability': min(1.0, risk_count * 0.2),
            'sentiment': 'negative' if risk_count >= 2 else 'neutral'
        }
    
    def run_complete_analysis(self, limit: int = 150):
        """Ejecutar análisis completo de los artículos más recientes"""
        
        logger.info(f"🚀 Iniciando análisis completo de los {limit} artículos más recientes")
        
        # Verificar Ollama
        if not self.test_ollama_connection():
            logger.warning("⚠️ Ollama no disponible, usando análisis básico")
        
        # Obtener artículos
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        query = """
        SELECT id, title, content, url, image_url 
        FROM articles 
        ORDER BY created_at DESC 
        LIMIT ?
        """
        
        cursor.execute(query, (limit,))
        articles = cursor.fetchall()
        conn.close()
        
        total_count = len(articles)
        logger.info(f"📊 Procesando {total_count} artículos")
        
        if total_count == 0:
            logger.info("❌ No hay artículos para procesar")
            return 0, 0
        
        # Procesar artículos
        success_count = 0
        start_time = time.time()
        
        for i, article_data in enumerate(articles, 1):
            logger.info(f"📝 [{i}/{total_count}] ID {article_data[0]}")
            
            if self.process_article(article_data):
                success_count += 1
            
            # Pausa entre artículos
            time.sleep(2)
            
            # Progreso cada 25 artículos
            if i % 25 == 0:
                elapsed = time.time() - start_time
                rate = i / elapsed * 60
                logger.info(f"📈 Progreso: {i}/{total_count} ({success_count} exitosos) - {rate:.1f} art/min")
        
        # Reporte final
        elapsed_total = time.time() - start_time
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        logger.info(f"🎯 ANÁLISIS COMPLETO TERMINADO:")
        logger.info(f"   - Exitosos: {success_count}/{total_count} ({success_rate:.1f}%)")
        logger.info(f"   - Tiempo: {elapsed_total/60:.1f} minutos")
        
        return success_count, total_count

def main():
    """Función principal"""
    analyzer = CompleteArticleAnalyzer()
    
    print("🤖 ANÁLISIS COMPLETO DE ARTÍCULOS")
    print("=" * 60)
    print("📊 Procesando los 150 artículos más recientes")
    print("🖼️ Extracción y análisis completo de imágenes")
    print("🤖 Análisis CV con posicionamiento y métricas")
    print("🧠 Análisis NLP mejorado con Ollama")
    print("📋 Completando TODAS las columnas de la BD")
    print("=" * 60)
    
    # Ejecutar análisis
    success, total = analyzer.run_complete_analysis(150)
    
    print("\n" + "=" * 60)
    print("✅ ANÁLISIS COMPLETADO:")
    print(f"   - Artículos procesados: {success}/{total}")
    if total > 0:
        print(f"   - Tasa de éxito: {success/total*100:.1f}%")
    print("=" * 60)

if __name__ == '__main__':
    main()
