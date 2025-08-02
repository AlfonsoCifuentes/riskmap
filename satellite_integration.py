#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Integración con APIs Satelitales
Soporte para SentinelHub, Planet, y otras fuentes de imágenes satelitales
"""

import os
import json
import time
import logging
import requests
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from urllib.parse import urljoin
import base64

# Configurar logging
logger = logging.getLogger(__name__)

@dataclass
class SatelliteQueryParams:
    """Parámetros para consultas satelitales"""
    bbox: List[float]  # [min_lon, min_lat, max_lon, max_lat]
    start_date: str
    end_date: str
    cloud_cover_max: int = 20
    resolution: str = "10m"
    collection: str = "sentinel-2-l2a"
    priority: str = "medium"
    data_format: str = "image/tiff"

@dataclass
class SatelliteImage:
    """Información de imagen satelital"""
    image_id: str
    collection: str
    date: str
    cloud_cover: float
    bbox: List[float]
    preview_url: Optional[str] = None
    download_url: Optional[str] = None
    metadata: Optional[Dict] = None
    local_path: Optional[str] = None

class SentinelHubAPI:
    """Cliente para SentinelHub API"""
    
    def __init__(self, client_id: str = None, client_secret: str = None):
        self.base_url = "https://services.sentinel-hub.com"
        self.client_id = client_id or os.getenv("SENTINELHUB_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("SENTINELHUB_CLIENT_SECRET")
        self.access_token = None
        self.token_expires_at = None
        
        if not self.client_id or not self.client_secret:
            logger.warning("SentinelHub credentials not found in environment variables")
    
    def authenticate(self) -> bool:
        """Autenticar con SentinelHub OAuth"""
        try:
            if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
                return True
            
            auth_url = f"{self.base_url}/auth/realms/main/protocol/openid-connect/token"
            
            data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            response = requests.post(auth_url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            
            # Calcular expiración (menos 5 minutos para seguridad)
            expires_in = token_data.get('expires_in', 3600) - 300
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            logger.info("SentinelHub authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"SentinelHub authentication failed: {e}")
            return False
    
    def search_images(self, params: SatelliteQueryParams) -> List[SatelliteImage]:
        """Buscar imágenes satelitales"""
        try:
            if not self.authenticate():
                return []
            
            search_url = f"{self.base_url}/api/v1/catalog/search"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Construir query para SentinelHub
            search_payload = {
                "collections": [params.collection],
                "datetime": f"{params.start_date}T00:00:00Z/{params.end_date}T23:59:59Z",
                "bbox": params.bbox,
                "limit": 100,
                "query": {
                    "eo:cloud_cover": {
                        "lt": params.cloud_cover_max
                    }
                }
            }
            
            response = requests.post(search_url, json=search_payload, headers=headers)
            response.raise_for_status()
            
            results = response.json()
            images = []
            
            for feature in results.get('features', []):
                try:
                    properties = feature.get('properties', {})
                    geometry = feature.get('geometry', {})
                    
                    # Extraer bbox de la geometría
                    if geometry.get('type') == 'Polygon':
                        coords = geometry['coordinates'][0]
                        lons = [coord[0] for coord in coords]
                        lats = [coord[1] for coord in coords]
                        bbox = [min(lons), min(lats), max(lons), max(lats)]
                    else:
                        bbox = params.bbox
                    
                    image = SatelliteImage(
                        image_id=feature.get('id', ''),
                        collection=params.collection,
                        date=properties.get('datetime', ''),
                        cloud_cover=properties.get('eo:cloud_cover', 0),
                        bbox=bbox,
                        metadata=properties
                    )
                    
                    images.append(image)
                    
                except Exception as e:
                    logger.warning(f"Error parsing SentinelHub feature: {e}")
                    continue
            
            logger.info(f"Found {len(images)} images from SentinelHub")
            return images
            
        except Exception as e:
            logger.error(f"SentinelHub search failed: {e}")
            return []
    
    def get_preview_url(self, image: SatelliteImage, width: int = 512, height: int = 512) -> Optional[str]:
        """Generar URL de preview para una imagen"""
        try:
            if not self.authenticate():
                return None
            
            # Configuración para preview RGB
            evalscript = """
            //VERSION=3
            function setup() {
                return {
                    input: ["B04", "B03", "B02"],
                    output: { bands: 3 }
                };
            }
            
            function evaluatePixel(sample) {
                return [2.5 * sample.B04, 2.5 * sample.B03, 2.5 * sample.B02];
            }
            """
            
            preview_payload = {
                "input": {
                    "bounds": {
                        "bbox": image.bbox,
                        "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}
                    },
                    "data": [
                        {
                            "dataFilter": {
                                "timeRange": {
                                    "from": image.date,
                                    "to": image.date
                                }
                            },
                            "type": image.collection.upper().replace('-', '_')
                        }
                    ]
                },
                "output": {
                    "width": width,
                    "height": height,
                    "responses": [
                        {
                            "identifier": "default",
                            "format": {"type": "image/png"}
                        }
                    ]
                },
                "evalscript": evalscript
            }
            
            process_url = f"{self.base_url}/api/v1/process"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(process_url, json=preview_payload, headers=headers)
            
            if response.status_code == 200:
                # Guardar preview localmente
                preview_dir = Path("static/images/satellite/previews")
                preview_dir.mkdir(parents=True, exist_ok=True)
                
                preview_filename = f"preview_{image.image_id}_{int(time.time())}.png"
                preview_path = preview_dir / preview_filename
                
                with open(preview_path, 'wb') as f:
                    f.write(response.content)
                
                preview_url = f"/static/images/satellite/previews/{preview_filename}"
                image.preview_url = preview_url
                
                logger.info(f"Preview generated for {image.image_id}")
                return preview_url
            
        except Exception as e:
            logger.error(f"Error generating preview for {image.image_id}: {e}")
        
        return None

class PlanetAPI:
    """Cliente para Planet API"""
    
    def __init__(self, api_key: str = None):
        self.base_url = "https://api.planet.com"
        self.api_key = api_key or os.getenv("PLANET_API_KEY")
        
        if not self.api_key:
            logger.warning("Planet API key not found in environment variables")
    
    def search_images(self, params: SatelliteQueryParams) -> List[SatelliteImage]:
        """Buscar imágenes en Planet"""
        try:
            if not self.api_key:
                return []
            
            search_url = f"{self.base_url}/data/v1/quick-search"
            
            headers = {
                'Authorization': f'api-key {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Mapear colección de SentinelHub a Planet
            planet_item_types = {
                'sentinel-2-l2a': ['PSScene'],
                'landsat-ot-l2': ['Landsat8L1G'],
                'default': ['PSScene', 'REOrthoTile']
            }
            
            item_types = planet_item_types.get(params.collection, planet_item_types['default'])
            
            search_payload = {
                "item_types": item_types,
                "filter": {
                    "type": "AndFilter",
                    "config": [
                        {
                            "type": "GeometryFilter",
                            "field_name": "geometry",
                            "config": {
                                "type": "Polygon",
                                "coordinates": [[
                                    [params.bbox[0], params.bbox[1]],
                                    [params.bbox[2], params.bbox[1]],
                                    [params.bbox[2], params.bbox[3]],
                                    [params.bbox[0], params.bbox[3]],
                                    [params.bbox[0], params.bbox[1]]
                                ]]
                            }
                        },
                        {
                            "type": "DateRangeFilter",
                            "field_name": "acquired",
                            "config": {
                                "gte": f"{params.start_date}T00:00:00.000Z",
                                "lte": f"{params.end_date}T23:59:59.999Z"
                            }
                        },
                        {
                            "type": "RangeFilter",
                            "field_name": "cloud_cover",
                            "config": {
                                "lte": params.cloud_cover_max / 100.0
                            }
                        }
                    ]
                }
            }
            
            response = requests.post(search_url, json=search_payload, headers=headers)
            response.raise_for_status()
            
            results = response.json()
            images = []
            
            for feature in results.get('features', []):
                try:
                    properties = feature.get('properties', {})
                    geometry = feature.get('geometry', {})
                    
                    # Extraer bbox
                    if geometry.get('type') == 'Polygon':
                        coords = geometry['coordinates'][0]
                        lons = [coord[0] for coord in coords]
                        lats = [coord[1] for coord in coords]
                        bbox = [min(lons), min(lats), max(lons), max(lats)]
                    else:
                        bbox = params.bbox
                    
                    image = SatelliteImage(
                        image_id=feature.get('id', ''),
                        collection=f"planet_{properties.get('item_type', 'unknown')}",
                        date=properties.get('acquired', ''),
                        cloud_cover=properties.get('cloud_cover', 0) * 100,
                        bbox=bbox,
                        metadata=properties
                    )
                    
                    images.append(image)
                    
                except Exception as e:
                    logger.warning(f"Error parsing Planet feature: {e}")
                    continue
            
            logger.info(f"Found {len(images)} images from Planet")
            return images
            
        except Exception as e:
            logger.error(f"Planet search failed: {e}")
            return []

class SatelliteIntegrationManager:
    """Gestor principal de integración satelital"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.getenv("DATABASE_PATH", "geopolitical_risk.db")
        self.sentinelhub = SentinelHubAPI()
        self.planet = PlanetAPI()
        
        # Crear tablas si no existen
        self._init_database()
    
    def _init_database(self):
        """Inicializar tablas de base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabla para imágenes satelitales
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS satellite_images (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        image_id TEXT UNIQUE NOT NULL,
                        collection TEXT NOT NULL,
                        date TEXT NOT NULL,
                        cloud_cover REAL,
                        bbox_min_lon REAL,
                        bbox_min_lat REAL,
                        bbox_max_lon REAL,
                        bbox_max_lat REAL,
                        preview_url TEXT,
                        download_url TEXT,
                        local_path TEXT,
                        metadata TEXT,
                        zone_id TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Tabla para consultas satelitales
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS satellite_queries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        zone_id TEXT NOT NULL,
                        query_params TEXT NOT NULL,
                        images_found INTEGER DEFAULT 0,
                        query_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'pending'
                    )
                """)
                
                # Índices para optimización
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_satellite_images_date ON satellite_images(date)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_satellite_images_zone ON satellite_images(zone_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_satellite_queries_zone ON satellite_queries(zone_id)")
                
                conn.commit()
                logger.info("Satellite database tables initialized")
                
        except Exception as e:
            logger.error(f"Error initializing satellite database: {e}")
    
    def load_geojson_zones(self, geojson_path: str) -> List[Dict]:
        """Cargar zonas de conflicto desde GeoJSON"""
        try:
            with open(geojson_path, 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)
            
            zones = []
            for feature in geojson_data.get('features', []):
                properties = feature.get('properties', {})
                geometry = feature.get('geometry', {})
                
                # Extraer bbox de las propiedades o calcular desde geometría
                bbox = properties.get('bbox')
                if not bbox and geometry.get('type') == 'Point':
                    coords = geometry['coordinates']
                    margin = 0.1  # 0.1 grados de margen
                    bbox = [
                        coords[0] - margin,
                        coords[1] - margin, 
                        coords[0] + margin,
                        coords[1] + margin
                    ]
                
                if bbox:
                    zones.append({
                        'id': properties.get('id', f"zone_{len(zones)}"),
                        'name': properties.get('name', 'Unknown Zone'),
                        'bbox': bbox,
                        'risk_level': properties.get('risk_level', 'medium'),
                        'cloud_cover_max': properties.get('cloud_cover_max', 30),
                        'recommended_resolution': properties.get('recommended_resolution', '10m'),
                        'monitoring_frequency': properties.get('monitoring_frequency', 'weekly'),
                        'sentinel_priority': properties.get('sentinel_priority', 'medium'),
                        'properties': properties
                    })
            
            logger.info(f"Loaded {len(zones)} zones from GeoJSON")
            return zones
            
        except Exception as e:
            logger.error(f"Error loading GeoJSON zones: {e}")
            return []
    
    def query_satellite_data_for_zone(self, zone: Dict, days_back: int = 30) -> List[SatelliteImage]:
        """Consultar datos satelitales para una zona específica"""
        try:
            # Preparar parámetros de consulta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            params = SatelliteQueryParams(
                bbox=zone['bbox'],
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                cloud_cover_max=zone.get('cloud_cover_max', 30),
                resolution=zone.get('recommended_resolution', '10m'),
                collection='sentinel-2-l2a',
                priority=zone.get('sentinel_priority', 'medium')
            )
            
            # Consultar en todas las fuentes disponibles
            all_images = []
            
            # SentinelHub
            try:
                sentinelhub_images = self.sentinelhub.search_images(params)
                for img in sentinelhub_images:
                    img.metadata = img.metadata or {}
                    img.metadata['source'] = 'sentinelhub'
                all_images.extend(sentinelhub_images)
            except Exception as e:
                logger.warning(f"SentinelHub query failed for zone {zone['id']}: {e}")
            
            # Planet
            try:
                planet_images = self.planet.search_images(params)
                for img in planet_images:
                    img.metadata = img.metadata or {}
                    img.metadata['source'] = 'planet'
                all_images.extend(planet_images)
            except Exception as e:
                logger.warning(f"Planet query failed for zone {zone['id']}: {e}")
            
            # Guardar consulta en base de datos
            self._save_satellite_query(zone['id'], asdict(params), len(all_images))
            
            # Guardar imágenes encontradas
            for image in all_images:
                self._save_satellite_image(image, zone['id'])
            
            logger.info(f"Found {len(all_images)} satellite images for zone {zone['id']}")
            return all_images
            
        except Exception as e:
            logger.error(f"Error querying satellite data for zone {zone['id']}: {e}")
            return []
    
    def process_all_zones(self, geojson_path: str, days_back: int = 30) -> Dict[str, Any]:
        """Procesar todas las zonas del GeoJSON"""
        try:
            zones = self.load_geojson_zones(geojson_path)
            
            if not zones:
                return {"success": False, "error": "No zones found in GeoJSON"}
            
            results = {
                "total_zones": len(zones),
                "processed_zones": 0,
                "total_images": 0,
                "zones_data": {},
                "errors": []
            }
            
            for zone in zones:
                try:
                    logger.info(f"Processing zone: {zone['name']} ({zone['id']})")
                    
                    images = self.query_satellite_data_for_zone(zone, days_back)
                    
                    # Generar previews para las mejores imágenes
                    best_images = sorted(images, key=lambda x: x.cloud_cover)[:3]
                    for image in best_images:
                        if image.metadata and image.metadata.get('source') == 'sentinelhub':
                            self.sentinelhub.get_preview_url(image)
                    
                    results["zones_data"][zone['id']] = {
                        "name": zone['name'],
                        "images_found": len(images),
                        "best_images": [asdict(img) for img in best_images],
                        "bbox": zone['bbox'],
                        "risk_level": zone['risk_level']
                    }
                    
                    results["processed_zones"] += 1
                    results["total_images"] += len(images)
                    
                except Exception as e:
                    error_msg = f"Error processing zone {zone['id']}: {e}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            results["success"] = True
            logger.info(f"Processed {results['processed_zones']} zones with {results['total_images']} total images")
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing all zones: {e}")
            return {"success": False, "error": str(e)}
    
    def _save_satellite_query(self, zone_id: str, params: Dict, images_found: int):
        """Guardar consulta satelital en base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO satellite_queries (zone_id, query_params, images_found, status)
                    VALUES (?, ?, ?, 'completed')
                """, (zone_id, json.dumps(params), images_found))
                conn.commit()
        except Exception as e:
            logger.error(f"Error saving satellite query: {e}")
    
    def _save_satellite_image(self, image: SatelliteImage, zone_id: str):
        """Guardar imagen satelital en base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO satellite_images 
                    (image_id, collection, date, cloud_cover, bbox_min_lon, bbox_min_lat, 
                     bbox_max_lon, bbox_max_lat, preview_url, download_url, local_path, 
                     metadata, zone_id, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    image.image_id,
                    image.collection,
                    image.date,
                    image.cloud_cover,
                    image.bbox[0], image.bbox[1], image.bbox[2], image.bbox[3],
                    image.preview_url,
                    image.download_url,
                    image.local_path,
                    json.dumps(image.metadata) if image.metadata else None,
                    zone_id
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Error saving satellite image: {e}")
    
    def get_zone_images(self, zone_id: str, limit: int = 50) -> List[Dict]:
        """Obtener imágenes satelitales para una zona"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM satellite_images 
                    WHERE zone_id = ? 
                    ORDER BY date DESC, cloud_cover ASC 
                    LIMIT ?
                """, (zone_id, limit))
                
                columns = [desc[0] for desc in cursor.description]
                images = []
                
                for row in cursor.fetchall():
                    image_dict = dict(zip(columns, row))
                    if image_dict['metadata']:
                        image_dict['metadata'] = json.loads(image_dict['metadata'])
                    images.append(image_dict)
                
                return images
                
        except Exception as e:
            logger.error(f"Error getting zone images: {e}")
            return []
    
    def generate_satellite_report(self, zone_id: str = None) -> Dict[str, Any]:
        """Generar reporte de datos satelitales"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Estadísticas generales
                if zone_id:
                    cursor.execute("""
                        SELECT COUNT(*) as total_images,
                               COUNT(DISTINCT collection) as collections,
                               AVG(cloud_cover) as avg_cloud_cover,
                               MIN(date) as earliest_date,
                               MAX(date) as latest_date
                        FROM satellite_images 
                        WHERE zone_id = ?
                    """, (zone_id,))
                else:
                    cursor.execute("""
                        SELECT COUNT(*) as total_images,
                               COUNT(DISTINCT collection) as collections,
                               AVG(cloud_cover) as avg_cloud_cover,
                               MIN(date) as earliest_date,
                               MAX(date) as latest_date
                        FROM satellite_images
                    """)
                
                stats = dict(zip([desc[0] for desc in cursor.description], cursor.fetchone()))
                
                # Imágenes por colección
                if zone_id:
                    cursor.execute("""
                        SELECT collection, COUNT(*) as count
                        FROM satellite_images 
                        WHERE zone_id = ?
                        GROUP BY collection
                    """, (zone_id,))
                else:
                    cursor.execute("""
                        SELECT collection, COUNT(*) as count
                        FROM satellite_images
                        GROUP BY collection
                    """)
                
                collections = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Consultas recientes
                if zone_id:
                    cursor.execute("""
                        SELECT * FROM satellite_queries 
                        WHERE zone_id = ?
                        ORDER BY query_date DESC 
                        LIMIT 10
                    """, (zone_id,))
                else:
                    cursor.execute("""
                        SELECT * FROM satellite_queries 
                        ORDER BY query_date DESC 
                        LIMIT 10
                    """)
                
                queries = [dict(zip([desc[0] for desc in cursor.description], row)) 
                          for row in cursor.fetchall()]
                
                return {
                    "success": True,
                    "zone_id": zone_id,
                    "statistics": stats,
                    "collections": collections,
                    "recent_queries": queries,
                    "generated_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error generating satellite report: {e}")
            return {"success": False, "error": str(e)}

def main():
    """Función principal para testing"""
    logging.basicConfig(level=logging.INFO)
    
    # Inicializar gestor
    manager = SatelliteIntegrationManager()
    
    # Buscar archivos GeoJSON
    geojson_files = list(Path("data/geojson").glob("*.geojson"))
    
    if geojson_files:
        latest_geojson = max(geojson_files, key=lambda p: p.stat().st_mtime)
        logger.info(f"Processing {latest_geojson}")
        
        # Procesar todas las zonas
        results = manager.process_all_zones(str(latest_geojson), days_back=30)
        
        # Generar reporte
        report = manager.generate_satellite_report()
        
        print(f"\n=== SATELLITE INTEGRATION RESULTS ===")
        print(f"Processed zones: {results.get('processed_zones', 0)}")
        print(f"Total images found: {results.get('total_images', 0)}")
        print(f"Collections: {list(report.get('collections', {}).keys())}")
        
        if results.get('errors'):
            print(f"Errors: {len(results['errors'])}")
            for error in results['errors'][:3]:
                print(f"  - {error}")
    
    else:
        print("No GeoJSON files found in data/geojson/")

if __name__ == "__main__":
    main()
