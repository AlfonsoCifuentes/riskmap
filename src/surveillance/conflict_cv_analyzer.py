"""
Conflict Indicator Analyzer using Computer Vision
=================================================

Analizador avanzado de Computer Vision para detectar automáticamente indicadores
de conflictos geopolíticos en streams de video y capturas de cámaras públicas.

Features:
- Detección de vehículos militares
- Identificación de columnas de humo/explosiones
- Análisis de multitudes y disturbios
- Detección de daños en infraestructura
- Clasificación de riesgo automática
- Generación de alertas inteligentes
"""

import os
import cv2
import torch
import numpy as np
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class ConflictDetection:
    """Representa una detección de indicador de conflicto"""
    detection_type: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x, y, w, h
    description: str
    risk_level: str
    timestamp: datetime
    additional_info: Dict = None

@dataclass
class FrameAnalysis:
    """Resultado completo del análisis de un frame"""
    frame_id: str
    timestamp: datetime
    detections: List[ConflictDetection]
    overall_risk_score: float
    overall_risk_level: str
    summary: str
    indicators_count: int
    processing_time: float
    metadata: Dict = None

class ConflictIndicatorAnalyzer:
    """
    Analizador de Computer Vision para indicadores de conflicto
    """
    
    def __init__(self, db_path: str = "./data/geopolitical_intel.db"):
        self.db_path = db_path
        
        # Configuración de modelos
        self.device = self._get_device()
        self.models = {}
        
        # Cargar modelos de detección
        self._load_models()
        
        # Configuración de detección
        self.detection_config = {
            'confidence_threshold': 0.3,
            'nms_threshold': 0.4,
            'max_detections_per_frame': 50,
            'risk_thresholds': {
                'low': 0.3,
                'medium': 0.6,
                'high': 0.8
            }
        }
        
        # Clases de objetos relacionados con conflictos
        self.conflict_classes = {
            # Vehículos militares
            'tank': {'risk_multiplier': 1.0, 'base_risk': 0.9, 'category': 'military_vehicle'},
            'military_truck': {'risk_multiplier': 0.8, 'base_risk': 0.7, 'category': 'military_vehicle'},
            'armored_vehicle': {'risk_multiplier': 0.9, 'base_risk': 0.8, 'category': 'military_vehicle'},
            'military_helicopter': {'risk_multiplier': 1.0, 'base_risk': 0.9, 'category': 'military_aircraft'},
            
            # Indicadores de violencia
            'fire': {'risk_multiplier': 0.9, 'base_risk': 0.8, 'category': 'destruction'},
            'smoke': {'risk_multiplier': 0.7, 'base_risk': 0.6, 'category': 'destruction'},
            'explosion': {'risk_multiplier': 1.0, 'base_risk': 1.0, 'category': 'destruction'},
            
            # Multitudes y disturbios
            'crowd': {'risk_multiplier': 0.6, 'base_risk': 0.5, 'category': 'civil_unrest'},
            'protest': {'risk_multiplier': 0.7, 'base_risk': 0.6, 'category': 'civil_unrest'},
            
            # Infraestructura dañada
            'destroyed_building': {'risk_multiplier': 0.8, 'base_risk': 0.7, 'category': 'infrastructure'},
            'debris': {'risk_multiplier': 0.5, 'base_risk': 0.4, 'category': 'infrastructure'},
            
            # Equipamiento militar
            'weapon': {'risk_multiplier': 0.8, 'base_risk': 0.7, 'category': 'weapons'},
            'ammunition': {'risk_multiplier': 0.9, 'base_risk': 0.8, 'category': 'weapons'}
        }
        
        logger.info(f"🤖 Analizador CV inicializado en dispositivo: {self.device}")
    
    def _get_device(self) -> str:
        """Determinar el mejor dispositivo disponible"""
        if torch.cuda.is_available():
            return 'cuda'
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return 'mps'
        else:
            return 'cpu'
    
    def _load_models(self):
        """Cargar modelos de detección"""
        try:
            # Modelo YOLO principal para detección de objetos
            self._load_yolo_model()
            
            # Modelo especializado para detección de humo y fuego
            self._load_fire_smoke_model()
            
            # Modelo para análisis de multitudes
            self._load_crowd_analysis_model()
            
            logger.info("✅ Modelos de CV cargados exitosamente")
            
        except Exception as e:
            logger.error(f"❌ Error cargando modelos CV: {e}")
            # Configurar modo fallback
            self._setup_fallback_mode()
    
    def _load_yolo_model(self):
        """Cargar modelo YOLO para detección general"""
        try:
            # Intentar cargar YOLOv8 o YOLOv5
            try:
                import ultralytics
                self.models['yolo'] = ultralytics.YOLO('yolov8n.pt')
                logger.info("✅ YOLOv8 cargado")
            except ImportError:
                # Fallback a YOLOv5
                self.models['yolo'] = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
                logger.info("✅ YOLOv5 cargado como fallback")
                
        except Exception as e:
            logger.error(f"Error cargando YOLO: {e}")
            self.models['yolo'] = None
    
    def _load_fire_smoke_model(self):
        """Cargar modelo especializado para detección de fuego y humo"""
        # En una implementación completa, aquí se cargaría un modelo especializado
        # Por ahora, usamos detección basada en color y texturas
        self.models['fire_smoke'] = self._create_fire_smoke_detector()
        logger.info("✅ Detector de fuego/humo inicializado")
    
    def _load_crowd_analysis_model(self):
        """Cargar modelo para análisis de multitudes"""
        # Detector básico de densidad de personas
        self.models['crowd'] = self._create_crowd_detector()
        logger.info("✅ Detector de multitudes inicializado")
    
    def _create_fire_smoke_detector(self):
        """Crear detector de fuego y humo basado en OpenCV"""
        return {
            'fire_color_ranges': [
                {'lower': np.array([0, 50, 50]), 'upper': np.array([10, 255, 255])},    # Rojo-Naranja
                {'lower': np.array([170, 50, 50]), 'upper': np.array([180, 255, 255])}  # Rojo
            ],
            'smoke_color_ranges': [
                {'lower': np.array([0, 0, 50]), 'upper': np.array([180, 30, 200])}     # Gris
            ]
        }
    
    def _create_crowd_detector(self):
        """Crear detector básico de multitudes"""
        return {
            'person_cascade': cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_fullbody.xml'),
            'face_cascade': cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        }
    
    def _setup_fallback_mode(self):
        """Configurar modo fallback cuando los modelos no están disponibles"""
        logger.warning("⚠️ Configurando modo fallback para análisis CV")
        self.models = {
            'yolo': None,
            'fire_smoke': self._create_fire_smoke_detector(),
            'crowd': self._create_crowd_detector(),
            'fallback_mode': True
        }
    
    def analyze_frame(self, frame: np.ndarray, camera_id: str = None) -> FrameAnalysis:
        """
        Analizar un frame completo para detectar indicadores de conflicto
        """
        start_time = datetime.now()
        frame_id = f"{camera_id}_{start_time.timestamp()}" if camera_id else f"frame_{start_time.timestamp()}"
        
        try:
            detections = []
            
            # Análisis con YOLO si está disponible
            if self.models.get('yolo'):
                yolo_detections = self._analyze_with_yolo(frame)
                detections.extend(yolo_detections)
            
            # Análisis de fuego y humo
            fire_smoke_detections = self._detect_fire_smoke(frame)
            detections.extend(fire_smoke_detections)
            
            # Análisis de multitudes
            crowd_detections = self._detect_crowds(frame)
            detections.extend(crowd_detections)
            
            # Análisis de patrones de movimiento
            movement_detections = self._analyze_movement_patterns(frame)
            detections.extend(movement_detections)
            
            # Calcular riesgo general
            overall_risk_score = self._calculate_overall_risk(detections)
            overall_risk_level = self._get_risk_level(overall_risk_score)
            
            # Generar resumen
            summary = self._generate_analysis_summary(detections, overall_risk_score)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            analysis = FrameAnalysis(
                frame_id=frame_id,
                timestamp=start_time,
                detections=detections,
                overall_risk_score=overall_risk_score,
                overall_risk_level=overall_risk_level,
                summary=summary,
                indicators_count=len(detections),
                processing_time=processing_time,
                metadata={
                    'frame_shape': frame.shape,
                    'camera_id': camera_id,
                    'models_used': list(self.models.keys())
                }
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analizando frame: {e}")
            # Retornar análisis vacío en caso de error
            return FrameAnalysis(
                frame_id=frame_id,
                timestamp=start_time,
                detections=[],
                overall_risk_score=0.0,
                overall_risk_level='low',
                summary="Error en análisis de frame",
                indicators_count=0,
                processing_time=(datetime.now() - start_time).total_seconds(),
                metadata={'error': str(e)}
            )
    
    def _analyze_with_yolo(self, frame: np.ndarray) -> List[ConflictDetection]:
        """Analizar frame con modelo YOLO"""
        detections = []
        
        try:
            # Ejecutar inferencia YOLO
            results = self.models['yolo'](frame)
            
            # Procesar resultados (formato puede variar según versión de YOLO)
            if hasattr(results, 'pandas'):
                # YOLOv5 format
                df = results.pandas().xyxy[0]
                for _, row in df.iterrows():
                    detection = self._process_yolo_detection(row)
                    if detection:
                        detections.append(detection)
            else:
                # YOLOv8 format
                for result in results:
                    boxes = result.boxes
                    if boxes is not None:
                        for box in boxes:
                            detection = self._process_yolo_detection_v8(box, result.names)
                            if detection:
                                detections.append(detection)
                                
        except Exception as e:
            logger.error(f"Error en análisis YOLO: {e}")
        
        return detections
    
    def _process_yolo_detection(self, detection) -> Optional[ConflictDetection]:
        """Procesar detección individual de YOLO (v5)"""
        try:
            class_name = detection['name'].lower()
            confidence = float(detection['confidence'])
            
            # Filtrar solo clases relacionadas con conflictos
            if class_name in self.conflict_classes and confidence > self.detection_config['confidence_threshold']:
                class_info = self.conflict_classes[class_name]
                
                risk_score = min(1.0, confidence * class_info['risk_multiplier'] * class_info['base_risk'])
                risk_level = self._get_risk_level(risk_score)
                
                return ConflictDetection(
                    detection_type=class_name,
                    confidence=confidence,
                    bbox=(int(detection['xmin']), int(detection['ymin']), 
                          int(detection['xmax'] - detection['xmin']), 
                          int(detection['ymax'] - detection['ymin'])),
                    description=f"{class_name.replace('_', ' ').title()} detectado",
                    risk_level=risk_level,
                    timestamp=datetime.now(),
                    additional_info={'category': class_info['category'], 'source': 'yolo'}
                )
        except Exception as e:
            logger.error(f"Error procesando detección YOLO: {e}")
        
        return None
    
    def _process_yolo_detection_v8(self, box, names) -> Optional[ConflictDetection]:
        """Procesar detección individual de YOLO (v8)"""
        try:
            class_id = int(box.cls.cpu().numpy()[0])
            confidence = float(box.conf.cpu().numpy()[0])
            class_name = names[class_id].lower()
            
            # Mapear nombres de clases YOLO estándar a nuestras clases de conflicto
            mapped_class = self._map_yolo_class_to_conflict(class_name)
            
            if mapped_class and confidence > self.detection_config['confidence_threshold']:
                class_info = self.conflict_classes[mapped_class]
                
                risk_score = min(1.0, confidence * class_info['risk_multiplier'] * class_info['base_risk'])
                risk_level = self._get_risk_level(risk_score)
                
                coords = box.xyxy.cpu().numpy()[0]
                
                return ConflictDetection(
                    detection_type=mapped_class,
                    confidence=confidence,
                    bbox=(int(coords[0]), int(coords[1]), 
                          int(coords[2] - coords[0]), 
                          int(coords[3] - coords[1])),
                    description=f"{mapped_class.replace('_', ' ').title()} detectado",
                    risk_level=risk_level,
                    timestamp=datetime.now(),
                    additional_info={'category': class_info['category'], 'source': 'yolo', 'original_class': class_name}
                )
        except Exception as e:
            logger.error(f"Error procesando detección YOLOv8: {e}")
        
        return None
    
    def _map_yolo_class_to_conflict(self, yolo_class: str) -> Optional[str]:
        """Mapear clases YOLO estándar a clases de conflicto"""
        mappings = {
            'truck': 'military_truck',
            'car': None,  # Ignorar coches normales
            'person': 'crowd',  # Se agrupará en análisis de multitudes
            'fire hydrant': None,
            'bus': None,
            'train': None,
            'airplane': 'military_helicopter',  # Asumir militar en zona de conflicto
            'boat': None
        }
        
        return mappings.get(yolo_class)
    
    def _detect_fire_smoke(self, frame: np.ndarray) -> List[ConflictDetection]:
        """Detectar fuego y humo usando análisis de color"""
        detections = []
        
        try:
            # Convertir a HSV para mejor detección de color
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Detectar fuego
            fire_detections = self._detect_color_based(hsv, 'fire', 
                                                     self.models['fire_smoke']['fire_color_ranges'])
            detections.extend(fire_detections)
            
            # Detectar humo
            smoke_detections = self._detect_color_based(hsv, 'smoke',
                                                      self.models['fire_smoke']['smoke_color_ranges'])
            detections.extend(smoke_detections)
            
        except Exception as e:
            logger.error(f"Error detectando fuego/humo: {e}")
        
        return detections
    
    def _detect_color_based(self, hsv_frame: np.ndarray, detection_type: str, color_ranges: List[Dict]) -> List[ConflictDetection]:
        """Detectar objetos basándose en rangos de color"""
        detections = []
        
        try:
            for color_range in color_ranges:
                # Crear máscara para el rango de color
                mask = cv2.inRange(hsv_frame, color_range['lower'], color_range['upper'])
                
                # Encontrar contornos
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    area = cv2.contourArea(contour)
                    
                    # Filtrar por tamaño mínimo
                    if area > 500:  # Área mínima para considerar detección válida
                        x, y, w, h = cv2.boundingRect(contour)
                        
                        # Calcular confianza basada en área y forma
                        confidence = min(0.9, area / 10000.0)  # Máximo 0.9
                        
                        if confidence > 0.3:
                            risk_score = confidence * self.conflict_classes[detection_type]['base_risk']
                            risk_level = self._get_risk_level(risk_score)
                            
                            detections.append(ConflictDetection(
                                detection_type=detection_type,
                                confidence=confidence,
                                bbox=(x, y, w, h),
                                description=f"{detection_type.title()} detectado por análisis de color",
                                risk_level=risk_level,
                                timestamp=datetime.now(),
                                additional_info={'area': area, 'source': 'color_analysis'}
                            ))
                            
        except Exception as e:
            logger.error(f"Error en detección por color: {e}")
        
        return detections
    
    def _detect_crowds(self, frame: np.ndarray) -> List[ConflictDetection]:
        """Detectar multitudes y posibles disturbios"""
        detections = []
        
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detectar personas usando cascadas Haar
            bodies = self.models['crowd']['person_cascade'].detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=3, minSize=(30, 30)
            )
            
            faces = self.models['crowd']['face_cascade'].detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=3, minSize=(20, 20)
            )
            
            # Contar detecciones
            total_people = len(bodies) + len(faces)
            
            if total_people > 5:  # Umbral para considerar multitud
                # Determinar tipo de multitud
                crowd_density = total_people / (frame.shape[0] * frame.shape[1]) * 1000000  # Por millón de píxeles
                
                if crowd_density > 50:
                    detection_type = 'protest'
                    confidence = min(0.8, crowd_density / 100)
                else:
                    detection_type = 'crowd'
                    confidence = min(0.6, crowd_density / 50)
                
                # Crear bbox que englobe todas las detecciones
                if len(bodies) > 0 or len(faces) > 0:
                    all_boxes = list(bodies) + list(faces)
                    x_min = min([box[0] for box in all_boxes])
                    y_min = min([box[1] for box in all_boxes])
                    x_max = max([box[0] + box[2] for box in all_boxes])
                    y_max = max([box[1] + box[3] for box in all_boxes])
                    
                    risk_score = confidence * self.conflict_classes[detection_type]['base_risk']
                    risk_level = self._get_risk_level(risk_score)
                    
                    detections.append(ConflictDetection(
                        detection_type=detection_type,
                        confidence=confidence,
                        bbox=(x_min, y_min, x_max - x_min, y_max - y_min),
                        description=f"Multitud de {total_people} personas detectada",
                        risk_level=risk_level,
                        timestamp=datetime.now(),
                        additional_info={
                            'people_count': total_people,
                            'density': crowd_density,
                            'source': 'haar_cascade'
                        }
                    ))
                    
        except Exception as e:
            logger.error(f"Error detectando multitudes: {e}")
        
        return detections
    
    def _analyze_movement_patterns(self, frame: np.ndarray) -> List[ConflictDetection]:
        """Análisis básico de patrones de movimiento (requiere frames previos)"""
        # Por ahora retorna lista vacía
        # En implementación completa, se analizaría flujo óptico y patrones de movimiento
        return []
    
    def _calculate_overall_risk(self, detections: List[ConflictDetection]) -> float:
        """Calcular puntuación general de riesgo del frame"""
        if not detections:
            return 0.0
        
        # Calcular riesgo ponderado
        total_risk = 0.0
        max_risk = 0.0
        
        for detection in detections:
            detection_risk = detection.confidence * self.conflict_classes.get(detection.detection_type, {}).get('base_risk', 0.5)
            total_risk += detection_risk
            max_risk = max(max_risk, detection_risk)
        
        # Combinación de riesgo total y máximo
        combined_risk = (total_risk / len(detections) * 0.7) + (max_risk * 0.3)
        
        return min(1.0, combined_risk)
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Convertir puntuación numérica a nivel de riesgo"""
        thresholds = self.detection_config['risk_thresholds']
        
        if risk_score >= thresholds['high']:
            return 'high'
        elif risk_score >= thresholds['medium']:
            return 'medium'
        else:
            return 'low'
    
    def _generate_analysis_summary(self, detections: List[ConflictDetection], risk_score: float) -> str:
        """Generar resumen del análisis"""
        if not detections:
            return "No se detectaron indicadores de conflicto"
        
        # Agrupar por categoría
        categories = {}
        for detection in detections:
            category = detection.additional_info.get('category', 'unknown') if detection.additional_info else 'unknown'
            if category not in categories:
                categories[category] = []
            categories[category].append(detection)
        
        summary_parts = []
        
        for category, cat_detections in categories.items():
            count = len(cat_detections)
            max_confidence = max([d.confidence for d in cat_detections])
            
            category_names = {
                'military_vehicle': 'vehículos militares',
                'military_aircraft': 'aeronaves militares',
                'destruction': 'signos de destrucción',
                'civil_unrest': 'disturbios civiles',
                'infrastructure': 'daños en infraestructura',
                'weapons': 'armamento'
            }
            
            category_name = category_names.get(category, category)
            summary_parts.append(f"{count} {category_name} (confianza máx: {max_confidence:.2f})")
        
        base_summary = f"Detectados: {', '.join(summary_parts)}"
        
        # Agregar evaluación de riesgo
        risk_evaluation = f"Riesgo general: {self._get_risk_level(risk_score)} ({risk_score:.2f})"
        
        return f"{base_summary}. {risk_evaluation}"
    
    def analyze_stream_batch(self, frames: List[np.ndarray], camera_id: str = None) -> List[FrameAnalysis]:
        """Analizar un lote de frames de un stream"""
        analyses = []
        
        for i, frame in enumerate(frames):
            try:
                frame_analysis = self.analyze_frame(frame, f"{camera_id}_frame_{i}" if camera_id else f"batch_frame_{i}")
                analyses.append(frame_analysis)
            except Exception as e:
                logger.error(f"Error analizando frame {i}: {e}")
        
        return analyses
    
    def save_analysis_to_db(self, analysis: FrameAnalysis, camera_id: str = None, capture_path: str = None) -> bool:
        """Guardar análisis en base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Guardar captura
            cursor.execute('''
                INSERT INTO auto_captures (
                    camera_id, capture_path, timestamp, cv_analysis,
                    risk_score, indicators_detected, alert_generated,
                    conflict_indicators, frame_analysis
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                camera_id,
                capture_path,
                analysis.timestamp,
                analysis.summary,
                analysis.overall_risk_score,
                json.dumps([{
                    'type': d.detection_type,
                    'confidence': d.confidence,
                    'bbox': d.bbox,
                    'description': d.description
                } for d in analysis.detections]),
                analysis.overall_risk_level in ['medium', 'high'],  # Generar alerta para riesgo medio/alto
                json.dumps([d.detection_type for d in analysis.detections]),
                json.dumps({
                    'frame_id': analysis.frame_id,
                    'indicators_count': analysis.indicators_count,
                    'processing_time': analysis.processing_time,
                    'metadata': analysis.metadata
                })
            ))
            
            capture_id = cursor.lastrowid
            
            # Generar alerta si es necesario
            if analysis.overall_risk_level in ['medium', 'high']:
                cursor.execute('''
                    INSERT INTO conflict_alerts (
                        camera_id, capture_id, alert_type, severity_level,
                        description, timestamp, acknowledged, confidence_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    camera_id,
                    capture_id,
                    'conflict_indicators',
                    analysis.overall_risk_level,
                    analysis.summary,
                    analysis.timestamp,
                    False,
                    analysis.overall_risk_score
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"💾 Análisis guardado para frame {analysis.frame_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando análisis: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """Obtener estadísticas del analizador"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Estadísticas generales
            cursor.execute("SELECT COUNT(*) FROM auto_captures")
            total_captures = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM auto_captures WHERE alert_generated = 1")
            captures_with_alerts = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM conflict_alerts")
            total_alerts = cursor.fetchone()[0]
            
            # Alertas por severidad
            cursor.execute('''
                SELECT severity_level, COUNT(*) 
                FROM conflict_alerts 
                GROUP BY severity_level
            ''')
            alerts_by_severity = dict(cursor.fetchall())
            
            # Indicadores más comunes
            cursor.execute('''
                SELECT conflict_indicators, COUNT(*) as freq
                FROM auto_captures 
                WHERE conflict_indicators IS NOT NULL 
                AND conflict_indicators != '[]'
                GROUP BY conflict_indicators
                ORDER BY freq DESC
                LIMIT 10
            ''')
            common_indicators = []
            for row in cursor.fetchall():
                try:
                    indicators = json.loads(row[0])
                    common_indicators.append({'indicators': indicators, 'frequency': row[1]})
                except Exception:
                    pass
            
            conn.close()
            
            return {
                'total_captures_analyzed': total_captures,
                'captures_with_alerts': captures_with_alerts,
                'total_alerts_generated': total_alerts,
                'alert_rate': (captures_with_alerts / total_captures * 100) if total_captures > 0 else 0,
                'alerts_by_severity': alerts_by_severity,
                'common_indicators': common_indicators,
                'models_loaded': list(self.models.keys()),
                'device': self.device,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}

# Función principal para testing
def main():
    """Función principal para testing"""
    analyzer = ConflictIndicatorAnalyzer()
    
    # Crear frame de prueba
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Analizar frame
    analysis = analyzer.analyze_frame(test_frame, "test_camera")
    
    print(f"\n🤖 Análisis CV completado:")
    print(f"  • Frame ID: {analysis.frame_id}")
    print(f"  • Detecciones: {analysis.indicators_count}")
    print(f"  • Riesgo: {analysis.overall_risk_level} ({analysis.overall_risk_score:.2f})")
    print(f"  • Tiempo: {analysis.processing_time:.2f}s")
    print(f"  • Resumen: {analysis.summary}")
    
    # Mostrar estadísticas
    stats = analyzer.get_statistics()
    print(f"\n📊 Estadísticas del analizador:")
    print(f"  • Device: {stats.get('device', 'unknown')}")
    print(f"  • Modelos: {', '.join(stats.get('models_loaded', []))}")

if __name__ == "__main__":
    main()