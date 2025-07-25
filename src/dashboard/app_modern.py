"""
Modern Flask Dashboard Application for Geopolitical Intelligence System
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.config import config, logger
from dashboard.language_config import get_language_config, get_available_languages

# --- Dynamic ingest on page access + scheduler every 5 min ------------------
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

# Re-use ingest_realtime from global scheduler module ensuring package path
root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

try:
    from src.scheduler import ingest_realtime  # Import as package
except ImportError as e:
    logger.error(f"Cannot import ingest_realtime: {e}")
    raise

last_ingest_time = datetime.utcnow() - timedelta(minutes=10)

scheduler_bg = BackgroundScheduler(timezone="UTC")
scheduler_bg.add_job(ingest_realtime, 'interval', minutes=5, id='realtime_ingest_live', max_instances=1, replace_existing=True)
scheduler_bg.start()

def ensure_ingest():
    """Run ingest if more than 5 min since last run."""
    global last_ingest_time
    if datetime.utcnow() - last_ingest_time > timedelta(minutes=5):
        logger.info('[Dashboard] Triggering realtime ingest before responding…')
        try:
            ingest_realtime()
            last_ingest_time = datetime.utcnow()
        except Exception as exc:
            logger.error(f'[Dashboard] Instant ingest error: {exc}')

app = Flask(__name__)
app.config['SECRET_KEY'] = config.get('dashboard.secret_key', 'geopolitical-intel-2024')
CORS(app)

# Absolute database path resolved dynamically (two levels above src/dashboard)
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = str(BASE_DIR / 'data' / 'geopolitical_intel.db')

def get_db_connection():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """Render the main dashboard."""
    return render_template('modern_dashboard.html')

@app.route('/api/dashboard/stats')
def get_dashboard_stats():
    """Get dashboard statistics."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total articles
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_articles = cursor.fetchone()[0]
        
        # High risk events
        cursor.execute("SELECT COUNT(*) FROM articles WHERE risk_level = 'high'")
        high_risk_events = cursor.fetchone()[0]
        
        # Processed in last 24h (more robust than same-date)
        cursor.execute("""
            SELECT COUNT(*) FROM articles 
            WHERE created_at > datetime('now', '-24 hours')
        """)
        processed_today = cursor.fetchone()[0]
        
        # Active regions (countries with events in last 7 days)
        cursor.execute("""
            SELECT COUNT(DISTINCT country) FROM articles 
            WHERE created_at > datetime('now', '-7 days')
            AND country IS NOT NULL
        """)
        active_regions = cursor.fetchone()[0]
        
        # Get recent alerts
        alerts = get_recent_alerts(cursor)
        
        # Get map events
        events = get_map_events(cursor)
        
        conn.close()
        
        return jsonify({
            'stats': {
                'total_articles': total_articles,
                'high_risk_events': high_risk_events,
                'processed_today': processed_today,
                'active_regions': active_regions
            },
            'alerts': alerts,
            'events': events
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/events/heatmap')
def get_heatmap_data():
    """Get heatmap data for the map."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get aggregated event data by location
        cursor.execute("""
            SELECT 
                country,
                COUNT(*) as event_count,
                AVG(CASE 
                    WHEN risk_level = 'high' THEN 1.0
                    WHEN risk_level = 'medium' THEN 0.6
                    ELSE 0.3
                END) as risk_score
            FROM articles
            WHERE created_at > datetime('now', '-30 days')
            GROUP BY country
            HAVING country IS NOT NULL
        """)
        
        heatmap_data = []
        for row in cursor.fetchall():
            # In production, you'd have a country-to-coordinates mapping
            coords = get_country_coordinates(row['country'])
            if coords:
                heatmap_data.append({
                    'lat': coords['lat'],
                    'lng': coords['lng'],
                    'intensity': row['risk_score'],
                    'count': row['event_count'],
                    'country': row['country']
                })
        
        conn.close()
        return jsonify(heatmap_data)
        
    except Exception as e:
        logger.error(f"Error getting heatmap data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/categories')
def get_category_distribution():
    """Get category distribution data."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get categories from processed_data table
        cursor.execute("""
            SELECT 
                pd.category,
                COUNT(*) as count
            FROM processed_data pd
            JOIN articles a ON pd.article_id = a.id
            WHERE a.created_at > datetime('now', '-30 days')
            AND pd.category IS NOT NULL
            AND pd.category != 'general_news'
            GROUP BY pd.category
            ORDER BY count DESC
        """)
        
        categories = []
        for row in cursor.fetchall():
            categories.append({
                'category': row['category'],
                'count': row['count']
            })
        
        # If no categories found, use risk levels as fallback
        if not categories:
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN risk_level = 'high' THEN 'Alto Riesgo'
                        WHEN risk_level = 'medium' THEN 'Riesgo Medio'
                        WHEN risk_level = 'low' THEN 'Bajo Riesgo'
                        ELSE 'Sin Clasificar'
                    END as category,
                    COUNT(*) as count
                FROM articles
                WHERE created_at > datetime('now', '-30 days')
                GROUP BY risk_level
                ORDER BY count DESC
            """)
            
            for row in cursor.fetchall():
                categories.append({
                    'category': row['category'],
                    'count': row['count']
                })
        
        conn.close()
        return jsonify(categories)
        
    except Exception as e:
        logger.error(f"Error getting category distribution: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/timeline')
def get_timeline_data():
    """Get timeline data for events."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as count,
                SUM(CASE WHEN risk_level = 'high' THEN 1 ELSE 0 END) as high_risk_count
            FROM articles
            WHERE created_at > datetime('now', '-30 days')
            GROUP BY DATE(created_at)
            ORDER BY date
        """)
        
        timeline = []
        for row in cursor.fetchall():
            timeline.append({
                'date': row['date'],
                'total': row['count'],
                'high_risk': row['high_risk_count']
            })
        
        conn.close()
        return jsonify(timeline)
        
    except Exception as e:
        logger.error(f"Error getting timeline data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/sentiment')
def get_sentiment_distribution():
    """Get sentiment distribution data."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN sentiment > 0.2 THEN 'positive'
                    WHEN sentiment < -0.2 THEN 'negative'
                    ELSE 'neutral'
                END as sentiment_category,
                COUNT(*) as count
            FROM processed_data
            GROUP BY sentiment_category
        """)
        
        sentiment_data = {}
        for row in cursor.fetchall():
            sentiment_data[row['sentiment_category']] = row['count']
        
        conn.close()
        return jsonify(sentiment_data)
        
    except Exception as e:
        logger.error(f"Error getting sentiment data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/wordcloud')
def get_wordcloud_data():
    """Get word frequency data for word cloud."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get keywords from recent articles
        cursor.execute("""
            SELECT keywords
            FROM processed_data pd
            JOIN articles a ON pd.article_id = a.id
            WHERE a.created_at > datetime('now', '-7 days')
            AND keywords IS NOT NULL AND keywords != '[]'
            LIMIT 100
        """)
        
        word_freq = {}
        for row in cursor.fetchall():
            try:
                keywords = json.loads(row['keywords'])
                for keyword in keywords:
                    word_freq[keyword] = word_freq.get(keyword, 0) + 1
            except:
                pass
        
        # Convert to word cloud format
        wordcloud_data = [
            {'text': word, 'size': min(count * 10, 50)}
            for word, count in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:50]
        ]
        
        conn.close()
        return jsonify(wordcloud_data)
        
    except Exception as e:
        logger.error(f"Error getting wordcloud data: {e}")
        return jsonify({'error': str(e)}), 500

def get_recent_alerts(cursor):
    """Get recent high-priority alerts."""
    cursor.execute("""
        SELECT 
            a.id,
            a.title,
            a.risk_level,
            a.country,
            a.created_at
        FROM articles a
        LEFT JOIN processed_data pd ON a.id = pd.article_id
        WHERE a.risk_level IN ('high', 'medium')
        AND a.created_at > datetime('now', '-24 hours')
        AND (pd.category IS NULL OR pd.category != 'sports_entertainment')
        ORDER BY a.created_at DESC
        LIMIT 10
    """)
    
    alerts = []
    for row in cursor.fetchall():
        alerts.append({
            'id': row['id'],
            'title': row['title'],
            'level': row['risk_level'],
            'category': 'general_news',  # Default category
            'location': row['country'] or 'Global',
            'time': row['created_at']
        })
    
    return alerts

def get_map_events(cursor):
    """Get events for map display."""
    cursor.execute("""
        SELECT 
            a.id,
            a.title,
            a.risk_level,
            a.country,
            a.created_at
        FROM articles a
        LEFT JOIN processed_data pd ON a.id = pd.article_id
        WHERE a.created_at > datetime('now', '-7 days')
        AND a.risk_level IN ('high', 'medium')
        AND (pd.category IS NULL OR pd.category != 'sports_entertainment')
        ORDER BY a.created_at DESC
        LIMIT 100
    """)
    
    events = []
    for row in cursor.fetchall():
        coords = get_country_coordinates(row['country'])
        if coords:
            events.append({
                'id': row['id'],
                'title': row['title'],
                'risk_level': row['risk_level'],
                'category': 'general_news',  # Default category
                'country': row['country'],
                'lat': coords['lat'],
                'lng': coords['lng'],
                'sentiment': 0,  # Default sentiment
                'date': row['created_at']
            })
    
    return events

def get_country_coordinates(country_name):
    """Get coordinates for a country (simplified version)."""
    # In production, use a proper geocoding service or database
    country_coords = {
        'US': {'lat': 39.8283, 'lng': -98.5795},
        'United States': {'lat': 39.8283, 'lng': -98.5795},
        'China': {'lat': 35.8617, 'lng': 104.1954},
        'Russia': {'lat': 61.5240, 'lng': 105.3188},
        'Ukraine': {'lat': 48.3794, 'lng': 31.1656},
        'Israel': {'lat': 31.0461, 'lng': 34.8516},
        'Iran': {'lat': 32.4279, 'lng': 53.6880},
        'France': {'lat': 46.2276, 'lng': 2.2137},
        'Germany': {'lat': 51.1657, 'lng': 10.4515},
        'UK': {'lat': 55.3781, 'lng': -3.4360},
        'Spain': {'lat': 40.4637, 'lng': -3.7492},
        'Italy': {'lat': 41.8719, 'lng': 12.5674},
        'Japan': {'lat': 36.2048, 'lng': 138.2529},
        'India': {'lat': 20.5937, 'lng': 78.9629},
        'Brazil': {'lat': -14.2350, 'lng': -51.9253},
        'Mexico': {'lat': 23.6345, 'lng': -102.5528},
        'Canada': {'lat': 56.1304, 'lng': -106.3468},
        'Australia': {'lat': -25.2744, 'lng': 133.7751},
        'Syria': {'lat': 34.8021, 'lng': 38.9968},
        'Iraq': {'lat': 33.2232, 'lng': 43.6793},
        'Egypt': {'lat': 26.8206, 'lng': 30.8025},
        'Saudi Arabia': {'lat': 23.8859, 'lng': 45.0792},
        'Turkey': {'lat': 38.9637, 'lng': 35.2433},
        'Global': {'lat': 0, 'lng': 0}
    }
    
    return country_coords.get(country_name)

@app.route('/api/articles/latest')
def get_latest_articles():
    """Get latest articles."""
    try:
        limit = request.args.get('limit', 10, type=int)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                a.id,
                a.title,
                a.source,
                a.language,
                a.risk_level,
                a.created_at
            FROM articles a
            WHERE a.url IS NOT NULL
            GROUP BY a.title
            ORDER BY MAX(a.created_at) DESC
            LIMIT ?
        """, (limit,))
        
        articles = []
        for row in cursor.fetchall():
            articles.append({
                'id': row['id'],
                'title': row['title'],
                'source': row['source'],
                'language': row['language'],
                'risk_level': row['risk_level'] or 'low',
                'date': row['created_at'],
                'category': 'general_news',
                'sentiment': 0
            })
        
        conn.close()
        return jsonify(articles)
        
    except Exception as e:
        logger.error(f"Error getting latest articles: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/articles/high-risk')
def get_high_risk_articles():
    """Get high risk articles."""
    try:
        limit = request.args.get('limit', 10, type=int)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                a.id,
                a.title,
                a.country,
                a.risk_level,
                a.created_at
            FROM articles a
            WHERE a.risk_level IN ('high', 'medium')
            AND a.url IS NOT NULL
            GROUP BY a.title
            ORDER BY 
                CASE MAX(a.risk_level)
                    WHEN 'high' THEN 1 
                    WHEN 'medium' THEN 2 
                    ELSE 3 
                END,
                MAX(a.created_at) DESC
            LIMIT ?
        """, (limit,))
        
        articles = []
        for row in cursor.fetchall():
            articles.append({
                'id': row['id'],
                'title': row['title'],
                'location': row['country'] or 'Unknown',
                'risk_level': row['risk_level'],
                'date': row['created_at'],
                'category': 'general_news',
                'sentiment': 0
            })
        
        conn.close()
        return jsonify(articles)
        
    except Exception as e:
        logger.error(f"Error getting high risk articles: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/articles/featured')
def get_featured_article():
    """Get a featured article with working URL - using known working URLs from recent tests."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        logger.info("[FEATURED] Getting featured article with working URL...")
        
        # Get the most recent article with a working URL (based on our tests)
        # These are URLs we know work from our testing
        working_domains = [
            'theguardian.com',
            'euronews.com', 
            'ft.com',
            'tass.com',
            'rt.com',
            'dawn.com',
            'hindustantimes.com',
            'elmundo.es'
        ]
        
        domain_conditions = " OR ".join([f"a.url LIKE '%{domain}%'" for domain in working_domains])
        
        cursor.execute(f"""
            SELECT 
                a.id,
                a.title,
                a.content,
                a.url,
                a.country,
                a.risk_level,
                a.created_at,
                a.image_url,
                a.source,
                pd.category,
                pd.summary,
                COALESCE(a.risk_score, 0) as risk_score
            FROM articles a
            LEFT JOIN processed_data pd ON a.id = pd.article_id
            WHERE a.created_at > datetime('now', '-24 hours')
            AND a.url IS NOT NULL 
            AND a.url != '' 
            AND a.url != '#'
            AND ({domain_conditions})
            ORDER BY 
                CASE a.risk_level 
                    WHEN 'high' THEN 1 
                    WHEN 'medium' THEN 2 
                    ELSE 3 
                END,
                a.created_at DESC
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        
        if not row:
            # Fallback to any recent article from working domains
            cursor.execute(f"""
                SELECT 
                    a.id,
                    a.title,
                    a.content,
                    a.url,
                    a.country,
                    a.risk_level,
                    a.created_at,
                    a.image_url,
                    a.source,
                    pd.category,
                    pd.summary,
                    COALESCE(a.risk_score, 0) as risk_score
                FROM articles a
                LEFT JOIN processed_data pd ON a.id = pd.article_id
                WHERE a.created_at > datetime('now', '-7 days')
                AND a.url IS NOT NULL 
                AND a.url != '' 
                AND a.url != '#'
                AND ({domain_conditions})
                ORDER BY a.created_at DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
        
        if row:
            # Create description from summary or content
            description = ''
            if row['summary'] and row['summary'].strip():
                description = row['summary'].strip()
            elif row['content'] and row['content'].strip():
                content = row['content'].strip()
                if len(content) > 300:
                    description = content[:300] + '...'
                else:
                    description = content
            else:
                description = 'Artículo disponible en la base de datos.'
            
            # Use the URL from database (from trusted domains)
            article_url = row['url']
            
            # Handle image URL
            image_url = row['image_url']
            if image_url and image_url.strip() and not image_url.startswith('javascript:'):
                if not image_url.startswith(('http://', 'https://')):
                    if image_url.startswith('/'):
                        image_url = None  # Relative URL without base domain
                    else:
                        image_url = 'https://' + image_url
            else:
                image_url = None
            
            # Use the ACTUAL risk level from database - don't artificially inflate it
            display_risk = row['risk_level'] or 'low'
            
            # If this is a low-risk article being shown as "highest risk", add a note
            display_title = row['title'] or 'Artículo sin título'
            if display_risk == 'low':
                display_title = f"[Artículo Más Relevante Disponible] {display_title}"
            
            article = {
                'id': row['id'],
                'title': display_title,
                'description': description,
                'url': article_url,
                'location': row['country'] or 'Global',
                'risk_level': display_risk,
                'date': row['created_at'],
                'image_url': image_url,
                'category': row['category'] or 'general_news',
                'source': row['source'] or 'Fuente no especificada'
            }
            
            logger.info(f"[FEATURED] ✅ Returning article with working URL: {article['title'][:50]}... Risk: {display_risk} URL: {article_url}")
        else:
            # No articles found
            logger.warning("[FEATURED] No articles found from trusted domains!")
            article = {
                'id': 0,
                'title': 'No hay artículos disponibles',
                'description': 'No se encontraron artículos recientes con URLs confiables. Ejecute el proceso de ingesta de datos.',
                'url': '#',
                'location': 'Sistema',
                'risk_level': 'low',
                'date': datetime.now().isoformat(),
                'image_url': None,
                'category': 'system_message',
                'source': 'Sistema'
            }
        
        conn.close()
        return jsonify(article)
        
    except Exception as e:
        logger.error(f"Error getting featured article: {e}")
        return jsonify({
            'id': 0,
            'title': 'Error del sistema',
            'description': f'Error al obtener artículo destacado: {str(e)}',
            'url': '#',
            'location': 'Sistema',
            'risk_level': 'low',
            'date': datetime.now().isoformat(),
            'image_url': None,
            'category': 'system_error',
            'source': 'Sistema'
        }), 500

@app.route('/api/languages')
def get_languages():
    """Get available languages."""
    try:
        languages = get_available_languages()
        return jsonify(languages)
    except Exception as e:
        logger.error(f"Error getting languages: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/language/<lang_code>')
def get_language_config_api(lang_code):
    """Get language configuration."""
    try:
        config_data = get_language_config(lang_code)
        return jsonify(config_data)
    except Exception as e:
        logger.error(f"Error getting language config: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/set-language', methods=['POST'])
def set_language():
    """Set the target language for RSS ingestion."""
    try:
        data = request.get_json()
        lang_code = data.get('language', 'es')
        
        # Update config (in a real app, you'd save this to a config file)
        # For now, we'll just return success
        
        return jsonify({
            'success': True,
            'language': lang_code,
            'message': f'Language set to {lang_code}'
        })
        
    except Exception as e:
        logger.error(f"Error setting language: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/weekly-analysis')
def get_ai_weekly_analysis():
    """Return realistic AI-generated weekly analysis using OpenAI (or fallback)."""
    try:
        openai_key = config.get_openai_key()
        start_date = (datetime.now() - timedelta(days=7)).strftime('%d/%m/%Y')
        end_date = datetime.now().strftime('%d/%m/%Y')

        # Count real articles last 7 days for the prompt (used by any model)
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM articles WHERE created_at > datetime('now','-7 days')")
        art_count = cur.fetchone()[0]
        conn.close()

        prompt = (
            f"Actúa como un periodista especializado en análisis geopolítico. Redacta un informe profesional "
            f"sobre la situación global entre {start_date} y {end_date}, basándote en los {art_count} artículos "
            f"disponibles en la base de datos. "
            f"Estructura tu análisis como un artículo periodístico con: "
            f"1) Un titular llamativo, 2) Los 3 focos geopolíticos más críticos de la semana, "
            f"3) Impactos económicos y sociales relevantes, 4) Proyecciones a corto plazo. "
            f"IMPORTANTE: Responde ÚNICAMENTE en formato HTML válido usando etiquetas como <h2>, <h3>, <p>, <ul>, <li>, <strong>, <em>. "
            f"NO uses markdown (**, ##, -, etc.). Escribe en español con un tono profesional y analítico."
        )

        # ---------------- GROQ ONLY ----------------
        content = None
        groq_key = config.get_groq_key()
        if groq_key:
            try:
                import requests, json
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
                payload = {
                    "model": "llama3-8b-8192",
                    "messages": [
                        {"role": "system", "content": "Eres un analista geopolítico."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.4,
                    "max_tokens": 800
                }
                r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
                r.raise_for_status()
                content = r.json()['choices'][0]['message']['content']
            except Exception as err:
                logger.error(f"Groq generation failed: {err}")
                content = "<p>No fue posible generar el análisis automático (Groq error).</p>"
        else:
            content = "<p>API key de Groq no configurada.</p>"
                    
                
        # --- Try OpenAI (new client) ---
        if openai_key and content is None:
            try:
                import openai
                try:
                    from openai import OpenAI  # v1 client
                    client = OpenAI(api_key=openai_key)
                    resp = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "system", "content": "Eres un analista geopolítico."},
                                  {"role": "user", "content": prompt}],
                        temperature=0.4,
                        max_tokens=800
                    )
                    content = resp.choices[0].message.content
                except ImportError:
                    # fallback to old interface
                    openai.api_key = openai_key
                    resp = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "system", "content": "Eres un analista geopolítico."},
                                  {"role": "user", "content": prompt}],
                        temperature=0.4,
                        max_tokens=800
                    )
                    content = resp.choices[0].message.content
            except Exception as err:
                logger.warning(f"OpenAI fallback failed: {err}")
                content = None

        # --- Try DeepSeek ---
        if content is None and config.get_deepseek_key():
            try:
                import requests, json
                ds_key = config.get_deepseek_key()
                url = "https://api.deepseek.com/v1/chat/completions"
                headers = {"Authorization": f"Bearer {ds_key}", "Content-Type": "application/json"}
                payload = {
                    "model": "deepseek-chat",
                    "messages": [{"role": "system", "content": "Eres un analista geopolítico."},
                                 {"role": "user", "content": prompt}],
                    "temperature": 0.4,
                    "max_tokens": 800
                }
                r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
                r.raise_for_status()
                content = r.json()['choices'][0]['message']['content']
            except Exception as err:
                logger.warning(f"DeepSeek generation failed: {err}")
                content = None

        # --- Try HuggingFace Inference API ---
        if content is None and config.get_hf_token():
            try:
                import requests
                hf_token = config.get_hf_token()
                headers = {"Authorization": f"Bearer {hf_token}"}
                data = {"inputs": prompt, "parameters": {"max_new_tokens": 800, "temperature": 0.4}}
                r = requests.post("https://api-inference.huggingface.co/models/google/flan-t5-large", headers=headers, json=data, timeout=60)
                r.raise_for_status()
                content = r.json()[0]['generated_text']
            except Exception as err:
                logger.warning(f"HF generation failed: {err}")
                content = None

        # --- Final local transformers fallback ---
        if content is None:
            try:
                from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
                logger.info("Using local Qwen2.5-0.5B-Instruct fallback…")
                model_name = "Qwen/Qwen2.5-0.5B-Instruct"
                tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
                model = AutoModelForCausalLM.from_pretrained(model_name, trust_remote_code=True)
                generator = pipeline("text-generation", model=model, tokenizer=tokenizer, device_map="auto")

                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("""
                    SELECT title, content FROM articles
                    WHERE created_at > datetime('now','-7 days')
                    ORDER BY created_at DESC LIMIT 15
                """)
                rows = cur.fetchall(); conn.close()
                corpus = "\n".join([(r['title'] or '') + " - " + (r['content'] or '') for r in rows])[:3000]
                local_prompt = (
                    "<|system|>Eres un analista geopolítico experto.<|user|>" +
                    prompt + "\n\nArtículos:\n" + corpus + "\n<|assistant|>")
                out = generator(local_prompt, max_new_tokens=300, temperature=0.4)[0]['generated_text']
                # Remove the prompt part
                content = "<p>" + out.split("<|assistant|>")[-1].strip().replace("\n", "</p><p>") + "</p>"
            except Exception as err:
                logger.warning(f"Local transformers fallback failed: {err}")
                content = "<p>No fue posible generar el análisis automático en este momento.</p>"

        return jsonify({'content': content})

    except Exception as e:
        logger.error(f"Error generating AI analysis: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Ensure database path exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Run the application
    app.run(
        host=config.get('app.host', '127.0.0.1'),
        port=config.get('app.port', 5001),
        debug=config.get('app.debug', True)
    )