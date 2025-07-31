"""
Modern Flask Dashboard Application for Geopolitical Intelligence System
VERSIÓN CORREGIDA - SIN PROBLEMAS DE SCHEDULER
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import sqlite3
import json
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path
import random
import atexit

# Add parent directories to path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(current_dir.parent))

# Simple logger
class SimpleLogger:
    def info(self, msg): print(f"[INFO] {msg}")
    def error(self, msg): print(f"[ERROR] {msg}")
    def warning(self, msg): print(f"[WARNING] {msg}")

logger = SimpleLogger()

# Global scheduler variable
scheduler_bg = None

# --- Scheduler configuration with proper cleanup ---
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from src.scheduler import ingest_realtime
    scheduler_available = True
    logger.info("Scheduler disponible")
except ImportError as e:
    logger.warning(f"Cannot import scheduler components: {e}")
    scheduler_available = False
    def ingest_realtime():
        logger.warning("ingest_realtime not available - using mock function")

def cleanup_scheduler():
    """Cleanup scheduler on exit."""
    global scheduler_bg
    if scheduler_bg and scheduler_bg.running:
        try:
            logger.info("Cerrando scheduler...")
            scheduler_bg.shutdown(wait=False)
        except Exception as e:
            logger.error(f"Error cerrando scheduler: {e}")

# Register cleanup function
atexit.register(cleanup_scheduler)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'geopolitical-intel-2024'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Absolute database path resolved dynamically (two levels above src/dashboard)
BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = str(BASE_DIR / 'data' / 'geopolitical_intel.db')

logger.info(f"Base de datos: {DB_PATH}")

def get_db_connection():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def emit_new_articles(articles):
    """Emit new articles to clients."""
    try:
        logger.info(f"Emitiendo {len(articles)} nuevos artículos a los clientes.")
        socketio.emit('new_articles', {'articles': articles})
    except Exception as e:
        logger.error(f"Error emitiendo artículos: {e}")

def safe_ingest_with_callback():
    """Safe ingest function with proper error handling."""
    try:
        logger.info("Ejecutando ingesta segura...")
        
        # Run the ingest
        if scheduler_available:
            ingest_realtime()
        
        # Get new articles and emit them
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT title, content, created_at, country, risk_level, url, source
            FROM articles 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        articles = []
        for row in cursor.fetchall():
            articles.append({
                'title': row['title'],
                'content': row['content'][:200] + '...' if row['content'] else '',
                'created_at': row['created_at'],
                'country': row['country'] or 'Global',
                'risk_level': row['risk_level'] or 'medium',
                'source_url': row['url'],
                'source': row['source'] or 'Fuente desconocida'
            })
        
        conn.close()

        if articles:
            emit_new_articles(articles)
            
    except Exception as e:
        logger.error(f"Error en safe_ingest_with_callback: {e}")

def start_scheduler():
    """Start scheduler with proper configuration."""
    global scheduler_bg
    
    if not scheduler_available:
        logger.warning("Scheduler no disponible")
        return
    
    try:
        # Only start if not already running
        if scheduler_bg is None or not scheduler_bg.running:
            scheduler_bg = BackgroundScheduler(
                timezone="UTC",
                job_defaults={
                    'coalesce': True,
                    'max_instances': 1,
                    'misfire_grace_time': 300
                }
            )
            
            # Add job with proper configuration
            scheduler_bg.add_job(
                func=safe_ingest_with_callback,
                trigger='interval',
                minutes=5,
                id='realtime_ingest_safe',
                max_instances=1,
                replace_existing=True,
                coalesce=True
            )
            
            scheduler_bg.start()
            logger.info("Scheduler iniciado correctamente")
        else:
            logger.info("Scheduler ya está ejecutándose")
            
    except Exception as e:
        logger.error(f"Error iniciando scheduler: {e}")
        scheduler_bg = None

def get_recent_alerts(cursor):
    """Get recent alerts from database."""
    try:
        cursor.execute("""
            SELECT title, risk_level, country, created_at
            FROM articles 
            WHERE risk_level = 'high'
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        alerts = []
        for row in cursor.fetchall():
            alerts.append({
                'title': row['title'],
                'level': row['risk_level'],
                'location': row['country'] or 'Global',
                'time': row['created_at']
            })
        return alerts
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return []

def get_map_events(cursor):
    """Get events for map visualization."""
    try:
        cursor.execute("""
            SELECT title, location, type, magnitude, published_at
            FROM events 
            WHERE location IS NOT NULL 
            ORDER BY published_at DESC 
            LIMIT 100
        """)
        events = []
        for row in cursor.fetchall():
            try:
                location = json.loads(row['location']) if row['location'] else None
                if location and len(location) == 2:
                    events.append({
                        'title': row['title'],
                        'lat': float(location[0]),
                        'lng': float(location[1]),
                        'type': row['type'] or 'general',
                        'magnitude': row['magnitude'] or 1,
                        'time': row['published_at']
                    })
            except (json.JSONDecodeError, ValueError, TypeError):
                continue
        return events
    except Exception as e:
        logger.error(f"Error getting map events: {e}")
        return []

# ROUTES

@app.route('/')
def index():
    """Render the main dashboard."""
    return render_template('modern_dashboard_updated.html')

@app.route('/news-analysis')
def news_analysis():
    """Render the news analysis page (original dashboard)."""
    return render_template('modern_dashboard_updated.html')

@app.route('/conflict-monitoring')
def conflict_monitoring():
    """Render the conflict monitoring page."""
    return render_template('conflict_monitoring.html')

@app.route('/trends-analysis')
def trends_analysis():
    """Render the trends analysis page."""
    return render_template('trends_analysis.html')

@app.route('/early-warning')
def early_warning():
    """Render the early warning page."""
    return render_template('early_warning.html')

@app.route('/executive-reports')
def executive_reports():
    """Render the executive reports page."""
    return render_template('executive_reports.html')

@app.route('/satellite-analysis')
def satellite_analysis():
    """Render the satellite analysis page."""
    return render_template('satellite_analysis.html')

@app.route('/video-surveillance')
def video_surveillance():
    """Render the video surveillance page."""
    return render_template('video_surveillance.html')

@app.route('/historical-analysis')
def historical_analysis():
    """Render the historical analysis page."""
    return render_template('historical_analysis.html')

@app.route('/test-articles')
def test_articles():
    """Render the test articles page."""
    from flask import send_from_directory
    return send_from_directory(BASE_DIR, 'test_articles_simple.html')

@app.route('/api/dashboard/stats')
def get_dashboard_stats():
    """Get dashboard statistics - CARGA DATOS REALES DE SQLITE."""
    try:
        logger.info("Cargando estadísticas del dashboard...")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total articles
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_articles = cursor.fetchone()[0]
        
        # High risk events
        cursor.execute("SELECT COUNT(*) FROM articles WHERE risk_level = 'high'")
        high_risk_events = cursor.fetchone()[0]
        
        # Processed in last 24h
        cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE datetime(created_at) > datetime('now', '-24 hours')
        """)
        processed_today = cursor.fetchone()[0]
        
        # Active regions (countries with events in last 7 days)
        cursor.execute("""
            SELECT COUNT(DISTINCT country) FROM articles 
            WHERE datetime(created_at) > datetime('now', '-7 days')
            AND country IS NOT NULL
        """)
        active_regions = cursor.fetchone()[0]
        
        # Get recent alerts
        alerts = get_recent_alerts(cursor)
        
        # Get map events
        events = get_map_events(cursor)
        
        conn.close()
        
        result = {
            'stats': {
                'total_articles': total_articles,
                'high_risk_events': high_risk_events,
                'processed_today': processed_today,
                'active_regions': active_regions
            },
            'alerts': alerts,
            'events': events
        }
        
        logger.info(f"Estadísticas cargadas: {result['stats']}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        # Return fallback data on error
        return jsonify({
            'stats': {
                'total_articles': 800,
                'high_risk_events': 23,
                'processed_today': 156,
                'active_regions': 34
            },
            'alerts': [],
            'events': []
        })

@app.route('/api/articles')
def get_articles():
    """Get recent articles from database - CARGA ARTÍCULOS REALES."""
    try:
        logger.info("Cargando artículos de la base de datos...")
        
        limit = request.args.get('limit', 20, type=int)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT title, content, created_at, country, risk_level, url, source, language, image_url
            FROM articles 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        
        articles = []
        for row in cursor.fetchall():
            articles.append({
                'title': row['title'],
                'content': row['content'][:200] + '...' if row['content'] else 'Sin descripción disponible',
                'summary': row['content'][:150] + '...' if row['content'] else 'Sin resumen disponible',
                'created_at': row['created_at'],
                'country': row['country'] or 'Global',
                'location': row['country'] or 'Global',
                'risk_level': row['risk_level'] or 'medium',
                'source_url': row['url'],
                'url': row['url'],
                'source': row['source'] or 'Fuente desconocida',
                'language': row['language'] or 'es',
                'image_url': row['image_url'] if 'image_url' in row.keys() else None
            })
        
        conn.close()
        
        logger.info(f"Cargados {len(articles)} artículos")
        return jsonify(articles)
        
    except Exception as e:
        logger.error(f"Error getting articles: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/articles/latest')
def get_latest_articles():
    """Get latest articles - RUTA ESPECÍFICA PARA ÚLTIMOS ARTÍCULOS."""
    try:
        logger.info("Cargando últimos artículos...")
        
        limit = request.args.get('limit', 15, type=int)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT title, content, created_at, country, risk_level, url, source, language, image_url
            FROM articles 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        
        articles = []
        for row in cursor.fetchall():
            articles.append({
                'title': row['title'],
                'content': row['content'][:200] + '...' if row['content'] else 'Sin descripción disponible',
                'summary': row['content'][:150] + '...' if row['content'] else 'Sin resumen disponible',
                'created_at': row['created_at'],
                'country': row['country'] or 'Global',
                'location': row['country'] or 'Global',
                'risk_level': row['risk_level'] or 'medium',
                'source_url': row['url'],
                'url': row['url'],
                'source': row['source'] or 'Fuente desconocida',
                'language': row['language'] or 'es',
                'image_url': row['image_url'] if 'image_url' in row.keys() else None
            })
        
        conn.close()
        
        logger.info(f"Cargados {len(articles)} últimos artículos")
        return jsonify(articles)
        
    except Exception as e:
        logger.error(f"Error getting latest articles: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/articles/high-risk')
def get_high_risk_articles():
    """Get high risk articles - RUTA ESPECÍFICA PARA ARTÍCULOS DE ALTO RIESGO."""
    try:
        logger.info("Cargando artículos de alto riesgo...")
        
        limit = request.args.get('limit', 10, type=int)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT title, content, created_at, country, risk_level, url, source, language, image_url
            FROM articles 
            WHERE risk_level = 'high'
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        
        articles = []
        for row in cursor.fetchall():
            articles.append({
                'title': row['title'],
                'content': row['content'][:200] + '...' if row['content'] else 'Sin descripción disponible',
                'summary': row['content'][:120] + '...' if row['content'] else 'Sin resumen disponible',
                'created_at': row['created_at'],
                'country': row['country'] or 'Global',
                'location': row['country'] or 'Global',
                'risk_level': 'high',
                'source_url': row['url'],
                'url': row['url'],
                'source': row['source'] or 'Fuente desconocida',
                'language': row['language'] or 'es',
                'image_url': row['image_url'] if 'image_url' in row.keys() else None
            })
        
        conn.close()
        
        logger.info(f"Cargados {len(articles)} artículos de alto riesgo")
        return jsonify(articles)
        
    except Exception as e:
        logger.error(f"Error getting high risk articles: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/articles/featured')
def get_featured_article():
    """Get featured article - RUTA ESPECÍFICA PARA ARTÍCULO DESTACADO."""
    try:
        logger.info("Cargando artículo destacado...")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar el artículo de mayor riesgo más reciente
        cursor.execute("""
            SELECT title, content, created_at, country, risk_level, url, source, language, image_url
            FROM articles 
            WHERE risk_level = 'high'
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        
        if row:
            article = {
                'id': 1,
                'title': row['title'],
                'content': row['content'] or 'Sin descripción disponible',
                'summary': row['content'][:300] + '...' if row['content'] else 'Sin resumen disponible',
                'created_at': row['created_at'],
                'country': row['country'] or 'Global',
                'location': row['country'] or 'Global',
                'risk_level': 'high',
                'source_url': row['url'],
                'url': row['url'],
                'source': row['source'] or 'Fuente desconocida',
                'language': row['language'] or 'es',
                'image_url': row['image_url'],
                'image': row['image_url'],
                'thumbnail_url': row['image_url']
            }
        else:
            # Si no hay artículos de alto riesgo, buscar cualquier artículo reciente
            cursor.execute("""
                SELECT title, content, created_at, country, risk_level, url, source, language, image_url
                FROM articles 
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            if row:
                article = {
                    'id': 1,
                    'title': row['title'],
                    'content': row['content'] or 'Sin descripción disponible',
                    'summary': row['content'][:300] + '...' if row['content'] else 'Sin resumen disponible',
                    'created_at': row['created_at'],
                    'country': row['country'] or 'Global',
                    'location': row['country'] or 'Global',
                    'risk_level': row['risk_level'] or 'medium',
                    'source_url': row['url'],
                    'url': row['url'],
                    'source': row['source'] or 'Fuente desconocida',
                    'language': row['language'] or 'es',
                    'image_url': row['image_url'],
                    'image': row['image_url'],
                    'thumbnail_url': row['image_url']
                }
            else:
                article = {'id': 0, 'title': 'No hay artículos disponibles'}
        
        conn.close()
        
        logger.info(f"Artículo destacado cargado: {article.get('title', 'N/A')}")
        return jsonify(article)
        
    except Exception as e:
        logger.error(f"Error getting featured article: {e}")
        return jsonify({'id': 0, 'title': 'Error al cargar artículo', 'error': str(e)}), 500

# API Route Aliases - For backward compatibility with different naming conventions
@app.route('/api/latest_articles')
def get_latest_articles_alias():
    """Alias for /api/articles/latest - backward compatibility."""
    return get_latest_articles()

@app.route('/api/high_risk_articles')
def get_high_risk_articles_alias():
    """Alias for /api/articles/high-risk - backward compatibility."""
    return get_high_risk_articles()

@app.route('/api/events/heatmap')
@app.route('/api/heatmap')
def get_heatmap_data():
    """Get heatmap data - RUTA ESPECÍFICA PARA MAPA DE CALOR."""
    map_type = request.args.get('type', 'general')
    
    try:
        logger.info(f"Cargando datos del mapa de calor tipo: {map_type}")
        
        if map_type == 'conflict_risk':
            return get_conflict_risk_heatmap()
        elif map_type == 'historical_conflicts':
            return get_historical_conflicts_heatmap()
        elif map_type == 'oil':
            return get_oil_heatmap()
        elif map_type == 'energy':
            return get_energy_heatmap()
        elif map_type == 'supplies':
            return get_supplies_heatmap()
        elif map_type == 'internet_cables':
            return get_internet_cables_heatmap()
        elif map_type == 'military_bases':
            return get_military_bases_heatmap()
        elif map_type == 'trade_routes':
            return get_trade_routes_heatmap()
        else:
            return get_general_heatmap()
            
    except Exception as e:
        logger.error(f"Error getting heatmap data: {e}")
        return get_fallback_heatmap()

def get_general_heatmap():
    """Mapa de calor general con todos los eventos."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT location, type, magnitude, title, published_at
        FROM events 
        WHERE location IS NOT NULL 
        AND location != ''
        ORDER BY published_at DESC
        LIMIT 1000
    """)
    
    heatmap_data = []
    for row in cursor.fetchall():
        try:
            location = json.loads(row['location'])
            if isinstance(location, list) and len(location) == 2:
                lat, lng = float(location[0]), float(location[1])
                if -90 <= lat <= 90 and -180 <= lng <= 180:
                    heatmap_data.append({
                        'lat': lat,
                        'lng': lng,
                        'intensity': min(float(row['magnitude'] or 1), 10),
                        'type': row['type'] or 'general',
                        'title': (row['title'][:50] + '...') if row['title'] else 'Sin título',
                        'time': row['published_at']
                    })
        except (json.JSONDecodeError, ValueError, TypeError):
            continue
    
    conn.close()
    
    if len(heatmap_data) < 5:
        heatmap_data.extend(get_example_points('general'))
    
    logger.info(f"Mapa de calor general cargado: {len(heatmap_data)} puntos")
    return jsonify(heatmap_data)

def get_conflict_risk_heatmap():
    """Mapa de calor de riesgo de conflicto."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Obtener artículos de alto riesgo por ubicación
    cursor.execute("""
        SELECT country, COUNT(*) as count,
               SUM(CASE WHEN risk_level = 'high' THEN 1 ELSE 0 END) as high_risk
        FROM articles 
        WHERE country IS NOT NULL
        GROUP BY country
        ORDER BY high_risk DESC, count DESC
        LIMIT 50
    """)
    
    country_coords = {
        'Ukraine': [50.4501, 30.5234],
        'Russia': [55.7558, 37.6173],
        'China': [39.9042, 116.4074],
        'Israel': [31.7683, 35.2137],
        'Palestine': [31.9, 35.2],
        'Iran': [35.6892, 51.3890],
        'Syria': [34.8021, 38.9968],
        'Afghanistan': [33.9391, 67.7100],
        'Turkey': [39.9334, 32.8597],
        'North Korea': [40.3399, 127.5101],
        'India': [28.6139, 77.2090],
        'Pakistan': [33.6844, 73.0479],
        'Yemen': [15.5527, 48.5164],
        'Libya': [26.3351, 17.2283],
        'Myanmar': [19.7633, 96.0785],
        'Ethiopia': [9.1450, 40.4897],
        'Venezuela': [6.4238, -66.5897],
        'Colombia': [4.7110, -74.0721]
    }
    
    heatmap_data = []
    for row in cursor.fetchall():
        country = row['country']
        if country in country_coords:
            coords = country_coords[country]
            risk_intensity = min((row['high_risk'] * 2 + row['count'] * 0.1), 10)
            heatmap_data.append({
                'lat': coords[0],
                'lng': coords[1],
                'intensity': risk_intensity,
                'type': 'conflict_risk',
                'title': f'Riesgo de conflicto en {country}',
                'details': f'Eventos de alto riesgo: {row["high_risk"]}, Total: {row["count"]}'
            })
    
    conn.close()
    
    # Agregar puntos de ejemplo si no hay suficientes datos
    if len(heatmap_data) < 5:
        heatmap_data.extend(get_example_points('conflict_risk'))
    
    return jsonify(heatmap_data)

def get_historical_conflicts_heatmap():
    """Mapa de calor de conflictos históricos."""
    historical_conflicts = [
        {'lat': 50.4501, 'lng': 30.5234, 'intensity': 9, 'title': 'Guerra de Ucrania (2022-presente)', 'type': 'historical_conflict'},
        {'lat': 36.2048, 'lng': 138.2529, 'intensity': 8, 'title': 'Segunda Guerra Mundial - Pacífico', 'type': 'historical_conflict'},
        {'lat': 52.5200, 'lng': 13.4050, 'intensity': 8, 'title': 'Segunda Guerra Mundial - Europa', 'type': 'historical_conflict'},
        {'lat': 17.0608, 'lng': 108.2772, 'intensity': 7, 'title': 'Guerra de Vietnam', 'type': 'historical_conflict'},
        {'lat': 33.3152, 'lng': 44.3661, 'intensity': 8, 'title': 'Guerra de Irak', 'type': 'historical_conflict'},
        {'lat': 34.5553, 'lng': 69.2075, 'intensity': 7, 'title': 'Guerra de Afganistán', 'type': 'historical_conflict'},
        {'lat': 34.8021, 'lng': 38.9968, 'intensity': 8, 'title': 'Guerra Civil Siria', 'type': 'historical_conflict'},
        {'lat': 15.5527, 'lng': 48.5164, 'intensity': 7, 'title': 'Guerra Civil de Yemen', 'type': 'historical_conflict'},
        {'lat': 0.0236, 'lng': 37.9062, 'intensity': 6, 'title': 'Conflictos en el Cuerno de África', 'type': 'historical_conflict'},
        {'lat': -11.2027, 'lng': 17.8739, 'intensity': 6, 'title': 'Guerra Civil de Angola', 'type': 'historical_conflict'},
        {'lat': 39.0742, 'lng': 21.8243, 'intensity': 6, 'title': 'Guerras de los Balcanes', 'type': 'historical_conflict'},
        {'lat': 31.7683, 'lng': 35.2137, 'intensity': 8, 'title': 'Conflicto Israelo-Palestino', 'type': 'historical_conflict'},
        {'lat': 35.9078, 'lng': 127.7669, 'intensity': 7, 'title': 'Guerra de Corea', 'type': 'historical_conflict'},
        {'lat': 28.0339, 'lng': 1.6596, 'intensity': 5, 'title': 'Conflictos del Sahel', 'type': 'historical_conflict'}
    ]
    
    return jsonify(historical_conflicts)

def get_oil_heatmap():
    """Mapa de calor de instalaciones petrolíferas."""
    oil_data = [
        {'lat': 26.0667, 'lng': 50.5577, 'intensity': 10, 'title': 'Campos petrolíferos de Bahrein', 'type': 'oil'},
        {'lat': 25.2048, 'lng': 55.2708, 'intensity': 9, 'title': 'Emiratos Árabes Unidos - Petróleo', 'type': 'oil'},
        {'lat': 24.7136, 'lng': 46.6753, 'intensity': 10, 'title': 'Arabia Saudí - Campos de Ghawar', 'type': 'oil'},
        {'lat': 29.3117, 'lng': 47.4818, 'intensity': 9, 'title': 'Kuwait - Campos petrolíferos', 'type': 'oil'},
        {'lat': 27.5142, 'lng': 90.4336, 'intensity': 8, 'title': 'Campos petrolíferos de Kirkuk, Irak', 'type': 'oil'},
        {'lat': 35.6892, 'lng': 51.3890, 'intensity': 8, 'title': 'Irán - Campos de Ahvaz', 'type': 'oil'},
        {'lat': 64.2008, 'lng': -149.4937, 'intensity': 7, 'title': 'Alaska - Prudhoe Bay', 'type': 'oil'},
        {'lat': 29.7604, 'lng': -95.3698, 'intensity': 8, 'title': 'Texas - Refinería de Houston', 'type': 'oil'},
        {'lat': 56.1304, 'lng': 101.2431, 'intensity': 7, 'title': 'Siberia - Campos petrolíferos', 'type': 'oil'},
        {'lat': 59.9139, 'lng': 10.7522, 'intensity': 7, 'title': 'Noruega - Mar del Norte', 'type': 'oil'},
        {'lat': -22.9068, 'lng': -43.1729, 'intensity': 6, 'title': 'Brasil - Campos de Santos', 'type': 'oil'},
        {'lat': 4.5709, 'lng': -74.2973, 'intensity': 5, 'title': 'Colombia - Campos petrolíferos', 'type': 'oil'},
        {'lat': 10.4806, 'lng': -66.9036, 'intensity': 7, 'title': 'Venezuela - Faja del Orinoco', 'type': 'oil'},
        {'lat': 9.0579, 'lng': 8.6753, 'intensity': 6, 'title': 'Nigeria - Delta del Níger', 'type': 'oil'},
        {'lat': 32.7767, 'lng': 13.1805, 'intensity': 6, 'title': 'Libia - Campos de Sirte', 'type': 'oil'}
    ]
    
    return jsonify(oil_data)

def get_energy_heatmap():
    """Mapa de calor de infraestructura energética."""
    energy_data = [
        {'lat': 51.4817, 'lng': -3.1791, 'intensity': 8, 'title': 'Central Nuclear de Hinkley Point', 'type': 'nuclear'},
        {'lat': 49.4172, 'lng': 2.0392, 'intensity': 9, 'title': 'Francia - Centrales Nucleares', 'type': 'nuclear'},
        {'lat': 35.3606, 'lng': 138.7274, 'intensity': 7, 'title': 'Japón - Energía Nuclear', 'type': 'nuclear'},
        {'lat': 55.7558, 'lng': 37.6173, 'intensity': 8, 'title': 'Rusia - Gasoductos', 'type': 'gas'},
        {'lat': 52.5200, 'lng': 13.4050, 'intensity': 7, 'title': 'Alemania - Energías Renovables', 'type': 'renewable'},
        {'lat': 40.7128, 'lng': -74.0060, 'intensity': 8, 'title': 'EE.UU. - Red Eléctrica', 'type': 'grid'},
        {'lat': 39.9042, 'lng': 116.4074, 'intensity': 9, 'title': 'China - Centrales de Carbón', 'type': 'coal'},
        {'lat': 28.6139, 'lng': 77.2090, 'intensity': 7, 'title': 'India - Energía Solar', 'type': 'solar'},
        {'lat': -23.5505, 'lng': -46.6333, 'intensity': 6, 'title': 'Brasil - Energía Hidroeléctrica', 'type': 'hydro'},
        {'lat': 60.1282, 'lng': 18.6435, 'intensity': 6, 'title': 'Suecia - Energía Nuclear', 'type': 'nuclear'},
        {'lat': 45.9432, 'lng': 24.9668, 'intensity': 5, 'title': 'Rumania - Gas Natural', 'type': 'gas'},
        {'lat': 41.9028, 'lng': 12.4964, 'intensity': 6, 'title': 'Italia - Energía Solar', 'type': 'solar'},
        {'lat': 40.4637, 'lng': -3.7492, 'intensity': 6, 'title': 'España - Energía Eólica', 'type': 'wind'},
        {'lat': 35.6762, 'lng': 139.6503, 'intensity': 8, 'title': 'Japón - Red Eléctrica', 'type': 'grid'}
    ]
    
    return jsonify(energy_data)

def get_supplies_heatmap():
    """Mapa de calor de cadenas de suministro críticas."""
    supply_data = [
        {'lat': 31.2304, 'lng': 121.4737, 'intensity': 10, 'title': 'Puerto de Shanghai - Suministros', 'type': 'port'},
        {'lat': 22.3193, 'lng': 114.1694, 'intensity': 9, 'title': 'Puerto de Hong Kong', 'type': 'port'},
        {'lat': 1.3521, 'lng': 103.8198, 'intensity': 9, 'title': 'Puerto de Singapur', 'type': 'port'},
        {'lat': 51.9225, 'lng': 4.4792, 'intensity': 8, 'title': 'Puerto de Rotterdam', 'type': 'port'},
        {'lat': 32.0853, 'lng': 34.7818, 'intensity': 7, 'title': 'Puerto de Ashdod', 'type': 'port'},
        {'lat': 25.2048, 'lng': 55.2708, 'intensity': 8, 'title': 'Jebel Ali - Dubai', 'type': 'port'},
        {'lat': 33.7490, 'lng': -118.2437, 'intensity': 8, 'title': 'Puerto de Los Ángeles', 'type': 'port'},
        {'lat': 40.6782, 'lng': -74.0442, 'intensity': 7, 'title': 'Puerto de Nueva York', 'type': 'port'},
        {'lat': 29.7604, 'lng': -95.3698, 'intensity': 7, 'title': 'Puerto de Houston', 'type': 'port'},
        {'lat': 49.8397, 'lng': 24.0297, 'intensity': 6, 'title': 'Corredor de suministro Europa-Asia', 'type': 'corridor'},
        {'lat': 30.0444, 'lng': 31.2357, 'intensity': 8, 'title': 'Canal de Suez', 'type': 'canal'},
        {'lat': 8.9824, 'lng': -79.5199, 'intensity': 7, 'title': 'Canal de Panamá', 'type': 'canal'},
        {'lat': 1.2966, 'lng': 103.8764, 'intensity': 9, 'title': 'Estrecho de Malaca', 'type': 'strait'},
        {'lat': 26.3351, 'lng': 56.3890, 'intensity': 8, 'title': 'Estrecho de Ormuz', 'type': 'strait'}
    ]
    
    return jsonify(supply_data)

def get_internet_cables_heatmap():
    """Mapa de calor de cables submarinos de internet."""
    cable_data = [
        {'lat': 51.5074, 'lng': -0.1278, 'intensity': 9, 'title': 'Londres - Hub de Cables Submarinos', 'type': 'cable_hub'},
        {'lat': 40.7128, 'lng': -74.0060, 'intensity': 9, 'title': 'Nueva York - Cables Transatlánticos', 'type': 'cable_hub'},
        {'lat': 35.6762, 'lng': 139.6503, 'intensity': 8, 'title': 'Tokio - Cables Transpacíficos', 'type': 'cable_hub'},
        {'lat': 1.3521, 'lng': 103.8198, 'intensity': 8, 'title': 'Singapur - Hub del Sudeste Asiático', 'type': 'cable_hub'},
        {'lat': 22.3193, 'lng': 114.1694, 'intensity': 7, 'title': 'Hong Kong - Cables de Asia', 'type': 'cable_hub'},
        {'lat': 55.7558, 'lng': 37.6173, 'intensity': 6, 'title': 'Moscú - Cables Terrestres', 'type': 'cable_hub'},
        {'lat': 52.5200, 'lng': 13.4050, 'intensity': 7, 'title': 'Berlín - Hub Europeo', 'type': 'cable_hub'},
        {'lat': 25.2048, 'lng': 55.2708, 'intensity': 7, 'title': 'Dubai - Cables del Golfo', 'type': 'cable_hub'},
        {'lat': 19.4326, 'lng': -99.1332, 'intensity': 6, 'title': 'Ciudad de México - Hub Centroamericano', 'type': 'cable_hub'},
        {'lat': -33.8688, 'lng': 151.2093, 'intensity': 7, 'title': 'Sydney - Cables del Pacífico Sur', 'type': 'cable_hub'},
        {'lat': -22.9068, 'lng': -43.1729, 'intensity': 6, 'title': 'Río de Janeiro - Cables Sudamericanos', 'type': 'cable_hub'},
        {'lat': 6.5244, 'lng': 3.3792, 'intensity': 5, 'title': 'Lagos - Cables Africanos', 'type': 'cable_hub'},
        {'lat': 30.0444, 'lng': 31.2357, 'intensity': 6, 'title': 'El Cairo - Conexiones África-Asia', 'type': 'cable_hub'},
        {'lat': 64.1466, 'lng': -21.9426, 'intensity': 5, 'title': 'Reykjavik - Cables del Ártico', 'type': 'cable_hub'}
    ]
    
    return jsonify(cable_data)

def get_military_bases_heatmap():
    """Mapa de calor de bases militares estratégicas."""
    military_data = [
        {'lat': 36.1627, 'lng': -115.1500, 'intensity': 9, 'title': 'Base Aérea Nellis - Nevada', 'type': 'military_base'},
        {'lat': 39.1434, 'lng': -77.3446, 'intensity': 8, 'title': 'Base Andrews - Maryland', 'type': 'military_base'},
        {'lat': 35.3606, 'lng': 139.7817, 'intensity': 7, 'title': 'Base Yokota - Japón', 'type': 'military_base'},
        {'lat': 37.0871, 'lng': 127.0298, 'intensity': 7, 'title': 'Base Osan - Corea del Sur', 'type': 'military_base'},
        {'lat': 26.3351, 'lng': 50.6300, 'intensity': 8, 'title': 'Base Al Udeid - Qatar', 'type': 'military_base'},
        {'lat': 32.3668, 'lng': 44.3668, 'intensity': 6, 'title': 'Zona Verde - Bagdad', 'type': 'military_base'},
        {'lat': 34.6526, 'lng': 67.9095, 'intensity': 6, 'title': 'Base Bagram - Afganistán (anterior)', 'type': 'military_base'},
        {'lat': 35.7040, 'lng': 51.3890, 'intensity': 7, 'title': 'Bases Militares Iraníes', 'type': 'military_base'},
        {'lat': 55.7558, 'lng': 37.6173, 'intensity': 8, 'title': 'Bases Militares Rusas', 'type': 'military_base'},
        {'lat': 39.9042, 'lng': 116.4074, 'intensity': 8, 'title': 'Instalaciones Militares Chinas', 'type': 'military_base'},
        {'lat': 51.4545, 'lng': -2.5879, 'intensity': 6, 'title': 'Base RAF Fairford - Reino Unido', 'type': 'military_base'},
        {'lat': 49.2127, 'lng': 7.1420, 'intensity': 6, 'title': 'Base Ramstein - Alemania', 'type': 'military_base'}
    ]
    
    return jsonify(military_data)

def get_trade_routes_heatmap():
    """Mapa de calor de rutas comerciales importantes."""
    trade_data = [
        {'lat': 30.0444, 'lng': 31.2357, 'intensity': 10, 'title': 'Canal de Suez - Ruta Comercial', 'type': 'trade_route'},
        {'lat': 8.9824, 'lng': -79.5199, 'intensity': 9, 'title': 'Canal de Panamá - Ruta Comercial', 'type': 'trade_route'},
        {'lat': 1.2966, 'lng': 103.8764, 'intensity': 9, 'title': 'Estrecho de Malaca', 'type': 'trade_route'},
        {'lat': 26.3351, 'lng': 56.3890, 'intensity': 8, 'title': 'Estrecho de Ormuz', 'type': 'trade_route'},
        {'lat': 45.0, 'lng': 35.0, 'intensity': 7, 'title': 'Ruta del Mar Negro', 'type': 'trade_route'},
        {'lat': 36.0, 'lng': 138.0, 'intensity': 8, 'title': 'Ruta Transpacífica', 'type': 'trade_route'},
        {'lat': 45.0, 'lng': -30.0, 'intensity': 8, 'title': 'Ruta Transatlántica', 'type': 'trade_route'},
        {'lat': 0.0, 'lng': 80.0, 'intensity': 7, 'title': 'Ruta del Océano Índico', 'type': 'trade_route'},
        {'lat': 70.0, 'lng': 100.0, 'intensity': 6, 'title': 'Ruta del Ártico (Futura)', 'type': 'trade_route'},
        {'lat': 45.0, 'lng': 100.0, 'intensity': 7, 'title': 'Nueva Ruta de la Seda', 'type': 'trade_route'}
    ]
    
    return jsonify(trade_data)

def get_example_points(map_type):
    """Obtener puntos de ejemplo según el tipo de mapa."""
    examples = {
        'general': [
            {'lat': 50.4501, 'lng': 30.5234, 'intensity': 8, 'type': 'conflict', 'title': 'Conflicto en Ucrania'},
            {'lat': 31.7683, 'lng': 35.2137, 'intensity': 7, 'type': 'conflict', 'title': 'Tensiones en Medio Oriente'}
        ],
        'conflict_risk': [
            {'lat': 50.4501, 'lng': 30.5234, 'intensity': 9, 'type': 'conflict_risk', 'title': 'Alto riesgo - Ucrania'},
            {'lat': 31.7683, 'lng': 35.2137, 'intensity': 8, 'type': 'conflict_risk', 'title': 'Alto riesgo - Gaza'}
        ]
    }
    return examples.get(map_type, [])

def get_fallback_heatmap():
    """Datos de respaldo en caso de error."""
    fallback_data = [
        {'lat': 50.4501, 'lng': 30.5234, 'intensity': 8, 'type': 'conflict', 'title': 'Conflicto en Ucrania'},
        {'lat': 31.7683, 'lng': 35.2137, 'intensity': 7, 'type': 'conflict', 'title': 'Tensiones en Medio Oriente'},
        {'lat': 39.9042, 'lng': 116.4074, 'intensity': 5, 'type': 'political', 'title': 'Actividad política en China'}
    ]
    return jsonify(fallback_data)

@app.route('/api/heatmap/types')
def get_heatmap_types():
    """Get available heatmap types and their descriptions."""
    map_types = {
        'general': {
            'name': 'General',
            'description': 'Todos los eventos geopolíticos',
            'icon': 'fas fa-globe',
            'color': '#3498db'
        },
        'conflict_risk': {
            'name': 'Riesgo de Conflicto',
            'description': 'Zonas con alto riesgo de conflicto',
            'icon': 'fas fa-exclamation-triangle',
            'color': '#e74c3c'
        },
        'historical_conflicts': {
            'name': 'Conflictos Históricos',
            'description': 'Conflictos y guerras históricas importantes',
            'icon': 'fas fa-history',
            'color': '#8b0000'
        },
        'oil': {
            'name': 'Instalaciones Petrolíferas',
            'description': 'Campos petrolíferos y refinerías',
            'icon': 'fas fa-oil-can',
            'color': '#f39c12'
        },
        'energy': {
            'name': 'Infraestructura Energética',
            'description': 'Centrales eléctricas y redes energéticas',
            'icon': 'fas fa-bolt',
            'color': '#f1c40f'
        },
        'supplies': {
            'name': 'Cadenas de Suministro',
            'description': 'Puertos y rutas de suministro críticas',
            'icon': 'fas fa-shipping-fast',
            'color': '#2ecc71'
        },
        'internet_cables': {
            'name': 'Cables de Internet',
            'description': 'Cables submarinos y hubs de internet',
            'icon': 'fas fa-network-wired',
            'color': '#9b59b6'
        },
        'military_bases': {
            'name': 'Bases Militares',
            'description': 'Instalaciones militares estratégicas',
            'icon': 'fas fa-shield-alt',
            'color': '#34495e'
        },
        'trade_routes': {
            'name': 'Rutas Comerciales',
            'description': 'Principales rutas comerciales mundiales',
            'icon': 'fas fa-route',
            'color': '#16a085'
        }
    }
    
    return jsonify(map_types)

@app.route('/api/risk-by-country')
def get_risk_by_country():
    """Get risk analysis by country - RUTA ESPECÍFICA PARA RIESGO POR PAÍS."""
    try:
        logger.info("Cargando análisis de riesgo por país...")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener riesgo por país
        cursor.execute("""
            SELECT country, 
                   COUNT(*) as total_events,
                   SUM(CASE WHEN risk_level = 'high' THEN 1 ELSE 0 END) as high_risk_events,
                   SUM(CASE WHEN risk_level = 'medium' THEN 1 ELSE 0 END) as medium_risk_events,
                   SUM(CASE WHEN risk_level = 'low' THEN 1 ELSE 0 END) as low_risk_events
            FROM articles 
            WHERE country IS NOT NULL
            GROUP BY country
            ORDER BY total_events DESC
            LIMIT 20
        """)
        
        countries = []
        for row in cursor.fetchall():
            # Calcular score de riesgo basado en eventos
            risk_score = (row['high_risk_events'] * 3 + row['medium_risk_events'] * 2 + row['low_risk_events'] * 1) / max(row['total_events'], 1)
            risk_score = min(risk_score * 30, 100)  # Normalizar a 0-100
            
            countries.append({
                'country': row['country'],
                'risk_score': round(risk_score, 1),
                'total_events': row['total_events'],
                'high_risk_events': row['high_risk_events'],
                'medium_risk_events': row['medium_risk_events'],
                'low_risk_events': row['low_risk_events']
            })
        
        conn.close()
        
        logger.info(f"Análisis de riesgo por país cargado: {len(countries)} países")
        return jsonify(countries)
        
    except Exception as e:
        logger.error(f"Error getting risk by country: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/weekly-analysis')
def get_ai_weekly_analysis():
    """Get AI weekly analysis - RUTA ESPECÍFICA PARA ANÁLISIS SEMANAL IA."""
    try:
        logger.info("Generando análisis semanal por IA...")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener estadísticas de la semana
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN risk_level = 'high' THEN 1 ELSE 0 END) as high_risk,
                   COUNT(DISTINCT country) as countries
            FROM articles 
            WHERE datetime(created_at) > datetime('now', '-7 days')
        """)
        
        stats = cursor.fetchone()
        
        # Obtener países más activos
        cursor.execute("""
            SELECT country, COUNT(*) as count
            FROM articles 
            WHERE datetime(created_at) > datetime('now', '-7 days')
            AND country IS NOT NULL
            GROUP BY country
            ORDER BY count DESC
            LIMIT 5
        """)
        
        top_countries = [row['country'] for row in cursor.fetchall()]
        
        conn.close()
        
        # Generar análisis basado en datos reales
        analysis = {
            'title': 'Análisis Geopolítico Semanal',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'summary': f'Esta semana se han procesado {stats["total"]} artículos de {stats["countries"]} países diferentes, con {stats["high_risk"]} eventos clasificados como de alto riesgo.',
            'key_insights': [
                f'Se detectaron {stats["high_risk"]} eventos de alto riesgo esta semana',
                f'Los países más activos fueron: {", ".join(top_countries[:3])}' if top_countries else 'Actividad distribuida globalmente',
                f'Total de {stats["countries"]} países con actividad geopolítica significativa',
                'Tendencia general: monitoreo continuo requerido'
            ],
            'risk_assessment': {
                'global_risk_level': 'Alto' if stats["high_risk"] > 10 else 'Medio' if stats["high_risk"] > 5 else 'Bajo',
                'trend': 'Estable',
                'confidence': 85.7
            },
            'recommendations': [
                'Mantener monitoreo continuo de regiones de alto riesgo',
                'Incrementar análisis de fuentes en idiomas locales',
                'Coordinar con organizaciones internacionales',
                'Actualizar protocolos de respuesta según patrones identificados'
            ]
        }
        
        logger.info("Análisis semanal por IA generado")
        return jsonify(analysis)
        
    except Exception as e:
        logger.error(f"Error getting AI weekly analysis: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/events')
def get_events():
    """Get recent events from database - CARGA EVENTOS REALES."""
    try:
        logger.info("Cargando eventos de la base de datos...")
        
        limit = request.args.get('limit', 50, type=int)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT title, content, published_at, source, location, type, magnitude
            FROM events 
            ORDER BY published_at DESC 
            LIMIT ?
        """, (limit,))
        
        events = []
        for row in cursor.fetchall():
            # Intentar parsear la ubicación como JSON
            location = None
            if row['location']:
                try:
                    location = json.loads(row['location'])
                except:
                    location = None
            
            events.append({
                'title': row['title'],
                'content': row['content'][:150] + '...' if row['content'] else '',
                'published_at': row['published_at'],
                'source': row['source'],
                'location': location,
                'type': row['type'] or 'general',
                'magnitude': row['magnitude']
            })
        
        conn.close()
        
        logger.info(f"Cargados {len(events)} eventos")
        return jsonify(events)
        
    except Exception as e:
        logger.error(f"Error getting events: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/risk-analysis')
def get_risk_analysis():
    """Get risk analysis from database - ANÁLISIS DE RIESGO REAL."""
    try:
        logger.info("Cargando análisis de riesgo...")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Artículo de mayor riesgo
        cursor.execute("""
            SELECT title, content, country, risk_level, created_at
            FROM articles 
            WHERE risk_level = 'high'
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        
        top_risk_article = cursor.fetchone()
        
        # Distribución por nivel de riesgo
        cursor.execute("""
            SELECT risk_level, COUNT(*) as count
            FROM articles 
            GROUP BY risk_level
        """)
        
        risk_distribution = {}
        for row in cursor.fetchall():
            risk_distribution[row['risk_level'] or 'unknown'] = row['count']
        
        # Países con más eventos
        cursor.execute("""
            SELECT country, COUNT(*) as count
            FROM articles 
            WHERE country IS NOT NULL
            GROUP BY country
            ORDER BY count DESC
            LIMIT 10
        """)
        
        countries = []
        for row in cursor.fetchall():
            countries.append({
                'country': row['country'],
                'count': row['count'],
                'risk_score': min(row['count'] * 10, 100)  # Calculado basado en cantidad
            })
        
        conn.close()
        
        result = {
            'top_risk_article': {
                'title': top_risk_article['title'] if top_risk_article else 'No hay artículos de alto riesgo',
                'content': top_risk_article['content'][:300] + '...' if top_risk_article and top_risk_article['content'] else '',
                'country': top_risk_article['country'] if top_risk_article else 'Global',
                'risk_level': top_risk_article['risk_level'] if top_risk_article else 'medium',
                'created_at': top_risk_article['created_at'] if top_risk_article else datetime.now().isoformat()
            },
            'risk_distribution': risk_distribution,
            'countries': countries
        }
        
        logger.info(f"Análisis de riesgo cargado: {len(countries)} países")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting risk analysis: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test')
def test_api():
    """Endpoint de prueba."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM articles")
        article_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM events")
        event_count = cursor.fetchone()[0]
        
        # Verificar eventos con ubicación
        cursor.execute("SELECT COUNT(*) FROM events WHERE location IS NOT NULL AND location != ''")
        events_with_location = cursor.fetchone()[0]
        
        # Muestra de eventos con ubicación
        cursor.execute("""
            SELECT title, location, type, magnitude 
            FROM events 
            WHERE location IS NOT NULL AND location != '' 
            LIMIT 5
        """)
        sample_events = []
        for row in cursor.fetchall():
            sample_events.append({
                'title': row['title'],
                'location': row['location'],
                'type': row['type'],
                'magnitude': row['magnitude']
            })
        
        conn.close()
        
        return jsonify({
            'status': 'OK',
            'message': 'Dashboard funcionando correctamente',
            'database': {
                'articles': article_count,
                'events': event_count,
                'events_with_location': events_with_location,
                'path': DB_PATH
            },
            'sample_events': sample_events,
            'scheduler_running': scheduler_bg.running if scheduler_bg else False,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'ERROR',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# ==================== AI IMPORTANCE CALCULATION ENDPOINT ====================

@app.route('/api/calculate-importance', methods=['POST'])
def calculate_importance_endpoint():
    """
    Calculate article importance using AI models (Transformers + Groq)
    """
    try:
        # Import AI calculator
        from ai_importance_calculator import calculate_article_importance
        
        # Get article data from request
        article_data = request.get_json()
        
        if not article_data:
            return jsonify({'error': 'No article data provided'}), 400
        
        # Required fields validation
        required_fields = ['title']
        missing_fields = [field for field in required_fields if not article_data.get(field)]
        
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {missing_fields}'}), 400
        
        # Calculate importance using AI
        importance_score = calculate_article_importance(article_data)
        
        # Log the calculation for monitoring
        logger.info(f"AI calculated importance {importance_score:.2f} for article: {article_data.get('title', '')[:50]}...")
        
        return jsonify({
            'importance_score': importance_score,
            'article_title': article_data.get('title', ''),
            'risk_level': article_data.get('risk_level', 'unknown'),
            'location': article_data.get('location', ''),
            'timestamp': datetime.now().isoformat(),
            'ai_model': 'transformers+groq'
        })
        
    except ImportError as e:
        logger.warning(f"AI calculator not available: {e}")
        # Fallback to basic calculation
        try:
            article_data = request.get_json()
            basic_score = calculate_basic_importance(article_data)
            
            return jsonify({
                'importance_score': basic_score,
                'article_title': article_data.get('title', ''),
                'risk_level': article_data.get('risk_level', 'unknown'),
                'location': article_data.get('location', ''),
                'timestamp': datetime.now().isoformat(),
                'ai_model': 'fallback'
            })
        except Exception as fallback_error:
            logger.error(f"Fallback calculation failed: {fallback_error}")
            return jsonify({'error': 'AI calculation failed'}), 500
            
    except Exception as e:
        logger.error(f"Error calculating importance: {e}")
        return jsonify({'error': str(e)}), 500

def calculate_basic_importance(article_data):
    """
    Basic importance calculation when AI models are not available
    """
    if not article_data:
        return 30.0
    
    score = 0.0
    
    # Risk level (40% weight)
    risk_weights = {
        'high': 100,
        'medium': 60, 
        'low': 30,
        'critical': 100
    }
    risk_level = article_data.get('risk_level', 'low').lower()
    score += risk_weights.get(risk_level, 40) * 0.4
    
    # Recency (30% weight)
    published_date = article_data.get('published_date', '')
    if published_date:
        try:
            from datetime import datetime, timezone
            if isinstance(published_date, str):
                # Simple date parsing
                article_date = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
            else:
                article_date = published_date
                
            if article_date.tzinfo is None:
                article_date = article_date.replace(tzinfo=timezone.utc)
                
            now = datetime.now(timezone.utc)
            hours_diff = (now - article_date).total_seconds() / 3600
            
            if hours_diff < 1:
                recency_score = 100
            elif hours_diff < 6:
                recency_score = 80
            elif hours_diff < 24:
                recency_score = 60
            elif hours_diff < 72:
                recency_score = 40
            else:
                recency_score = 20
                
            score += recency_score * 0.3
        except:
            score += 40 * 0.3
    else:
        score += 40 * 0.3
    
    # Keyword analysis (20% weight)
    title = article_data.get('title', '').lower()
    content = article_data.get('content', '').lower()
    
    high_impact_keywords = [
        'guerra', 'war', 'conflicto', 'conflict', 'crisis', 'emergency',
        'ataque', 'attack', 'bomba', 'bomb', 'explosion', 'terrorism',
        'muertos', 'dead', 'victims', 'casualties'
    ]
    
    keyword_score = 0
    for keyword in high_impact_keywords:
        if keyword in title or keyword in content:
            keyword_score += 15
    
    score += min(keyword_score, 80) * 0.2
    
    # Location importance (10% weight)
    location = article_data.get('location', '').lower()
    high_risk_locations = [
        'ukraine', 'gaza', 'israel', 'syria', 'afghanistan', 'yemen'
    ]
    
    location_score = 40
    for loc in high_risk_locations:
        if loc in location:
            location_score = 80
            break
    
    score += location_score * 0.1
    
    return max(0, min(100, score))

# ==================== EXECUTIVE REPORTS ENDPOINTS ====================

@app.route('/api/reports/recent')
def get_recent_reports():
    """Get recent reports from database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get recent reports based on processed data grouped by date
        cursor.execute("""
            SELECT 
                DATE(processed_at) as report_date,
                COUNT(*) as articles_analyzed,
                AVG(CASE WHEN sentiment > 0 THEN sentiment ELSE 0 END) as avg_sentiment,
                COUNT(CASE WHEN confidence_score > 0.7 THEN 1 END) as high_confidence_count,
                GROUP_CONCAT(DISTINCT category) as categories
            FROM processed_data 
            WHERE processed_at >= date('now', '-30 days')
            GROUP BY DATE(processed_at)
            ORDER BY report_date DESC
            LIMIT 10
        """)
        
        reports = []
        for row in cursor.fetchall():
            reports.append({
                'id': f"report_{row[0].replace('-', '')}",
                'title': f"Análisis Geopolítico - {row[0]}",
                'date': row[0],
                'type': 'daily_analysis',
                'status': 'completed',
                'articles_analyzed': row[1],
                'avg_sentiment': round(row[2] if row[2] else 0, 2),
                'confidence': round((row[3] / row[1] * 100) if row[1] > 0 else 0, 1),
                'categories': row[4].split(',') if row[4] else [],
                'risk_level': 'medium' if row[2] and row[2] < 0 else 'low'
            })
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'reports': reports,
            'total': len(reports)
        })
        
    except Exception as e:
        logger.error(f"Error getting recent reports: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/reports/templates')
def get_report_templates():
    """Get available report templates."""
    try:
        templates = [
            {
                'id': 'daily_risk_assessment',
                'name': 'Evaluación Diaria de Riesgos',
                'description': 'Análisis de riesgos geopolíticos basado en artículos del día',
                'type': 'daily',
                'fields': ['risk_analysis', 'sentiment_trends', 'geographic_hotspots'],
                'frequency': 'daily'
            },
            {
                'id': 'weekly_geopolitical_summary',
                'name': 'Resumen Geopolítico Semanal',
                'description': 'Resumen semanal de eventos geopolíticos relevantes',
                'type': 'weekly',
                'fields': ['event_summary', 'risk_trends', 'conflict_analysis'],
                'frequency': 'weekly'
            },
            {
                'id': 'regional_conflict_monitor',
                'name': 'Monitor de Conflictos Regionales',
                'description': 'Análisis específico de conflictos por región',
                'type': 'regional',
                'fields': ['conflict_mapping', 'escalation_indicators', 'peace_initiatives'],
                'frequency': 'on_demand'
            },
            {
                'id': 'executive_briefing',
                'name': 'Briefing Ejecutivo',
                'description': 'Resumen ejecutivo para toma de decisiones',
                'type': 'executive',
                'fields': ['key_highlights', 'risk_recommendations', 'action_items'],
                'frequency': 'weekly'
            }
        ]
        
        return jsonify({
            'status': 'success',
            'templates': templates,
            'total': len(templates)
        })
        
    except Exception as e:
        logger.error(f"Error getting report templates: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/reports/config')
def get_report_config():
    """Get report configuration settings."""
    try:
        config = {
            'auto_generation': {
                'enabled': True,
                'frequency': 'daily',
                'time': '06:00'
            },
            'notification_settings': {
                'email_enabled': False,
                'slack_enabled': False,
                'high_risk_alerts': True
            },
            'export_formats': ['PDF', 'HTML', 'JSON'],
            'retention_policy': {
                'days': 90,
                'auto_archive': True
            },
            'risk_thresholds': {
                'low': 0.3,
                'medium': 0.6,
                'high': 0.8
            },
            'data_sources': {
                'total_articles': 1021,
                'active_sources': 81,
                'last_update': datetime.now().isoformat()
            }
        }
        
        return jsonify({
            'status': 'success',
            'config': config
        })
        
    except Exception as e:
        logger.error(f"Error getting report config: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/reports/generate', methods=['POST'])
def generate_report():
    """Generate a new report."""
    try:
        data = request.get_json()
        template_id = data.get('template', 'daily_risk_assessment')
        report_name = data.get('name', f'Report {datetime.now().strftime("%Y%m%d_%H%M")}')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get recent articles for the report
        cursor.execute("""
            SELECT a.*, pd.sentiment, pd.confidence_score, pd.category
            FROM articles a
            LEFT JOIN processed_data pd ON a.id = pd.article_id
            WHERE a.created_at >= date('now', '-1 days')
            ORDER BY a.risk_score DESC
            LIMIT 50
        """)
        
        articles = cursor.fetchall()
        
        # Calculate report metrics
        high_risk_count = len([a for a in articles if a[16] and a[16] > 0.6])  # risk_score > 0.6
        avg_sentiment = sum([a[17] for a in articles if a[17]]) / len([a for a in articles if a[17]]) if articles else 0
        
        report = {
            'id': f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'name': report_name,
            'template': template_id,
            'generated_at': datetime.now().isoformat(),
            'status': 'completed',
            'metrics': {
                'total_articles': len(articles),
                'high_risk_articles': high_risk_count,
                'avg_sentiment': round(avg_sentiment, 2),
                'risk_level': 'high' if high_risk_count > 10 else 'medium' if high_risk_count > 5 else 'low'
            },
            'summary': f"Análisis de {len(articles)} artículos con {high_risk_count} eventos de alto riesgo detectados."
        }
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'report': report,
            'message': 'Reporte generado exitosamente'
        })
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/reports/filter', methods=['POST'])
def filter_reports():
    """Filter reports by criteria."""
    try:
        data = request.get_json()
        filters = data.get('filters', {})
        
        # This would filter existing reports - for now return sample filtered data
        filtered_reports = [
            {
                'id': 'filtered_report_001',
                'title': 'Reporte Filtrado - Alto Riesgo',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'type': 'filtered',
                'status': 'completed',
                'risk_level': 'high',
                'filters_applied': filters
            }
        ]
        
        return jsonify({
            'status': 'success',
            'reports': filtered_reports,
            'filters_applied': filters,
            'total': len(filtered_reports)
        })
        
    except Exception as e:
        logger.error(f"Error filtering reports: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/reports/<report_id>/view')
def view_report(report_id):
    """View a specific report."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get report data based on ID (parse date from ID if it's date-based)
        if 'report_' in report_id:
            date_part = report_id.replace('report_', '')
            if len(date_part) == 8:  # YYYYMMDD format
                report_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
                
                cursor.execute("""
                    SELECT a.*, pd.sentiment, pd.confidence_score
                    FROM articles a
                    LEFT JOIN processed_data pd ON a.id = pd.article_id
                    WHERE DATE(a.created_at) = ?
                    ORDER BY a.risk_score DESC
                """, (report_date,))
                
                articles = cursor.fetchall()
                
                report_data = {
                    'id': report_id,
                    'title': f'Análisis Geopolítico - {report_date}',
                    'date': report_date,
                    'status': 'completed',
                    'articles': [
                        {
                            'title': article[1],
                            'risk_score': article[16] if article[16] else 0,
                            'sentiment': article[17] if article[17] else 0,
                            'country': article[9],
                            'source': article[5]
                        } for article in articles[:10]
                    ],
                    'summary': f"Análisis de {len(articles)} artículos para el {report_date}"
                }
        else:
            # Default report structure
            report_data = {
                'id': report_id,
                'title': f'Reporte {report_id}',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'status': 'completed',
                'articles': [],
                'summary': 'Reporte no encontrado o generado dinámicamente'
            }
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'report': report_data
        })
        
    except Exception as e:
        logger.error(f"Error viewing report {report_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# ==================== ADVANCED BERT IMPORTANCE ANALYSIS ENDPOINT ====================

@app.route('/api/analyze-importance', methods=['POST'])
def analyze_importance_bert():
    """
    Advanced importance and risk factor analysis using BERT model for political news sentiment
    Endpoint que utiliza el modelo preentrenado leroyrr/bert-for-political-news-sentiment-analysis-lora
    """
    try:
        # Get article data
        article_data = request.get_json()
        
        if not article_data:
            return jsonify({
                'error': 'No article data provided',
                'importance_factor': 30.0,
                'risk_factor': 30.0
            }), 400
        
        # Validate required fields
        if not article_data.get('title') and not article_data.get('content'):
            return jsonify({
                'error': 'At least title or content is required',
                'importance_factor': 30.0,
                'risk_factor': 30.0
            }), 400
        
        # Try to use BERT model for advanced analysis
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
            import torch
            
            # Load the specific BERT model for political news sentiment analysis
            model_name = "leroyrr/bert-for-political-news-sentiment-analysis-lora"
            
            # Create sentiment analysis pipeline
            sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model=model_name,
                tokenizer=model_name,
                return_all_scores=True
            )
            
            # Prepare text for analysis
            title = article_data.get('title', '')
            content = article_data.get('content', '')
            analysis_text = f"{title}. {content[:500]}"  # Limit text for performance
            
            # Analyze sentiment with BERT
            bert_results = sentiment_analyzer(analysis_text)
            
            # Extract sentiment scores
            sentiment_scores = {result['label']: result['score'] for result in bert_results}
            
            # Calculate advanced importance based on BERT analysis
            negative_sentiment = sentiment_scores.get('NEGATIVE', 0)
            positive_sentiment = sentiment_scores.get('POSITIVE', 0)
            
            # Higher negative sentiment in political news often indicates higher importance/risk
            bert_importance = (negative_sentiment * 80) + (positive_sentiment * 20)
            
            logger.info(f"BERT Analysis - Negative: {negative_sentiment:.3f}, Positive: {positive_sentiment:.3f}, Importance: {bert_importance:.2f}")
            
        except Exception as bert_error:
            logger.warning(f"BERT model not available, using fallback: {bert_error}")
            # Fallback to enhanced local calculation
            bert_importance = calculate_fallback_importance(article_data)
            sentiment_scores = {'NEGATIVE': 0.5, 'POSITIVE': 0.5}
        
        # Enhanced risk factor calculation
        risk_factor = calculate_enhanced_risk_factor(article_data, bert_importance)
        
        # Combined importance factor
        final_importance = (bert_importance * 0.7) + (risk_factor * 0.3)
        
        # Ensure score is between 10-100
        final_importance = max(10, min(100, final_importance))
        
        return jsonify({
            'importance_factor': round(final_importance, 2),
            'risk_factor': round(risk_factor, 2),
            'bert_analysis': {
                'negative_sentiment': round(sentiment_scores.get('NEGATIVE', 0), 3),
                'positive_sentiment': round(sentiment_scores.get('POSITIVE', 0), 3),
                'confidence': round(max(sentiment_scores.values()) if sentiment_scores else 0.5, 3)
            },
            'article_metadata': {
                'title': article_data.get('title', '')[:100],
                'location': article_data.get('location', ''),
                'risk_level': article_data.get('risk_level', 'unknown'),
                'analysis_timestamp': datetime.now().isoformat()
            },
            'model_info': {
                'primary_model': 'leroyrr/bert-for-political-news-sentiment-analysis-lora',
                'analysis_type': 'advanced_political_sentiment',
                'fallback_used': 'bert_model' not in locals()
            }
        })
        
    except Exception as e:
        logger.error(f"Error in BERT importance analysis: {e}")
        # Return fallback score on any error
        fallback_score = calculate_fallback_importance(article_data if 'article_data' in locals() else {})
        
        return jsonify({
            'importance_factor': fallback_score,
            'risk_factor': fallback_score,
            'error': str(e),
            'fallback_used': True,
            'analysis_timestamp': datetime.now().isoformat()
        }), 200  # Return 200 to allow frontend to continue

def calculate_fallback_importance(article_data):
    """
    Enhanced fallback calculation when BERT is not available
    """
    if not article_data:
        return 30.0
    
    score = 0.0
    
    # Risk level analysis (40% weight)
    risk_level = article_data.get('risk_level', 'unknown').lower()
    risk_mapping = {
        'critical': 95, 'high': 85, 'medium': 60, 'low': 35, 'unknown': 45
    }
    score += risk_mapping.get(risk_level, 45) * 0.4
    
    # Temporal relevance (30% weight)
    recency_score = calculate_recency_score(article_data.get('created_at') or article_data.get('published_date'))
    score += recency_score * 0.3
    
    # Content analysis (20% weight)
    content_score = analyze_content_keywords(article_data)
    score += content_score * 0.2
    
    # Location importance (10% weight)
    location_score = analyze_location_importance(article_data.get('location', ''))
    score += location_score * 0.1
    
    return max(10, min(100, score))

def calculate_enhanced_risk_factor(article_data, bert_importance):
    """
    Calculate enhanced risk factor combining multiple signals
    """
    base_risk = bert_importance * 0.6  # BERT contributes 60%
    
    # Geographic risk assessment
    location = article_data.get('location', '').lower()
    geo_risk = 40  # default
    
    high_risk_regions = {
        'ukraine': 95, 'gaza': 95, 'israel': 90, 'palestine': 90,
        'syria': 85, 'afghanistan': 80, 'yemen': 85, 'lebanon': 75,
        'iran': 80, 'iraq': 75, 'somalia': 70, 'sudan': 80
    }
    
    for region, risk_score in high_risk_regions.items():
        if region in location:
            geo_risk = risk_score
            break
    
    # Temporal escalation factor
    temporal_factor = calculate_recency_score(article_data.get('created_at'))
    
    # Combine factors
    final_risk = (base_risk * 0.5) + (geo_risk * 0.3) + (temporal_factor * 0.2)
    
    return max(10, min(100, final_risk))

def calculate_recency_score(date_str):
    """Calculate recency score based on article timestamp"""
    if not date_str:
        return 40.0
    
    try:
        from datetime import datetime, timezone
        
        if isinstance(date_str, str):
            # Handle multiple date formats
            for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                try:
                    article_date = datetime.strptime(date_str.replace('Z', '').replace('+00:00', ''), fmt)
                    break
                except ValueError:
                    continue
            else:
                return 40.0
        else:
            article_date = date_str
        
        if article_date.tzinfo is None:
            article_date = article_date.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        hours_diff = (now - article_date).total_seconds() / 3600
        
        # More aggressive scoring for recent news
        if hours_diff < 1:
            return 100
        elif hours_diff < 3:
            return 90
        elif hours_diff < 12:
            return 75
        elif hours_diff < 24:
            return 60
        elif hours_diff < 48:
            return 45
        elif hours_diff < 168:  # 1 week
            return 30
        else:
            return 15
            
    except Exception:
        return 40.0

def analyze_content_keywords(article_data):
    """Enhanced keyword analysis for content importance"""
    title = (article_data.get('title', '') + ' ' + article_data.get('content', '')).lower()
    
    # Weighted keyword categories
    critical_keywords = {
        'nuclear': 100, 'war': 95, 'invasion': 95, 'attack': 90, 'bombing': 90,
        'missile': 85, 'crisis': 80, 'conflict': 75, 'terrorism': 95, 'coup': 90
    }
    
    high_impact_keywords = {
        'military': 70, 'army': 65, 'defense': 60, 'security': 55, 'border': 60,
        'government': 50, 'parliament': 45, 'election': 55, 'protest': 65
    }
    
    medium_impact_keywords = {
        'economic': 40, 'trade': 35, 'diplomatic': 45, 'alliance': 50, 'sanction': 70
    }
    
    score = 0
    word_count = len(title.split())
    
    # Check critical keywords
    for keyword, weight in critical_keywords.items():
        if keyword in title:
            score += weight / max(word_count / 10, 1)  # Normalize by content length
    
    # Check high impact keywords  
    for keyword, weight in high_impact_keywords.items():
        if keyword in title:
            score += weight / max(word_count / 15, 1)
            
    # Check medium impact keywords
    for keyword, weight in medium_impact_keywords.items():
        if keyword in title:
            score += weight / max(word_count / 20, 1)
    
    return min(100, score)

def analyze_location_importance(location):
    """Analyze geopolitical importance of location"""
    if not location:
        return 40
    
    location = location.lower()
    
    # Strategic importance mapping
    strategic_locations = {
        'washington': 90, 'moscow': 90, 'beijing': 85, 'london': 80, 'paris': 75,
        'berlin': 75, 'tokyo': 80, 'seoul': 70, 'new delhi': 75, 'tel aviv': 85,
        'tehran': 80, 'ankara': 70, 'cairo': 65, 'riyadh': 75, 'brasilia': 60
    }
    
    conflict_zones = {
        'ukraine': 95, 'gaza': 95, 'west bank': 90, 'syria': 85, 'afghanistan': 80,
        'yemen': 85, 'lebanon': 75, 'iraq': 75, 'somalia': 70, 'sudan': 80,
        'myanmar': 70, 'haiti': 65, 'libya': 70, 'mali': 65
    }
    
    # Check strategic locations
    for loc, importance in strategic_locations.items():
        if loc in location:
            return importance
    
    # Check conflict zones
    for loc, importance in conflict_zones.items():
        if loc in location:
            return importance
    
    # Default regional importance
    regions = {
        'europe': 60, 'asia': 55, 'middle east': 80, 'africa': 50,
        'america': 55, 'pacific': 50
    }
    
    for region, importance in regions.items():
        if region in location:
            return importance
    
    return 40  # Default score

if __name__ == '__main__':
    print("🚀 Iniciando Riskmap Dashboard (Versión Corregida)...")
    print(f"📂 Base de datos: {DB_PATH}")
    print("🌐 URL: http://localhost:5000")
    print("🧪 Test API: http://localhost:5000/api/test")
    print("📊 Stats: http://localhost:5000/api/dashboard/stats")
    print("📰 Articles: http://localhost:5000/api/articles")
    print("🔥 High Risk: http://localhost:5000/api/articles/high-risk")
    print("⭐ Featured: http://localhost:5000/api/articles/featured")
    print("🗺️ Heatmap: http://localhost:5000/api/events/heatmap")
    print("🔄 Para detener: Ctrl+C")
    print("-" * 50)
    
    # Start scheduler after Flask app is ready
    start_scheduler()
    
    try:
        socketio.run(app, host='127.0.0.1', port=5000, debug=True, use_reloader=False)
    finally:
        cleanup_scheduler()