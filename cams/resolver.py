"""
Stream URL Resolver
==================

Módulo para resolver y extraer URLs de streaming de diferentes fuentes:
- YouTube Live
- Webcams municipales
- Cámaras de tráfico
- Streaming RTSP/HTTP directo
"""

import os
import re
import requests
import yt_dlp
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime, timedelta
import json
import time
import threading
from urllib.parse import urlparse, parse_qs
import subprocess

logger = logging.getLogger(__name__)

class StreamResolver:
    """
    Resolvedor de URLs de streaming
    """
    
    # Headers comunes para requests
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    # Patrones para diferentes tipos de URLs
    URL_PATTERNS = {
        'youtube_live': r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)',
        'youtube_channel': r'youtube\.com/(?:c/|channel/|@)([a-zA-Z0-9_-]+)',
        'rtsp': r'^rtsp://',
        'rtmp': r'^rtmp://',
        'hls': r'\.m3u8(?:\?|$)',
        'mjpeg': r'(?:\.mjpg|\.mjpeg|mjpeg_stream)',
        'webcam_generic': r'webcam|camera|cam(?:\d+)?\.(?:jpg|jpeg|png)',
        'traffic_cam': r'(?:traffic|road|highway).*(?:cam|camera)'
    }
    
    def __init__(self):
        """Inicializar el resolver"""
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)
        
        # Cache de URLs resueltas
        self.url_cache = {}
        self.cache_lock = threading.Lock()
        
        # Configuración de yt-dlp
        self.ytdl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extractaudio': False,
            'format': 'best[height<=720]',  # Calidad moderada para análisis
            'noplaylist': True
        }
        
        logger.info("🔗 StreamResolver inicializado")
    
    def resolve_url(self, url: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Resolver URL de streaming principal
        
        Args:
            url: URL original a resolver
            force_refresh: Forzar actualización del cache
            
        Returns:
            Diccionario con información del stream
        """
        # Verificar cache
        cache_key = url
        if not force_refresh and cache_key in self.url_cache:
            cached = self.url_cache[cache_key]
            # Verificar si el cache no ha expirado (30 minutos)
            if datetime.now() - cached['timestamp'] < timedelta(minutes=30):
                return cached['data']
        
        # Determinar tipo de URL
        url_type = self._detect_url_type(url)
        
        try:
            # Resolver según tipo
            if url_type == 'youtube_live':
                result = self._resolve_youtube_live(url)
            elif url_type == 'youtube_channel':
                result = self._resolve_youtube_channel(url)
            elif url_type in ['rtsp', 'rtmp']:
                result = self._resolve_direct_stream(url)
            elif url_type == 'hls':
                result = self._resolve_hls_stream(url)
            elif url_type == 'mjpeg':
                result = self._resolve_mjpeg_stream(url)
            else:
                result = self._resolve_generic_url(url)
            
            # Guardar en cache
            with self.cache_lock:
                self.url_cache[cache_key] = {
                    'timestamp': datetime.now(),
                    'data': result
                }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error resolviendo URL {url}: {e}")
            return {
                'success': False,
                'error': str(e),
                'url_type': url_type,
                'original_url': url
            }
    
    def _detect_url_type(self, url: str) -> str:
        """Detectar tipo de URL"""
        url_lower = url.lower()
        
        for pattern_type, pattern in self.URL_PATTERNS.items():
            if re.search(pattern, url_lower):
                return pattern_type
        
        # Detectar por extensión o protocolo
        if url.startswith('http'):
            if '.m3u8' in url:
                return 'hls'
            elif any(x in url_lower for x in ['mjpeg', 'mjpg']):
                return 'mjpeg'
            else:
                return 'http_generic'
        
        return 'unknown'
    
    def _resolve_youtube_live(self, url: str) -> Dict[str, Any]:
        """Resolver stream de YouTube Live"""
        try:
            with yt_dlp.YoutubeDL(self.ytdl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info.get('is_live', False):
                    return {
                        'success': False,
                        'error': 'El video no es un stream en vivo',
                        'url_type': 'youtube_live',
                        'original_url': url
                    }
                
                # Buscar formato adecuado
                formats = info.get('formats', [])
                best_format = None
                
                for fmt in formats:
                    if (fmt.get('ext') == 'mp4' and 
                        fmt.get('height', 0) <= 720 and
                        fmt.get('protocol') in ['https', 'http']):
                        best_format = fmt
                        break
                
                if not best_format:
                    # Usar primer formato disponible
                    best_format = formats[0] if formats else None
                
                if not best_format:
                    return {
                        'success': False,
                        'error': 'No se encontró formato de stream válido',
                        'url_type': 'youtube_live',
                        'original_url': url
                    }
                
                return {
                    'success': True,
                    'stream_url': best_format['url'],
                    'format': best_format.get('ext', 'unknown'),
                    'resolution': f"{best_format.get('width', '?')}x{best_format.get('height', '?')}",
                    'fps': best_format.get('fps', 'unknown'),
                    'title': info.get('title', 'YouTube Live Stream'),
                    'uploader': info.get('uploader', 'Unknown'),
                    'viewer_count': info.get('view_count', 0),
                    'url_type': 'youtube_live',
                    'original_url': url,
                    'headers': self.DEFAULT_HEADERS
                }
                
        except Exception as e:
            logger.error(f"❌ Error resolviendo YouTube Live {url}: {e}")
            return {
                'success': False,
                'error': f'Error de yt-dlp: {str(e)}',
                'url_type': 'youtube_live',
                'original_url': url
            }
    
    def _resolve_youtube_channel(self, url: str) -> Dict[str, Any]:
        """Resolver canal de YouTube para buscar streams en vivo"""
        try:
            # Extraer información del canal
            with yt_dlp.YoutubeDL(self.ytdl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Buscar videos en vivo en el canal
                entries = info.get('entries', [])
                live_streams = [e for e in entries if e.get('is_live', False)]
                
                if not live_streams:
                    return {
                        'success': False,
                        'error': 'No hay streams en vivo en este canal',
                        'url_type': 'youtube_channel',
                        'original_url': url
                    }
                
                # Usar el primer stream en vivo encontrado
                live_stream = live_streams[0]
                return self._resolve_youtube_live(live_stream['webpage_url'])
                
        except Exception as e:
            logger.error(f"❌ Error resolviendo canal YouTube {url}: {e}")
            return {
                'success': False,
                'error': f'Error resolviendo canal: {str(e)}',
                'url_type': 'youtube_channel',
                'original_url': url
            }
    
    def _resolve_direct_stream(self, url: str) -> Dict[str, Any]:
        """Resolver stream RTSP/RTMP directo"""
        try:
            # Para streams directos, verificar conectividad básica
            # usando ffprobe si está disponible
            
            result = {
                'success': True,
                'stream_url': url,
                'format': 'rtsp' if url.startswith('rtsp') else 'rtmp',
                'url_type': 'direct_stream',
                'original_url': url,
                'headers': {}
            }
            
            # Intentar obtener información con ffprobe
            try:
                probe_result = self._probe_stream_info(url)
                if probe_result:
                    result.update(probe_result)
            except:
                pass  # No es crítico si falla
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url_type': 'direct_stream',
                'original_url': url
            }
    
    def _resolve_hls_stream(self, url: str) -> Dict[str, Any]:
        """Resolver stream HLS (.m3u8)"""
        try:
            # Verificar que el stream HLS esté accesible
            response = self.session.head(url, timeout=10)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'stream_url': url,
                    'format': 'hls',
                    'url_type': 'hls',
                    'original_url': url,
                    'headers': self.DEFAULT_HEADERS
                }
            else:
                return {
                    'success': False,
                    'error': f'Stream no accesible: HTTP {response.status_code}',
                    'url_type': 'hls',
                    'original_url': url
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url_type': 'hls',
                'original_url': url
            }
    
    def _resolve_mjpeg_stream(self, url: str) -> Dict[str, Any]:
        """Resolver stream MJPEG"""
        try:
            # Test de conectividad para MJPEG
            response = self.session.head(url, timeout=10)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'stream_url': url,
                    'format': 'mjpeg',
                    'url_type': 'mjpeg',
                    'original_url': url,
                    'headers': self.DEFAULT_HEADERS
                }
            else:
                return {
                    'success': False,
                    'error': f'Stream MJPEG no accesible: HTTP {response.status_code}',
                    'url_type': 'mjpeg',
                    'original_url': url
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url_type': 'mjpeg',
                'original_url': url
            }
    
    def _resolve_generic_url(self, url: str) -> Dict[str, Any]:
        """Resolver URL genérica usando yt-dlp como fallback"""
        try:
            # Primero intentar acceso directo
            response = self.session.head(url, timeout=10)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                
                # Determinar formato por content-type
                if 'video' in content_type:
                    return {
                        'success': True,
                        'stream_url': url,
                        'format': 'video',
                        'content_type': content_type,
                        'url_type': 'http_video',
                        'original_url': url,
                        'headers': self.DEFAULT_HEADERS
                    }
                elif 'image' in content_type:
                    return {
                        'success': True,
                        'stream_url': url,
                        'format': 'image',
                        'content_type': content_type,
                        'url_type': 'http_image',
                        'original_url': url,
                        'headers': self.DEFAULT_HEADERS
                    }
            
            # Fallback: intentar con yt-dlp
            try:
                with yt_dlp.YoutubeDL(self.ytdl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    formats = info.get('formats', [])
                    if formats:
                        best_format = formats[0]
                        return {
                            'success': True,
                            'stream_url': best_format['url'],
                            'format': best_format.get('ext', 'unknown'),
                            'title': info.get('title', 'Stream'),
                            'url_type': 'generic_extracted',
                            'original_url': url,
                            'headers': self.DEFAULT_HEADERS
                        }
            except:
                pass  # yt-dlp failed, continue
            
            return {
                'success': False,
                'error': 'No se pudo resolver la URL',
                'url_type': 'generic',
                'original_url': url
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url_type': 'generic',
                'original_url': url
            }
    
    def _probe_stream_info(self, url: str) -> Optional[Dict]:
        """Obtener información del stream usando ffprobe"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                # Extraer información útil
                info = {}
                
                format_info = data.get('format', {})
                if 'duration' in format_info:
                    info['duration'] = format_info['duration']
                if 'bit_rate' in format_info:
                    info['bitrate'] = format_info['bit_rate']
                
                # Información de streams de video
                video_streams = [s for s in data.get('streams', []) if s.get('codec_type') == 'video']
                if video_streams:
                    vs = video_streams[0]
                    info['resolution'] = f"{vs.get('width', '?')}x{vs.get('height', '?')}"
                    info['fps'] = vs.get('r_frame_rate', 'unknown')
                    info['codec'] = vs.get('codec_name', 'unknown')
                
                return info
                
        except Exception as e:
            logger.debug(f"ffprobe falló para {url}: {e}")
            return None
    
    def batch_resolve(self, urls: List[str], max_workers: int = 5) -> Dict[str, Dict]:
        """
        Resolver múltiples URLs en paralelo
        
        Args:
            urls: Lista de URLs a resolver
            max_workers: Máximo número de workers concurrentes
            
        Returns:
            Diccionario {url: resultado}
        """
        import concurrent.futures
        
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Enviar tareas
            future_to_url = {
                executor.submit(self.resolve_url, url): url 
                for url in urls
            }
            
            # Recoger resultados
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result(timeout=30)
                    results[url] = result
                except Exception as e:
                    results[url] = {
                        'success': False,
                        'error': f'Timeout o error: {str(e)}',
                        'original_url': url
                    }
        
        return results
    
    def test_stream_connectivity(self, stream_url: str, headers: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Testear conectividad de un stream
        
        Args:
            stream_url: URL del stream a testear
            headers: Headers opcionales
            
        Returns:
            Resultado del test
        """
        try:
            test_headers = headers or self.DEFAULT_HEADERS
            
            start_time = time.time()
            response = self.session.head(stream_url, headers=test_headers, timeout=15)
            response_time = (time.time() - start_time) * 1000  # ms
            
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'response_time_ms': response_time,
                'content_type': response.headers.get('content-type'),
                'content_length': response.headers.get('content-length'),
                'server': response.headers.get('server'),
                'accessible': True
            }
            
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Timeout',
                'accessible': False
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Connection Error',
                'accessible': False
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'accessible': False
            }
    
    def get_cache_stats(self) -> Dict:
        """Obtener estadísticas del cache"""
        with self.cache_lock:
            now = datetime.now()
            active_entries = sum(1 for entry in self.url_cache.values() 
                               if now - entry['timestamp'] < timedelta(minutes=30))
            
            return {
                'total_entries': len(self.url_cache),
                'active_entries': active_entries,
                'expired_entries': len(self.url_cache) - active_entries
            }
    
    def clear_cache(self, expired_only: bool = True):
        """Limpiar cache"""
        with self.cache_lock:
            if not expired_only:
                self.url_cache.clear()
                logger.info("🗑️ Cache completamente limpiado")
            else:
                now = datetime.now()
                expired_keys = [
                    key for key, entry in self.url_cache.items()
                    if now - entry['timestamp'] > timedelta(minutes=30)
                ]
                
                for key in expired_keys:
                    del self.url_cache[key]
                
                logger.info(f"🗑️ {len(expired_keys)} entradas expiradas eliminadas del cache")


if __name__ == "__main__":
    # Test del resolver
    resolver = StreamResolver()
    
    # Test URLs
    test_urls = [
        "rtsp://example.com/stream",
        "https://example.com/stream.m3u8",
    ]
    
    for url in test_urls:
        print(f"\nTestando: {url}")
        result = resolver.resolve_url(url)
        print(f"Resultado: {result}")
    
    print(f"\nEstadísticas del cache: {resolver.get_cache_stats()}")
