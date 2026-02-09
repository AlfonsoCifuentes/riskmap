"""
Public Camera Surveillance System Routes
========================================

Sistema avanzado de rutas Flask para videovigilancia en zonas de conflicto:
- API REST para cámaras públicas gelocalizadas
- Streaming en tiempo real con análisis CV
- Sistema de alertas automatizado
- Captura inteligente adaptativa
- Dashboard moderno y responsivo
"""

import os
import json
import cv2
import base64
import threading
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from flask import Blueprint, request, jsonify, render_template, send_file, Response, stream_template
from flask_socketio import SocketIO, emit, join_room, leave_room
import numpy as np
from pathlib import Path
import sqlite3

# Configurar logger
logger = logging.getLogger(__name__)

# Importar módulos del sistema de videovigilancia
try:
    from src.surveillance.public_camera_detector import PublicCameraDetector
    from src.surveillance.conflict_cv_analyzer import ConflictIndicatorAnalyzer
    from src.surveillance.smart_capture_system import SmartCaptureSystem
    SURVEILLANCE_AVAILABLE = True
    logger.info("✅ Módulos de videovigilancia cargados correctamente")
except ImportError as e:
    logger.error(f"❌ Error cargando módulos de videovigilancia: {e}")
    SURVEILLANCE_AVAILABLE = False
    
    # Crear clases mock para compatibilidad
    class PublicCameraDetector:
        def __init__(self, db_path): pass
        def get_all_conflict_zone_cameras(self): return []
        def get_cameras_for_location(self, lat, lon, radius): return []
    
    class ConflictIndicatorAnalyzer:
        def __init__(self, db_path): pass
        def analyze_frame(self, frame, camera_id): return None
    
    class SmartCaptureSystem:
        def __init__(self, db_path=None): pass
        def start_monitoring(self): return False
        def stop_monitoring(self): pass
        def get_capture_statistics(self): return {}

# Crear Blueprint
surveillance_bp = Blueprint('surveillance', __name__, url_prefix='/video-surveillance')

# Variables globales para instancias del sistema
camera_detector: Optional[PublicCameraDetector] = None
cv_analyzer: Optional[ConflictIndicatorAnalyzer] = None
capture_system: Optional[SmartCaptureSystem] = None
socketio: Optional[SocketIO] = None

# Estado de streams activos
active_streams = {}
stream_lock = threading.Lock()
active_rooms = set()

def init_surveillance_system(app_socketio: SocketIO, db_path: str = "./data/geopolitical_intel.db"):
    """
    Inicializar sistema completo de videovigilancia
    
    Args:
        app_socketio: Instancia de SocketIO de Flask
        db_path: Ruta a la base de datos
    
    Returns:
        bool: True si se inicializó correctamente
    """
    global camera_detector, cv_analyzer, capture_system, socketio
    
    try:
        logger.info("🚀 Inicializando sistema de videovigilancia...")
        
        # Guardar referencia a socketio
        socketio = app_socketio
        
        if not SURVEILLANCE_AVAILABLE:
            logger.error("❌ Módulos de videovigilancia no disponibles")
            return False
        
        # Inicializar componentes
        camera_detector = PublicCameraDetector(db_path)
        cv_analyzer = ConflictIndicatorAnalyzer(db_path)
        capture_system = SmartCaptureSystem(db_path)
        
        # Configurar callback para notificaciones en tiempo real
        capture_system.add_notification_callback(_handle_capture_notification)
        
        logger.info("✅ Sistema de videovigilancia inicializado correctamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error inicializando sistema de videovigilancia: {e}")
        return False

def _handle_capture_notification(result):
    """Manejar notificaciones de captura para WebSocket"""
    try:
        if socketio and result.analysis and result.analysis.overall_risk_level in ['medium', 'high']:
            # Emitir alerta en tiempo real
            alert_data = {
                'camera_id': result.camera_id,
                'timestamp': result.timestamp.isoformat(),
                'risk_level': result.analysis.overall_risk_level,
                'risk_score': result.analysis.overall_risk_score,
                'summary': result.analysis.summary,
                'detections': len(result.analysis.detections),
                'capture_path': result.capture_path
            }
            
            socketio.emit('real_time_alert', alert_data, namespace='/surveillance')
            logger.info(f"📡 Alerta en tiempo real emitida: {result.camera_id}")
            
    except Exception as e:
        logger.error(f"Error enviando notificación en tiempo real: {e}")

# =============================================================================
# RUTAS PRINCIPALES DEL DASHBOARD
# =============================================================================

@surveillance_bp.route('/')
def surveillance_dashboard():
    """Página principal del dashboard de videovigilancia"""
    try:
        return render_template('surveillance/dashboard.html', 
                             title="Video Surveillance - Conflict Zones")
    except Exception as e:
        logger.error(f"Error cargando dashboard: {e}")
        return jsonify({'error': 'Error loading dashboard'}), 500

@surveillance_bp.route('/cameras')
def cameras_view():
    """Vista de cámaras activas"""
    try:
        return render_template('surveillance/cameras.html',
                             title="Public Cameras - Live View")
    except Exception as e:
        logger.error(f"Error cargando vista de cámaras: {e}")
        return jsonify({'error': 'Error loading cameras view'}), 500

@surveillance_bp.route('/alerts')
def alerts_view():
    """Vista de alertas y análisis"""
    try:
        return render_template('surveillance/alerts.html',
                             title="Conflict Alerts & Analysis")
    except Exception as e:
        logger.error(f"Error cargando vista de alertas: {e}")
        return jsonify({'error': 'Error loading alerts view'}), 500

# =============================================================================
# API ENDPOINTS - CÁMARAS
# =============================================================================

@surveillance_bp.route('/api/cameras/conflict-zones')
def get_conflict_zone_cameras():
    """Obtener todas las cámaras en zonas de conflicto"""
    try:
        if not camera_detector:
            return jsonify({'error': 'Camera detector not initialized'}), 503
        
        cameras = camera_detector.get_all_conflict_zone_cameras()
        
        # Enriquecer con estado actual
        enriched_cameras = []
        for camera in cameras:
            camera_id = camera.get('camera_id')
            
            # Obtener estado del sistema de captura
            camera_status = {}
            if capture_system:
                camera_status = capture_system.get_camera_status(camera_id)
            
            enriched_camera = {
                **camera,
                'status': camera_status,
                'is_active': camera_status.get('thread_active', False),
                'last_capture': camera_status.get('last_capture'),
                'current_interval': camera_status.get('current_interval')
            }
            
            enriched_cameras.append(enriched_camera)
        
        return jsonify({
            'success': True,
            'count': len(enriched_cameras),
            'cameras': enriched_cameras,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo cámaras de zonas de conflicto: {e}")
        return jsonify({'error': str(e)}), 500

@surveillance_bp.route('/api/cameras/location')
def get_cameras_by_location():
    """Obtener cámaras por ubicación geográfica"""
    try:
        lat = float(request.args.get('lat', 0))
        lon = float(request.args.get('lon', 0))
        radius = float(request.args.get('radius', 50))  # km
        
        if not camera_detector:
            return jsonify({'error': 'Camera detector not initialized'}), 503
        
        cameras = camera_detector.get_cameras_for_location(lat, lon, radius)
        
        return jsonify({
            'success': True,
            'query': {'lat': lat, 'lon': lon, 'radius': radius},
            'count': len(cameras),
            'cameras': cameras,
            'timestamp': datetime.now().isoformat()
        })
        
    except ValueError:
        return jsonify({'error': 'Invalid coordinates or radius'}), 400
    except Exception as e:
        logger.error(f"Error obteniendo cámaras por ubicación: {e}")
        return jsonify({'error': str(e)}), 500

@surveillance_bp.route('/api/cameras/<camera_id>/stream')
def get_camera_stream_info(camera_id):
    """Obtener información de stream para una cámara específica"""
    try:
        if not camera_detector:
            return jsonify({'error': 'Camera detector not initialized'}), 503
        
        # Buscar cámara en todas las ubicaciones
        all_cameras = camera_detector.get_all_conflict_zone_cameras()
        camera_info = next((c for c in all_cameras if c['camera_id'] == camera_id), None)
        
        if not camera_info:
            return jsonify({'error': 'Camera not found'}), 404
        
        return jsonify({
            'success': True,
            'camera_id': camera_id,
            'stream_url': camera_info.get('stream_url'),
            'camera_info': camera_info,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo información de stream: {e}")
        return jsonify({'error': str(e)}), 500

# =============================================================================
# API ENDPOINTS - SISTEMA DE CAPTURA
# =============================================================================

@surveillance_bp.route('/api/capture/start', methods=['POST'])
def start_capture_monitoring():
    """Iniciar sistema de captura automático"""
    try:
        if not capture_system:
            return jsonify({'error': 'Capture system not initialized'}), 503
        
        success = capture_system.start_monitoring()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Capture monitoring started',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to start capture monitoring'
            }), 500
            
    except Exception as e:
        logger.error(f"Error iniciando captura: {e}")
        return jsonify({'error': str(e)}), 500

@surveillance_bp.route('/api/capture/stop', methods=['POST'])
def stop_capture_monitoring():
    """Detener sistema de captura automático"""
    try:
        if not capture_system:
            return jsonify({'error': 'Capture system not initialized'}), 503
        
        capture_system.stop_monitoring()
        
        return jsonify({
            'success': True,
            'message': 'Capture monitoring stopped',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error deteniendo captura: {e}")
        return jsonify({'error': str(e)}), 500

@surveillance_bp.route('/api/capture/stats')
def get_capture_statistics():
    """Obtener estadísticas del sistema de captura"""
    try:
        if not capture_system:
            return jsonify({'error': 'Capture system not initialized'}), 503
        
        stats = capture_system.get_capture_statistics()
        
        return jsonify({
            'success': True,
            'statistics': stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return jsonify({'error': str(e)}), 500

@surveillance_bp.route('/api/capture/camera/<camera_id>')
def get_camera_capture_status(camera_id):
    """Obtener estado de captura para una cámara específica"""
    try:
        if not capture_system:
            return jsonify({'error': 'Capture system not initialized'}), 503
        
        status = capture_system.get_camera_status(camera_id)
        
        return jsonify({
            'success': True,
            'camera_id': camera_id,
            'status': status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de cámara: {e}")
        return jsonify({'error': str(e)}), 500

# =============================================================================
# API ENDPOINTS - ANÁLISIS CV Y ALERTAS
# =============================================================================

@surveillance_bp.route('/api/analysis/frame', methods=['POST'])
def analyze_frame():
    """Analizar frame individual con Computer Vision"""
    try:
        if not cv_analyzer:
            return jsonify({'error': 'CV analyzer not initialized'}), 503
        
        # Obtener datos de la request
        data = request.get_json()
        
        if not data or 'image_data' not in data:
            return jsonify({'error': 'No image data provided'}), 400
        
        camera_id = data.get('camera_id', 'unknown')
        image_data = data['image_data']
        
        # Decodificar imagen base64
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        image_array = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({'error': 'Invalid image data'}), 400
        
        # Analizar frame
        analysis = cv_analyzer.analyze_frame(frame, camera_id)
        
        # Convertir análisis a diccionario para JSON
        result = {
            'success': True,
            'camera_id': camera_id,
            'analysis': {
                'overall_risk_level': analysis.overall_risk_level,
                'overall_risk_score': analysis.overall_risk_score,
                'summary': analysis.summary,
                'detections': [
                    {
                        'detection_type': d.detection_type,
                        'confidence_score': d.confidence_score,
                        'bounding_box': d.bounding_box,
                        'description': d.description
                    }
                    for d in analysis.detections
                ],
                'metadata': analysis.metadata,
                'analysis_timestamp': analysis.analysis_timestamp.isoformat()
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error analizando frame: {e}")
        return jsonify({'error': str(e)}), 500

@surveillance_bp.route('/api/alerts/recent')
def get_recent_alerts():
    """Obtener alertas recientes"""
    try:
        limit = int(request.args.get('limit', 50))
        hours = int(request.args.get('hours', 24))
        
        if not capture_system:
            return jsonify({'error': 'Capture system not initialized'}), 503
        
        # Obtener estadísticas que incluyen alertas
        stats = capture_system.get_capture_statistics()
        
        # Por ahora retornar estadísticas, en el futuro implementar query específico
        return jsonify({
            'success': True,
            'alerts': [],  # TODO: Implementar query específico de alertas
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo alertas: {e}")
        return jsonify({'error': str(e)}), 500

@surveillance_bp.route('/api/system/status')
def get_system_status():
    """Obtener estado general del sistema"""
    try:
        status = {
            'surveillance_available': SURVEILLANCE_AVAILABLE,
            'components': {
                'camera_detector': camera_detector is not None,
                'cv_analyzer': cv_analyzer is not None,
                'capture_system': capture_system is not None,
                'socketio': socketio is not None
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Agregar estadísticas si están disponibles
        if capture_system:
            try:
                status['capture_stats'] = capture_system.get_capture_statistics()
            except:
                pass
        
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estado del sistema: {e}")
        return jsonify({'error': str(e)}), 500

# =============================================================================
# WEBSOCKET HANDLERS
# =============================================================================

def setup_websocket_handlers(app_socketio: SocketIO):
    """Configurar handlers de WebSocket"""
    global socketio
    socketio = app_socketio
    
    @socketio.on('connect', namespace='/surveillance')
    def handle_connect():
        """Manejar conexión WebSocket"""
        try:
            logger.info(f"🔌 Cliente conectado a videovigilancia: {request.sid}")
            emit('connection_status', {
                'connected': True,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error en conexión WebSocket: {e}")
    
    @socketio.on('disconnect', namespace='/surveillance')
    def handle_disconnect():
        """Manejar desconexión WebSocket"""
        try:
            logger.info(f"🔌 Cliente desconectado de videovigilancia: {request.sid}")
        except Exception as e:
            logger.error(f"Error en desconexión WebSocket: {e}")
    
    @socketio.on('join_camera_room', namespace='/surveillance')
    def handle_join_camera(data):
        """Unirse a sala de cámara específica"""
        try:
            camera_id = data.get('camera_id')
            if camera_id:
                room = f"camera_{camera_id}"
                join_room(room)
                active_rooms.add(room)
                
                emit('joined_camera', {
                    'camera_id': camera_id,
                    'room': room,
                    'timestamp': datetime.now().isoformat()
                })
                
                logger.debug(f"Cliente {request.sid} unido a sala {room}")
        except Exception as e:
            logger.error(f"Error uniéndose a sala de cámara: {e}")
    
    @socketio.on('leave_camera_room', namespace='/surveillance')
    def handle_leave_camera(data):
        """Salir de sala de cámara específica"""
        try:
            camera_id = data.get('camera_id')
            if camera_id:
                room = f"camera_{camera_id}"
                leave_room(room)
                
                if room in active_rooms:
                    active_rooms.remove(room)
                
                emit('left_camera', {
                    'camera_id': camera_id,
                    'room': room,
                    'timestamp': datetime.now().isoformat()
                })
                
                logger.debug(f"Cliente {request.sid} salió de sala {room}")
        except Exception as e:
            logger.error(f"Error saliendo de sala de cámara: {e}")
    
    @socketio.on('request_camera_status', namespace='/surveillance')
    def handle_camera_status_request(data):
        """Solicitar estado de cámara en tiempo real"""
        try:
            camera_id = data.get('camera_id')
            if camera_id and capture_system:
                status = capture_system.get_camera_status(camera_id)
                
                emit('camera_status_update', {
                    'camera_id': camera_id,
                    'status': status,
                    'timestamp': datetime.now().isoformat()
                })
        except Exception as e:
            logger.error(f"Error obteniendo estado de cámara: {e}")

# =============================================================================
# UTILIDADES Y HELPERS
# =============================================================================

def cleanup_surveillance_system():
    """Limpiar recursos del sistema de videovigilancia"""
    global camera_detector, cv_analyzer, capture_system
    
    try:
        logger.info("🧹 Limpiando sistema de videovigilancia...")
        
        if capture_system:
            capture_system.stop_monitoring()
        
        camera_detector = None
        cv_analyzer = None
        capture_system = None
        
        active_streams.clear()
        active_rooms.clear()
        
        logger.info("✅ Sistema de videovigilancia limpiado")
        
    except Exception as e:
        logger.error(f"Error limpiando sistema: {e}")

def get_surveillance_blueprint():
    """Obtener Blueprint configurado"""
    return surveillance_bp

# Función de testing
def test_surveillance_system():
    """Función de testing para el sistema de videovigilancia"""
    print("🧪 Probando sistema de videovigilancia...")
    
    try:
        # Inicializar sistema
        success = init_surveillance_system(None)  # Sin SocketIO para testing
        
        if success:
            print("✅ Sistema inicializado correctamente")
            
            # Probar detección de cámaras
            if camera_detector:
                cameras = camera_detector.get_all_conflict_zone_cameras()
                print(f"📹 Cámaras encontradas: {len(cameras)}")
            
            # Probar estadísticas
            if capture_system:
                stats = capture_system.get_capture_statistics()
                print(f"📊 Estadísticas: {stats}")
            
        else:
            print("❌ Error inicializando sistema")
    
    except Exception as e:
        print(f"❌ Error en testing: {e}")

if __name__ == "__main__":
    test_surveillance_system()