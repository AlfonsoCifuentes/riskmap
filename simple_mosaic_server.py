#!/usr/bin/env python3
"""
Script simple para probar el mosaico sin las dependencias pesadas
"""
import sqlite3
import json
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Template HTML simple para mostrar el mosaico
MOSAIC_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Mosaico de Noticias Geopolíticas</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: white; }
        h1 { color: #ff6b6b; text-align: center; }
        .article { 
            background: #2d2d2d; 
            margin: 20px 0; 
            padding: 15px; 
            border-radius: 8px;
            border-left: 4px solid #ff6b6b;
        }
        .article img { max-width: 300px; max-height: 200px; object-fit: cover; }
        .title { color: #fff; font-size: 18px; font-weight: bold; margin-bottom: 10px; }
        .meta { color: #aaa; font-size: 14px; margin-bottom: 10px; }
        .description { color: #ccc; line-height: 1.6; }
        .status { background: #2d2d2d; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px; }
    </style>
</head>
<body>
    <h1>🗺️ Mosaico de Noticias Geopolíticas</h1>
    <div class="status">
        <p>📊 <strong>Total de artículos válidos:</strong> {{ articles|length }}</p>
        <p>✅ Solo noticias geopolíticas con imágenes reales</p>
    </div>
    
    {% for article in articles %}
    <div class="article">
        <div class="title">{{ article.title }}</div>
        <div class="meta">
            🏢 {{ article.source or 'Fuente desconocida' }} | 
            📅 {{ article.created_at or 'Fecha desconocida' }} |
            🆔 ID: {{ article.id }}
        </div>
        {% if article.image_url %}
        <div style="margin: 10px 0;">
            <img src="{{ article.image_url }}" alt="Imagen del artículo" style="border-radius: 4px;">
        </div>
        {% endif %}
        <div class="description">{{ article.description or 'Sin descripción disponible.' }}</div>
    </div>
    {% endfor %}
    
    {% if not articles %}
    <div class="status">
        <p>⚠️ No se encontraron artículos que cumplan los criterios</p>
        <p>Esto podría indicar un problema con el filtro SQL o falta de datos</p>
    </div>
    {% endif %}
</body>
</html>
"""

def get_geopolitical_articles():
    """Obtiene artículos geopolíticos con imágenes reales desde la base de datos"""
    db_path = "./data/geopolitical_intel.db"
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # SQL estricto para solo artículos geopolíticos con imágenes reales
        query = """
            SELECT 
                id, title, description, url, source, created_at,
                CASE 
                    WHEN original_image_url IS NOT NULL AND original_image_url != '' 
                    THEN original_image_url
                    WHEN image_url IS NOT NULL AND image_url != '' 
                         AND image_url NOT LIKE '%placeholder%' 
                         AND image_url NOT LIKE '%via.placeholder%'
                    THEN image_url
                    ELSE NULL
                END as image_url
            FROM articles 
            WHERE 
                -- Debe tener imagen real
                (
                    (original_image_url IS NOT NULL AND original_image_url != '') OR
                    (image_url IS NOT NULL AND image_url != '' AND 
                     image_url NOT LIKE '%placeholder%' AND 
                     image_url NOT LIKE '%via.placeholder%')
                )
                AND
                -- Debe ser geopolítico
                (
                    LOWER(title) LIKE '%war%' OR LOWER(title) LIKE '%conflict%' OR
                    LOWER(title) LIKE '%military%' OR LOWER(title) LIKE '%politics%' OR
                    LOWER(title) LIKE '%russia%' OR LOWER(title) LIKE '%ukraine%' OR
                    LOWER(title) LIKE '%china%' OR LOWER(title) LIKE '%iran%' OR
                    LOWER(title) LIKE '%israel%' OR LOWER(title) LIKE '%gaza%' OR
                    LOWER(title) LIKE '%security%' OR LOWER(title) LIKE '%diplomat%' OR
                    LOWER(title) LIKE '%government%' OR LOWER(title) LIKE '%president%' OR
                    LOWER(title) LIKE '%minister%' OR LOWER(title) LIKE '%trump%' OR
                    LOWER(title) LIKE '%biden%' OR LOWER(title) LIKE '%putin%' OR
                    LOWER(title) LIKE '%nuclear%' OR LOWER(title) LIKE '%nato%'
                )
                AND
                -- Solo artículos recientes (14 días)
                created_at >= datetime('now', '-14 days')
            ORDER BY created_at DESC
            LIMIT 50
        """
        
        cursor.execute(query)
        articles = [dict(row) for row in cursor.fetchall()]
        
        # Procesar imágenes locales
        for article in articles:
            if article['image_url'] and article['image_url'].startswith('news_'):
                article['image_url'] = f"/static/images/news/{article['image_url']}"
        
        conn.close()
        return articles
        
    except Exception as e:
        print(f"Error accediendo a la base de datos: {e}")
        return []

@app.route('/')
def index():
    """Página principal con el mosaico"""
    articles = get_geopolitical_articles()
    return render_template_string(MOSAIC_TEMPLATE, articles=articles)

@app.route('/api/articles')
def api_articles():
    """Endpoint de API para obtener artículos"""
    articles = get_geopolitical_articles()
    return jsonify(articles)

@app.route('/static/images/news/<filename>')
def serve_image(filename):
    """Servir imágenes locales"""
    import os
    from flask import send_from_directory
    
    image_dir = os.path.join(os.getcwd(), 'src', 'web', 'static', 'images', 'news')
    if os.path.exists(os.path.join(image_dir, filename)):
        return send_from_directory(image_dir, filename)
    else:
        # Imagen placeholder si no existe
        from flask import redirect
        return redirect('https://via.placeholder.com/400x300/ff6b6b/ffffff?text=Image+Not+Found')

@app.route('/test')
def test():
    """Endpoint de prueba"""
    articles = get_geopolitical_articles()
    return jsonify({
        'status': 'OK',
        'articles_count': len(articles),
        'message': 'Mosaico funcionando correctamente',
        'sample_articles': articles[:3]
    })

if __name__ == '__main__':
    print("🚀 Iniciando servidor simple del mosaico...")
    print("🌐 Accede a: http://localhost:5002")
    print("🔌 API: http://localhost:5002/api/articles")
    print("🧪 Test: http://localhost:5002/test")
    
    app.run(host='0.0.0.0', port=5002, debug=True, threaded=True)