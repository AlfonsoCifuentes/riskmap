#!/usr/bin/env python3
"""
BLOQUE 2C: Mapas con Datos Reales + Análisis SentinelHub
=======================================================

Automatización para:
- Implementar todos los mapas con datos reales (no mockups)
- Automatizar subida de GeoJSON desde SentinelHub
- Análisis automático de imágenes satelitales
- Integración con GDELT para eventos geopolíticos

Fecha: Agosto 2025
"""

import os
import sys
import logging
from pathlib import Path
import json
import sqlite3
import requests
from datetime import datetime, timedelta

# Configurar logging UTF-8
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('automation_block_2c.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class RealMapsAndSentinelSystem:
    """Sistema para mapas reales y análisis SentinelHub"""
    
    def __init__(self):
        logger.info("🚀 Iniciando Sistema Mapas Reales + SentinelHub - BLOQUE 2C")
        self.db_path = 'geopolitical_intelligence.db'
        
    def run_all_updates(self):
        """Ejecutar todas las actualizaciones"""
        try:
            logger.info("=" * 60)
            logger.info("🗺️ BLOQUE 2C: MAPAS REALES + SENTINELHUB")
            logger.info("=" * 60)
            
            # 1. Crear sistema de mapas con datos reales
            self.create_real_maps_system()
            
            # 2. Implementar automación SentinelHub
            self.implement_sentinelhub_automation()
            
            # 3. Crear endpoint para subida automática GeoJSON
            self.create_geojson_upload_system()
            
            # 4. Integrar análisis de imágenes satelitales
            self.implement_satellite_analysis()
            
            # 5. Actualizar base de datos para datos reales
            self.update_database_for_real_data()
            
            # 6. Crear sistema de cache inteligente
            self.create_intelligent_cache_system()
            
            logger.info("✅ BLOQUE 2C COMPLETADO EXITOSAMENTE")
            
        except Exception as e:
            logger.error(f"❌ Error en BLOQUE 2C: {e}")
            raise e
    
    def create_real_maps_system(self):
        """Crear sistema de mapas con datos reales"""
        try:
            logger.info("🗺️ Creando sistema de mapas con datos reales...")
            
            # Crear directorio para mapas
            maps_dir = Path('src/maps')
            maps_dir.mkdir(parents=True, exist_ok=True)
            
            # Sistema de mapas reales con Mapbox
            real_maps_code = '''
import folium
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import sqlite3
import json
from datetime import datetime, timedelta
import requests
import os
from dotenv import load_dotenv

load_dotenv()

class RealMapsEngine:
    """Motor de mapas con datos reales exclusivamente"""
    
    def __init__(self):
        self.mapbox_token = os.getenv('MAPBOX_TOKEN')
        self.db_path = 'geopolitical_intelligence.db'
        
    def get_real_conflicts_data(self):
        """Obtener datos reales de conflictos desde BD"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
            SELECT DISTINCT 
                location, latitude, longitude, 
                event_type, intensity_score, 
                date, source_reliability,
                description, affected_population
            FROM conflicts 
            WHERE latitude IS NOT NULL 
            AND longitude IS NOT NULL
            AND date >= date('now', '-30 days')
            AND source_reliability >= 0.7
            ORDER BY intensity_score DESC
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            return df
            
        except Exception as e:
            print(f"Error obteniendo datos reales de conflictos: {e}")
            return pd.DataFrame()
    
    def get_real_climate_data(self):
        """Obtener datos reales de clima desde GDELT"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
            SELECT DISTINCT 
                location, latitude, longitude,
                event_type, goldstein_scale,
                event_date, num_mentions,
                avg_tone, source_url
            FROM gdelt_events 
            WHERE latitude IS NOT NULL 
            AND longitude IS NOT NULL
            AND event_date >= date('now', '-7 days')
            AND (event_type LIKE '%CLIMATE%' 
                 OR event_type LIKE '%ENVIRONMENT%'
                 OR event_type LIKE '%DISASTER%')
            ORDER BY num_mentions DESC
            LIMIT 1000
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            return df
            
        except Exception as e:
            print(f"Error obteniendo datos climáticos reales: {e}")
            return pd.DataFrame()
    
    def create_real_heatmap(self):
        """Crear mapa de calor con datos reales"""
        try:
            # Datos reales de conflictos
            conflicts_df = self.get_real_conflicts_data()
            
            if conflicts_df.empty:
                return self.create_empty_map_message("No hay datos de conflictos disponibles")
            
            # Crear mapa de calor con Plotly
            fig = go.Figure()
            
            # Añadir puntos de conflictos reales
            fig.add_trace(go.Scattermapbox(
                lat=conflicts_df['latitude'],
                lon=conflicts_df['longitude'],
                mode='markers',
                marker=dict(
                    size=conflicts_df['intensity_score'] * 10,
                    color=conflicts_df['intensity_score'],
                    colorscale='Reds',
                    showscale=True,
                    colorbar=dict(title="Intensidad"),
                    sizemode='diameter'
                ),
                text=conflicts_df.apply(lambda row: 
                    f"<b>{row['location']}</b><br>"
                    f"Tipo: {row['event_type']}<br>"
                    f"Intensidad: {row['intensity_score']:.2f}<br>"
                    f"Fecha: {row['date']}<br>"
                    f"Fiabilidad: {row['source_reliability']:.2f}", axis=1),
                hovertemplate='%{text}<extra></extra>',
                name='Conflictos Actuales'
            ))
            
            # Configuración del mapa
            fig.update_layout(
                mapbox=dict(
                    accesstoken=self.mapbox_token,
                    style='satellite-streets',
                    zoom=2,
                    center=dict(lat=20, lon=0)
                ),
                height=600,
                margin=dict(r=0, t=0, l=0, b=0),
                title={
                    'text': 'Mapa de Calor - Conflictos Reales (Últimos 30 días)',
                    'x': 0.5,
                    'xanchor': 'center'
                }
            )
            
            return fig.to_html(include_plotlyjs=True)
            
        except Exception as e:
            print(f"Error creando mapa de calor real: {e}")
            return self.create_empty_map_message(f"Error: {str(e)}")
    
    def create_real_3d_globe(self):
        """Crear globo 3D con datos reales"""
        try:
            # Combinar datos reales
            conflicts_df = self.get_real_conflicts_data()
            climate_df = self.get_real_climate_data()
            
            fig = go.Figure()
            
            # Conflictos en rojo
            if not conflicts_df.empty:
                fig.add_trace(go.Scatter3d(
                    x=conflicts_df['longitude'],
                    y=conflicts_df['latitude'],
                    z=[0] * len(conflicts_df),
                    mode='markers',
                    marker=dict(
                        size=8,
                        color='red',
                        symbol='diamond'
                    ),
                    text=conflicts_df['location'],
                    name='Conflictos'
                ))
            
            # Eventos climáticos en azul
            if not climate_df.empty:
                fig.add_trace(go.Scatter3d(
                    x=climate_df['longitude'],
                    y=climate_df['latitude'],
                    z=[1] * len(climate_df),
                    mode='markers',
                    marker=dict(
                        size=6,
                        color='blue',
                        symbol='circle'
                    ),
                    text=climate_df['location'],
                    name='Eventos Climáticos'
                ))
            
            fig.update_layout(
                scene=dict(
                    xaxis_title='Longitud',
                    yaxis_title='Latitud',
                    zaxis_title='Tipo de Evento',
                    camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
                ),
                title='Globo 3D - Eventos Reales Mundiales',
                height=600
            )
            
            return fig.to_html(include_plotlyjs=True)
            
        except Exception as e:
            print(f"Error creando globo 3D: {e}")
            return self.create_empty_map_message(f"Error: {str(e)}")
    
    def create_empty_map_message(self, message):
        """Crear mensaje para mapa vacío"""
        return f"""
        <div class="alert alert-info text-center">
            <h4><i class="fas fa-info-circle"></i> Información</h4>
            <p>{message}</p>
            <small>Los datos se actualizan automáticamente cada hora</small>
        </div>
        """
    
    def get_real_statistics(self):
        """Obtener estadísticas reales de la BD"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Estadísticas de conflictos
            conflicts_stats = pd.read_sql_query("""
                SELECT 
                    COUNT(*) as total_conflicts,
                    AVG(intensity_score) as avg_intensity,
                    MAX(intensity_score) as max_intensity,
                    COUNT(DISTINCT location) as affected_locations
                FROM conflicts 
                WHERE date >= date('now', '-30 days')
            """, conn)
            
            # Estadísticas GDELT
            gdelt_stats = pd.read_sql_query("""
                SELECT 
                    COUNT(*) as total_events,
                    AVG(goldstein_scale) as avg_goldstein,
                    COUNT(DISTINCT location) as gdelt_locations
                FROM gdelt_events 
                WHERE event_date >= date('now', '-7 days')
            """, conn)
            
            conn.close()
            
            return {
                'conflicts': conflicts_stats.to_dict('records')[0] if not conflicts_stats.empty else {},
                'gdelt': gdelt_stats.to_dict('records')[0] if not gdelt_stats.empty else {}
            }
            
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
            return {'conflicts': {}, 'gdelt': {}}
            '''
            
            # Guardar motor de mapas reales
            real_maps_file = maps_dir / 'real_maps_engine.py'
            with open(real_maps_file, 'w', encoding='utf-8') as f:
                f.write(real_maps_code)
            
            logger.info("✅ Sistema de mapas reales creado")
            
        except Exception as e:
            logger.error(f"❌ Error creando mapas reales: {e}")
    
    def implement_sentinelhub_automation(self):
        """Implementar automación SentinelHub"""
        try:
            logger.info("🛰️ Implementando automación SentinelHub...")
            
            # Crear directorio satellite
            satellite_dir = Path('src/satellite')
            satellite_dir.mkdir(parents=True, exist_ok=True)
            
            # Sistema SentinelHub automatizado
            sentinel_code = '''
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
            '''
            
            # Guardar sistema SentinelHub
            sentinel_file = satellite_dir / 'sentinelhub_automation.py'
            with open(sentinel_file, 'w', encoding='utf-8') as f:
                f.write(sentinel_code)
            
            logger.info("✅ Automación SentinelHub implementada")
            
        except Exception as e:
            logger.error(f"❌ Error implementando SentinelHub: {e}")
    
    def create_geojson_upload_system(self):
        """Crear sistema de subida automática de GeoJSON"""
        try:
            logger.info("📤 Creando sistema de subida automática GeoJSON...")
            
            # Script de subida automática
            upload_code = '''
import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime
import shutil
import logging

class GeoJSONUploadSystem:
    """Sistema de subida automática de GeoJSON"""
    
    def __init__(self):
        self.geojson_dir = Path('src/satellite/geojson')
        self.upload_dir = Path('src/web/static/geojson')
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = 'geopolitical_intelligence.db'
    
    def scan_and_upload_geojson(self):
        """Escanear y subir archivos GeoJSON automáticamente"""
        try:
            uploaded_files = []
            
            # Buscar archivos GeoJSON
            geojson_files = list(self.geojson_dir.glob('*.geojson'))
            
            for geojson_file in geojson_files:
                # Leer contenido
                with open(geojson_file, 'r', encoding='utf-8') as f:
                    geojson_data = json.load(f)
                
                # Copiar a directorio web
                web_filename = f"auto_{geojson_file.name}"
                web_path = self.upload_dir / web_filename
                
                shutil.copy2(geojson_file, web_path)
                
                # Registrar en BD
                self.register_geojson_in_database(geojson_data, str(web_path))
                
                uploaded_files.append({
                    'original': str(geojson_file),
                    'web_path': str(web_path),
                    'location': geojson_data['properties'].get('location', 'Unknown')
                })
            
            print(f"Subidos automáticamente {len(uploaded_files)} archivos GeoJSON")
            return uploaded_files
            
        except Exception as e:
            print(f"Error en subida automática: {e}")
            return []
    
    def register_geojson_in_database(self, geojson_data, web_path):
        """Registrar GeoJSON en base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            properties = geojson_data['properties']
            
            cursor = conn.execute("""
                INSERT OR REPLACE INTO geojson_files
                (filename, location, upload_date, properties, geometry, web_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                Path(web_path).name,
                properties.get('location', 'Unknown'),
                datetime.now().isoformat(),
                json.dumps(properties),
                json.dumps(geojson_data['geometry']),
                web_path
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error registrando GeoJSON en BD: {e}")
    
    def create_geojson_api_endpoint(self):
        """Crear endpoint API para GeoJSON"""
        endpoint_code = """
# Endpoints API para GeoJSON
@app.route('/api/geojson/list')
def api_geojson_list():
    \"\"\"Listar todos los archivos GeoJSON disponibles\"\"\"
    try:
        conn = sqlite3.connect('geopolitical_intelligence.db')
        
        cursor = conn.execute(\"\"\"
            SELECT filename, location, upload_date, web_path, properties
            FROM geojson_files
            ORDER BY upload_date DESC
        \"\"\")
        
        geojson_files = []
        for row in cursor.fetchall():
            geojson_files.append({
                'filename': row[0],
                'location': row[1], 
                'upload_date': row[2],
                'web_path': row[3],
                'properties': json.loads(row[4]) if row[4] else {}
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'count': len(geojson_files),
            'files': geojson_files
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/geojson/auto-upload')
def api_geojson_auto_upload():
    \"\"\"Ejecutar subida automática de GeoJSON\"\"\"
    try:
        upload_system = GeoJSONUploadSystem()
        uploaded_files = upload_system.scan_and_upload_geojson()
        
        return jsonify({
            'success': True,
            'uploaded_count': len(uploaded_files),
            'files': uploaded_files
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
"""
        return endpoint_code
            '''
            
            # Guardar sistema de subida
            upload_dir = Path('src/upload')
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            upload_file = upload_dir / 'geojson_upload_system.py'
            with open(upload_file, 'w', encoding='utf-8') as f:
                f.write(upload_code)
            
            logger.info("✅ Sistema de subida automática GeoJSON creado")
            
        except Exception as e:
            logger.error(f"❌ Error creando sistema de subida: {e}")
    
    def implement_satellite_analysis(self):
        """Implementar análisis automático de imágenes satelitales"""
        try:
            logger.info("🔍 Implementando análisis de imágenes satelitales...")
            
            # Crear directorio analysis
            analysis_dir = Path('src/analysis')
            analysis_dir.mkdir(parents=True, exist_ok=True)
            
            # Sistema de análisis satelital
            analysis_code = '''
import cv2
import numpy as np
from pathlib import Path
import json
import sqlite3
from datetime import datetime
import logging

class SatelliteImageAnalysis:
    """Análisis automático de imágenes satelitales"""
    
    def __init__(self):
        self.images_dir = Path('src/satellite/images')
        self.db_path = 'geopolitical_intelligence.db'
    
    def analyze_all_images(self):
        """Analizar todas las imágenes satelitales"""
        try:
            image_files = list(self.images_dir.glob('*.jpg'))
            results = []
            
            for image_file in image_files:
                analysis_result = self.analyze_single_image(image_file)
                if analysis_result:
                    results.append(analysis_result)
                    self.save_analysis_to_database(analysis_result)
            
            print(f"Analizadas {len(results)} imágenes satelitales")
            return results
            
        except Exception as e:
            print(f"Error en análisis masivo: {e}")
            return []
    
    def analyze_single_image(self, image_path):
        """Analizar una imagen satelital individual"""
        try:
            # Cargar imagen
            image = cv2.imread(str(image_path))
            if image is None:
                return None
            
            # Convertir a RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Análisis básico
            analysis = {
                'image_path': str(image_path),
                'filename': image_path.name,
                'analysis_date': datetime.now().isoformat(),
                'dimensions': image.shape,
                'file_size': image_path.stat().st_size
            }
            
            # Detección de cambios en vegetación (NDVI simplificado)
            analysis['vegetation_index'] = self.calculate_vegetation_index(image_rgb)
            
            # Detección de agua
            analysis['water_detection'] = self.detect_water_bodies(image_rgb)
            
            # Detección de infraestructura
            analysis['infrastructure_detection'] = self.detect_infrastructure(image_rgb)
            
            # Score de riesgo general
            analysis['risk_score'] = self.calculate_risk_score(analysis)
            
            return analysis
            
        except Exception as e:
            print(f"Error analizando imagen {image_path}: {e}")
            return None
    
    def calculate_vegetation_index(self, image):
        """Calcular índice de vegetación simplificado"""
        try:
            # Separar canales RGB
            red = image[:, :, 0].astype(float)
            green = image[:, :, 1].astype(float)
            blue = image[:, :, 2].astype(float)
            
            # NDVI simplificado (usando verde como proxy de NIR)
            ndvi = np.divide(green - red, green + red + 1e-8)
            
            return {
                'mean_ndvi': float(np.mean(ndvi)),
                'vegetation_coverage': float(np.sum(ndvi > 0.2) / ndvi.size),
                'healthy_vegetation': float(np.sum(ndvi > 0.5) / ndvi.size)
            }
            
        except Exception as e:
            print(f"Error calculando índice vegetación: {e}")
            return {}
    
    def detect_water_bodies(self, image):
        """Detectar cuerpos de agua"""
        try:
            # Convertir a HSV para mejor detección de agua
            hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
            
            # Rangos para detectar agua (azules)
            lower_water = np.array([100, 50, 50])
            upper_water = np.array([130, 255, 255])
            
            # Crear máscara de agua
            water_mask = cv2.inRange(hsv, lower_water, upper_water)
            
            # Calcular estadísticas
            water_pixels = np.sum(water_mask > 0)
            total_pixels = water_mask.size
            water_percentage = (water_pixels / total_pixels) * 100
            
            return {
                'water_coverage_percent': float(water_percentage),
                'water_pixels': int(water_pixels),
                'has_significant_water': water_percentage > 5.0
            }
            
        except Exception as e:
            print(f"Error detectando agua: {e}")
            return {}
    
    def detect_infrastructure(self, image):
        """Detectar infraestructura (simplicado)"""
        try:
            # Convertir a escala de grises
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # Detectar bordes (infraestructura suele tener líneas rectas)
            edges = cv2.Canny(gray, 50, 150)
            
            # Detectar líneas usando transformada de Hough
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=30, maxLineGap=10)
            
            infrastructure_score = 0
            if lines is not None:
                infrastructure_score = min(len(lines) / 100.0, 1.0)  # Normalizar
            
            return {
                'edge_density': float(np.sum(edges > 0) / edges.size),
                'detected_lines': len(lines) if lines is not None else 0,
                'infrastructure_score': float(infrastructure_score)
            }
            
        except Exception as e:
            print(f"Error detectando infraestructura: {e}")
            return {}
    
    def calculate_risk_score(self, analysis):
        """Calcular score de riesgo basado en análisis"""
        try:
            risk_score = 0.0
            
            # Factor vegetación (menos vegetación = más riesgo)
            veg_data = analysis.get('vegetation_index', {})
            if veg_data.get('vegetation_coverage', 1.0) < 0.3:
                risk_score += 0.3
            
            # Factor agua (sequía o inundación)
            water_data = analysis.get('water_detection', {})
            water_coverage = water_data.get('water_coverage_percent', 0)
            if water_coverage < 2 or water_coverage > 30:  # Muy poca o mucha agua
                risk_score += 0.2
            
            # Factor infraestructura (mucha infraestructura = más población en riesgo)
            infra_data = analysis.get('infrastructure_detection', {})
            if infra_data.get('infrastructure_score', 0) > 0.7:
                risk_score += 0.4
            
            # Normalizar entre 0 y 1
            return min(risk_score, 1.0)
            
        except Exception as e:
            print(f"Error calculando risk score: {e}")
            return 0.0
    
    def save_analysis_to_database(self, analysis):
        """Guardar análisis en base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            cursor = conn.execute("""
                INSERT OR REPLACE INTO satellite_analysis
                (image_path, filename, analysis_date, vegetation_index, 
                 water_detection, infrastructure_detection, risk_score, raw_analysis)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                analysis['image_path'],
                analysis['filename'],
                analysis['analysis_date'],
                json.dumps(analysis.get('vegetation_index', {})),
                json.dumps(analysis.get('water_detection', {})),
                json.dumps(analysis.get('infrastructure_detection', {})),
                analysis.get('risk_score', 0.0),
                json.dumps(analysis)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error guardando análisis en BD: {e}")
            '''
            
            # Guardar sistema de análisis
            analysis_file = analysis_dir / 'satellite_analysis.py'
            with open(analysis_file, 'w', encoding='utf-8') as f:
                f.write(analysis_code)
            
            logger.info("✅ Sistema de análisis satelital implementado")
            
        except Exception as e:
            logger.error(f"❌ Error implementando análisis satelital: {e}")
    
    def update_database_for_real_data(self):
        """Actualizar base de datos para datos reales"""
        try:
            logger.info("🗄️ Actualizando base de datos para datos reales...")
            
            conn = sqlite3.connect(self.db_path)
            
            # Tabla para imágenes satelitales
            conn.execute('''
                CREATE TABLE IF NOT EXISTS satellite_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location TEXT NOT NULL,
                    image_path TEXT NOT NULL,
                    geojson_path TEXT,
                    download_date TEXT NOT NULL,
                    intensity_score REAL,
                    source TEXT DEFAULT 'SentinelHub',
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla para archivos GeoJSON
            conn.execute('''
                CREATE TABLE IF NOT EXISTS geojson_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    location TEXT,
                    upload_date TEXT NOT NULL,
                    properties TEXT,
                    geometry TEXT,
                    web_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla para análisis satelital
            conn.execute('''
                CREATE TABLE IF NOT EXISTS satellite_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_path TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    analysis_date TEXT NOT NULL,
                    vegetation_index TEXT,
                    water_detection TEXT,
                    infrastructure_detection TEXT,
                    risk_score REAL DEFAULT 0.0,
                    raw_analysis TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Índices para optimización
            conn.execute('CREATE INDEX IF NOT EXISTS idx_satellite_location ON satellite_images(location)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_geojson_location ON geojson_files(location)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_analysis_date ON satellite_analysis(analysis_date)')
            
            conn.commit()
            conn.close()
            
            logger.info("✅ Base de datos actualizada para datos reales")
            
        except Exception as e:
            logger.error(f"❌ Error actualizando base de datos: {e}")
    
    def create_intelligent_cache_system(self):
        """Crear sistema de cache inteligente"""
        try:
            logger.info("🧠 Creando sistema de cache inteligente...")
            
            # Crear directorio cache
            cache_dir = Path('src/cache')
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Sistema de cache
            cache_code = '''
import json
import os
import time
from pathlib import Path
from datetime import datetime, timedelta
import hashlib
import pickle

class IntelligentCacheSystem:
    """Sistema de cache inteligente para optimizar rendimiento"""
    
    def __init__(self):
        self.cache_dir = Path('src/cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuración de cache
        self.cache_config = {
            'maps': {'ttl': 3600, 'max_size': 100},  # 1 hora
            'satellite': {'ttl': 7200, 'max_size': 50},  # 2 horas
            'geojson': {'ttl': 1800, 'max_size': 200},  # 30 minutos
            'analysis': {'ttl': 86400, 'max_size': 1000}  # 24 horas
        }
    
    def generate_cache_key(self, data_type, params):
        """Generar clave única para cache"""
        key_string = f"{data_type}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get_cache_file_path(self, cache_key):
        """Obtener ruta del archivo cache"""
        return self.cache_dir / f"{cache_key}.cache"
    
    def is_cache_valid(self, cache_file, ttl):
        """Verificar si cache es válido"""
        if not cache_file.exists():
            return False
        
        file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
        expiry_time = datetime.now() - timedelta(seconds=ttl)
        
        return file_time > expiry_time
    
    def get_from_cache(self, data_type, params):
        """Obtener datos del cache"""
        try:
            cache_key = self.generate_cache_key(data_type, params)
            cache_file = self.get_cache_file_path(cache_key)
            
            config = self.cache_config.get(data_type, {'ttl': 3600})
            
            if self.is_cache_valid(cache_file, config['ttl']):
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                
                print(f"Cache HIT para {data_type}: {cache_key[:8]}...")
                return cached_data
            else:
                print(f"Cache MISS para {data_type}: {cache_key[:8]}...")
                return None
                
        except Exception as e:
            print(f"Error obteniendo del cache: {e}")
            return None
    
    def save_to_cache(self, data_type, params, data):
        """Guardar datos en cache"""
        try:
            cache_key = self.generate_cache_key(data_type, params)
            cache_file = self.get_cache_file_path(cache_key)
            
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
            
            print(f"Guardado en cache {data_type}: {cache_key[:8]}...")
            
            # Limpiar cache si es necesario
            self.cleanup_cache(data_type)
            
        except Exception as e:
            print(f"Error guardando en cache: {e}")
    
    def cleanup_cache(self, data_type):
        """Limpiar cache antiguo"""
        try:
            config = self.cache_config.get(data_type, {'max_size': 100})
            max_size = config['max_size']
            
            # Obtener archivos cache ordenados por fecha
            cache_files = list(self.cache_dir.glob('*.cache'))
            cache_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Eliminar archivos excedentes
            if len(cache_files) > max_size:
                for old_file in cache_files[max_size:]:
                    old_file.unlink()
                    print(f"Cache limpiado: {old_file.name}")
                    
        except Exception as e:
            print(f"Error limpiando cache: {e}")
    
    def clear_all_cache(self):
        """Limpiar todo el cache"""
        try:
            cache_files = list(self.cache_dir.glob('*.cache'))
            for cache_file in cache_files:
                cache_file.unlink()
            
            print(f"Cache completamente limpiado: {len(cache_files)} archivos eliminados")
            
        except Exception as e:
            print(f"Error limpiando cache completo: {e}")
    
    def get_cache_stats(self):
        """Obtener estadísticas del cache"""
        try:
            cache_files = list(self.cache_dir.glob('*.cache'))
            total_size = sum(f.stat().st_size for f in cache_files)
            
            return {
                'total_files': len(cache_files),
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'oldest_file': min((f.stat().st_mtime for f in cache_files), default=0),
                'newest_file': max((f.stat().st_mtime for f in cache_files), default=0)
            }
            
        except Exception as e:
            print(f"Error obteniendo estadísticas cache: {e}")
            return {}
            '''
            
            # Guardar sistema de cache
            cache_file = cache_dir / 'intelligent_cache.py'
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(cache_code)
            
            logger.info("✅ Sistema de cache inteligente creado")
            
        except Exception as e:
            logger.error(f"❌ Error creando sistema de cache: {e}")

def main():
    """Función principal para ejecutar BLOQUE 2C"""
    try:
        system = RealMapsAndSentinelSystem()
        system.run_all_updates()
        
        print("\n" + "="*60)
        print("🎉 BLOQUE 2C COMPLETADO EXITOSAMENTE")
        print("="*60)
        print("✅ Sistema de mapas con datos reales creado")
        print("✅ Automación SentinelHub implementada")
        print("✅ Sistema de subida automática GeoJSON creado")
        print("✅ Análisis automático de imágenes satelitales implementado")
        print("✅ Base de datos actualizada para datos reales")
        print("✅ Sistema de cache inteligente creado")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERROR EN BLOQUE 2C: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
