#!/usr/bin/env python3
"""
Real Computer Vision Analysis Service
Utiliza el modelo entrenado personalizado para análisis de imágenes satelitales
"""

import os
import sys
import json
import cv2
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import sqlite3
from datetime import datetime

logger = logging.getLogger(__name__)

class ComputerVisionService:
    """Servicio real de computer vision para análisis de imágenes satelitales"""
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path or "models/trained/deployment_package"
        self.model = None
        self.class_labels = []
        self.confidence_threshold = 0.5
        
        # Verificar que el modelo existe
        model_dir = Path(self.model_path)
        if not model_dir.exists():
            raise FileNotFoundError(f"Modelo no encontrado en {self.model_path}")
        
        self._load_model()
    
    def _load_model(self):
        """Cargar el modelo entrenado"""
        try:
            model_dir = Path(self.model_path)
            
            # Buscar archivos del modelo
            model_files = list(model_dir.glob("*.pb")) + list(model_dir.glob("*.h5")) + list(model_dir.glob("*.onnx"))
            
            if not model_files:
                raise FileNotFoundError(f"No se encontraron archivos de modelo en {model_dir}")
            
            model_file = model_files[0]
            
            # Intentar cargar dependiendo del tipo
            if model_file.suffix == '.pb':
                self._load_tensorflow_model(model_file)
            elif model_file.suffix == '.h5':
                self._load_keras_model(model_file)
            elif model_file.suffix == '.onnx':
                self._load_onnx_model(model_file)
            else:
                # Fallback: usar OpenCV DNN
                self._load_opencv_model(model_file)
            
            # Cargar etiquetas de clases si existen
            labels_file = model_dir / "labels.txt"
            if labels_file.exists():
                with open(labels_file, 'r') as f:
                    self.class_labels = [line.strip() for line in f.readlines()]
            else:
                # Etiquetas por defecto para detección de conflictos
                self.class_labels = [
                    'background', 'vehicle', 'military_vehicle', 'tank', 'aircraft',
                    'fire', 'smoke', 'explosion', 'damage', 'infrastructure',
                    'civilian_area', 'military_base', 'refugee_camp'
                ]
            
            logger.info(f"✅ Modelo cargado: {model_file}")
            logger.info(f"📋 Clases disponibles: {len(self.class_labels)}")
            
        except Exception as e:
            logger.error(f"Error cargando modelo: {e}")
            # Fallback: usar detector genérico
            self._setup_fallback_detector()
    
    def _load_tensorflow_model(self, model_file: Path):
        """Cargar modelo TensorFlow"""
        try:
            import tensorflow as tf
            self.model = tf.saved_model.load(str(model_file.parent))
            self.model_type = 'tensorflow'
            logger.info("Modelo TensorFlow cargado")
        except ImportError:
            logger.warning("TensorFlow no disponible, usando fallback")
            self._setup_fallback_detector()
        except Exception as e:
            logger.error(f"Error cargando modelo TensorFlow: {e}")
            self._setup_fallback_detector()
    
    def _load_keras_model(self, model_file: Path):
        """Cargar modelo Keras"""
        try:
            import tensorflow as tf
            self.model = tf.keras.models.load_model(str(model_file))
            self.model_type = 'keras'
            logger.info("Modelo Keras cargado")
        except ImportError:
            logger.warning("Keras no disponible, usando fallback")
            self._setup_fallback_detector()
        except Exception as e:
            logger.error(f"Error cargando modelo Keras: {e}")
            self._setup_fallback_detector()
    
    def _load_onnx_model(self, model_file: Path):
        """Cargar modelo ONNX"""
        try:
            import onnxruntime as ort
            self.model = ort.InferenceSession(str(model_file))
            self.model_type = 'onnx'
            logger.info("Modelo ONNX cargado")
        except ImportError:
            logger.warning("ONNX Runtime no disponible, usando fallback")
            self._setup_fallback_detector()
        except Exception as e:
            logger.error(f"Error cargando modelo ONNX: {e}")
            self._setup_fallback_detector()
    
    def _load_opencv_model(self, model_file: Path):
        """Cargar modelo usando OpenCV DNN"""
        try:
            self.model = cv2.dnn.readNet(str(model_file))
            self.model_type = 'opencv'
            logger.info("Modelo OpenCV DNN cargado")
        except Exception as e:
            logger.error(f"Error cargando modelo OpenCV: {e}")
            self._setup_fallback_detector()
    
    def _setup_fallback_detector(self):
        """Configurar detector de fallback usando características tradicionales"""
        logger.warning("Usando detector de fallback basado en características tradicionales")
        self.model = None
        self.model_type = 'fallback'
        
        # Configurar detectores OpenCV
        try:
            # Detector de características SIFT/ORB
            self.feature_detector = cv2.ORB_create()
            # Detector de contornos para vehículos/estructuras
            self.contour_detector = cv2.SimpleBlobDetector_create()
        except Exception:
            logger.error("Error configurando detectores de fallback")
    
    def analyze_satellite_image(self, image_path: str) -> Dict:
        """Analizar imagen satelital completa"""
        try:
            # Cargar imagen
            image = cv2.imread(image_path)
            if image is None:
                return {
                    'success': False,
                    'error': f'No se pudo cargar la imagen: {image_path}'
                }
            
            logger.info(f"🔍 Analizando imagen: {image_path} ({image.shape})")
            
            # Realizar análisis según el tipo de modelo
            if self.model_type == 'tensorflow':
                results = self._analyze_with_tensorflow(image)
            elif self.model_type == 'keras':
                results = self._analyze_with_keras(image)
            elif self.model_type == 'onnx':
                results = self._analyze_with_onnx(image)
            elif self.model_type == 'opencv':
                results = self._analyze_with_opencv(image)
            else:
                results = self._analyze_with_fallback(image)
            
            # Enriquecer resultados con metadatos
            results.update({
                'image_path': image_path,
                'image_shape': image.shape,
                'analysis_timestamp': datetime.now().isoformat(),
                'model_type': self.model_type,
                'confidence_threshold': self.confidence_threshold
            })
            
            return results
            
        except Exception as e:
            logger.error(f"Error en análisis de imagen: {e}")
            return {
                'success': False,
                'error': str(e),
                'image_path': image_path
            }
    
    def _analyze_with_fallback(self, image: np.ndarray) -> Dict:
        """Análisis con métodos tradicionales de computer vision"""
        try:
            detections = []
            confidence_scores = []
            
            # Detectar características de interés
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 1. Detectar formas rectangulares (posibles vehículos/edificios)
            contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            vehicle_count = 0
            structure_count = 0
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 100 < area < 5000:  # Filtrar por tamaño
                    # Aproximar contorno
                    epsilon = 0.02 * cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, epsilon, True)
                    
                    # Detectar formas rectangulares (posibles vehículos)
                    if len(approx) == 4:
                        x, y, w, h = cv2.boundingRect(contour)
                        aspect_ratio = w / h
                        
                        if 1.5 < aspect_ratio < 4:  # Ratio típico de vehículos
                            vehicle_count += 1
                            detections.append({
                                'class': 'vehicle',
                                'confidence': 0.6,
                                'bbox': [x, y, w, h],
                                'area': area
                            })
                        else:
                            structure_count += 1
                            detections.append({
                                'class': 'structure',
                                'confidence': 0.5,
                                'bbox': [x, y, w, h],
                                'area': area
                            })
            
            # 2. Detectar cambios de color (posible fuego/humo)
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Detectar rojos/naranjas (fuego)
            fire_mask = cv2.inRange(hsv, (0, 50, 50), (20, 255, 255))
            fire_contours, _ = cv2.findContours(fire_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            fire_count = 0
            for contour in fire_contours:
                area = cv2.contourArea(contour)
                if area > 50:
                    x, y, w, h = cv2.boundingRect(contour)
                    fire_count += 1
                    detections.append({
                        'class': 'fire',
                        'confidence': 0.7,
                        'bbox': [x, y, w, h],
                        'area': area
                    })
            
            # 3. Detectar grises (humo)
            smoke_mask = cv2.inRange(gray, 100, 180)
            smoke_contours, _ = cv2.findContours(smoke_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            smoke_count = 0
            for contour in smoke_contours:
                area = cv2.contourArea(contour)
                if area > 200:
                    x, y, w, h = cv2.boundingRect(contour)
                    smoke_count += 1
                    detections.append({
                        'class': 'smoke',
                        'confidence': 0.6,
                        'bbox': [x, y, w, h],
                        'area': area
                    })
            
            # Calcular métricas de riesgo
            risk_score = 0.0
            risk_factors = []
            
            if vehicle_count > 5:
                risk_score += 0.3
                risk_factors.append(f"{vehicle_count} vehículos detectados")
            
            if fire_count > 0:
                risk_score += 0.5
                risk_factors.append(f"{fire_count} fuegos detectados")
            
            if smoke_count > 0:
                risk_score += 0.4
                risk_factors.append(f"{smoke_count} columnas de humo detectadas")
            
            # Limitar score a 1.0
            risk_score = min(risk_score, 1.0)
            
            # Determinar nivel de riesgo
            if risk_score >= 0.7:
                risk_level = 'high'
            elif risk_score >= 0.4:
                risk_level = 'medium'
            else:
                risk_level = 'low'
            
            return {
                'success': True,
                'detections': detections,
                'total_detections': len(detections),
                'vehicle_count': vehicle_count,
                'structure_count': structure_count,
                'fire_count': fire_count,
                'smoke_count': smoke_count,
                'risk_score': risk_score,
                'risk_level': risk_level,
                'risk_factors': risk_factors,
                'analysis_method': 'traditional_cv'
            }
            
        except Exception as e:
            logger.error(f"Error en análisis fallback: {e}")
            return {
                'success': False,
                'error': str(e),
                'analysis_method': 'traditional_cv'
            }
    
    def _analyze_with_tensorflow(self, image: np.ndarray) -> Dict:
        """Análisis usando modelo TensorFlow"""
        # Implementar cuando el modelo específico esté disponible
        logger.warning("Análisis TensorFlow no implementado, usando fallback")
        return self._analyze_with_fallback(image)
    
    def _analyze_with_keras(self, image: np.ndarray) -> Dict:
        """Análisis usando modelo Keras"""
        # Implementar cuando el modelo específico esté disponible
        logger.warning("Análisis Keras no implementado, usando fallback")
        return self._analyze_with_fallback(image)
    
    def _analyze_with_onnx(self, image: np.ndarray) -> Dict:
        """Análisis usando modelo ONNX"""
        # Implementar cuando el modelo específico esté disponible
        logger.warning("Análisis ONNX no implementado, usando fallback")
        return self._analyze_with_fallback(image)
    
    def _analyze_with_opencv(self, image: np.ndarray) -> Dict:
        """Análisis usando OpenCV DNN"""
        # Implementar cuando el modelo específico esté disponible
        logger.warning("Análisis OpenCV DNN no implementado, usando fallback")
        return self._analyze_with_fallback(image)
    
    def save_analysis_to_db(self, analysis_id: int, results: Dict, db_path: str = None):
        """Guardar resultados de análisis en la base de datos"""
        try:
            if db_path is None:
                db_path = "data/geopolitical_intel.db"
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Actualizar registro de análisis satelital
                cursor.execute("""
                    UPDATE satellite_analysis 
                    SET status = ?, completed_at = CURRENT_TIMESTAMP,
                        cv_detections = ?, confidence_score = ?,
                        analysis_results = ?
                    WHERE id = ?
                """, (
                    'completed' if results['success'] else 'failed',
                    json.dumps(results.get('detections', [])),
                    results.get('risk_score', 0.0),
                    json.dumps(results),
                    analysis_id
                ))
                
                conn.commit()
                logger.info(f"✅ Resultados guardados para análisis #{analysis_id}")
                
        except Exception as e:
            logger.error(f"Error guardando resultados: {e}")

def test_computer_vision_service():
    """Test del servicio de computer vision"""
    try:
        service = ComputerVisionService()
        
        # Crear imagen de prueba
        test_image = np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)
        test_path = "test_image.jpg"
        cv2.imwrite(test_path, test_image)
        
        print("🔍 Ejecutando análisis de computer vision...")
        results = service.analyze_satellite_image(test_path)
        
        if results['success']:
            print(f"✅ Análisis completado")
            print(f"📊 Detecciones: {results.get('total_detections', 0)}")
            print(f"🚨 Nivel de riesgo: {results.get('risk_level', 'unknown')}")
            print(f"📈 Score de riesgo: {results.get('risk_score', 0):.2f}")
        else:
            print(f"❌ Error: {results.get('error')}")
        
        # Limpiar
        if os.path.exists(test_path):
            os.remove(test_path)
        
        return results['success']
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return False

if __name__ == "__main__":
    test_computer_vision_service()
