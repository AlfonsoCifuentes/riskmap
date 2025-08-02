"""
Computer Vision Module for Image Analysis
Analiza las imágenes de los artículos para determinar áreas de interés
y optimizar su posición en el mosaico de noticias.
"""

import cv2
import numpy as np
import requests
from PIL import Image, ImageEnhance
import io
import logging
from typing import Dict, List, Tuple, Optional
import json
from pathlib import Path
import base64

logger = logging.getLogger(__name__)

class ImageInterestAnalyzer:
    """
    Analizador de áreas de interés en imágenes usando computer vision
    """
    
    def __init__(self):
        self.face_cascade = None
        self.body_cascade = None
        self.car_cascade = None
        self.building_cascade = None
        self._initialize_cascades()
    
    def _initialize_cascades(self):
        """Inicializar clasificadores en cascada de OpenCV"""
        try:
            # Cargar clasificadores preentrenados
            cascade_dir = cv2.data.haarcascades
            
            # Clasificador para caras
            face_cascade_path = cascade_dir + 'haarcascade_frontalface_default.xml'
            if Path(face_cascade_path).exists():
                self.face_cascade = cv2.CascadeClassifier(face_cascade_path)
                logger.info("✅ Clasificador de caras cargado")
            
            # Clasificador para perfiles
            profile_cascade_path = cascade_dir + 'haarcascade_profileface.xml'
            if Path(profile_cascade_path).exists():
                self.profile_cascade = cv2.CascadeClassifier(profile_cascade_path)
                logger.info("✅ Clasificador de perfiles cargado")
            
            # Clasificador para ojos (útil para detectar personas)
            eye_cascade_path = cascade_dir + 'haarcascade_eye.xml'
            if Path(eye_cascade_path).exists():
                self.eye_cascade = cv2.CascadeClassifier(eye_cascade_path)
                logger.info("✅ Clasificador de ojos cargado")
            
            logger.info("Computer vision inicializado correctamente")
            
        except Exception as e:
            logger.error(f"Error inicializando clasificadores: {e}")
    
    def analyze_image_interest_areas(self, image_url: str, article_title: str = "") -> Dict:
        """
        Analizar una imagen para encontrar áreas de interés
        
        Args:
            image_url: URL de la imagen a analizar
            article_title: Título del artículo para contexto
            
        Returns:
            Dict con análisis de áreas de interés
        """
        try:
            logger.info(f"🔍 Analizando imagen: {image_url[:100]}...")
            
            # Descargar y procesar imagen
            image_array = self._download_and_process_image(image_url)
            if image_array is None:
                return self._default_analysis()
            
            # Realizar múltiples análisis
            analysis = {
                'url': image_url,
                'title': article_title,
                'dimensions': {
                    'width': image_array.shape[1],
                    'height': image_array.shape[0]
                },
                'interest_areas': [],
                'composition_analysis': {},
                'positioning_recommendation': {},
                'crop_suggestions': [],
                'quality_score': 0.0
            }
            
            # Análisis de composición
            analysis['composition_analysis'] = self._analyze_composition(image_array)
            
            # Detectar áreas de interés
            analysis['interest_areas'] = self._detect_interest_areas(image_array)
            
            # Análisis de texto en imagen
            text_analysis = self._analyze_text_presence(image_array)
            analysis['text_areas'] = text_analysis
            
            # Generar recomendaciones de posicionamiento
            analysis['positioning_recommendation'] = self._generate_positioning_recommendation(
                analysis['interest_areas'], 
                analysis['composition_analysis'],
                analysis['dimensions']
            )
            
            # Generar sugerencias de recorte
            analysis['crop_suggestions'] = self._generate_crop_suggestions(
                analysis['interest_areas'],
                analysis['dimensions']
            )
            
            # Calcular puntuación de calidad
            analysis['quality_score'] = self._calculate_quality_score(analysis)
            
            logger.info(f"✅ Análisis completado - Calidad: {analysis['quality_score']:.2f}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analizando imagen {image_url}: {e}")
            return self._default_analysis()
    
    def _download_and_process_image(self, image_url: str) -> Optional[np.ndarray]:
        """Descargar/cargar y convertir imagen a array de OpenCV (URLs o rutas locales)"""
        try:
            pil_image = None
            
            # Determinar si es URL o ruta local
            if image_url.startswith(('http://', 'https://')):
                # Es una URL, descargar
                logger.debug(f"Descargando imagen desde URL: {image_url}")
                response = requests.get(image_url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                response.raise_for_status()
                pil_image = Image.open(io.BytesIO(response.content))
                
            else:
                # Es una ruta local, cargar directamente
                logger.debug(f"Cargando imagen local: {image_url}")
                
                # Construir ruta absoluta si es necesario
                if image_url.startswith('static/images/'):
                    # Ruta relativa desde el directorio del proyecto
                    base_path = Path(__file__).parent.parent.parent  # Volver a la raíz del proyecto
                    full_path = base_path / image_url
                else:
                    full_path = Path(image_url)
                
                # Verificar que el archivo existe
                if not full_path.exists():
                    logger.warning(f"Archivo de imagen no encontrado: {full_path}")
                    return None
                
                # Cargar imagen desde archivo
                pil_image = Image.open(full_path)
            
            # Convertir a RGB si es necesario
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Redimensionar si es muy grande (para optimizar procesamiento)
            max_size = 1200
            if max(pil_image.size) > max_size:
                ratio = max_size / max(pil_image.size)
                new_size = tuple(int(dim * ratio) for dim in pil_image.size)
                pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convertir a array de OpenCV
            cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            logger.debug(f"Imagen procesada exitosamente: {cv_image.shape}")
            return cv_image
            
        except Exception as e:
            logger.error(f"Error procesando imagen {image_url}: {e}")
            return None
    
    def _detect_interest_areas(self, image: np.ndarray) -> List[Dict]:
        """Detectar áreas de interés en la imagen"""
        interest_areas = []
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        height, width = image.shape[:2]
        
        # Detectar caras
        if self.face_cascade:
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            for (x, y, w, h) in faces:
                interest_areas.append({
                    'type': 'face',
                    'confidence': 0.8,
                    'bbox': {'x': int(x), 'y': int(y), 'width': int(w), 'height': int(h)},
                    'center': {'x': int(x + w/2), 'y': int(y + h/2)},
                    'importance': 0.9
                })
        
        # Detectar perfiles
        if hasattr(self, 'profile_cascade') and self.profile_cascade:
            profiles = self.profile_cascade.detectMultiScale(gray, 1.1, 4)
            for (x, y, w, h) in profiles:
                interest_areas.append({
                    'type': 'profile',
                    'confidence': 0.7,
                    'bbox': {'x': int(x), 'y': int(y), 'width': int(w), 'height': int(h)},
                    'center': {'x': int(x + w/2), 'y': int(y + h/2)},
                    'importance': 0.8
                })
        
        # Detectar características usando esquinas de Harris
        corners = cv2.cornerHarris(gray, 2, 3, 0.04)
        corners = cv2.dilate(corners, None)
        
        # Encontrar puntos de interés significativos
        threshold = 0.01 * corners.max()
        corner_points = np.where(corners > threshold)
        
        if len(corner_points[0]) > 0:
            # Agrupar puntos cercanos
            corner_clusters = self._cluster_corner_points(corner_points, width, height)
            
            for cluster in corner_clusters:
                interest_areas.append({
                    'type': 'feature_cluster',
                    'confidence': 0.6,
                    'bbox': cluster['bbox'],
                    'center': cluster['center'],
                    'importance': 0.6,
                    'points_count': cluster['points_count']
                })
        
        # Análisis de contornos para objetos
        contours, _ = cv2.findContours(
            cv2.Canny(gray, 50, 150), 
            cv2.RETR_EXTERNAL, 
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > (width * height * 0.01):  # Al menos 1% del área total
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filtrar contornos que son demasiado pequeños o grandes
                if w > 30 and h > 30 and area < (width * height * 0.7):
                    interest_areas.append({
                        'type': 'object',
                        'confidence': 0.5,
                        'bbox': {'x': int(x), 'y': int(y), 'width': int(w), 'height': int(h)},
                        'center': {'x': int(x + w/2), 'y': int(y + h/2)},
                        'importance': min(0.7, area / (width * height) * 3),
                        'area': int(area)
                    })
        
        # Ordenar por importancia
        interest_areas.sort(key=lambda x: x['importance'], reverse=True)
        
        return interest_areas[:10]  # Máximo 10 áreas de interés
    
    def _cluster_corner_points(self, corner_points: Tuple, width: int, height: int) -> List[Dict]:
        """Agrupar puntos de esquinas cercanos en clusters"""
        clusters = []
        points = list(zip(corner_points[1], corner_points[0]))  # (x, y)
        
        cluster_distance = min(width, height) * 0.1  # 10% de la dimensión menor
        
        used_points = set()
        
        for i, point in enumerate(points):
            if i in used_points:
                continue
                
            cluster_points = [point]
            used_points.add(i)
            
            # Buscar puntos cercanos
            for j, other_point in enumerate(points):
                if j in used_points:
                    continue
                    
                distance = np.sqrt((point[0] - other_point[0])**2 + (point[1] - other_point[1])**2)
                if distance < cluster_distance:
                    cluster_points.append(other_point)
                    used_points.add(j)
            
            if len(cluster_points) >= 3:  # Mínimo 3 puntos para formar un cluster
                # Calcular bounding box del cluster
                xs = [p[0] for p in cluster_points]
                ys = [p[1] for p in cluster_points]
                
                min_x, max_x = min(xs), max(xs)
                min_y, max_y = min(ys), max(ys)
                
                clusters.append({
                    'bbox': {
                        'x': int(min_x),
                        'y': int(min_y),
                        'width': int(max_x - min_x),
                        'height': int(max_y - min_y)
                    },
                    'center': {
                        'x': int((min_x + max_x) / 2),
                        'y': int((min_y + max_y) / 2)
                    },
                    'points_count': len(cluster_points)
                })
        
        return clusters
    
    def _analyze_composition(self, image: np.ndarray) -> Dict:
        """Analizar la composición de la imagen"""
        height, width = image.shape[:2]
        
        # Análisis de regla de tercios
        third_x = width // 3
        third_y = height // 3
        
        thirds_points = [
            (third_x, third_y), (2 * third_x, third_y),
            (third_x, 2 * third_y), (2 * third_x, 2 * third_y)
        ]
        
        # Análisis de brillo y contraste
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)
        contrast = np.std(gray)
        
        # Análisis de colores dominantes
        colors = image.reshape(-1, 3)
        dominant_colors = self._find_dominant_colors(colors)
        
        return {
            'rule_of_thirds_points': thirds_points,
            'brightness': float(brightness),
            'contrast': float(contrast),
            'dominant_colors': dominant_colors,
            'aspect_ratio': width / height,
            'resolution_quality': 'high' if min(width, height) > 800 else 'medium' if min(width, height) > 400 else 'low'
        }
    
    def _find_dominant_colors(self, colors: np.ndarray, k: int = 5) -> List[Dict]:
        """Encontrar colores dominantes usando K-means"""
        try:
            from sklearn.cluster import KMeans
            
            # Submuestrear para mejorar rendimiento
            if len(colors) > 10000:
                indices = np.random.choice(len(colors), 10000, replace=False)
                colors = colors[indices]
            
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(colors)
            
            colors_dominant = []
            labels = kmeans.labels_
            for i, color in enumerate(kmeans.cluster_centers_):
                percentage = np.sum(labels == i) / len(labels)
                colors_dominant.append({
                    'color': [int(c) for c in color],
                    'percentage': float(percentage)
                })
            
            return sorted(colors_dominant, key=lambda x: x['percentage'], reverse=True)
            
        except ImportError:
            # Fallback simple si sklearn no está disponible
            return [
                {'color': [128, 128, 128], 'percentage': 1.0}
            ]
    
    def _analyze_text_presence(self, image: np.ndarray) -> Dict:
        """Analizar presencia de texto en la imagen"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Aplicar filtros para detectar texto
        kernel = np.ones((1, 5), np.uint8)
        morph = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
        
        # Detectar regiones que podrían contener texto
        contours, _ = cv2.findContours(
            cv2.adaptiveThreshold(morph, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        text_regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h
            
            # Filtros para posibles regiones de texto
            if (w > 20 and h > 10 and 
                aspect_ratio > 1.5 and aspect_ratio < 15 and
                cv2.contourArea(contour) > 100):
                
                text_regions.append({
                    'bbox': {'x': int(x), 'y': int(y), 'width': int(w), 'height': int(h)},
                    'confidence': min(0.8, aspect_ratio / 10)
                })
        
        return {
            'has_text': len(text_regions) > 0,
            'text_regions': text_regions,
            'text_coverage': sum(r['bbox']['width'] * r['bbox']['height'] for r in text_regions) / (image.shape[0] * image.shape[1])
        }
    
    def _generate_positioning_recommendation(self, interest_areas: List[Dict], 
                                           composition: Dict, dimensions: Dict) -> Dict:
        """Generar recomendaciones de posicionamiento para el mosaico"""
        
        if not interest_areas:
            return {
                'position': 'center',
                'mosaic_position': 'center',
                'crop_focus': 'center',
                'focal_point': {'x': dimensions.get('width', 0) // 2, 'y': dimensions.get('height', 0) // 2},
                'confidence': 0.5,
                'reasoning': 'No se detectaron áreas de interés específicas'
            }
        
        # Encontrar el área de mayor importancia
        main_interest = max(interest_areas, key=lambda x: x.get('importance', 0))
        center_x = main_interest['center']['x']
        center_y = main_interest['center']['y']
        
        width = dimensions['width']
        height = dimensions['height']
        
        # Determinar posición recomendada basada en la ubicación del área de interés
        if center_x < width * 0.33:
            h_pos = 'left'
        elif center_x > width * 0.67:
            h_pos = 'right'
        else:
            h_pos = 'center'
        
        if center_y < height * 0.33:
            v_pos = 'top'
        elif center_y > height * 0.67:
            v_pos = 'bottom'
        else:
            v_pos = 'center'
        
        # Generar posición de mosaico
        if v_pos == 'center' and h_pos == 'center':
            mosaic_position = 'center'
        elif v_pos == 'top':
            mosaic_position = f'top-{h_pos}'
        elif v_pos == 'bottom':
            mosaic_position = f'bottom-{h_pos}'
        else:
            mosaic_position = f'{v_pos}-{h_pos}'
        
        # Determinar el tamaño recomendado basado en la importancia
        importance = main_interest.get('importance', 0)
        if importance > 0.8:
            size_recommendation = 'large'
        elif importance > 0.6:
            size_recommendation = 'medium'
        else:
            size_recommendation = 'small'
        
        return {
            'position': mosaic_position,
            'mosaic_position': mosaic_position,
            'size_recommendation': size_recommendation,
            'crop_focus': f"{center_x},{center_y}",
            'focal_point': {'x': center_x, 'y': center_y},
            'confidence': main_interest['importance'],
            'reasoning': f'Área de interés principal ({main_interest["type"]}) detectada en posición {mosaic_position}',
            'main_interest_type': main_interest['type']
        }
    
    def _generate_crop_suggestions(self, interest_areas: List[Dict], dimensions: Dict) -> List[Dict]:
        """Generar sugerencias de recorte para diferentes formatos"""
        suggestions = []
        
        if not interest_areas:
            return [{
                'format': 'square',
                'crop': {'x': 0, 'y': 0, 'width': min(dimensions['width'], dimensions['height']), 'height': min(dimensions['width'], dimensions['height'])},
                'confidence': 0.5
            }]
        
        main_interest = interest_areas[0]
        center_x = main_interest['center']['x']
        center_y = main_interest['center']['y']
        
        width = dimensions['width']
        height = dimensions['height']
        
        # Sugerencia para formato cuadrado (mosaico)
        square_size = min(width, height)
        square_x = max(0, min(center_x - square_size // 2, width - square_size))
        square_y = max(0, min(center_y - square_size // 2, height - square_size))
        
        suggestions.append({
            'format': 'square',
            'crop': {'x': int(square_x), 'y': int(square_y), 'width': int(square_size), 'height': int(square_size)},
            'confidence': main_interest['importance'],
            'description': 'Recorte cuadrado centrado en área de interés principal'
        })
        
        # Sugerencia para formato 16:9 (widescreen)
        if width >= height * 1.5:  # Si la imagen es suficientemente ancha
            crop_width = int(height * 16/9)
            crop_height = height
            crop_x = max(0, min(center_x - crop_width // 2, width - crop_width))
            crop_y = 0
            
            suggestions.append({
                'format': '16:9',
                'crop': {'x': int(crop_x), 'y': int(crop_y), 'width': int(crop_width), 'height': int(crop_height)},
                'confidence': main_interest['importance'] * 0.8,
                'description': 'Recorte 16:9 horizontal'
            })
        
        # Sugerencia para formato 4:3
        target_ratio = 4/3
        if width / height > target_ratio:
            # Imagen más ancha, recortar los lados
            crop_width = int(height * target_ratio)
            crop_height = height
            crop_x = max(0, min(center_x - crop_width // 2, width - crop_width))
            crop_y = 0
        else:
            # Imagen más alta, recortar arriba y abajo
            crop_width = width
            crop_height = int(width / target_ratio)
            crop_x = 0
            crop_y = max(0, min(center_y - crop_height // 2, height - crop_height))
        
        suggestions.append({
            'format': '4:3',
            'crop': {'x': int(crop_x), 'y': int(crop_y), 'width': int(crop_width), 'height': int(crop_height)},
            'confidence': main_interest['importance'] * 0.9,
            'description': 'Recorte 4:3 estándar'
        })
        
        return suggestions
    
    def _calculate_quality_score(self, analysis: Dict) -> float:
        """Calcular puntuación de calidad general de la imagen"""
        score = 0.0
        
        # Puntuación base por resolución
        dimensions = analysis['dimensions']
        min_dimension = min(dimensions['width'], dimensions['height'])
        
        if min_dimension >= 800:
            score += 0.3
        elif min_dimension >= 400:
            score += 0.2
        else:
            score += 0.1
        
        # Puntuación por áreas de interés
        if analysis['interest_areas']:
            main_interest = analysis['interest_areas'][0]
            score += main_interest['importance'] * 0.4
            
            # Bonus por múltiples áreas de interés
            if len(analysis['interest_areas']) > 1:
                score += 0.1
        
        # Puntuación por composición
        composition = analysis['composition_analysis']
        
        # Brightness óptimo (ni muy oscuro ni muy claro)
        brightness_score = 1.0 - abs(composition['brightness'] - 128) / 128
        score += brightness_score * 0.1
        
        # Contraste adecuado
        contrast_score = min(1.0, composition['contrast'] / 50)
        score += contrast_score * 0.1
        
        # Penalty por texto excesivo
        if analysis.get('text_areas', {}).get('text_coverage', 0) > 0.3:
            score -= 0.1
        
        return min(1.0, max(0.0, score))
    
    def _default_analysis(self) -> Dict:
        """Análisis por defecto cuando falla el procesamiento"""
        return {
            'url': '',
            'title': '',
            'dimensions': {'width': 400, 'height': 300},
            'interest_areas': [],
            'composition_analysis': {
                'brightness': 128,
                'contrast': 50,
                'dominant_colors': [{'color': [128, 128, 128], 'percentage': 1.0}],
                'aspect_ratio': 4/3,
                'resolution_quality': 'medium'
            },
            'positioning_recommendation': {
                'position': 'center',
                'crop_focus': 'center',
                'confidence': 0.5,
                'reasoning': 'Análisis por defecto'
            },
            'crop_suggestions': [{
                'format': 'square',
                'crop': {'x': 0, 'y': 0, 'width': 300, 'height': 300},
                'confidence': 0.5
            }],
            'text_areas': {'has_text': False, 'text_regions': [], 'text_coverage': 0},
            'quality_score': 0.5
        }

def analyze_article_image(image_url: str, article_title: str = "") -> Dict:
    """
    Función de conveniencia para analizar una imagen de artículo
    
    Args:
        image_url: URL de la imagen
        article_title: Título del artículo
        
    Returns:
        Análisis completo de la imagen
    """
    analyzer = ImageInterestAnalyzer()
    return analyzer.analyze_image_interest_areas(image_url, article_title)

if __name__ == "__main__":
    # Ejemplo de uso
    test_url = "https://example.com/image.jpg"
    result = analyze_article_image(test_url, "Test Article")
    print(json.dumps(result, indent=2, ensure_ascii=False))
