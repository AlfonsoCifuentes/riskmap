#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema Automatizado de Monitoreo Satelital
Integra las mejores prácticas de la conversación ChatGPT con la arquitectura existente de RiskMap
"""

import os
import sqlite3
import logging
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
import threading

# Configurar logging
logger = logging.getLogger(__name__)

try:
    from sentinelhub import (
        SHConfig, BBox, CRS, 
        SentinelHubCatalog, SentinelHubRequest, 
        DataCollection, MimeType
    )
    from shapely import wkt
    from shapely.geometry import box
    SENTINELHUB_AVAILABLE = True
    logger.info("✅ SentinelHub SDK available")
    
    # Type alias para cuando SentinelHub esté disponible
    BBoxType = BBox
    
except ImportError as e:
    SENTINELHUB_AVAILABLE = False
    logger.warning(f"⚠️ SentinelHub SDK not available: {e}")
    
    # Crear clases mock para cuando SentinelHub no esté disponible
    class MockBBox:
        def __init__(self, bbox=None, crs=None):
            self.bbox = bbox or [0, 0, 1, 1]
            self.crs = crs
    
    class MockCRS:
        WGS84 = "EPSG:4326"
    
    class MockDataCollection:
        SENTINEL2_L2A = "sentinel-2-l2a"
    
    # Asignar mocks
    BBox = MockBBox
    CRS = MockCRS
    DataCollection = MockDataCollection
    BBoxType = MockBBox  # Type alias para mocks
    
    # Mock para shapely
    try:
        from shapely import wkt
        from shapely.geometry import box
    except ImportError:
        class MockWkt:
            @staticmethod
            def loads(wkt_string):
                # Retornar un objeto mock con bounds
                class MockGeom:
                    def __init__(self):
                        self.bounds = (0, 0, 1, 1)  # mock bounds
                return MockGeom()
        
        wkt = MockWkt()
        box = lambda *args: None
    
    # Crear clases mock para cuando SentinelHub no esté disponible
    class MockBBox:
        def __init__(self, bbox=None, crs=None):
            self.bbox = bbox or [0, 0, 1, 1]
            self.crs = crs
    
    class MockCRS:
        WGS84 = "EPSG:4326"
    
    class MockDataCollection:
        SENTINEL2_L2A = "sentinel-2-l2a"
    
    # Asignar mocks
    BBox = MockBBox
    CRS = MockCRS
    DataCollection = MockDataCollection
    
    # Mock para shapely
    try:
        from shapely import wkt
        from shapely.geometry import box
    except ImportError:
        class MockWkt:
            @staticmethod
            def loads(wkt_string):
                # Retornar un objeto mock con bounds
                class MockGeom:
                    def __init__(self):
                        self.bounds = (0, 0, 1, 1)  # mock bounds
                return MockGeom()
        
        wkt = MockWkt()
        box = lambda *args: None

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    logger.warning("⚠️ APScheduler not available, using threading fallback")

@dataclass
class ConflictZone:
    """Zona de conflicto para monitoreo satelital"""
    zone_id: int
    name: str
    geom_wkt: str
    risk_level: str
    last_checked: Optional[str] = None
    priority: int = 1

@dataclass 
class SatelliteImage:
    """Imagen satelital descargada"""
    zone_id: int
    sensed_date: str
    local_path: str
    cloud_percent: float
    download_time: str
    bbox_wgs84: str
    collection: str = "SENTINEL2_L2A"
    resolution: str = "10m"

class AutomatedSatelliteMonitor:
    """
    Monitor automático de imágenes satelitales basado en zonas de conflicto
    Implementa las mejores prácticas de la conversación ChatGPT adaptadas a RiskMap
    """
    
    def __init__(self, db_path: str = None, config: Dict = None):
        self.db_path = db_path or self._get_database_path()
        self.config = config or self._get_default_config()
        
        # Configuración de SentinelHub
        self.sh_config = None
        if SENTINELHUB_AVAILABLE:
            self._setup_sentinelhub_config()
        
        # Scheduler
        self.scheduler = None
        self.running = False
        self.stop_event = threading.Event()
        
        # Directorios
        self.images_dir = Path(self.config.get('images_dir', 'data/satellite_images'))
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        # Inicializar BD
        self._ensure_satellite_tables()
        
        logger.info(f"AutomatedSatelliteMonitor initialized with DB: {self.db_path}")

    def _get_database_path(self) -> str:
        """Obtener ruta de la base de datos"""
        # Usar la misma función que usa el resto del sistema
        try:
            from src.utils.config import get_database_path
            return get_database_path()
        except ImportError:
            # Fallback directo
            db_path = os.getenv('DATABASE_PATH', './data/geopolitical_intel.db')
            # Crear directorio si no existe
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            return db_path

    def _get_default_config(self) -> Dict:
        """Configuración por defecto del monitor satelital"""
        return {
            'images_dir': 'data/satellite_images',
            'max_cloud_cover': 20,  # % máximo de nubes
            'image_size': (512, 512),  # píxeles
            'check_interval_hours': 4,  # cada 4 horas
            'max_age_days': 30,  # no buscar imágenes más viejas
            'priority_zones_interval_hours': 2,  # zonas alta prioridad cada 2h
            'batch_size': 10,  # procesar zonas de a 10
            'retry_attempts': 3,
            'timeout_seconds': 120
        }

    def _setup_sentinelhub_config(self):
        """Configurar SentinelHub con credenciales del .env"""
        try:
            self.sh_config = SHConfig()
            
            # Cargar desde variables de entorno (ya las tienes en .env)
            client_id = os.getenv('SENTINEL_CLIENT_ID')
            client_secret = os.getenv('SENTINEL_CLIENT_SECRET')
            instance_id = os.getenv('SENTINEL_INSTANCE_ID')
            
            if client_id and client_secret:
                self.sh_config.sh_client_id = client_id
                self.sh_config.sh_client_secret = client_secret
                self.sh_config.instance_id = instance_id
                
                logger.info("✅ SentinelHub configured with credentials from .env")
            else:
                logger.error("❌ SentinelHub credentials not found in environment variables")
                self.sh_config = None
                
        except Exception as e:
            logger.error(f"Error configuring SentinelHub: {e}")
            self.sh_config = None

    def _ensure_satellite_tables(self):
        """Crear tablas necesarias para el monitoreo satelital"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabla de zonas de conflicto (adaptada al esquema existente)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS conflict_zones (
                        zone_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        geom_wkt TEXT NOT NULL,
                        geom_geojson TEXT,
                        risk_level TEXT DEFAULT 'medium',
                        priority INTEGER DEFAULT 2,
                        last_checked TEXT,
                        created_at TEXT DEFAULT (datetime('now')),
                        updated_at TEXT DEFAULT (datetime('now')),
                        active INTEGER DEFAULT 1
                    )
                """)
                
                # Tabla de imágenes satelitales (una por zona, se sobrescribe)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS zone_satellite_images (
                        zone_id INTEGER PRIMARY KEY,
                        sensed_date TEXT NOT NULL,
                        local_path TEXT NOT NULL,
                        cloud_percent REAL,
                        download_time TEXT DEFAULT (datetime('now')),
                        bbox_wgs84 TEXT,
                        collection TEXT DEFAULT 'SENTINEL2_L2A',
                        resolution TEXT DEFAULT '10m',
                        file_size INTEGER,
                        metadata TEXT,
                        FOREIGN KEY (zone_id) REFERENCES conflict_zones (zone_id)
                    )
                """)
                
                # Índices para optimizar consultas
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_zones_priority ON conflict_zones (priority, active)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_zones_last_checked ON conflict_zones (last_checked)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_sensed_date ON zone_satellite_images (sensed_date)")
                
                conn.commit()
                logger.info("✅ Satellite monitoring tables ensured")
                
        except Exception as e:
            logger.error(f"Error creating satellite tables: {e}")

    def populate_zones_from_geojson_endpoint(self):
        """
        Poblar zonas de conflicto desde el endpoint GeoJSON existente
        Integra con el sistema que ya tienes implementado
        """
        try:
            # Simular llamada al endpoint interno de analytics/geojson
            from src.utils.config import get_database_path
            
            db_path = get_database_path()
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Obtener artículos con geolocalización y riesgo alto/medio
                cursor.execute("""
                    SELECT 
                        id,
                        title,
                        country,
                        region,
                        latitude,
                        longitude,
                        risk_level,
                        risk_score,
                        published_at
                    FROM articles 
                    WHERE latitude IS NOT NULL 
                    AND longitude IS NOT NULL
                    AND risk_level IN ('high', 'medium')
                    AND published_at >= date('now', '-30 days')
                    ORDER BY risk_score DESC, published_at DESC
                    LIMIT 50
                """)
                
                articles = cursor.fetchall()
                
                # Agrupar artículos por región/país para crear zonas
                zones_created = 0
                processed_locations = set()
                
                for article in articles:
                    (article_id, title, country, region, 
                     lat, lon, risk_level, risk_score, published_date) = article
                    
                    # Crear identificador único de ubicación
                    location_key = f"{country}_{region}_{round(lat, 2)}_{round(lon, 2)}"
                    
                    if location_key in processed_locations:
                        continue
                    
                    processed_locations.add(location_key)
                    
                    # Crear bbox de ~10km alrededor del punto
                    bbox_size = 0.05  # ~5.5km en grados
                    min_lon = lon - bbox_size
                    min_lat = lat - bbox_size  
                    max_lon = lon + bbox_size
                    max_lat = lat + bbox_size
                    
                    # Crear geometría WKT
                    geom_wkt = f"POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, {max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))"
                    
                    # Crear GeoJSON también
                    geom_geojson = json.dumps({
                        "type": "Polygon",
                        "coordinates": [[
                            [min_lon, min_lat],
                            [max_lon, min_lat], 
                            [max_lon, max_lat],
                            [min_lon, max_lat],
                            [min_lon, min_lat]
                        ]]
                    })
                    
                    # Determinar prioridad basada en risk_level
                    priority = 1 if risk_level == 'high' else 2
                    
                    # Nombre de la zona
                    zone_name = f"{location or country or region} - Área de Conflicto"
                    
                    # Insertar o actualizar zona
                    cursor.execute("""
                        INSERT OR REPLACE INTO conflict_zones 
                        (name, geom_wkt, geom_geojson, risk_level, priority, updated_at)
                        VALUES (?, ?, ?, ?, ?, datetime('now'))
                    """, (zone_name, geom_wkt, geom_geojson, risk_level, priority))
                    
                    zones_created += 1
                
                conn.commit()
                logger.info(f"✅ Created/updated {zones_created} conflict zones from existing geopolitical data")
                return zones_created
                
        except Exception as e:
            logger.error(f"Error populating zones from GeoJSON: {e}")
            return 0

    def fetch_latest_scene(self, bbox: Any, max_age_days: int = None) -> Optional[Dict]:
        """
        Buscar la escena más reciente para un bbox
        Implementa la lógica de ChatGPT adaptada
        """
        if not SENTINELHUB_AVAILABLE or not self.sh_config:
            logger.warning("SentinelHub not available for scene fetching")
            return None
            
        try:
            catalog = SentinelHubCatalog(config=self.sh_config)
            
            # Rango de fechas
            max_age = max_age_days or self.config['max_age_days']
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=max_age)
            
            # Búsqueda con filtros de ChatGPT
            search_iter = catalog.search(
                DataCollection.SENTINEL2_L2A,  # 10m resolution
                bbox=bbox,
                time=(start_date, end_date),
                query={
                    "eo:cloud_cover": {"lt": self.config['max_cloud_cover']}
                },
                limit=1,
                sortby=[{"property": "datetime", "direction": "desc"}]
            )
            
            scene = next(search_iter, None)
            if scene:
                logger.debug(f"Found scene: {scene['properties']['datetime']}, clouds: {scene['properties']['eo:cloud_cover']}%")
            
            return scene
            
        except Exception as e:
            logger.error(f"Error fetching latest scene: {e}")
            return None

    def download_image(self, bbox: Any, sensed_date: str, zone_id: int) -> Optional[str]:
        """
        Descargar imagen usando Processing API
        Implementa la lógica de descarga de ChatGPT
        """
        if not SENTINELHUB_AVAILABLE or not self.sh_config:
            return None
            
        try:
            # Evalscript para imagen RGB de alta calidad
            evalscript = """
            //VERSION=3
            function setup() {
                return {
                    input: [{
                        bands: ["B04", "B03", "B02", "B08"],
                        units: "REFLECTANCE"
                    }],
                    output: {
                        bands: 3,
                        sampleType: "UINT8"
                    }
                };
            }
            
            function evaluatePixel(sample) {
                // Enhanced RGB with NIR influence for better contrast
                let r = sample.B04 * 2.5;
                let g = sample.B03 * 2.5; 
                let b = sample.B02 * 2.5;
                
                // Enhance with NIR for vegetation/urban distinction
                let nir = sample.B08;
                r = r + nir * 0.1;
                g = g + nir * 0.2;
                
                return [
                    Math.min(255, Math.max(0, r * 255)),
                    Math.min(255, Math.max(0, g * 255)), 
                    Math.min(255, Math.max(0, b * 255))
                ];
            }
            """
            
            # Request de descarga
            request = SentinelHubRequest(
                data_collection=DataCollection.SENTINEL2_L2A,
                evalscript=evalscript,
                input_data=[{
                    "bounds": {
                        "bbox": bbox.bbox,
                        "properties": {"crs": bbox.crs.pyproj_crs.to_epsg()}
                    },
                    "dataFilter": {
                        "timeRange": {
                            "from": f"{sensed_date}T00:00:00Z",
                            "to": f"{sensed_date}T23:59:59Z"
                        }
                    }
                }],
                responses=[{
                    "identifier": "default", 
                    "format": {"type": "image/tiff"}
                }],
                bbox=bbox,
                size=self.config['image_size'],
                config=self.sh_config
            )
            
            # Descargar
            img_data = request.get_data()[0]
            
            # Guardar archivo
            filename = f"zone_{zone_id}_{sensed_date.replace('-', '')}.tif"
            file_path = self.images_dir / filename
            
            with open(file_path, "wb") as f:
                # Si es numpy array, convertir a bytes
                if hasattr(img_data, 'tobytes'):
                    f.write(img_data.tobytes())
                else:
                    f.write(img_data)
            
            logger.info(f"✅ Downloaded satellite image: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error downloading image for zone {zone_id}: {e}")
            return None

    def update_zone_image(self, zone: ConflictZone) -> bool:
        """
        Actualizar imagen de una zona específica
        Implementa la lógica de sobrescritura de ChatGPT
        """
        try:
            # Crear bbox desde WKT
            geom = wkt.loads(zone.geom_wkt)
            bbox = BBox(bbox=geom.bounds, crs=CRS.WGS84)
            
            # Buscar escena más reciente
            scene = self.fetch_latest_scene(bbox)
            if not scene:
                logger.debug(f"No scenes found for zone {zone.zone_id}")
                return False
            
            sensed_date = scene["properties"]["datetime"][:10]  # YYYY-MM-DD
            cloud_percent = scene["properties"]["eo:cloud_cover"]
            
            # Verificar si ya tenemos esta imagen o una más nueva
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT sensed_date FROM zone_satellite_images WHERE zone_id = ?",
                    (zone.zone_id,)
                )
                row = cursor.fetchone()
                
                if row and row[0] >= sensed_date:
                    logger.debug(f"Zone {zone.zone_id} already has latest image ({row[0]} >= {sensed_date})")
                    return False
            
            # Descargar nueva imagen
            local_path = self.download_image(bbox, sensed_date, zone.zone_id)
            if not local_path:
                return False
            
            # Obtener tamaño del archivo
            file_size = Path(local_path).stat().st_size
            
            # Guardar/sobrescribir en BD (lógica de ChatGPT)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # ON CONFLICT sobrescribe automáticamente
                cursor.execute("""
                    INSERT INTO zone_satellite_images 
                    (zone_id, sensed_date, local_path, cloud_percent, download_time, bbox_wgs84, file_size, metadata)
                    VALUES (?, ?, ?, ?, datetime('now'), ?, ?, ?)
                    ON CONFLICT(zone_id) DO UPDATE SET
                        sensed_date = excluded.sensed_date,
                        local_path = excluded.local_path, 
                        cloud_percent = excluded.cloud_percent,
                        download_time = excluded.download_time,
                        bbox_wgs84 = excluded.bbox_wgs84,
                        file_size = excluded.file_size,
                        metadata = excluded.metadata
                """, (
                    zone.zone_id, sensed_date, local_path, cloud_percent,
                    ",".join(map(str, bbox.bbox)),
                    file_size,
                    json.dumps(scene["properties"])
                ))
                
                # Actualizar timestamp de la zona
                cursor.execute(
                    "UPDATE conflict_zones SET last_checked = datetime('now') WHERE zone_id = ?",
                    (zone.zone_id,)
                )
                
                conn.commit()
            
            logger.info("✅ Updated satellite image for zone %s: %s (%s%% clouds)", zone.zone_id, sensed_date, cloud_percent)
            return True
            
        except Exception as e:
            logger.error(f"Error updating zone {zone.zone_id}: {e}")
            return False

    def update_all_zones(self, priority_only: bool = False) -> Dict[str, int]:
        """
        Actualizar todas las zonas de conflicto
        Implementa el flujo principal de ChatGPT con mejoras
        """
        stats = {'processed': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Query adaptado para prioridades
                if priority_only:
                    query = """
                        SELECT zone_id, name, geom_wkt, risk_level, last_checked, priority
                        FROM conflict_zones 
                        WHERE active = 1 AND priority = 1
                        ORDER BY priority, last_checked ASC NULLS FIRST
                    """
                else:
                    query = """
                        SELECT zone_id, name, geom_wkt, risk_level, last_checked, priority
                        FROM conflict_zones 
                        WHERE active = 1
                        ORDER BY priority, last_checked ASC NULLS FIRST
                    """
                
                cursor.execute(query)
                rows = cursor.fetchall()
                
                if not rows:
                    logger.info("No conflict zones found for processing")
                    return stats
                
                logger.info(f"Processing {len(rows)} conflict zones (priority_only={priority_only})")
                
                # Procesar en lotes para no sobrecargar
                batch_size = self.config['batch_size']
                
                for i in range(0, len(rows), batch_size):
                    batch = rows[i:i + batch_size]
                    
                    for row in batch:
                        if self.stop_event.is_set():
                            logger.info("Stopping satellite monitoring due to stop event")
                            break
                            
                        zone = ConflictZone(*row)
                        stats['processed'] += 1
                        
                        try:
                            if self.update_zone_image(zone):
                                stats['updated'] += 1
                            else:
                                stats['skipped'] += 1
                                
                        except Exception as e:
                            logger.error(f"Error processing zone {zone.zone_id}: {e}")
                            stats['errors'] += 1
                    
                    # Pequeña pausa entre lotes
                    if not self.stop_event.is_set():
                        time.sleep(2)
                
                logger.info(f"✅ Satellite monitoring complete: {stats}")
                return stats
                
        except Exception as e:
            logger.error(f"Error in update_all_zones: {e}")
            stats['errors'] += 1
            return stats

    def start_monitoring(self):
        """
        Iniciar monitoreo automático
        Integra scheduler de ChatGPT con threading fallback
        """
        if self.running:
            logger.warning("Satellite monitoring already running")
            return
            
        if not SENTINELHUB_AVAILABLE or not self.sh_config:
            logger.error("Cannot start monitoring: SentinelHub not configured")
            return
        
        self.running = True
        self.stop_event.clear()
        
        # Poblar zonas desde el sistema existente
        zones_count = self.populate_zones_from_geojson_endpoint()
        logger.info(f"Populated {zones_count} zones for monitoring")
        
        if SCHEDULER_AVAILABLE:
            # Usar APScheduler (preferido)
            self.scheduler = BackgroundScheduler()
            
            # Job principal: todas las zonas cada X horas
            self.scheduler.add_job(
                func=lambda: self.update_all_zones(priority_only=False),
                trigger="interval",
                hours=self.config['check_interval_hours'],
                id='update_all_zones'
            )
            
            # Job prioritario: zonas de alta prioridad más frecuentemente
            self.scheduler.add_job(
                func=lambda: self.update_all_zones(priority_only=True),
                trigger="interval", 
                hours=self.config['priority_zones_interval_hours'],
                id='update_priority_zones'
            )
            
            self.scheduler.start()
            logger.info("✅ Satellite monitoring started with APScheduler")
            
        else:
            # Fallback con threading
            def monitoring_loop():
                while not self.stop_event.is_set():
                    try:
                        # Procesar zonas prioritarias cada 2h
                        self.update_all_zones(priority_only=True)
                        
                        # Esperar o terminar si se para
                        if self.stop_event.wait(timeout=self.config['priority_zones_interval_hours'] * 3600):
                            break
                            
                        # Procesar todas las zonas cada 4h  
                        if not self.stop_event.is_set():
                            self.update_all_zones(priority_only=False)
                            
                        # Esperar intervalo completo
                        if self.stop_event.wait(timeout=self.config['check_interval_hours'] * 3600):
                            break
                            
                    except Exception as e:
                        logger.error(f"Error in monitoring loop: {e}")
                        self.stop_event.wait(300)  # Esperar 5 min y reintentar
            
            thread = threading.Thread(target=monitoring_loop, daemon=True)
            thread.start()
            logger.info("✅ Satellite monitoring started with threading fallback")

    def stop_monitoring(self):
        """Detener monitoreo automático"""
        if not self.running:
            return
            
        self.running = False
        self.stop_event.set()
        
        if self.scheduler:
            self.scheduler.shutdown(wait=False)
            self.scheduler = None
            
        logger.info("🛑 Satellite monitoring stopped")

    def get_monitoring_statistics(self) -> Dict:
        """Obtener estadísticas del monitoreo"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Estadísticas de zonas
                cursor.execute("SELECT COUNT(*) FROM conflict_zones WHERE active = 1")
                total_zones = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM conflict_zones WHERE active = 1 AND priority = 1")
                priority_zones = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM zone_satellite_images")
                images_downloaded = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT COUNT(*) FROM zone_satellite_images 
                    WHERE download_time >= date('now', '-24 hours')
                """)
                recent_downloads = cursor.fetchone()[0]
                
                # Tamaño total de imágenes
                cursor.execute("SELECT SUM(file_size) FROM zone_satellite_images")
                total_size = cursor.fetchone()[0] or 0
                
                return {
                    'total_zones': total_zones,
                    'priority_zones': priority_zones,
                    'images_downloaded': images_downloaded,
                    'recent_downloads_24h': recent_downloads,
                    'total_storage_mb': round(total_size / (1024 * 1024), 2),
                    'monitoring_running': self.running,
                    'sentinelhub_configured': self.sh_config is not None,
                    'images_directory': str(self.images_dir)
                }
                
        except Exception as e:
            logger.error(f"Error getting monitoring statistics: {e}")
            return {'error': str(e)}

    def cleanup_old_images(self, days_to_keep: int = 90):
        """Limpiar imágenes antiguas para ahorrar espacio"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Obtener imágenes a eliminar
                cursor.execute("""
                    SELECT local_path FROM zone_satellite_images 
                    WHERE download_time < ?
                """, (cutoff_date.isoformat(),))
                
                old_images = cursor.fetchall()
                deleted_count = 0
                
                for (path,) in old_images:
                    try:
                        if Path(path).exists():
                            Path(path).unlink()
                            deleted_count += 1
                    except Exception as e:
                        logger.warning(f"Could not delete {path}: {e}")
                
                # Limpiar registros de BD
                cursor.execute("""
                    DELETE FROM zone_satellite_images 
                    WHERE download_time < ?
                """, (cutoff_date.isoformat(),))
                
                conn.commit()
                
                logger.info(f"✅ Cleaned up {deleted_count} old satellite images")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Error cleaning up old images: {e}")
            return 0

# Función de conveniencia para usar desde app_BUENA.py
def create_satellite_monitor(db_path: str = None, config: Dict = None) -> AutomatedSatelliteMonitor:
    """Factory function para crear el monitor satelital"""
    return AutomatedSatelliteMonitor(db_path=db_path, config=config)

if __name__ == "__main__":
    # Ejemplo de uso directo
    monitor = AutomatedSatelliteMonitor()
    
    try:
        # Poblar zonas desde datos existentes
        zones_count = monitor.populate_zones_from_geojson_endpoint()
        print(f"Populated {zones_count} zones")
        
        # Ejecutar una actualización manual
        stats = monitor.update_all_zones()
        print(f"Update stats: {stats}")
        
        # Mostrar estadísticas
        monitoring_stats = monitor.get_monitoring_statistics()
        print(f"Monitoring stats: {monitoring_stats}")
        
    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
