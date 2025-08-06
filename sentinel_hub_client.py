#!/usr/bin/env python3
"""
Sentinel Hub API Client Mejorado

Este módulo implementa un cliente robusto para la API de Sentinel Hub
siguiendo la documentación oficial y mejores prácticas.

Características:
- Autenticación OAuth2 correcta
- Requests para imágenes Sentinel-2 L2A
- Manejo de errores y reintentos
- Cache de tokens de autenticación
- Soporte para múltiples formatos de imagen
- Coordenadas correctas y bounding boxes
"""

import os
import sys
import logging
import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import base64
from io import BytesIO
from PIL import Image
import hashlib

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SentinelHubClient:
    """Cliente mejorado para Sentinel Hub API."""
    
    def __init__(self, client_id: str = None, client_secret: str = None):
        """
        Inicializa el cliente de Sentinel Hub.
        
        Args:
            client_id: Client ID de OAuth2
            client_secret: Client Secret de OAuth2
        """
        self.client_id = client_id or os.getenv('SENTINEL_HUB_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('SENTINEL_HUB_CLIENT_SECRET')
        
        if not self.client_id or not self.client_secret:
            logger.warning("Credenciales de Sentinel Hub no encontradas en variables de entorno")
        
        # URLs base según documentación oficial
        self.auth_url = "https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token"
        self.process_url = "https://services.sentinel-hub.com/api/v1/process"
        
        # Cache de token
        self.access_token = None
        self.token_expires_at = None
        
        # Configuración de requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RiskMap-SentinelHub-Client/1.0'
        })
    
    def get_access_token(self) -> Optional[str]:
        """
        Obtiene un token de acceso OAuth2 válido.
        
        Returns:
            Token de acceso o None si falla
        """
        # Verificar si el token actual sigue válido
        if (self.access_token and self.token_expires_at and 
            datetime.now() < self.token_expires_at - timedelta(minutes=5)):
            return self.access_token
        
        if not self.client_id or not self.client_secret:
            logger.error("Credenciales de Sentinel Hub no configuradas")
            return None
        
        try:
            # Preparar datos de autenticación según documentación
            auth_data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            logger.info("Solicitando token de acceso a Sentinel Hub...")
            response = self.session.post(
                self.auth_url,
                data=auth_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                
                # Calcular tiempo de expiración
                expires_in = token_data.get('expires_in', 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                logger.info(f"Token obtenido exitosamente, expira en {expires_in} segundos")
                return self.access_token
            
            else:
                logger.error(f"Error obteniendo token: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Excepción obteniendo token: {e}")
            return None
    
    def create_evalscript_true_color(self) -> str:
        """
        Crea el evalscript para obtener imágenes en color verdadero.
        
        Returns:
            Evalscript para Sentinel-2 true color
        """
        return """
        //VERSION=3
        function setup() {
            return {
                input: ["B02", "B03", "B04"],
                output: {
                    bands: 3,
                    sampleType: "AUTO"
                }
            }
        }
        
        function evaluatePixel(sample) {
            // Ajustar brillo y contraste para mejor visualización
            return [2.5 * sample.B04, 2.5 * sample.B03, 2.5 * sample.B02];
        }
        """
    
    def create_bounding_box(self, latitude: float, longitude: float, 
                           buffer_km: float = 5.0) -> List[float]:
        """
        Crea un bounding box alrededor de las coordenadas especificadas.
        
        Args:
            latitude: Latitud central
            longitude: Longitud central
            buffer_km: Buffer en kilómetros alrededor del punto
            
        Returns:
            Bounding box en formato [min_lon, min_lat, max_lon, max_lat]
        """
        # Conversión aproximada: 1 grado ≈ 111 km
        degree_buffer = buffer_km / 111.0
        
        # Ajustar por latitud para longitud (más preciso)
        import math
        lat_rad = math.radians(latitude)
        lon_degree_buffer = degree_buffer / math.cos(lat_rad)
        
        bbox = [
            longitude - lon_degree_buffer,  # min_lon
            latitude - degree_buffer,       # min_lat
            longitude + lon_degree_buffer,  # max_lon
            latitude + degree_buffer        # max_lat
        ]
        
        logger.info(f"Bounding box creado: {bbox} (buffer: {buffer_km}km)")
        return bbox
    
    def create_process_request(self, bbox: List[float], 
                             start_date: str = None, 
                             end_date: str = None,
                             width: int = 512, 
                             height: int = 512,
                             cloud_coverage: float = 50.0) -> Dict:
        """
        Crea el request para la API de Process según documentación oficial.
        
        Args:
            bbox: Bounding box [min_lon, min_lat, max_lon, max_lat]
            start_date: Fecha inicio (formato ISO: "2024-01-01T00:00:00Z")
            end_date: Fecha fin (formato ISO: "2024-01-31T00:00:00Z")
            width: Ancho de imagen en píxeles
            height: Alto de imagen en píxeles
            cloud_coverage: Máximo porcentaje de nubes aceptable
            
        Returns:
            Diccionario con el request completo
        """
        # Fechas por defecto: últimos 30 días
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%dT00:00:00Z")
        if not start_date:
            start_time = datetime.now() - timedelta(days=30)
            start_date = start_time.strftime("%Y-%m-%dT00:00:00Z")
        
        request_data = {
            "input": {
                "bounds": {
                    "properties": {
                        "crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
                    },
                    "bbox": bbox
                },
                "data": [
                    {
                        "type": "sentinel-2-l2a",
                        "dataFilter": {
                            "timeRange": {
                                "from": start_date,
                                "to": end_date
                            },
                            "maxCloudCoverage": cloud_coverage
                        }
                    }
                ]
            },
            "output": {
                "width": width,
                "height": height,
                "responses": [
                    {
                        "identifier": "default",
                        "format": {
                            "type": "image/jpeg"
                        }
                    }
                ]
            },
            "evalscript": self.create_evalscript_true_color()
        }
        
        logger.info(f"Request creado: bbox={bbox}, fechas={start_date} a {end_date}")
        return request_data
    
    def get_satellite_image(self, latitude: float, longitude: float,
                           buffer_km: float = 5.0,
                           start_date: str = None,
                           end_date: str = None,
                           width: int = 512,
                           height: int = 512) -> Optional[Dict]:
        """
        Obtiene una imagen satelital de Sentinel-2 para las coordenadas especificadas.
        
        Args:
            latitude: Latitud del punto de interés
            longitude: Longitud del punto de interés
            buffer_km: Buffer en kilómetros alrededor del punto
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)
            width: Ancho de la imagen
            height: Alto de la imagen
            
        Returns:
            Diccionario con información de la imagen y datos binarios
        """
        # Obtener token de acceso
        token = self.get_access_token()
        if not token:
            return None
        
        try:
            # Crear bounding box
            bbox = self.create_bounding_box(latitude, longitude, buffer_km)
            
            # Crear request
            request_data = self.create_process_request(
                bbox, start_date, end_date, width, height
            )
            
            # Preparar headers
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'multipart/form-data'
            }
            
            # Preparar datos para multipart/form-data
            files = {
                'request': (None, json.dumps(request_data), 'application/json'),
                'evalscript': (None, request_data['evalscript'], 'text/plain')
            }
            
            logger.info(f"Solicitando imagen satelital para {latitude}, {longitude}")
            
            # Hacer request a la API
            response = self.session.post(
                self.process_url,
                files=files,
                headers={'Authorization': f'Bearer {token}'},
                timeout=60
            )
            
            if response.status_code == 200:
                # Verificar que es una imagen
                content_type = response.headers.get('content-type', '')
                if 'image' in content_type:
                    
                    # Crear hash único para la imagen
                    image_hash = hashlib.md5(response.content).hexdigest()
                    
                    result = {
                        'success': True,
                        'image_data': response.content,
                        'content_type': content_type,
                        'size': len(response.content),
                        'coordinates': {
                            'latitude': latitude,
                            'longitude': longitude,
                            'bbox': bbox
                        },
                        'acquisition_info': {
                            'satellite': 'Sentinel-2',
                            'processing_level': 'L2A',
                            'date_range': f"{start_date} to {end_date}",
                            'buffer_km': buffer_km
                        },
                        'image_hash': image_hash,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    logger.info(f"Imagen obtenida exitosamente: {len(response.content)} bytes")
                    return result
                else:
                    logger.error(f"Respuesta no es una imagen: {content_type}")
                    return None
            
            elif response.status_code == 400:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                logger.error(f"Error 400 - Request inválido: {error_data}")
                return None
                
            elif response.status_code == 401:
                logger.error("Error 401 - Token de acceso inválido")
                # Limpiar token para forzar renovación
                self.access_token = None
                self.token_expires_at = None
                return None
                
            elif response.status_code == 429:
                logger.warning("Error 429 - Rate limit alcanzado")
                return None
                
            else:
                logger.error(f"Error {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("Timeout en request a Sentinel Hub")
            return None
        except Exception as e:
            logger.error(f"Excepción obteniendo imagen satelital: {e}")
            return None
    
    def save_image_to_file(self, image_data: bytes, filepath: str) -> bool:
        """
        Guarda los datos de imagen a un archivo.
        
        Args:
            image_data: Datos binarios de la imagen
            filepath: Ruta donde guardar la imagen
            
        Returns:
            True si se guardó exitosamente
        """
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            logger.info(f"Imagen guardada en: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando imagen: {e}")
            return False
    
    def convert_to_base64(self, image_data: bytes) -> str:
        """
        Convierte datos de imagen a base64 para uso en web.
        
        Args:
            image_data: Datos binarios de la imagen
            
        Returns:
            String base64 de la imagen
        """
        try:
            b64_data = base64.b64encode(image_data).decode('utf-8')
            return f"data:image/jpeg;base64,{b64_data}"
        except Exception as e:
            logger.error(f"Error convirtiendo a base64: {e}")
            return ""

# Funciones de utilidad para integración

def get_satellite_image_for_coordinates(lat: float, lon: float, 
                                      location_name: str = None) -> Optional[Dict]:
    """
    Función de alto nivel para obtener imagen satelital con coordenadas.
    
    Args:
        lat: Latitud
        lon: Longitud  
        location_name: Nombre del lugar (opcional)
        
    Returns:
        Diccionario con datos de la imagen o None
    """
    client = SentinelHubClient()
    
    # Verificar credenciales
    if not client.client_id or not client.client_secret:
        logger.error("Credenciales de Sentinel Hub no configuradas")
        return None
    
    result = client.get_satellite_image(lat, lon)
    
    if result and location_name:
        result['location_name'] = location_name
    
    return result

def get_satellite_image_for_zone(geojson_feature: Dict, zone_id: str, 
                                location: str = None, priority: str = 'medium') -> Optional[Dict]:
    """
    Función para obtener imagen satelital de zona de conflicto usando GeoJSON.
    
    Args:
        geojson_feature: Feature GeoJSON completo con geometría
        zone_id: ID único de la zona de conflicto
        location: Nombre de la ubicación (opcional)
        priority: Prioridad de la zona (critical, high, medium, low)
        
    Returns:
        Diccionario con datos de la imagen y metadatos de zona o None
    """
    try:
        client = SentinelHubClient()
        
        # Verificar credenciales
        if not client.client_id or not client.client_secret:
            logger.error("Credenciales de Sentinel Hub no configuradas")
            return None
        
        # Extraer información de la zona
        properties = geojson_feature.get('properties', {})
        geometry = geojson_feature.get('geometry', {})
        
        if geometry.get('type') != 'Polygon':
            logger.error(f"Geometría no válida para zona {zone_id}: {geometry.get('type')}")
            return None
        
        # Obtener coordenadas del polígono (primera coordenada para el centro)
        coordinates = geometry.get('coordinates', [[]])[0]
        if not coordinates:
            logger.error(f"Coordenadas vacías para zona {zone_id}")
            return None
        
        # Calcular centro del polígono
        center_lat = sum(coord[1] for coord in coordinates) / len(coordinates)
        center_lon = sum(coord[0] for coord in coordinates) / len(coordinates)
        
        logger.info(f"🛰️ Obteniendo imagen satelital para zona {zone_id}: {location} (centro: {center_lat:.4f}, {center_lon:.4f})")
        
        # Obtener imagen satelital usando el centro
        result = client.get_satellite_image(center_lat, center_lon)
        
        if result:
            # Agregar metadatos de zona
            result.update({
                'zone_id': zone_id,
                'location_name': location or properties.get('location', f'Zona {zone_id}'),
                'priority': priority,
                'risk_score': properties.get('risk_score', 0.0),
                'risk_level': properties.get('risk_level', 'unknown'),
                'total_events': properties.get('total_events', 0),
                'fatalities': properties.get('fatalities', 0),
                'data_sources': properties.get('data_sources', []),
                'geojson_feature': geojson_feature,
                'bbox': properties.get('bbox'),
                'monitoring_frequency': properties.get('monitoring_frequency', 'weekly'),
                'analysis_type': 'conflict_zone_satellite',
                'center_coordinates': {
                    'latitude': center_lat,
                    'longitude': center_lon
                }
            })
            
            logger.info(f"✅ Imagen satelital obtenida exitosamente para zona {zone_id}")
        else:
            logger.error(f"❌ Falló obtener imagen satelital para zona {zone_id}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error obteniendo imagen satelital para zona {zone_id}: {e}")
        return None

def setup_sentinel_hub_credentials():
    """
    Guía para configurar las credenciales de Sentinel Hub.
    """
    print("🛰️ CONFIGURACIÓN DE SENTINEL HUB")
    print("=" * 50)
    print()
    print("Para usar Sentinel Hub, necesitas:")
    print("1. Crear una cuenta en https://apps.sentinel-hub.com/")
    print("2. Ir a 'User Settings' > 'OAuth clients'")
    print("3. Crear un nuevo OAuth client")
    print("4. Copiar Client ID y Client Secret")
    print()
    print("Luego configura las variables de entorno:")
    print("export SENTINEL_HUB_CLIENT_ID='tu_client_id'")
    print("export SENTINEL_HUB_CLIENT_SECRET='tu_client_secret'")
    print()
    print("O crea un archivo .env en el directorio del proyecto:")
    print("SENTINEL_HUB_CLIENT_ID=tu_client_id")
    print("SENTINEL_HUB_CLIENT_SECRET=tu_client_secret")

if __name__ == "__main__":
    # Prueba del cliente
    import asyncio
    
    async def test_sentinel_hub():
        """Prueba básica del cliente de Sentinel Hub."""
        print("🛰️ Probando cliente de Sentinel Hub...")
        
        # Coordenadas de prueba (Madrid)
        test_lat = 40.4168
        test_lon = -3.7038
        
        result = get_satellite_image_for_coordinates(
            test_lat, test_lon, "Madrid, Spain"
        )
        
        if result:
            print(f"✅ Imagen obtenida: {result['size']} bytes")
            print(f"📍 Coordenadas: {result['coordinates']}")
            print(f"🛰️ Satélite: {result['acquisition_info']['satellite']}")
            
            # Guardar imagen de prueba
            if result.get('image_data'):
                test_path = "test_satellite_image.jpg"
                client = SentinelHubClient()
                if client.save_image_to_file(result['image_data'], test_path):
                    print(f"💾 Imagen guardada en: {test_path}")
        else:
            print("❌ No se pudo obtener imagen satelital")
            setup_sentinel_hub_credentials()
    
    # Ejecutar prueba
    asyncio.run(test_sentinel_hub())
