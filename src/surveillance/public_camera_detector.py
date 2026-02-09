"""
Public Camera Detector for Geopolitical Conflict Zones
======================================================

Sistema para detectar y gestionar cámaras públicas en zonas de conflicto geopolítico.
Integra con múltiples APIs y servicios para encontrar streams públicos accesibles.

Features:
- Detección geográfica de cámaras públicas
- Filtrado por zonas de conflicto activo
- Integración con artículos geopolíticos
- APIs múltiples para cobertura global
"""

import os
import json
import logging
import requests
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class PublicCamera:
    """Representa una cámara pública detectada"""
    camera_id: str
    name: str
    location: str
    latitude: float
    longitude: float
    stream_url: str
    provider: str
    country: str = ""
    city: str = ""
    status: str = "active"
    last_verified: datetime = None
    conflict_zone: bool = False
    risk_level: str = "low"
    additional_info: Dict = None

class PublicCameraDetector:
    """
    Detector de cámaras públicas en zonas de conflicto
    """
    
    def __init__(self, db_path: str = "./data/geopolitical_intel.db"):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.timeout = 10
        
        # APIs de cámaras públicas conocidas
        self.camera_apis = {
            'windy_webcams': {
                'base_url': 'https://api.windy.com/api/webcams/v2',
                'requires_key': True,
                'key_env': 'WINDY_API_KEY'
            },
            'webcams_travel': {
                'base_url': 'https://webcamstravel.p.rapidapi.com',
                'requires_key': True,
                'key_env': 'RAPIDAPI_KEY'
            },
            'traffic_cams': {
                'base_url': 'https://api.traffic-cameras.com',
                'requires_key': False
            }
        }
        
        # Zonas de conflicto conocidas (actualizadas dinámicamente)
        self.conflict_zones = self._load_conflict_zones()
        
        # Inicializar base de datos
        self._init_database()
        
    def _init_database(self):
        """Inicializar tablas de base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Tabla de cámaras públicas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS public_cameras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    camera_id VARCHAR(100) UNIQUE,
                    name VARCHAR(200),
                    location VARCHAR(200),
                    latitude REAL,
                    longitude REAL,
                    stream_url TEXT,
                    provider VARCHAR(100),
                    country VARCHAR(100),
                    city VARCHAR(100),
                    status VARCHAR(50) DEFAULT 'active',
                    last_verified TIMESTAMP,
                    conflict_zone BOOLEAN DEFAULT 0,
                    risk_level VARCHAR(50) DEFAULT 'low',
                    additional_info TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de capturas automáticas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS auto_captures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    camera_id VARCHAR(100),
                    capture_path TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    cv_analysis TEXT,
                    risk_score REAL DEFAULT 0.0,
                    indicators_detected TEXT,
                    alert_generated BOOLEAN DEFAULT 0,
                    article_related_id INTEGER,
                    conflict_indicators TEXT,
                    frame_analysis TEXT,
                    FOREIGN KEY (article_related_id) REFERENCES unified_articles(id),
                    FOREIGN KEY (camera_id) REFERENCES public_cameras(camera_id)
                )
            ''')
            
            # Tabla de alertas de conflicto
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conflict_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    camera_id VARCHAR(100),
                    capture_id INTEGER,
                    alert_type VARCHAR(100),
                    severity_level VARCHAR(50),
                    description TEXT,
                    coordinates TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    acknowledged BOOLEAN DEFAULT 0,
                    related_article_id INTEGER,
                    auto_generated BOOLEAN DEFAULT 1,
                    confidence_score REAL DEFAULT 0.0,
                    FOREIGN KEY (capture_id) REFERENCES auto_captures(id),
                    FOREIGN KEY (camera_id) REFERENCES public_cameras(camera_id),
                    FOREIGN KEY (related_article_id) REFERENCES unified_articles(id)
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("✅ Base de datos de cámaras públicas inicializada")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando base de datos: {e}")
    
    def _load_conflict_zones(self) -> List[Dict]:
        """Cargar zonas de conflicto desde artículos geopolíticos"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Obtener ubicaciones de artículos de alto riesgo
            cursor.execute('''
                SELECT DISTINCT 
                    country, region, location_extracted,
                    latitude, longitude,
                    AVG(COALESCE(risk_score, 50)) as avg_risk,
                    COUNT(*) as article_count
                FROM unified_articles 
                WHERE geopolitical_relevance = 1 
                AND risk_level IN ('high', 'medium')
                AND created_at > datetime('now', '-30 days')
                AND (latitude IS NOT NULL OR country IS NOT NULL)
                GROUP BY country, region, location_extracted, latitude, longitude
                HAVING avg_risk > 60 OR article_count >= 3
                ORDER BY avg_risk DESC, article_count DESC
            ''')
            
            conflict_zones = []
            for row in cursor.fetchall():
                country, region, location, lat, lon, avg_risk, count = row
                
                # Determinar nombre de zona
                zone_name = location or region or country or "Zona desconocida"
                
                # Coordenadas por defecto si no están disponibles
                if not lat or not lon:
                    lat, lon = self._get_default_coordinates(country)
                
                conflict_zones.append({
                    'name': zone_name,
                    'country': country or 'Unknown',
                    'region': region or '',
                    'latitude': float(lat) if lat else 0.0,
                    'longitude': float(lon) if lon else 0.0,
                    'risk_level': 'high' if avg_risk > 70 else 'medium',
                    'article_count': count,
                    'avg_risk_score': avg_risk
                })
            
            conn.close()
            
            # Agregar zonas de conflicto conocidas si la detección automática es insuficiente
            if len(conflict_zones) < 5:
                conflict_zones.extend(self._get_default_conflict_zones())
            
            logger.info(f"🗺️ Cargadas {len(conflict_zones)} zonas de conflicto")
            return conflict_zones[:20]  # Limitar a 20 zonas prioritarias
            
        except Exception as e:
            logger.error(f"Error cargando zonas de conflicto: {e}")
            return self._get_default_conflict_zones()
    
    def _get_default_coordinates(self, country: str) -> Tuple[float, float]:
        """Obtener coordenadas por defecto para países"""
        default_coords = {
            'ukraine': (50.4501, 30.5234),  # Kiev
            'israel': (31.7683, 35.2137),   # Jerusalén
            'palestine': (31.5, 34.45),     # Gaza
            'syria': (33.5138, 36.2765),    # Damasco
            'lebanon': (33.8547, 35.8623),  # Beirut
            'iran': (35.6892, 51.3890),     # Teherán
            'russia': (55.7558, 37.6173),   # Moscú
            'china': (39.9042, 116.4074),   # Beijing
            'taiwan': (25.0320, 121.5654),  # Taipei
        }
        
        if country:
            country_lower = country.lower()
            for key, coords in default_coords.items():
                if key in country_lower:
                    return coords
        
        return (0.0, 0.0)  # Fallback
    
    def _get_default_conflict_zones(self) -> List[Dict]:
        """Zonas de conflicto por defecto"""
        return [
            {
                'name': 'Gaza Strip',
                'country': 'Palestine',
                'region': 'Middle East',
                'latitude': 31.5,
                'longitude': 34.45,
                'risk_level': 'high',
                'article_count': 50,
                'avg_risk_score': 85
            },
            {
                'name': 'Eastern Ukraine',
                'country': 'Ukraine',
                'region': 'Eastern Europe',
                'latitude': 48.5132,
                'longitude': 35.2981,
                'risk_level': 'high',
                'article_count': 45,
                'avg_risk_score': 82
            },
            {
                'name': 'West Bank',
                'country': 'Palestine',
                'region': 'Middle East',
                'latitude': 31.9522,
                'longitude': 35.2332,
                'risk_level': 'high',
                'article_count': 30,
                'avg_risk_score': 78
            },
            {
                'name': 'Lebanon-Israel Border',
                'country': 'Lebanon',
                'region': 'Middle East',
                'latitude': 33.2774,
                'longitude': 35.4662,
                'risk_level': 'medium',
                'article_count': 25,
                'avg_risk_score': 70
            },
            {
                'name': 'Taiwan Strait',
                'country': 'Taiwan',
                'region': 'Asia Pacific',
                'latitude': 23.8103,
                'longitude': 120.9605,
                'risk_level': 'medium',
                'article_count': 20,
                'avg_risk_score': 65
            }
        ]
    
    def detect_cameras_in_conflict_zones(self, max_cameras_per_zone: int = 10) -> List[PublicCamera]:
        """
        Detectar cámaras públicas en todas las zonas de conflicto identificadas
        """
        logger.info(f"🔍 Iniciando detección de cámaras en {len(self.conflict_zones)} zonas de conflicto")
        
        all_cameras = []
        
        for zone in self.conflict_zones:
            try:
                logger.info(f"🎥 Buscando cámaras en: {zone['name']}")
                
                cameras_in_zone = self._search_cameras_in_radius(
                    lat=zone['latitude'],
                    lon=zone['longitude'],
                    radius_km=50,  # 50km de radio
                    max_results=max_cameras_per_zone
                )
                
                # Marcar como zona de conflicto
                for camera in cameras_in_zone:
                    camera.conflict_zone = True
                    camera.risk_level = zone['risk_level']
                    camera.country = zone['country']
                
                all_cameras.extend(cameras_in_zone)
                
                logger.info(f"✅ Encontradas {len(cameras_in_zone)} cámaras en {zone['name']}")
                
            except Exception as e:
                logger.error(f"❌ Error detectando cámaras en {zone['name']}: {e}")
        
        # Guardar en base de datos
        saved_count = self._save_cameras_to_db(all_cameras)
        
        logger.info(f"🎯 Detección completada: {len(all_cameras)} cámaras encontradas, {saved_count} guardadas")
        
        return all_cameras
    
    def _search_cameras_in_radius(self, lat: float, lon: float, radius_km: int, max_results: int = 10) -> List[PublicCamera]:
        """Buscar cámaras en un radio específico"""
        cameras = []
        
        # Intentar múltiples APIs
        for api_name, api_config in self.camera_apis.items():
            try:
                api_cameras = self._query_api(api_name, lat, lon, radius_km, max_results // len(self.camera_apis))
                cameras.extend(api_cameras)
            except Exception as e:
                logger.warning(f"⚠️ API {api_name} falló: {e}")
        
        # Si no encontramos cámaras reales, generar cámaras de demostración
        if len(cameras) == 0:
            cameras = self._generate_demo_cameras(lat, lon, max_results)
        
        return cameras[:max_results]
    
    def _query_api(self, api_name: str, lat: float, lon: float, radius_km: int, max_results: int) -> List[PublicCamera]:
        """Consultar una API específica de cámaras"""
        api_config = self.camera_apis[api_name]
        cameras = []
        
        try:
            if api_name == 'windy_webcams':
                cameras = self._query_windy_webcams(lat, lon, radius_km, max_results)
            elif api_name == 'webcams_travel':
                cameras = self._query_webcams_travel(lat, lon, radius_km, max_results)
            elif api_name == 'traffic_cams':
                cameras = self._query_traffic_cams(lat, lon, radius_km, max_results)
                
        except Exception as e:
            logger.warning(f"Error querying {api_name}: {e}")
        
        return cameras
    
    def _query_windy_webcams(self, lat: float, lon: float, radius_km: int, max_results: int) -> List[PublicCamera]:
        """Consultar Windy Webcams API"""
        api_key = os.getenv('WINDY_API_KEY')
        if not api_key:
            logger.warning("⚠️ WINDY_API_KEY no encontrada")
            return []
        
        url = f"https://api.windy.com/api/webcams/v2/list/nearby={lat},{lon},{radius_km}"
        params = {
            'show': 'webcams:basic,location,player',
            'limit': max_results,
            'key': api_key
        }
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        cameras = []
        
        for webcam in data.get('result', {}).get('webcams', []):
            try:
                camera = PublicCamera(
                    camera_id=f"windy_{webcam['id']}",
                    name=webcam.get('title', 'Windy Webcam'),
                    location=webcam.get('location', {}).get('city', 'Unknown'),
                    latitude=webcam.get('location', {}).get('latitude', lat),
                    longitude=webcam.get('location', {}).get('longitude', lon),
                    stream_url=webcam.get('player', {}).get('live', {}).get('embed', ''),
                    provider='windy_webcams',
                    country=webcam.get('location', {}).get('country', 'Unknown'),
                    city=webcam.get('location', {}).get('city', 'Unknown'),
                    additional_info={'api_data': webcam}
                )
                cameras.append(camera)
            except Exception as e:
                logger.warning(f"Error procesando webcam Windy: {e}")
        
        return cameras
    
    def _query_webcams_travel(self, lat: float, lon: float, radius_km: int, max_results: int) -> List[PublicCamera]:
        """Consultar Webcams.travel API via RapidAPI"""
        api_key = os.getenv('RAPIDAPI_KEY')
        if not api_key:
            logger.warning("⚠️ RAPIDAPI_KEY no encontrada")
            return []
        
        url = "https://webcamstravel.p.rapidapi.com/webcams/list/nearby"
        params = {
            'lat': lat,
            'lon': lon,
            'radius': radius_km,
            'limit': max_results
        }
        headers = {
            'X-RapidAPI-Key': api_key,
            'X-RapidAPI-Host': 'webcamstravel.p.rapidapi.com'
        }
        
        response = self.session.get(url, params=params, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        cameras = []
        
        for webcam in data.get('result', {}).get('webcams', []):
            try:
                camera = PublicCamera(
                    camera_id=f"travel_{webcam['id']}",
                    name=webcam.get('title', 'Travel Webcam'),
                    location=webcam.get('location', {}).get('city', 'Unknown'),
                    latitude=webcam.get('location', {}).get('latitude', lat),
                    longitude=webcam.get('location', {}).get('longitude', lon),
                    stream_url=webcam.get('images', {}).get('current', {}).get('preview', ''),
                    provider='webcams_travel',
                    country=webcam.get('location', {}).get('country', 'Unknown'),
                    city=webcam.get('location', {}).get('city', 'Unknown'),
                    additional_info={'api_data': webcam}
                )
                cameras.append(camera)
            except Exception as e:
                logger.warning(f"Error procesando webcam Travel: {e}")
        
        return cameras
    
    def _query_traffic_cams(self, lat: float, lon: float, radius_km: int, max_results: int) -> List[PublicCamera]:
        """Consultar APIs de cámaras de tráfico (simulado)"""
        # Esta es una implementación de demostración
        # En producción, se integraría con APIs reales de cámaras de tráfico
        return []
    
    def _generate_demo_cameras(self, lat: float, lon: float, max_results: int) -> List[PublicCamera]:
        """Generar cámaras de demostración para testing"""
        import random
        
        demo_cameras = []
        
        for i in range(min(max_results, 5)):  # Máximo 5 cámaras demo por zona
            # Generar coordenadas cercanas
            lat_offset = random.uniform(-0.05, 0.05)  # ~5km
            lon_offset = random.uniform(-0.05, 0.05)
            
            demo_lat = lat + lat_offset
            demo_lon = lon + lon_offset
            
            camera = PublicCamera(
                camera_id=f"demo_{lat}_{lon}_{i}",
                name=f"Demo Camera {i+1}",
                location=f"Demo Location {i+1}",
                latitude=demo_lat,
                longitude=demo_lon,
                stream_url=f"https://demo-stream.example.com/camera_{i}",
                provider='demo_system',
                country='Demo Country',
                city='Demo City',
                status='demo',
                additional_info={'demo': True, 'generated_at': datetime.now().isoformat()}
            )
            
            demo_cameras.append(camera)
        
        logger.info(f"🎬 Generadas {len(demo_cameras)} cámaras de demostración")
        return demo_cameras
    
    def _save_cameras_to_db(self, cameras: List[PublicCamera]) -> int:
        """Guardar cámaras en la base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            saved_count = 0
            
            for camera in cameras:
                try:
                    # Verificar si ya existe
                    cursor.execute("SELECT id FROM public_cameras WHERE camera_id = ?", (camera.camera_id,))
                    existing = cursor.fetchone()
                    
                    if existing:
                        # Actualizar existente
                        cursor.execute('''
                            UPDATE public_cameras SET
                                name = ?, location = ?, latitude = ?, longitude = ?,
                                stream_url = ?, provider = ?, country = ?, city = ?,
                                status = ?, last_verified = ?, conflict_zone = ?,
                                risk_level = ?, additional_info = ?, updated_at = ?
                            WHERE camera_id = ?
                        ''', (
                            camera.name, camera.location, camera.latitude, camera.longitude,
                            camera.stream_url, camera.provider, camera.country, camera.city,
                            camera.status, datetime.now(), camera.conflict_zone,
                            camera.risk_level, json.dumps(camera.additional_info or {}),
                            datetime.now(), camera.camera_id
                        ))
                    else:
                        # Insertar nueva
                        cursor.execute('''
                            INSERT INTO public_cameras (
                                camera_id, name, location, latitude, longitude,
                                stream_url, provider, country, city, status,
                                last_verified, conflict_zone, risk_level, additional_info
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            camera.camera_id, camera.name, camera.location,
                            camera.latitude, camera.longitude, camera.stream_url,
                            camera.provider, camera.country, camera.city,
                            camera.status, datetime.now(), camera.conflict_zone,
                            camera.risk_level, json.dumps(camera.additional_info or {})
                        ))
                    
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"Error guardando cámara {camera.camera_id}: {e}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"💾 Guardadas {saved_count} cámaras en base de datos")
            return saved_count
            
        except Exception as e:
            logger.error(f"Error guardando cámaras: {e}")
            return 0
    
    def get_cameras_for_location(self, lat: float, lon: float, radius_km: int = 50) -> List[Dict]:
        """Obtener cámaras existentes para una ubicación específica"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Usar fórmula de distancia aproximada
            cursor.execute('''
                SELECT * FROM public_cameras
                WHERE status = 'active'
                AND (
                    (latitude BETWEEN ? AND ?) AND
                    (longitude BETWEEN ? AND ?)
                )
                ORDER BY 
                    conflict_zone DESC,
                    (ABS(latitude - ?) + ABS(longitude - ?)) ASC
                LIMIT 20
            ''', (
                lat - (radius_km / 111.0),  # Aproximación: 1 grado ≈ 111km
                lat + (radius_km / 111.0),
                lon - (radius_km / 111.0),
                lon + (radius_km / 111.0),
                lat, lon
            ))
            
            cameras = []
            for row in cursor.fetchall():
                camera_data = {
                    'id': row[0],
                    'camera_id': row[1],
                    'name': row[2],
                    'location': row[3],
                    'latitude': row[4],
                    'longitude': row[5],
                    'stream_url': row[6],
                    'provider': row[7],
                    'country': row[8],
                    'city': row[9],
                    'status': row[10],
                    'last_verified': row[11],
                    'conflict_zone': bool(row[12]),
                    'risk_level': row[13],
                    'additional_info': json.loads(row[14] or '{}'),
                    'created_at': row[15],
                    'updated_at': row[16]
                }
                cameras.append(camera_data)
            
            conn.close()
            return cameras
            
        except Exception as e:
            logger.error(f"Error obteniendo cámaras para ubicación: {e}")
            return []
    
    def get_all_conflict_zone_cameras(self) -> List[Dict]:
        """Obtener todas las cámaras en zonas de conflicto"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM public_cameras
                WHERE conflict_zone = 1
                AND status = 'active'
                ORDER BY risk_level DESC, created_at DESC
            ''')
            
            cameras = []
            for row in cursor.fetchall():
                camera_data = {
                    'id': row[0],
                    'camera_id': row[1],
                    'name': row[2],
                    'location': row[3],
                    'latitude': row[4],
                    'longitude': row[5],
                    'stream_url': row[6],
                    'provider': row[7],
                    'country': row[8],
                    'city': row[9],
                    'status': row[10],
                    'last_verified': row[11],
                    'conflict_zone': bool(row[12]),
                    'risk_level': row[13],
                    'additional_info': json.loads(row[14] or '{}'),
                    'created_at': row[15],
                    'updated_at': row[16]
                }
                cameras.append(camera_data)
            
            conn.close()
            return cameras
            
        except Exception as e:
            logger.error(f"Error obteniendo cámaras de zonas de conflicto: {e}")
            return []
    
    def get_camera_statistics(self) -> Dict:
        """Obtener estadísticas de cámaras"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Estadísticas generales
            cursor.execute("SELECT COUNT(*) FROM public_cameras")
            total_cameras = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM public_cameras WHERE conflict_zone = 1")
            conflict_cameras = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM public_cameras WHERE status = 'active'")
            active_cameras = cursor.fetchone()[0]
            
            # Por proveedor
            cursor.execute('''
                SELECT provider, COUNT(*) 
                FROM public_cameras 
                GROUP BY provider 
                ORDER BY COUNT(*) DESC
            ''')
            by_provider = dict(cursor.fetchall())
            
            # Por país
            cursor.execute('''
                SELECT country, COUNT(*) 
                FROM public_cameras 
                WHERE conflict_zone = 1
                GROUP BY country 
                ORDER BY COUNT(*) DESC
                LIMIT 10
            ''')
            by_country = dict(cursor.fetchall())
            
            # Por nivel de riesgo
            cursor.execute('''
                SELECT risk_level, COUNT(*) 
                FROM public_cameras 
                WHERE conflict_zone = 1
                GROUP BY risk_level
            ''')
            by_risk_level = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                'total_cameras': total_cameras,
                'conflict_zone_cameras': conflict_cameras,
                'active_cameras': active_cameras,
                'coverage_percentage': (conflict_cameras / total_cameras * 100) if total_cameras > 0 else 0,
                'by_provider': by_provider,
                'by_country': by_country,
                'by_risk_level': by_risk_level,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}

# Función principal para ejecutar detección
def main():
    """Función principal para testing"""
    detector = PublicCameraDetector()
    
    # Detectar cámaras en zonas de conflicto
    cameras = detector.detect_cameras_in_conflict_zones()
    
    print(f"\n🎯 Detección completada:")
    print(f"📹 Total de cámaras encontradas: {len(cameras)}")
    
    # Mostrar estadísticas
    stats = detector.get_camera_statistics()
    print(f"\n📊 Estadísticas:")
    print(f"  • Total: {stats.get('total_cameras', 0)}")
    print(f"  • En zonas de conflicto: {stats.get('conflict_zone_cameras', 0)}")
    print(f"  • Activas: {stats.get('active_cameras', 0)}")
    print(f"  • Cobertura: {stats.get('coverage_percentage', 0):.1f}%")
    
    print(f"\n🌍 Por país:")
    for country, count in stats.get('by_country', {}).items():
        print(f"  • {country}: {count} cámaras")

if __name__ == "__main__":
    main()