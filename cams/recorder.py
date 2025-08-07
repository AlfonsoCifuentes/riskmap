"""
Video Recorder
==============

Sistema de grabación de video para streams de cámaras:
- Grabación continua en segmentos
- Grabación activada por alertas
- Gestión de almacenamiento
- Generación de thumbnails
"""

import os
import cv2
import numpy as np
import threading
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import logging
from pathlib import Path
import subprocess
import shutil
from collections import deque

logger = logging.getLogger(__name__)

class VideoRecorder:
    """
    Grabador de video para streams de cámaras
    """
    
    def __init__(self, 
                 storage_path: str = "static/recordings",
                 thumb_path: str = "static/thumbs",
                 max_storage_gb: float = 50.0,
                 segment_duration: int = 300,  # 5 minutos
                 alert_buffer_seconds: int = 30):
        """
        Inicializar el grabador
        
        Args:
            storage_path: Directorio para almacenar grabaciones
            thumb_path: Directorio para thumbnails
            max_storage_gb: Máximo espacio de almacenamiento en GB
            segment_duration: Duración de segmentos en segundos
            alert_buffer_seconds: Buffer antes/después de alertas
        """
        self.storage_path = Path(storage_path)
        self.thumb_path = Path(thumb_path)
        self.max_storage_bytes = max_storage_gb * 1024 * 1024 * 1024
        self.segment_duration = segment_duration
        self.alert_buffer_seconds = alert_buffer_seconds
        
        # Crear directorios
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.thumb_path.mkdir(parents=True, exist_ok=True)
        
        # Estado de grabadores activos
        self.active_recorders = {}
        self.recorder_lock = threading.Lock()
        
        # Buffer de frames para grabación de alertas
        self.frame_buffers = {}
        self.buffer_lock = threading.Lock()
        
        # Configuración de codecs
        self.video_codec = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_fps = int(os.getenv('RECORDING_FPS', '15'))
        
        # Hilo de limpieza de almacenamiento
        self.cleanup_thread = None
        self.running = True
        self._start_cleanup_thread()
        
        logger.info(f"📹 VideoRecorder inicializado - Storage: {storage_path}, Max: {max_storage_gb}GB")
    
    def start_continuous_recording(self, cam_id: str, stream_url: str, 
                                 headers: Optional[Dict] = None) -> bool:
        """
        Iniciar grabación continua para una cámara
        
        Args:
            cam_id: ID de la cámara
            stream_url: URL del stream
            headers: Headers para el stream
            
        Returns:
            True si se inició correctamente
        """
        with self.recorder_lock:
            if cam_id in self.active_recorders:
                logger.warning(f"⚠️ Grabación ya activa para cámara {cam_id}")
                return False
        
        try:
            # Crear directorio para la cámara
            cam_dir = self.storage_path / cam_id
            cam_dir.mkdir(exist_ok=True)
            
            # Inicializar buffer de frames
            with self.buffer_lock:
                self.frame_buffers[cam_id] = deque(maxlen=self.alert_buffer_seconds * self.video_fps)
            
            # Crear y iniciar hilo de grabación
            recorder_thread = threading.Thread(
                target=self._continuous_recording_worker,
                args=(cam_id, stream_url, headers),
                daemon=True
            )
            
            with self.recorder_lock:
                self.active_recorders[cam_id] = {
                    'thread': recorder_thread,
                    'stream_url': stream_url,
                    'headers': headers,
                    'start_time': datetime.now(),
                    'status': 'starting',
                    'current_segment': None,
                    'total_segments': 0,
                    'last_frame_time': None
                }
            
            recorder_thread.start()
            logger.info(f"📹 Iniciada grabación continua para cámara {cam_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error iniciando grabación para {cam_id}: {e}")
            return False
    
    def stop_recording(self, cam_id: str) -> bool:
        """
        Detener grabación para una cámara
        
        Args:
            cam_id: ID de la cámara
            
        Returns:
            True si se detuvo correctamente
        """
        with self.recorder_lock:
            if cam_id not in self.active_recorders:
                logger.warning(f"⚠️ No hay grabación activa para cámara {cam_id}")
                return False
            
            # Marcar para detener
            recorder_info = self.active_recorders[cam_id]
            recorder_info['status'] = 'stopping'
        
        # Esperar a que termine el hilo
        try:
            recorder_info['thread'].join(timeout=10)
            
            with self.recorder_lock:
                del self.active_recorders[cam_id]
            
            with self.buffer_lock:
                if cam_id in self.frame_buffers:
                    del self.frame_buffers[cam_id]
            
            logger.info(f"⏹️ Grabación detenida para cámara {cam_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error deteniendo grabación para {cam_id}: {e}")
            return False
    
    def record_alert_clip(self, cam_id: str, alert_info: Dict, 
                         duration_after: int = 30) -> Optional[str]:
        """
        Grabar clip de alerta usando buffer pre-existente
        
        Args:
            cam_id: ID de la cámara
            alert_info: Información de la alerta
            duration_after: Duración adicional después de la alerta
            
        Returns:
            Ruta del archivo grabado o None si falló
        """
        try:
            # Crear directorio de alertas
            alert_dir = self.storage_path / cam_id / "alerts"
            alert_dir.mkdir(exist_ok=True)
            
            # Generar nombre de archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            alert_type = alert_info.get('type', 'unknown')
            filename = f"alert_{alert_type}_{timestamp}.mp4"
            output_path = alert_dir / filename
            
            # Obtener frames del buffer
            with self.buffer_lock:
                if cam_id not in self.frame_buffers:
                    logger.error(f"❌ No hay buffer de frames para {cam_id}")
                    return None
                
                # Copiar frames del buffer (pre-alerta)
                buffered_frames = list(self.frame_buffers[cam_id])
            
            if not buffered_frames:
                logger.error(f"❌ Buffer vacío para {cam_id}")
                return None
            
            # Inicializar writer de video
            frame_height, frame_width = buffered_frames[0].shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(
                str(output_path), 
                fourcc, 
                self.video_fps, 
                (frame_width, frame_height)
            )
            
            if not out.isOpened():
                logger.error(f"❌ No se pudo abrir writer para {output_path}")
                return None
            
            # Escribir frames del buffer (pre-alerta)
            for frame in buffered_frames:
                out.write(frame)
            
            # Continuar grabando por duration_after segundos
            frames_after = duration_after * self.video_fps
            frames_written = 0
            
            # Obtener frames adicionales del stream activo
            recorder_info = self.active_recorders.get(cam_id)
            if recorder_info and recorder_info['status'] == 'recording':
                # TODO: Implementar captura de frames adicionales
                # Por ahora, simplemente duplicar último frame
                last_frame = buffered_frames[-1]
                for _ in range(frames_after):
                    out.write(last_frame)
                    frames_written += 1
            
            out.release()
            
            # Generar thumbnail
            thumb_path = self._generate_thumbnail(output_path, buffered_frames[-1])
            
            # Guardar metadata
            metadata = {
                'cam_id': cam_id,
                'alert_info': alert_info,
                'timestamp': datetime.now().isoformat(),
                'duration_seconds': len(buffered_frames) / self.video_fps + duration_after,
                'frames_total': len(buffered_frames) + frames_written,
                'file_size': output_path.stat().st_size,
                'thumbnail': str(thumb_path) if thumb_path else None
            }
            
            metadata_path = output_path.with_suffix('.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"🎬 Clip de alerta grabado: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"❌ Error grabando clip de alerta para {cam_id}: {e}")
            return None
    
    def _continuous_recording_worker(self, cam_id: str, stream_url: str, 
                                   headers: Optional[Dict] = None):
        """Worker para grabación continua"""
        try:
            # Abrir stream de video
            cap = self._open_video_stream(stream_url, headers)
            if cap is None:
                with self.recorder_lock:
                    self.active_recorders[cam_id]['status'] = 'error'
                return
            
            with self.recorder_lock:
                self.active_recorders[cam_id]['status'] = 'recording'
            
            segment_start_time = time.time()
            current_writer = None
            frame_count = 0
            
            while self.running and self.active_recorders.get(cam_id, {}).get('status') == 'recording':
                ret, frame = cap.read()
                
                if not ret:
                    logger.warning(f"⚠️ No se pudo leer frame de {cam_id}")
                    time.sleep(1)
                    continue
                
                # Actualizar buffer de frames para alertas
                with self.buffer_lock:
                    if cam_id in self.frame_buffers:
                        self.frame_buffers[cam_id].append(frame.copy())
                
                # Verificar si necesitamos nuevo segmento
                current_time = time.time()
                if (current_writer is None or 
                    current_time - segment_start_time >= self.segment_duration):
                    
                    # Cerrar writer anterior
                    if current_writer is not None:
                        current_writer.release()
                        self._finalize_segment(cam_id, current_segment_path, frame_count)
                    
                    # Crear nuevo segmento
                    current_segment_path, current_writer = self._create_new_segment(cam_id, frame)
                    if current_writer is None:
                        logger.error(f"❌ No se pudo crear nuevo segmento para {cam_id}")
                        break
                    
                    segment_start_time = current_time
                    frame_count = 0
                    
                    with self.recorder_lock:
                        self.active_recorders[cam_id]['current_segment'] = current_segment_path
                        self.active_recorders[cam_id]['total_segments'] += 1
                
                # Escribir frame
                if current_writer is not None:
                    current_writer.write(frame)
                    frame_count += 1
                
                # Actualizar timestamp
                with self.recorder_lock:
                    self.active_recorders[cam_id]['last_frame_time'] = datetime.now()
                
                # Control de FPS
                time.sleep(1.0 / self.video_fps)
            
            # Limpiar al finalizar
            if current_writer is not None:
                current_writer.release()
                self._finalize_segment(cam_id, current_segment_path, frame_count)
            
            cap.release()
            
            with self.recorder_lock:
                if cam_id in self.active_recorders:
                    self.active_recorders[cam_id]['status'] = 'stopped'
            
            logger.info(f"📹 Grabación continua finalizada para {cam_id}")
            
        except Exception as e:
            logger.error(f"❌ Error en grabación continua para {cam_id}: {e}")
            with self.recorder_lock:
                if cam_id in self.active_recorders:
                    self.active_recorders[cam_id]['status'] = 'error'
    
    def _open_video_stream(self, stream_url: str, headers: Optional[Dict] = None) -> Optional[cv2.VideoCapture]:
        """Abrir stream de video"""
        try:
            # Para streams HTTP/HTTPS, configurar headers si es necesario
            cap = cv2.VideoCapture(stream_url)
            
            if not cap.isOpened():
                logger.error(f"❌ No se pudo abrir stream: {stream_url}")
                return None
            
            # Configurar buffer mínimo para reducir latencia
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            return cap
            
        except Exception as e:
            logger.error(f"❌ Error abriendo stream {stream_url}: {e}")
            return None
    
    def _create_new_segment(self, cam_id: str, sample_frame: np.ndarray) -> tuple:
        """Crear nuevo segmento de grabación"""
        try:
            # Generar nombre de archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"segment_{timestamp}.mp4"
            output_path = self.storage_path / cam_id / filename
            
            # Crear writer
            frame_height, frame_width = sample_frame.shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(
                str(output_path), 
                fourcc, 
                self.video_fps, 
                (frame_width, frame_height)
            )
            
            if not writer.isOpened():
                logger.error(f"❌ No se pudo crear writer para {output_path}")
                return None, None
            
            logger.debug(f"📹 Nuevo segmento creado: {output_path}")
            return str(output_path), writer
            
        except Exception as e:
            logger.error(f"❌ Error creando segmento para {cam_id}: {e}")
            return None, None
    
    def _finalize_segment(self, cam_id: str, segment_path: str, frame_count: int):
        """Finalizar segmento y generar metadata"""
        try:
            if not os.path.exists(segment_path):
                return
            
            # Generar thumbnail del último frame
            # (simplificado - en una implementación completa, se tomaría el frame medio)
            
            # Guardar metadata del segmento
            metadata = {
                'cam_id': cam_id,
                'timestamp': datetime.now().isoformat(),
                'frame_count': frame_count,
                'duration_seconds': frame_count / self.video_fps,
                'file_size': os.path.getsize(segment_path),
                'fps': self.video_fps
            }
            
            metadata_path = Path(segment_path).with_suffix('.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.debug(f"📹 Segmento finalizado: {segment_path} ({frame_count} frames)")
            
        except Exception as e:
            logger.error(f"❌ Error finalizando segmento {segment_path}: {e}")
    
    def _generate_thumbnail(self, video_path: str, frame: Optional[np.ndarray] = None) -> Optional[str]:
        """Generar thumbnail para un video"""
        try:
            video_name = Path(video_path).stem
            thumb_path = self.thumb_path / f"{video_name}.jpg"
            
            if frame is not None:
                # Usar frame proporcionado
                thumbnail = frame
            else:
                # Extraer frame del video
                cap = cv2.VideoCapture(video_path)
                if not cap.isOpened():
                    return None
                
                # Ir al frame medio
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)
                
                ret, thumbnail = cap.read()
                cap.release()
                
                if not ret:
                    return None
            
            # Redimensionar thumbnail
            height, width = thumbnail.shape[:2]
            if width > 320:
                ratio = 320 / width
                new_width = 320
                new_height = int(height * ratio)
                thumbnail = cv2.resize(thumbnail, (new_width, new_height))
            
            # Guardar thumbnail
            cv2.imwrite(str(thumb_path), thumbnail)
            
            return str(thumb_path)
            
        except Exception as e:
            logger.error(f"❌ Error generando thumbnail para {video_path}: {e}")
            return None
    
    def _start_cleanup_thread(self):
        """Iniciar hilo de limpieza de almacenamiento"""
        def cleanup_worker():
            while self.running:
                try:
                    self._cleanup_storage()
                    time.sleep(3600)  # Limpiar cada hora
                except Exception as e:
                    logger.error(f"❌ Error en limpieza de almacenamiento: {e}")
                    time.sleep(300)  # Reintentar en 5 minutos
        
        self.cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self.cleanup_thread.start()
    
    def _cleanup_storage(self):
        """Limpiar almacenamiento eliminando archivos antiguos"""
        try:
            # Calcular uso actual de almacenamiento
            total_size = self._get_directory_size(self.storage_path)
            
            if total_size <= self.max_storage_bytes:
                return  # No es necesario limpiar
            
            logger.info(f"🧹 Iniciando limpieza de almacenamiento: {total_size / (1024**3):.2f}GB / {self.max_storage_bytes / (1024**3):.2f}GB")
            
            # Obtener lista de archivos con timestamps
            files_with_time = []
            for cam_dir in self.storage_path.iterdir():
                if cam_dir.is_dir():
                    for file_path in cam_dir.rglob("*.mp4"):
                        if file_path.is_file():
                            files_with_time.append((
                                file_path.stat().st_mtime,
                                file_path,
                                file_path.stat().st_size
                            ))
            
            # Ordenar por timestamp (más antiguos primero)
            files_with_time.sort(key=lambda x: x[0])
            
            # Eliminar archivos hasta estar bajo el límite
            bytes_to_remove = total_size - int(self.max_storage_bytes * 0.8)  # Margen del 20%
            bytes_removed = 0
            files_removed = 0
            
            for mtime, file_path, file_size in files_with_time:
                if bytes_removed >= bytes_to_remove:
                    break
                
                try:
                    # Eliminar archivo de video
                    file_path.unlink()
                    bytes_removed += file_size
                    files_removed += 1
                    
                    # Eliminar metadata asociada
                    metadata_path = file_path.with_suffix('.json')
                    if metadata_path.exists():
                        metadata_path.unlink()
                    
                    # Eliminar thumbnail asociado
                    thumb_path = self.thumb_path / f"{file_path.stem}.jpg"
                    if thumb_path.exists():
                        thumb_path.unlink()
                    
                except Exception as e:
                    logger.error(f"❌ Error eliminando {file_path}: {e}")
            
            logger.info(f"🧹 Limpieza completada: {files_removed} archivos eliminados, {bytes_removed / (1024**3):.2f}GB liberados")
            
        except Exception as e:
            logger.error(f"❌ Error en limpieza de almacenamiento: {e}")
    
    def _get_directory_size(self, path: Path) -> int:
        """Calcular tamaño total de un directorio"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
        return total_size
    
    def get_recording_status(self, cam_id: Optional[str] = None) -> Dict:
        """Obtener estado de grabaciones"""
        with self.recorder_lock:
            if cam_id:
                return self.active_recorders.get(cam_id, {})
            return self.active_recorders.copy()
    
    def get_recordings(self, cam_id: str, limit: int = 20) -> List[Dict]:
        """Obtener lista de grabaciones para una cámara"""
        try:
            cam_dir = self.storage_path / cam_id
            if not cam_dir.exists():
                return []
            
            recordings = []
            
            # Buscar archivos de video
            for video_file in cam_dir.rglob("*.mp4"):
                metadata_file = video_file.with_suffix('.json')
                
                recording_info = {
                    'file_path': str(video_file),
                    'filename': video_file.name,
                    'size_bytes': video_file.stat().st_size,
                    'created_time': datetime.fromtimestamp(video_file.stat().st_ctime).isoformat(),
                    'type': 'alert' if 'alerts' in str(video_file) else 'continuous'
                }
                
                # Cargar metadata si existe
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        recording_info.update(metadata)
                    except:
                        pass
                
                # Buscar thumbnail
                thumb_path = self.thumb_path / f"{video_file.stem}.jpg"
                if thumb_path.exists():
                    recording_info['thumbnail'] = str(thumb_path)
                
                recordings.append(recording_info)
            
            # Ordenar por timestamp descendente
            recordings.sort(key=lambda x: x.get('created_time', ''), reverse=True)
            
            return recordings[:limit]
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo grabaciones para {cam_id}: {e}")
            return []
    
    def get_storage_stats(self) -> Dict:
        """Obtener estadísticas de almacenamiento"""
        try:
            total_size = self._get_directory_size(self.storage_path)
            
            # Contar archivos por tipo
            video_count = len(list(self.storage_path.rglob("*.mp4")))
            thumb_count = len(list(self.thumb_path.rglob("*.jpg")))
            
            return {
                'total_size_bytes': total_size,
                'total_size_gb': total_size / (1024**3),
                'max_size_gb': self.max_storage_bytes / (1024**3),
                'usage_percentage': (total_size / self.max_storage_bytes) * 100,
                'video_files': video_count,
                'thumbnail_files': thumb_count,
                'active_recorders': len(self.active_recorders),
                'storage_path': str(self.storage_path)
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas de almacenamiento: {e}")
            return {}
    
    def cleanup(self):
        """Limpiar recursos del grabador"""
        self.running = False
        
        # Detener todas las grabaciones
        with self.recorder_lock:
            for cam_id in list(self.active_recorders.keys()):
                self.stop_recording(cam_id)
        
        # Esperar a que termine el hilo de limpieza
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=5)
        
        logger.info("📹 VideoRecorder limpiado")


if __name__ == "__main__":
    # Test del grabador
    recorder = VideoRecorder()
    print(f"Estadísticas de almacenamiento: {recorder.get_storage_stats()}")
    print(f"Estado de grabaciones: {recorder.get_recording_status()}")
