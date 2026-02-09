"""
Public Camera Surveillance System
=================================

Sistema avanzado de videovigilancia para cámaras públicas en zonas de conflicto:
- Detección automática de cámaras públicas en zonas de conflicto
- Análisis en tiempo real con Computer Vision
- Captura inteligente con intervalos adaptativos
- Sistema de alertas multinivel
- Interfaz web moderna y responsiva
"""

import os
import json
import cv2
import base64
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from flask import Blueprint, request, jsonify, render_template, send_file, Response
from flask_socketio import SocketIO, emit, join_room, leave_room
import numpy as np
from pathlib import Path

# Importar módulos locales del sistema de videovigilancia
try:
    from src.surveillance.public_camera_detector import PublicCameraDetector
    from src.surveillance.conflict_cv_analyzer import ConflictIndicatorAnalyzer
    from src.surveillance.smart_capture_system import SmartCaptureSystem
    SURVEILLANCE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ Módulos de videovigilancia no disponibles: {e}")
    SURVEILLANCE_AVAILABLE = False

# Importar módulos legacy (compatibilidad)
try:
    from .detector import RiskDetector
    from .resolver import StreamResolver
    from .recorder import VideoRecorder
    from .alerts import AlertManager
    LEGACY_CAMS_AVAILABLE = True
except ImportError:
    LEGACY_CAMS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Crear Blueprint
cams_bp = Blueprint('cams', __name__, url_prefix='/cams')

# Variables globales para instancias de servicios
detector = None
resolver = None
recorder = None
alert_manager = None
socketio = None

# Estado de streams activos
active_streams = {}
stream_lock = threading.Lock()

# Mock SocketIO para evitar errores de inicialización
class MockSocketIO:
    def on(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    def emit(self, *args, **kwargs):
        # Mock emit - no hace nada pero no falla
        pass

# Mock classes para servicios no disponibles
class MockService:
    def __getattr__(self, name):
        def mock_method(*args, **kwargs):
            return {}
        return mock_method

def init_cams_services(app_socketio: SocketIO):
    """
    Inicializar servicios de cámaras
    
    Args:
        app_socketio: Instancia de SocketIO de la aplicación
    """
    global detector, resolver, recorder, alert_manager, socketio
    
    try:
        socketio = app_socketio
        
        # Inicializar servicios legacy si están disponibles
        if LEGACY_CAMS_AVAILABLE:
            detector = RiskDetector()
            resolver = StreamResolver()
            recorder = VideoRecorder()
            alert_manager = AlertManager()
            
            # Configurar callback de alertas para WebSocket
            alert_manager.add_notification_callback(_emit_alert_notification)
        else:
            # Usar servicios mock si no están disponibles
            detector = MockService()
            resolver = MockService() 
            recorder = MockService()
            alert_manager = MockService()
        
        logger.info("✅ Servicios de cámaras inicializados")
        
    except Exception as e:
        logger.error(f"❌ Error inicializando servicios de cámaras: {e}")
        # Fallback a servicios mock
        detector = MockService()
        resolver = MockService()
        recorder = MockService()
        alert_manager = MockService()

# Inicializar socketio y servicios con mock para evitar errores en decoradores
if socketio is None:
    socketio = MockSocketIO()
if detector is None:
    detector = MockService()
if resolver is None:
    resolver = MockService()
if recorder is None:
    recorder = MockService()
if alert_manager is None:
    alert_manager = MockService()

def _emit_alert_notification(alert: Dict):
    """Callback para emitir alertas via WebSocket"""
    if socketio:
        try:
            socketio.emit('new_alert', alert, namespace='/cams')
            logger.debug(f"🔴 Alerta emitida via WebSocket: {alert['id']}")
        except Exception as e:
            logger.error(f"❌ Error emitiendo alerta via WebSocket: {e}")

# =================== RUTAS REST API ===================

@cams_bp.route('/')
def cams_dashboard():
    """Dashboard principal de cámaras"""
    return render_template('cams/cams_map.html')

@cams_bp.route('/live/<cam_id>')
def live_view(cam_id: str):
    """Vista en vivo de una cámara específica"""
    return render_template('cams/cams_view.html', cam_id=cam_id)

@cams_bp.route('/review')
def review_page():
    """Página de revisión de alertas y grabaciones"""
    return render_template('cams/review.html')

@cams_bp.route('/api/cameras')
def get_cameras():
    """Obtener lista de cámaras configuradas"""
    try:
        cameras_file = Path("data/cameras.json")
        if not cameras_file.exists():
            return jsonify({"success": False, "error": "Archivo de cámaras no encontrado"})
        
        with open(cameras_file, 'r', encoding='utf-8') as f:
            cameras_data = json.load(f)
        
        return jsonify({
            "success": True,
            "cameras": cameras_data.get("cameras", []),
            "total": len(cameras_data.get("cameras", []))
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo cámaras: {e}")
        return jsonify({"success": False, "error": str(e)})

@cams_bp.route('/api/cameras/<cam_id>')
def get_camera(cam_id: str):
    """Obtener información de una cámara específica"""
    try:
        cameras_file = Path("data/cameras.json")
        if not cameras_file.exists():
            return jsonify({"success": False, "error": "Archivo de cámaras no encontrado"})
        
        with open(cameras_file, 'r', encoding='utf-8') as f:
            cameras_data = json.load(f)
        
        camera = next((c for c in cameras_data.get("cameras", []) if c["id"] == cam_id), None)
        
        if not camera:
            return jsonify({"success": False, "error": "Cámara no encontrada"})
        
        # Agregar información de estado
        with stream_lock:
            stream_info = active_streams.get(cam_id, {})
        
        camera_info = camera.copy()
        camera_info["status"] = stream_info.get("status", "stopped")
        camera_info["last_update"] = stream_info.get("last_update")
        camera_info["viewer_count"] = stream_info.get("viewer_count", 0)
        
        return jsonify({
            "success": True,
            "camera": camera_info
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo cámara {cam_id}: {e}")
        return jsonify({"success": False, "error": str(e)})

@cams_bp.route('/api/cameras/<cam_id>/start', methods=['POST'])
def start_camera_stream(cam_id: str):
    """Iniciar stream de una cámara"""
    global detector, resolver, recorder
    
    try:
        # Obtener información de la cámara
        cameras_file = Path("data/cameras.json")
        with open(cameras_file, 'r', encoding='utf-8') as f:
            cameras_data = json.load(f)
        
        camera = next((c for c in cameras_data.get("cameras", []) if c["id"] == cam_id), None)
        
        if not camera:
            return jsonify({"success": False, "error": "Cámara no encontrada"})
        
        # Verificar si ya está activa
        with stream_lock:
            if cam_id in active_streams:
                return jsonify({"success": False, "error": "Stream ya activo"})
        
        # Resolver URL del stream
        stream_url = camera.get("stream_url")
        if not stream_url:
            return jsonify({"success": False, "error": "URL de stream no configurada"})
        
        resolved_stream = resolver.resolve_url(stream_url)
        
        if not resolved_stream.get("success"):
            return jsonify({
                "success": False, 
                "error": f"No se pudo resolver stream: {resolved_stream.get('error')}"
            })
        
        # Crear entrada en streams activos
        with stream_lock:
            active_streams[cam_id] = {
                "camera": camera,
                "resolved_stream": resolved_stream,
                "status": "starting",
                "start_time": datetime.now(),
                "viewer_count": 0,
                "last_update": datetime.now().isoformat(),
                "thread": None
            }
        
        # Iniciar grabación si está habilitada
        if camera.get("record_continuous", False):
            recorder.start_continuous_recording(
                cam_id, 
                resolved_stream["stream_url"], 
                resolved_stream.get("headers")
            )
        
        # Iniciar hilo de procesamiento de stream
        stream_thread = threading.Thread(
            target=_process_camera_stream,
            args=(cam_id,),
            daemon=True
        )
        
        with stream_lock:
            active_streams[cam_id]["thread"] = stream_thread
            active_streams[cam_id]["status"] = "running"
        
        stream_thread.start()
        
        logger.info(f"📹 Stream iniciado para cámara {cam_id}")
        
        return jsonify({
            "success": True,
            "message": f"Stream iniciado para cámara {cam_id}",
            "stream_info": resolved_stream
        })
        
    except Exception as e:
        logger.error(f"❌ Error iniciando stream para {cam_id}: {e}")
        return jsonify({"success": False, "error": str(e)})

@cams_bp.route('/api/cameras/<cam_id>/stop', methods=['POST'])
def stop_camera_stream(cam_id: str):
    """Detener stream de una cámara"""
    try:
        with stream_lock:
            if cam_id not in active_streams:
                return jsonify({"success": False, "error": "Stream no activo"})
            
            active_streams[cam_id]["status"] = "stopping"
        
        # Detener grabación
        recorder.stop_recording(cam_id)
        
        # El hilo se detendrá automáticamente al cambiar el status
        time.sleep(1)  # Dar tiempo para que se detenga
        
        with stream_lock:
            if cam_id in active_streams:
                del active_streams[cam_id]
        
        logger.info(f"⏹️ Stream detenido para cámara {cam_id}")
        
        return jsonify({
            "success": True,
            "message": f"Stream detenido para cámara {cam_id}"
        })
        
    except Exception as e:
        logger.error(f"❌ Error deteniendo stream para {cam_id}: {e}")
        return jsonify({"success": False, "error": str(e)})

@cams_bp.route('/api/cameras/<cam_id>/status')
def get_camera_status(cam_id: str):
    """Obtener estado de una cámara"""
    try:
        with stream_lock:
            stream_info = active_streams.get(cam_id, {})
        
        if not stream_info:
            return jsonify({
                "success": True,
                "status": "stopped",
                "message": "Stream no activo"
            })
        
        # Agregar información de detección
        detection_stats = detector.get_statistics() if detector else {}
        active_detections = detector.get_active_detections(cam_id) if detector else {}
        
        return jsonify({
            "success": True,
            "status": stream_info.get("status"),
            "start_time": stream_info.get("start_time", datetime.now()).isoformat(),
            "viewer_count": stream_info.get("viewer_count", 0),
            "last_update": stream_info.get("last_update"),
            "detection_stats": detection_stats,
            "active_detections": active_detections
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estado de {cam_id}: {e}")
        return jsonify({"success": False, "error": str(e)})

# =================== RUTAS DE ALERTAS ===================

@cams_bp.route('/api/alerts')
def get_alerts():
    """Obtener alertas con filtros"""
    try:
        # Obtener parámetros de query
        resolved = request.args.get('resolved')
        cam_id = request.args.get('cam_id')
        alert_type = request.args.get('type')
        severity = request.args.get('severity')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Convertir resolved a boolean si está presente
        if resolved is not None:
            resolved = resolved.lower() == 'true'
        
        alerts = alert_manager.get_alerts(
            resolved=resolved,
            cam_id=cam_id,
            alert_type=alert_type,
            severity=severity,
            limit=limit,
            offset=offset
        )
        
        return jsonify({
            "success": True,
            "alerts": alerts,
            "total": len(alerts)
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo alertas: {e}")
        return jsonify({"success": False, "error": str(e)})

@cams_bp.route('/api/alerts/<alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id: str):
    """Resolver una alerta"""
    try:
        data = request.get_json() or {}
        resolved_by = data.get('resolved_by', 'api_user')
        resolution_notes = data.get('notes', '')
        
        success = alert_manager.resolve_alert(alert_id, resolved_by, resolution_notes)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Alerta {alert_id} resuelta"
            })
        else:
            return jsonify({
                "success": False,
                "error": "No se pudo resolver la alerta"
            })
        
    except Exception as e:
        logger.error(f"❌ Error resolviendo alerta {alert_id}: {e}")
        return jsonify({"success": False, "error": str(e)})

@cams_bp.route('/api/alerts/statistics')
def get_alert_statistics():
    """Obtener estadísticas de alertas"""
    try:
        stats = alert_manager.get_alert_statistics()
        
        return jsonify({
            "success": True,
            "statistics": stats
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas de alertas: {e}")
        return jsonify({"success": False, "error": str(e)})

# =================== RUTAS DE GRABACIONES ===================

@cams_bp.route('/api/recordings/<cam_id>')
def get_recordings(cam_id: str):
    """Obtener grabaciones de una cámara"""
    try:
        limit = int(request.args.get('limit', 20))
        recordings = recorder.get_recordings(cam_id, limit)
        
        return jsonify({
            "success": True,
            "recordings": recordings,
            "total": len(recordings)
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo grabaciones para {cam_id}: {e}")
        return jsonify({"success": False, "error": str(e)})

@cams_bp.route('/api/recordings/storage/stats')
def get_storage_stats():
    """Obtener estadísticas de almacenamiento"""
    try:
        stats = recorder.get_storage_stats()
        
        return jsonify({
            "success": True,
            "storage_stats": stats
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas de almacenamiento: {e}")
        return jsonify({"success": False, "error": str(e)})

# =================== WEBSOCKET HANDLERS ===================

@socketio.on('connect', namespace='/cams')
def handle_connect():
    """Cliente conectado a WebSocket"""
    logger.debug(f"🔌 Cliente conectado a /cams: {request.sid}")
    emit('connected', {'message': 'Conectado al sistema de cámaras'})

@socketio.on('disconnect', namespace='/cams')
def handle_disconnect():
    """Cliente desconectado de WebSocket"""
    logger.debug(f"🔌 Cliente desconectado de /cams: {request.sid}")
    
    # Remover de todas las salas
    with stream_lock:
        for cam_id in active_streams:
            if active_streams[cam_id]["viewer_count"] > 0:
                active_streams[cam_id]["viewer_count"] -= 1

@socketio.on('join_camera', namespace='/cams')
def handle_join_camera(data):
    """Cliente se une al stream de una cámara"""
    try:
        cam_id = data.get('cam_id')
        if not cam_id:
            emit('error', {'message': 'cam_id requerido'})
            return
        
        join_room(f"camera_{cam_id}")
        
        with stream_lock:
            if cam_id in active_streams:
                active_streams[cam_id]["viewer_count"] += 1
        
        emit('joined_camera', {'cam_id': cam_id, 'message': f'Unido a cámara {cam_id}'})
        logger.debug(f"👁️ Cliente {request.sid} se unió a cámara {cam_id}")
        
    except Exception as e:
        logger.error(f"❌ Error en join_camera: {e}")
        emit('error', {'message': str(e)})

@socketio.on('leave_camera', namespace='/cams')
def handle_leave_camera(data):
    """Cliente abandona el stream de una cámara"""
    try:
        cam_id = data.get('cam_id')
        if not cam_id:
            return
        
        leave_room(f"camera_{cam_id}")
        
        with stream_lock:
            if cam_id in active_streams and active_streams[cam_id]["viewer_count"] > 0:
                active_streams[cam_id]["viewer_count"] -= 1
        
        emit('left_camera', {'cam_id': cam_id})
        logger.debug(f"👁️ Cliente {request.sid} abandonó cámara {cam_id}")
        
    except Exception as e:
        logger.error(f"❌ Error en leave_camera: {e}")

@socketio.on('request_frame', namespace='/cams')
def handle_request_frame(data):
    """Cliente solicita frame actual de una cámara"""
    try:
        cam_id = data.get('cam_id')
        if not cam_id:
            emit('error', {'message': 'cam_id requerido'})
            return
        
        # Verificar que el stream esté activo
        with stream_lock:
            if cam_id not in active_streams:
                emit('error', {'message': f'Stream {cam_id} no activo'})
                return
        
        # El frame se enviará automáticamente por el hilo de procesamiento
        emit('frame_requested', {'cam_id': cam_id})
        
    except Exception as e:
        logger.error(f"❌ Error en request_frame: {e}")
        emit('error', {'message': str(e)})

# =================== FUNCIONES DE PROCESAMIENTO ===================

def _process_camera_stream(cam_id: str):
    """
    Procesar stream de cámara en hilo separado
    
    Args:
        cam_id: ID de la cámara a procesar
    """
    try:
        with stream_lock:
            stream_info = active_streams.get(cam_id)
        
        if not stream_info:
            return
        
        camera = stream_info["camera"]
        resolved_stream = stream_info["resolved_stream"]
        
        # Abrir stream de video
        cap = cv2.VideoCapture(resolved_stream["stream_url"])
        
        if not cap.isOpened():
            logger.error(f"❌ No se pudo abrir stream para {cam_id}")
            with stream_lock:
                if cam_id in active_streams:
                    active_streams[cam_id]["status"] = "error"
            return
        
        # Configurar captura
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Buffer mínimo
        
        logger.info(f"📹 Procesamiento iniciado para cámara {cam_id}")
        
        frame_count = 0
        last_detection_time = time.time()
        
        while True:
            # Verificar si debe continuar
            with stream_lock:
                current_status = active_streams.get(cam_id, {}).get("status")
            
            if current_status != "running":
                break
            
            # Leer frame
            ret, frame = cap.read()
            
            if not ret:
                logger.warning(f"⚠️ No se pudo leer frame de {cam_id}")
                time.sleep(1)
                continue
            
            frame_count += 1
            current_time = time.time()
            
            # Procesar detección cada 2 segundos
            if current_time - last_detection_time >= 2.0:
                try:
                    # Ejecutar detección
                    detection_result = detector.detect_frame(frame, cam_id)
                    
                    # Procesar alertas
                    alerts = detection_result.get("alerts", [])
                    for alert in alerts:
                        # Crear alerta en el sistema
                        alert_id = alert_manager.create_alert(
                            cam_id=cam_id,
                            alert_type=alert["type"],
                            severity=alert["severity"],
                            title=alert.get("description", "Alerta detectada"),
                            description=alert.get("description", ""),
                            confidence=alert.get("confidence", 1.0),
                            metadata=alert.get("metadata", {}),
                            zone_id=camera.get("zone")
                        )
                        
                        # Grabar clip de alerta si está habilitado
                        if camera.get("record_alerts", True):
                            recorder.record_alert_clip(cam_id, alert)
                    
                    # Emitir detecciones via WebSocket
                    if socketio and detection_result.get("detections"):
                        socketio.emit('detections', {
                            'cam_id': cam_id,
                            'detections': detection_result["detections"],
                            'tracking': detection_result.get("tracking", []),
                            'timestamp': datetime.now().isoformat()
                        }, room=f"camera_{cam_id}", namespace='/cams')
                    
                    last_detection_time = current_time
                    
                except Exception as e:
                    logger.error(f"❌ Error en detección para {cam_id}: {e}")
            
            # Enviar frame via WebSocket (cada 5 frames para reducir carga)
            if frame_count % 5 == 0 and socketio:
                try:
                    # Redimensionar frame para WebSocket
                    height, width = frame.shape[:2]
                    if width > 640:
                        ratio = 640 / width
                        new_width = 640
                        new_height = int(height * ratio)
                        frame_resized = cv2.resize(frame, (new_width, new_height))
                    else:
                        frame_resized = frame
                    
                    # Codificar a JPEG
                    _, buffer = cv2.imencode('.jpg', frame_resized, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    frame_b64 = base64.b64encode(buffer).decode('utf-8')
                    
                    # Emitir frame
                    socketio.emit('frame', {
                        'cam_id': cam_id,
                        'frame': frame_b64,
                        'timestamp': datetime.now().isoformat()
                    }, room=f"camera_{cam_id}", namespace='/cams')
                    
                except Exception as e:
                    logger.error(f"❌ Error enviando frame para {cam_id}: {e}")
            
            # Actualizar timestamp
            with stream_lock:
                if cam_id in active_streams:
                    active_streams[cam_id]["last_update"] = datetime.now().isoformat()
            
            # Control de FPS (procesar a ~10 FPS)
            time.sleep(0.1)
        
        # Limpiar
        cap.release()
        
        with stream_lock:
            if cam_id in active_streams:
                active_streams[cam_id]["status"] = "stopped"
        
        logger.info(f"📹 Procesamiento finalizado para cámara {cam_id}")
        
    except Exception as e:
        logger.error(f"❌ Error en procesamiento de stream {cam_id}: {e}")
        with stream_lock:
            if cam_id in active_streams:
                active_streams[cam_id]["status"] = "error"

def get_active_streams_status():
    """Obtener estado de todos los streams activos"""
    with stream_lock:
        return {
            cam_id: {
                "status": info["status"],
                "viewer_count": info["viewer_count"],
                "last_update": info["last_update"],
                "camera_name": info["camera"].get("name", cam_id)
            }
            for cam_id, info in active_streams.items()
        }

def cleanup_cams_services():
    """Limpiar servicios de cámaras"""
    global detector, resolver, recorder, alert_manager
    
    # Detener todos los streams
    with stream_lock:
        for cam_id in list(active_streams.keys()):
            if active_streams[cam_id]["status"] == "running":
                active_streams[cam_id]["status"] = "stopping"
        active_streams.clear()
    
    # Limpiar servicios
    if detector:
        detector.cleanup()
    if recorder:
        recorder.cleanup()
    if alert_manager:
        alert_manager.cleanup()
    
    logger.info("🧹 Servicios de cámaras limpiados")

def register_routes(blueprint):
    """
    Registrar rutas en el blueprint (compatibilidad con __init__.py)
    
    Args:
        blueprint: Blueprint de Flask donde registrar las rutas
    """
    # Las rutas ya están registradas en cams_bp automáticamente
    # Esta función existe solo para compatibilidad
    pass

def register_cctv_routes(app, socketio_instance=None):
    """
    Función para registrar rutas CCTV en la aplicación principal
    
    Args:
        app: Aplicación Flask
        socketio_instance: Instancia de SocketIO (opcional)
    """
    # Inicializar servicios con SocketIO si se proporciona
    if socketio_instance:
        init_cams_services(socketio_instance)
    
    # Registrar el blueprint
    app.register_blueprint(cams_bp)
    
    logger.info("✅ Rutas CCTV registradas en aplicación principal")
