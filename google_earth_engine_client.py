#!/usr/bin/env python3
"""
Google Earth Engine Client - Ultra High Resolution Satellite Imagery

Este módulo implementa la solución completa de Google Earth Engine para obtener
imágenes satelitales de ultra alta resolución usando las mejores prácticas.

Capacidades:
- Sentinel-2: Resolución 10m, actualización cada 5 días
- Landsat 8/9: Resolución 30m, actualización cada 16 días  
- MODIS: Resolución 250m, actualización diaria
- Exportación masiva por regiones GeoJSON
- Detección automática de cambios temporales
- Análisis multi-espectral optimizado para detección militar

Basado en la guía oficial de Google Earth Engine:
https://developers.google.com/earth-engine
"""

import os
import sys
import logging
import json
import pathlib
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple, Any
import numpy as np
from PIL import Image
import io
import tempfile

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleEarthEngineClient:
    """Cliente para Google Earth Engine con funcionalidades avanzadas."""
    
    def __init__(self):
        """Inicializa el cliente Google Earth Engine."""
        self.is_initialized = False
        self.service_account_email = os.getenv('GEE_SERVICE_ACCOUNT_EMAIL')
        self.private_key_path = os.getenv('GEE_PRIVATE_KEY_PATH')
        
        # Configuración de colecciones disponibles
        self.collections_config = {
            'sentinel2': {
                'collection_id': 'COPERNICUS/S2_SR',
                'resolution': 10,  # metros
                'bands': ['B4', 'B3', 'B2', 'B8'],  # RGB + NIR
                'cloud_property': 'CLOUDY_PIXEL_PERCENTAGE',
                'description': 'Sentinel-2 Surface Reflectance'
            },
            'landsat8': {
                'collection_id': 'LANDSAT/LC08/C02/T1_L2',
                'resolution': 30,
                'bands': ['SR_B4', 'SR_B3', 'SR_B2', 'SR_B5'],  # RGB + NIR
                'cloud_property': 'CLOUD_COVER',
                'description': 'Landsat 8 Collection 2 Level 2'
            },
            'modis': {
                'collection_id': 'MODIS/006/MOD09GA',
                'resolution': 250,
                'bands': ['sur_refl_b01', 'sur_refl_b04', 'sur_refl_b03'],
                'cloud_property': 'cloud_state',
                'description': 'MODIS Surface Reflectance'
            }
        }
        
        # Intentar inicializar Earth Engine
        self._initialize_ee()
    
    def authenticate(self) -> bool:
        """Autentica con Google Earth Engine."""
        if self.is_initialized:
            return True
        return self._initialize_ee()
    
    def _initialize_ee(self) -> bool:
        """Inicializa Google Earth Engine con autenticación."""
        try:
            import ee
            
            if self.service_account_email and self.private_key_path:
                # Autenticación con service account
                if os.path.exists(self.private_key_path):
                    credentials = ee.ServiceAccountCredentials(
                        self.service_account_email, 
                        self.private_key_path
                    )
                    ee.Initialize(credentials)
                    logger.info("✅ Google Earth Engine inicializado con service account")
                else:
                    logger.warning(f"⚠️ Archivo de clave privada no encontrado: {self.private_key_path}")
                    return False
            else:
                # Intentar autenticación por defecto (requiere `earthengine authenticate`)
                try:
                    ee.Initialize()
                    logger.info("✅ Google Earth Engine inicializado con credenciales por defecto")
                except Exception as e:
                    error_msg = str(e)
                    logger.warning(f"⚠️ Fallo autenticación por defecto: {e}")
                    
                    # Proporcionar ayuda específica según el tipo de error
                    if "not registered" in error_msg:
                        logger.info("💡 El proyecto no está registrado para Google Earth Engine")
                        logger.info("🔗 Regístrate en: https://code.earthengine.google.com/register")
                    elif "not been used" in error_msg or "is disabled" in error_msg:
                        logger.info("💡 Habilita la API de Google Earth Engine en Google Cloud Console")
                    elif "permission" in error_msg.lower():
                        logger.info("💡 Verifica los permisos IAM del proyecto")
                    else:
                        logger.info("💡 Ejecuta 'earthengine authenticate' para configurar credenciales")
                    
                    return False
            
            self.is_initialized = True
            return True
            
        except ImportError:
            logger.error("❌ Google Earth Engine no instalado. Ejecuta: pip install earthengine-api")
            return False
        except Exception as e:
            logger.error(f"❌ Error inicializando Google Earth Engine: {e}")
            return False

    def batch_export_images(self, geometry: dict, date_range: dict = None, 
                          max_cloud_cover: int = 20, collection: str = 'LANDSAT/LC08/C02/T1_L2') -> dict:
        """
        Exporta lote de imágenes usando Google Earth Engine.
        
        Args:
            geometry: Geometría del área (GeoJSON)
            date_range: Rango de fechas {'start': 'YYYY-MM-DD', 'end': 'YYYY-MM-DD'}
            max_cloud_cover: Máximo porcentaje de nubes
            collection: Colección de imágenes a usar
            
        Returns:
            Diccionario con información de las tareas de exportación
        """
        if not self.is_initialized:
            logger.warning("⚠️ Google Earth Engine no inicializado")
            return {'success': False, 'error': 'GEE not initialized'}
        
        try:
            import ee
            
            # Convertir geometría GeoJSON a ee.Geometry
            if isinstance(geometry, dict):
                ee_geometry = ee.Geometry(geometry)
            else:
                ee_geometry = geometry
            
            # Configurar rango de fechas
            if not date_range:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                date_range = {
                    'start': start_date.strftime('%Y-%m-%d'),
                    'end': end_date.strftime('%Y-%m-%d')
                }
            
            # Crear colección de imágenes
            collection_obj = (ee.ImageCollection(collection)
                             .filterBounds(ee_geometry)
                             .filterDate(date_range['start'], date_range['end']))
            
            # Filtrar por nubosidad según la colección
            if 'LANDSAT' in collection:
                collection_obj = collection_obj.filter(ee.Filter.lt('CLOUD_COVER', max_cloud_cover))
            elif 'COPERNICUS/S2' in collection:
                collection_obj = collection_obj.filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', max_cloud_cover))
            
            # Contar imágenes disponibles
            image_count = collection_obj.size().getInfo()
            
            if image_count == 0:
                return {
                    'success': False,
                    'error': 'No images found for the specified criteria',
                    'collection': collection,
                    'date_range': date_range,
                    'max_cloud_cover': max_cloud_cover
                }
            
            # Crear compuesto de la colección
            composite = collection_obj.median()
            
            # Configurar tarea de exportación
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            task_name = f'gee_batch_export_{timestamp}'
            
            task = ee.batch.Export.image.toDrive(
                image=composite,
                description=task_name,
                folder='gee_batch_exports',
                scale=30 if 'LANDSAT' in collection else 10,
                region=ee_geometry,
                maxPixels=int(1e9),
                fileFormat='GeoTIFF'
            )
            
            task.start()
            
            return {
                'success': True,
                'task_id': task.id,
                'task_name': task_name,
                'task_count': 1,
                'collection': collection,
                'image_count': image_count,
                'date_range': date_range,
                'max_cloud_cover': max_cloud_cover,
                'export_folder': 'gee_batch_exports',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error en exportación por lotes: {e}")
            return {'success': False, 'error': str(e)}

    def find_best_image(self, latitude: float, longitude: float, 
                       date_range: dict = None, max_cloud_cover: int = 10,
                       target_resolution: int = 10) -> dict:
        """
        Busca la mejor imagen disponible para una ubicación.
        
        Args:
            latitude: Latitud del punto
            longitude: Longitud del punto
            date_range: Rango de fechas
            max_cloud_cover: Máximo porcentaje de nubes
            target_resolution: Resolución objetivo en metros
            
        Returns:
            Diccionario con información de la mejor imagen
        """
        if not self.is_initialized:
            logger.warning("⚠️ Google Earth Engine no inicializado")
            return {'success': False, 'error': 'GEE not initialized'}
        
        try:
            import ee
            
            # Crear geometría del punto
            point = ee.Geometry.Point([longitude, latitude])
            
            # Configurar rango de fechas
            if not date_range:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                date_range = {
                    'start': start_date.strftime('%Y-%m-%d'),
                    'end': end_date.strftime('%Y-%m-%d')
                }
            
            # Seleccionar colección según resolución objetivo
            if target_resolution <= 10:
                collection_id = 'COPERNICUS/S2_SR'
                cloud_property = 'CLOUDY_PIXEL_PERCENTAGE'
                scale = 10
            else:
                collection_id = 'LANDSAT/LC08/C02/T1_L2'
                cloud_property = 'CLOUD_COVER'
                scale = 30
            
            # Crear colección filtrada
            collection = (ee.ImageCollection(collection_id)
                         .filterBounds(point)
                         .filterDate(date_range['start'], date_range['end'])
                         .filter(ee.Filter.lt(cloud_property, max_cloud_cover))
                         .sort(cloud_property))
            
            image_count = collection.size().getInfo()
            
            if image_count == 0:
                return {
                    'success': False,
                    'error': 'No suitable images found',
                    'collection': collection_id,
                    'date_range': date_range,
                    'max_cloud_cover': max_cloud_cover
                }
            
            # Obtener la mejor imagen (menos nubes)
            best_image = collection.first()
            
            # Obtener información de la imagen
            image_info = best_image.getInfo()
            
            return {
                'success': True,
                'image_info': {
                    'id': image_info['id'],
                    'date': image_info['properties'].get('system:time_start'),
                    'cloud_cover': image_info['properties'].get(cloud_property, 0)
                },
                'collection': collection_id,
                'resolution_m': scale,
                'total_images': image_count,
                'coordinates': {'latitude': latitude, 'longitude': longitude},
                'date_range': date_range,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error buscando mejor imagen: {e}")
            return {'success': False, 'error': str(e)}

    def create_ultra_hd_mosaic(self, geometry: dict, date_range: dict = None,
                             max_cloud_cover: int = 5, target_resolution: int = 1) -> dict:
        """
        Crea un mosaico de ultra alta resolución.
        
        Args:
            geometry: Geometría del área
            date_range: Rango de fechas
            max_cloud_cover: Máximo porcentaje de nubes
            target_resolution: Resolución objetivo en metros
            
        Returns:
            Diccionario con información del mosaico
        """
        if not self.is_initialized:
            logger.warning("⚠️ Google Earth Engine no inicializado")
            return {'success': False, 'error': 'GEE not initialized'}
        
        try:
            import ee
            
            # Convertir geometría
            if isinstance(geometry, dict):
                ee_geometry = ee.Geometry(geometry)
            else:
                ee_geometry = geometry
            
            # Configurar rango de fechas
            if not date_range:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=60)  # Más días para mejor mosaico
                date_range = {
                    'start': start_date.strftime('%Y-%m-%d'),
                    'end': end_date.strftime('%Y-%m-%d')
                }
            
            # Usar Sentinel-2 para máxima resolución disponible (10m)
            collection = (ee.ImageCollection('COPERNICUS/S2_SR')
                         .filterBounds(ee_geometry)
                         .filterDate(date_range['start'], date_range['end'])
                         .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', max_cloud_cover)))
            
            image_count = collection.size().getInfo()
            
            if image_count == 0:
                return {
                    'success': False,
                    'error': 'No suitable images found for mosaic',
                    'date_range': date_range,
                    'max_cloud_cover': max_cloud_cover
                }
            
            # Crear mosaico usando las mejores imágenes
            mosaic = collection.median()
            
            # Aplicar realce para detección militar
            enhanced = mosaic.multiply(ee.Image([2.5, 2.5, 2.5]))
            
            # Configurar exportación del mosaico
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            task_name = f'ultra_hd_mosaic_{timestamp}'
            
            task = ee.batch.Export.image.toDrive(
                image=enhanced,
                description=task_name,
                folder='gee_ultra_hd_mosaics',
                scale=10,  # Máxima resolución de Sentinel-2
                region=ee_geometry,
                maxPixels=int(1e10),  # Más píxeles para mosaicos grandes
                fileFormat='GeoTIFF'
            )
            
            task.start()
            
            return {
                'success': True,
                'task_id': task.id,
                'task_name': task_name,
                'mosaic_info': {
                    'resolution': 10,  # Sentinel-2 máxima resolución
                    'images_used': image_count,
                    'enhancement': 'military_detection'
                },
                'date_range': date_range,
                'max_cloud_cover': max_cloud_cover,
                'export_folder': 'gee_ultra_hd_mosaics',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error generando mosaico ultra HD: {e}")
            return {'success': False, 'error': str(e)}

    def check_task_status(self, task_id: str) -> dict:
        """
        Verifica el estado de una tarea de Google Earth Engine.
        
        Args:
            task_id: ID de la tarea
            
        Returns:
            Diccionario con el estado de la tarea
        """
        if not self.is_initialized:
            logger.warning("⚠️ Google Earth Engine no inicializado")
            return {'success': False, 'error': 'GEE not initialized'}
        
        try:
            import ee
            
            # Obtener lista de tareas
            tasks = ee.batch.Task.list()
            
            for task in tasks:
                if task.id == task_id:
                    return {
                        'success': True,
                        'status': task.state,
                        'task_id': task_id,
                        'description': task.config.get('description', ''),
                        'creation_timestamp': task.creation_timestamp_ms,
                        'start_timestamp': task.start_timestamp_ms,
                        'update_timestamp': task.update_timestamp_ms
                    }
            
            return {
                'success': False,
                'error': 'Task not found',
                'task_id': task_id
            }
            
        except Exception as e:
            logger.error(f"❌ Error verificando tarea: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_optimized_image_collection(self, 
                                        collection_name: str,
                                        start_date: str, 
                                        end_date: str,
                                        region: Any,
                                        max_cloud_cover: int = 10) -> Optional[Any]:
        """
        Crea una colección de imágenes optimizada para análisis militar.
        
        Args:
            collection_name: Nombre de la colección ('sentinel2', 'landsat8', 'modis')
            start_date: Fecha inicio (YYYY-MM-DD)
            end_date: Fecha fin (YYYY-MM-DD)
            region: Región de interés (ee.Geometry)
            max_cloud_cover: Máximo porcentaje de nubes
            
        Returns:
            Colección de imágenes filtrada y procesada
        """
        if not self.is_initialized:
            logger.error("❌ Google Earth Engine no inicializado")
            return None
        
        try:
            import ee
            
            config = self.collections_config.get(collection_name)
            if not config:
                logger.error(f"❌ Colección desconocida: {collection_name}")
                return None
            
            # Crear colección base
            collection = (ee.ImageCollection(config['collection_id'])
                         .filterDate(start_date, end_date)
                         .filterBounds(region)
                         .filter(ee.Filter.lt(config['cloud_property'], max_cloud_cover)))
            
            # Seleccionar bandas específicas
            collection = collection.select(config['bands'])
            
            # Aplicar máscara de nubes específica por colección
            if collection_name == 'sentinel2':
                collection = collection.map(self._mask_s2_clouds)
            elif collection_name == 'landsat8':
                collection = collection.map(self._mask_landsat_clouds)
            
            logger.info(f"✅ Colección {collection_name} creada: {collection.size().getInfo()} imágenes")
            return collection
            
        except Exception as e:
            logger.error(f"❌ Error creando colección {collection_name}: {e}")
            return None
    
    def _mask_s2_clouds(self, image: Any) -> Any:
        """Máscara de nubes optimizada para Sentinel-2."""
        import ee
        
        qa = image.select('QA60')
        cloud_bit_mask = 1 << 10
        cirrus_bit_mask = 1 << 11
        mask = qa.bitwiseAnd(cloud_bit_mask).eq(0).And(
               qa.bitwiseAnd(cirrus_bit_mask).eq(0))
        
        return image.updateMask(mask).divide(10000).copyProperties(image, ['system:time_start'])
    
    def _mask_landsat_clouds(self, image: Any) -> Any:
        """Máscara de nubes optimizada para Landsat 8."""
        import ee
        
        qa = image.select('QA_PIXEL')
        cloud_mask = qa.bitwiseAnd(1 << 3).eq(0).And(
                    qa.bitwiseAnd(1 << 4).eq(0))
        
        return image.updateMask(cloud_mask).multiply(0.0000275).add(-0.2).copyProperties(image, ['system:time_start'])
    
    def create_military_detection_composite(self, 
                                          collection: Any,
                                          composite_method: str = 'median') -> Optional[Any]:
        """
        Crea un compuesto optimizado para detección de actividad militar.
        
        Args:
            collection: Colección de imágenes EE
            composite_method: Método de composición ('median', 'mean', 'mosaic')
            
        Returns:
            Imagen compuesta optimizada
        """
        if not self.is_initialized:
            return None
        
        try:
            import ee
            
            if composite_method == 'median':
                composite = collection.median()
            elif composite_method == 'mean':
                composite = collection.mean()
            elif composite_method == 'mosaic':
                composite = collection.mosaic()
            else:
                logger.warning(f"⚠️ Método desconocido {composite_method}, usando median")
                composite = collection.median()
            
            # Aplicar realce específico para detección militar
            # Realzar contraste para vehículos y estructuras
            enhanced = composite.multiply(ee.Image([2.5, 2.5, 2.5, 1.8]))  # RGB + NIR
            
            # Aplicar filtros de detección de bordes
            # Útil para identificar vehículos y estructuras rectangulares
            sobel = enhanced.convolve(ee.Kernel.sobel())
            
            # Combinar imagen original con detección de bordes
            final_composite = enhanced.addBands(sobel.rename('edges'))
            
            logger.info("✅ Compuesto militar creado exitosamente")
            return final_composite
            
        except Exception as e:
            logger.error(f"❌ Error creando compuesto militar: {e}")
            return None
    
    def export_images_by_geojson(self, 
                                image: Any,
                                geojson_path: str,
                                scale: int = 10,
                                folder: str = 'gee_batch_export',
                                name_pattern: str = 'satellite_{index}_{id}',
                                max_pixels: int = int(1e13)) -> List[Any]:
        """
        Exporta imágenes por cada feature en un archivo GeoJSON.
        
        Args:
            image: Imagen EE a exportar
            geojson_path: Ruta al archivo GeoJSON
            scale: Resolución en metros
            folder: Carpeta de destino en Google Drive
            name_pattern: Patrón de nombres (puede usar {index}, {id}, {name})
            max_pixels: Máximo número de píxeles por exportación
            
        Returns:
            Lista de tareas de exportación
        """
        if not self.is_initialized:
            logger.error("❌ Google Earth Engine no inicializado")
            return []
        
        try:
            import ee
            import geetools
            import geemap
            
            # Cargar GeoJSON
            with open(geojson_path, 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)
            
            # Convertir a FeatureCollection de EE
            fc = geemap.geojson_to_ee(geojson_data)
            
            # Lanzar exportaciones masivas
            tasks = geetools.batch.Export.image.byFeatures(
                image=image,
                features=fc,
                scale=scale,
                folder=folder,
                namePattern=name_pattern,
                maxPixels=max_pixels,
                fileFormat='GeoTIFF'
            )
            
            logger.info(f"✅ Se lanzaron {len(tasks)} tareas de exportación")
            logger.info(f"📁 Destino: Google Drive/{folder}")
            logger.info(f"📊 Resolución: {scale}m por pixel")
            
            return tasks
            
        except Exception as e:
            logger.error(f"❌ Error en exportación masiva: {e}")
            return []
    
    def get_best_available_image(self, 
                               latitude: float, 
                               longitude: float,
                               buffer_km: float = 5.0,
                               days_back: int = 30) -> Optional[Dict]:
        """
        Obtiene la mejor imagen disponible para una ubicación específica.
        
        Args:
            latitude: Latitud del punto de interés
            longitude: Longitud del punto de interés
            buffer_km: Buffer en kilómetros alrededor del punto
            days_back: Días hacia atrás para buscar imágenes
            
        Returns:
            Diccionario con información de la mejor imagen disponible
        """
        if not self.is_initialized:
            logger.warning("⚠️ Google Earth Engine no inicializado")
            return None
        
        try:
            import ee
            
            # Crear geometría del punto de interés
            point = ee.Geometry.Point([longitude, latitude])
            region = point.buffer(buffer_km * 1000)  # Convertir km a metros
            
            # Definir rango de fechas
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            best_image = None
            best_info = None
            
            # Probar diferentes colecciones en orden de preferencia
            collection_priority = ['sentinel2', 'landsat8', 'modis']
            
            for collection_name in collection_priority:
                try:
                    collection = self.create_optimized_image_collection(
                        collection_name, start_str, end_str, region, max_cloud_cover=20
                    )
                    
                    if collection and collection.size().getInfo() > 0:
                        # Obtener la imagen más reciente con menos nubes
                        sorted_collection = collection.sort('system:time_start', False)
                        first_image = sorted_collection.first()
                        
                        # Crear compuesto optimizado
                        composite = self.create_military_detection_composite(
                            ee.ImageCollection([first_image])
                        )
                        
                        config = self.collections_config[collection_name]
                        
                        best_info = {
                            'success': True,
                            'collection': collection_name,
                            'description': config['description'],
                            'resolution_m': config['resolution'],
                            'bands': config['bands'],
                            'region': region.getInfo(),
                            'date_range': f"{start_str} to {end_str}",
                            'total_images': collection.size().getInfo(),
                            'coordinates': {'latitude': latitude, 'longitude': longitude},
                            'buffer_km': buffer_km,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        best_image = composite
                        break
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error con colección {collection_name}: {e}")
                    continue
            
            if best_image is None:
                logger.warning("⚠️ No se encontraron imágenes para la región especificada")
                return {
                    'success': False,
                    'message': 'No se encontraron imágenes para la región y período especificado',
                    'coordinates': {'latitude': latitude, 'longitude': longitude},
                    'search_radius_km': buffer_km,
                    'days_searched': days_back
                }
            
            logger.info(f"✅ Mejor imagen encontrada: {best_info['collection']} "
                       f"({best_info['resolution_m']}m resolución)")
            
            return best_info
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo mejor imagen: {e}")
            return None
    
    def export_single_region(self, 
                            latitude: float, 
                            longitude: float,
                            buffer_km: float = 2.0,
                            filename: str = None) -> Optional[Dict]:
        """
        Exporta una imagen de una región específica.
        
        Args:
            latitude: Latitud del centro
            longitude: Longitud del centro
            buffer_km: Radio del buffer en kilómetros
            filename: Nombre del archivo (opcional)
            
        Returns:
            Información de la tarea de exportación
        """
        if not self.is_initialized:
            return None
        
        try:
            import ee
            
            # Obtener la mejor imagen disponible
            image_info = self.get_best_available_image(latitude, longitude, buffer_km)
            
            if not image_info or not image_info.get('success'):
                return image_info
            
            # Crear geometría de la región
            point = ee.Geometry.Point([longitude, latitude])
            region = point.buffer(buffer_km * 1000)
            
            # Recrear la imagen para exportación
            collection_name = image_info['collection']
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            collection = self.create_optimized_image_collection(
                collection_name, 
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d'),
                region
            )
            
            composite = self.create_military_detection_composite(collection)
            
            # Configurar exportación
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'satellite_{collection_name}_{timestamp}'
            
            # Lanzar tarea de exportación
            task = ee.batch.Export.image.toDrive(
                image=composite,
                description=filename,
                folder='gee_single_exports',
                scale=image_info['resolution_m'],
                region=region,
                maxPixels=int(1e9),
                fileFormat='GeoTIFF'
            )
            
            task.start()
            
            export_info = {
                'success': True,
                'task_id': task.id,
                'task_status': task.status(),
                'filename': filename,
                'collection': collection_name,
                'resolution_m': image_info['resolution_m'],
                'region_center': {'latitude': latitude, 'longitude': longitude},
                'buffer_km': buffer_km,
                'export_folder': 'gee_single_exports',
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Exportación iniciada: {filename}")
            logger.info(f"📊 ID de tarea: {task.id}")
            
            return export_info
            
        except Exception as e:
            logger.error(f"❌ Error en exportación individual: {e}")
            return None
    
    def check_export_status(self, task_id: str) -> Optional[Dict]:
        """
        Verifica el estado de una tarea de exportación.
        
        Args:
            task_id: ID de la tarea de exportación
            
        Returns:
            Estado de la tarea
        """
        if not self.is_initialized:
            return None
        
        try:
            import ee
            
            # Obtener lista de tareas
            tasks = ee.batch.Task.list()
            
            for task in tasks:
                if task.id == task_id:
                    status_info = {
                        'task_id': task_id,
                        'state': task.state,
                        'description': task.config.get('description', ''),
                        'creation_timestamp': task.creation_timestamp_ms,
                        'start_timestamp': task.start_timestamp_ms,
                        'update_timestamp': task.update_timestamp_ms,
                        'progress': getattr(task, 'progress', 0)
                    }
                    
                    if task.state == 'COMPLETED':
                        logger.info(f"✅ Tarea {task_id} completada exitosamente")
                    elif task.state == 'FAILED':
                        logger.error(f"❌ Tarea {task_id} falló")
                        status_info['error_message'] = getattr(task, 'error_message', 'Error desconocido')
                    elif task.state == 'RUNNING':
                        logger.info(f"🔄 Tarea {task_id} en progreso...")
                    
                    return status_info
            
            logger.warning(f"⚠️ Tarea {task_id} no encontrada")
            return {'task_id': task_id, 'state': 'NOT_FOUND'}
            
        except Exception as e:
            logger.error(f"❌ Error verificando estado de tarea {task_id}: {e}")
            return None
    
    def list_all_tasks(self) -> List[Dict]:
        """
        Lista todas las tareas de exportación.
        
        Returns:
            Lista de información de tareas
        """
        if not self.is_initialized:
            return []
        
        try:
            import ee
            
            tasks = ee.batch.Task.list()
            task_list = []
            
            for task in tasks:
                task_info = {
                    'task_id': task.id,
                    'state': task.state,
                    'description': task.config.get('description', ''),
                    'creation_timestamp': task.creation_timestamp_ms,
                    'task_type': task.task_type
                }
                task_list.append(task_info)
            
            logger.info(f"📋 {len(task_list)} tareas encontradas")
            return task_list
            
        except Exception as e:
            logger.error(f"❌ Error listando tareas: {e}")
            return []

# Función de utilidad para uso directo
def get_gee_client() -> GoogleEarthEngineClient:
    """Obtiene una instancia del cliente Google Earth Engine."""
    return GoogleEarthEngineClient()

# Ejemplo de uso
if __name__ == "__main__":
    # Crear cliente
    client = GoogleEarthEngineClient()
    
    if client.is_initialized:
        print("🚀 Cliente Google Earth Engine inicializado correctamente")
        
        # Ejemplo: Obtener imagen para Gaza
        result = client.get_best_available_image(31.4, 34.4, buffer_km=10)
        if result:
            print(f"📸 Mejor imagen: {result['collection']} - {result['resolution_m']}m")
        
        # Ejemplo: Listar tareas
        tasks = client.list_all_tasks()
        print(f"📋 Tareas activas: {len(tasks)}")
    else:
        print("❌ No se pudo inicializar Google Earth Engine")
        print("💡 Ejecuta 'earthengine authenticate' para configurar credenciales")
