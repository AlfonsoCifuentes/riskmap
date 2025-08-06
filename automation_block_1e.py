#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatización del Dashboard - BLOQUE 1E
Implementación del mapa de calor interactivo
"""

import sys
import os
import re
import logging
from pathlib import Path
from datetime import datetime

# Configurar codificación UTF-8 para Windows
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configurar logging sin emojis
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HeatmapImplementation:
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.app_file = self.project_root / "app_BUENA.py"
        self.templates_dir = self.project_root / "src" / "web" / "templates"
        self.static_dir = self.project_root / "src" / "web" / "static"
        
    def implement_heatmap_system(self):
        """Implementar sistema completo de mapa de calor"""
        logger.info("IMPLEMENTANDO MAPA DE CALOR INTERACTIVO...")
        
        try:
            # 1. Agregar rutas para el mapa de calor
            success_routes = self._add_heatmap_routes()
            
            # 2. Agregar métodos de procesamiento de datos geográficos
            success_methods = self._add_heatmap_methods()
            
            # 3. Agregar API para datos del mapa de calor
            success_api = self._add_heatmap_api()
            
            if all([success_routes, success_methods, success_api]):
                logger.info("MAPA DE CALOR IMPLEMENTADO COMPLETAMENTE")
                return True
            else:
                logger.error("FALLOS EN IMPLEMENTACIÓN DE MAPA DE CALOR")
                return False
                
        except Exception as e:
            logger.error(f"Error implementando mapa de calor: {e}")
            return False
    
    def _add_heatmap_routes(self):
        """Agregar rutas para el mapa de calor"""
        try:
            if not self.app_file.exists():
                logger.error("app_BUENA.py no encontrado")
                return False
            
            with open(self.app_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificar si las rutas ya existen
            if '/mapa-calor' in content:
                logger.info("Rutas de mapa de calor ya existen")
                return True
            
            heatmap_routes = '''
# === RUTAS PARA MAPA DE CALOR ===
@app.route('/mapa-calor')
def mapa_calor():
    """Página del mapa de calor interactivo"""
    try:
        # Obtener datos iniciales para el mapa
        heatmap_data = get_heatmap_initial_data()
        
        return render_template('mapa_calor.html', 
                             heatmap_data=heatmap_data,
                             page_title="Mapa de Calor - RiskMap")
    except Exception as e:
        logger.error(f"Error en mapa de calor: {e}")
        return render_template('error.html', error="Error cargando mapa de calor")

@app.route('/heatmap')
def heatmap():
    """Redirigir al mapa de calor"""
    return redirect(url_for('mapa_calor'))
'''
            
            # Insertar rutas antes del final del archivo
            content += heatmap_routes
            
            with open(self.app_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info("RUTAS DE MAPA DE CALOR AGREGADAS")
            return True
            
        except Exception as e:
            logger.error(f"Error agregando rutas de mapa de calor: {e}")
            return False
    
    def _add_heatmap_methods(self):
        """Agregar métodos para procesamiento de datos del mapa de calor"""
        try:
            with open(self.app_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'get_heatmap_initial_data' in content:
                logger.info("Métodos de mapa de calor ya existen")
                return True
            
            heatmap_methods = '''
# === MÉTODOS PARA MAPA DE CALOR ===
def get_heatmap_initial_data():
    """Obtener datos iniciales para el mapa de calor"""
    try:
        # Obtener puntos de calor básicos
        heatmap_points = get_heatmap_points()
        geographic_stats = get_geographic_statistics()
        risk_zones = get_risk_zones()
        
        return {
            'heatmap_points': heatmap_points,
            'geographic_stats': geographic_stats,
            'risk_zones': risk_zones,
            'total_points': len(heatmap_points),
            'last_updated': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo datos iniciales de mapa de calor: {e}")
        return {}

def get_heatmap_points(days_back=30, min_risk=0.0):
    """Obtener puntos para el mapa de calor"""
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data', 'riskmap.db'))
        cursor = conn.cursor()
        
        # Obtener artículos con coordenadas válidas
        cursor.execute("""
            SELECT 
                latitude, longitude, location, risk_level, 
                title, processed_date, source, url
            FROM enhanced_articles 
            WHERE latitude IS NOT NULL 
            AND longitude IS NOT NULL
            AND latitude != '' 
            AND longitude != ''
            AND CAST(risk_level AS FLOAT) >= ?
            AND processed_date >= DATE('now', '-{} days')
            ORDER BY processed_date DESC
        """.format(days_back), (min_risk,))
        
        heatmap_points = []
        for row in cursor.fetchall():
            try:
                lat = float(row[0])
                lng = float(row[1])
                risk = float(row[3]) if row[3] else 0.0
                
                # Validar coordenadas
                if -90 <= lat <= 90 and -180 <= lng <= 180:
                    point = {
                        'lat': lat,
                        'lng': lng,
                        'location': row[2] or 'Ubicación desconocida',
                        'risk_level': risk,
                        'title': row[4] or 'Sin título',
                        'processed_date': row[5],
                        'source': row[6] or 'Fuente desconocida',
                        'url': row[7],
                        'intensity': min(risk / 10.0, 1.0),  # Normalizar para mapa de calor
                        'color': get_risk_color(risk)
                    }
                    heatmap_points.append(point)
                    
            except (ValueError, TypeError) as e:
                logger.warning(f"Coordenadas inválidas: {row[0]}, {row[1]} - {e}")
                continue
        
        conn.close()
        
        logger.info(f"Obtenidos {len(heatmap_points)} puntos para mapa de calor")
        return heatmap_points
        
    except Exception as e:
        logger.error(f"Error obteniendo puntos de mapa de calor: {e}")
        return []

def get_geographic_statistics():
    """Obtener estadísticas geográficas para el mapa"""
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data', 'riskmap.db'))
        cursor = conn.cursor()
        
        # Estadísticas por ubicación
        cursor.execute("""
            SELECT 
                location,
                COUNT(*) as article_count,
                AVG(CAST(risk_level AS FLOAT)) as avg_risk,
                MAX(CAST(risk_level AS FLOAT)) as max_risk,
                MIN(CAST(risk_level AS FLOAT)) as min_risk
            FROM enhanced_articles 
            WHERE location IS NOT NULL 
            AND risk_level IS NOT NULL
            AND latitude IS NOT NULL 
            AND longitude IS NOT NULL
            GROUP BY location
            HAVING COUNT(*) >= 2
            ORDER BY avg_risk DESC, article_count DESC
            LIMIT 20
        """)
        
        location_stats = []
        for row in cursor.fetchall():
            stat = {
                'location': row[0],
                'article_count': row[1],
                'average_risk': round(row[2], 2),
                'max_risk': round(row[3], 2),
                'min_risk': round(row[4], 2),
                'risk_category': get_risk_category(row[2])
            }
            location_stats.append(stat)
        
        # Estadísticas generales
        cursor.execute("""
            SELECT 
                COUNT(*) as total_geolocated,
                AVG(CAST(risk_level AS FLOAT)) as global_avg_risk,
                COUNT(DISTINCT location) as unique_locations
            FROM enhanced_articles 
            WHERE latitude IS NOT NULL 
            AND longitude IS NOT NULL
            AND risk_level IS NOT NULL
        """)
        
        general_stats = cursor.fetchone()
        
        conn.close()
        
        return {
            'location_stats': location_stats,
            'total_geolocated_articles': general_stats[0] if general_stats else 0,
            'global_average_risk': round(general_stats[1], 2) if general_stats[1] else 0.0,
            'unique_locations': general_stats[2] if general_stats else 0
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas geográficas: {e}")
        return {}

def get_risk_zones():
    """Obtener zonas de riesgo definidas"""
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data', 'riskmap.db'))
        cursor = conn.cursor()
        
        # Agrupar por coordenadas aproximadas para crear zonas
        cursor.execute("""
            SELECT 
                ROUND(CAST(latitude AS FLOAT), 1) as lat_zone,
                ROUND(CAST(longitude AS FLOAT), 1) as lng_zone,
                COUNT(*) as article_count,
                AVG(CAST(risk_level AS FLOAT)) as avg_risk,
                MAX(CAST(risk_level AS FLOAT)) as max_risk
            FROM enhanced_articles 
            WHERE latitude IS NOT NULL 
            AND longitude IS NOT NULL
            AND risk_level IS NOT NULL
            GROUP BY lat_zone, lng_zone
            HAVING COUNT(*) >= 3
            ORDER BY avg_risk DESC
            LIMIT 50
        """)
        
        risk_zones = []
        for row in cursor.fetchall():
            zone = {
                'center_lat': row[0],
                'center_lng': row[1],
                'article_count': row[2],
                'average_risk': round(row[3], 2),
                'max_risk': round(row[4], 2),
                'risk_category': get_risk_category(row[3]),
                'zone_radius': calculate_zone_radius(row[2]),  # Radio basado en cantidad
                'zone_color': get_risk_color(row[3])
            }
            risk_zones.append(zone)
        
        conn.close()
        
        return risk_zones
        
    except Exception as e:
        logger.error(f"Error obteniendo zonas de riesgo: {e}")
        return []

def get_risk_color(risk_level):
    """Obtener color basado en nivel de riesgo"""
    try:
        risk = float(risk_level)
        if risk >= 8.0:
            return '#FF0000'  # Rojo - Crítico
        elif risk >= 6.0:
            return '#FF6600'  # Naranja - Alto
        elif risk >= 4.0:
            return '#FFCC00'  # Amarillo - Medio
        elif risk >= 2.0:
            return '#99FF00'  # Verde claro - Bajo
        else:
            return '#00FF00'  # Verde - Muy bajo
    except (ValueError, TypeError):
        return '#808080'  # Gris - Desconocido

def get_risk_category(risk_level):
    """Obtener categoría de riesgo"""
    try:
        risk = float(risk_level)
        if risk >= 8.0:
            return 'Crítico'
        elif risk >= 6.0:
            return 'Alto'
        elif risk >= 4.0:
            return 'Medio'
        elif risk >= 2.0:
            return 'Bajo'
        else:
            return 'Muy bajo'
    except (ValueError, TypeError):
        return 'Desconocido'

def calculate_zone_radius(article_count):
    """Calcular radio de zona basado en cantidad de artículos"""
    # Radio base de 5000 metros, escalado por cantidad
    base_radius = 5000
    scale_factor = min(article_count / 10.0, 3.0)  # Máximo 3x el radio base
    return int(base_radius * (1 + scale_factor))

def get_heatmap_data_filtered(risk_min=0.0, risk_max=10.0, days_back=30, location_filter=None):
    """Obtener datos de mapa de calor con filtros"""
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data', 'riskmap.db'))
        cursor = conn.cursor()
        
        # Construir consulta con filtros
        where_conditions = [
            "latitude IS NOT NULL",
            "longitude IS NOT NULL",
            "latitude != ''",
            "longitude != ''",
            "CAST(risk_level AS FLOAT) >= ?",
            "CAST(risk_level AS FLOAT) <= ?",
            "processed_date >= DATE('now', '-{} days')".format(days_back)
        ]
        
        params = [risk_min, risk_max]
        
        if location_filter:
            where_conditions.append("location LIKE ?")
            params.append(f"%{location_filter}%")
        
        query = f"""
            SELECT latitude, longitude, location, risk_level, title, processed_date
            FROM enhanced_articles 
            WHERE {' AND '.join(where_conditions)}
            ORDER BY processed_date DESC
            LIMIT 1000
        """
        
        cursor.execute(query, params)
        
        filtered_points = []
        for row in cursor.fetchall():
            try:
                lat = float(row[0])
                lng = float(row[1])
                risk = float(row[3])
                
                if -90 <= lat <= 90 and -180 <= lng <= 180:
                    point = {
                        'lat': lat,
                        'lng': lng,
                        'location': row[2],
                        'risk_level': risk,
                        'title': row[4],
                        'processed_date': row[5],
                        'intensity': min(risk / 10.0, 1.0),
                        'color': get_risk_color(risk)
                    }
                    filtered_points.append(point)
                    
            except (ValueError, TypeError):
                continue
        
        conn.close()
        
        return filtered_points
        
    except Exception as e:
        logger.error(f"Error obteniendo datos filtrados: {e}")
        return []
'''
            
            content += heatmap_methods
            
            with open(self.app_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info("MÉTODOS DE MAPA DE CALOR AGREGADOS")
            return True
            
        except Exception as e:
            logger.error(f"Error agregando métodos de mapa de calor: {e}")
            return False
    
    def _add_heatmap_api(self):
        """Agregar API endpoints para el mapa de calor"""
        try:
            with open(self.app_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if '/api/heatmap/data' in content:
                logger.info("API de mapa de calor ya existe")
                return True
            
            heatmap_api = '''
# === API ENDPOINTS PARA MAPA DE CALOR ===
@app.route('/api/heatmap/data')
def api_heatmap_data():
    """API para obtener datos del mapa de calor"""
    try:
        # Obtener parámetros de filtro
        risk_min = float(request.args.get('risk_min', 0.0))
        risk_max = float(request.args.get('risk_max', 10.0))
        days_back = int(request.args.get('days_back', 30))
        location_filter = request.args.get('location')
        
        # Obtener datos filtrados
        heatmap_points = get_heatmap_data_filtered(risk_min, risk_max, days_back, location_filter)
        
        return jsonify({
            'success': True,
            'heatmap_points': heatmap_points,
            'total_points': len(heatmap_points),
            'filters_applied': {
                'risk_min': risk_min,
                'risk_max': risk_max,
                'days_back': days_back,
                'location_filter': location_filter
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en API heatmap data: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/heatmap/zones')
def api_heatmap_zones():
    """API para obtener zonas de riesgo"""
    try:
        risk_zones = get_risk_zones()
        
        return jsonify({
            'success': True,
            'risk_zones': risk_zones,
            'total_zones': len(risk_zones),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en API heatmap zones: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/heatmap/statistics')
def api_heatmap_statistics():
    """API para obtener estadísticas geográficas"""
    try:
        geographic_stats = get_geographic_statistics()
        
        return jsonify({
            'success': True,
            'statistics': geographic_stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en API heatmap statistics: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/heatmap/refresh', methods=['POST'])
def api_heatmap_refresh():
    """API para refrescar datos del mapa de calor"""
    try:
        # Regenerar datos del mapa
        heatmap_data = get_heatmap_initial_data()
        
        return jsonify({
            'success': True,
            'message': 'Mapa de calor actualizado',
            'data': heatmap_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error refrescando mapa de calor: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/heatmap/export')
def api_heatmap_export():
    """API para exportar datos del mapa de calor"""
    try:
        format_type = request.args.get('format', 'geojson')
        
        if format_type == 'geojson':
            # Exportar como GeoJSON
            heatmap_points = get_heatmap_points()
            geojson_data = convert_to_geojson(heatmap_points)
            
            response = make_response(jsonify(geojson_data))
            response.headers['Content-Type'] = 'application/geo+json'
            response.headers['Content-Disposition'] = 'attachment; filename=heatmap_data.geojson'
            
            return response
            
        elif format_type == 'csv':
            # Exportar como CSV
            import csv
            import io
            
            heatmap_points = get_heatmap_points()
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Escribir encabezados
            writer.writerow(['latitude', 'longitude', 'location', 'risk_level', 'title', 'processed_date'])
            
            # Escribir datos
            for point in heatmap_points:
                writer.writerow([
                    point['lat'], point['lng'], point['location'], 
                    point['risk_level'], point['title'], point['processed_date']
                ])
            
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = 'attachment; filename=heatmap_data.csv'
            
            return response
            
        else:
            return jsonify({'success': False, 'error': 'Formato no soportado'})
            
    except Exception as e:
        logger.error(f"Error exportando mapa de calor: {e}")
        return jsonify({'success': False, 'error': str(e)})

def convert_to_geojson(heatmap_points):
    """Convertir puntos a formato GeoJSON"""
    try:
        features = []
        
        for point in heatmap_points:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [point['lng'], point['lat']]
                },
                "properties": {
                    "location": point['location'],
                    "risk_level": point['risk_level'],
                    "title": point['title'],
                    "processed_date": point['processed_date'],
                    "intensity": point['intensity'],
                    "color": point['color']
                }
            }
            features.append(feature)
        
        geojson = {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {
                "total_points": len(features),
                "generated_at": datetime.now().isoformat(),
                "source": "RiskMap Heatmap Data"
            }
        }
        
        return geojson
        
    except Exception as e:
        logger.error(f"Error convirtiendo a GeoJSON: {e}")
        return {"type": "FeatureCollection", "features": []}
'''
            
            content += heatmap_api
            
            with open(self.app_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info("API DE MAPA DE CALOR AGREGADA")
            return True
            
        except Exception as e:
            logger.error(f"Error agregando API de mapa de calor: {e}")
            return False

if __name__ == "__main__":
    project_root = Path(__file__).parent.absolute()
    heatmap_implementation = HeatmapImplementation(project_root)
    
    print("\n" + "="*50)
    print("BLOQUE 1E: IMPLEMENTACIÓN MAPA DE CALOR INTERACTIVO")
    print("="*50)
    
    success = heatmap_implementation.implement_heatmap_system()
    
    if success:
        logger.info("BLOQUE 1E COMPLETADO EXITOSAMENTE")
        print("\nBLOQUE 1E COMPLETADO EXITOSAMENTE!")
        print("- Mapa de calor interactivo implementado")
        print("- Procesamiento de datos geográficos configurado")
        print("- Zonas de riesgo definidas")
        print("- API de exportación creada")
        print("- Filtros avanzados implementados")
    else:
        logger.error("BLOQUE 1E FALLÓ")
        print("\nBLOQUE 1E FALLÓ - Revisar logs")
    
    sys.exit(0 if success else 1)
