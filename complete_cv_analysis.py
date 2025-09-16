#!/usr/bin/env python3
"""
Análisis completo de CV para los 150 artículos más recientes con riesgo medio/alto
Incluye: descarga de imágenes, análisis de calidad, posicionamiento y análisis visual completo
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
from PIL import Image, ImageStat
import colorsys
import numpy as np

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'cv_analysis_complete_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

class CompleteImageAnalyzer:
    """Analizador completo de imágenes para artículos de alto riesgo"""
    
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.models = {
            'vision': 'llava:latest',        # Modelo de visión para análisis de imágenes
            'analysis': 'deepseek-r1:7b',    # Modelo para análisis textual
            'fast': 'gemma2:2b'              # Modelo rápido
        }
        self.db_path = Path('data/geopolitical_intel.db')
        self.images_dir = Path('data/images')
        self.images_dir.mkdir(exist_ok=True)
        
        # Headers para requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def test_ollama_connection(self):
        """Verificar que Ollama esté funcionando"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = [model['name'] for model in response.json().get('models', [])]
                logger.info(f"✅ Ollama conectado. Modelos disponibles: {models}")
                return True
            else:
                logger.error(f"❌ Ollama responde pero con error: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ No se puede conectar a Ollama: {e}")
            return False
    
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
            response = requests.get(url, headers=self.headers, timeout=20)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar meta tags de imagen primero
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                image_url = og_image['content']
                if self.is_valid_image_url(image_url, url):
                    result = self.download_image_from_url(image_url, article_id)
                    if result:
                        return result
            
            # Buscar Twitter card
            twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
            if twitter_image and twitter_image.get('content'):
                image_url = twitter_image['content']
                if self.is_valid_image_url(image_url, url):
                    result = self.download_image_from_url(image_url, article_id)
                    if result:
                        return result
            
            # Buscar imágenes en el contenido
            img_selectors = [
                'img[class*="featured"]',
                'img[class*="hero"]',
                'img[class*="main"]',
                'article img',
                '.article img',
                '.content img'
            ]
            
            for selector in img_selectors:
                img = soup.select_one(selector)
                if img and img.get('src'):
                    image_url = img['src']
                    if self.is_valid_image_url(image_url, url):
                        result = self.download_image_from_url(image_url, article_id)
                        if result:
                            return result
            
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo imagen de {url}: {e}")
        
        return None
    
    def is_valid_image_url(self, image_url: str, base_url: str) -> bool:
        """Validar y normalizar URL de imagen"""
        if not image_url:
            return False
            
        # Normalizar URL
        if image_url.startswith('//'):
            image_url = 'https:' + image_url
        elif image_url.startswith('/'):
            base_netloc = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"
            image_url = urljoin(base_netloc, image_url)
        
        # Verificar que sea una URL válida de imagen
        if not image_url.startswith('http'):
            return False
            
        # Verificar extensión
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        url_lower = image_url.lower()
        
        return any(ext in url_lower for ext in valid_extensions) or 'image' in url_lower
    
    def analyze_image_properties(self, image_path: str) -> Dict[str, Any]:
        """Análisis completo de propiedades de la imagen"""
        try:
            with Image.open(image_path) as img:
                # Propiedades básicas
                width, height = img.size
                file_size = os.path.getsize(image_path)
                
                # Convertir a RGB si es necesario
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Análisis de colores dominantes
                colors = img.getcolors(maxcolors=256*256*256)
                if colors:
                    # Obtener los 5 colores más comunes
                    sorted_colors = sorted(colors, key=lambda x: x[0], reverse=True)[:5]
                    dominant_colors = []
                    
                    for count, color in sorted_colors:
                        hex_color = '#{:02x}{:02x}{:02x}'.format(*color)
                        dominant_colors.append({
                            'hex': hex_color,
                            'rgb': color,
                            'percentage': count / (width * height) * 100
                        })
                else:
                    dominant_colors = []
                
                # Calcular puntuación de calidad
                quality_score = self.calculate_quality_score(img, width, height, file_size)
                
                # Calcular puntuación CV
                cv_quality_score = self.calculate_cv_quality_score(img, width, height)
                
                # Determinar posición en mosaico
                mosaic_position = self.determine_mosaic_position(quality_score, cv_quality_score)
                
                # Puntuación de posicionamiento
                positioning_score = self.calculate_positioning_score(img, width, height)
                
                # Análisis visual para riesgo
                visual_risk_score = self.calculate_visual_risk_score(img, dominant_colors)
                
                return {
                    'width': width,
                    'height': height,
                    'file_size_kb': round(file_size / 1024, 2),
                    'dominant_colors': json.dumps(dominant_colors),
                    'quality_score': quality_score,
                    'cv_quality_score': cv_quality_score,
                    'mosaic_position': mosaic_position,
                    'positioning_score': positioning_score,
                    'visual_risk_score': visual_risk_score
                }
                
        except Exception as e:
            logger.warning(f"⚠️ Error analizando imagen {image_path}: {e}")
            return {}
    
    def calculate_quality_score(self, img: Image.Image, width: int, height: int, file_size: int) -> float:
        """Calcular puntuación de calidad de la imagen"""
        score = 0.0
        
        # Resolución (25% del score)
        resolution_score = min((width * height) / (1920 * 1080), 1.0) * 25
        score += resolution_score
        
        # Proporción de aspecto (15% del score)
        aspect_ratio = width / height
        ideal_ratios = [16/9, 4/3, 3/2, 1/1]  # Ratios comunes
        aspect_score = max([15 - abs(aspect_ratio - ratio) * 5 for ratio in ideal_ratios])
        score += max(0, min(15, aspect_score))
        
        # Tamaño de archivo vs resolución (20% del score)
        expected_size = (width * height) * 0.5  # Estimación rough
        size_efficiency = min(file_size / expected_size, 2.0)
        size_score = (2.0 - abs(size_efficiency - 1.0)) * 10
        score += max(0, size_score)
        
        # Análisis estadístico de la imagen (40% del score)
        try:
            # Calcular estadísticas de brillo y contraste
            gray_img = img.convert('L')
            stat = ImageStat.Stat(gray_img)
            
            # Brillo promedio (óptimo entre 100-180)
            brightness = stat.mean[0]
            brightness_score = 20 - abs(brightness - 140) / 140 * 20
            score += max(0, brightness_score)
            
            # Desviación estándar (contraste) - mayor es mejor hasta cierto punto
            contrast = stat.stddev[0]
            contrast_score = min(contrast / 50, 1.0) * 20
            score += contrast_score
            
        except Exception:
            score += 20  # Score neutral si falla el análisis
        
        return round(min(100.0, max(0.0, score)), 2)
    
    def calculate_cv_quality_score(self, img: Image.Image, width: int, height: int) -> float:
        """Calcular puntuación CV específica para análisis computacional"""
        score = 0.0
        
        try:
            # Convertir a array numpy para análisis más avanzado
            img_array = np.array(img)
            
            # Análisis de nitidez usando Laplaciano
            gray = np.mean(img_array, axis=2)
            laplacian_var = np.var(np.gradient(gray))
            sharpness_score = min(laplacian_var / 1000, 1.0) * 30
            score += sharpness_score
            
            # Análisis de rango dinámico
            dynamic_range = np.max(gray) - np.min(gray)
            range_score = (dynamic_range / 255) * 25
            score += range_score
            
            # Análisis de complejidad visual
            unique_colors = len(np.unique(img_array.reshape(-1, img_array.shape[-1]), axis=0))
            complexity_score = min(unique_colors / (width * height * 0.1), 1.0) * 25
            score += complexity_score
            
            # Detección de bordes
            edges = np.abs(np.gradient(gray))
            edge_density = np.mean(edges) / 255
            edge_score = edge_density * 20
            score += edge_score
            
        except Exception:
            score = 50.0  # Score neutral si falla
        
        return round(min(100.0, max(0.0, score)), 2)
    
    def determine_mosaic_position(self, quality_score: float, cv_quality_score: float) -> str:
        """Determinar posición en mosaico basado en scores"""
        avg_score = (quality_score + cv_quality_score) / 2
        
        if avg_score >= 80:
            return "featured"  # Posición destacada
        elif avg_score >= 60:
            return "primary"   # Posición principal
        elif avg_score >= 40:
            return "secondary" # Posición secundaria
        else:
            return "background" # Posición de fondo
    
    def calculate_positioning_score(self, img: Image.Image, width: int, height: int) -> float:
        """Calcular puntuación de posicionamiento para mosaico"""
        try:
            # Análisis de puntos de interés
            img_array = np.array(img.convert('L'))
            
            # Dividir imagen en grid 3x3
            h_third = height // 3
            w_third = width // 3
            
            zones_interest = []
            for i in range(3):
                for j in range(3):
                    zone = img_array[i*h_third:(i+1)*h_third, j*w_third:(j+1)*w_third]
                    # Calcular interés basado en varianza
                    interest = np.var(zone)
                    zones_interest.append(interest)
            
            # Normalizar scores
            max_interest = max(zones_interest) if zones_interest else 1
            normalized_zones = [z / max_interest * 100 for z in zones_interest]
            
            # Las zonas centrales y superiores tienen más peso
            weights = [0.8, 1.2, 0.8, 1.0, 1.5, 1.0, 0.6, 1.0, 0.6]
            weighted_score = sum(z * w for z, w in zip(normalized_zones, weights)) / sum(weights)
            
            return round(min(100.0, max(0.0, weighted_score)), 2)
            
        except Exception:
            return 50.0
    
    def calculate_visual_risk_score(self, img: Image.Image, dominant_colors: List[Dict]) -> float:
        """Calcular puntuación de riesgo visual basado en colores y contenido"""
        try:
            risk_score = 0.0
            
            # Análisis de colores asociados con riesgo
            high_risk_colors = {
                'red': (255, 0, 0),
                'dark_red': (139, 0, 0),
                'orange': (255, 165, 0),
                'black': (0, 0, 0),
                'dark_gray': (64, 64, 64)
            }
            
            for color_info in dominant_colors:
                r, g, b = color_info['rgb']
                percentage = color_info['percentage']
                
                # Calcular distancia a colores de riesgo
                for risk_color_name, (rr, rg, rb) in high_risk_colors.items():
                    distance = ((r-rr)**2 + (g-rg)**2 + (b-rb)**2)**0.5
                    if distance < 100:  # Colores similares
                        risk_score += (100 - distance) / 100 * percentage * 0.3
            
            # Análisis de brillo general (imágenes muy oscuras pueden indicar riesgo)
            gray_img = img.convert('L')
            avg_brightness = np.mean(np.array(gray_img))
            if avg_brightness < 80:  # Imagen oscura
                risk_score += (80 - avg_brightness) / 80 * 20
            
            # Análisis de contraste alto (puede indicar tensión)
            contrast = np.std(np.array(gray_img))
            if contrast > 60:
                risk_score += (contrast - 60) / 60 * 15
            
            return round(min(100.0, max(0.0, risk_score)), 2)
            
        except Exception:
            return 30.0  # Score neutral-medio
    
    def generate_visual_analysis_json(self, image_path: str, analysis_data: Dict) -> str:
        """Generar JSON completo de análisis visual"""
        analysis = {
            "image_properties": {
                "width": analysis_data.get('width', 0),
                "height": analysis_data.get('height', 0),
                "file_size_kb": analysis_data.get('file_size_kb', 0),
                "aspect_ratio": round(analysis_data.get('width', 1) / analysis_data.get('height', 1), 2)
            },
            "quality_analysis": {
                "quality_score": analysis_data.get('quality_score', 0),
                "cv_quality_score": analysis_data.get('cv_quality_score', 0),
                "positioning_score": analysis_data.get('positioning_score', 0)
            },
            "visual_content": {
                "dominant_colors": json.loads(analysis_data.get('dominant_colors', '[]')),
                "visual_risk_score": analysis_data.get('visual_risk_score', 0),
                "mosaic_position": analysis_data.get('mosaic_position', 'background')
            },
            "metadata": {
                "analysis_timestamp": datetime.now().isoformat(),
                "analyzer_version": "1.0",
                "local_path": image_path
            }
        }
        
        return json.dumps(analysis, indent=2)
    
    def analyze_article_complete(self, article_id: int, title: str, url: str, 
                                existing_image: str = None) -> bool:
        """Análisis completo de un artículo"""
        
        logger.info(f"🔍 Analizando artículo {article_id}: {title[:50]}...")
        
        # 1. Obtener imagen si no existe
        local_image_path = existing_image
        if not local_image_path or not os.path.exists(local_image_path):
            if url and url.startswith('http'):
                logger.info(f"🖼️ Descargando imagen para artículo {article_id}")
                local_image_path = self.extract_image_from_article(url, article_id)
            
            if not local_image_path:
                logger.warning(f"⚠️ No se pudo obtener imagen para artículo {article_id}")
                return False
        
        # 2. Análisis completo de la imagen
        logger.info(f"🤖 Analizando propiedades de imagen para artículo {article_id}")
        image_analysis = self.analyze_image_properties(local_image_path)
        
        if not image_analysis:
            logger.warning(f"⚠️ Falló análisis de imagen para artículo {article_id}")
            return False
        
        # 3. Generar análisis visual JSON
        visual_analysis_json = self.generate_visual_analysis_json(local_image_path, image_analysis)
        
        # 4. Preparar actualización completa
        updates = {
            'image_url': local_image_path,
            'image_width': image_analysis.get('width'),
            'image_height': image_analysis.get('height'),
            'dominant_colors': image_analysis.get('dominant_colors'),
            'quality_score': image_analysis.get('quality_score'),
            'cv_quality_score': image_analysis.get('cv_quality_score'),
            'mosaic_position': image_analysis.get('mosaic_position'),
            'positioning_score': image_analysis.get('positioning_score'),
            'visual_risk_score': image_analysis.get('visual_risk_score'),
            'visual_analysis_json': visual_analysis_json,
            'has_faces': 0  # Por defecto, se puede mejorar con detección de caras
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
            
            logger.info(f"✅ Artículo {article_id} completamente analizado")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error actualizando artículo {article_id}: {e}")
            return False
    
    def run_complete_analysis(self, limit: int = 150):
        """Ejecutar análisis completo de los artículos de riesgo medio/alto más recientes"""
        
        logger.info(f"🚀 Iniciando análisis completo de CV para {limit} artículos de riesgo medio/alto")
        
        # Conectar a base de datos
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Obtener los artículos más recientes con riesgo medio/alto
        query = """
        SELECT id, title, url, image_url, quality_score
        FROM articles 
        WHERE risk_level IN ('medium', 'high')
        AND (quality_score IS NULL OR cv_quality_score IS NULL OR mosaic_position IS NULL)
        ORDER BY created_at DESC 
        LIMIT ?
        """
        
        cursor.execute(query, (limit,))
        articles = cursor.fetchall()
        total_count = len(articles)
        
        logger.info(f"📊 Encontrados {total_count} artículos de riesgo medio/alto para analizar")
        
        if total_count == 0:
            logger.info("✅ No hay artículos pendientes de análisis CV")
            conn.close()
            return 0, 0
        
        # Procesar artículos
        success_count = 0
        start_time = time.time()
        
        for i, (article_id, title, url, existing_image, quality_score) in enumerate(articles, 1):
            logger.info(f"📝 [{i}/{total_count}] ID {article_id}")
            
            if self.analyze_article_complete(article_id, title, url, existing_image):
                success_count += 1
            
            # Pausa para no sobrecargar
            time.sleep(2)
            
            # Progreso cada 10 artículos
            if i % 10 == 0:
                elapsed = time.time() - start_time
                rate = i / elapsed * 60  # artículos por minuto
                logger.info(f"📈 Progreso: {i}/{total_count} ({success_count} exitosos) - {rate:.1f} art/min")
        
        conn.close()
        
        # Reporte final
        elapsed_total = time.time() - start_time
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        logger.info(f"🎯 ANÁLISIS CV COMPLETO TERMINADO:")
        logger.info(f"   - Exitosos: {success_count}/{total_count} ({success_rate:.1f}%)")
        logger.info(f"   - Tiempo total: {elapsed_total/60:.1f} minutos")
        if total_count > 0:
            logger.info(f"   - Velocidad promedio: {total_count/(elapsed_total/60):.1f} artículos/minuto")
        
        return success_count, total_count

def main():
    """Función principal"""
    analyzer = CompleteImageAnalyzer()
    
    print("🤖 ANÁLISIS COMPLETO DE CV PARA ARTÍCULOS DE ALTO RIESGO")
    print("=" * 80)
    print("📊 Procesando los 150 artículos más recientes con riesgo medio/alto")
    print("🖼️ Descarga de imágenes faltantes")
    print("🔍 Análisis de calidad y propiedades de imagen")
    print("📐 Cálculo de posicionamiento en mosaico")
    print("🎨 Análisis de colores dominantes")
    print("⚠️ Evaluación de riesgo visual")
    print("=" * 80)
    
    # Confirmar antes de proceder
    try:
        confirm = input("\n¿Continuar con el análisis completo de CV? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ Cancelado por el usuario")
            return
    except KeyboardInterrupt:
        print("\n❌ Cancelado por el usuario")
        return
    
    # Ejecutar análisis completo
    success, total = analyzer.run_complete_analysis(150)
    
    print("\n" + "=" * 80)
    print("✅ ANÁLISIS CV COMPLETADO:")
    print(f"   - Artículos procesados exitosamente: {success}")
    print(f"   - Total de artículos: {total}")
    if total > 0:
        print(f"   - Tasa de éxito final: {success/total*100:.1f}%")
    print("=" * 80)

if __name__ == '__main__':
    main()
