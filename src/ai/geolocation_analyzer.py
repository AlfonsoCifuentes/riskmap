#!/usr/bin/env python3
"""
Analizador de Geolocalización Inteligente usando Ollama
Determina coordenadas geográficas reales de conflictos basándose en análisis de IA
"""

import sqlite3
import json
import logging
import requests
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import re

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeolocationAnalyzer:
    """Analizador que usa Ollama para determinar ubicaciones geográficas de conflictos"""
    
    def __init__(self, ollama_base_url="http://localhost:11434"):
        self.ollama_base_url = ollama_base_url
        self.model = "llama3:latest"  # Modelo principal disponible
        self.fallback_models = ["qwen3:14b", "qwen3:4b", "deepseek-r1:7b", "gemma2:2b"]  # Modelos de respaldo
        
        # Base de datos de coordenadas de países y ciudades principales para validación
        self.known_locations = {
            # Países principales con sus capitales
            'ucrania': {'lat': 50.4501, 'lon': 30.5234, 'type': 'country'},
            'ukraine': {'lat': 50.4501, 'lon': 30.5234, 'type': 'country'},
            'rusia': {'lat': 55.7558, 'lon': 37.6176, 'type': 'country'},
            'russia': {'lat': 55.7558, 'lon': 37.6176, 'type': 'country'},
            'china': {'lat': 39.9042, 'lon': 116.4074, 'type': 'country'},
            'iran': {'lat': 35.6892, 'lon': 51.3890, 'type': 'country'},
            'israel': {'lat': 31.7683, 'lon': 35.2137, 'type': 'country'},
            'palestina': {'lat': 31.9474, 'lon': 35.3027, 'type': 'country'},
            'palestine': {'lat': 31.9474, 'lon': 35.3027, 'type': 'country'},
            'siria': {'lat': 33.5138, 'lon': 36.2765, 'type': 'country'},
            'syria': {'lat': 33.5138, 'lon': 36.2765, 'type': 'country'},
            'irak': {'lat': 33.3152, 'lon': 44.3661, 'type': 'country'},
            'iraq': {'lat': 33.3152, 'lon': 44.3661, 'type': 'country'},
            'afganistan': {'lat': 34.5553, 'lon': 69.2075, 'type': 'country'},
            'afghanistan': {'lat': 34.5553, 'lon': 69.2075, 'type': 'country'},
            'corea del norte': {'lat': 39.0392, 'lon': 125.7625, 'type': 'country'},
            'north korea': {'lat': 39.0392, 'lon': 125.7625, 'type': 'country'},
            'taiwan': {'lat': 25.0330, 'lon': 121.5654, 'type': 'country'},
            'venezuela': {'lat': 10.4806, 'lon': -66.9036, 'type': 'country'},
            'colombia': {'lat': 4.7110, 'lon': -74.0721, 'type': 'country'},
            'myanmar': {'lat': 19.7633, 'lon': 96.0785, 'type': 'country'},
            'etiopia': {'lat': 9.1450, 'lon': 40.4897, 'type': 'country'},
            'ethiopia': {'lat': 9.1450, 'lon': 40.4897, 'type': 'country'},
            'sudan': {'lat': 15.5007, 'lon': 32.5599, 'type': 'country'},
            'mali': {'lat': 17.5707, 'lon': -3.9962, 'type': 'country'},
            'yemen': {'lat': 15.5527, 'lon': 48.5164, 'type': 'country'},
            'libia': {'lat': 26.3351, 'lon': 17.2283, 'type': 'country'},
            'libya': {'lat': 26.3351, 'lon': 17.2283, 'type': 'country'},
            
            # Ciudades importantes en zonas de conflicto
            'gaza': {'lat': 31.3547, 'lon': 34.3088, 'type': 'city'},
            'donetsk': {'lat': 48.0159, 'lon': 37.8028, 'type': 'city'},
            'lugansk': {'lat': 48.5740, 'lon': 39.3078, 'type': 'city'},
            'mariupol': {'lat': 47.0971, 'lon': 37.5407, 'type': 'city'},
            'kharkiv': {'lat': 49.9935, 'lon': 36.2304, 'type': 'city'},
            'aleppo': {'lat': 36.2021, 'lon': 37.1343, 'type': 'city'},
            'damascus': {'lat': 33.5138, 'lon': 36.2765, 'type': 'city'},
            'damasco': {'lat': 33.5138, 'lon': 36.2765, 'type': 'city'},
            'bagdad': {'lat': 33.3152, 'lon': 44.3661, 'type': 'city'},
            'baghdad': {'lat': 33.3152, 'lon': 44.3661, 'type': 'city'},
            'kabul': {'lat': 34.5553, 'lon': 69.2075, 'type': 'city'},
            'pyongyang': {'lat': 39.0392, 'lon': 125.7625, 'type': 'city'},
            'caracas': {'lat': 10.4806, 'lon': -66.9036, 'type': 'city'},
            'yangon': {'lat': 16.8661, 'lon': 96.1951, 'type': 'city'},
            'addis ababa': {'lat': 9.1450, 'lon': 40.4897, 'type': 'city'},
            'sanaa': {'lat': 15.3694, 'lon': 44.1910, 'type': 'city'},
            'tripoli': {'lat': 32.8872, 'lon': 13.1913, 'type': 'city'},
            'tripoli libya': {'lat': 32.8872, 'lon': 13.1913, 'type': 'city'},
            
            # Regiones problemáticas
            'donbas': {'lat': 48.0, 'lon': 38.0, 'type': 'region'},
            'crimea': {'lat': 45.0, 'lon': 34.0, 'type': 'region'},
            'kashmir': {'lat': 34.0, 'lon': 76.0, 'type': 'region'},
            'xinjiang': {'lat': 43.0, 'lon': 87.0, 'type': 'region'},
            'tibet': {'lat': 29.0, 'lon': 91.0, 'type': 'region'},
            'sahel': {'lat': 15.0, 'lon': 0.0, 'type': 'region'},
        }
    
    def test_ollama_connection(self) -> bool:
        """Verificar conectividad con Ollama"""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                available_models = [model['name'] for model in models]
                logger.info(f"✅ Ollama conectado. Modelos disponibles: {available_models}")
                
                # Verificar si nuestro modelo principal está disponible
                if self.model in available_models:
                    logger.info(f"✅ Modelo principal {self.model} disponible")
                    return True
                
                # Verificar modelos de respaldo
                for fallback in self.fallback_models:
                    if fallback in available_models:
                        logger.info(f"⚠️ Usando modelo de respaldo {fallback}")
                        self.model = fallback
                        return True
                
                # Si no hay modelos específicos, usar el primero disponible
                if available_models:
                    self.model = available_models[0]
                    logger.info(f"⚠️ Usando primer modelo disponible: {self.model}")
                    return True
                
                logger.error("❌ No hay modelos disponibles en Ollama")
                return False
            return False
        except Exception as e:
            logger.error(f"❌ Error conectando a Ollama: {e}")
            return False
    
    def extract_geolocation_with_ai(self, title: str, content: str) -> Optional[Dict]:
        """Usar Ollama para extraer información geográfica de un artículo"""
        
        # Texto combinado para análisis
        text = f"Título: {title}\n\nContenido: {content[:1000]}"  # Limitar contenido para eficiencia
        
        prompt = f"""Analiza el siguiente artículo de noticias y extrae información geográfica específica sobre conflictos, tensiones o eventos geopolíticos.

ARTÍCULO:
{text}

INSTRUCCIONES:
1. Identifica TODAS las ubicaciones geográficas específicas mencionadas (países, ciudades, regiones)
2. Determina cuál es la ubicación PRIMARY del conflicto o evento principal
3. Evalúa el nivel de intensidad del conflicto (high, medium, low)
4. Clasifica el tipo de conflicto (military, political, economic, territorial, diplomatic, cyber, other)

RESPONDE ÚNICAMENTE EN FORMATO JSON VÁLIDO:
{{
    "primary_location": "nombre de la ubicación principal",
    "all_locations": ["ubicación1", "ubicación2", "ubicación3"],
    "conflict_intensity": "high|medium|low",
    "conflict_type": "military|political|economic|territorial|diplomatic|cyber|other",
    "confidence": 0.0-1.0,
    "reasoning": "breve explicación de por qué elegiste esta ubicación"
}}

IMPORTANTE: Solo responde con JSON válido, sin texto adicional."""

        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Baja temperatura para respuestas más consistentes
                        "top_p": 0.9,
                        "num_predict": 500
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get('response', '').strip()
                
                # Intentar parsear JSON
                try:
                    # Limpiar respuesta para obtener solo el JSON
                    json_start = ai_response.find('{')
                    json_end = ai_response.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = ai_response[json_start:json_end]
                        geo_data = json.loads(json_str)
                        
                        # Validar estructura
                        required_fields = ['primary_location', 'conflict_intensity', 'confidence']
                        if all(field in geo_data for field in required_fields):
                            return geo_data
                        else:
                            logger.warning(f"Respuesta de IA incompleta: {geo_data}")
                            return None
                    else:
                        logger.warning(f"No se encontró JSON válido en respuesta: {ai_response}")
                        return None
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Error parseando JSON de IA: {e}")
                    logger.error(f"Respuesta completa: {ai_response}")
                    return None
            else:
                logger.error(f"Error en Ollama API: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error llamando a Ollama: {e}")
            return None
    
    def get_coordinates_for_location(self, location: str) -> Optional[Tuple[float, float]]:
        """Obtener coordenadas para una ubicación usando base de datos local"""
        if not location:
            return None
            
        location_lower = location.lower().strip()
        
        # Buscar coincidencia exacta
        if location_lower in self.known_locations:
            loc_data = self.known_locations[location_lower]
            return (loc_data['lat'], loc_data['lon'])
        
        # Buscar coincidencia parcial
        for known_loc, loc_data in self.known_locations.items():
            if known_loc in location_lower or location_lower in known_loc:
                logger.info(f"Coincidencia parcial: '{location}' -> '{known_loc}'")
                return (loc_data['lat'], loc_data['lon'])
        
        logger.warning(f"No se encontraron coordenadas para: {location}")
        return None
    
    def get_precise_coordinates_and_bounds(self, location_name: str, conflict_type: str) -> Dict:
        """Obtener coordenadas precisas y bounds para una ubicación específica"""
        location_lower = location_name.lower().strip()
        
        # Buscar en nuestro diccionario de coordenadas conocidas
        if location_lower in self.known_locations:
            coords = self.known_locations[location_lower]
            precision_type = coords['type']  # 'city', 'country', 'region'
            
            # Calcular bounds basado en el tipo de ubicación y tipo de conflicto
            bounds = self._calculate_bounds(coords['lat'], coords['lon'], precision_type, conflict_type)
            
            # Generar GeoJSON feature
            geojson_feature = self._create_geojson_feature(
                location_name, coords['lat'], coords['lon'], bounds, conflict_type, precision_type
            )
            
            return {
                'latitude': coords['lat'],
                'longitude': coords['lon'],
                'precision_type': precision_type,
                'bounds': bounds,
                'geojson_feature': geojson_feature,
                'area_size_km2': self._calculate_area_size(bounds),
                'satellite_ready': 1
            }
        
        # Si no se encuentra en coordenadas conocidas, intentar geocodificación básica
        return self._fallback_geocoding(location_name, conflict_type)
    
    def _calculate_bounds(self, lat: float, lon: float, precision_type: str, conflict_type: str) -> Dict:
        """Calcular bounds precisos basado en tipo de ubicación y conflicto"""
        
        # Factores de expansión basados en tipo de conflicto
        conflict_expansion = {
            'military': 1.5,    # Conflictos militares tienen mayor área de impacto
            'territorial': 2.0,  # Disputas territoriales cubren más área
            'political': 1.0,    # Conflictos políticos más localizados
            'economic': 1.2,     # Conflictos económicos moderadamente expandidos
            'diplomatic': 0.8,   # Conflictos diplomáticos más específicos
            'cyber': 0.5,        # Ciberataques muy localizados
            'other': 1.0
        }
        
        expansion_factor = conflict_expansion.get(conflict_type, 1.0)
        
        # Tamaños base por tipo de ubicación (en grados)
        base_sizes = {
            'coordinates': 0.01,  # ~1km
            'city': 0.05,         # ~5km
            'region': 0.3,        # ~30km
            'country': 1.0        # ~100km
        }
        
        base_size = base_sizes.get(precision_type, 0.1) * expansion_factor
        
        return {
            'north': lat + base_size,
            'south': lat - base_size,
            'east': lon + base_size,
            'west': lon - base_size
        }
    
    def _create_geojson_feature(self, location_name: str, lat: float, lon: float, 
                               bounds: Dict, conflict_type: str, precision_type: str) -> Dict:
        """Crear GeoJSON feature completo listo para API satelital"""
        
        # Crear polígono de bounds
        coordinates = [[
            [bounds['west'], bounds['north']],
            [bounds['east'], bounds['north']],
            [bounds['east'], bounds['south']],
            [bounds['west'], bounds['south']],
            [bounds['west'], bounds['north']]  # Cerrar polígono
        ]]
        
        feature = {
            "type": "Feature",
            "properties": {
                "name": location_name,
                "conflict_type": conflict_type,
                "precision": precision_type,
                "center_lat": lat,
                "center_lon": lon,
                "area_size_km2": self._calculate_area_size(bounds),
                "generated_at": datetime.now().isoformat(),
                "satellite_api_ready": True
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": coordinates
            }
        }
        
        return feature
    
    def _calculate_area_size(self, bounds: Dict) -> float:
        """Calcular área aproximada en km² usando fórmula haversine simplificada"""
        try:
            # Diferencias en grados
            lat_diff = abs(bounds['north'] - bounds['south'])
            lon_diff = abs(bounds['east'] - bounds['west'])
            
            # Conversión aproximada: 1 grado ≈ 111 km
            lat_km = lat_diff * 111
            lon_km = lon_diff * 111 * abs(math.cos(math.radians((bounds['north'] + bounds['south']) / 2)))
            
            return round(lat_km * lon_km, 2)
        except (ValueError, TypeError, KeyError):
            return 0.0
    
    def _fallback_geocoding(self, location_name: str, conflict_type: str) -> Dict:
        """Geocodificación de respaldo para ubicaciones no conocidas"""
        
        # Búsqueda aproximada por palabras clave
        location_lower = location_name.lower()
        
        # Patrones de países/regiones
        for keyword, coords in self.known_locations.items():
            if keyword in location_lower or location_lower in keyword:
                precision_type = 'region'  # Menos preciso al ser fallback
                bounds = self._calculate_bounds(coords['lat'], coords['lon'], precision_type, conflict_type)
                
                geojson_feature = self._create_geojson_feature(
                    location_name, coords['lat'], coords['lon'], bounds, conflict_type, precision_type
                )
                
                return {
                    'latitude': coords['lat'],
                    'longitude': coords['lon'],
                    'precision_type': precision_type,
                    'bounds': bounds,
                    'geojson_feature': geojson_feature,
                    'area_size_km2': self._calculate_area_size(bounds),
                    'satellite_ready': 1
                }
        
        # Si no se encuentra nada, retornar None
        return {
            'latitude': None,
            'longitude': None,
            'precision_type': 'unknown',
            'bounds': None,
            'geojson_feature': None,
            'area_size_km2': 0.0,
            'satellite_ready': 0
        }
    
    def analyze_articles_for_conflicts(self, timeframe_days: int = 7) -> List[Dict]:
        """Analizar artículos recientes para determinar zonas de conflicto reales"""
        
        if not self.test_ollama_connection():
            raise ConnectionError("❌ No se puede conectar a Ollama. Asegúrate de que esté corriendo y tenga modelos disponibles.")
        
        logger.info(f"🧠 Analizando artículos de los últimos {timeframe_days} días con IA...")
        
        # Conectar a base de datos
        conn = sqlite3.connect('data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        # Obtener artículos recientes con contenido sustancial
        cutoff_date = datetime.now() - timedelta(days=timeframe_days)
        cursor.execute("""
            SELECT id, title, content, url, published_at, risk_level, country, region
            FROM articles 
            WHERE published_at >= ? 
            AND (content IS NOT NULL AND LENGTH(content) > 100)
            AND (title IS NOT NULL AND LENGTH(title) > 10)
            ORDER BY published_at DESC
            LIMIT 50
        """, (cutoff_date.strftime('%Y-%m-%d %H:%M:%S'),))
        
        articles = cursor.fetchall()
        logger.info(f"📊 Encontrados {len(articles)} artículos para analizar")
        
        if not articles:
            logger.warning("⚠️ No se encontraron artículos recientes para analizar")
            return []
        
        conflicts = []
        processed = 0
        
        for article in articles:
            article_id, title, content, url, published_at, _, _, _ = article
            
            try:
                logger.info(f"🔍 Analizando artículo {article_id}: {title[:50]}...")
                
                # Analizar con IA
                geo_data = self.extract_geolocation_with_ai(title, content or "")
                
                if geo_data and geo_data.get('confidence', 0) >= 0.5:
                    primary_location = geo_data.get('primary_location', '')
                    
                    # Obtener coordenadas
                    coordinates = self.get_coordinates_for_location(primary_location)
                    
                    if coordinates:
                        lat, lon = coordinates
                        
                        conflict = {
                            'id': article_id,
                            'title': title,
                            'url': url,
                            'location': primary_location,
                            'all_locations': geo_data.get('all_locations', []),
                            'latitude': lat,
                            'longitude': lon,
                            'risk_level': geo_data.get('conflict_intensity', 'medium'),
                            'conflict_type': geo_data.get('conflict_type', 'other'),
                            'confidence': geo_data.get('confidence', 0),
                            'reasoning': geo_data.get('reasoning', ''),
                            'published_at': published_at,
                            'ai_analyzed': True
                        }
                        
                        conflicts.append(conflict)
                        logger.info(f"✅ Conflicto detectado: {primary_location} ({lat}, {lon}) - {geo_data.get('conflict_intensity')}")
                    else:
                        logger.warning(f"⚠️ Ubicación detectada pero sin coordenadas: {primary_location}")
                else:
                    logger.debug(f"❌ No se detectó conflicto válido en artículo {article_id}")
                
                processed += 1
                
                # Pausa pequeña para no saturar Ollama
                if processed % 5 == 0:
                    logger.info(f"📈 Progreso: {processed}/{len(articles)} artículos procesados")
                    
            except Exception as e:
                logger.error(f"❌ Error analizando artículo {article_id}: {e}")
                continue
        
        conn.close()
        
        logger.info(f"🎯 Análisis completado: {len(conflicts)} conflictos detectados de {len(articles)} artículos")
        
        return conflicts
    
    def save_conflicts_to_db(self, conflicts: List[Dict]) -> None:
        """Guardar conflictos analizados en la base de datos"""
        if not conflicts:
            return
            
        conn = sqlite3.connect('data/geopolitical_intel.db')
        cursor = conn.cursor()
        
        # Crear tabla de conflictos si no existe (versión mejorada)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_detected_conflicts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER,
                title TEXT,
                url TEXT,
                location TEXT,
                all_locations TEXT,
                latitude REAL,
                longitude REAL,
                precise_bounds TEXT, -- JSON con bounds precisos para área específica
                risk_level TEXT,
                conflict_type TEXT,
                confidence REAL,
                reasoning TEXT,
                published_at TEXT,
                detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                geojson_feature TEXT, -- GeoJSON feature completo listo para satélite
                area_precision TEXT, -- 'coordinates', 'city', 'region', 'country'
                area_size_km2 REAL, -- Tamaño estimado del área en km²
                satellite_ready INTEGER DEFAULT 0, -- 1 si está listo para consulta satelital
                FOREIGN KEY (article_id) REFERENCES articles (id)
            )
        """)
        
        # Crear tabla de zonas agregadas para consultas satelitales
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS satellite_target_zones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zone_name TEXT UNIQUE,
                center_latitude REAL,
                center_longitude REAL,
                bounds_geojson TEXT, -- GeoJSON Polygon con área exacta
                priority INTEGER, -- 1=high, 2=medium, 3=low
                conflict_count INTEGER,
                latest_conflict_date DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                area_size_km2 REAL
            )
        """)
        
        # Agregar columnas nuevas si no existen
        try:
            cursor.execute("ALTER TABLE ai_detected_conflicts ADD COLUMN precise_bounds TEXT")
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute("ALTER TABLE ai_detected_conflicts ADD COLUMN geojson_feature TEXT")
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute("ALTER TABLE ai_detected_conflicts ADD COLUMN area_precision TEXT")
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute("ALTER TABLE ai_detected_conflicts ADD COLUMN area_size_km2 REAL")
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute("ALTER TABLE ai_detected_conflicts ADD COLUMN satellite_ready INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        
        # Limpiar conflictos antiguos (más de 30 días)
        cursor.execute("""
            DELETE FROM ai_detected_conflicts 
            WHERE detected_at < datetime('now', '-30 days')
        """)
        
        # Insertar nuevos conflictos con coordenadas precisas y GeoJSON
        for conflict in conflicts:
            # Obtener coordenadas precisas y GeoJSON
            precise_data = self.get_precise_coordinates_and_bounds(
                conflict['location'], 
                conflict.get('conflict_type', 'other')
            )
            
            cursor.execute("""
                INSERT OR REPLACE INTO ai_detected_conflicts 
                (article_id, title, url, location, all_locations, latitude, longitude, 
                 precise_bounds, risk_level, conflict_type, confidence, reasoning, published_at,
                 geojson_feature, area_precision, area_size_km2, satellite_ready)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                conflict['id'],
                conflict['title'],
                conflict['url'],
                conflict['location'],
                json.dumps(conflict['all_locations']),
                precise_data['latitude'],
                precise_data['longitude'],
                json.dumps(precise_data['bounds']) if precise_data['bounds'] else None,
                conflict['risk_level'],
                conflict['conflict_type'],
                conflict['confidence'],
                conflict['reasoning'],
                conflict['published_at'],
                json.dumps(precise_data['geojson_feature']) if precise_data['geojson_feature'] else None,
                precise_data['precision_type'],
                precise_data['area_size_km2'],
                precise_data['satellite_ready']
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"💾 {len(conflicts)} conflictos guardados en base de datos")
        
        # Generar zonas agregadas para satélite
        self.generate_satellite_target_zones()
    
    def generate_satellite_target_zones(self):
        """Generar zonas agregadas optimizadas para consultas satelitales"""
        try:
            conn = sqlite3.connect('data/geopolitical_intel.db')
            cursor = conn.cursor()
            
            # Obtener conflictos recientes con coordenadas válidas
            cursor.execute("""
                SELECT location, latitude, longitude, conflict_type, 
                       area_precision, area_size_km2, detected_at,
                       COUNT(*) as conflict_count
                FROM ai_detected_conflicts 
                WHERE latitude IS NOT NULL 
                AND longitude IS NOT NULL 
                AND satellite_ready = 1
                AND detected_at >= datetime('now', '-14 days')
                GROUP BY ROUND(latitude, 2), ROUND(longitude, 2), location
                HAVING conflict_count >= 1
                ORDER BY conflict_count DESC, detected_at DESC
            """)
            
            zones_data = cursor.fetchall()
            
            if not zones_data:
                logger.warning("⚠️ No se encontraron zonas válidas para agregación satelital")
                return
            
            # Limpiar zonas antiguas
            cursor.execute("DELETE FROM satellite_target_zones WHERE created_at < datetime('now', '-7 days')")
            
            for zone in zones_data:
                location, lat, lon, conflict_type, precision, area_km2, last_conflict, count = zone
                
                # Determinar prioridad basada en número de conflictos y tipo
                priority = self._calculate_zone_priority(count, conflict_type, precision)
                
                # Crear bounds para la zona agregada
                bounds = self._calculate_bounds(lat, lon, precision, conflict_type)
                
                # Crear GeoJSON para la zona
                zone_geojson = self._create_geojson_feature(
                    location, lat, lon, bounds, conflict_type, precision
                )
                
                # Insertar o actualizar zona
                cursor.execute("""
                    INSERT OR REPLACE INTO satellite_target_zones
                    (zone_name, center_latitude, center_longitude, bounds_geojson,
                     priority, conflict_count, latest_conflict_date, area_size_km2,
                     last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (
                    location,
                    lat,
                    lon,
                    json.dumps(zone_geojson),
                    priority,
                    count,
                    last_conflict,
                    area_km2 or self._calculate_area_size(bounds)
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"🎯 {len(zones_data)} zonas satelitales agregadas generadas")
            
        except Exception as e:
            logger.error(f"❌ Error generando zonas satelitales: {e}")
    
    def _calculate_zone_priority(self, conflict_count: int, conflict_type: str, precision: str) -> int:
        """Calcular prioridad de zona para consultas satelitales (1=high, 2=medium, 3=low)"""
        
        # Prioridad base por tipo de conflicto
        type_priority = {
            'military': 1,
            'territorial': 1,
            'political': 2,
            'economic': 2,
            'diplomatic': 3,
            'cyber': 3,
            'other': 2
        }
        
        # Prioridad por precisión
        precision_bonus = {
            'coordinates': 0,
            'city': 0,
            'region': 1,
            'country': 2
        }
        
        base_priority = type_priority.get(conflict_type, 2)
        precision_penalty = precision_bonus.get(precision, 1)
        
        # Bonus por cantidad de conflictos
        if conflict_count >= 3:
            count_bonus = -1  # Mayor prioridad
        elif conflict_count >= 2:
            count_bonus = 0
        else:
            count_bonus = 1
        
        final_priority = max(1, min(3, base_priority + precision_penalty + count_bonus))
        return final_priority
    
    def get_satellite_ready_zones(self) -> List[Dict]:
        """Obtener zonas listas para consulta satelital"""
        try:
            conn = sqlite3.connect('data/geopolitical_intel.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT zone_name, center_latitude, center_longitude, bounds_geojson,
                       priority, conflict_count, latest_conflict_date, area_size_km2
                FROM satellite_target_zones
                ORDER BY priority ASC, conflict_count DESC
                LIMIT 20
            """)
            
            zones = cursor.fetchall()
            conn.close()
            
            result = []
            for zone in zones:
                name, lat, lon, geojson_str, priority, count, last_conflict, area = zone
                
                try:
                    geojson_data = json.loads(geojson_str) if geojson_str else None
                except (json.JSONDecodeError, TypeError):
                    geojson_data = None
                
                result.append({
                    'name': name,
                    'latitude': lat,
                    'longitude': lon,
                    'geojson': geojson_data,
                    'priority': priority,
                    'conflict_count': count,
                    'latest_conflict': last_conflict,
                    'area_size_km2': area,
                    'priority_label': ['High', 'Medium', 'Low'][priority - 1] if 1 <= priority <= 3 else 'Unknown'
                })
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo zonas satelitales: {e}")
            return []

if __name__ == "__main__":
    analyzer = GeolocationAnalyzer()
    
    try:
        conflicts = analyzer.analyze_articles_for_conflicts(timeframe_days=7)
        
        if conflicts:
            analyzer.save_conflicts_to_db(conflicts)
            print("\n✅ Análisis completado exitosamente!")
            print(f"🎯 {len(conflicts)} zonas de conflicto detectadas")
            
            # Mostrar resumen
            for i, conflict in enumerate(conflicts[:5], 1):
                print(f"\n{i}. {conflict['location']} ({conflict['latitude']}, {conflict['longitude']})")
                print(f"   Intensidad: {conflict['risk_level']} | Confianza: {conflict['confidence']:.2f}")
                print(f"   Tipo: {conflict['conflict_type']}")
                print(f"   Artículo: {conflict['title'][:60]}...")
        else:
            print("\n❌ No se detectaron conflictos. Verifica:")
            print("1. Que Ollama esté corriendo")
            print("2. Que haya artículos recientes en la base de datos")
            print("3. Que los artículos contengan información geográfica")
            
    except Exception as e:
        print(f"\n❌ Error en análisis: {e}")
        print("\nPosibles soluciones:")
        print("1. Iniciar Ollama: ollama serve")
        print("2. Instalar modelo: ollama pull llama3.1:8b")
        print("3. Verificar que la base de datos tenga artículos")
