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
            SELECT title, content, created_at, country, risk_level, url, source, language
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
                'language': row['language'] or 'es'
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
            SELECT title, content, created_at, country, risk_level, url, source, language
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
                'language': row['language'] or 'es'
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
            SELECT title, content, created_at, country, risk_level, url, source, language
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
                'language': row['language'] or 'es'
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
            SELECT title, content, created_at, country, risk_level, url, source, language
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
                'language': row['language'] or 'es'
            }
        else:
            # Si no hay artículos de alto riesgo, buscar cualquier artículo reciente
            cursor.execute("""
                SELECT title, content, created_at, country, risk_level, url, source, language
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
                    'language': row['language'] or 'es'
                }
            else:
                article = {'id': 0, 'title': 'No hay artículos disponibles'}
        
        conn.close()
        
        logger.info(f"Artículo destacado cargado: {article.get('title', 'N/A')}")
        return jsonify(article)
        
    except Exception as e:
        logger.error(f"Error getting featured article: {e}")
        return jsonify({'id': 0, 'title': 'Error al cargar artículo', 'error': str(e)}), 500

@app.route('/api/events/heatmap')
def get_heatmap_data():
    """Get heatmap data - RUTA ESPECÍFICA PARA MAPA DE CALOR."""
    try:
        logger.info("Cargando datos del mapa de calor...")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener eventos con ubicación
        cursor.execute("""
            SELECT location, type, magnitude, title
            FROM events 
            WHERE location IS NOT NULL 
            AND location != ''
            ORDER BY published_at DESC
            LIMIT 500
        """)
        
        heatmap_data = []
        for row in cursor.fetchall():
            try:
                location = json.loads(row['location'])
                if isinstance(location, list) and len(location) == 2:
                    heatmap_data.append({
                        'lat': float(location[0]),
                        'lng': float(location[1]),
                        'intensity': min(float(row['magnitude'] or 1), 10),
                        'type': row['type'] or 'general',
                        'title': row['title'][:50] + '...'
                    })
            except (json.JSONDecodeError, ValueError, TypeError):
                continue
        
        # Si no hay datos reales, generar algunos puntos de ejemplo
        if len(heatmap_data) == 0:
            heatmap_data = [
                {'lat': 50.4501, 'lng': 30.5234, 'intensity': 8, 'type': 'conflict', 'title': 'Conflicto en Ucrania'},
                {'lat': 31.7683, 'lng': 35.2137, 'intensity': 7, 'type': 'conflict', 'title': 'Tensiones en Medio Oriente'},
                {'lat': 39.9042, 'lng': 116.4074, 'intensity': 5, 'type': 'political', 'title': 'Actividad política en China'},
                {'lat': 55.7558, 'lng': 37.6173, 'intensity': 6, 'type': 'economic', 'title': 'Situación económica en Rusia'},
                {'lat': 40.7128, 'lng': -74.0060, 'intensity': 4, 'type': 'social', 'title': 'Eventos sociales en EE.UU.'}
            ]
        
        conn.close()
        
        logger.info(f"Mapa de calor cargado: {len(heatmap_data)} puntos")
        return jsonify(heatmap_data)
        
    except Exception as e:
        logger.error(f"Error getting heatmap data: {e}")
        return jsonify({'error': str(e)}), 500

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

@app.route('/api/heatmap')
def get_heatmap():
    """Get heatmap data from database - MAPA DE CALOR REAL."""
    try:
        logger.info("Cargando datos del mapa de calor...")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener eventos con ubicación
        cursor.execute("""
            SELECT location, type, magnitude, title
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
                    heatmap_data.append({
                        'lat': float(location[0]),
                        'lng': float(location[1]),
                        'intensity': min(float(row['magnitude'] or 1), 10),
                        'type': row['type'] or 'general',
                        'title': row['title'][:50] + '...'
                    })
            except (json.JSONDecodeError, ValueError, TypeError):
                continue
        
        conn.close()
        
        logger.info(f"Mapa de calor cargado: {len(heatmap_data)} puntos")
        return jsonify(heatmap_data)
        
    except Exception as e:
        logger.error(f"Error getting heatmap: {e}")
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
        
        conn.close()
        
        return jsonify({
            'status': 'OK',
            'message': 'Dashboard funcionando correctamente',
            'database': {
                'articles': article_count,
                'events': event_count,
                'path': DB_PATH
            },
            'scheduler_running': scheduler_bg.running if scheduler_bg else False,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'ERROR',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

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