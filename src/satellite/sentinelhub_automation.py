
import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import sqlite3
import base64
from pathlib import Path
import logging

load_dotenv()

class SentinelHubAutomation:
    """Automatización completa de SentinelHub"""
    
    def __init__(self):
        self.client_id = os.getenv('SENTINELHUB_CLIENT_ID')
        self.client_secret = os.getenv('SENTINELHUB_CLIENT_SECRET')
        self.base_url = "https://services.sentinel-hub.com"
        self.access_token = None
        self.db_path = 'geopolitical_intelligence.db'
        
        # Crear directorio para imágenes
        self.images_dir = Path('src/satellite/images')
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        # Crear directorio para GeoJSON
        self.geojson_dir = Path('src/satellite/geojson')
        self.geojson_dir.mkdir(parents=True, exist_ok=True)
    
    def authenticate(self):
        """Autenticación con SentinelHub"""
        try:
            auth_url = f"{self.base_url}/oauth/token"
            
            data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            response = requests.post(auth_url, data=data)
            
            if response.status_code == 200:
                self.access_token = response.json()['access_token']
                return True
            else:
                print(f"Error de autenticación: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Error en autenticación SentinelHub: {e}")
            return False
    
    def get_conflict_locations(self):
        """Obtener ubicaciones de conflictos activos"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
            SELECT DISTINCT 
                location, latitude, longitude, 
                intensity_score, date
            FROM conflicts 
            WHERE latitude IS NOT NULL 
            AND longitude IS NOT NULL
            AND date >= date('now', '-7 days')
            AND intensity_score >= 0.5
            ORDER BY intensity_score DESC
            LIMIT 20
            """
            
            cursor = conn.execute(query)
            locations = []
            
            for row in cursor.fetchall():
                locations.append({
                    'location': row[0],
                    'lat': row[1],
                    'lon': row[2],
                    'intensity': row[3],
                    'date': row[4]
                })
            
            conn.close()
            return locations
            
        except Exception as e:
            print(f"Error obteniendo ubicaciones: {e}")
            return []
    
    def create_bbox(self, lat, lon, size_km=10):
        """Crear bounding box alrededor de coordenadas"""
        # Aproximación: 1 grado ≈ 111 km
        size_deg = size_km / 111.0
        
        return {
            "type": "Polygon",
            "coordinates": [[
                [lon - size_deg, lat - size_deg],
                [lon + size_deg, lat - size_deg],
                [lon + size_deg, lat + size_deg],
                [lon - size_deg, lat + size_deg],
                [lon - size_deg, lat - size_deg]
            ]]
        }
    
    def download_satellite_image(self, location):
        """Descargar imagen satelital para una ubicación"""
        try:
            if not self.access_token:
                if not self.authenticate():
                    return None
            
            # Crear bounding box
            bbox = self.create_bbox(location['lat'], location['lon'])
            
            # Configuración de la solicitud
            request_payload = {
                "input": {
                    "bounds": {
                        "geometry": bbox,
                        "properties": {
                            "crs": "http://www.opengis.net/def/crs/EPSG/0/4326"
                        }
                    },
                    "data": [{
                        "type": "sentinel-2-l2a",
                        "dataFilter": {
                            "timeRange": {
                                "from": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%dT00:00:00Z"),
                                "to": datetime.now().strftime("%Y-%m-%dT23:59:59Z")
                            },
                            "maxCloudCoverage": 20
                        }
                    }]
                },
                "output": {
                    "width": 512,
                    "height": 512,
                    "responses": [{
                        "identifier": "default",
                        "format": {
                            "type": "image/jpeg"
                        }
                    }]
                },
                "evalscript": """
                //VERSION=3
                function setup() {
                    return {
                        input: ["B02", "B03", "B04"],
                        output: { bands: 3 }
                    };
                }
                
                function evaluatePixel(sample) {
                    return [sample.B04, sample.B03, sample.B02];
                }
                """
            }
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            url = f"{self.base_url}/api/v1/process"
            response = requests.post(url, json=request_payload, headers=headers)
            
            if response.status_code == 200:
                # Guardar imagen
                safe_location = location['location'].replace(' ', '_').replace('/', '_')
                filename = f"{safe_location}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                filepath = self.images_dir / filename
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                # Crear GeoJSON con metadatos
                geojson_data = {
                    "type": "Feature",
                    "geometry": bbox,
                    "properties": {
                        "location": location['location'],
                        "intensity": location['intensity'],
                        "date": location['date'],
                        "image_file": str(filepath),
                        "download_date": datetime.now().isoformat(),
                        "source": "SentinelHub",
                        "cloud_coverage": "< 20%"
                    }
                }
                
                geojson_filename = f"{safe_location}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.geojson"
                geojson_filepath = self.geojson_dir / geojson_filename
                
                with open(geojson_filepath, 'w', encoding='utf-8') as f:
                    json.dump(geojson_data, f, indent=2, ensure_ascii=False)
                
                return {
                    'image_path': str(filepath),
                    'geojson_path': str(geojson_filepath),
                    'success': True
                }
            
            else:
                print(f"Error descargando imagen: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error en descarga satelital: {e}")
            return None
    
    def run_automated_download(self):
        """Ejecutar descarga automatizada para todas las ubicaciones"""
        try:
            locations = self.get_conflict_locations()
            results = []
            
            print(f"Iniciando descarga automatizada para {len(locations)} ubicaciones...")
            
            for i, location in enumerate(locations, 1):
                print(f"Procesando {i}/{len(locations)}: {location['location']}")
                
                result = self.download_satellite_image(location)
                if result:
                    results.append(result)
                    print(f"✅ Descargado: {location['location']}")
                else:
                    print(f"❌ Error: {location['location']}")
            
            print(f"Completado: {len(results)} imágenes descargadas")
            return results
            
        except Exception as e:
            print(f"Error en descarga automatizada: {e}")
            return []
    
    def update_database_with_satellite_data(self, results):
        """Actualizar BD con datos satelitales"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            for result in results:
                # Leer GeoJSON para obtener metadatos
                with open(result['geojson_path'], 'r', encoding='utf-8') as f:
                    geojson_data = json.load(f)
                
                properties = geojson_data['properties']
                
                # Insertar en tabla satellite_images
                cursor = conn.execute("""
                    INSERT OR REPLACE INTO satellite_images 
                    (location, image_path, geojson_path, download_date, 
                     intensity_score, source, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    properties['location'],
                    result['image_path'],
                    result['geojson_path'],
                    properties['download_date'],
                    properties['intensity'],
                    properties['source'],
                    json.dumps(properties)
                ))
            
            conn.commit()
            conn.close()
            
            print(f"Base de datos actualizada con {len(results)} registros satelitales")
            
        except Exception as e:
            print(f"Error actualizando BD: {e}")
            