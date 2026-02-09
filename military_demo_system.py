#!/usr/bin/env python3
"""
Sistema de Demostración Militar para CV - RiskMap

Este módulo implementa detección de vehículos militares en coordenadas específicas
usando Google Maps Static API para obtener imágenes de bases militares reales
y procesarlas con nuestro modelo YOLO para demostrar capacidades de CV.

Coordenadas de demostración:
- Madrid área militar (España)
- Torrejón de Ardoz base aérea (España) 
- Kubinka airfield (Rusia)
- Le Bourget (Francia)
- Bases militares adicionales

Sistema diseñado para demostrar capacidades sin comprometer seguridad.
"""

import os
import sys
import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import random

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Coordenadas de demostración militar (bases públicamente conocidas)
DEMO_MILITARY_COORDINATES = [
    {
        'name': 'Base Aérea Torrejón de Ardoz',
        'country': 'España',
        'coordinates': (40.49748269453285, -3.435297016433034),
        'type': 'air_base',
        'expected_vehicles': ['aircraft', 'military_truck', 'helicopter'],
        'zoom_level': 18,
        'description': 'Base aérea principal de la Fuerza Aérea Española'
    },
    {
        'name': 'Área Militar Madrid',
        'country': 'España', 
        'coordinates': (40.555238777148816, -3.707179917614723),
        'type': 'military_facility',
        'expected_vehicles': ['military_truck', 'armored_vehicle'],
        'zoom_level': 19,
        'description': 'Instalación militar en área metropolitana de Madrid'
    },
    {
        'name': 'Kubinka Airfield',
        'country': 'Rusia',
        'coordinates': (55.56625086807381, 36.7176019105621),
        'type': 'air_base',
        'expected_vehicles': ['fighter_jet', 'military_truck', 'tank'],
        'zoom_level': 17,
        'description': 'Base aérea militar rusa con museo de aviación'
    },
    {
        'name': 'Le Bourget Airport',
        'country': 'Francia',
        'coordinates': (47.2428952109199, -0.0704433072085928),
        'type': 'mixed_facility',
        'expected_vehicles': ['aircraft', 'helicopter'],
        'zoom_level': 18,
        'description': 'Aeropuerto con secciones militares y civiles'
    },
    {
        'name': 'Base Militar Madrid Sur',
        'country': 'España',
        'coordinates': (40.55665555398047, -3.7080549074961917),
        'type': 'military_base',
        'expected_vehicles': ['armored_vehicle', 'military_truck'],
        'zoom_level': 19,
        'description': 'Instalación militar al sur de Madrid'
    },
    {
        'name': 'Facility Normandy',
        'country': 'Francia',
        'coordinates': (50.69476148157575, -2.2420507777713565),
        'type': 'military_facility',
        'expected_vehicles': ['military_truck', 'aircraft'],
        'zoom_level': 18,
        'description': 'Instalación militar en región de Normandía'
    },
    {
        'name': 'Madrid Military Complex',
        'country': 'España',
        'coordinates': (40.3747125710422, -3.7827595581231197),
        'type': 'military_complex',
        'expected_vehicles': ['tank', 'armored_vehicle', 'military_truck'],
        'zoom_level': 18,
        'description': 'Complejo militar en zona sur de Madrid'
    }
]

class MilitaryDemoSystem:
    """Sistema de demostración para detección de vehículos militares"""
    
    def __init__(self):
        """Inicializar sistema de demostración militar"""
        self.coordinates = DEMO_MILITARY_COORDINATES
        self.processed_images = []
        self.detection_results = []
        
        # Importar dependencias necesarias
        try:
            from google_maps_client import GoogleMapsClient
            self.google_maps = GoogleMapsClient()
        except ImportError:
            logger.warning("Google Maps client no disponible")
            self.google_maps = None
            
        try:
            from sentinel_hub_client import analyze_image_with_yolo, load_yolo_model
            self.yolo_model = load_yolo_model()
            self.analyze_function = analyze_image_with_yolo
        except ImportError:
            logger.warning("YOLO no disponible, usando simulación")
            self.yolo_model = None
            self.analyze_function = self._simulate_military_detection
    
    def process_all_demo_coordinates(self) -> List[Dict]:
        """
        Procesar todas las coordenadas de demostración militar
        
        Returns:
            Lista de resultados con detecciones
        """
        results = []
        
        for coord_info in self.coordinates:
            try:
                logger.info(f"🎯 Procesando: {coord_info['name']}")
                result = self.process_single_coordinate(coord_info)
                if result:
                    results.append(result)
                    
            except Exception as e:
                logger.error(f"Error procesando {coord_info['name']}: {e}")
                continue
        
        logger.info(f"✅ Procesadas {len(results)}/{len(self.coordinates)} coordenadas militares")
        return results
    
    def process_single_coordinate(self, coord_info: Dict) -> Optional[Dict]:
        """
        Procesar una coordenada específica
        
        Args:
            coord_info: Información de la coordenada
            
        Returns:
            Resultado del análisis con detecciones
        """
        try:
            lat, lon = coord_info['coordinates']
            zoom = coord_info.get('zoom_level', 18)
            
            # Obtener imagen de Google Maps
            image_data = self._get_google_maps_image(lat, lon, zoom)
            if not image_data:
                return None
            
            # Guardar imagen temporalmente
            image_path = f"temp_military_{coord_info['name'].replace(' ', '_')}.jpg"
            with open(image_path, 'wb') as f:
                f.write(image_data)
            
            # Analizar con YOLO
            analysis_result = self.analyze_function(image_path, self.yolo_model)
            
            # Agregar información de contexto
            analysis_result.update({
                'location_info': coord_info,
                'source_type': 'google_maps_static',
                'coordinates': coord_info['coordinates'],
                'image_path': image_path,
                'demo_purpose': True
            })
            
            # Crear imagen con detecciones marcadas
            annotated_image_path = self._create_annotated_image(
                image_path, 
                analysis_result.get('detections', []),
                coord_info['name']
            )
            
            analysis_result['annotated_image_path'] = annotated_image_path
            
            logger.info(f"✅ {coord_info['name']}: {analysis_result.get('military_objects', 0)} vehículos militares detectados")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error procesando coordenada {coord_info['name']}: {e}")
            return None
    
    def _get_google_maps_image(self, lat: float, lon: float, zoom: int) -> Optional[bytes]:
        """
        Obtener imagen de Google Maps Static API
        
        Args:
            lat: Latitud
            lon: Longitud  
            zoom: Nivel de zoom
            
        Returns:
            Datos binarios de la imagen
        """
        try:
            if self.google_maps:
                result = self.google_maps.get_static_map_image(
                    lat=lat,
                    lon=lon,
                    zoom=zoom,
                    width=1024,
                    height=1024,
                    map_type="satellite"
                )
                
                if result and result.get('success') and result.get('image_data'):
                    return result['image_data']
            
            # Fallback: usar requests directamente
            return self._fallback_google_maps_request(lat, lon, zoom)
            
        except Exception as e:
            logger.error(f"Error obteniendo imagen de Google Maps: {e}")
            return None
    
    def _fallback_google_maps_request(self, lat: float, lon: float, zoom: int) -> Optional[bytes]:
        """Fallback para obtener imagen directamente de Google Maps"""
        try:
            api_key = os.getenv('GOOGLE_MAPS_API_KEY')
            if not api_key:
                logger.warning("Google Maps API key no encontrada")
                return None
            
            url = f"https://maps.googleapis.com/maps/api/staticmap"
            
            # Intentar diferentes tipos de mapa si satellite falla
            map_types = ['satellite', 'hybrid', 'roadmap']
            
            for map_type in map_types:
                params = {
                    'center': f"{lat},{lon}",
                    'zoom': zoom,
                    'size': '1024x1024',
                    'maptype': map_type,
                    'key': api_key
                }
                
                try:
                    response = requests.get(url, params=params, timeout=30)
                    
                    if response.status_code == 200:
                        logger.info(f"✅ Imagen obtenida con maptype={map_type}")
                        return response.content
                    elif response.status_code == 403:
                        logger.warning(f"⚠️ Maptype {map_type} no disponible (403), probando siguiente...")
                        continue
                    else:
                        response.raise_for_status()
                        
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Error con maptype {map_type}: {e}")
                    continue
            
            # Si ningún tipo de mapa funciona, generar imagen simulada
            logger.warning("🎭 Generando imagen simulada como último recurso")
            return self._generate_mock_satellite_image(lat, lon, zoom)
            
        except Exception as e:
            logger.error(f"Error en fallback Google Maps: {e}")
            return self._generate_mock_satellite_image(lat, lon, zoom)
    
    def _generate_mock_satellite_image(self, lat: float, lon: float, zoom: int) -> bytes:
        """Generar imagen simulada para demostración"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io
            
            # Crear imagen base de 1024x1024
            img = Image.new('RGB', (1024, 1024), color=(34, 139, 34))  # Verde militar
            draw = ImageDraw.Draw(img)
            
            # Dibujar patrón de base militar simulada
            # Edificios rectangulares
            for i in range(5):
                for j in range(3):
                    x1 = 100 + i * 150
                    y1 = 200 + j * 200
                    x2 = x1 + 120
                    y2 = y1 + 80
                    draw.rectangle([x1, y1, x2, y2], fill=(128, 128, 128), outline=(64, 64, 64), width=2)
            
            # Pistas/carreteras
            draw.rectangle([50, 500, 950, 550], fill=(64, 64, 64))  # Pista horizontal
            draw.rectangle([500, 50, 550, 950], fill=(64, 64, 64))  # Pista vertical
            
            # Vehículos simulados (pequeños rectángulos)
            vehicle_positions = [(200, 300), (400, 350), (600, 320), (300, 700), (700, 650)]
            for x, y in vehicle_positions:
                draw.rectangle([x, y, x+15, y+25], fill=(139, 69, 19))  # Color marrón militar
            
            # Añadir texto informativo
            try:
                font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            text = f"DEMO MILITAR: {lat:.3f}, {lon:.3f} (Zoom: {zoom})"
            draw.text((10, 10), text, fill='white', font=font)
            draw.text((10, 40), "Imagen simulada para demostración", fill='yellow', font=font)
            
            # Convertir a bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='JPEG', quality=85)
            img_buffer.seek(0)
            
            logger.info(f"✅ Imagen simulada generada para {lat}, {lon}")
            return img_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error generando imagen simulada: {e}")
            # Retornar imagen mínima si falla todo
            return b''
    
    def _create_annotated_image(self, image_path: str, detections: List[Dict], location_name: str) -> str:
        """
        Crear imagen con detecciones marcadas
        
        Args:
            image_path: Ruta de la imagen original
            detections: Lista de detecciones
            location_name: Nombre de la ubicación
            
        Returns:
            Ruta de la imagen anotada
        """
        try:
            # Abrir imagen original
            image = Image.open(image_path)
            draw = ImageDraw.Draw(image)
            
            # Configurar fuente
            try:
                font = ImageFont.truetype("arial.ttf", 16)
            except:
                font = ImageFont.load_default()
            
            # Colores para diferentes tipos de vehículos
            colors = {
                'tank': '#FF0000',
                'armored_vehicle': '#FF6600', 
                'military_truck': '#00FF00',
                'aircraft': '#0066FF',
                'helicopter': '#FF00FF',
                'fighter_jet': '#FF0066',
                'default': '#FFFF00'
            }
            
            # Dibujar detecciones
            for detection in detections:
                if detection.get('confidence', 0) > 0.3:
                    bbox = detection.get('bbox', [])
                    if len(bbox) == 4:
                        x1, y1, x2, y2 = bbox
                        class_name = detection.get('class_name', 'unknown')
                        confidence = detection.get('confidence', 0)
                        
                        # Seleccionar color
                        color = colors.get(class_name.lower(), colors['default'])
                        
                        # Dibujar rectángulo
                        draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
                        
                        # Dibujar etiqueta
                        label = f"{class_name}: {confidence:.2f}"
                        text_bbox = draw.textbbox((x1, y1-25), label, font=font)
                        draw.rectangle(text_bbox, fill=color)
                        draw.text((x1, y1-25), label, fill='white', font=font)
            
            # Agregar título
            title = f"Detección Militar: {location_name}"
            draw.text((10, 10), title, fill='white', font=font)
            
            # Guardar imagen anotada
            annotated_path = image_path.replace('.jpg', '_annotated.jpg')
            image.save(annotated_path, 'JPEG', quality=95)
            
            return annotated_path
            
        except Exception as e:
            logger.error(f"Error creando imagen anotada: {e}")
            return image_path
    
    def _simulate_military_detection(self, image_path: str, model=None) -> Dict:
        """
        Simular detección militar si YOLO no está disponible
        
        Args:
            image_path: Ruta de la imagen
            model: Modelo (no usado en simulación)
            
        Returns:
            Resultado simulado de detección
        """
        logger.info(f"🎭 Simulando detección militar para: {image_path}")
        
        # Generar detecciones simuladas realistas
        military_vehicles = ['tank', 'armored_vehicle', 'military_truck', 'aircraft', 'helicopter']
        
        detections = []
        for i in range(random.randint(2, 6)):
            detection = {
                'class_id': i,
                'class_name': random.choice(military_vehicles),
                'confidence': random.uniform(0.65, 0.95),
                'bbox': [
                    random.randint(50, 300),  # x1
                    random.randint(50, 300),  # y1
                    random.randint(350, 800),  # x2
                    random.randint(350, 800)   # y2
                ],
                'is_military': True,
                'is_civilian': False,
                'is_infrastructure': False
            }
            detections.append(detection)
        
        military_count = len(detections)
        threat_level = "CRÍTICO" if military_count >= 4 else "ALTO" if military_count >= 2 else "MEDIO"
        
        return {
            'total_detections': len(detections),
            'high_confidence_detections': len(detections),
            'military_objects': military_count,
            'civilian_objects': 0,
            'infrastructure': random.randint(1, 3),
            'detections': detections,
            'explanations': [f"Vehículo militar detectado: {d['class_name']}" for d in detections[:3]],
            'threat_level': threat_level,
            'analysis_summary': f"Detección de {military_count} vehículos militares en zona de demostración",
            'analysis_timestamp': datetime.now().isoformat(),
            'image_analyzed': image_path,
            'model_used': 'simulation_demo',
            'has_detections': True,
            'max_confidence': max(d['confidence'] for d in detections),
            'has_military_detections': True,
            'demo_mode': True
        }
    
    def get_demo_summary(self) -> Dict:
        """
        Obtener resumen de las capacidades de demostración
        
        Returns:
            Resumen del sistema de demostración
        """
        return {
            'total_demo_locations': len(self.coordinates),
            'locations': [
                {
                    'name': coord['name'],
                    'country': coord['country'],
                    'type': coord['type'],
                    'expected_vehicles': coord['expected_vehicles']
                }
                for coord in self.coordinates
            ],
            'capabilities': [
                'Detección de tanques y vehículos blindados',
                'Identificación de aeronaves militares',
                'Reconocimiento de helicópteros de combate',
                'Detección de camiones militares',
                'Análisis de infraestructura militar'
            ],
            'demo_purpose': 'Demostración de capacidades CV sin comprometer seguridad',
            'data_sources': ['Google Maps Static API', 'Imágenes satelitales públicas'],
            'analysis_methods': ['YOLO custom model', 'Computer Vision', 'Machine Learning']
        }

# Función principal para integración con el sistema principal
def run_military_demo() -> Dict:
    """
    Ejecutar demostración completa del sistema militar
    
    Returns:
        Resultados completos de la demostración
    """
    demo_system = MilitaryDemoSystem()
    
    logger.info("🎯 Iniciando demostración de detección militar")
    results = demo_system.process_all_demo_coordinates()
    summary = demo_system.get_demo_summary()
    
    return {
        'demo_results': results,
        'summary': summary,
        'timestamp': datetime.now().isoformat(),
        'total_processed': len(results),
        'success': len(results) > 0
    }

if __name__ == "__main__":
    # Ejecutar demostración directamente
    demo_results = run_military_demo()
    print(json.dumps(demo_results, indent=2, ensure_ascii=False))