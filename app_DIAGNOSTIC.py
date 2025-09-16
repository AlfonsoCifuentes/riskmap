#!/usr/bin/env python3
"""
Aplicación simplificada para diagnóstico - sin módulos problemáticos
Solo con los endpoints básicos para el frontend
"""

import sys
import os
import time
from datetime import datetime, timedelta

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuración Flask
from flask import Flask, jsonify, request, render_template, send_from_directory, send_file
from flask_cors import CORS
import sqlite3
import json
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Base de datos
DATABASE_PATH = "./data/geopolitical_intel.db"

def get_db_connection():
    """Obtener conexión a la base de datos"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_recent_articles(hours=24, limit=50):
    """Obtener artículos recientes"""
    try:
        conn = get_db_connection()
        
        # Calcular fecha límite
        cutoff_time = datetime.now() - timedelta(hours=hours)
        cutoff_str = cutoff_time.strftime('%Y-%m-%d %H:%M:%S')
        
        query = """
        SELECT 
            id, title, content, url, created_at, 
            source, source as source_name, image_url,
            summary, sentiment_score, risk_score
        FROM articles 
        WHERE created_at >= ? 
        ORDER BY created_at DESC 
        LIMIT ?
        """
        
        cursor = conn.execute(query, (cutoff_str, limit))
        articles = []
        
        for row in cursor.fetchall():
            article = {
                'id': row['id'],
                'title': row['title'] or 'Sin título',
                'content': row['content'] or 'Sin contenido',
                'url': row['url'],
                'pub_date': row['created_at'],  # Usar created_at como pub_date
                'source_url': row['url'],  # Usar url como source_url
                'source_name': row['source_name'] or 'Fuente desconocida',
                'image_url': row['image_url'] or '/static/default-news-image.jpg',  # Imagen por defecto
                'summary': row['summary'] or 'Sin resumen',
                'sentiment_score': row['sentiment_score'] or 0.0,
                'risk_score': row['risk_score'] or 0.0
            }
            articles.append(article)
        
        conn.close()
        return articles
        
    except Exception as e:
        logger.error(f"Error obteniendo artículos: {e}")
        return []

def get_hero_article():
    """Obtener artículo destacado"""
    try:
        articles = get_recent_articles(hours=48, limit=1)
        if articles:
            return articles[0]
        return None
    except Exception as e:
        logger.error(f"Error obteniendo artículo hero: {e}")
        return None

# RUTAS PRINCIPALES
@app.route('/')
def index():
    """Página principal"""
    return render_template('riskmap_modern.html')

@app.route('/favicon.ico')
def favicon():
    """Favicon"""
    try:
        static_dir = app.static_folder or 'static'
        return send_from_directory(static_dir, 'favicon.ico')
    except FileNotFoundError:
        # Crear un favicon simple si no existe
        return jsonify({'error': 'Favicon not found'}), 404

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Servir archivos estáticos"""
    static_dir = app.static_folder or 'static'
    return send_from_directory(static_dir, filename)

# API ENDPOINTS
@app.route('/api/articles', methods=['GET'])
def api_articles():
    """API: Obtener artículos"""
    try:
        hours = request.args.get('hours', 24, type=int)
        limit = request.args.get('limit', 50, type=int)
        
        articles = get_recent_articles(hours=hours, limit=limit)
        
        return jsonify({
            'success': True,
            'articles': articles,
            'total': len(articles),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en /api/articles: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/articles/deduplicated', methods=['GET'])
def api_articles_deduplicated():
    """API: Artículos deduplicados para el mosaico"""
    try:
        hours = request.args.get('hours', 24, type=int)
        
        # Para simplificar, usar artículos normales como "deduplicados"
        articles = get_recent_articles(hours=hours, limit=20)
        
        # Formatear para el mosaico
        mosaic = []
        for article in articles[:12]:  # Máximo 12 para el mosaico
            mosaic_item = {
                'id': article['id'],
                'title': article['title'],
                'summary': article['summary'][:200] + '...' if len(article.get('summary', '')) > 200 else article['summary'],
                'url': article['url'],
                'image_url': article['image_url'] or '/static/default-news-image.jpg',
                'source_name': article['source_name'],
                'pub_date': article['pub_date'],
                'sentiment_score': article['sentiment_score'],
                'risk_score': article['risk_score']
            }
            mosaic.append(mosaic_item)
        
        if len(mosaic) == 0:
            return jsonify({
                'success': False,
                'error': 'No hay artículos disponibles',
                'mosaic': [],
                'fallback': 'regular_articles'
            })
        
        return jsonify({
            'success': True,
            'mosaic': mosaic,
            'total': len(mosaic),
            'message': f'Mosaico generado con {len(mosaic)} artículos',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en /api/articles/deduplicated: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'mosaic': [],
            'fallback': 'regular_articles'
        }), 500

@app.route('/api/hero-article', methods=['GET'])
def api_hero_article():
    """API: Artículo destacado"""
    try:
        hero = get_hero_article()
        
        if not hero:
            return jsonify({
                'success': False,
                'error': 'No hay artículo destacado disponible'
            })
        
        return jsonify({
            'success': True,
            'article': hero,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en /api/hero-article: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/status', methods=['GET'])
def api_status():
    """API: Estado del sistema"""
    try:
        # Verificar base de datos
        conn = get_db_connection()
        cursor = conn.execute("SELECT COUNT(*) as count FROM articles")
        article_count = cursor.fetchone()['count']
        conn.close()
        
        return jsonify({
            'success': True,
            'status': 'running',
            'database': 'connected',
            'articles_total': article_count,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en /api/status: {e}")
        return jsonify({
            'success': False,
            'status': 'error',
            'error': str(e)
        }), 500

def create_favicon():
    """Crear un favicon simple si no existe"""
    static_dir = app.static_folder or 'static'
    favicon_path = os.path.join(static_dir, 'favicon.ico')
    if not os.path.exists(favicon_path):
        # Crear directorio static si no existe
        os.makedirs(static_dir, exist_ok=True)
        
        # Crear un favicon básico (16x16 bitmap)
        # En lugar de usar PIL, simplemente copiamos uno existente o creamos uno mínimo
        try:
            with open(favicon_path, 'wb') as f:
                # Favicon ICO mínimo (16x16, 1-bit)
                ico_data = b'\x00\x00\x01\x00\x01\x00\x10\x10\x00\x00\x01\x00\x01\x00(\x01\x00\x00\x16\x00\x00\x00(\x00\x00\x00\x10\x00\x00\x00 \x00\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x80\x00\x00\x80\x00\x00\x80\x00\x00\x80\x00\x00\x80\x00\x00\x80\x00\x00\x80\x00\x00\x80\x00\x00\x80\x00\x00\x80\x00\x00\x80\x00\x00\x80\x00\x00\x80\x00\x00\x80\x00\x00\x80\x00\x00\x80\x00\x00\x80\x00\x00\x80\x00\x00\x80\x00\x00\x80\x00\x00\x80\x00\x00\x80\x00\x00\x80\x00\x00\x80\x00\x00\x80\x00\x00\x80\x00\x00\x80\x00\x00\x80\x00\x00\x80\x00\x00\x80\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
                f.write(ico_data)
            logger.info(f"Favicon creado en: {favicon_path}")
        except Exception as e:
            logger.error(f"No se pudo crear favicon: {e}")

def check_database():
    """Verificar que la base de datos existe"""
    if not os.path.exists(DATABASE_PATH):
        logger.error(f"Base de datos no encontrada: {DATABASE_PATH}")
        return False
    
    try:
        conn = get_db_connection()
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articles'")
        table_exists = cursor.fetchone() is not None
        conn.close()
        
        if not table_exists:
            logger.error("Tabla 'articles' no encontrada en la base de datos")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error verificando base de datos: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 APLICACIÓN SIMPLIFICADA PARA DIAGNÓSTICO")
    print("=" * 50)
    
    # Verificar base de datos
    print("🔍 Verificando base de datos...")
    if not check_database():
        print("❌ Problema con la base de datos")
        print("💡 Verifica que existe: ./data/geopolitical_intel.db")
        return
    print("✅ Base de datos OK")
    
    # Crear favicon
    print("🎨 Verificando favicon...")
    create_favicon()
    print("✅ Favicon OK")
    
    # Iniciar aplicación
    print("🌐 Iniciando servidor...")
    print("📍 URL: http://localhost:5001")
    print("🔧 Modo diagnóstico - solo endpoints básicos")
    
    try:
        app.run(host='0.0.0.0', port=5001, debug=False)
    except Exception as e:
        logger.error(f"Error iniciando aplicación: {e}")

if __name__ == "__main__":
    main()