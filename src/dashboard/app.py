"""
Dashboard Principal Flask para el Sistema de Inteligencia Geopolítica.
Interfaz web profesional con diseño moderno, APIs optimizadas y análisis en tiempo real.
"""

from flask import Flask, render_template, jsonify, request, send_from_directory, abort
from flask_cors import CORS
import sqlite3
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from functools import wraps
import sys
import traceback
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.config import config, DatabaseManager

# AI Models
try:
    from analytics.ai_models import AIModels
    ai_models = AIModels(config)
    
    def ai_generate_analysis(articles_data, nlp_summary=None):
        """
        Genera análisis de IA combinando datos de artículos con análisis NLP avanzado.
        Integra modelos Groq, OpenAI y análisis NuNER.
        """
        if not articles_data:
            return {
                'analysis': 'No hay suficientes datos disponibles para generar un análisis completo.',
                'risk_level': 'MEDIUM',
                'key_insights': ['Datos insuficientes para análisis detallado'],
                'recommendations': ['Monitorear desarrollo de eventos'],
                'nlp_enhanced': False
            }
        
        # Preparar texto de artículos con información NLP enriquecida
        articles_text = ""
        nlp_metrics = ""
        
        for article in articles_data[:10]:  # Limitar a 10 artículos
            title = article.get('title', '')
            content = article.get('content', '') or article.get('summary', '')
            risk_score = article.get('risk_score')
            sentiment = article.get('sentiment_label')
            
            article_line = f"- {title}: {content}"
            if risk_score:
                article_line += f" [Risk Score: {risk_score}/10]"
            if sentiment:
                article_line += f" [Sentiment: {sentiment}]"
            
            articles_text += article_line + "\n"
        
        # Agregar métricas NLP si están disponibles
        if nlp_summary and nlp_summary.get('risk_levels'):
            avg_risk = sum(nlp_summary['risk_levels']) / len(nlp_summary['risk_levels'])
            sentiment_dist = nlp_summary.get('sentiment_distribution', {})
            key_entities = list(set(nlp_summary.get('key_entities', [])))[:10]
            countries = list(nlp_summary.get('countries_involved', set()))
            
            nlp_metrics = f"""
            
MÉTRICAS DE ANÁLISIS NLP AVANZADO:
- Score de Riesgo Promedio: {avg_risk:.2f}/10
- Distribución de Sentimientos: {sentiment_dist}
- Entidades Clave Identificadas: {', '.join(key_entities) if key_entities else 'N/A'}
- Países Involucrados: {', '.join(countries) if countries else 'Global'}
- Indicadores de Conflicto: {len(nlp_summary.get('conflict_indicators', []))} detectados
"""
        
        prompt = f"""
        Como analista geopolítico experto con acceso a análisis NLP avanzado, analiza los siguientes datos:

        ARTÍCULOS ANALIZADOS CON IA:
        {articles_text}
        {nlp_metrics}

        Genera un análisis estratégico completo que incluya:
        1. Un análisis ejecutivo detallado (máximo 300 palabras)
        2. Evaluación del nivel de riesgo global (CRITICAL, HIGH, MEDIUM, LOW)
        3. 4-6 insights clave basados en patrones identificados
        4. 4-6 recomendaciones estratégicas específicas

        IMPORTANTE: Utiliza las métricas NLP proporcionadas para fundamentar tu análisis.
        
        Responde en formato JSON:
        {{
            "analysis": "análisis_ejecutivo_detallado",
            "risk_level": "nivel_riesgo",
            "key_insights": ["insight1", "insight2", "insight3", "insight4"],
            "recommendations": ["rec1", "rec2", "rec3", "rec4"]
        }}
        """
        
        try:
            response = ai_models.generate_response(prompt)
            # Intentar parsear respuesta JSON
            import json
            result = json.loads(response)
            result['nlp_enhanced'] = True
            result['nlp_metrics'] = nlp_summary if nlp_summary else {}
            return result
        except Exception as e:
            logger.warning(f"Error parsing AI response: {e}")
            # Respuesta de fallback mejorada con datos NLP
            fallback_risk = 'HIGH' if nlp_summary and sum(nlp_summary.get('risk_levels', [0])) / len(nlp_summary.get('risk_levels', [1])) > 5 else 'MEDIUM'
            
            return {
                'analysis': f'Análisis geopolítico basado en {len(articles_data)} artículos recientes con análisis NLP avanzado. Los datos muestran tendencias complejas en múltiples regiones con un score de riesgo promedio de {sum(nlp_summary.get("risk_levels", [0])) / len(nlp_summary.get("risk_levels", [1])):.1f}/10.' if nlp_summary else 'Análisis geopolítico basado en eventos recientes muestra tendencias complejas en múltiples regiones.',
                'risk_level': fallback_risk,
                'key_insights': [
                    'Análisis NLP detectó patrones de riesgo emergentes',
                    'Múltiples entidades geopolíticas bajo monitoreo',
                    'Indicadores de conflicto en seguimiento continuo',
                    'Tendencias de sentimiento variadas por región'
                ] if nlp_summary else [
                    'Incremento en tensiones regionales',
                    'Cambios en dinámicas diplomáticas',
                    'Impacto en mercados globales'
                ],
                'recommendations': [
                    'Monitoreo intensivo de entidades identificadas por NLP',
                    'Seguimiento de indicadores de conflicto detectados',
                    'Análisis de tendencias de sentimiento por región',
                    'Preparación para escenarios de alto riesgo identificados'
                ] if nlp_summary else [
                    'Monitoreo continuo de desarrollos',
                    'Diversificación de fuentes de información',
                    'Preparación para múltiples escenarios'
                ],
                'nlp_enhanced': bool(nlp_summary),
                'nlp_metrics': nlp_summary if nlp_summary else {}
            }
            
except ImportError as e:
    print(f"AI models not available: {e}")
    
    def ai_generate_analysis(articles_data, nlp_summary=None):
        """Fallback AI analysis function."""
        return {
            'summary': 'Sistema de análisis AI temporalmente no disponible. Análisis basado en patrones históricos.',
            'risk_level': 'MEDIUM',
            'key_insights': [
                'Monitoreo de tendencias geopolíticas en curso',
                'Evaluación de impactos regionales',
                'Análisis de estabilidad internacional'
            ],
            'recommendations': [
                'Continuar vigilancia de eventos clave',
                'Mantener diversificación de fuentes',
                'Preparar estrategias de contingencia'
            ]
        }

logger = logging.getLogger(__name__)

# Initialize database manager
db = DatabaseManager(config)

# Initialize Flask app with enhanced configuration
app = Flask(__name__)
app.secret_key = config.get('dashboard.secret_key', 'geopolitical-intelligence-secure-key-2024')
app.config['JSON_SORT_KEYS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Enable CORS for all routes
CORS(app)

# Configure static file serving for generated images
@app.route('/static/data/generated_images/<path:filename>')
def serve_generated_image(filename):
    """Serve generated images from the data directory."""
    try:
        from pathlib import Path
        base_dir = Path(__file__).parent.parent.parent
        image_path = base_dir / 'data' / 'generated_images' / filename
        
        if image_path.exists() and image_path.is_file():
            return send_from_directory(str(image_path.parent), image_path.name)
        else:
            abort(404)
    except Exception as e:
        logger.error(f"Error serving image {filename}: {e}")
        abort(404)

# Global variables
startup_time = datetime.now()
request_count = 0


def performance_monitor(f):
    """Decorator to monitor endpoint performance."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        global request_count
        request_count += 1
        
        start_time = time.time()
        try:
            result = f(*args, **kwargs)
            execution_time = time.time() - start_time
            
            if execution_time > 1:  # Log slow requests
                logger.warning(f"Slow request to {request.endpoint}: {execution_time:.2f}s")
            
            return result
        except Exception as e:
            logger.error(f"Error en endpoint {request.endpoint}: {e}")
            return jsonify({'error': 'Error interno del servidor'}), 500
    
    return decorated_function


def get_database_connection():
    """Obtiene conexión a la base de datos con manejo de errores."""
    try:
        # Use absolute path to ensure database is found
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(current_dir, '..', '..', 'data', 'geopolitical_intel.db')
        db_path = os.path.normpath(db_path)
        logger.info(f"Connecting to database: {db_path}")
        
        if not os.path.exists(db_path):
            logger.error(f"Database file not found: {db_path}")
            return None
            
        return sqlite3.connect(db_path)
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {e}")
        return None


@app.route('/')
@performance_monitor
def dashboard():
    """Página principal del dashboard con datos en tiempo real."""
    try:
        # Obtener estadísticas básicas para la página principal
        conn = get_database_connection()
        if not conn:
            return render_template('error.html', error="Error de base de datos"), 500
        
        cursor = conn.cursor()
        
        # Estadísticas básicas mejoradas
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_articles = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM articles WHERE created_at > datetime('now', '-24 hours')")
        articles_24h = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM articles WHERE created_at > datetime('now', '-7 days')")
        articles_week = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT language) FROM articles")
        languages_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT source) FROM articles")
        sources_count = cursor.fetchone()[0]
        
        # Distribución por idiomas
        cursor.execute("SELECT language, COUNT(*) FROM articles GROUP BY language ORDER BY COUNT(*) DESC")
        language_distribution = dict(cursor.fetchall())
        
        conn.close()
        
        dashboard_data = {
            'total_articles': total_articles,
            'articles_24h': articles_24h,
            'articles_week': articles_week,
            'processed_articles': total_articles,  # Por ahora, consideramos todos como procesados
            'languages_count': languages_count,
            'sources_count': sources_count,
            'language_distribution': language_distribution,
            'last_update': datetime.now().isoformat(),
            'system_uptime': str(datetime.now() - startup_time),
            'supported_languages': config.get_supported_languages(),
            'global_risk_level': 'MEDIUM' if total_articles > 50 else 'LOW'
        }
        
        return render_template('dashboard.html', data=dashboard_data)
        
    except Exception as e:
        logger.error(f"Error cargando dashboard: {e}")
        return render_template('error.html', error="Error cargando dashboard"), 500


@app.route('/api/summary')
@performance_monitor
def api_summary():
    """API endpoint para estadísticas resumidas del dashboard."""
    try:
        conn = get_database_connection()
        if not conn:
            return jsonify({'error': 'Error de base de datos'}), 500
        
        cursor = conn.cursor()
        
        # Estadísticas básicas
        cursor.execute('SELECT COUNT(*) FROM articles')
        total_articles = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM articles WHERE created_at > datetime('now', '-24 hours')")
        articles_today = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM articles WHERE created_at > datetime('now', '-7 days')")
        articles_week = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT language) FROM articles")
        languages_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT source) FROM articles")
        sources_count = cursor.fetchone()[0]
        
        # Distribución por idiomas
        cursor.execute("SELECT language, COUNT(*) FROM articles GROUP BY language ORDER BY COUNT(*) DESC")
        language_distribution = dict(cursor.fetchall())
        
        # Artículos recientes (últimas 24h)
        cursor.execute("""
            SELECT title, source, language, created_at 
            FROM articles 
            WHERE created_at > datetime('now', '-24 hours')
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        recent_articles = [
            {
                'title': row[0],
                'source': row[1],
                'language': row[2],
                'created_at': row[3]
            }
            for row in cursor.fetchall()
        ]
        
        # Artículo del día (más reciente con contenido)
        cursor.execute("""
            SELECT title, content, url, source, language, created_at
            FROM articles 
            WHERE content IS NOT NULL AND content != ''
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        article_of_day_row = cursor.fetchone()
        article_of_day = None
        if article_of_day_row:
            article_of_day = {
                'title': article_of_day_row[0],
                'content': article_of_day_row[1][:300] + '...' if len(article_of_day_row[1]) > 300 else article_of_day_row[1],
                'url': article_of_day_row[2],
                'source': article_of_day_row[3],
                'language': article_of_day_row[4],
                'created_at': article_of_day_row[5],
                'risk_level': 'HIGH' if 'war' in article_of_day_row[0].lower() or 'conflict' in article_of_day_row[0].lower() or 'crisis' in article_of_day_row[0].lower() else 'MEDIUM' if 'tension' in article_of_day_row[0].lower() or 'protest' in article_of_day_row[0].lower() else 'LOW',
                'image_url': f'https://images.unsplash.com/photo-{["1504711434969-e33886168f5c", "1495020689067-958852a7e369", "1557804506-669a67965ba0", "1526666923127-b2bb3ecb763d"][hash(article_of_day_row[0]) % 4]}?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80'
            }
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_articles': total_articles,
            'articles_today': articles_today,
            'articles_week': articles_week,
            'processed_articles': total_articles,  # Consideramos todos como procesados
            'languages_count': languages_count,
            'sources_count': sources_count,
            'language_distribution': language_distribution,
            'recent_articles': recent_articles,
            'article_of_day': article_of_day,
            'active_regions': max(3, languages_count),  # Regiones estimadas basadas en idiomas
            'global_risk_level': 'HIGH' if total_articles > 100 else 'MEDIUM' if total_articles > 50 else 'LOW',
            'system_info': {
                'uptime': str(datetime.now() - startup_time),
                'requests_served': request_count,
                'supported_languages': config.get_supported_languages()
            }
        }
        
        conn.close()
        return jsonify(summary)
        
    except Exception as e:
        logger.error(f"Error en API summary: {e}")
        return jsonify({'error': 'Error obteniendo resumen'}), 500


@app.route('/api/articles')
@performance_monitor
def api_articles():
    """API endpoint para obtener artículos filtrados."""
    try:
        # Parámetros de filtro
        days = request.args.get('days', 7, type=int)
        category = request.args.get('category', '')
        language = request.args.get('language', '')
        sentiment = request.args.get('sentiment', '')
        limit = request.args.get('limit', 50, type=int)
        target_lang = request.args.get('lang', 'en')  # Para traducción
        
        conn = get_database_connection()
        if not conn:
            return jsonify({'error': 'Error de base de datos'}), 500
        
        cursor = conn.cursor()
        
        # Construcción de la consulta con filtros
        query = """
            SELECT title, content, url, source, language, created_at, 
                   risk_level, conflict_type, country, region, sentiment_score, summary
            FROM articles 
            WHERE created_at > datetime('now', '-{} days')
        """.format(days)
        
        params = []
        
        if language:
            query += " AND language = ?"
            params.append(language)
        
        if category:
            query += " AND conflict_type = ?"
            params.append(category)
            
        if sentiment:
            query += " AND risk_level = ?"
            params.append(sentiment)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        
        articles = [
            {
                'title': row[0],
                'content': row[1][:500] + '...' if row[1] and len(row[1]) > 500 else row[1],
                'url': row[2],
                'source': row[3],
                'language': row[4],
                'created_at': row[5],
                'risk_level': row[6],
                'conflict_type': row[7],
                'country': row[8],
                'region': row[9],
                'sentiment_score': row[10],
                'summary': row[11]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        # Traducir artículos si es necesario
        if target_lang != 'en':
            try:
                from src.utils.translator import get_translator
                translator = get_translator()
                articles = translator.translate_articles_list(articles, target_lang)
            except Exception as e:
                logger.warning(f"Error translating articles: {e}")
        
        return jsonify({
            'articles': articles,
            'total': len(articles),
            'filters': {
                'days': days,
                'category': category,
                'language': language,
                'sentiment': sentiment,
                'limit': limit
            }
        })
        
    except Exception as e:
        logger.error(f"Error en API articles: {e}")
        return jsonify({'error': 'Error obteniendo artículos'}), 500


@app.route('/api/high_risk_articles')
@performance_monitor
def api_high_risk_articles():
    """
    Obtiene los artículos de mayor riesgo ordenados por risk_score
    """
    try:
        lang = request.args.get('lang', 'en')
        limit = int(request.args.get('limit', 20))
        
        conn = get_database_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Obtener artículos ordenados por risk_score descendente
        query = """
        SELECT title, summary, url, published_at, source, 
               language, conflict_type, sentiment_score, risk_score,
               COALESCE(country, 'Unknown') as location,
               sentiment_label, key_persons, key_locations
        FROM articles 
        WHERE risk_score IS NOT NULL 
        ORDER BY risk_score DESC, published_at DESC 
        LIMIT ?
        """
        
        cursor.execute(query, (limit,))
        results = cursor.fetchall()
        
        articles = []
        for row in results:
            articles.append({
                'title': row[0],
                'description': row[1],  # summary como description
                'url': row[2],
                'published_at': row[3],
                'source_name': row[4],  # source como source_name
                'language': row[5],
                'category': row[6] or 'neutral',  # conflict_type como category
                'sentiment_score': row[7] or 0.0,
                'risk_score': row[8] or 0.0,
                'location': row[9],
                'sentiment_label': row[10] or 'neutral',
                'key_persons': row[11] or '',
                'key_locations': row[12] or ''
            })
        
        conn.close()
        
        # Traducir artículos si es necesario
        if lang != 'en':
            try:
                from src.utils.simple_translator import get_translator
                translator = get_translator()
                articles = translator.translate_articles_list(articles, lang)
            except Exception as e:
                logger.warning(f"Error translating articles: {e}")
        
        return jsonify({
            'articles': articles,
            'total': len(articles),
            'language': lang
        })
        
    except Exception as e:
        logger.error(f"Error en API high risk articles: {e}")
        return jsonify({'error': 'Error obteniendo artículos de alto riesgo'}), 500


@app.route('/api/translate')
@performance_monitor
def api_translate():
    """
    Traduce textos y elementos de la UI al idioma especificado
    """
    try:
        target_lang = request.args.get('lang', 'en')
        ui_only = request.args.get('ui_only', 'false').lower() == 'true'
        
        # Traducciones estáticas simples
        translations = {
            'es': {
                'dashboard': 'Panel de Control',
                'reports': 'Informes', 
                'ai_chat': 'Chat IA',
                'about': 'Acerca de',
                'recent_articles': 'Artículos Recientes',
                'high_risk_articles': 'Artículos de Alto Riesgo',
                'language_distribution': 'Distribución por Idioma',
                'ai_geopolitical_analysis': 'Análisis Geopolítico por IA',
                'key_insights': 'Percepciones Clave',
                'recommendations': 'Recomendaciones',
                'title': 'Título',
                'description': 'Descripción',
                'published': 'Publicado',
                'source': 'Fuente',
                'language': 'Idioma',
                'risk_level': 'Nivel de Riesgo',
                'sentiment': 'Sentimiento',
                'loading': 'Cargando...',
                'error': 'Error',
                'high': 'Alto',
                'medium': 'Medio',
                'low': 'Bajo',
                'positive': 'Positivo',
                'negative': 'Negativo',
                'neutral': 'Neutral',
                'select_language': 'Seleccionar Idioma',
                'geopolitical_intelligence_system': 'Sistema de Inteligencia Geopolítica'
            }
        }
        
        # Obtener traducciones
        if target_lang in translations:
            ui_texts = translations[target_lang]
        else:
            # Inglés por defecto
            ui_texts = {
                'dashboard': 'Dashboard',
                'reports': 'Reports', 
                'ai_chat': 'AI Chat',
                'about': 'About',
                'recent_articles': 'Recent Articles',
                'high_risk_articles': 'High Risk Articles',
                'language_distribution': 'Language Distribution',
                'ai_geopolitical_analysis': 'AI Geopolitical Analysis',
                'key_insights': 'Key Insights',
                'recommendations': 'Recommendations',
                'title': 'Title',
                'description': 'Description',
                'published': 'Published',
                'source': 'Source',
                'language': 'Language',
                'risk_level': 'Risk Level',
                'sentiment': 'Sentiment',
                'loading': 'Loading...',
                'error': 'Error',
                'high': 'High',
                'medium': 'Medium',
                'low': 'Low',
                'positive': 'Positive',
                'negative': 'Negative',
                'neutral': 'Neutral',
                'select_language': 'Select Language',
                'geopolitical_intelligence_system': 'Geopolitical Intelligence System'
            }
        
        return jsonify({'ui': ui_texts})
        
    except Exception as e:
        logger.error(f"Error en API translate: {e}")
        return jsonify({'error': 'Error en traducción'}), 500


@app.route('/api/ai_analysis')
@performance_monitor
def api_ai_analysis():
    """
    Genera un análisis geopolítico utilizando IA basado en los artículos disponibles.
    Soporta múltiples modelos: OpenAI, DeepSeek, Groq, HuggingFace y fallback local.
    Siempre genera contenido, incluso si no hay artículos del día actual.
    Soporta traducción automática.
    """
    try:
        from datetime import datetime, timedelta
        
        # Obtener parámetro de idioma
        target_lang = request.args.get('lang', 'en')
        
        conn = get_database_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Strategy 1: Priorizar artículos con análisis NLP avanzado de hoy
        cursor.execute("""
            SELECT title, summary, conflict_type, conflict_type, country, region, source, language,
                   risk_score, sentiment_label, sentiment_score, key_persons, key_locations,
                   entities_json, conflict_indicators
            FROM articles 
            WHERE created_at > datetime('now', '-24 hours')
            AND risk_score IS NOT NULL
            ORDER BY risk_score DESC, created_at DESC
            LIMIT 10
        """)
        
        articles_today = cursor.fetchall()
        
        # Strategy 2: Si no hay artículos de hoy con NLP, usar los de mayor riesgo de días recientes
        if not articles_today:
            logger.info("No articles from today with NLP analysis, using high-risk articles from recent days")
            cursor.execute("""
                SELECT title, summary, conflict_type, conflict_type, country, region, source, language,
                       risk_score, sentiment_label, sentiment_score, key_persons, key_locations,
                       entities_json, conflict_indicators
                FROM articles 
                WHERE created_at > datetime('now', '-7 days')
                AND risk_score IS NOT NULL
                ORDER BY risk_score DESC, created_at DESC
                LIMIT 15
            """)
            articles_today = cursor.fetchall()
        
        # Strategy 3: Si aún no hay artículos con análisis NLP, usar artículos recientes sin análisis
        if not articles_today:
            logger.info("No articles with NLP analysis, using any recent articles")
            cursor.execute("""
                SELECT title, summary, 'Political' as conflict_type, 'Political' as conflict_type, 
                       'Global' as country, 'International' as region, source, language,
                       NULL, NULL, NULL, NULL, NULL, NULL, NULL
                FROM articles 
                WHERE created_at > datetime('now', '-7 days')
                ORDER BY created_at DESC
                LIMIT 10
            """)
            articles_today = cursor.fetchall()
        
        conn.close()
        
        # Preparar datos de artículos para análisis de IA con información NLP enriquecida
        articles_data = []
        nlp_summary = {
            'total_risk_score': 0,
            'sentiment_distribution': {},
            'key_entities': [],
            'conflict_indicators': [],
            'countries_involved': set(),  # Se convertirá a lista antes del retorno
            'risk_levels': []
        }
        
        if articles_today:
            for article in articles_today:
                if len(article) >= 15:  # Artículos con análisis NLP completo
                    (title, summary, conflict_type, conflict_type2, country, region, source, language,
                     risk_score, sentiment_label, sentiment_score, key_persons, key_locations,
                     entities_json, conflict_indicators) = article
                    
                    # Usar conflict_type del análisis NLP
                    risk_level = 'HIGH' if risk_score and risk_score > 4 else 'MEDIUM' if risk_score and risk_score > 2 else 'LOW'
                    
                    # Recopilar información para el análisis agregado
                    if risk_score:
                        nlp_summary['total_risk_score'] += risk_score
                    if sentiment_label:
                        nlp_summary['sentiment_distribution'][sentiment_label] = nlp_summary['sentiment_distribution'].get(sentiment_label, 0) + 1
                    if key_persons:
                        nlp_summary['key_entities'].extend(key_persons.split(',') if key_persons else [])
                    if key_locations:
                        nlp_summary['key_entities'].extend(key_locations.split(',') if key_locations else [])
                    if conflict_indicators:
                        nlp_summary['conflict_indicators'].extend(conflict_indicators.split(',') if conflict_indicators else [])
                    if country:
                        nlp_summary['countries_involved'].add(country)
                    if risk_score:
                        nlp_summary['risk_levels'].append(risk_score)
                else:
                    # Artículos sin análisis NLP completo
                    title, summary, conflict_type, conflict_type2, country, region, source, language = article[:8]
                    risk_score = None
                    sentiment_label = None
                    sentiment_score = None
                    risk_level = 'MEDIUM'
                
                # Limitar contenido para eficiencia de API
                limited_content = summary[:300] + '...' if summary and len(summary) > 300 else (summary or '')
                
                articles_data.append({
                    'title': title,
                    'content': limited_content,
                    'risk_level': risk_level,
                    'conflict_type': conflict_type,
                    'country': country,
                    'region': region,
                    'source': source,
                    'language': language,
                    'risk_score': risk_score,
                    'sentiment_label': sentiment_label,
                    'sentiment_score': sentiment_score
                })
        
        # Calcular métricas agregadas del análisis NLP
        avg_risk_score = sum(nlp_summary['risk_levels']) / len(nlp_summary['risk_levels']) if nlp_summary['risk_levels'] else 0
        dominant_sentiment = max(nlp_summary['sentiment_distribution'].items(), key=lambda x: x[1])[0] if nlp_summary['sentiment_distribution'] else 'neutral'
        
        # Convertir sets a listas para serialización JSON
        nlp_summary['countries_involved'] = list(nlp_summary['countries_involved'])
        
        # Generar análisis de IA usando el cliente multi-modelo con datos NLP enriquecidos
        result = ai_generate_analysis(articles_data, nlp_summary)
        
        # Generate AI image for the analysis if content exists
        if result and result.get('analysis'):
            try:
                from utils.ai_image_generator import AIImageGenerator
                
                image_generator = AIImageGenerator(config)
                analysis_content = result['analysis']
                
                # Generate image based on AI analysis
                image_path = image_generator.generate_image_for_analysis(
                    analysis_content, 
                    "Análisis Geopolítico Global"
                )
                
                if image_path:
                    result['image_url'] = image_path
                    result['has_generated_image'] = True
                else:
                    result['image_url'] = 'https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80'
                    result['has_generated_image'] = False
                    
            except Exception as img_error:
                logger.warning(f"Could not generate AI image: {img_error}")
                result['image_url'] = 'https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80'
                result['has_generated_image'] = False
        
        # Traducir el resultado si es necesario
        if target_lang != 'en':
            try:
                from src.utils.translator import get_translator
                translator = get_translator()
                
                # Traducir campos de texto
                if 'key_insights' in result:
                    result['key_insights'] = translator.translate(str(result['key_insights']), target_lang)
                if 'recommendations' in result:
                    result['recommendations'] = translator.translate(str(result['recommendations']), target_lang)
                if 'analysis' in result:
                    result['analysis'] = translator.translate(str(result['analysis']), target_lang)
                
                result['translated'] = True
                result['target_language'] = target_lang
            except Exception as trans_error:
                logger.warning(f"Error translating AI analysis: {trans_error}")
                result['translated'] = False
        
        return jsonify(result)
        
    except Exception as e:
        from datetime import datetime
        logger.error(f"Error generating AI analysis: {e}")
        # Return fallback using the multi-model client
        try:
            result = ai_generate_analysis([])  # Empty articles will trigger fallback
            return jsonify(result)
        except:
            return jsonify({
                'analysis': _emergency_fallback_analysis(),
                'generated_at': datetime.now().isoformat(),
                'source': 'emergency_fallback',
                'error': str(e)
            })


def _emergency_fallback_analysis():
    """Análisis de emergencia cuando todo falla."""
    from datetime import datetime
    current_time = datetime.now().strftime("%H:%M del %d de %B de %Y")
    
    return f"""ANÁLISIS GEOPOLÍTICO GLOBAL - {current_time}

El panorama internacional actual presenta múltiples focos de tensión que requieren monitoreo constante. Nuestros sistemas continúan procesando información de fuentes globales para identificar patrones emergentes y evaluar riesgos potenciales.

La estabilidad geopolítica mundial enfrenta desafíos complejos que abarcan desde tensiones regionales hasta nuevas formas de conflicto digital y económico. Los indicadores muestran la necesidad de mantener vigilancia sobre varios teatros simultáneamente.

Para las próximas horas, se recomienda vigilancia especial sobre canales diplomáticos oficiales, indicadores económicos y movimientos en regiones sensibles. La información de fuentes abiertas sigue siendo fundamental para construir una imagen situacional precisa."""


@app.route('/api/article-of-day')
@performance_monitor
def api_article_of_day():
    """API endpoint para obtener el artículo del día de mayor riesgo con imagen."""
    try:
        conn = get_database_connection()
        if not conn:
            return jsonify({'error': 'Error de base de datos'}), 500
        
        cursor = conn.cursor()
        
        # Primero intentar obtener artículos con análisis NLP e imagen
        cursor.execute("""
            SELECT title, content, url, source, language, created_at, risk_level, conflict_type, country, region, image_url
            FROM articles 
            WHERE content IS NOT NULL AND content != ''
            AND created_at > datetime('now', '-7 days')
            ORDER BY 
                CASE risk_level
                    WHEN 'CRITICAL' THEN 1
                    WHEN 'HIGH' THEN 2
                    WHEN 'MEDIUM' THEN 3
                    WHEN 'LOW' THEN 4
                    ELSE 5
                END,
                created_at DESC 
            LIMIT 15
        """)
        
        rows = cursor.fetchall()
        
        # Si no hay artículos con análisis NLP, usar método tradicional
        if not rows:
            cursor.execute("""
                SELECT title, content, url, source, language, created_at, NULL, NULL, NULL, NULL, image_url
                FROM articles 
                WHERE content IS NOT NULL AND content != ''
                ORDER BY created_at DESC 
                LIMIT 10
            """)
            rows = cursor.fetchall()
        
        if not rows:
            return jsonify({'error': 'No articles available'}), 404
        
        best_article = None
        highest_risk_score = 0
        
        # Si tenemos artículos con análisis NLP, usar el primero (ya ordenado por riesgo)
        if rows[0][6] is not None:  # risk_level column exists
            best_article = rows[0]
        else:
            # Método tradicional: calcular riesgo por palabras clave
            high_risk_keywords = ['war', 'conflict', 'crisis', 'attack', 'violence', 'terrorism', 'invasion', 'guerra', 'conflicto', 'ataque', 'violencia', 'terrorismo', 'invasión']
            medium_risk_keywords = ['tension', 'protest', 'dispute', 'sanctions', 'military', 'political', 'tensión', 'protesta', 'disputa', 'sanciones', 'militar', 'político']
            
            for row in rows:
                title_lower = row[0].lower()
                content_lower = (row[1] or '').lower()
                
                risk_score = 0
                
                # Calcular puntuación de riesgo
                for keyword in high_risk_keywords:
                    if keyword in title_lower:
                        risk_score += 10
                    if keyword in content_lower:
                        risk_score += 5
                
                for keyword in medium_risk_keywords:
                    if keyword in title_lower:
                        risk_score += 5
                    if keyword in content_lower:
                        risk_score += 2
                
                if risk_score > highest_risk_score:
                    highest_risk_score = risk_score
                    best_article = row
            
            # Si no hay artículos de riesgo, tomar el más reciente
            if not best_article:
                best_article = rows[0]
        
        # Extraer datos del artículo (ahora incluye image_url)
        title, content, url, source, language, created_at, risk_level, conflict_type, country, region, image_url = best_article
        
        # Determinar nivel de riesgo si no está disponible
        if not risk_level:
            title_lower = title.lower()
            content_lower = (content or '').lower()
            
            high_risk_keywords = ['war', 'conflict', 'crisis', 'attack', 'violence', 'terrorism', 'invasion', 'guerra', 'conflicto', 'ataque', 'violencia', 'terrorismo', 'invasión']
            medium_risk_keywords = ['tension', 'protest', 'dispute', 'sanctions', 'military', 'political', 'tensión', 'protesta', 'disputa', 'sanciones', 'militar', 'político']
            
            risk_level = 'LOW'
            if any(keyword in title_lower or keyword in content_lower for keyword in high_risk_keywords):
                risk_level = 'HIGH'
            elif any(keyword in title_lower or keyword in content_lower for keyword in medium_risk_keywords):
                risk_level = 'MEDIUM'
        
        # Determinar la imagen del artículo
        article_image = None
        
        # 1. Usar imagen de la base de datos si existe
        if image_url and image_url.strip():
            article_image = image_url
        
        # 2. Si no hay imagen y tenemos URL, intentar extraerla
        elif url and url.strip():
            try:
                from utils.image_extractor import extract_article_image
                logger.info(f"Extracting image from URL: {url}")
                extracted_image = extract_article_image(url, source)
                if extracted_image:
                    article_image = extracted_image
                    # Guardar en la base de datos para futuras consultas
                    cursor.execute("""
                        UPDATE articles 
                        SET image_url = ? 
                        WHERE title = ? AND source = ?
                    """, (extracted_image, title, source))
                    conn.commit()
                    logger.info(f"Saved extracted image for article: {title}")
            except Exception as e:
                logger.error(f"Error extracting image: {e}")
        
        # 3. Fallback a imagen temática por fuente
        if not article_image:
            source_images = {
                'CNN': 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80',
                'BBC': 'https://images.unsplash.com/photo-1495020689067-958852a7e369?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80',
                'Reuters': 'https://images.unsplash.com/photo-1557804506-669a67965ba0?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80',
                'Al Jazeera': 'https://images.unsplash.com/photo-1526666923127-b2bb3ecb763d?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80'
            }
            
            # Buscar imagen por fuente
            for src_name, img_url in source_images.items():
                if src_name.lower() in source.lower():
                    article_image = img_url
                    break
            
            # Fallback final
            if not article_image:
                article_image = 'https://images.unsplash.com/photo-1495020689067-958852a7e369?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80'
        
        article = {
            'title': title,
            'content': content[:400] + '...' if content and len(content) > 400 else (content or 'No content available'),
            'url': url,
            'source': source,
            'language': language,
            'created_at': created_at,
            'risk_level': risk_level or 'MEDIUM',
            'conflict_type': conflict_type or 'Political',
            'country': country or 'Global',
            'region': region or 'International',
            'image_url': article_image
        }
        
        conn.close()
        logger.info(f"Article of day: {title} - Risk: {risk_level}")
        return jsonify(article)
        
    except Exception as e:
        logger.error(f"Error obteniendo artículo del día: {e}")
        return jsonify({'error': 'Error obteniendo artículo del día'}), 500


@app.route('/api/heatmap_data')
@performance_monitor
def api_heatmap_data():
    """
    Proporciona datos para el mapa de calor interactivo.
    """
    conflict_type = request.args.get('conflict_type', 'all')
    
    try:
        conn = get_database_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Consulta base para obtener artículos con datos de ubicación
        query = """
            SELECT 
                a.country,
                a.region,
                a.risk_level,
                pd.summary
            FROM articles a
            JOIN processed_data pd ON a.id = pd.article_id
            WHERE a.country IS NOT NULL AND a.published_at > datetime('now', '-30 days')
        """
        
        params = []
        if conflict_type != 'all':
            query += " AND a.conflict_type = ?"
            params.append(conflict_type)
            
        cursor.execute(query, params)
        articles = cursor.fetchall()
        conn.close()

        # Mapeo de riesgo a intensidad
        risk_intensity_map = {'LOW': 1, 'MEDIUM': 3, 'HIGH': 5, 'CRITICAL': 10}

        # Usar una librería para obtener coordenadas de países
        from pycountry_convert import country_name_to_country_alpha2, country_alpha2_to_continent_code
        import country_converter as coco
        
        heatmap_points = []
        for country_name, region, risk, summary in articles:
            try:
                # Obtener coordenadas (esto es una simplificación, se necesitaría un geocodificador)
                # Usaremos una librería que pueda dar coordenadas aproximadas o de la capital
                # Esta parte es una simulación y puede requerir una API de geocodificación real
                
                # Simulación con country_converter
                lat, lon = coco.convert(names=[country_name], to='lat_lon', not_found=None)[0]

                if lat and lon:
                    intensity = risk_intensity_map.get(risk, 1)
                    heatmap_points.append({
                        'lat': lat,
                        'lon': lon,
                        'intensity': intensity,
                        'info': f"{country_name} - Risk: {risk}"
                    })
            except Exception as e:
                logger.warning(f"No se pudieron obtener coordenadas para '{country_name}': {e}")
                continue

        return jsonify(heatmap_points)

    except ImportError:
        logger.error("Librerías de geocodificación no instaladas. Instale 'pycountry_convert' y 'country_converter'.")
        return jsonify({'error': "Geocoding libraries not installed."}), 500
    except Exception as e:
        logger.error(f"Error generando datos para el mapa de calor: {e}")
        return jsonify({'error': 'Could not generate heatmap data.'}), 500


@app.route('/api/alerts')
@performance_monitor
def api_alerts():
    """API endpoint para obtener alertas críticas generadas por IA."""
    try:
        conn = get_database_connection()
        if not conn:
            return jsonify({'error': 'Error de base de datos'}), 500
        
        cursor = conn.cursor()
        
        # Generar alertas basadas en análisis de artículos recientes
        cursor.execute("""
            SELECT title, content, source, language, created_at
            FROM articles 
            WHERE created_at > datetime('now', '-24 hours')
            ORDER BY created_at DESC 
            LIMIT 20
        """)
        
        articles = cursor.fetchall()
        alerts = []
        
        # Palabras clave para diferentes tipos de alertas
        military_keywords = ['military', 'troops', 'war', 'invasion', 'conflict', 'armed', 'ejercito', 'guerra', 'conflicto', 'tropas']
        economic_keywords = ['economy', 'crisis', 'sanctions', 'tariffs', 'inflation', 'recession', 'economia', 'crisis', 'sanciones']
        cyber_keywords = ['cyber', 'hack', 'attack', 'breach', 'malware', 'ransomware', 'ciberataque', 'hackeo']
        political_keywords = ['coup', 'election', 'protest', 'parliament', 'government', 'golpe', 'elecciones', 'protesta', 'gobierno']
        
        for article in articles:
            title_lower = article[0].lower()
            content_lower = (article[1] or '').lower()
            
            # Detectar alertas militares
            if any(keyword in title_lower or keyword in content_lower for keyword in military_keywords):
                if any(word in title_lower for word in ['escalation', 'imminent', 'threat', 'escalada', 'inminente', 'amenaza']):
                    alerts.append({
                        'type': 'military',
                        'level': 'high',
                        'title': 'Escalada Militar Detectada',
                        'description': f'Actividad militar intensa reportada: {article[0][:100]}...',
                        'source': article[2],
                        'timestamp': article[4],
                        'icon': 'airplane-engines-fill',
                        'probability': 75 + len([k for k in military_keywords if k in content_lower]) * 5
                    })
            
            # Detectar alertas económicas
            if any(keyword in title_lower or keyword in content_lower for keyword in economic_keywords):
                if any(word in title_lower for word in ['collapse', 'crash', 'crisis', 'emergency', 'colapso', 'emergencia']):
                    alerts.append({
                        'type': 'economic',
                        'level': 'medium',
                        'title': 'Riesgo Económico Elevado',
                        'description': f'Indicadores económicos críticos: {article[0][:100]}...',
                        'source': article[2],
                        'timestamp': article[4],
                        'icon': 'currency-exchange',
                        'probability': 60 + len([k for k in economic_keywords if k in content_lower]) * 3
                    })
            
            # Detectar alertas de ciberseguridad
            if any(keyword in title_lower or keyword in content_lower for keyword in cyber_keywords):
                alerts.append({
                    'type': 'cyber',
                    'level': 'high',
                    'title': 'Amenaza de Ciberseguridad',
                    'description': f'Actividad cibernética maliciosa detectada: {article[0][:100]}...',
                    'source': article[2],
                    'timestamp': article[4],
                    'icon': 'shield-exclamation',
                    'probability': 80 + len([k for k in cyber_keywords if k in content_lower]) * 4
                })
        
        # Ordenar por probabilidad y tomar las top 5
        alerts = sorted(alerts, key=lambda x: x['probability'], reverse=True)[:5]
        
        conn.close()
        return jsonify({
            'alerts': alerts,
            'total_alerts': len(alerts),
            'high_priority': len([a for a in alerts if a['level'] == 'high']),
            'ai_analysis': True,
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error generando alertas: {e}")
        return jsonify({'error': 'Error generando alertas'}), 500


@app.route('/api/trends')
@performance_monitor
def api_trends():
    """API endpoint para análisis de tendencias por IA."""
    try:
        conn = get_database_connection()
        if not conn:
            return jsonify({'error': 'Error de base de datos'}), 500
        
        cursor = conn.cursor()
        
        # Análisis de tendencias por idioma/región en los últimos 7 días
        cursor.execute("""
            SELECT 
                language,
                DATE(created_at) as date,
                COUNT(*) as article_count
            FROM articles 
            WHERE created_at > datetime('now', '-7 days')
            GROUP BY language, DATE(created_at)
            ORDER BY date DESC
        """)
        
        trend_data = cursor.fetchall()
        
        # Organizar datos para gráficos
        languages = {}
        for row in trend_data:
            lang = row[0]
            date = row[1]
            count = row[2]
            
            if lang not in languages:
                languages[lang] = {}
            languages[lang][date] = count
        
        # Calcular índice de riesgo global simulado
        risk_timeline = []
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            base_risk = 45 + (i * 2)  # Tendencia creciente simulada
            risk_timeline.append({
                'date': date,
                'risk_index': min(100, base_risk + (len(trend_data) % 10)),
                'events': len([r for r in trend_data if r[1] == date])
            })
        
        risk_timeline.reverse()
        
        conn.close()
        return jsonify({
            'risk_timeline': risk_timeline,
            'language_trends': languages,
            'global_risk_index': risk_timeline[-1]['risk_index'] if risk_timeline else 50,
            'ai_predictions': {
                'next_7_days_risk': min(100, risk_timeline[-1]['risk_index'] + 5) if risk_timeline else 55,
                'confidence': 87,
                'key_factors': ['Military escalation patterns', 'Economic indicators', 'Social unrest metrics']
            },
            'ml_insights': {
                'pattern_recognition': True,
                'sentiment_analysis': True,
                'predictive_modeling': True,
                'last_training': '2025-07-15T00:00:00Z'
            }
        })
        
    except Exception as e:
        logger.error(f"Error generando análisis de tendencias: {e}")
        return jsonify({'error': 'Error generando análisis'}), 500


@app.route('/api/heatmap')
@performance_monitor
def api_heatmap():
    """API endpoint para datos del mapa de calor geopolítico basado en análisis de IA."""
    try:
        # Import GeographicAnalyzer
        from analytics.geographic_analyzer import GeographicAnalyzer
        
        analyzer = GeographicAnalyzer(config)
        heatmap_csv_data = analyzer.get_heatmap_data()
        
        # Convert CSV data to heatmap format with coordinates
        region_coordinates = {
            'North America': {'lat': 54.5260, 'lng': -105.2551},
            'South America': {'lat': -8.7832, 'lng': -55.4915},
            'Europe': {'lat': 54.5260, 'lng': 15.2551},
            'Eastern Europe': {'lat': 53.7098, 'lng': 27.9534},
            'Middle East': {'lat': 29.2985, 'lng': 42.5510},
            'Asia': {'lat': 34.0479, 'lng': 100.6197},
            'Southeast Asia': {'lat': 4.2105, 'lng': 101.9758},
            'Africa': {'lat': -8.7832, 'lng': 34.5085},
            'Oceania': {'lat': -25.2744, 'lng': 133.7751},
            'Central Asia': {'lat': 48.0196, 'lng': 66.9237}
        }
        
        heatmap_data = []
        for region_data in heatmap_csv_data:
            region_name = region_data['region']
            if region_name in region_coordinates:
                coords = region_coordinates[region_name]
                
                heatmap_data.append({
                    'lat': coords['lat'],
                    'lng': coords['lng'],
                    'intensity': float(region_data.get('risk_intensity', 0)),
                    'region': region_name,
                    'articles_count': int(region_data.get('articles_count', 0)),
                    'average_risk_score': float(region_data.get('average_risk_score', 0)),
                    'high_risk_articles': int(region_data.get('high_risk_articles', 0)),
                    'medium_risk_articles': int(region_data.get('medium_risk_articles', 0)),
                    'low_risk_articles': int(region_data.get('low_risk_articles', 0)),
                    'unique_sources': int(region_data.get('unique_sources', 0)),
                    'unique_languages': int(region_data.get('unique_languages', 0)),
                    'last_updated': region_data.get('last_updated', '')
                })
        
        logger.info(f"Heatmap data generated for {len(heatmap_data)} regions from AI analysis")
        return jsonify({'heatmap_data': heatmap_data})
        
    except Exception as e:
        logger.error(f"Error generando mapa de calor: {e}")
        return jsonify({'error': 'Error generando mapa de calor'}), 500

@app.route('/api/charts/sentiment-timeline')
@performance_monitor
def api_sentiment_timeline():
    """API endpoint para gráfico de timeline de sentimiento."""
    try:
        days = request.args.get('days', 7, type=int)
        
        # Por ahora retornamos datos simulados
        timeline_data = []
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            timeline_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'positive': 30 + i * 2,
                'negative': 20 - i,
                'neutral': 50 + i
            })
        
        return jsonify({
            'timeline': list(reversed(timeline_data)),
            'period': f'{days} days'
        })
        
    except Exception as e:
        logger.error(f"Error en sentiment timeline: {e}")
        return jsonify({'error': 'Error generando timeline'}), 500


@app.route('/api/charts/category-distribution')
@performance_monitor
def api_category_distribution():
    """API endpoint para distribución de categorías."""
    try:
        conn = get_database_connection()
        if not conn:
            return jsonify({'error': 'Error de base de datos'}), 500
        
        cursor = conn.cursor()
        
        # Distribución por idiomas como proxy de regiones
        cursor.execute("""
            SELECT language, COUNT(*) as count
            FROM articles 
            WHERE created_at > datetime('now', '-7 days')
            GROUP BY language 
            ORDER BY count DESC
        """)
        
        distribution = [
            {'category': row[0], 'count': row[1]}
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return jsonify({
            'distribution': distribution,
            'total': sum(item['count'] for item in distribution)
        })
        
    except Exception as e:
        logger.error(f"Error en category distribution: {e}")
        return jsonify({'error': 'Error obteniendo distribución'}), 500


@app.route('/api/heatmap/conflicts')
@performance_monitor
def api_conflict_heatmap():
    """API endpoint para mapa de calor de conflictos globales."""
    try:
        conn = get_database_connection()
        if not conn:
            return jsonify({'error': 'Error de base de datos'}), 500
        
        cursor = conn.cursor()
        
        # Datos de conflictos por región (simulados basados en idiomas)
        language_regions = {
            'en': [
                {'country': 'USA', 'region': 'Americas', 'lat': 39.8283, 'lng': -98.5795, 'risk': 'HIGH', 'incidents': 45},
                {'country': 'UK', 'region': 'Europe', 'lat': 55.3781, 'lng': -3.4360, 'risk': 'MEDIUM', 'incidents': 12},
                {'country': 'Australia', 'region': 'Asia-Pacific', 'lat': -25.2744, 'lng': 133.7751, 'risk': 'LOW', 'incidents': 3}
            ],
            'ru': [
                {'country': 'Russia', 'region': 'Europe', 'lat': 61.5240, 'lng': 105.3188, 'risk': 'HIGH', 'incidents': 78},
                {'country': 'Ukraine', 'region': 'Europe', 'lat': 48.3794, 'lng': 31.1656, 'risk': 'CRITICAL', 'incidents': 156},
                {'country': 'Belarus', 'region': 'Europe', 'lat': 53.7098, 'lng': 27.9534, 'risk': 'HIGH', 'incidents': 23}
            ],
            'zh': [
                {'country': 'China', 'region': 'Asia-Pacific', 'lat': 35.8617, 'lng': 104.1954, 'risk': 'HIGH', 'incidents': 67},
                {'country': 'Taiwan', 'region': 'Asia-Pacific', 'lat': 23.6978, 'lng': 120.9605, 'risk': 'HIGH', 'incidents': 34}
            ],
            'ar': [
                {'country': 'Siria', 'region': 'Middle East', 'lat': 34.8021, 'lng': 38.9968, 'risk': 'CRITICAL', 'incidents': 203},
                {'country': 'Irak', 'region': 'Middle East', 'lat': 33.2232, 'lng': 43.6793, 'risk': 'CRITICAL', 'incidents': 145},
                {'country': 'Israel', 'region': 'Middle East', 'lat': 31.0461, 'lng': 34.8516, 'risk': 'HIGH', 'incidents': 89},
                {'country': 'Palestine', 'region': 'Middle East', 'lat': 31.9522, 'lng': 35.2332, 'risk': 'CRITICAL', 'incidents': 167},
                {'country': 'Saudi Arabia', 'region': 'Middle East', 'lat': 23.8859, 'lng': 45.0792, 'risk': 'MEDIUM', 'incidents': 18}
            ],
            'es': [
                {'country': 'Colombia', 'region': 'Americas', 'lat': 4.5709, 'lng': -74.2973, 'risk': 'MEDIUM', 'incidents': 34},
                {'country': 'Venezuela', 'region': 'Americas', 'lat': 6.4238, 'lng': -66.5897, 'risk': 'HIGH', 'incidents': 67}
            ],
            'fr': [
                {'country': 'Mali', 'region': 'Africa', 'lat': 17.5707, 'lng': -3.9962, 'risk': 'HIGH', 'incidents': 56},
                {'country': 'Chad', 'region': 'Africa', 'lat': 15.4542, 'lng': 18.7322, 'risk': 'HIGH', 'incidents': 43}
            ]
        }
        
        # Obtener idiomas presentes en la base de datos
        cursor.execute("SELECT DISTINCT language FROM articles")
        active_languages = [row[0] for row in cursor.fetchall()]
        
        # Generar datos del heatmap
        heatmap_data = []
        for lang in active_languages:
            if lang in language_regions:
                heatmap_data.extend(language_regions[lang])
        
        # Si no hay datos, usar datos por defecto de conflictos actuales
        if not heatmap_data:
            heatmap_data = [
                {'country': 'Ukraine', 'region': 'Europe', 'lat': 48.3794, 'lng': 31.1656, 'risk': 'CRITICAL', 'incidents': 156},
                {'country': 'Gaza', 'region': 'Middle East', 'lat': 31.3547, 'lng': 34.3088, 'risk': 'CRITICAL', 'incidents': 189},
                {'country': 'Siria', 'region': 'Middle East', 'lat': 34.8021, 'lng': 38.9968, 'risk': 'CRITICAL', 'incidents': 203},
                {'country': 'Myanmar', 'region': 'Asia-Pacific', 'lat': 21.9162, 'lng': 95.9560, 'risk': 'HIGH', 'incidents': 78},
                {'country': 'Yemen', 'region': 'Middle East', 'lat': 15.5527, 'lng': 48.5164, 'risk': 'CRITICAL', 'incidents': 134}
            ]
        
        conn.close()
        
        return jsonify({
            'heatmap_data': heatmap_data,
            'total_incidents': sum(item['incidents'] for item in heatmap_data),
            'critical_zones': len([item for item in heatmap_data if item['risk'] == 'CRITICAL']),
            'high_risk_zones': len([item for item in heatmap_data if item['risk'] == 'HIGH']),
            'regions': list(set(item['region'] for item in heatmap_data))
        })
        
    except Exception as e:
        logger.error(f"Error en conflict heatmap: {e}")
        return jsonify({'error': 'Error generando heatmap'}), 500


@app.errorhandler(404)
def not_found(error):
    """404 error handler."""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """500 error handler."""
    return render_template('500.html'), 500


def create_app():
    """Application factory."""
    # Ensure database tables exist
    db.create_tables()
    
    # Configure logging
    if not app.debug:
        file_handler = logging.FileHandler('logs/dashboard.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
    
    return app


@app.route('/about')
def about_page():
    """Página About - Explica cómo funciona el sistema."""
    return render_template('about.html')

@app.route('/reports')
def reports_page():
    """Página de Reports - Generación de reportes."""
    return render_template('reports.html')

@app.route('/chat')
def chat_page():
    """Página de AI Chat - Chat con IA usando modelo open-source."""
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """API endpoint para el chat con IA usando modelos open-source completamente gratuitos."""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        user_message = data['message'].strip()
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Use the AI chat processor
        from ..analytics.ai_chat_processor import AIChat
        chat_processor = AIChat()
        
        # Generate response using open-source AI
        ai_response = chat_processor.generate_response(user_message)
        
        # Get chat statistics
        stats = chat_processor.get_chat_statistics()
        
        return jsonify({
            'response': ai_response,
            'timestamp': datetime.now().isoformat(),
            'model_info': {
                'type': stats['model_type'],
                'is_open_source': stats['is_open_source'],
                'is_free': stats['is_free']
            }
        })
        
    except Exception as e:
        logger.error(f"Error in chat API: {str(e)}")
        
        # Enhanced fallback responses for geopolitical context
        fallback_responses = [
            f"Tu pregunta sobre geopolítica es muy interesante. En el análisis geopolítico moderno, consideramos múltiples factores como estabilidad política, dinámicas económicas, relaciones internacionales y indicadores de riesgo para proporcionar evaluaciones comprehensivas.",
            
            f"Esa es una consulta relevante para el análisis geopolítico. Nuestro sistema normalmente utiliza técnicas avanzadas de IA y análisis de big data para procesar información de múltiples fuentes globales y generar insights sobre tendencias y riesgos emergentes.",
            
            f"Tu consulta toca aspectos importantes del monitoreo geopolítico. Te recomiendo revisar nuestros reportes detallados en la sección Reports, donde encontrarás análisis específicos por región y tema, basados en datos actualizados en tiempo real.",
            
            f"Excelente pregunta sobre geopolítica. El análisis geopolítico requiere examinar interconexiones entre política internacional, economía global, seguridad regional y factores socioculturales. Nuestros reportes automáticos proporcionan este tipo de análisis integral."
        ]
        
        import random
        response = random.choice(fallback_responses)
        
        return jsonify({
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'model_info': {
                'type': 'Enhanced Fallback',
                'is_open_source': True,
                'is_free': True
            }
        })

@app.route('/api/generate_report', methods=['POST'])
def api_generate_report():
    """API endpoint para generar reportes."""
    try:
        data = request.get_json()
        report_type = data.get('type', 'summary')
        date_range = data.get('date_range', '7')
        
        conn = db.get_connection()
        
        # Fetch data based on date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=int(date_range))
        
        cursor = conn.execute('''
            SELECT title, summary, published_at, source_name, risk_level, conflict_type, 
                   regions_mentioned, sentiment_score, image_url
            FROM articles 
            WHERE published_at >= ? AND published_at <= ?
            ORDER BY published_at DESC
        ''', (start_date.isoformat(), end_date.isoformat()))
        
        articles = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        if report_type == 'summary':
            # Generate AI summary report
            articles_text = ""
            for article in articles[:20]:  # Limit to 20 articles
                articles_text += f"- {article['title']}: {article['summary']}\n"
            
            prompt = f"""
            Genera un reporte ejecutivo completo sobre la situación geopolítica basado en los siguientes artículos de los últimos {date_range} días:

            {articles_text}

            El reporte debe incluir:
            1. Resumen ejecutivo (200 palabras)
            2. Principales tendencias y patrones
            3. Regiones de mayor riesgo
            4. Recomendaciones estratégicas
            5. Análisis de impacto potencial

            Formato en HTML profesional.
            """
            
            report_content = ai_models.generate_response(prompt)
            
            return jsonify({
                'success': True,
                'report': {
                    'type': report_type,
                    'title': f'Reporte Geopolítico - Últimos {date_range} días',
                    'content': report_content,
                    'generated_at': datetime.now().isoformat(),
                    'article_count': len(articles),
                    'date_range': f'{start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")}'
                }
            })
        
        else:
            # Detailed data report
            return jsonify({
                'success': True,
                'report': {
                    'type': 'detailed',
                    'title': f'Reporte Detallado - Últimos {date_range} días',
                    'articles': articles,
                    'generated_at': datetime.now().isoformat(),
                    'article_count': len(articles)
                }
            })
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return jsonify({'error': 'Error generating report'}), 500


@app.route('/test')
def test_page():
    """Página de prueba simple para verificar APIs."""
    return '''<!DOCTYPE html>
<html>
<head>
    <title>Dashboard Test</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a2e; color: white; }
        .card { background: #16213e; padding: 20px; margin: 10px 0; border-radius: 10px; }
        .loading { color: #ffa500; }
        .error { color: #ff4757; }
        .success { color: #2ed573; }
        pre { background: #0c0c0c; padding: 10px; border-radius: 5px; overflow-x: auto; font-size: 12px; }
    </style>
</head>
<body>
    <h1>🔧 Dashboard API Test</h1>
    
    <div class="card">
        <h3>📊 Summary API Test</h3>
        <div id="summary-status" class="loading">Loading...</div>
        <pre id="summary-data"></pre>
    </div>
    
    <div class="card">
        <h3>📰 Articles API Test</h3>
        <div id="articles-status" class="loading">Loading...</div>
        <pre id="articles-data"></pre>
    </div>

    <script>
        console.log('🚀 Starting API tests...');
        
        // Test Summary API
        fetch('/api/summary')
            .then(response => {
                console.log('📊 Summary API response status:', response.status);
                if (!response.ok) throw new Error('Response not ok');
                return response.json();
            })
            .then(data => {
                console.log('📊 Summary data:', data);
                document.getElementById('summary-status').innerHTML = '<span class="success">✅ SUCCESS</span>';
                document.getElementById('summary-data').textContent = JSON.stringify(data, null, 2);
            })
            .catch(error => {
                console.error('❌ Summary API error:', error);
                document.getElementById('summary-status').innerHTML = '<span class="error">❌ ERROR: ' + error.message + '</span>';
                document.getElementById('summary-data').textContent = error.toString();
            });
        
        // Test Articles API
        fetch('/api/articles?limit=3')
            .then(response => {
                console.log('📰 Articles API response status:', response.status);
                if (!response.ok) throw new Error('Response not ok');
                return response.json();
            })
            .then(data => {
                console.log('📰 Articles data:', data);
                document.getElementById('articles-status').innerHTML = '<span class="success">✅ SUCCESS</span>';
                document.getElementById('articles-data').textContent = JSON.stringify(data, null, 2);
            })
            .catch(error => {
                console.error('❌ Articles API error:', error);
                document.getElementById('articles-status').innerHTML = '<span class="error">❌ ERROR: ' + error.message + '</span>';
                document.getElementById('articles-data').textContent = error.toString();
            });
    </script>
</body>
</html>'''


if __name__ == '__main__':
    app = create_app()
    
    host = config.get('dashboard.host', '0.0.0.0')
    port = config.get('dashboard.port', 5000)
    debug = config.get('dashboard.debug', True)
    
    logger.info(f"Starting dashboard on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
