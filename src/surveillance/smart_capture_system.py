"""
Smart Capture System for Conflict Monitoring
============================================

Sistema inteligente de captura automática para monitoreo de conflictos geopolíticos.
Gestiona la captura adaptativa de screenshots, análisis CV automático y generación de alertas.

Features:
- Captura adaptativa basada en nivel de riesgo
- Programación inteligente de intervalos
- Integración con análisis CV
- Sistema de alertas multinivel
- Almacenamiento optimizado
- Notificaciones en tiempo real
"""

import os
import cv2
import asyncio
import threading
import time
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from pathlib import Path
import json
import sqlite3
import hashlib
from concurrent.futures import ThreadPoolExecutor
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

# Importar módulos locales
from .conflict_cv_analyzer import ConflictIndicatorAnalyzer, FrameAnalysis
from .public_camera_detector import PublicCameraDetector

logger = logging.getLogger(__name__)

@dataclass
class CaptureSchedule:
    """Configuración de programación de capturas"""
    camera_id: str
    interval_seconds: int
    risk_level: str
    priority: str
    last_capture: datetime = None
    consecutive_alerts: int = 0
    adaptive_interval: int = None
    enabled: bool = True

@dataclass
class CaptureResult:
    """Resultado de una captura"""
    camera_id: str
    timestamp: datetime
    capture_path: str
    frame: Optional[any] = None
    analysis: Optional[FrameAnalysis] = None
    success: bool = True
    error: str = None
    file_size: int = 0

@dataclass
class AlertConfig:
    """Configuración de alertas"""
    email_enabled: bool = True
    webhook_enabled: bool = True
    severity_threshold: str = 'medium'
    max_alerts_per_hour: int = 10
    recipients: List[str] = None
    webhook_url: str = None

class SmartCaptureSystem:
    """
    Sistema inteligente de captura automática para monitoreo de conflictos
    """
    
    def __init__(self, db_path: str = "./data/geopolitical_intel.db"):
        self.db_path = db_path
        
        # Componentes principales
        self.camera_detector = PublicCameraDetector(db_path)
        self.cv_analyzer = ConflictIndicatorAnalyzer(db_path)
        
        # Estado del sistema
        self.is_running = False
        self.capture_threads = {}
        self.capture_schedules: Dict[str, CaptureSchedule] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Configuración
        self.config = {
            'capture_base_dir': Path("captures"),
            'max_file_size_mb': 10,
            'image_quality': 85,
            'max_retries': 3,
            'timeout_seconds': 30,
            'cleanup_days': 30
        }
        
        # Configuración de intervalos adaptativos
        self.interval_config = {
            'high_risk': {
                'base_interval': 30,    # 30 segundos
                'alert_interval': 15,   # 15 segundos después de alerta
                'max_interval': 300     # 5 minutos máximo
            },
            'medium_risk': {
                'base_interval': 120,   # 2 minutos
                'alert_interval': 60,   # 1 minuto después de alerta
                'max_interval': 600     # 10 minutos máximo
            },
            'low_risk': {
                'base_interval': 300,   # 5 minutos
                'alert_interval': 120,  # 2 minutos después de alerta
                'max_interval': 1800    # 30 minutos máximo
            }
        }
        
        # Sistema de alertas
        self.alert_config = AlertConfig()
        self.alert_history = []
        self.notification_callbacks = []
        
        # Crear directorios
        self._setup_directories()
        
        logger.info("🎯 Sistema de captura inteligente inicializado")
    
    def _setup_directories(self):
        """Crear estructura de directorios"""
        base_dir = self.config['capture_base_dir']
        directories = [
            base_dir,
            base_dir / "screenshots",
            base_dir / "alerts",
            base_dir / "analysis",
            base_dir / "temp"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        logger.info("📁 Directorios de captura creados")
    
    def start_monitoring(self) -> bool:
        """Iniciar monitoreo automático de todas las cámaras en zonas de conflicto"""
        try:
            if self.is_running:
                logger.warning("⚠️ El sistema ya está ejecutándose")
                return False
            
            logger.info("🚀 Iniciando sistema de monitoreo automático...")
            
            # Obtener cámaras en zonas de conflicto
            cameras = self.camera_detector.get_all_conflict_zone_cameras()
            
            if not cameras:
                logger.warning("⚠️ No se encontraron cámaras en zonas de conflicto")
                return False
            
            # Configurar programación para cada cámara
            self._setup_camera_schedules(cameras)
            
            # Marcar como ejecutándose
            self.is_running = True
            
            # Iniciar hilos de captura
            self._start_capture_threads()
            
            # Iniciar limpieza automática
            self._start_cleanup_thread()
            
            logger.info(f"✅ Monitoreo iniciado para {len(cameras)} cámaras")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error iniciando monitoreo: {e}")
            return False
    
    def stop_monitoring(self):
        """Detener monitoreo automático"""
        try:
            logger.info("⏹️ Deteniendo sistema de monitoreo...")
            
            self.is_running = False
            
            # Esperar a que terminen los hilos
            for thread in self.capture_threads.values():
                if thread.is_alive():
                    thread.join(timeout=5)
            
            self.capture_threads.clear()
            self.executor.shutdown(wait=True)
            
            logger.info("✅ Sistema de monitoreo detenido")
            
        except Exception as e:
            logger.error(f"❌ Error deteniendo monitoreo: {e}")
    
    def _setup_camera_schedules(self, cameras: List[Dict]):
        """Configurar programación de captura para cada cámara"""
        self.capture_schedules.clear()
        
        for camera in cameras:
            camera_id = camera['camera_id']
            risk_level = camera.get('risk_level', 'medium')
            
            # Determinar intervalo base según riesgo
            interval_config = self.interval_config.get(risk_level, self.interval_config['medium_risk'])
            base_interval = interval_config['base_interval']
            
            # Crear programación
            schedule = CaptureSchedule(
                camera_id=camera_id,
                interval_seconds=base_interval,
                risk_level=risk_level,
                priority=camera.get('priority', 'normal'),
                adaptive_interval=base_interval
            )
            
            self.capture_schedules[camera_id] = schedule
            
            logger.info(f"📋 Programación configurada para {camera_id}: {base_interval}s (riesgo: {risk_level})")
    
    def _start_capture_threads(self):
        """Iniciar hilos de captura para cada cámara"""
        for camera_id, schedule in self.capture_schedules.items():
            if schedule.enabled:
                thread = threading.Thread(
                    target=self._capture_loop,
                    args=(camera_id,),
                    daemon=True,
                    name=f"capture_thread_{camera_id}"
                )
                
                self.capture_threads[camera_id] = thread
                thread.start()
                
                logger.info(f"🎬 Hilo de captura iniciado para {camera_id}")
    
    def _capture_loop(self, camera_id: str):
        """Loop principal de captura para una cámara específica"""
        logger.info(f"🔄 Loop de captura iniciado para {camera_id}")
        
        while self.is_running:
            try:
                schedule = self.capture_schedules.get(camera_id)
                if not schedule or not schedule.enabled:
                    break
                
                # Verificar si es hora de capturar
                current_time = datetime.now()
                if schedule.last_capture:
                    time_since_last = (current_time - schedule.last_capture).total_seconds()
                    if time_since_last < schedule.adaptive_interval:
                        # Esperar hasta el próximo intervalo
                        sleep_time = schedule.adaptive_interval - time_since_last
                        time.sleep(min(sleep_time, 10))  # Máximo 10s de sleep
                        continue
                
                # Ejecutar captura
                capture_result = self._execute_camera_capture(camera_id)
                
                # Actualizar programación
                schedule.last_capture = current_time
                
                # Procesar resultado
                if capture_result.success:
                    self._process_capture_result(capture_result, schedule)
                else:
                    logger.error(f"❌ Error en captura de {camera_id}: {capture_result.error}")
                
                # Esperar intervalo dinámico
                time.sleep(schedule.adaptive_interval)
                
            except Exception as e:
                logger.error(f"❌ Error en loop de captura para {camera_id}: {e}")
                time.sleep(60)  # Esperar 1 minuto antes de reintentar
    
    def _execute_camera_capture(self, camera_id: str) -> CaptureResult:
        """Ejecutar captura individual de una cámara"""
        start_time = datetime.now()
        
        try:
            # Obtener información de la cámara
            cameras = self.camera_detector.get_cameras_for_location(0, 0, 999999)  # Obtener todas
            camera_info = next((c for c in cameras if c['camera_id'] == camera_id), None)
            
            if not camera_info:
                return CaptureResult(
                    camera_id=camera_id,
                    timestamp=start_time,
                    capture_path="",
                    success=False,
                    error="Cámara no encontrada"
                )
            
            stream_url = camera_info.get('stream_url')
            if not stream_url:
                return CaptureResult(
                    camera_id=camera_id,
                    timestamp=start_time,
                    capture_path="",
                    success=False,
                    error="URL de stream no disponible"
                )
            
            # Capturar frame
            frame = self._capture_frame_from_stream(stream_url)
            
            if frame is None:
                return CaptureResult(
                    camera_id=camera_id,
                    timestamp=start_time,
                    capture_path="",
                    success=False,
                    error="No se pudo capturar frame"
                )
            
            # Guardar imagen
            capture_path = self._save_captured_frame(camera_id, frame, start_time)
            
            # Analizar con CV
            analysis = self.cv_analyzer.analyze_frame(frame, camera_id)
            
            # Guardar análisis en BD
            self.cv_analyzer.save_analysis_to_db(analysis, camera_id, capture_path)
            
            file_size = os.path.getsize(capture_path) if os.path.exists(capture_path) else 0
            
            return CaptureResult(
                camera_id=camera_id,
                timestamp=start_time,
                capture_path=capture_path,
                frame=frame,
                analysis=analysis,
                success=True,
                file_size=file_size
            )
            
        except Exception as e:
            logger.error(f"Error ejecutando captura de {camera_id}: {e}")
            return CaptureResult(
                camera_id=camera_id,
                timestamp=start_time,
                capture_path="",
                success=False,
                error=str(e)
            )
    
    def _capture_frame_from_stream(self, stream_url: str) -> Optional[any]:
        """Capturar frame desde stream de video"""
        try:
            # Para streams HTTPS, intentar captura directa
            if stream_url.startswith('https://') or stream_url.startswith('http://'):
                return self._capture_from_http_stream(stream_url)
            
            # Para streams RTSP u otros protocolos
            elif stream_url.startswith('rtsp://') or stream_url.startswith('rtmp://'):
                return self._capture_from_rtsp_stream(stream_url)
            
            # Para URLs de imagen estática
            else:
                return self._capture_from_image_url(stream_url)
                
        except Exception as e:
            logger.error(f"Error capturando frame: {e}")
            return None
    
    def _capture_from_http_stream(self, stream_url: str) -> Optional[any]:
        """Capturar frame desde stream HTTP/HTTPS"""
        try:
            # Intentar abrir el stream con OpenCV
            cap = cv2.VideoCapture(stream_url)
            
            if not cap.isOpened():
                # Fallback: descargar imagen directamente
                return self._capture_from_image_url(stream_url)
            
            # Leer frame
            ret, frame = cap.read()
            cap.release()
            
            if ret and frame is not None:
                return frame
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error en captura HTTP: {e}")
            return None
    
    def _capture_from_rtsp_stream(self, stream_url: str) -> Optional[any]:
        """Capturar frame desde stream RTSP"""
        try:
            cap = cv2.VideoCapture(stream_url)
            
            if not cap.isOpened():
                return None
            
            # Configurar timeout
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Leer frame
            ret, frame = cap.read()
            cap.release()
            
            return frame if ret else None
            
        except Exception as e:
            logger.error(f"Error en captura RTSP: {e}")
            return None
    
    def _capture_from_image_url(self, image_url: str) -> Optional[any]:
        """Capturar imagen desde URL estática"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(image_url, headers=headers, timeout=10, stream=True)
            response.raise_for_status()
            
            # Convertir a array numpy
            image_array = np.frombuffer(response.content, np.uint8)
            frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            
            return frame
            
        except Exception as e:
            logger.error(f"Error descargando imagen: {e}")
            return None
    
    def _save_captured_frame(self, camera_id: str, frame: any, timestamp: datetime) -> str:
        """Guardar frame capturado en disco"""
        try:
            # Crear nombre de archivo
            timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
            filename = f"{camera_id}_{timestamp_str}.jpg"
            
            # Determinar directorio basado en fecha
            date_dir = self.config['capture_base_dir'] / "screenshots" / timestamp.strftime("%Y-%m-%d")
            date_dir.mkdir(parents=True, exist_ok=True)
            
            filepath = date_dir / filename
            
            # Guardar imagen
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.config['image_quality']]
            success = cv2.imwrite(str(filepath), frame, encode_params)
            
            if not success:
                raise Exception("No se pudo guardar la imagen")
            
            # Verificar tamaño de archivo
            file_size_mb = filepath.stat().st_size / (1024 * 1024)
            if file_size_mb > self.config['max_file_size_mb']:
                logger.warning(f"⚠️ Archivo grande: {file_size_mb:.1f}MB")
            
            logger.debug(f"💾 Frame guardado: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error guardando frame: {e}")
            raise
    
    def _process_capture_result(self, result: CaptureResult, schedule: CaptureSchedule):
        """Procesar resultado de captura y ajustar programación"""
        try:
            if not result.analysis:
                return
            
            # Ajustar intervalo adaptativo basado en nivel de riesgo detectado
            self._adjust_capture_interval(schedule, result.analysis)
            
            # Generar alertas si es necesario
            if result.analysis.overall_risk_level in ['medium', 'high']:
                self._generate_alert(result)
            
            # Notificar a callbacks registrados
            self._notify_callbacks(result)
            
            logger.debug(f"🔄 Resultado procesado para {result.camera_id}: {result.analysis.overall_risk_level}")
            
        except Exception as e:
            logger.error(f"Error procesando resultado de captura: {e}")
    
    def _adjust_capture_interval(self, schedule: CaptureSchedule, analysis: FrameAnalysis):
        """Ajustar intervalo de captura basado en análisis CV"""
        try:
            interval_config = self.interval_config.get(schedule.risk_level, self.interval_config['medium_risk'])
            
            if analysis.overall_risk_level == 'high':
                # Aumentar frecuencia para alto riesgo
                schedule.adaptive_interval = interval_config['alert_interval']
                schedule.consecutive_alerts += 1
            elif analysis.overall_risk_level == 'medium':
                # Frecuencia moderada
                schedule.adaptive_interval = min(
                    interval_config['base_interval'], 
                    schedule.adaptive_interval * 1.2
                )
                schedule.consecutive_alerts += 1
            else:
                # Reducir frecuencia para bajo riesgo
                if schedule.consecutive_alerts > 0:
                    schedule.consecutive_alerts = max(0, schedule.consecutive_alerts - 1)
                
                if schedule.consecutive_alerts == 0:
                    schedule.adaptive_interval = min(
                        interval_config['max_interval'],
                        schedule.adaptive_interval * 1.5
                    )
            
            # Asegurar límites
            schedule.adaptive_interval = max(
                interval_config['alert_interval'],
                min(schedule.adaptive_interval, interval_config['max_interval'])
            )
            
            logger.debug(f"📊 Intervalo ajustado para {schedule.camera_id}: {schedule.adaptive_interval}s")
            
        except Exception as e:
            logger.error(f"Error ajustando intervalo: {e}")
    
    def _generate_alert(self, result: CaptureResult):
        """Generar alerta basada en resultado de captura"""
        try:
            if not result.analysis or result.analysis.overall_risk_level == 'low':
                return
            
            # Verificar límites de alerta
            current_time = datetime.now()
            recent_alerts = [
                a for a in self.alert_history 
                if (current_time - a['timestamp']).total_seconds() < 3600  # Última hora
            ]
            
            if len(recent_alerts) >= self.alert_config.max_alerts_per_hour:
                logger.warning("⚠️ Límite de alertas por hora alcanzado")
                return
            
            # Crear alerta
            alert_data = {
                'id': hashlib.md5(f"{result.camera_id}_{result.timestamp}".encode()).hexdigest()[:8],
                'camera_id': result.camera_id,
                'timestamp': result.timestamp,
                'severity': result.analysis.overall_risk_level,
                'description': result.analysis.summary,
                'indicators': [d.detection_type for d in result.analysis.detections],
                'capture_path': result.capture_path,
                'confidence_score': result.analysis.overall_risk_score
            }
            
            # Agregar a historial
            self.alert_history.append(alert_data)
            
            # Enviar notificaciones
            if self.alert_config.email_enabled:
                self._send_email_alert(alert_data)
            
            if self.alert_config.webhook_enabled:
                self._send_webhook_alert(alert_data)
            
            logger.info(f"🚨 Alerta generada: {alert_data['id']} - {alert_data['severity']}")
            
        except Exception as e:
            logger.error(f"Error generando alerta: {e}")
    
    def _send_email_alert(self, alert_data: Dict):
        """Enviar alerta por email"""
        try:
            smtp_server = os.getenv('SMTP_SERVER')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_user = os.getenv('SMTP_USER')
            smtp_password = os.getenv('SMTP_PASSWORD')
            
            if not all([smtp_server, smtp_user, smtp_password]):
                logger.warning("⚠️ Configuración SMTP incompleta")
                return
            
            recipients = self.alert_config.recipients or [smtp_user]
            
            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"🚨 Alerta de Conflicto - {alert_data['severity'].upper()}"
            
            # Cuerpo del mensaje
            body = f"""
            Alerta de Conflicto Detectada
            ============================
            
            ID de Alerta: {alert_data['id']}
            Cámara: {alert_data['camera_id']}
            Severidad: {alert_data['severity']}
            Timestamp: {alert_data['timestamp']}
            
            Descripción:
            {alert_data['description']}
            
            Indicadores Detectados:
            {', '.join(alert_data['indicators'])}
            
            Puntuación de Confianza: {alert_data['confidence_score']:.2f}
            
            Imagen capturada guardada en: {alert_data['capture_path']}
            
            ---
            Sistema de Monitoreo de Conflictos Geopolíticos
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Adjuntar imagen si existe
            if os.path.exists(alert_data['capture_path']):
                try:
                    with open(alert_data['capture_path'], 'rb') as f:
                        img = MIMEImage(f.read())
                        img.add_header('Content-Disposition', 'attachment', filename=f"alert_{alert_data['id']}.jpg")
                        msg.attach(img)
                except Exception as e:
                    logger.warning(f"No se pudo adjuntar imagen: {e}")
            
            # Enviar email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            logger.info(f"📧 Email de alerta enviado: {alert_data['id']}")
            
        except Exception as e:
            logger.error(f"Error enviando email: {e}")
    
    def _send_webhook_alert(self, alert_data: Dict):
        """Enviar alerta vía webhook"""
        try:
            webhook_url = self.alert_config.webhook_url or os.getenv('ALERT_WEBHOOK_URL')
            
            if not webhook_url:
                return
            
            payload = {
                'alert_id': alert_data['id'],
                'camera_id': alert_data['camera_id'],
                'timestamp': alert_data['timestamp'].isoformat(),
                'severity': alert_data['severity'],
                'description': alert_data['description'],
                'indicators': alert_data['indicators'],
                'confidence_score': alert_data['confidence_score'],
                'system': 'geopolitical_conflict_monitor'
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info(f"🔗 Webhook enviado: {alert_data['id']}")
            
        except Exception as e:
            logger.error(f"Error enviando webhook: {e}")
    
    def _notify_callbacks(self, result: CaptureResult):
        """Notificar a callbacks registrados"""
        for callback in self.notification_callbacks:
            try:
                callback(result)
            except Exception as e:
                logger.error(f"Error en callback: {e}")
    
    def add_notification_callback(self, callback: Callable[[CaptureResult], None]):
        """Agregar callback para notificaciones"""
        self.notification_callbacks.append(callback)
    
    def _start_cleanup_thread(self):
        """Iniciar hilo de limpieza automática"""
        def cleanup_loop():
            while self.is_running:
                try:
                    self._cleanup_old_captures()
                    time.sleep(3600)  # Ejecutar cada hora
                except Exception as e:
                    logger.error(f"Error en limpieza automática: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_old_captures(self):
        """Limpiar capturas antiguas"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.config['cleanup_days'])
            
            screenshots_dir = self.config['capture_base_dir'] / "screenshots"
            
            deleted_count = 0
            freed_bytes = 0
            
            for date_dir in screenshots_dir.iterdir():
                if date_dir.is_dir():
                    try:
                        dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d")
                        
                        if dir_date < cutoff_date:
                            # Calcular tamaño total antes de eliminar
                            dir_size = sum(f.stat().st_size for f in date_dir.rglob('*') if f.is_file())
                            
                            # Eliminar directorio completo
                            import shutil
                            shutil.rmtree(date_dir)
                            
                            deleted_count += len(list(date_dir.glob('*')))
                            freed_bytes += dir_size
                            
                            logger.info(f"🗑️ Eliminado directorio antiguo: {date_dir.name}")
                            
                    except ValueError:
                        # Formato de fecha inválido, saltar
                        continue
            
            if deleted_count > 0:
                freed_mb = freed_bytes / (1024 * 1024)
                logger.info(f"🧹 Limpieza completada: {deleted_count} archivos eliminados, {freed_mb:.1f}MB liberados")
            
        except Exception as e:
            logger.error(f"Error en limpieza: {e}")
    
    def get_capture_statistics(self) -> Dict:
        """Obtener estadísticas del sistema de captura"""
        try:
            # Estadísticas de programación
            active_cameras = len([s for s in self.capture_schedules.values() if s.enabled])
            total_captures_today = 0
            
            # Estadísticas de archivos
            screenshots_dir = self.config['capture_base_dir'] / "screenshots"
            total_files = 0
            total_size_bytes = 0
            
            if screenshots_dir.exists():
                for file_path in screenshots_dir.rglob('*.jpg'):
                    if file_path.is_file():
                        total_files += 1
                        total_size_bytes += file_path.stat().st_size
            
            # Estadísticas de alertas
            alerts_today = len([
                a for a in self.alert_history 
                if a['timestamp'].date() == datetime.now().date()
            ])
            
            return {
                'system_status': 'running' if self.is_running else 'stopped',
                'active_cameras': active_cameras,
                'total_schedules': len(self.capture_schedules),
                'total_capture_files': total_files,
                'total_storage_mb': total_size_bytes / (1024 * 1024),
                'alerts_today': alerts_today,
                'total_alerts_history': len(self.alert_history),
                'capture_threads_active': len(self.capture_threads),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    def get_camera_status(self, camera_id: str) -> Dict:
        """Obtener estado de una cámara específica"""
        try:
            schedule = self.capture_schedules.get(camera_id)
            if not schedule:
                return {'error': 'Cámara no encontrada'}
            
            thread = self.capture_threads.get(camera_id)
            thread_active = thread.is_alive() if thread else False
            
            return {
                'camera_id': camera_id,
                'enabled': schedule.enabled,
                'risk_level': schedule.risk_level,
                'current_interval': schedule.adaptive_interval,
                'base_interval': schedule.interval_seconds,
                'last_capture': schedule.last_capture.isoformat() if schedule.last_capture else None,
                'consecutive_alerts': schedule.consecutive_alerts,
                'thread_active': thread_active,
                'priority': schedule.priority
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado de cámara: {e}")
            return {'error': str(e)}

# Función principal para testing
def main():
    """Función principal para testing"""
    capture_system = SmartCaptureSystem()
    
    # Iniciar monitoreo
    if capture_system.start_monitoring():
        print("✅ Sistema de captura iniciado")
        
        try:
            # Mantener ejecutándose por un tiempo
            time.sleep(30)
            
            # Mostrar estadísticas
            stats = capture_system.get_capture_statistics()
            print(f"\n📊 Estadísticas del sistema:")
            print(f"  • Estado: {stats.get('system_status')}")
            print(f"  • Cámaras activas: {stats.get('active_cameras')}")
            print(f"  • Archivos de captura: {stats.get('total_capture_files')}")
            print(f"  • Almacenamiento: {stats.get('total_storage_mb', 0):.1f}MB")
            print(f"  • Alertas hoy: {stats.get('alerts_today')}")
            
        finally:
            # Detener sistema
            capture_system.stop_monitoring()
            print("⏹️ Sistema detenido")
    else:
        print("❌ Error iniciando sistema de captura")

if __name__ == "__main__":
    main()