"""
Detector de Riesgos en Tiempo Real
=================================

Sistema de detección basado en YOLO + OpenCV para identificar riesgos en streams de video.
Incluye tracking de objetos, análisis de comportamiento y generación de alertas.
"""

import os
import cv2
import numpy as np
import torch
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from pathlib import Path
import json
import threading
import time

# Intentar importar YOLO y Sort
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    print("⚠️ ultralytics no disponible. Usando detector simulado.")
    YOLO_AVAILABLE = False

try:
    from sort import Sort
    SORT_AVAILABLE = True
except ImportError:
    print("⚠️ sort-tracker no disponible. Tracking deshabilitado.")
    SORT_AVAILABLE = False

logger = logging.getLogger(__name__)

class RiskDetector:
    """
    Detector principal de riesgos en video streams
    """
    
    # Clases de riesgo relevantes para conflictos geopolíticos
    RISK_CLASSES = {
        'person': 0,
        'car': 2,
        'truck': 7,
        'bus': 5,
        'motorcycle': 3,
        'bicycle': 1,
        'fire': 99,  # Clase personalizada
        'smoke': 98,  # Clase personalizada
        'explosion': 97,  # Clase personalizada
        'weapon': 96,  # Clase personalizada
        'crowd': 95,  # Clase personalizada
        'military_vehicle': 94  # Clase personalizada
    }
    
    # Umbrales para diferentes tipos de alertas
    ALERT_THRESHOLDS = {
        'manifestation': {
            'min_persons': 50,
            'min_density': 0.15,
            'min_duration': 30  # segundos
        },
        'traffic_jam': {
            'min_vehicles': 30,
            'max_speed': 3,  # km/h
            'min_duration': 30
        },
        'weapon_detection': {
            'confidence': 0.7
        },
        'fire_smoke': {
            'confidence': 0.6,
            'min_area': 0.05  # % del frame
        },
        'crowd_density': {
            'high_density': 0.2,
            'critical_density': 0.35
        }
    }
    
    def __init__(self, model_path: Optional[str] = None, device: str = "auto"):
        """
        Inicializar el detector de riesgos
        
        Args:
            model_path: Ruta al modelo YOLO personalizado
            device: Dispositivo para inferencia (cpu, cuda, auto)
        """
        self.device = self._get_device(device)
        self.model = None
        self.tracker = None
        self.active_detections = {}
        self.alert_history = []
        self.frame_count = 0
        self.fps = int(os.getenv('FPS_ANALYZE', '5'))
        
        # Inicializar modelo y tracker
        self._init_model(model_path)
        self._init_tracker()
        
        # Threading para análisis
        self.detection_lock = threading.Lock()
        self.running = False
        
        logger.info(f"🔴 RiskDetector inicializado en {self.device}")
    
    def _get_device(self, device: str) -> str:
        """Determinar dispositivo optimal para inferencia"""
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            else:
                return "cpu"
        return device
    
    def _init_model(self, model_path: Optional[str] = None):
        """Inicializar modelo YOLO"""
        if not YOLO_AVAILABLE:
            logger.warning("YOLO no disponible, usando detector simulado")
            return
        
        try:
            # Usar modelo por defecto si no se especifica uno personalizado
            if model_path is None:
                model_path = "yolov8n.pt"  # Modelo ligero por defecto
            
            # Verificar si existe modelo personalizado para conflictos
            custom_model = Path("weights/yolo_conflict.pt")
            if custom_model.exists():
                model_path = str(custom_model)
                logger.info("🎯 Usando modelo personalizado para detección de conflictos")
            
            self.model = YOLO(model_path)
            
            # Configurar para device específico
            if self.device == "cuda":
                self.model.to('cuda')
                
            logger.info(f"✅ Modelo YOLO cargado: {model_path}")
            
        except Exception as e:
            logger.error(f"❌ Error cargando modelo YOLO: {e}")
            self.model = None
    
    def _init_tracker(self):
        """Inicializar tracker de objetos"""
        if not SORT_AVAILABLE:
            logger.warning("SORT tracker no disponible")
            return
        
        try:
            self.tracker = Sort(max_age=20, min_hits=3)
            logger.info("✅ Tracker SORT inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando tracker: {e}")
            self.tracker = None
    
    def detect_frame(self, frame: np.ndarray, cam_id: str) -> Dict[str, Any]:
        """
        Detectar riesgos en un frame individual
        
        Args:
            frame: Frame de video como array numpy
            cam_id: ID de la cámara
            
        Returns:
            Diccionario con detecciones y alertas
        """
        if frame is None:
            return {"detections": [], "alerts": [], "tracking": []}
        
        self.frame_count += 1
        
        # Solo procesar cada N frames según FPS configurado
        if self.frame_count % (30 // self.fps) != 0:
            return {"detections": [], "alerts": [], "tracking": []}
        
        try:
            # Realizar detección
            detections = self._run_detection(frame)
            
            # Aplicar tracking si está disponible
            tracked_objects = self._apply_tracking(detections, cam_id)
            
            # Evaluar reglas de alerta
            alerts = self._evaluate_alert_rules(tracked_objects, frame, cam_id)
            
            # Guardar detecciones activas
            with self.detection_lock:
                self.active_detections[cam_id] = {
                    'timestamp': datetime.now(),
                    'detections': detections,
                    'tracking': tracked_objects,
                    'alerts': alerts
                }
            
            return {
                "detections": detections,
                "alerts": alerts,
                "tracking": tracked_objects,
                "frame_info": {
                    "frame_count": self.frame_count,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error en detección para cámara {cam_id}: {e}")
            return {"detections": [], "alerts": [], "tracking": []}
    
    def _run_detection(self, frame: np.ndarray) -> List[Dict]:
        """Ejecutar detección YOLO en el frame"""
        if self.model is None:
            # Detector simulado para desarrollo
            return self._simulate_detections(frame)
        
        try:
            # Ejecutar inferencia YOLO
            results = self.model(frame, verbose=False)
            
            if not results or len(results) == 0:
                return []
            
            # Procesar resultados
            detections = []
            result = results[0]
            
            if result.boxes is not None:
                for box in result.boxes:
                    # Extraer información de la detección
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = float(box.conf[0].cpu().numpy())
                    class_id = int(box.cls[0].cpu().numpy())
                    
                    # Filtrar solo clases relevantes
                    if class_id in self.RISK_CLASSES.values():
                        class_name = self._get_class_name(class_id)
                        
                        detection = {
                            'bbox': [float(x1), float(y1), float(x2), float(y2)],
                            'confidence': confidence,
                            'class_id': class_id,
                            'class_name': class_name,
                            'area': (x2 - x1) * (y2 - y1),
                            'center': [(x1 + x2) / 2, (y1 + y2) / 2]
                        }
                        
                        detections.append(detection)
            
            return detections
            
        except Exception as e:
            logger.error(f"❌ Error en detección YOLO: {e}")
            return []
    
    def _simulate_detections(self, frame: np.ndarray) -> List[Dict]:
        """Simular detecciones para desarrollo/testing"""
        h, w = frame.shape[:2]
        
        # Generar detecciones simuladas basadas en análisis de frame
        detections = []
        
        # Análisis básico de movimiento/cambio
        if hasattr(self, '_prev_frame'):
            diff = cv2.absdiff(frame, self._prev_frame)
            movement = np.sum(diff) / (h * w * 3)
            
            if movement > 5000:  # Umbral de movimiento
                # Simular detección de personas
                detections.append({
                    'bbox': [w*0.3, h*0.4, w*0.7, h*0.9],
                    'confidence': 0.75,
                    'class_id': 0,
                    'class_name': 'person',
                    'area': (w*0.4) * (h*0.5),
                    'center': [w*0.5, h*0.65]
                })
        
        self._prev_frame = frame.copy()
        
        return detections
    
    def _get_class_name(self, class_id: int) -> str:
        """Obtener nombre de clase por ID"""
        class_map = {v: k for k, v in self.RISK_CLASSES.items()}
        return class_map.get(class_id, f'unknown_{class_id}')
    
    def _apply_tracking(self, detections: List[Dict], cam_id: str) -> List[Dict]:
        """Aplicar tracking a las detecciones"""
        if self.tracker is None or not detections:
            return detections
        
        try:
            # Convertir detecciones a formato SORT
            dets = []
            for det in detections:
                bbox = det['bbox']
                conf = det['confidence']
                dets.append([bbox[0], bbox[1], bbox[2], bbox[3], conf])
            
            dets = np.array(dets)
            
            # Aplicar tracking
            tracked = self.tracker.update(dets)
            
            # Actualizar detecciones con IDs de tracking
            tracked_detections = []
            for i, det in enumerate(detections):
                if i < len(tracked):
                    det['track_id'] = int(tracked[i][4])
                else:
                    det['track_id'] = -1
                tracked_detections.append(det)
            
            return tracked_detections
            
        except Exception as e:
            logger.error(f"❌ Error en tracking: {e}")
            return detections
    
    def _evaluate_alert_rules(self, detections: List[Dict], frame: np.ndarray, cam_id: str) -> List[Dict]:
        """Evaluar reglas de alerta basadas en detecciones"""
        alerts = []
        
        if not detections:
            return alerts
        
        h, w = frame.shape[:2]
        frame_area = h * w
        
        # Contar tipos de objetos
        person_count = len([d for d in detections if d['class_name'] == 'person'])
        vehicle_count = len([d for d in detections if d['class_name'] in ['car', 'truck', 'bus']])
        
        # Regla 1: Detección de manifestación/multitudes
        if person_count >= self.ALERT_THRESHOLDS['manifestation']['min_persons']:
            # Calcular densidad
            person_area = sum([d['area'] for d in detections if d['class_name'] == 'person'])
            density = person_area / frame_area
            
            if density >= self.ALERT_THRESHOLDS['manifestation']['min_density']:
                alerts.append({
                    'type': 'manifestation',
                    'severity': 'high' if person_count > 100 else 'medium',
                    'description': f'Posible manifestación detectada: {person_count} personas',
                    'confidence': min(0.9, density * 2),
                    'location': cam_id,
                    'timestamp': datetime.now().isoformat(),
                    'metadata': {
                        'person_count': person_count,
                        'density': density,
                        'frame_coverage': person_area / frame_area
                    }
                })
        
        # Regla 2: Detección de armas
        weapon_detections = [d for d in detections if d['class_name'] == 'weapon']
        for weapon in weapon_detections:
            if weapon['confidence'] >= self.ALERT_THRESHOLDS['weapon_detection']['confidence']:
                alerts.append({
                    'type': 'weapon_detected',
                    'severity': 'critical',
                    'description': 'Arma detectada en el área',
                    'confidence': weapon['confidence'],
                    'location': cam_id,
                    'timestamp': datetime.now().isoformat(),
                    'metadata': {
                        'bbox': weapon['bbox'],
                        'weapon_type': 'unknown'
                    }
                })
        
        # Regla 3: Detección de humo/fuego
        fire_smoke = [d for d in detections if d['class_name'] in ['fire', 'smoke']]
        for fs in fire_smoke:
            area_ratio = fs['area'] / frame_area
            if (fs['confidence'] >= self.ALERT_THRESHOLDS['fire_smoke']['confidence'] and
                area_ratio >= self.ALERT_THRESHOLDS['fire_smoke']['min_area']):
                
                alerts.append({
                    'type': 'fire_smoke',
                    'severity': 'high',
                    'description': f'Detección de {fs["class_name"]}',
                    'confidence': fs['confidence'],
                    'location': cam_id,
                    'timestamp': datetime.now().isoformat(),
                    'metadata': {
                        'type': fs['class_name'],
                        'area_coverage': area_ratio,
                        'bbox': fs['bbox']
                    }
                })
        
        # Regla 4: Atasco de tráfico (simplificado)
        if vehicle_count >= self.ALERT_THRESHOLDS['traffic_jam']['min_vehicles']:
            # Análisis simplificado de densidad vehicular
            vehicle_area = sum([d['area'] for d in detections if d['class_name'] in ['car', 'truck', 'bus']])
            vehicle_density = vehicle_area / frame_area
            
            if vehicle_density > 0.3:  # Alta densidad vehicular
                alerts.append({
                    'type': 'traffic_jam',
                    'severity': 'medium',
                    'description': f'Posible atasco de tráfico: {vehicle_count} vehículos',
                    'confidence': min(0.8, vehicle_density * 1.5),
                    'location': cam_id,
                    'timestamp': datetime.now().isoformat(),
                    'metadata': {
                        'vehicle_count': vehicle_count,
                        'density': vehicle_density
                    }
                })
        
        # Guardar alertas en historial
        for alert in alerts:
            self.alert_history.append(alert)
            
        # Mantener solo últimas 100 alertas
        self.alert_history = self.alert_history[-100:]
        
        return alerts
    
    def get_active_detections(self, cam_id: Optional[str] = None) -> Dict:
        """Obtener detecciones activas"""
        with self.detection_lock:
            if cam_id:
                return self.active_detections.get(cam_id, {})
            return self.active_detections.copy()
    
    def get_alert_history(self, limit: int = 20, cam_id: Optional[str] = None) -> List[Dict]:
        """Obtener historial de alertas"""
        alerts = self.alert_history[-limit:]
        
        if cam_id:
            alerts = [a for a in alerts if a.get('location') == cam_id]
        
        return alerts
    
    def get_statistics(self) -> Dict:
        """Obtener estadísticas del detector"""
        return {
            'frames_processed': self.frame_count,
            'active_cameras': len(self.active_detections),
            'total_alerts': len(self.alert_history),
            'recent_alerts': len([a for a in self.alert_history 
                                 if datetime.fromisoformat(a['timestamp']) > 
                                 datetime.now() - timedelta(hours=1)]),
            'device': self.device,
            'fps_target': self.fps,
            'model_loaded': self.model is not None,
            'tracker_enabled': self.tracker is not None
        }
    
    def cleanup(self):
        """Limpiar recursos del detector"""
        self.running = False
        if hasattr(self, 'model') and self.model:
            del self.model
        if hasattr(self, 'tracker') and self.tracker:
            del self.tracker
        logger.info("🔴 RiskDetector limpiado")


class ColorBasedSmokeDetector:
    """
    Detector de humo basado en análisis de color
    Complemento al detector YOLO para casos específicos
    """
    
    def __init__(self):
        # Rangos HSV para detección de humo
        self.smoke_hsv_range = [
            (np.array([0, 0, 50]), np.array([180, 50, 200]))  # Gris-blanco
        ]
    
    def detect_smoke(self, frame: np.ndarray) -> Tuple[bool, float, Optional[np.ndarray]]:
        """
        Detectar humo usando análisis de color
        
        Returns:
            (smoke_detected, confidence, mask)
        """
        try:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Crear máscara para colores de humo
            mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
            
            for lower, upper in self.smoke_hsv_range:
                color_mask = cv2.inRange(hsv, lower, upper)
                mask = cv2.bitwise_or(mask, color_mask)
            
            # Filtrar ruido
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            
            # Calcular área de humo
            smoke_area = cv2.countNonZero(mask)
            total_area = frame.shape[0] * frame.shape[1]
            coverage = smoke_area / total_area
            
            # Determinar si hay humo
            smoke_detected = coverage > 0.05  # 5% del frame
            confidence = min(1.0, coverage * 10)  # Normalizar confianza
            
            return smoke_detected, confidence, mask
            
        except Exception as e:
            logger.error(f"❌ Error en detección de humo: {e}")
            return False, 0.0, None


if __name__ == "__main__":
    # Test del detector
    detector = RiskDetector()
    print(f"Estadísticas iniciales: {detector.get_statistics()}")
