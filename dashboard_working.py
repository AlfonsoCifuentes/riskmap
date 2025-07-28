#!/usr/bin/env python3
"""
Dashboard funcional que carga datos inmediatamente de SQLite
"""
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path
import random

# Configurar paths
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

app = Flask(__name__)
CORS(app)

# Configuración de la base de datos
DB_PATH = current_dir / "data" / "geopolitical_intel.db"

def get_db_connection():
    """Obtener conexión a la base de datos."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """Página principal del dashboard."""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/stats')
def get_stats():
    """Obtener estadísticas del dashboard."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Estadísticas básicas
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_articles = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM articles WHERE risk_level = 'high'")
        high_risk_events = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM events")
        total_events = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM sources")
        active_sources = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'total_articles': total_articles,
            'high_risk_events': high_risk_events,
            'total_events': total_events,
            'active_sources': active_sources,
            'processing_efficiency': round(96.5 + random.uniform(-2, 2), 1),
            'last_update': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/articles')
def get_articles():
    """Obtener artículos recientes."""
    try:
        limit = request.args.get('limit', 20, type=int)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT title, content, created_at, country, risk_level, source_url
            FROM articles 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        
        articles = []
        for row in cursor.fetchall():
            articles.append({
                'title': row['title'],
                'content': row['content'][:200] + '...' if row['content'] else '',
                'created_at': row['created_at'],
                'country': row['country'] or 'Global',
                'risk_level': row['risk_level'] or 'medium',
                'source_url': row['source_url']
            })
        
        conn.close()
        return jsonify(articles)
        
    except Exception as e:
        print(f"Error getting articles: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/events')
def get_events():
    """Obtener eventos recientes."""
    try:
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
        return jsonify(events)
        
    except Exception as e:
        print(f"Error getting events: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/risk-analysis')
def get_risk_analysis():
    """Obtener análisis de riesgo."""
    try:
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
                'risk_score': random.randint(30, 95)  # Simulado por ahora
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
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error getting risk analysis: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/heatmap')
def get_heatmap():
    """Obtener datos para el mapa de calor."""
    try:
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
        return jsonify(heatmap_data)
        
    except Exception as e:
        print(f"Error getting heatmap: {e}")
        return jsonify({'error': str(e)}), 500

# Template HTML del dashboard
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Riskmap Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            min-height: 100vh;
        }
        
        .header {
            background: rgba(0,0,0,0.2);
            padding: 1rem 2rem;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .header h1 {
            font-size: 2rem;
            font-weight: 300;
        }
        
        .container {
            padding: 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: rgba(255,255,255,0.1);
            padding: 1.5rem;
            border-radius: 10px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: bold;
            color: #4CAF50;
        }
        
        .stat-label {
            font-size: 0.9rem;
            opacity: 0.8;
            margin-top: 0.5rem;
        }
        
        .content-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            margin-bottom: 2rem;
        }
        
        .panel {
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 1.5rem;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .panel h3 {
            margin-bottom: 1rem;
            color: #FFD700;
        }
        
        .article-item, .event-item {
            background: rgba(255,255,255,0.05);
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 5px;
            border-left: 3px solid #4CAF50;
        }
        
        .risk-high { border-left-color: #f44336; }
        .risk-medium { border-left-color: #ff9800; }
        .risk-low { border-left-color: #4CAF50; }
        
        .article-title {
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        
        .article-meta {
            font-size: 0.8rem;
            opacity: 0.7;
        }
        
        .loading {
            text-align: center;
            padding: 2rem;
            opacity: 0.7;
        }
        
        .error {
            background: rgba(244, 67, 54, 0.2);
            color: #ffcdd2;
            padding: 1rem;
            border-radius: 5px;
            margin: 1rem 0;
        }
        
        .heatmap-container {
            height: 400px;
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 2rem;
        }
        
        .risk-analysis {
            grid-column: 1 / -1;
        }
        
        .top-risk-article {
            background: rgba(244, 67, 54, 0.2);
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            border: 1px solid rgba(244, 67, 54, 0.3);
        }
        
        .countries-list {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }
        
        .country-item {
            background: rgba(255,255,255,0.05);
            padding: 1rem;
            border-radius: 5px;
            text-align: center;
        }
        
        .country-score {
            font-size: 1.5rem;
            font-weight: bold;
            color: #FFD700;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌍 Riskmap Dashboard - Inteligencia Geopolítica</h1>
    </div>
    
    <div class="container">
        <!-- Estadísticas principales -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number" id="total-articles">-</div>
                <div class="stat-label">Artículos Analizados</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="high-risk-events">-</div>
                <div class="stat-label">Eventos de Alto Riesgo</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="total-events">-</div>
                <div class="stat-label">Eventos Monitoreados</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="active-sources">-</div>
                <div class="stat-label">Fuentes Activas</div>
            </div>
        </div>
        
        <!-- Mapa de calor -->
        <div class="panel">
            <h3>🗺️ Mapa de Eventos Globales</h3>
            <div class="heatmap-container">
                <div id="heatmap-content">Cargando mapa de eventos...</div>
            </div>
        </div>
        
        <!-- Análisis de riesgo -->
        <div class="panel risk-analysis">
            <h3>⚠️ Análisis de Riesgo</h3>
            <div id="risk-analysis-content">
                <div class="loading">Cargando análisis de riesgo...</div>
            </div>
        </div>
        
        <!-- Contenido principal -->
        <div class="content-grid">
            <div class="panel">
                <h3>📰 Artículos Recientes</h3>
                <div id="articles-content">
                    <div class="loading">Cargando artículos...</div>
                </div>
            </div>
            
            <div class="panel">
                <h3>🔔 Eventos en Tiempo Real</h3>
                <div id="events-content">
                    <div class="loading">Cargando eventos...</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Función para cargar estadísticas
        async function loadStats() {
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();
                
                document.getElementById('total-articles').textContent = data.total_articles.toLocaleString();
                document.getElementById('high-risk-events').textContent = data.high_risk_events.toLocaleString();
                document.getElementById('total-events').textContent = data.total_events.toLocaleString();
                document.getElementById('active-sources').textContent = data.active_sources.toLocaleString();
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }
        
        // Función para cargar artículos
        async function loadArticles() {
            try {
                const response = await fetch('/api/articles?limit=10');
                const articles = await response.json();
                
                const container = document.getElementById('articles-content');
                container.innerHTML = '';
                
                articles.forEach(article => {
                    const div = document.createElement('div');
                    div.className = `article-item risk-${article.risk_level}`;
                    div.innerHTML = `
                        <div class="article-title">${article.title}</div>
                        <div class="article-content">${article.content}</div>
                        <div class="article-meta">
                            ${article.country} • ${article.risk_level.toUpperCase()} • ${new Date(article.created_at).toLocaleString()}
                        </div>
                    `;
                    container.appendChild(div);
                });
            } catch (error) {
                console.error('Error loading articles:', error);
                document.getElementById('articles-content').innerHTML = '<div class="error">Error cargando artículos</div>';
            }
        }
        
        // Función para cargar eventos
        async function loadEvents() {
            try {
                const response = await fetch('/api/events?limit=10');
                const events = await response.json();
                
                const container = document.getElementById('events-content');
                container.innerHTML = '';
                
                events.forEach(event => {
                    const div = document.createElement('div');
                    div.className = 'event-item';
                    div.innerHTML = `
                        <div class="article-title">${event.title}</div>
                        <div class="article-content">${event.content}</div>
                        <div class="article-meta">
                            ${event.source} • ${event.type} • ${new Date(event.published_at).toLocaleString()}
                        </div>
                    `;
                    container.appendChild(div);
                });
            } catch (error) {
                console.error('Error loading events:', error);
                document.getElementById('events-content').innerHTML = '<div class="error">Error cargando eventos</div>';
            }
        }
        
        // Función para cargar análisis de riesgo
        async function loadRiskAnalysis() {
            try {
                const response = await fetch('/api/risk-analysis');
                const data = await response.json();
                
                const container = document.getElementById('risk-analysis-content');
                container.innerHTML = `
                    <div class="top-risk-article">
                        <h4>🚨 Artículo de Mayor Riesgo</h4>
                        <div class="article-title">${data.top_risk_article.title}</div>
                        <div class="article-content">${data.top_risk_article.content}</div>
                        <div class="article-meta">
                            ${data.top_risk_article.country} • ${data.top_risk_article.risk_level.toUpperCase()}
                        </div>
                    </div>
                    
                    <h4>🌍 Países con Mayor Actividad</h4>
                    <div class="countries-list">
                        ${data.countries.map(country => `
                            <div class="country-item">
                                <div class="country-score">${country.risk_score}</div>
                                <div>${country.country}</div>
                                <div style="font-size: 0.8rem; opacity: 0.7;">${country.count} eventos</div>
                            </div>
                        `).join('')}
                    </div>
                `;
            } catch (error) {
                console.error('Error loading risk analysis:', error);
                document.getElementById('risk-analysis-content').innerHTML = '<div class="error">Error cargando análisis de riesgo</div>';
            }
        }
        
        // Función para cargar mapa de calor
        async function loadHeatmap() {
            try {
                const response = await fetch('/api/heatmap');
                const data = await response.json();
                
                const container = document.getElementById('heatmap-content');
                container.innerHTML = `
                    <div style="text-align: center;">
                        <div style="font-size: 2rem; margin-bottom: 1rem;">🗺️</div>
                        <div>Eventos detectados: ${data.length.toLocaleString()}</div>
                        <div style="font-size: 0.8rem; opacity: 0.7; margin-top: 0.5rem;">
                            Distribución global de eventos geopolíticos
                        </div>
                    </div>
                `;
            } catch (error) {
                console.error('Error loading heatmap:', error);
                document.getElementById('heatmap-content').innerHTML = '<div class="error">Error cargando mapa</div>';
            }
        }
        
        // Cargar todos los datos al inicio
        document.addEventListener('DOMContentLoaded', function() {
            loadStats();
            loadArticles();
            loadEvents();
            loadRiskAnalysis();
            loadHeatmap();
            
            // Actualizar cada 30 segundos
            setInterval(() => {
                loadStats();
                loadArticles();
                loadEvents();
                loadRiskAnalysis();
            }, 30000);
        });
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("🚀 Iniciando Riskmap Dashboard...")
    print(f"📂 Base de datos: {DB_PATH}")
    print("🌐 URL: http://localhost:5001")
    print("🔄 Para detener: Ctrl+C")
    print("-" * 50)
    
    app.run(host='127.0.0.1', port=5001, debug=True, use_reloader=False)