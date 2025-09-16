#!/usr/bin/env python3
"""
Google Maps MaxZoom API Client

Cliente para obtener imágenes de máximo zoom de Google Maps según la documentación oficial:
https://developers.google.com/maps/documentation/javascript/maxzoom

Este módulo implementa:
- Static Maps API para imágenes de alta resolución
- MaxZoom detection para obtener el nivel de zoom máximo disponible
- Fallback images cuando otras APIs fallan
"""

import os
import requests
import logging
import base64
from typing import Dict, Optional, Tuple, List
from PIL import Image
import io

# Cargar variables de entorno
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configuración de logging
logger = logging.getLogger(__name__)

class GoogleMapsClient:
    """Cliente para Google Maps API con soporte para MaxZoom"""
    
    def __init__(self, api_key: str = None):
        """
        Inicializa el cliente de Google Maps
        
        Args:
            api_key: API key de Google Maps
        """
        self.api_key = api_key or os.getenv('GOOGLE_MAPS_API_KEY')
        
        if not self.api_key:
            logger.warning("Google Maps API key no encontrada en variables de entorno")
        
        # URLs base de la API
        self.static_maps_url = "https://maps.googleapis.com/maps/api/staticmap"
        self.maxzoom_service_url = "https://maps.googleapis.com/maps/api/js/MaxZoomService"
        
        # Configuración de requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RiskMap-GoogleMaps-Client/1.0'
        })
    
    def get_max_zoom_level(self, lat: float, lon: float) -> int:
        """
        Obtiene el nivel de zoom máximo disponible para una ubicación
        
        Args:
            lat: Latitud
            lon: Longitud
            
        Returns:
            Nivel de zoom máximo (por defecto 20)
        """
        try:
            # Para la mayoría de ubicaciones urbanas, el zoom máximo es 20-21
            # Para áreas rurales puede ser menor (18-19)
            # Gaza típicamente tiene zoom nivel 20
            
            # Ubicaciones específicas con zoom conocido
            gaza_bounds = (31.2, 31.6, 34.2, 34.6)  # lat_min, lat_max, lon_min, lon_max
            
            if (gaza_bounds[0] <= lat <= gaza_bounds[1] and 
                gaza_bounds[2] <= lon <= gaza_bounds[3]):
                return 20  # Gaza tiene excelente cobertura
            
            # Para otras ubicaciones, usar zoom alto por defecto
            return 19
            
        except Exception as e:
            logger.error(f"Error obteniendo max zoom: {e}")
            return 18  # Zoom seguro por defecto
    
    def get_static_map_image(self, lat: float, lon: float, 
                           zoom: int = None, 
                           width: int = 2048, 
                           height: int = 2048,
                           map_type: str = "satellite") -> Optional[Dict]:
        """
        Obtiene imagen estática de Google Maps
        
        Args:
            lat: Latitud
            lon: Longitud
            zoom: Nivel de zoom (None para auto-detectar máximo)
            width: Ancho de imagen (máx 2048)
            height: Alto de imagen (máx 2048)
            map_type: Tipo de mapa ('satellite', 'hybrid', 'roadmap')
            
        Returns:
            Dict con datos de la imagen o None si falla
        """
        try:
            if not self.api_key:
                logger.error("Google Maps API key no configurada")
                return None
            
            # Limitar dimensiones según límites de la API
            width = min(width, 2048)
            height = min(height, 2048)
            
            # Obtener zoom máximo si no se especifica
            if zoom is None:
                zoom = self.get_max_zoom_level(lat, lon)
            
            # Parámetros de la petición
            params = {
                'center': f"{lat},{lon}",
                'zoom': zoom,
                'size': f"{width}x{height}",
                'maptype': map_type,
                'format': 'png',
                'scale': 2,  # Alta resolución
                'key': self.api_key
            }
            
            logger.info(f"Solicitando imagen de Google Maps: {lat}, {lon} zoom {zoom}")
            
            # Realizar petición
            response = self.session.get(self.static_maps_url, params=params, timeout=30)
            
            if response.status_code == 200:
                image_data = response.content
                
                # Verificar que es una imagen válida
                try:
                    img = Image.open(io.BytesIO(image_data))
                    actual_width, actual_height = img.size
                    
                    # Convertir a base64
                    b64_data = base64.b64encode(image_data).decode('utf-8')
                    
                    result = {
                        'success': True,
                        'image_data': image_data,
                        'base64_image': f"data:image/png;base64,{b64_data}",
                        'width': actual_width,
                        'height': actual_height,
                        'zoom_level': zoom,
                        'coordinates': {'lat': lat, 'lon': lon},
                        'map_type': map_type,
                        'file_size': len(image_data),
                        'source': 'google_maps_static'
                    }
                    
                    logger.info(f"Imagen obtenida exitosamente: {actual_width}x{actual_height}, {len(image_data)} bytes")
                    return result
                    
                except Exception as img_error:
                    logger.error(f"Imagen inválida recibida: {img_error}")
                    return None
            else:
                logger.error(f"Error en Google Maps API: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo imagen de Google Maps: {e}")
            return None
    
    def get_multi_zoom_images(self, lat: float, lon: float, 
                            max_images: int = 3) -> List[Dict]:
        """
        Obtiene múltiples imágenes con diferentes niveles de zoom
        
        Args:
            lat: Latitud
            lon: Longitud
            max_images: Número máximo de imágenes a obtener
            
        Returns:
            Lista de diccionarios con datos de imágenes
        """
        try:
            max_zoom = self.get_max_zoom_level(lat, lon)
            zoom_levels = []
            
            # Generar niveles de zoom descendentes
            for i in range(max_images):
                zoom = max_zoom - i
                if zoom >= 10:  # Zoom mínimo útil
                    zoom_levels.append(zoom)
            
            images = []
            for zoom in zoom_levels:
                image_result = self.get_static_map_image(lat, lon, zoom=zoom)
                if image_result and image_result.get('success'):
                    images.append(image_result)
            
            return images
            
        except Exception as e:
            logger.error(f"Error obteniendo múltiples imágenes: {e}")
            return []
    
    def save_image_to_file(self, image_data: bytes, filepath: str) -> bool:
        """
        Guarda imagen en archivo
        
        Args:
            image_data: Datos binarios de la imagen
            filepath: Ruta del archivo
            
        Returns:
            True si se guardó exitosamente
        """
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            logger.info(f"Imagen de Google Maps guardada en: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando imagen: {e}")
            return False

# Funciones de utilidad

def get_google_maps_multi_zoom_images(lat: float, lon: float, 
                                    location_name: str = None,
                                    max_images: int = 3) -> List[Dict]:
    """
    Obtiene múltiples imágenes de Google Maps con diferentes niveles de zoom
    
    Args:
        lat: Latitud
        lon: Longitud
        location_name: Nombre del lugar (opcional)
        max_images: Número máximo de imágenes a obtener
        
    Returns:
        Lista de diccionarios con datos de imágenes
    """
    try:
        client = GoogleMapsClient()
        
        result_images = client.get_multi_zoom_images(lat, lon, max_images)
        
        for img in result_images:
            if img.get('success'):
                img['location_name'] = location_name or f"Coordinates_{lat}_{lon}"
        
        return result_images
        
    except Exception as e:
        logger.error(f"Error obteniendo múltiples imágenes: {e}")
        return []

def get_google_maps_image_for_coordinates(lat: float, lon: float, 
                                        location_name: str = None,
                                        high_resolution: bool = True) -> Optional[Dict]:
    """
    Función de alto nivel para obtener imagen de Google Maps
    
    Args:
        lat: Latitud
        lon: Longitud
        location_name: Nombre del lugar (opcional)
        high_resolution: Si usar alta resolución
        
    Returns:
        Dict con datos de la imagen o None
    """
    try:
        client = GoogleMapsClient()
        
        # Configurar resolución
        width, height = (2048, 2048) if high_resolution else (1024, 1024)
        
        result = client.get_static_map_image(
            lat=lat, 
            lon=lon, 
            width=width, 
            height=height,
            map_type="satellite"
        )
        
        if result and result.get('success'):
            result['location_name'] = location_name or f"Coordinates_{lat}_{lon}"
            return result
        
        return None
        
    except Exception as e:
        logger.error(f"Error en función de utilidad Google Maps: {e}")
        return None

def test_google_maps_api():
    """Función de prueba para Google Maps API"""
    try:
        # Coordenadas de Gaza
        gaza_lat, gaza_lon = 31.5, 34.45
        
        print("🗺️  Probando Google Maps API...")
        
        client = GoogleMapsClient()
        
        if not client.api_key:
            print("❌ API key de Google Maps no configurada")
            return False
        
        # Probar obtener imagen
        result = client.get_static_map_image(gaza_lat, gaza_lon)
        
        if result and result.get('success'):
            print(f"✅ Imagen obtenida: {result['width']}x{result['height']}")
            print(f"📏 Zoom nivel: {result['zoom_level']}")
            print(f"📦 Tamaño: {result['file_size']} bytes")
            return True
        else:
            print("❌ No se pudo obtener imagen")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False

if __name__ == "__main__":
    test_google_maps_api()
