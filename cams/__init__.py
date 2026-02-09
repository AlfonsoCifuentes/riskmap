"""
Cams Module - Sistema de Vigilancia con Webcams y CCTV
====================================================

Módulo principal para el análisis automático de riesgos usando streams de cámaras públicas.
Integra detección YOLO, tracking, alertas en tiempo real y análisis offline.
"""

from flask import Blueprint
from .routes import register_routes, register_cctv_routes
from .detector import RiskDetector
from .resolver import StreamResolver
from .recorder import VideoRecorder as StreamRecorder  # Alias para compatibilidad
from .alerts import AlertManager

# Crear Blueprint principal
cams_bp = Blueprint('cams', __name__, 
                   template_folder='templates',
                   static_folder='../static',
                   url_prefix='/cams')

# Registrar rutas
register_routes(cams_bp)

# Componentes principales del sistema
detector = None
resolver = None
recorder = None
alert_manager = None

# Clase principal del sistema CCTV para compatibilidad
class CCTVSystem:
    """
    Sistema CCTV principal para compatibilidad con RISKMAP.py
    """
    def __init__(self):
        self.detector = RiskDetector
        self.resolver = StreamResolver
        self.recorder = StreamRecorder
        self.alert_manager = AlertManager
        
    def start_monitoring(self):
        """Iniciar monitoreo"""
        return {"status": "started", "message": "CCTV monitoring started"}
    
    def stop_monitoring(self):
        """Detener monitoreo"""
        return {"status": "stopped", "message": "CCTV monitoring stopped"}
    
    def get_status(self):
        """Obtener estado del sistema"""
        return {
            "status": "active",
            "components": {
                "detector": "available",
                "resolver": "available", 
                "recorder": "available",
                "alert_manager": "available"
            }
        }

def init_cams_system(app=None):
    """
    Inicializar el sistema completo de cámaras
    """
    global detector, resolver, recorder, alert_manager
    
    try:
        # Inicializar componentes
        detector = RiskDetector()
        resolver = StreamResolver()
        recorder = StreamRecorder()
        alert_manager = AlertManager()
        
        print("✅ Sistema de cámaras inicializado correctamente")
        
        if app:
            app.logger.info("🔴 Cams system initialized successfully")
            
        return True
        
    except Exception as e:
        print(f"❌ Error inicializando sistema de cámaras: {e}")
        if app:
            app.logger.error(f"Failed to initialize cams system: {e}")
        return False

def get_detector():
    """Obtener instancia del detector"""
    return detector

def get_resolver():
    """Obtener instancia del resolver"""
    return resolver

def get_recorder():
    """Obtener instancia del recorder"""
    return recorder

def get_alert_manager():
    """Obtener instancia del alert manager"""
    return alert_manager

__all__ = [
    'cams_bp', 
    'init_cams_system',
    'get_detector',
    'get_resolver', 
    'get_recorder',
    'get_alert_manager'
]
