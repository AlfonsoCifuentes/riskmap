#!/usr/bin/env python3
"""
Real Sentinel Hub Satellite Service
Integración real con la API de Sentinel Hub para análisis satelital
"""

import os
import requests
import json
import base64
import datetime
from pathlib import Path
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class SentinelHubService:
    """Servicio real para obtener imágenes satelitales de Sentinel Hub"""
    
    def __init__(self, client_id: str = None, client_secret: str = None, instance_id: str = None):
        self.client_id = client_id or os.getenv('SENTINEL_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('SENTINEL_CLIENT_SECRET')
        self.instance_id = instance_id or os.getenv('SENTINEL_INSTANCE_ID')
        self.base_url = "https://services.sentinel-hub.com"
        
        if not (self.client_id and self.client_secret and self.instance_id):
            raise ValueError("Credenciales de Sentinel Hub no configuradas: necesitas SENTINEL_CLIENT_ID, SENTINEL_CLIENT_SECRET y SENTINEL_INSTANCE_ID")
        
        # Crear directorio para imágenes
        self.images_dir = Path('data/satellite_images')
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
    def get_oauth_token(self) -> str:
        """Obtener token OAuth2 para autenticación"""
        try:
            auth_url = f"{self.base_url}/oauth/token"
            
            # Usar client_credentials flow
            data = {
                'grant_type': 'client_credentials'
            }
            
            # Usar client_id y client_secret para basic auth
            auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
            headers = {
                'Authorization': f'Basic {auth_header}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            response = requests.post(auth_url, data=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                return token_data['access_token']
            else:
                logger.error(f"Error obteniendo token OAuth: {response.status_code} - {response.text}")
                raise Exception(f"Error de autenticación: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error en autenticación OAuth: {e}")
            raise
    
    def search_available_images(self, lat: float, lon: float, 
                              days_back: int = 30,
                              cloud_cover_max: int = 20) -> List[Dict]:
        """Buscar imágenes disponibles para una ubicación"""
        try:
            token = self.get_oauth_token()
            
            # Crear bbox alrededor del punto (aprox 5km x 5km)
            offset = 0.05  # Aprox 5km en grados
            bbox = [lon - offset, lat - offset, lon + offset, lat + offset]
            
            # Fecha de búsqueda
            end_date = datetime.datetime.now()
            start_date = end_date - datetime.timedelta(days=days_back)
            
            search_url = f"{self.base_url}/api/v1/catalog/search"
            
            payload = {
                "collections": ["sentinel-2-l2a"],
                "datetime": f"{start_date.isoformat()}Z/{end_date.isoformat()}Z",
                "bbox": bbox,
                "limit": 10,
                "filter": {
                    "op": "and",
                    "args": [
                        {
                            "op": "<=",
                            "args": [{"property": "eo:cloud_cover"}, cloud_cover_max]
                        }
                    ]
                }
            }
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(search_url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                results = response.json()
                features = results.get('features', [])
                logger.info(f"✅ Encontradas {len(features)} imágenes disponibles")
                return features
            else:
                logger.error(f"Error buscando imágenes: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error en búsqueda de imágenes: {e}")
            return []
    
    def get_satellite_image(self, lat: float, lon: float, 
                           width: int = 512, height: int = 512,
                           image_format: str = 'jpeg') -> Tuple[bool, str, Dict]:
        """Obtener imagen satelital real para coordenadas específicas"""
        try:
            token = self.get_oauth_token()
            
            # Crear bbox alrededor del punto
            offset = 0.01  # Aprox 1km en grados para imagen detallada
            bbox = [lon - offset, lat - offset, lon + offset, lat + offset]
            
            # Evalscript para obtener imagen RGB verdadero color
            evalscript = """
            //VERSION=3
            function setup() {
                return {
                    input: ["B02", "B03", "B04"],
                    output: { bands: 3 }
                };
            }
            
            function evaluatePixel(sample) {
                return [sample.B04 * 2.5, sample.B03 * 2.5, sample.B02 * 2.5];
            }
            """
            
            # Request payload para Process API
            payload = {
                "input": {
                    "bounds": {
                        "bbox": bbox,
                        "properties": {
                            "crs": "http://www.opengis.net/def/crs/EPSG/0/4326"
                        }
                    },
                    "data": [{
                        "type": "sentinel-2-l2a",
                        "dataFilter": {
                            "timeRange": {
                                "from": (datetime.datetime.now() - datetime.timedelta(days=30)).isoformat() + "Z",
                                "to": datetime.datetime.now().isoformat() + "Z"
                            },
                            "maxCloudCoverage": 20
                        }
                    }]
                },
                "output": {
                    "width": width,
                    "height": height,
                    "responses": [{
                        "identifier": "default",
                        "format": {
                            "type": f"image/{image_format}"
                        }
                    }]
                },
                "evalscript": evalscript
            }
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            process_url = f"{self.base_url}/api/v1/process"
            response = requests.post(process_url, json=payload, headers=headers, timeout=60)
            
            if response.status_code == 200:
                # Guardar imagen
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"satellite_{lat}_{lon}_{timestamp}.{image_format}"
                file_path = self.images_dir / filename
                
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                
                # Metadatos
                metadata = {
                    'filename': filename,
                    'file_path': str(file_path),
                    'latitude': lat,
                    'longitude': lon,
                    'width': width,
                    'height': height,
                    'format': image_format,
                    'bbox': bbox,
                    'timestamp': datetime.datetime.now().isoformat(),
                    'file_size_bytes': len(response.content),
                    'provider': 'Sentinel Hub',
                    'collection': 'sentinel-2-l2a'
                }
                
                logger.info(f"✅ Imagen satelital guardada: {filename} ({len(response.content)} bytes)")
                return True, str(file_path), metadata
                
            else:
                logger.error(f"Error obteniendo imagen: {response.status_code} - {response.text}")
                return False, f"Error HTTP {response.status_code}", {}
                
        except Exception as e:
            logger.error(f"Error en get_satellite_image: {e}")
            return False, str(e), {}
    
    def get_latest_image_for_location(self, lat: float, lon: float) -> Tuple[bool, str, Dict]:
        """Obtener la imagen más reciente disponible para una ubicación"""
        try:
            # Primero buscar imágenes disponibles
            available_images = self.search_available_images(lat, lon, days_back=60, cloud_cover_max=30)
            
            if not available_images:
                logger.warning(f"No se encontraron imágenes para {lat}, {lon}")
                return False, "No hay imágenes disponibles para esta ubicación", {}
            
            # Tomar la imagen más reciente
            latest_image = available_images[0]  # Ya están ordenadas por fecha
            
            # Obtener la imagen
            success, path_or_error, metadata = self.get_satellite_image(lat, lon)
            
            if success:
                # Enriquecer metadatos con información de la búsqueda
                metadata.update({
                    'satellite_date': latest_image.get('properties', {}).get('datetime'),
                    'cloud_cover': latest_image.get('properties', {}).get('eo:cloud_cover'),
                    'satellite_id': latest_image.get('properties', {}).get('platform'),
                    'processing_level': latest_image.get('properties', {}).get('processing:level')
                })
                
                return True, path_or_error, metadata
            else:
                return False, path_or_error, metadata
                
        except Exception as e:
            logger.error(f"Error obteniendo imagen más reciente: {e}")
            return False, str(e), {}
    
    def test_connection(self) -> bool:
        """Probar conexión con Sentinel Hub"""
        try:
            token = self.get_oauth_token()
            logger.info("✅ Conexión con Sentinel Hub exitosa")
            return True
        except Exception as e:
            logger.error(f"❌ Error de conexión con Sentinel Hub: {e}")
            return False

def test_sentinel_hub_service():
    """Test del servicio de Sentinel Hub"""
    try:
        service = SentinelHubService()
        
        # Test básico de conexión
        if not service.test_connection():
            print("❌ Error de conexión")
            return False
        
        # Test con coordenadas de ejemplo (Siria)
        lat, lon = 36.2021, 37.1343
        
        print(f"🛰️ Obteniendo imagen satelital para {lat}, {lon}")
        success, result, metadata = service.get_latest_image_for_location(lat, lon)
        
        if success:
            print(f"✅ Imagen obtenida: {result}")
            print(f"📊 Metadatos: {json.dumps(metadata, indent=2)}")
        else:
            print(f"❌ Error: {result}")
        
        return success
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return False

if __name__ == "__main__":
    test_sentinel_hub_service()
