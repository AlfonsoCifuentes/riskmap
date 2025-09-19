#!/usr/bin/env python3
"""
Servidor de prueba mínimo para probar solo el endpoint de artículos
"""
import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

def get_database_path():
    """Obtener la ruta de la base de datos"""
    return "./data/geopolitical_intel.db"

def get_top_articles_from_db(limit=20, exclude_hero_id=None):
    """
    Obtener artículos usando la nueva lógica SQL corregida
    """
    try:
        db_path = get_database_path()
        
        base_query = """
            SELECT 
                id, title, 
                CASE 
                    WHEN summary IS NOT NULL AND summary != '' AND summary NOT LIKE '%<think>%' THEN 
                        summary
                    WHEN auto_generated_summary IS NOT NULL AND auto_generated_summary != '' AND auto_generated_summary NOT LIKE '%<think>%' THEN 
                        auto_generated_summary
                    WHEN content IS NOT NULL AND content != '' AND content NOT LIKE '%<think>%' THEN 
                        SUBSTR(content, 1, 300) || '...'
                    ELSE 
                        'Análisis de contenido geopolítico disponible para revisión.'
                END as summary,
                url, source, published_at, country, region, risk_level, 
                conflict_type, sentiment_score, risk_score,
                CASE 
                    WHEN image_url IS NOT NULL AND image_url != '' AND image_url NOT LIKE '%via.placeholder%' THEN 
                        image_url
                    ELSE 
                        'https://images.unsplash.com/photo-1495020689067-958852a7765e?w=400&h=200&fit=crop'
                END as image_url,
                ai_importance
            FROM articles 
            WHERE 
                -- Campos básicos requeridos
                title IS NOT NULL AND title != '' AND
                content IS NOT NULL AND content != '' AND
                
                -- Riesgo válido
                risk_score >= 0.0 AND
                
                -- Excluir artículos HERO (solo para mosaic)
                (content NOT LIKE '%HERO ARTICLE%' OR content IS NULL) AND
                (title NOT LIKE '%HERO%' OR title IS NULL)
        """
        
        # Si hay un ID de artículo HERO para excluir
        exclude_filter = ""
        if exclude_hero_id:
            exclude_filter = f" AND id != {exclude_hero_id}"
        
        # Query final
        final_query = base_query + exclude_filter + """
            ORDER BY ai_importance DESC, published_at DESC
            LIMIT ?
        """
        
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(final_query, (limit,))
            articles = [dict(row) for row in cursor.fetchall()]
            
        return articles
        
    except Exception as e:
        print(f"Error getting articles: {e}")
        return []

@app.route('/api/articles')
def get_articles():
    """Endpoint de artículos simplificado"""
    try:
        # Parámetros
        limit = request.args.get('limit', 20, type=int)
        
        # Obtener artículos
        articles = get_top_articles_from_db(limit)
        
        # Convertir a formato dashboard
        dashboard_articles = []
        for article in articles:
            risk_mapping = {
                'high': 'high',
                'medium': 'medium', 
                'low': 'low',
                'unknown': 'low'
            }
            
            risk_level = risk_mapping.get(article.get('risk_level', 'unknown'), 'low')
            
            dashboard_article = {
                'id': article.get('id'),
                'title': article.get('title', 'Sin título'),
                'content': article.get('summary', 'Sin contenido'),  # Usar summary procesado
                'location': article.get('country', 'Global'),
                'country': article.get('country', 'Global'),
                'region': article.get('region', 'Internacional'),
                'risk': risk_level,
                'risk_level': risk_level,
                'risk_score': article.get('risk_score', 0.0),
                'source': article.get('source', 'Fuente desconocida'),
                'published_at': article.get('published_at'),
                'summary': article.get('summary'),
                'url': article.get('url'),
                'image': article.get('image_url'),  # URL corregida
                'image_url': article.get('image_url'),
                'conflict_type': article.get('conflict_type'),
                'sentiment_score': article.get('sentiment_score'),
                'ai_importance': article.get('ai_importance', 0)
            }
            dashboard_articles.append(dashboard_article)
        
        return jsonify({
            'success': True,
            'articles': dashboard_articles,
            'total': len(dashboard_articles),
            'message': f'Obtenidos {len(dashboard_articles)} artículos desde la base de datos',
            'filters_applied': {
                'no_think_content': True,
                'valid_image_urls': True,
                'basic_validation': True
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'articles': []
        }), 500

@app.route('/api/status')
def status():
    """Estado del servidor"""
    return jsonify({
        'status': 'running',
        'server': 'test_minimal',
        'database': os.path.exists('./data/geopolitical_intel.db')
    })

@app.route('/')
def home():
    """Página de inicio simple"""
    return '''
    <h1>🧪 Servidor de Prueba - RiskMap</h1>
    <p>Endpoints disponibles:</p>
    <ul>
        <li><a href="/api/articles">/api/articles</a> - Obtener artículos</li>
        <li><a href="/api/status">/api/status</a> - Estado del servidor</li>
    </ul>
    '''

if __name__ == '__main__':
    print("🧪 Iniciando servidor de prueba mínimo...")
    print("📡 Endpoints:")
    print("   - http://localhost:5000/api/articles")
    print("   - http://localhost:5000/api/status")
    print("   - http://localhost:5000/")
    print()
    app.run(debug=True, port=5000, host='0.0.0.0')