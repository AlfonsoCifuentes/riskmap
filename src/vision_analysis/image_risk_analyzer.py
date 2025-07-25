"""
Análisis de Imágenes con YOLO y OpenCV para Detección de Riesgos Geopolíticos
Detecta objetos relacionados con conflictos, manifestaciones, armamento, etc.
"""
import cv2
import numpy as np
import requests
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import tempfile
from urllib.parse import urlparse
import hashlib

# Intentar importar YOLO
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("YOLO (ultralytics) no está instalado. Instale con: pip install ultralytics")

logger = logging.getLogger(__name__)


class ImageRiskAnalyzer:
    """
    Analizador de riesgos en imágenes usando YOLO y OpenCV
    """

    def __init__(self, config=None):
        self.config = config or {}
        self.model = None
        self.cache_dir = Path("data/image_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Mapeo de objetos detectados a niveles de riesgo
        self.risk_objects = {
            # Alto riesgo - Armamento y conflictos
            'gun': {'risk': 9, 'category': 'weapons', 'keywords': ['weapon', 'firearm', 'gun']},
            'rifle': {'risk': 10, 'category': 'weapons', 'keywords': ['rifle', 'assault', 'military']},
            'tank': {'risk': 10, 'category': 'military', 'keywords': ['tank', 'armor', 'military']},
            'missile': {'risk': 10, 'category': 'weapons', 'keywords': ['missile', 'rocket', 'weapon']},

            # Riesgo medio-alto - Vehículos militares
            'truck': {'risk': 4, 'category': 'vehicles', 'keywords': ['military truck', 'convoy']},
            'airplane': {'risk': 6, 'category': 'aircraft', 'keywords': ['military aircraft', 'fighter']},
            'helicopter': {'risk': 7, 'category': 'aircraft', 'keywords': ['military helicopter', 'combat']},

            # Riesgo medio - Multitudes y manifestaciones
            'person': {'risk': 3, 'category': 'crowd', 'keywords': ['crowd', 'protest', 'demonstration']},

            # Riesgo bajo-medio - Infraestructura
            'building': {'risk': 2, 'category': 'infrastructure', 'keywords': ['damaged building', 'destruction']},
            'fire': {'risk': 8, 'category': 'disaster', 'keywords': ['fire', 'explosion', 'burning']},
            'smoke': {'risk': 7, 'category': 'disaster', 'keywords': ['smoke', 'fire', 'explosion']},
        }

        # Detectores de patrones específicos
        self.pattern_detectors = {
            'crowd_density': self._analyze_crowd_density,
            'smoke_fire': self._detect_smoke_fire,
            'military_vehicles': self._detect_military_vehicles,
            'damaged_buildings': self._detect_damage,
        }

        self._initialize_model()

    def _initialize_model(self):
        """Inicializa el modelo YOLO"""
        if not YOLO_AVAILABLE:
            logger.warning("YOLO no disponible, usando análisis OpenCV básico")
            return

        try:
            # Usar YOLOv8 pre-entrenado
            model_path = self.config.get('yolo_model_path', 'yolov8n.pt')
            self.model = YOLO(model_path)
            logger.info("Modelo YOLO inicializado correctamente")
        except Exception as e:
            logger.error(f"Error inicializando YOLO: {e}")
            self.model = None

    def analyze_image_risk(
            self,
            image_url: str,
            article_context: Dict = None) -> Dict:
        """
        Analiza una imagen y determina el nivel de riesgo basado en objetos detectados

        Args:
            image_url: URL de la imagen a analizar
            article_context: Contexto del artículo (título, contenido, etc.)

        Returns:
            Dict con análisis de riesgo visual
        """
        try:
            # Descargar y cachear la imagen
            image_path = self._download_and_cache_image(image_url)
            if not image_path:
                return self._create_error_result("Error descargando imagen")

            # Cargar imagen con OpenCV
            image = cv2.imread(str(image_path))
            if image is None:
                return self._create_error_result("Error cargando imagen")

            # Análisis principal
            analysis_result = {
                'image_url': image_url,
                'visual_risk_score': 0,
                'detected_objects': [],
                'risk_indicators': [],
                'pattern_analysis': {},
                'recommendations': [],
                'confidence': 0.0,
                'analysis_method': 'hybrid'
            }

            # 1. Análisis con YOLO (si está disponible)
            if self.model:
                yolo_results = self._analyze_with_yolo(image)
                analysis_result.update(yolo_results)

            # 2. Análisis con OpenCV (patrones y características)
            opencv_results = self._analyze_with_opencv(image)
            analysis_result = self._merge_analysis_results(
                analysis_result, opencv_results)

            # 3. Análisis contextual (combinar con texto del artículo)
            if article_context:
                context_bonus = self._analyze_context_correlation(
                    analysis_result, article_context)
                analysis_result['visual_risk_score'] += context_bonus
                analysis_result['context_correlation'] = context_bonus

            # 4. Normalizar puntuación final
            analysis_result['visual_risk_score'] = min(
                10, max(0, analysis_result['visual_risk_score']))
            analysis_result['risk_level'] = self._get_risk_level(
                analysis_result['visual_risk_score'])

            logger.info(
                f"Análisis completado - Risk Score: {analysis_result['visual_risk_score']}")
            return analysis_result

        except Exception as e:
            logger.error(f"Error en análisis de imagen: {e}")
            return self._create_error_result(str(e))

    def _download_and_cache_image(self, image_url: str) -> Optional[Path]:
        """Descarga y cachea una imagen"""
        try:
            # Generar hash para el cache
            url_hash = hashlib.md5(image_url.encode()).hexdigest()
            cache_path = self.cache_dir / f"{url_hash}.jpg"

            # Si ya está en cache, usar esa versión
            if cache_path.exists():
                return cache_path

            # Descargar imagen
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

            response = requests.get(
                image_url,
                headers=headers,
                timeout=10,
                stream=True)
            response.raise_for_status()

            # Guardar en cache
            with open(cache_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return cache_path

        except Exception as e:
            logger.error(f"Error descargando imagen {image_url}: {e}")
            return None

    def _analyze_with_yolo(self, image: np.ndarray) -> Dict:
        """Análisis usando YOLO"""
        try:
            results = self.model(image, verbose=False)

            detected_objects = []
            total_risk = 0
            confidence_sum = 0

            for r in results:
                boxes = r.boxes
                if boxes is not None:
                    for box in boxes:
                        # Obtener clase y confianza
                        cls = int(box.cls[0])
                        conf = float(box.conf[0])
                        class_name = self.model.names[cls]

                        # Calcular riesgo del objeto
                        object_risk = self._calculate_object_risk(
                            class_name, conf)

                        detected_objects.append({
                            'object': class_name,
                            'confidence': conf,
                            'risk_score': object_risk,
                            'bbox': box.xyxy[0].tolist() if hasattr(box, 'xyxy') else None
                        })

                        total_risk += object_risk * conf
                        confidence_sum += conf

            avg_confidence = confidence_sum / \
                len(detected_objects) if detected_objects else 0

            return {
                'detected_objects': detected_objects,
                'visual_risk_score': min(10, total_risk),
                'confidence': avg_confidence,
                'analysis_method': 'yolo'
            }

        except Exception as e:
            logger.error(f"Error en análisis YOLO: {e}")
            return {
                'detected_objects': [],
                'visual_risk_score': 0,
                'confidence': 0}

    def _analyze_with_opencv(self, image: np.ndarray) -> Dict:
        """Análisis usando OpenCV para patrones específicos"""
        analysis = {
            'pattern_analysis': {},
            'risk_indicators': [],
            'visual_risk_score': 0
        }

        try:
            # Ejecutar detectores de patrones
            for pattern_name, detector_func in self.pattern_detectors.items():
                pattern_result = detector_func(image)
                analysis['pattern_analysis'][pattern_name] = pattern_result

                if pattern_result.get('detected', False):
                    analysis['visual_risk_score'] += pattern_result.get(
                        'risk_score', 0)
                    analysis['risk_indicators'].append({
                        'type': pattern_name,
                        'description': pattern_result.get('description', ''),
                        'confidence': pattern_result.get('confidence', 0)
                    })

            return analysis

        except Exception as e:
            logger.error(f"Error en análisis OpenCV: {e}")
            return analysis

    def _analyze_crowd_density(self, image: np.ndarray) -> Dict:
        """Detecta densidad de multitudes"""
        try:
            # Convertir a escala de grises
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Detectar contornos que podrían ser personas
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(
                edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Filtrar contornos por tamaño (posibles personas)
            person_contours = [
                c for c in contours if 500 < cv2.contourArea(c) < 5000]

            crowd_density = len(person_contours) / \
                (image.shape[0] * image.shape[1] / 10000)

            risk_score = 0
            if crowd_density > 5:  # Multitud densa
                risk_score = min(6, crowd_density * 0.5)

            return {
                'detected': crowd_density > 3,
                'risk_score': risk_score,
                'confidence': min(
                    0.8,
                    crowd_density * 0.1),
                'description': f"Densidad de multitud detectada: {crowd_density:.1f}",
                'metrics': {
                    'crowd_density': crowd_density,
                    'person_shapes': len(person_contours)}}

        except Exception as e:
            logger.error(f"Error detectando multitudes: {e}")
            return {'detected': False, 'risk_score': 0, 'confidence': 0}

    def _detect_smoke_fire(self, image: np.ndarray) -> Dict:
        """Detecta humo y fuego"""
        try:
            # Convertir a HSV para mejor detección de colores
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            # Rango de colores para fuego/humo
            fire_lower = np.array([0, 50, 50])
            fire_upper = np.array([35, 255, 255])

            smoke_lower = np.array([0, 0, 50])
            smoke_upper = np.array([180, 30, 200])

            # Crear máscaras
            fire_mask = cv2.inRange(hsv, fire_lower, fire_upper)
            smoke_mask = cv2.inRange(hsv, smoke_lower, smoke_upper)

            # Calcular porcentaje de píxeles que coinciden
            fire_percentage = np.sum(fire_mask > 0) / \
                (image.shape[0] * image.shape[1])
            smoke_percentage = np.sum(
                smoke_mask > 0) / (image.shape[0] * image.shape[1])

            risk_score = 0
            detected = False
            description = ""

            if fire_percentage > 0.05:  # 5% de la imagen
                risk_score += min(8, fire_percentage * 100)
                detected = True
                description += f"Fuego detectado ({fire_percentage*100:.1f}%) "

            if smoke_percentage > 0.1:  # 10% de la imagen
                risk_score += min(6, smoke_percentage * 50)
                detected = True
                description += f"Humo detectado ({smoke_percentage*100:.1f}%)"

            return {
                'detected': detected,
                'risk_score': risk_score,
                'confidence': max(fire_percentage, smoke_percentage) * 10,
                'description': description.strip(),
                'metrics': {
                    'fire_percentage': fire_percentage,
                    'smoke_percentage': smoke_percentage
                }
            }

        except Exception as e:
            logger.error(f"Error detectando fuego/humo: {e}")
            return {'detected': False, 'risk_score': 0, 'confidence': 0}

    def _detect_military_vehicles(self, image: np.ndarray) -> Dict:
        """Detecta vehículos militares usando características geométricas"""
        try:
            # Convertir a escala de grises
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Detectar formas rectangulares grandes (posibles vehículos)
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(
                edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            military_shapes = 0
            for contour in contours:
                # Aproximar contorno
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)

                # Buscar formas rectangulares grandes
                if len(approx) >= 4 and cv2.contourArea(contour) > 2000:
                    # Calcular relación de aspecto
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = float(w) / h

                    # Vehículos militares suelen ser alargados
                    if 1.5 < aspect_ratio < 4.0:
                        military_shapes += 1

            risk_score = min(7, military_shapes * 2)
            detected = military_shapes > 0

            return {
                'detected': detected,
                'risk_score': risk_score,
                'confidence': min(
                    0.7,
                    military_shapes * 0.2),
                'description': f"Posibles vehículos militares detectados: {military_shapes}",
                'metrics': {
                    'military_shapes': military_shapes}}

        except Exception as e:
            logger.error(f"Error detectando vehículos militares: {e}")
            return {'detected': False, 'risk_score': 0, 'confidence': 0}

    def _detect_damage(self, image: np.ndarray) -> Dict:
        """Detecta daños en edificios o infraestructura"""
        try:
            # Convertir a escala de grises
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Detectar bordes irregulares (posible daño)
            edges = cv2.Canny(gray, 30, 100)

            # Calcular densidad de bordes (más bordes = más irregular)
            edge_density = np.sum(edges > 0) / \
                (image.shape[0] * image.shape[1])

            # Detectar variación en intensidad (escombros, daños)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

            risk_score = 0
            detected = False

            if edge_density > 0.1 and laplacian_var > 500:
                risk_score = min(5, (edge_density * 20) +
                                 (laplacian_var / 200))
                detected = True

            return {
                'detected': detected,
                'risk_score': risk_score,
                'confidence': min(0.6, edge_density * 5),
                'description': f"Posible daño estructural detectado",
                'metrics': {
                    'edge_density': edge_density,
                    'texture_variance': laplacian_var
                }
            }

        except Exception as e:
            logger.error(f"Error detectando daños: {e}")
            return {'detected': False, 'risk_score': 0, 'confidence': 0}

    def _calculate_object_risk(
            self,
            class_name: str,
            confidence: float) -> float:
        """Calcula el riesgo de un objeto detectado"""
        if class_name in self.risk_objects:
            base_risk = self.risk_objects[class_name]['risk']
            return base_risk * confidence
        return 1.0 * confidence  # Riesgo base para objetos no clasificados

    def _analyze_context_correlation(
            self,
            visual_analysis: Dict,
            article_context: Dict) -> float:
        """Analiza correlación entre análisis visual y contexto del artículo"""
        bonus = 0.0

        try:
            title = article_context.get('title', '').lower()
            content = article_context.get('content', '').lower()
            text = f"{title} {content}"

            # Palabras clave que correlacionan con objetos detectados
            for obj in visual_analysis.get('detected_objects', []):
                obj_name = obj['object'].lower()

                if obj_name in self.risk_objects:
                    keywords = self.risk_objects[obj_name]['keywords']
                    for keyword in keywords:
                        if keyword in text:
                            bonus += obj['confidence'] * 1.5
                            break

            # Correlación con patrones detectados
            for indicator in visual_analysis.get('risk_indicators', []):
                indicator_type = indicator['type']

                correlations = {
                    'crowd_density': [
                        'protest', 'demonstration', 'crowd', 'rally'], 'smoke_fire': [
                        'fire', 'explosion', 'burn', 'smoke'], 'military_vehicles': [
                        'military', 'army', 'tank', 'convoy'], 'damaged_buildings': [
                        'destruction', 'damage', 'collapsed', 'ruins']}

                if indicator_type in correlations:
                    for keyword in correlations[indicator_type]:
                        if keyword in text:
                            bonus += indicator['confidence'] * 2.0
                            break

            return min(3.0, bonus)  # Máximo bonus de 3 puntos

        except Exception as e:
            logger.error(f"Error en correlación contextual: {e}")
            return 0.0

    def _merge_analysis_results(
            self,
            yolo_results: Dict,
            opencv_results: Dict) -> Dict:
        """Combina resultados de YOLO y OpenCV"""
        merged = yolo_results.copy()

        # Combinar puntuaciones de riesgo
        merged['visual_risk_score'] += opencv_results.get(
            'visual_risk_score', 0)

        # Agregar análisis de patrones
        merged['pattern_analysis'] = opencv_results.get('pattern_analysis', {})

        # Combinar indicadores de riesgo
        merged['risk_indicators'] = opencv_results.get('risk_indicators', [])

        # Generar recomendaciones
        merged['recommendations'] = self._generate_recommendations(merged)

        return merged

    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """Genera recomendaciones basadas en el análisis"""
        recommendations = []

        risk_score = analysis.get('visual_risk_score', 0)

        if risk_score > 8:
            recommendations.append(
                "ALERTA CRÍTICA: Evidencia visual de alto riesgo detectada")
            recommendations.append(
                "Verificar información con fuentes adicionales")
            recommendations.append(
                "Considerar activación de protocolos de emergencia")
        elif risk_score > 5:
            recommendations.append(
                "Nivel de riesgo elevado en contenido visual")
            recommendations.append("Monitoreo continuo recomendado")
            recommendations.append("Corroborar con análisis de texto")
        elif risk_score > 2:
            recommendations.append(
                "Elementos de riesgo moderado identificados")
            recommendations.append("Seguimiento de la situación aconsejado")
        else:
            recommendations.append("Nivel de riesgo visual bajo")
            recommendations.append("Continuar monitoreo rutinario")

        # Recomendaciones específicas por objetos detectados
        for obj in analysis.get('detected_objects', []):
            if obj['object'] in ['gun', 'rifle', 'missile', 'tank']:
                recommendations.append(
                    f"Armamento detectado: {obj['object']} - Verificación urgente requerida")

        return list(set(recommendations))  # Eliminar duplicados

    def _get_risk_level(self, risk_score: float) -> str:
        """Convierte puntuación numérica a nivel de riesgo"""
        if risk_score >= 8:
            return "CRITICAL"
        elif risk_score >= 6:
            return "HIGH"
        elif risk_score >= 3:
            return "MEDIUM"
        else:
            return "LOW"

    def _create_error_result(self, error_message: str) -> Dict:
        """Crea resultado de error estándar"""
        return {
            'error': error_message,
            'visual_risk_score': 0,
            'detected_objects': [],
            'risk_indicators': [],
            'pattern_analysis': {},
            'recommendations': ['Error en análisis visual - usar solo análisis de texto'],
            'confidence': 0.0,
            'risk_level': 'UNKNOWN'}

    def batch_analyze_images(
            self,
            image_urls: List[str],
            article_contexts: List[Dict] = None) -> List[Dict]:
        """Analiza múltiples imágenes en lote"""
        results = []

        for i, url in enumerate(image_urls):
            context = article_contexts[i] if article_contexts and i < len(
                article_contexts) else None
            result = self.analyze_image_risk(url, context)
            results.append(result)

            # Log progreso
            if (i + 1) % 10 == 0:
                logger.info(f"Procesadas {i + 1}/{len(image_urls)} imágenes")

        return results
